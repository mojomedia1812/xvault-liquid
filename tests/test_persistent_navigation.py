import unittest
import xml.etree.ElementTree as ET

from liquid_xml import XML, expanded_window


class PersistentNavigationTests(unittest.TestCase):
    INSET_WINDOWS = (
        "Home", "Settings", "SettingsCategory", "SkinSettings", "SettingsSystemInfo",
        "SettingsProfile", "MyPics", "MyGames", "FileManager", "EventLog", "MyPlaylist",
        "MyMusicPlaylistEditor", "MyWeather", "MyPVRChannels", "MyPVRGuide", "MyPVRProviders",
        "MyPVRRecordings", "MyPVRSearch", "MyPVRTimers", "DialogVideoInfo", "DialogAddonInfo",
        "DialogMusicInfo",
    )
    MEDIA_WINDOWS = ("MyVideoNav", "MyMusicNav", "MyFavourites", "MyPrograms", "AddonBrowser", "Custom_1100_AddonLauncher")

    def test_each_menu_has_exactly_one_persistent_rail(self):
        for name in self.INSET_WINDOWS + self.MEDIA_WINDOWS:
            with self.subTest(window=name):
                root = expanded_window(name + ".xml")
                self.assertEqual(len(root.findall(".//control[@id='9300']")), 1)
                for control_id in range(9301, 9308):
                    self.assertEqual(len(root.findall(f".//control[@id='{control_id}']")), 1)
                rail = root.find(".//control[@id='9300']")
                self.assertIsNone(rail.find("visible"))
                self.assertNotIn("$PARAM", ET.tostring(rail, encoding="unicode"))

    def test_legacy_menu_content_reserves_sidebar_width(self):
        for name in self.INSET_WINDOWS:
            with self.subTest(window=name):
                root = ET.parse(XML / (name + ".xml"))
                content = root.find("./controls/control[@id='9320']")
                self.assertEqual(content.findtext("left"), "92")
                self.assertEqual(content.findtext("right"), "0")
                self.assertEqual(content.findtext("onleft"), "9300")

    def test_home_shelf_does_not_collide_with_navigation(self):
        root = expanded_window("Home.xml")
        ids = [node.get("id") for node in root.findall(".//control") if node.get("id")]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertIsNotNone(root.find(".//control[@id='9350']/content"))
        self.assertEqual(root.findtext(".//control[@id='9100']/onleft"), "9300")
        self.assertEqual(root.findtext(".//control[@id='9000']/onleft"), "9300")

    def test_settings_category_and_file_manager_have_keyboard_entry_routes(self):
        settings = expanded_window("SettingsCategory.xml")
        self.assertEqual(settings.findtext(".//control[@id='3']/onleft"), "9300")
        for name in ("SkinSettings", "SettingsProfile", "SettingsSystemInfo"):
            root = expanded_window(name + ".xml")
            self.assertEqual(root.findtext(".//control[@id='9000']/onleft"), "9300")
        files = ET.parse(XML / "FileManager.xml")
        self.assertEqual(files.find(".//include[@content='FileManagerPanel']/param[@name='onleft_id']").get("value"), "9300")

    def test_fullscreen_playback_is_not_covered_by_menu_navigation(self):
        for name in ("VideoFullScreen", "MusicVisualisation", "SlideShow"):
            self.assertNotIn("LiquidNavigationRail", (XML / (name + ".xml")).read_text(encoding="utf-8"))

    def test_each_navigation_button_has_its_own_native_return_route(self):
        root = expanded_window("SettingsSystemInfo.xml")
        for control_id in range(9301, 9308):
            routes = root.findall(f".//control[@id='{control_id}']/onright")
            self.assertTrue(any(route.text == "95" for route in routes))
            self.assertNotIn("$PARAM", "".join(ET.tostring(route, encoding="unicode") for route in routes))
