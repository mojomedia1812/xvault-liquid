import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class StandaloneZipTests(unittest.TestCase):
    def test_zip_contains_service_and_only_kodi_dependencies(self):
        build = load_module("build_release", ROOT / "tools/build_release.py")
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(build, "DIST", Path(directory)):
                output = build.build_addon_zip(ROOT / "skin.xvault.liquid")
                build.validate_zip(output)
                with zipfile.ZipFile(output) as archive:
                    manifest = ET.fromstring(archive.read("skin.xvault.liquid/addon.xml"))
                    dependencies = {node.get("addon") for node in manifest.findall("requires/import")}
                    self.assertEqual(dependencies, {
                        "xbmc.gui", "xbmc.python", "resource.images.weathericons.default",
                    })
                    self.assertIsNotNone(manifest.find("extension[@point='xbmc.service']"))

    def test_launcher_without_companion_runs_bundled_code(self):
        launcher = load_module("skin_launcher", ROOT / "skin.xvault.liquid/service.py")
        kodi = types.SimpleNamespace(getCondVisibility=lambda _: False)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / "resources/lib/promos.py"
            script.parent.mkdir(parents=True)
            script.touch()
            with patch.dict(sys.modules, {"xbmc": kodi}), patch.object(sys, "argv", ["service.py"]), patch.object(launcher, "__file__", str(root / "service.py")), patch.object(launcher.runpy, "run_path") as run:
                launcher.main()
                run.assert_called_once_with(str(script), run_name="__main__")

    def test_legacy_companion_does_not_duplicate_rotation(self):
        launcher = load_module("skin_launcher", ROOT / "skin.xvault.liquid/service.py")
        kodi = types.SimpleNamespace(getCondVisibility=lambda _: True)
        with patch.dict(sys.modules, {"xbmc": kodi}), patch.object(sys, "argv", ["service.py"]), patch.object(launcher.runpy, "run_path") as run:
            launcher.main()
            run.assert_not_called()

    def test_spotlight_still_runs_when_companion_enabled(self):
        launcher = load_module("skin_launcher", ROOT / "skin.xvault.liquid/service.py")
        kodi = types.SimpleNamespace(getCondVisibility=lambda _: True)
        with patch.dict(sys.modules, {"xbmc": kodi}), patch.object(sys, "argv", ["service.py", "--open-spotlight"]), patch.object(launcher.runpy, "run_path") as run:
            launcher.main()
            run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
