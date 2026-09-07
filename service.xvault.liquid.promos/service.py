from __future__ import annotations

import datetime as _datetime
import html
import json
import re
import socket
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SERVICE_ID = "service.xvault.liquid.promos"
SKIN_ID = "skin.xvault.liquid"
XVAULT_VIDEO_ADDON_ID = "plugin.video.xvault"
JUSTWATCH_BASE_URL = "https://www.justwatch.com"
JUSTWATCH_SERIES_URL = f"{JUSTWATCH_BASE_URL}/de/Serien"
JUSTWATCH_IMAGE_BASE = "https://images.justwatch.com"
TVMAZE_API_URL = "https://www.tvmaze.com/api"
USER_AGENT = "Mozilla/5.0 xVAULT-Liquid-Kodi-Skin/0.1.7 (+https://www.justwatch.com/de/Serien)"
MAX_DOWNLOADS = 14
MAX_DETAIL_FETCHES = 24
REFRESH_HOURS = 8
ROTATION_SECONDS = 8
HOME_WINDOW_ID = 10000

_TVSHOW_INDEX = None
_LIBRARY_PATH_CACHE: dict[str, str] = {}
_XVAULT_ADDON_AVAILABLE = None

XVAULT_RUNTIME_MODULE_IDS = (
    "script.module.requests",
    "script.module.certifi",
    "script.module.urllib3",
    "script.module.idna",
    "script.module.chardet",
    "script.module.six",
    "script.module.infotagger",
    "script.module.pyaes",
    "script.module.pyqrcode",
)

FALLBACK_ITEMS = {
    "00-liquid-wall.png": {
        "show": "xVAULT Liquid",
        "episode": "Cinematic Home",
        "channel": "Lokales Fanart",
        "summary": "Ein ruhiger Glas-Look fuer dein Kodi-Wohnzimmer: Artwork im Vollbild, schwebende Navigation und genug Kontrast fuer Couch-Entfernung.",
    },
    "01-night-city.png": {
        "show": "Night City Stories",
        "episode": "Fallback Promo",
        "channel": "xVAULT",
        "summary": "Neon, Glas und Tiefe als Platzhalter-Promo, solange noch keine aktuellen Serienbilder geladen wurden.",
    },
    "02-orbit-signal.png": {
        "show": "Orbit Signal",
        "episode": "Fallback Promo",
        "channel": "xVAULT",
        "summary": "Ein warmer Sci-Fi-Hintergrund fuer die Startseite, wenn der Live-Dienst gerade keine TVmaze-Bilder erreicht.",
    },
    "03-north-coast.png": {
        "show": "North Coast",
        "episode": "Fallback Promo",
        "channel": "xVAULT",
        "summary": "Kuehle Kinostimmung fuer den Slider: reduziert, kontrastreich und passend zum Liquid-Glass-Dock.",
    },
}


def _kodi_modules():
    try:
        import xbmc  # type: ignore
        import xbmcaddon  # type: ignore
        import xbmcgui  # type: ignore

        return xbmc, xbmcaddon, xbmcgui
    except Exception:
        return None, None, None


xbmc, xbmcaddon, xbmcgui = _kodi_modules()
IS_KODI = xbmc is not None and xbmcaddon is not None and xbmcgui is not None


def _log(message: str) -> None:
    line = f"[{SERVICE_ID}] {message}"
    if IS_KODI:
        xbmc.log(line, xbmc.LOGINFO)  # type: ignore[union-attr]
    else:
        print(line)


def _notify(message: str) -> None:
    if not IS_KODI:
        _log(message)
        return

    try:
        xbmcgui.Dialog().notification(  # type: ignore[union-attr]
            "xVAULT",
            message,
            xbmcgui.NOTIFICATION_INFO,  # type: ignore[union-attr]
            3500,
        )
    except Exception:
        _log(message)


