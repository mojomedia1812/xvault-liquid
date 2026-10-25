import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("required_xvault_build", ROOT / "tools/build_release.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)
VERSION = "2026.10.24.1"


class RequiredXvaultTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.skin = self.root / "skin.xvault.liquid"
        self.skin.mkdir()
        (self.skin / "addon.xml").write_text(
            f'<addon id="skin.xvault.liquid" version="0.2.1"><requires><import addon="plugin.video.xvault" version="{VERSION}"/></requires></addon>'
        )
        self.metadata = self.root / "addons.xml"
        self.metadata.write_text(
            f'<addons><addon id="plugin.video.xvault" version="{VERSION}"/><addon id="skin.xvault.liquid" version="0.2.1"/></addons>'
        )
        self.patch_dist = patch.object(build, "DIST", self.root)
        self.patch_dist.start()
        self.addCleanup(self.patch_dist.stop)

    def package(self, version=VERSION):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("plugin.video.xvault/addon.xml", f'<addon id="plugin.video.xvault" version="{version}"/>')
        return buffer.getvalue()

    def test_required_package_is_downloaded_from_official_https_and_bundled(self):
        payload = self.package()
        with patch.object(build.urllib.request, "urlopen", return_value=io.BytesIO(payload)) as request:
            paths = build.fetch_dependency_zips([self.skin], self.metadata)
        self.assertEqual(paths[0].read_bytes(), payload)
        request.assert_called_once_with(f"https://xvault.repowork.de/plugin.video.xvault/plugin.video.xvault-{VERSION}.zip", timeout=60)
        with patch.object(build, "UPLOAD_DIR", self.root / "upload"), patch.object(build, "ROOT", self.root):
            (self.root / "addons.xml.md5").write_text("checksum")
            upload = build.copy_for_upload(paths, self.metadata)
            with zipfile.ZipFile(upload) as archive:
                self.assertEqual(archive.read(f"plugin.video.xvault/{paths[0].name}"), payload)

    def test_wrong_package_version_is_rejected_without_promoting_download(self):
        with patch.object(build.urllib.request, "urlopen", return_value=io.BytesIO(self.package("1.0.0"))):
            with self.assertRaisesRegex(RuntimeError, "identity does not match"):
                build.fetch_dependency_zips([self.skin], self.metadata)
        self.assertFalse(list(self.root.glob("*.zip*")))

    def test_corrupt_package_is_rejected_and_temporary_file_removed(self):
        with patch.object(build.urllib.request, "urlopen", return_value=io.BytesIO(b"not a ZIP")):
            with self.assertRaises(zipfile.BadZipFile):
                build.fetch_dependency_zips([self.skin], self.metadata)
        self.assertFalse(list(self.root.glob("*.part")))

    def test_failed_download_does_not_replace_existing_package(self):
        target = self.root / f"plugin.video.xvault-{VERSION}.zip"
        target.write_bytes(self.package())
        previous = target.read_bytes()
        with patch.object(build.urllib.request, "urlopen", side_effect=OSError("offline")):
            with self.assertRaises(OSError):
                build.fetch_dependency_zips([self.skin], self.metadata)
        self.assertEqual(target.read_bytes(), previous)

    def test_metadata_alone_is_not_sufficient_without_dependency_zip(self):
        with self.assertRaisesRegex(RuntimeError, "no plugin.video.xvault zip"):
            build.validate_dependency_resolution([self.skin], self.metadata, [self.root / "skin.xvault.liquid-0.2.1.zip"])

    def test_outdated_repository_package_fails_before_downloading(self):
        self.metadata.write_text('<addons><addon id="plugin.video.xvault" version="2026.09.23.3"/></addons>')
        with patch.object(build.urllib.request, "urlopen") as request:
            with self.assertRaisesRegex(RuntimeError, "requires >="):
                build.fetch_dependency_zips([self.skin], self.metadata)
            request.assert_not_called()

    def test_repository_refresh_replaces_stale_cached_metadata(self):
        cache = self.root / "cached.xml"
        cache.write_text('<addons><addon id="plugin.video.xvault" version="1.0"/></addons>')
        live = self.metadata.read_bytes()
        with patch.object(build, "REMOTE_ADDONS_XML", cache), patch.object(build.urllib.request, "urlopen", return_value=io.BytesIO(live)):
            result = build.write_repository_metadata([self.skin])
        self.assertEqual(ET.parse(result).find("addon[@id='plugin.video.xvault']").get("version"), VERSION)

    def test_repository_bootstrap_uses_current_https_endpoints(self):
        root = ET.parse(ROOT / "repository.xvault/addon.xml")
        directory = root.find("extension[@point='xbmc.addon.repository']/dir")
        self.assertEqual(directory.findtext("info"), build.REMOTE_ADDONS_URL)
        self.assertEqual(directory.findtext("datadir"), "https://xvault.repowork.de/")
