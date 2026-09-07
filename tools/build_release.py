from __future__ import annotations

import hashlib
import os
import shutil
import urllib.request
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
REMOTE_ADDONS_XML = DIST / "xvault-remote-addons.xml"
REMOTE_ADDONS_URL = "http://xvault.ddnss.de/addons.xml"
UPLOAD_DIR = DIST / "xvault-repo-upload"
REPO_ID = "repository.xvault"


def safe_rmtree(path: Path, allowed_parent: Path) -> None:
    resolved_path = path.resolve()
    resolved_parent = allowed_parent.resolve()
    if resolved_path == resolved_parent or resolved_parent not in resolved_path.parents:
        raise RuntimeError(f"Refusing to remove path outside {resolved_parent}: {resolved_path}")
    shutil.rmtree(resolved_path)


def addon_info(addon_dir: Path) -> tuple[str, str]:
    root = ET.parse(addon_dir / "addon.xml").getroot()
    return root.attrib["id"], root.attrib["version"]


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
    if not REMOTE_ADDONS_XML.exists():
        try:
            REMOTE_ADDONS_XML.write_bytes(urllib.request.urlopen(REMOTE_ADDONS_URL, timeout=20).read())
        except Exception:
            pass

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
        bad = [name for name in archive.namelist() if "__pycache__" in name or name.endswith(".pyc")]
        if bad:
            raise RuntimeError(f"{zip_path.name} contains Python cache files: {bad[:3]}")


def main() -> None:
    DIST.mkdir(exist_ok=True)
    addon_dirs = [
        ROOT / "repository.xvault",
        ROOT / "service.xvault.liquid.promos",
        ROOT / "skin.xvault.liquid",
    ]
    addon_zips = [build_addon_zip(path) for path in addon_dirs if path.exists()]
    zip_paths = addon_zips
    for zip_path in zip_paths:
        validate_zip(zip_path)

    metadata_path = write_repository_metadata(addon_dirs)
    upload_zip = copy_for_upload(zip_paths, metadata_path)

    for path in zip_paths + [metadata_path, DIST / "addons.xml.md5", upload_zip]:
        print(path)


if __name__ == "__main__":
    main()