def _is_xvault_addon_available(refresh: bool = False) -> bool:
    global _XVAULT_ADDON_AVAILABLE

    if not IS_KODI:
        return False
    if _XVAULT_ADDON_AVAILABLE is not None and not refresh:
        return bool(_XVAULT_ADDON_AVAILABLE)

    available = False
    for condition in (
        f"System.AddonIsEnabled({XVAULT_VIDEO_ADDON_ID})",
        f"System.HasAddon({XVAULT_VIDEO_ADDON_ID})",
    ):
        try:
            if xbmc.getCondVisibility(condition):  # type: ignore[union-attr]
                available = True
                break
        except Exception:
            pass

    if not available:
        try:
            xbmcaddon.Addon(XVAULT_VIDEO_ADDON_ID)  # type: ignore[union-attr]
            available = True
        except Exception:
            available = False

    if _XVAULT_ADDON_AVAILABLE is None or bool(_XVAULT_ADDON_AVAILABLE) != available:
        _log(f"{XVAULT_VIDEO_ADDON_ID} available: {available}")

    _XVAULT_ADDON_AVAILABLE = available
    return available


def _xvault_addon_path() -> str:
    if not IS_KODI:
        return ""

    try:
        return _translate_kodi_path(str(xbmcaddon.Addon(XVAULT_VIDEO_ADDON_ID).getAddonInfo("path")))  # type: ignore[union-attr]
    except Exception as exc:
        _log(f"could not resolve {XVAULT_VIDEO_ADDON_ID} path: {exc}")
        return ""


def _translate_kodi_path(path: str) -> str:
    if not path or not path.startswith("special://"):
        return path

    try:
        import xbmcvfs  # type: ignore

        return str(xbmcvfs.translatePath(path))
    except Exception:
        pass

    try:
        translated = xbmc.translatePath(path)  # type: ignore[union-attr]
        return translated.decode("utf-8") if isinstance(translated, bytes) else str(translated)
    except Exception:
        return path


def _addon_root_path(addon_id: str) -> str:
    if not IS_KODI:
        return ""

    try:
        return _translate_kodi_path(str(xbmcaddon.Addon(addon_id).getAddonInfo("path")))  # type: ignore[union-attr]
    except Exception:
        return ""


def _xvault_python_paths() -> list[str]:
    paths: list[str] = []

    addon_path = _xvault_addon_path()
    if addon_path:
        paths.append(addon_path)

    for addon_id in XVAULT_RUNTIME_MODULE_IDS:
        root = _addon_root_path(addon_id)
        if not root:
            continue
        for relative in ("lib", "resources/lib"):
            candidate = Path(root) / relative
            try:
                if candidate.exists():
                    paths.append(str(candidate))
            except Exception:
                pass

    seen: set[str] = set()
    unique_paths: list[str] = []
    for path in paths:
        key = path.casefold()
        if key in seen:
            continue
        seen.add(key)
        unique_paths.append(path)
    return unique_paths


def _prepend_python_paths(paths: list[str]) -> list[str]:
    inserted: list[str] = []
    for path in reversed(paths):
        if path and path not in sys.path:
            sys.path.insert(0, path)
            inserted.append(path)
    return inserted


def _restore_python_paths(paths: list[str]) -> None:
    for path in paths:
        try:
            sys.path.remove(path)
        except ValueError:
            pass


def _xvault_tvshow_meta(title: str, year: str = "") -> dict:
    if not title:
        return {}

    python_paths = _xvault_python_paths()
    if not python_paths:
        return {}

    inserted_paths = _prepend_python_paths(python_paths)

    try:
        try:
            from resources.lib import dependencies  # type: ignore

            dependencies.ensure_all_dependencies()
        except Exception as exc:
            _log(f"xVAULT dependency bootstrap skipped: {exc}")

        from resources.lib.tmdb import cTMDB  # type: ignore

        meta = cTMDB().get_meta("tvshow", title, year=str(year or ""), advanced="true")
    except Exception as exc:
        _log(f"xVAULT metadata lookup failed for '{title}': {exc}")
        return {}
    finally:
        _restore_python_paths(inserted_paths)

    if not isinstance(meta, dict) or not meta.get("tmdb_id"):
        return {}

    requested = _normalize_lookup(title)
    resolved = _normalize_lookup(str(meta.get("title") or meta.get("originaltitle") or ""))
    if requested and resolved and requested != resolved and requested not in resolved and resolved not in requested:
        _log(f"xVAULT metadata mismatch for '{title}': resolved '{meta.get('title')}'")
        return {}

    return meta


