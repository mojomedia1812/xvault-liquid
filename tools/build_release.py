from __future__ import annotations

import hashlib
import os
import re
import shutil
import urllib.request
import urllib.parse
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
REMOTE_ADDONS_XML = DIST / "xvault-remote-addons.xml"
REMOTE_ADDONS_URL = "https://xvault.repowork.de/addons.xml"
DEPENDENCY_REPOSITORIES = {"plugin.video.xvault": "https://xvault.repowork.de/"}
UPLOAD_DIR = DIST / "xvault-repo-upload"
REPO_ID = "repository.xvault"
EXTERNAL_REPOSITORY_DEPENDENCIES = {
    # Resolved by Kodi's official repository, not packaged in the xVAULT repo upload.
    "resource.images.weathericons.default",
}


def safe_rmtree(path: Path, allowed_parent: Path) -> None:
    resolved_path = path.resolve()
    resolved_parent = allowed_parent.resolve()
    if resolved_path == resolved_parent or resolved_parent not in resolved_path.parents:
        raise RuntimeError(f"Refusing to remove path outside {resolved_parent}: {resolved_path}")
    shutil.rmtree(resolved_path)


def addon_info(addon_dir: Path) -> tuple[str, str]:
    root = ET.parse(addon_dir / "addon.xml").getroot()
    return root.attrib["id"], root.attrib["version"]


def required_imports(addon_dir: Path) -> list[tuple[str, str]]:
    root = ET.parse(addon_dir / "addon.xml").getroot()
    requires = root.find("requires")
    if requires is None:
        return []

    imports: list[tuple[str, str]] = []
    for node in requires.findall("import"):
        if node.attrib.get("optional", "").lower() == "true":
            continue
        addon_id = node.attrib.get("addon", "").strip()
        if addon_id:
            imports.append((addon_id, node.attrib.get("version", "").strip()))
    return imports


def is_builtin_dependency(addon_id: str) -> bool:
    return addon_id.startswith("xbmc.")


def version_parts(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in re.findall(r"\d+", version or "0"))


def version_satisfies(actual: str, required: str) -> bool:
    if not required:
        return True
    actual_parts = version_parts(actual)
    required_parts = version_parts(required)
    length = max(len(actual_parts), len(required_parts))
    return actual_parts + (0,) * (length - len(actual_parts)) >= required_parts + (0,) * (length - len(required_parts))


def should_include(addon_id: str, relative_path: Path) -> bool:
    parts = relative_path.parts
    name = relative_path.name

    if "__pycache__" in parts or name.endswith((".pyc", ".pyo")):
        return False
    if name in {".DS_Store", "Thumbs.db"}:
        return False

    if addon_id == "skin.xvault.liquid":
        if parts and parts[0] == "skin.estuary":
            return False
        if len(parts) >= 3 and parts[0] == "media" and parts[1] == "promos":
            promo_name = parts[2]
            if promo_name == "movies":
                return False
            if promo_name.startswith("live-"):
                return False
            if promo_name.endswith("-promos.json"):
                return False
            if promo_name.startswith("source-") and promo_name.endswith(".txt"):
                return False

    return True


def build_addon_zip(addon_dir: Path) -> Path:
    addon_id, version = addon_info(addon_dir)
    zip_path = DIST / f"{addon_id}-{version}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(addon_dir.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(addon_dir)
            if not should_include(addon_id, relative):
                continue
            archive.write(path, Path(addon_id) / relative)

        if addon_id == "skin.xvault.liquid":
            archive.write(
                ROOT / "service.xvault.liquid.promos" / "service.py",
                f"{addon_id}/resources/lib/promos.py",
            )

    return zip_path


def build_repository_zip() -> Path | None:
    project_repo_dir = ROOT / REPO_ID
    if (project_repo_dir / "addon.xml").exists():
        return build_addon_zip(project_repo_dir)

    appdata = os.environ.get("APPDATA")
    if not appdata:
        return None

    repo_dir = Path(appdata) / "Kodi" / "addons" / REPO_ID
    addon_xml = repo_dir / "addon.xml"
    if not addon_xml.exists():
        return None

    _, version = addon_info(repo_dir)
    zip_path = DIST / f"{REPO_ID}-{version}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(repo_dir.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(repo_dir)
            if "__pycache__" in relative.parts or relative.name.endswith((".pyc", ".pyo")):
                continue
            archive.write(path, Path(REPO_ID) / relative)

    return zip_path


