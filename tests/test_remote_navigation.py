import unittest
import xml.etree.ElementTree as ET

from liquid_xml import ROOT, expanded_window


class RemoteNavigationTests(unittest.TestCase):
    def test_green_focus_palettes_and_liquid_accents_are_red(self):
        for name in ("defaults", "green", "teal", "chartreuse"):
            palette = ET.parse(ROOT / f"skin.xvault.liquid/colors/{name}.xml")
            self.assertEqual(palette.findtext("color[@name='button_focus']"), "FFB83232")
            self.assertEqual(palette.findtext("color[@name='button_alt_focus']"), "80B83232")
        root = expanded_window("MyVideoNav.xml")
        scrollbar = root.find(".//control[@id='5199']/texturesliderbarfocus")
        self.assertEqual(scrollbar.get("colordiffuse"), "ffb83232")
        row = root.find(".//control[@id='50']/focusedlayout")
        accent = next(image for image in row.findall("control") if image.findtext("width") == "3")
        self.assertEqual(accent.find("texture").get("colordiffuse"), "ffb83232")
        self.assertEqual(accent.findtext("visible"), "Control.HasFocus(50)")
        info = expanded_window("DialogVideoInfo.xml")
        border = next(image for image in info.findall(".//control[@type='image']") if image.findtext("visible") == "Control.HasFocus(138)")
        self.assertEqual(border.find("texture").get("colordiffuse"), "ffb83232")

    def test_sidebar_focus_is_red_on_every_entry(self):
        root = expanded_window("Home.xml")
        for control_id in range(9301, 9309):
            texture = root.find(f".//control[@id='{control_id}']/texturefocus")
            self.assertEqual(texture.get("colordiffuse"), "ffb83232")

    def test_focus_frames_only_highlight_the_active_container(self):
        for window, ids in (("Home.xml", (9100, 9350)), ("MyVideoNav.xml", (50, 51))):
            root = expanded_window(window)
            for control_id in ids:
                layout = root.find(f".//control[@id='{control_id}']/focusedlayout")
                self.assertIsNotNone(layout.find(f".//visible[.='Control.HasFocus({control_id})']"))

    def test_sidebar_tooltips_use_fixed_row_coordinates(self):
        root = expanded_window("Home.xml")
        order = [9301, 9308, 9302, 9303, 9304, 9305, 9306, 9307]
        for index, control_id in enumerate(order):
            groups = root.findall(".//control[@type='group']")
            tooltip = next(group for group in groups if group.findtext("visible") == f"Control.HasFocus({control_id})")
            self.assertEqual(tooltip.findtext("top"), str(178 + index * 78))
            self.assertIsNotNone(tooltip.find("control[@type='image']"))

    def test_home_starts_at_series_once_and_skips_empty_library_shelf(self):
        root = expanded_window("Home.xml")
        first = root.findall("onload")[0]
        self.assertEqual(first.text, "SetFocus(9100,0,absolute)")
        self.assertIn("liquid_home_initialized", first.get("condition"))
        dock = root.find(".//control[@id='9100']")
        self.assertEqual(dock.findtext("ondown"), "noop")
        self.assertEqual(dock.findtext("onright"), "noop")
        self.assertTrue(all("NumItems,0" in node.get("condition", "") for node in dock.findall("onup")))

    def test_sidebar_has_explicit_order_and_back_to_content_on_each_button(self):
        root = expanded_window("MyVideoNav.xml")
        order = [9301, 9308, 9302, 9303, 9304, 9305, 9306, 9307]
        for index, control_id in enumerate(order):
            button = root.find(f".//control[@id='{control_id}']")
            self.assertEqual(button.findtext("onup"), str(order[max(0, index - 1)]))
            self.assertEqual(button.findtext("ondown"), str(order[min(len(order) - 1, index + 1)]))
            self.assertTrue(button.findall("onback"))
        self.assertGreaterEqual(int(root.findtext(".//control[@id='9300']/height")), 8 * 60 + 7 * 18)

    def test_sidebar_and_dock_open_same_movie_and_series_destinations(self):
        home = expanded_window("Home.xml")
        items = home.findall(".//control[@id='9100']/content/item")
        for control_id, item in ((9308, items[0]), (9302, items[1])):
            actions = home.findall(f".//control[@id='{control_id}']/onclick")
            self.assertEqual(actions[-1].text, item.findtext("onclick"))
        icon = ROOT / "skin.xvault.liquid/media/icons/home.png"
        self.assertEqual(icon.read_bytes()[:8], b"\x89PNG\r\n\x1a\n")

    def test_vertical_lists_stay_in_content_and_right_opens_options(self):
        root = expanded_window("MyVideoNav.xml")
        view = root.find(".//control[@id='50']")
        self.assertEqual(view.findtext("onup"), "noop")
        self.assertEqual(view.findtext("ondown"), "noop")
        self.assertEqual(view.findtext("onleft"), "9300")
        self.assertEqual(view.findtext("onright"), "9000")
        poster = root.find(".//control[@id='51']")
        self.assertEqual(poster.findtext("onup"), "9203")
        self.assertEqual(poster.findtext("ondown"), "noop")

    def test_back_closes_options_from_each_individual_button(self):
        for name in ("MyVideoNav", "MyMusicNav", "MyFavourites", "MyPrograms", "AddonBrowser", "Custom_1100_AddonLauncher"):
            root = expanded_window(name + ".xml")
            options = root.find(".//control[@id='9000']")
            for button in options.findall("control"):
                if button.get("type") in ("button", "togglebutton", "radiobutton"):
                    self.assertTrue(button.findall("onback"), (name, button.get("id")))
            focus = options.find("control[@id='9401']")
            self.assertEqual(focus.get("type"), "radiobutton")
            self.assertEqual(focus.findtext("selected"), "Skin.HasSetting(liquid_focus_mode)")

    def test_detail_actions_do_not_focus_empty_cast(self):
        root = expanded_window("DialogVideoInfo.xml")
        actions = root.find(".//control[@id='5000']")
        self.assertTrue(all("Container(50).NumItems,0" in node.get("condition", "") for node in actions.findall("ondown")))