def _xvault_seasons_url_from_meta(meta: dict) -> str:
    if not meta or not meta.get("tmdb_id"):
        return ""

    title = str(meta.get("title") or meta.get("originaltitle") or "").strip()
    if not title:
        return ""

    sysmeta = {
        key: value
        for key, value in meta.items()
        if key
        in {
            "title",
            "originaltitle",
            "tmdb_id",
            "tvdb_id",
            "imdb_id",
            "imdbnumber",
            "number_of_seasons",
            "plot",
            "poster",
            "fanart",
            "year",
            "premiered",
            "duration",
            "rating",
            "votes",
            "genre",
            "status",
            "originallanguage",
            "backdrop_url",
            "cover_url",
        }
    }
    sysmeta["title"] = title
    sysmeta["systitle"] = title
    sysmeta["sysname"] = title
    sysmeta["mediatype"] = "tvshow"
    sysmeta.setdefault("plot", "")
    sysmeta.setdefault("number_of_seasons", 0)

    encoded = urllib.parse.quote_plus(json.dumps(sysmeta, ensure_ascii=False))
    return f"plugin://{XVAULT_VIDEO_ADDON_ID}/?action=seasons&sysmeta={encoded}"


def _xvault_tvshow_url(title: str, year: str = "") -> str:
    return _xvault_seasons_url_from_meta(_xvault_tvshow_meta(title, year))


def _open_xvault_tvshow(title: str, year: str = "") -> bool:
    if not title or not _is_xvault_addon_available(refresh=True):
        return False

    url = _xvault_tvshow_url(title, year)
    if not url:
        _log(f"could not build direct xVAULT tv show page for '{title}'")
        _notify(f"{_shorten(title, 34)} nicht direkt in xVAULT gefunden.")
        return False

    _log(f"opening xVAULT tv show page for spotlight show '{title}'")
    xbmc.executebuiltin(f"ActivateWindow(Videos,{url},return)")  # type: ignore[union-attr]
    return True


def _skin_root() -> Path:
    if IS_KODI:
        try:
            return Path(xbmcaddon.Addon(SKIN_ID).getAddonInfo("path"))  # type: ignore[union-attr]
        except Exception:
            pass
    return Path(__file__).resolve().parent.parent / SKIN_ID


def _promo_dir() -> Path:
    return _skin_root() / "media" / "promos"


def _fetch_text(url: str, timeout: int = 18) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "de-DE,de;q=0.9,en;q=0.7",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        encoding = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(encoding, "replace")


def _fetch_json(url: str, timeout: int = 18):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _execute_json_rpc(method: str, params=None) -> dict:
    if not IS_KODI:
        return {}

    payload = {"jsonrpc": "2.0", "method": method, "id": 1}
    if params is not None:
        payload["params"] = params

    try:
        response = xbmc.executeJSONRPC(json.dumps(payload))  # type: ignore[union-attr]
        return json.loads(response or "{}")
    except Exception as exc:
        _log(f"json-rpc failed for {method}: {exc}")
        return {}


def _normalize_lookup(value: str) -> str:
    text = html.unescape(str(value or ""))
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.casefold().replace("&", " and ")
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _load_tvshow_index() -> dict[str, str]:
    global _TVSHOW_INDEX

    if _TVSHOW_INDEX is not None:
        return _TVSHOW_INDEX

    _TVSHOW_INDEX = {}
    if not IS_KODI:
        return _TVSHOW_INDEX

    param_variants = (
        {"properties": ["title", "originaltitle", "year"], "limits": {"start": 0, "end": 10000}},
        {"limits": {"start": 0, "end": 10000}},
    )
    shows: list[dict] = []
    for params in param_variants:
        data = _execute_json_rpc("VideoLibrary.GetTVShows", params)
        if data.get("error"):
            continue
        shows = data.get("result", {}).get("tvshows") or []
        if shows:
            break

    for show in shows:
        tvshow_id = show.get("tvshowid")
        if not isinstance(tvshow_id, int):
            continue

        path = f"videodb://tvshows/titles/{tvshow_id}/"
        for key in ("title", "label", "originaltitle"):
            title = _normalize_lookup(str(show.get(key) or ""))
            if title and title not in _TVSHOW_INDEX:
                _TVSHOW_INDEX[title] = path

    _log(f"indexed {len(_TVSHOW_INDEX)} local tv show title aliases")
    return _TVSHOW_INDEX


