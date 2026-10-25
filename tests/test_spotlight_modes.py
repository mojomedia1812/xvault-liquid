import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("spotlight", ROOT / "service.xvault.liquid.promos/service.py")
promos = importlib.util.module_from_spec(spec)
spec.loader.exec_module(promos)


class SpotlightModeTests(unittest.TestCase):
    def test_dock_has_language_independent_media_types(self):
        home = ET.parse(ROOT / "skin.xvault.liquid/xml/Home.xml")
        items = home.findall(".//control[@id='9100']/content/item")
        self.assertEqual([item.findtext("property") for item in items[:2]], ["tvshow", "movie"])
        self.assertTrue(all(item.find("property") is None for item in items[2:]))

    def test_home_media_links_open_xvault_categories_not_local_library(self):
        home = ET.parse(ROOT / "skin.xvault.liquid/xml/Home.xml")
        items = home.findall(".//control[@id='9100']/content/item")
        for item, action in zip(items[:2], ("tvNavigator", "movieNavigator")):
            clicks = item.findall("onclick")
            self.assertEqual(len(clicks), 1)
            self.assertEqual(clicks[0].attrib, {})
            self.assertEqual(clicks[0].text, f"ActivateWindow(Videos,plugin://plugin.video.xvault/?action={action},return)")

    def test_switch_is_immediate_and_remembers_each_position(self):
        rotation = promos.SpotlightRotation({"tvshow": [{"title": "S1"}, {"title": "S2"}], "movie": [{"title": "M1"}, {"title": "M2"}]})
        self.assertEqual(rotation.select("tvshow", 100)[0]["title"], "S1")
        self.assertIsNone(rotation.select("tvshow", 101))
        self.assertEqual(rotation.select("tvshow", 108)[0]["title"], "S2")
        self.assertEqual(rotation.select("movie", 109)[0]["title"], "M1")
        self.assertEqual(rotation.select("movie", 117)[0]["title"], "M2")
        self.assertEqual(rotation.select("tvshow", 118)[0]["title"], "S2")
        self.assertEqual(rotation.select("movie", 119)[0]["title"], "M2")

    def test_refresh_handles_shorter_catalogue_without_advancing(self):
        rotation = promos.SpotlightRotation({"tvshow": [{}, {}], "movie": [{}]})
        rotation.select("tvshow", 100)
        rotation.select("tvshow", 108)
        rotation.catalogues["tvshow"] = [{"title": "refreshed"}]
        self.assertEqual(rotation.select("tvshow", 109, changed=True), ({"title": "refreshed"}, 0, 1))

    def test_other_dock_items_and_spotlight_keep_previous_mode(self):
        kodi = Mock()
        with patch.object(promos, "xbmc", kodi):
            kodi.getCondVisibility.return_value = True
            kodi.getInfoLabel.return_value = ""
            self.assertEqual(promos._focused_media_type("movie"), "movie")
            kodi.getInfoLabel.return_value = "tvshow"
            self.assertEqual(promos._focused_media_type("movie"), "tvshow")
            kodi.getCondVisibility.return_value = False
            self.assertEqual(promos._focused_media_type("movie"), "movie")

    def test_movie_catalogue_and_details_do_not_pick_series(self):
        movie = {"content": {"title": "Film", "fullPath": "/de/Film/film", "shortDescription": "Movie summary"}}
        show = {"content": {"title": "Series", "fullPath": "/de/Serie/series"}}
        data = [{"ROOT_QUERY": {}, "Show:1": show, "Movie:1": movie}]
        with patch.object(promos, "_fetch_text", return_value="markup") as fetch, patch.object(promos, "_extract_nuxt_data", return_value=data):
            items = promos._jw_catalog_items("movie")
            fetch.assert_called_once_with(promos.JUSTWATCH_MOVIES_URL)
            self.assertEqual([item["show"] for item in items], ["Film"])
            self.assertEqual(items[0]["media_type"], "movie")
            self.assertEqual(promos._jw_detail_item(items[0])["summary"], "Movie summary")

    def test_movie_failure_keeps_its_cache_and_never_uses_tvmaze(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            movies = root / "movies"
            movies.mkdir()
            image = movies / "live-old.jpg"
            image.write_bytes(b"existing")
            manifest = movies / "justwatch-promos.json"
            previous = json.dumps([{"file": image.name, "show": "Film", "media_type": "movie"}])
            manifest.write_text(previous)
            with patch.object(promos, "_promo_dir", return_value=root), patch.object(promos, "_collect_justwatch_items", return_value=[]), patch.object(promos, "_collect_tvmaze_items") as tvmaze:
                promos.update_promos(force=True, media_type="movie")
                tvmaze.assert_not_called()
                self.assertEqual(promos.load_slider_items("movie")[0]["title"], "Film")
            self.assertEqual(manifest.read_text(), previous)
            self.assertEqual(image.read_bytes(), b"existing")
            self.assertFalse((root / "justwatch-promos.json").exists())

    def test_empty_movie_cache_never_uses_series_fallbacks(self):
        with patch.object(promos, "_load_live_items", return_value=[]), patch.object(promos, "_local_movie_items", return_value=[]), patch.object(promos, "_load_fallback_items") as series:
            item = promos.load_slider_items("movie")[0]
            self.assertEqual(item["media_type"], "movie")
            self.assertEqual(item["source"], "local")
            series.assert_not_called()

    def test_movie_click_does_not_open_seasons_or_start_playback(self):
        window = Mock()
        properties = {"xvault_liquid_promo_lookup_title": "A film & more", "xvault_liquid_promo_type": "movie", "xvault_liquid_promo_source": "https://example.com/film"}
        window.getProperty.side_effect = lambda key: properties.get(key, "")
        kodi = Mock()
        gui = Mock()
        gui.Window.return_value = window
        with patch.object(promos, "IS_KODI", True), patch.object(promos, "xbmc", kodi), patch.object(promos, "xbmcgui", gui), patch.object(promos, "_is_xvault_addon_available", return_value=True), patch.object(promos, "_open_xvault_tvshow") as series:
            promos._open_spotlight()
            action = kodi.executebuiltin.call_args.args[0]
            self.assertIn("action=movies&page=1&query=A+film+%26+more", action)
            self.assertNotIn("Play", action)
            series.assert_not_called()

    def test_movie_runtime_cache_is_not_packaged(self):
        spec = importlib.util.spec_from_file_location("release", ROOT / "tools/build_release.py")
        release = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(release)
        self.assertFalse(release.should_include("skin.xvault.liquid", Path("media/promos/movies/live-film.jpg")))

    def test_local_movie_info_uses_native_dialog_and_database_id(self):
        gui = Mock()
        gui.Dialog.return_value.info.return_value = True
        details = {"title": "Local film", "file": "/films/local.mkv", "year": 2025, "art": {"fanart": "fanart.jpg"}}
        with patch.object(promos, "xbmcgui", gui), patch.object(promos, "_execute_json_rpc", return_value={"result": {"moviedetails": details}}) as rpc:
            self.assertTrue(promos._open_local_movie_info(42))
            self.assertEqual(rpc.call_args.args[0], "VideoLibrary.GetMovieDetails")
            self.assertEqual(rpc.call_args.args[1]["movieid"], 42)
            gui.ListItem.return_value.getVideoInfoTag.return_value.setDbId.assert_called_once_with(42)
            gui.Dialog.return_value.info.assert_called_once_with(gui.ListItem.return_value)
