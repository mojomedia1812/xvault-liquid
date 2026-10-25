import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("promos", ROOT / "service.xvault.liquid.promos/service.py")
promos = importlib.util.module_from_spec(spec)
spec.loader.exec_module(promos)


class PromoCacheTests(unittest.TestCase):
    def test_kodi_cache_is_outside_addon_directory(self):
        with patch.object(promos, "IS_KODI", True), patch.object(promos, "_translate_kodi_path", return_value="/profile/promos") as translate:
            self.assertEqual(promos._promo_dir(), Path("/profile/promos"))
            translate.assert_called_once_with("special://profile/addon_data/skin.xvault.liquid/promos")

    def test_fresh_stamp_does_not_hide_missing_images(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".xvault-promos-updated").touch()
            with patch.object(promos, "_promo_dir", return_value=root), patch.object(promos, "_collect_justwatch_items", return_value=[]) as collect, patch.object(promos, "_collect_tvmaze_items", return_value=[]):
                promos.update_promos()
                collect.assert_called_once()

    def test_failed_refresh_keeps_previous_images_and_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "live-old.jpg"
            image.write_bytes(b"existing image")
            manifest = root / "justwatch-promos.json"
            previous = json.dumps([{"file": image.name, "show": "Existing"}])
            manifest.write_text(previous)
            candidates = [{"show": "New", "image": "https://example.com/new.jpg"}]
            with patch.object(promos, "_promo_dir", return_value=root), patch.object(promos, "_collect_justwatch_items", return_value=candidates), patch.object(promos, "_collect_tvmaze_items", return_value=[]), patch.object(promos, "_download", return_value=False):
                self.assertEqual(promos.update_promos(force=True), 0)
            self.assertEqual(image.read_bytes(), b"existing image")
            self.assertEqual(manifest.read_text(), previous)

    def test_fallbacks_stay_in_skin_not_userdata(self):
        with patch.object(promos, "_promo_dir", return_value=Path("/cache")), patch.object(promos, "_skin_root", return_value=Path("/skin")), patch.object(promos, "_load_live_items", return_value=[]), patch.object(promos, "_load_fallback_items", return_value=[{"image": "fallback"}]) as fallback:
            self.assertEqual(promos.load_slider_items(), [{"image": "fallback"}])
            fallback.assert_called_once_with(Path("/skin/media/promos"))