def _find_local_tvshow_path(title: str) -> str:
    normalized = _normalize_lookup(title)
    if not normalized:
        return ""

    if normalized in _LIBRARY_PATH_CACHE:
        return _LIBRARY_PATH_CACHE[normalized]

    index = _load_tvshow_index()
    path = index.get(normalized, "")

    if not path and len(normalized) >= 6:
        loose_matches = [
            (abs(len(candidate) - len(normalized)), candidate_path)
            for candidate, candidate_path in index.items()
            if len(candidate) >= 6 and (normalized in candidate or candidate in normalized)
        ]
        if loose_matches:
            path = sorted(loose_matches, key=lambda item: item[0])[0][1]

    _LIBRARY_PATH_CACHE[normalized] = path
    return path


def _download(url: str, target: Path, timeout: int = 25) -> bool:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = response.headers.get("Content-Type", "")
            data = response.read()
    except (OSError, urllib.error.URLError, socket.timeout) as exc:
        _log(f"download failed: {url} ({exc})")
        return False

    if not data or "image" not in content_type.lower():
        return False

    target.write_bytes(data)
    return True


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64] or "show"


def _plain_summary(value: str | None) -> str:
    if not value:
        return ""
    text = re.sub(r"<[^>]+>", " ", value)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def _extract_nuxt_data(markup: str) -> list:
    match = re.search(r'<script[^>]+id=["\']__NUXT_DATA__["\'][^>]*>(.*?)</script>', markup, re.S)
    if not match:
        return []

    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        _log(f"JustWatch payload parse failed: {exc}")
        return []

    if isinstance(payload, list):
        return payload
    return []


def _jw_ref(data: list, value):
    if isinstance(value, int) and 0 <= value < len(data):
        return data[value]
    return value


def _jw_string(data: list, value) -> str:
    raw = _jw_ref(data, value)
    if raw is None or isinstance(raw, (dict, list)):
        return ""
    return str(raw).strip()


def _jw_int(data: list, value) -> int | None:
    raw = _jw_ref(data, value)
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw)
    return None


def _jw_list(data: list, value) -> list:
    raw = _jw_ref(data, value)
    if isinstance(raw, list):
        return raw
    return []


def _jw_dict(data: list, value) -> dict:
    raw = _jw_ref(data, value)
    if isinstance(raw, dict):
        return raw
    return {}


def _jw_cache(data: list) -> dict:
    for item in data:
        if isinstance(item, dict) and "ROOT_QUERY" in item:
            return item
    return {}


def _jw_lookup(data: list, cache: dict, ref_value) -> dict:
    value = _jw_ref(data, ref_value)
    if isinstance(value, dict) and "__ref" in value:
        ref_key = _jw_string(data, value.get("__ref"))
    elif isinstance(value, str):
        ref_key = value
    else:
        return {}

    cache_index = cache.get(ref_key)
    return _jw_dict(data, cache_index)


def _jw_show_content(data: list, show: dict) -> dict:
    preferred_keys = [
        'content({"country":"DE","language":"de"})',
        "content",
    ]
    for key in preferred_keys:
        content = _jw_dict(data, show.get(key))
        if content:
            return content

    for key, value in show.items():
        if key.startswith("content("):
            content = _jw_dict(data, value)
            if content:
                return content
    return {}


def _jw_image_url(path: str, profile: str = "s1920", image_format: str = "jpg") -> str:
    if not path:
        return ""

    url = path.replace("{profile}", profile).replace("{format}", image_format)
    if url.startswith("//"):
        return "https:" + url
    if url.startswith("http://") or url.startswith("https://"):
        return url
    if url.startswith("/"):
        return JUSTWATCH_IMAGE_BASE + url
    return ""


def _jw_backdrops_from_content(data: list, content: dict) -> list[str]:
    urls: list[str] = []
    keys = [
        'backdrops({"format":"JPG","profile":"S1920"})',
        "backdrops",
    ]

    for key in keys:
        for entry_ref in _jw_list(data, content.get(key)):
            entry = _jw_dict(data, entry_ref)
            image_url = _jw_image_url(_jw_string(data, entry.get("backdropUrl")))
            if image_url and image_url not in urls:
                urls.append(image_url)

    return urls