def clone_addon_node(addon_dir: Path) -> ET.Element:
    return ET.parse(addon_dir / "addon.xml").getroot()


def write_repository_metadata(addon_dirs: list[Path]) -> Path:
    try:
        with urllib.request.urlopen(REMOTE_ADDONS_URL, timeout=20) as response:
            remote_data = response.read()
        if ET.fromstring(remote_data).tag != "addons":
            raise ValueError("Unexpected repository metadata root")
        REMOTE_ADDONS_XML.write_bytes(remote_data)
    except Exception as exc:
        if not REMOTE_ADDONS_XML.exists():
            raise RuntimeError("Cannot build without xVAULT repository metadata") from exc
        print(f"Repository refresh failed; using cached metadata: {exc}")

    if REMOTE_ADDONS_XML.exists():
        root = ET.parse(REMOTE_ADDONS_XML).getroot()
    else:
        root = ET.Element("addons")

    new_ids = {addon_info(addon_dir)[0] for addon_dir in addon_dirs}
    for node in list(root):
        if node.tag == "addon" and node.attrib.get("id") in new_ids:
            root.remove(node)

    for addon_dir in addon_dirs:
        root.append(clone_addon_node(addon_dir))

    ET.indent(root, space="    ")
    tree = ET.ElementTree(root)
    output = DIST / "addons.xml"
    tree.write(output, encoding="UTF-8", xml_declaration=True)

    data = output.read_bytes()
    (DIST / "addons.xml.md5").write_text(hashlib.md5(data).hexdigest(), encoding="ascii")
    return output


def fetch_dependency_zips(addon_dirs: list[Path], metadata_path: Path) -> list[Path]:
    metadata = {node.get("id"): node for node in ET.parse(metadata_path).getroot().findall("addon")}
    local_ids = {addon_info(path)[0] for path in addon_dirs}
    required = {}
    for path in addon_dirs:
        for addon_id, version in required_imports(path):
            if addon_id not in local_ids and not is_builtin_dependency(addon_id) and addon_id not in EXTERNAL_REPOSITORY_DEPENDENCIES:
                if version_satisfies(version, required.get(addon_id, "")):
                    required[addon_id] = version

    archives = []
    for addon_id, minimum in required.items():
        base_url = DEPENDENCY_REPOSITORIES.get(addon_id)
        node = metadata.get(addon_id)
        if not base_url or node is None:
            raise RuntimeError(f"No trusted package source for required add-on {addon_id}")
        version = node.get("version", "")
        if not version_satisfies(version, minimum):
            raise RuntimeError(f"{addon_id} requires >= {minimum}, repository offers {version}")
        # IDs and versions become filesystem paths as well as URL segments.
        if not re.fullmatch(r"[a-zA-Z0-9._-]+", addon_id) or not re.fullmatch(r"[a-zA-Z0-9._+-]+", version):
            raise RuntimeError("Unsafe repository package identity")
        name = f"{addon_id}-{version}.zip"
        target = DIST / name
        temporary = target.with_suffix(".zip.part")
        url = base_url + urllib.parse.quote(addon_id) + "/" + urllib.parse.quote(name)
        try:
            with urllib.request.urlopen(url, timeout=60) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output)
            validate_zip(temporary)
            with zipfile.ZipFile(temporary) as archive:
                manifest = ET.fromstring(archive.read(f"{addon_id}/addon.xml"))
            if manifest.get("id") != addon_id or manifest.get("version") != version:
                raise RuntimeError(f"Downloaded package identity does not match {name}")
            temporary.replace(target)
        finally:
            if temporary.exists():
                temporary.unlink()
        archives.append(target)
    return archives


