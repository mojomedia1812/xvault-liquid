import unittest
import xml.etree.ElementTree as ET

from liquid_xml import ROOT, XML, expanded_window


class VideoNavigationTests(unittest.TestCase):
    def test_detail_description_extends_to_footer_without_progress_overlap(self):
        root = expanded_window("MyVideoNav.xml")
        detail = next(group for group in root.findall(".//control[@type='group']")
                      if group.findtext("visible") == "Control.IsVisible(50)")
        plot = detail.find("control[@type='textbox']")
        self.assertIsNone(plot.find("height"))
        self.assertEqual(plot.findtext("bottom"), "110")
        progress = next(label for label in detail.findall("control[@type='label']")
                        if "PercentPlayed" in label.findtext("label", ""))
        self.assertLessEqual(int(progress.findtext("top")) + int(progress.findtext("height")), 594)
        for height in (1080, 1200, 1440):
            plot_end = height - int(plot.findtext("bottom"))
            self.assertGreater(plot_end - int(plot.findtext("top")), 130)
            self.assertEqual(height - 86 - plot_end, 24)

    WINDOWS = (
        "MyVideoNav.xml", "MyFavourites.xml", "MyMusicNav.xml", "MyPrograms.xml",
        "AddonBrowser.xml", "Custom_1100_AddonLauncher.xml", "DialogVideoInfo.xml",
        "Custom_1107_SearchDialog.xml",
    )

    def test_shared_windows_have_unique_controls_and_valid_focus_routes(self):
        for name in self.WINDOWS:
            with self.subTest(window=name):
                root = expanded_window(name)
                controls = root.findall(".//control")
                ids = [control.get("id") for control in controls if control.get("id")]
                self.assertEqual(len(ids), len(set(ids)))
                for node in controls:
                    for direction in ("onleft", "onright", "onup", "ondown", "onback", "pagecontrol"):
                        for target in node.findall(direction):
                            if (target.text or "").isdigit():
                                guarded = target.get("condition", "").startswith(f"Control.IsVisible({target.text})")
                                self.assertTrue(target.text in ids or guarded, (name, direction, target.text))

    def test_native_media_lists_and_actor_provider_are_preserved(self):
        for name in self.WINDOWS[:5]:
            root = expanded_window(name)
            for view_id in root.findtext("views").split(","):
                view = root.find(f".//control[@id='{view_id}']")
                self.assertIsNotNone(view)
                self.assertIsNone(view.find("content"))
                self.assertEqual(view.find("itemlayout").attrib, view.find("focusedlayout").attrib)
        info = expanded_window("DialogVideoInfo.xml")
        self.assertIsNone(info.find(".//control[@id='50']/content"))
        self.assertTrue({"6", "7", "8", "10", "11", "13", "14", "15"}.issubset({n.get("id") for n in info.findall(".//control")}))

    def test_fonts_exist_and_artwork_layout_does_not_cover_footer(self):
        fonts = {node.text for node in ET.parse(XML / "Font.xml").findall(".//font/name")}
        for name in self.WINDOWS:
            for font in expanded_window(name).findall(".//font"):
                self.assertIn(font.text, fonts, (name, font.text))
        shelf = expanded_window("MyVideoNav.xml").find(".//control[@id='51']")
        top_ratio = float(shelf.findtext("top").rstrip("%")) / 100
        for height in (1080, 1200, 1440):
            self.assertLess(top_ratio * height + float(shelf.findtext("height")), height - 86)

    def test_drawers_can_be_focused_from_hidden_state(self):
        for name in self.WINDOWS[:6]:
            visible = expanded_window(name).find(".//control[@id='9000']/visible")
            self.assertEqual(visible.get("allowhiddenfocus"), "true", name)

    def test_addon_shortcuts_use_installed_provider_and_stable_layout(self):
        root = expanded_window("Custom_1100_AddonLauncher.xml")
        shortcuts = root.find(".//control[@id='9600']")
        self.assertEqual(shortcuts.findtext("content"), "addons://sources/video/")
        self.assertEqual(shortcuts.find("content").get("target"), "videos")
        self.assertEqual(shortcuts.find("content").get("sortby"), "lastused")
        self.assertEqual(shortcuts.find("content").get("sortorder"), "descending")
        self.assertEqual(shortcuts.find("itemlayout").attrib, shortcuts.find("focusedlayout").attrib)
        self.assertLess(int(shortcuts.findtext("top")) + int(shortcuts.findtext("height")), 1080 - 86)
        routes = root.findall(".//control[@id='50']/ondown")
        self.assertTrue(any(route.text == "9000" and "NumItems,0" in route.get("condition", "") for route in routes))

    def test_back_artwork_is_small_and_native_play_action_is_retained(self):
        includes = ET.parse(XML / "Includes_Liquid.xml")
        arrow = includes.find(".//include[@name='LiquidParentCardArt']/control")
        self.assertEqual(arrow.findtext("visible"), "ListItem.IsParentFolder")
        self.assertLessEqual(int(arrow.findtext("width")), 96)
        info = expanded_window("DialogVideoInfo.xml")
        play = info.find(".//control[@id='5000']/content/item")
        self.assertEqual(play.findtext("onclick"), "SendClick(8)")
        self.assertEqual(play.findtext("label"), "$VAR[LiquidPlayLabel]")

    def test_provider_season_and_episode_labels_are_not_replaced_by_series_title(self):
        includes = ET.parse(XML / "Includes_Liquid.xml")
        title = includes.find(".//variable[@name='LiquidItemTitle']")
        self.assertEqual(title.findall("value")[-1].text, "$INFO[ListItem.Label]")
        self.assertNotIn("$INFO[ListItem.Title]", [value.text for value in title.findall("value")])
        catalogue = includes.findtext(".//expression[@name='liquid_catalogue']")
        self.assertIn("!String.Contains(Container.FolderPath,plugin://plugin.video.xvault/?action=episodes&)", catalogue)

    def test_xml_and_localized_labels_are_complete(self):
        for path in XML.glob("*.xml"):
            ET.parse(path)
        for lang in ("en_gb", "de_de"):
            text = (ROOT / f"skin.xvault.liquid/language/resource.language.{lang}/strings.po").read_text(encoding="utf-8")
            for label_id in range(31800, 31827):
                self.assertEqual(text.count(f'msgctxt "#{label_id}"'), 1, (lang, label_id))