def _jw_backdrops_from_markup(markup: str) -> list[str]:
    candidates = re.findall(r"https://images\.justwatch\.com/backdrop/[^\"\\<>\s]+?\.jpg", markup)
    candidates.extend(
        JUSTWATCH_IMAGE_BASE + path
        for path in re.findall(r"(/backdrop/[^\"\\<>\s]+?\.jpg)", markup)
    )

    ordered: list[str] = []
    for image_url in candidates:
        if "/s1920/" in image_url and image_url not in ordered:
            ordered.append(image_url)
    for image_url in candidates:
        if image_url not in ordered:
            ordered.append(image_url)
    return ordered


def _jw_provider_name(data: list, cache: dict, show: dict) -> str:
    for key, value in show.items():
        if not key.startswith("watchNowOffer("):
            continue

        offer = _jw_lookup(data, cache, value)
        if not offer:
            continue

        package = _jw_lookup(data, cache, offer.get("package"))
        provider = _jw_string(data, package.get("clearName"))
        if provider:
            return provider
    return ""


def _jw_rank(data: list, show: dict) -> int | None:
    rank = _jw_dict(data, show.get('popularityRank({"country":"DE"})'))
    if rank:
        return _jw_int(data, rank.get("rank"))

    charts = _jw_dict(data, show.get('streamingCharts({"country":"DE"})'))
    for edge_ref in _jw_list(data, charts.get("edges")):
        edge = _jw_dict(data, edge_ref)
        info = _jw_dict(data, edge.get("streamingChartInfo"))
        value = _jw_int(data, info.get("rank"))
        if value:
            return value
    return None


def _jw_catalog_items() -> list[dict]:
    try:
        markup = _fetch_text(JUSTWATCH_SERIES_URL)
    except Exception as exc:
        _log(f"JustWatch catalogue fetch failed: {exc}")
        return []

    data = _extract_nuxt_data(markup)
    cache = _jw_cache(data)
    if not data or not cache:
        _log("JustWatch catalogue payload missing")
        return []

    items: list[dict] = []
    seen_paths: set[str] = set()
    for key, value in cache.items():
        if not key.startswith("Show:"):
            continue

        show = _jw_dict(data, value)
        content = _jw_show_content(data, show)
        full_path = _jw_string(data, content.get("fullPath"))
        title = _jw_string(data, content.get("title"))
        if not full_path.startswith("/de/Serie/") or not title or full_path in seen_paths:
            continue

        seen_paths.add(full_path)
        provider = _jw_provider_name(data, cache, show)
        poster = _jw_image_url(_jw_string(data, content.get('posterUrl({"format":"JPG","profile":"S718"})')), "s718")
        if not poster:
            poster = _jw_image_url(_jw_string(data, content.get("posterUrl")), "s718")

        items.append(
            {
                "source_name": "JustWatch",
                "show": title,
                "episode": "",
                "year": _jw_int(data, content.get("originalReleaseYear")),
                "runtime": _jw_int(data, content.get("runtime")),
                "rank": len(items) + 1,
                "channel": provider,
                "url": JUSTWATCH_BASE_URL + full_path,
                "image": poster,
                "summary": _plain_summary(_jw_string(data, content.get("shortDescription"))),
            }
        )

    return items