def validate_dependency_resolution(addon_dirs: list[Path], metadata_path: Path, zip_paths: list[Path]) -> None:
    root = ET.parse(metadata_path).getroot()
    metadata_versions = {
        node.attrib["id"]: node.attrib.get("version", "")
        for node in root
        if node.tag == "addon" and "id" in node.attrib
    }
    local_versions = dict(addon_info(addon_dir) for addon_dir in addon_dirs if addon_dir.exists())
    zipped_ids = {zip_path.name.rsplit("-", 1)[0] for zip_path in zip_paths}

    for addon_id in local_versions:
        if addon_id not in metadata_versions:
            raise RuntimeError(f"{metadata_path.name} is missing local add-on {addon_id}")
        if addon_id not in zipped_ids:
            raise RuntimeError(f"release upload is missing zip for local add-on {addon_id}")

    for addon_dir in addon_dirs:
        if not addon_dir.exists():
            continue

        addon_id, _ = addon_info(addon_dir)
        for dependency_id, dependency_version in required_imports(addon_dir):
            if is_builtin_dependency(dependency_id) or dependency_id in EXTERNAL_REPOSITORY_DEPENDENCIES:
                continue

            actual_version = metadata_versions.get(dependency_id)
            if actual_version is None:
                raise RuntimeError(
                    f"{addon_id} requires {dependency_id}, but it is missing from {metadata_path.name}"
                )
            if dependency_id not in zipped_ids:
                raise RuntimeError(
                    f"{addon_id} requires {dependency_id}, but no {dependency_id} zip is included"
                )
            if not version_satisfies(actual_version, dependency_version):
                raise RuntimeError(
                    f"{addon_id} requires {dependency_id} >= {dependency_version}, "
                    f"but {metadata_path.name} contains {actual_version}"
                )


def copy_for_upload(zip_paths: list[Path], metadata_path: Path) -> Path:
    if UPLOAD_DIR.exists():
        safe_rmtree(UPLOAD_DIR, DIST)
    UPLOAD_DIR.mkdir(parents=True)

    shutil.copy2(metadata_path, UPLOAD_DIR / "addons.xml")
    shutil.copy2(DIST / "addons.xml.md5", UPLOAD_DIR / "addons.xml.md5")

    for zip_path in zip_paths:
        addon_id = zip_path.name.rsplit("-", 1)[0]
        target_dir = UPLOAD_DIR / addon_id
        target_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(zip_path, target_dir / zip_path.name)

    _, skin_version = addon_info(ROOT / "skin.xvault.liquid")
    upload_zip = DIST / f"xvault-repo-upload-{skin_version}.zip"
    if upload_zip.exists():
        upload_zip.unlink()
    with zipfile.ZipFile(upload_zip, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(UPLOAD_DIR.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(UPLOAD_DIR))

    return upload_zip


def validate_zip(zip_path: Path) -> None:
    with zipfile.ZipFile(zip_path) as archive:
        corrupt = archive.testzip()
        if corrupt:
            raise RuntimeError(f"{zip_path.name} contains corrupt member {corrupt}")
        bad = [name for name in archive.namelist() if "__pycache__" in name or name.endswith(".pyc")]
        if bad:
            raise RuntimeError(f"{zip_path.name} contains Python cache files: {bad[:3]}")

        if zip_path.name.startswith("skin.xvault.liquid-"):
            prefix = "skin.xvault.liquid/"
            manifest = ET.fromstring(archive.read(prefix + "addon.xml"))
            for dependency in manifest.findall("requires/import"):
                if dependency.attrib["addon"] == "service.xvault.liquid.promos":
                    raise RuntimeError("Standalone skin ZIP must not require the companion add-on")
            for extension in manifest.findall("extension"):
                library = extension.get("library")
                if library and prefix + library not in archive.namelist():
                    raise RuntimeError(f"Missing skin entry point: {library}")
            embedded = archive.read(prefix + "resources/lib/promos.py")
            source = ROOT / "service.xvault.liquid.promos" / "service.py"
            if embedded != source.read_bytes():
                raise RuntimeError("Bundled promo service does not match companion source")


def main() -> None:
    DIST.mkdir(exist_ok=True)
    addon_dirs = [
        ROOT / "repository.xvault",
        ROOT / "service.xvault.liquid.promos",
        ROOT / "skin.xvault.liquid",
    ]
    addon_zips = [build_addon_zip(path) for path in addon_dirs if path.exists()]
    metadata_path = write_repository_metadata(addon_dirs)
    zip_paths = addon_zips + fetch_dependency_zips(addon_dirs, metadata_path)
    for zip_path in zip_paths:
        validate_zip(zip_path)

    validate_dependency_resolution(addon_dirs, metadata_path, zip_paths)
    upload_zip = copy_for_upload(zip_paths, metadata_path)

    for path in zip_paths + [metadata_path, DIST / "addons.xml.md5", upload_zip]:
        print(path)


if __name__ == "__main__":
    main()