def _jw_detail_item(item: dict) -> dict:
    url = item.get("url")
    if not url:
        return {}

    try:
        markup = _fetch_text(str(url))
    except Exception as exc:
        _log(f"JustWatch detail fetch failed: {url} ({exc})")
        return {}

    data = _extract_nuxt_data(markup)
    cache = _jw_cache(data)
    full_path = str(url).replace(JUSTWATCH_BASE_URL, "", 1)
    selected_show: dict = {}
    selected_content: dict = {}

    for key, value in cache.items():
        if not key.startswith("Show:"):
            continue

        show = _jw_dict(data, value)
        content = _jw_show_content(data, show)
        if _jw_string(data, content.get("fullPath")) == full_path:
            selected_show = show
            selected_content = content
            break

    if not selected_content:
        for key, value in cache.items():
            if key.startswith("Show:"):
                selected_show = _jw_dict(data, value)
                selected_content = _jw_show_content(data, selected_show)
                break

    detail: dict = {}
    title = _jw_string(data, selected_content.get("title"))
    if title:
        detail["show"] = title

    summary = _plain_summary(_jw_string(data, selected_content.get("shortDescription")))
    editorial = _jw_dict(data, selected_content.get("editorialContent"))
    editorial_summary = _plain_summary(_jw_string(data, editorial.get("synopsis")))
    if editorial_summary and len(editorial_summary) > len(summary):
        summary = editorial_summary
    if summary:
        detail["summary"] = summary

    for key_name, source_key in (("year", "originalReleaseYear"), ("runtime", "runtime")):
        value = _jw_int(data, selected_content.get(source_key))
        if value:
            detail[key_name] = value

    provider = _jw_provider_name(data, cache, selected_show)
    if provider:
        detail["channel"] = provider

    rank = _jw_rank(data, selected_show)
    if rank:
        detail["rank"] = rank

    backdrops = _jw_backdrops_from_content(data, selected_content) + _jw_backdrops_from_markup(markup)
    if backdrops:
        detail["image"] = backdrops[0]

    return detail


def _collect_justwatch_items() -> list[dict]:
    items = _jw_catalog_items()
    if not items:
        return []

    detailed: list[dict] = []
    for item in items[:MAX_DETAIL_FETCHES]:
        detail = _jw_detail_item(item)
        merged = {**item, **{key: value for key, value in detail.items() if value}}
        if not merged.get("image"):
            continue
        detailed.append(merged)
        if len(detailed) >= MAX_DOWNLOADS:
            break

    _log(f"JustWatch candidates found: {len(detailed)}")
    return detailed


def _shorten(value: str, limit: int = 360) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rsplit(" ", 1)[0] + "..."


def _spotlight_summary(value: str) -> str:
    text = re.sub(r"\s+", " ", value or "").strip()
    sentence = re.match(r"^(.{70,220}?[.!?])(?:\s|$)", text)
    if sentence and len(sentence.group(1)) <= 145:
        return sentence.group(1)
    if sentence:
        return _shorten(sentence.group(1), 145)
    return _shorten(text, 145)


def _episode_code(item: dict) -> str:
    season = item.get("season")
    number = item.get("number")
    if isinstance(season, int) and isinstance(number, int) and season < 100:
        return f"S{season:02d}E{number:02d}"
    if season and number:
        return f"{season} / {number}"
    return ""


def _meta_line(item: dict) -> str:
    if item.get("source_name") == "JustWatch":
        parts = []
        rank = item.get("rank")
        if rank:
            parts.append(f"Platz {rank}")
        year = item.get("year")
        if year:
            parts.append(str(year))
        runtime = item.get("runtime")
        if runtime:
            parts.append(f"{runtime} min")
        provider = item.get("channel")
        if provider:
            parts.append(str(provider))
        return "  |  ".join(parts)

    parts = []
    code = _episode_code(item)
    if code:
        parts.append(code)
    episode = item.get("episode")
    if episode:
        parts.append(str(episode))
    channel = item.get("channel")
    if channel:
        parts.append(str(channel))
    genres = item.get("genres") or []
    if genres:
        parts.append(", ".join(str(genre) for genre in genres[:3]))
    return "  |  ".join(parts)


def _candidate_image(episode: dict, show: dict) -> str | None:
    episode_image = episode.get("image") or {}
    if episode_image.get("original"):
        return episode_image["original"]

    show_image = show.get("image") or {}
    if show_image.get("original"):
        return show_image["original"]

    return None


def _collect_tvmaze_items(day: _datetime.date) -> list[dict]:
    endpoints = [
        f"https://api.tvmaze.com/schedule/web?country=US&date={day.isoformat()}",
        f"https://api.tvmaze.com/schedule?country=US&date={day.isoformat()}",
    ]
    seen: set[int] = set()
    items: list[dict] = []

    for endpoint in endpoints:
        try:
            payload = _fetch_json(endpoint)
        except Exception as exc:
            _log(f"schedule fetch failed: {endpoint} ({exc})")
            continue

        for episode in payload:
            show = (episode.get("_embedded") or {}).get("show") or {}
            show_id = show.get("id")
            if not show_id or show_id in seen:
                continue

            image_url = _candidate_image(episode, show)
            if not image_url:
                continue

            show_type = (show.get("type") or "").lower()
            if show_type in {"news", "sports", "talk show"}:
                continue

            seen.add(show_id)
            items.append(
                {
                    "source_name": "TVmaze",
                    "show": show.get("name") or "Serie",
                    "episode": episode.get("name") or "",
                    "season": episode.get("season"),
                    "number": episode.get("number"),
                    "genres": show.get("genres") or [],
                    "channel": ((show.get("webChannel") or show.get("network") or {}).get("name") or ""),
                    "url": show.get("url") or episode.get("url") or "",
                    "image": image_url,
                    "summary": _plain_summary(show.get("summary")),
                }
            )

    return items


def _stale(stamp: Path) -> bool:
    if not stamp.exists():
        return True
    age_seconds = time.time() - stamp.stat().st_mtime
    return age_seconds > REFRESH_HOURS * 60 * 60


def update_promos(force: bool = False) -> int:
    promo_dir = _promo_dir()
    promo_dir.mkdir(parents=True, exist_ok=True)
    stamp = promo_dir / ".xvault-promos-updated"

    if not force and not _stale(stamp):
        _log("promo cache is fresh")
        return 0

    today = _datetime.date.today()
    items = _collect_justwatch_items()
    if len(items) < 5:
        _log("not enough JustWatch promos, trying TVmaze fallback")
        items.extend(_collect_tvmaze_items(today))
        items.extend(_collect_tvmaze_items(today - _datetime.timedelta(days=1)))
        items.extend(_collect_tvmaze_items(today + _datetime.timedelta(days=1)))

    selected = items[:MAX_DOWNLOADS]
    if not selected:
        _log("no promo candidates found")
        return 0

    for old_file in promo_dir.glob("live-*.jpg"):
        try:
            old_file.unlink()
        except OSError:
            pass

    downloaded = 0
    manifest: list[dict] = []
    for index, item in enumerate(selected, 1):
        file_name = f"live-{index:02d}-{_slug(item['show'])}.jpg"
        target = promo_dir / file_name
        if _download(item["image"], target):
            downloaded += 1
            manifest.append({**item, "file": file_name})

    if downloaded:
        (promo_dir / "justwatch-promos.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        (promo_dir / "source-justwatch.txt").write_text(
            "Live promo images and metadata are loaded from JustWatch Germany series pages.\n"
            f"Catalogue: {JUSTWATCH_SERIES_URL}\n"
            f"Fallback API: {TVMAZE_API_URL}\n"
            "Downloaded artwork remains a local runtime cache and is not bundled in release zips.\n",
            encoding="utf-8",
        )
        stamp.write_text(today.isoformat(), encoding="utf-8")

    _log(f"downloaded {downloaded} live promo images")
    return downloaded


def _load_live_items(promo_dir: Path) -> list[dict]:
    manifest_path = promo_dir / "justwatch-promos.json"
    if not manifest_path.exists():
        manifest_path = promo_dir / "tvmaze-promos.json"
    if not manifest_path.exists():
        return []

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _log(f"could not read promo manifest: {exc}")
        return []

    items: list[dict] = []
    for entry in manifest:
        file_name = entry.get("file")
        if not file_name:
            continue
        image_path = promo_dir / str(file_name)
        if not image_path.exists():
            continue
        items.append(
            {
                "image": str(image_path),
                "title": _shorten(str(entry.get("show") or "Serie"), 48),
                "lookup_title": str(entry.get("show") or "Serie"),
                "year": str(entry.get("year") or ""),
                "meta": _shorten(_meta_line(entry), 88),
                "summary": _spotlight_summary(str(entry.get("summary") or "Keine Serienbeschreibung verfuegbar.")),
                "source": str(entry.get("url") or "https://www.tvmaze.com/api"),
            }
        )

    return items


def _load_fallback_items(promo_dir: Path) -> list[dict]:
    items: list[dict] = []
    for file_name, data in FALLBACK_ITEMS.items():
        image_path = promo_dir / file_name
        if not image_path.exists():
            continue
        items.append(
            {
                "image": str(image_path),
                "title": data["show"],
                "lookup_title": data["show"],
                "year": "",
                "meta": f"{data['episode']}  |  {data['channel']}",
                "summary": _shorten(data["summary"], 245),
                "source": "local",
            }
        )
    return items


def load_slider_items() -> list[dict]:
    promo_dir = _promo_dir()
    return _load_live_items(promo_dir) + _load_fallback_items(promo_dir)


def _publish(item: dict, index: int, total: int) -> None:
    if not IS_KODI:
        _log(f"preview {index + 1}/{total}: {item['title']} -> {item['image']}")
        return

    lookup_title = str(item.get("lookup_title") or item.get("title") or "")
    library_path = _find_local_tvshow_path(lookup_title)

    window = xbmcgui.Window(HOME_WINDOW_ID)  # type: ignore[union-attr]
    window.setProperty("xvault_liquid_promo_image", item["image"])
    window.setProperty("xvault_liquid_promo_title", item["title"])
    window.setProperty("xvault_liquid_promo_lookup_title", lookup_title)
    window.setProperty("xvault_liquid_promo_year", str(item.get("year") or ""))
    window.setProperty("xvault_liquid_promo_meta", item["meta"])
    window.setProperty("xvault_liquid_promo_summary", item["summary"])
    window.setProperty("xvault_liquid_promo_source", item["source"])
    window.setProperty("xvault_liquid_promo_library_path", library_path)
    window.setProperty(
        "xvault_liquid_xvault_search_available",
        "true" if _is_xvault_addon_available() else "false",
    )
    window.setProperty("xvault_liquid_promo_position", f"{index + 1}/{total}")


def _open_spotlight() -> None:
    if not IS_KODI:
        _log("spotlight open is only available inside Kodi")
        return

    window = xbmcgui.Window(HOME_WINDOW_ID)  # type: ignore[union-attr]
    title = (
        window.getProperty("xvault_liquid_promo_lookup_title")
        or window.getProperty("xvault_liquid_promo_title")
        or ""
    )
    library_path = window.getProperty("xvault_liquid_promo_library_path") or ""
    year = window.getProperty("xvault_liquid_promo_year") or ""

    if _open_xvault_tvshow(title, year):
        return

    if not library_path and title:
        library_path = _find_local_tvshow_path(title)

    if library_path:
        _log(f"opening spotlight show '{title}' at {library_path}")
        xbmc.executebuiltin(f"ActivateWindow(Videos,{library_path},return)")  # type: ignore[union-attr]
        return

    if title:
        _log(f"spotlight show not found in local library: {title}")
        _notify(f"{_shorten(title, 34)} nicht in der Kodi-Bibliothek gefunden.")

    if _load_tvshow_index():
        xbmc.executebuiltin("ActivateWindow(Videos,videodb://tvshows/titles/,return)")  # type: ignore[union-attr]
    else:
        xbmc.executebuiltin("ActivateWindow(Videos,sources://video/,return)")  # type: ignore[union-attr]


def _run_rotator(force: bool = False) -> None:
    update_promos(force=force)
    items = load_slider_items()
    if not items:
        _log("no slider items available")
        return

    _log(f"rotating {len(items)} promo items")

    if not IS_KODI:
        for index, item in enumerate(items):
            _publish(item, index, len(items))
        return

    monitor = xbmc.Monitor()  # type: ignore[union-attr]
    index = 0
    last_refresh = time.time()

    while not monitor.abortRequested():
        _publish(items[index], index, len(items))
        index = (index + 1) % len(items)

        if monitor.waitForAbort(ROTATION_SECONDS):
            break

        if time.time() - last_refresh > REFRESH_HOURS * 60 * 60:
            update_promos(force=True)
            refreshed = load_slider_items()
            if refreshed:
                items = refreshed
                index = 0
            last_refresh = time.time()


def main() -> None:
    if "--open-spotlight" in sys.argv or "open_spotlight" in sys.argv:
        try:
            _open_spotlight()
        except Exception as exc:
            _log(f"spotlight open failed: {exc}")
        return

    force = "--force" in sys.argv
    try:
        _run_rotator(force=force)
    except Exception as exc:
        _log(f"promo service failed: {exc}")


if __name__ == "__main__":
    main()
