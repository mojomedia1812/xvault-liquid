from copy import deepcopy
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
XML = ROOT / "skin.xvault.liquid/xml"
DEFINITIONS = {
    node.get("name"): node
    for node in ET.parse(XML / "Includes_Liquid.xml").getroot().findall("include")
    if node.get("name")
}


def expanded_window(name):
    root = ET.parse(XML / name).getroot()

    def expand(parent):
        for child in list(parent):
            name = child.get("content") or (child.text or "").strip()
            if child.tag == "include" and name in DEFINITIONS:
                position = list(parent).index(child)
                parent.remove(child)
                definition = DEFINITIONS[name]
                parameters = {param.get("name"): param.text or "" for param in definition.findall("param")}
                parameters.update({param.get("name"): param.get("value", param.text or "") for param in child.findall("param")})
                nodes = definition.find("definition")
                for offset, replacement in enumerate(nodes if nodes is not None else definition):
                    replacement = deepcopy(replacement)
                    for node in replacement.iter():
                        for key, value in parameters.items():
                            if node.text:
                                node.text = node.text.replace(f"$PARAM[{key}]", value)
                            node.attrib = {attr: text.replace(f"$PARAM[{key}]", value) for attr, text in node.attrib.items()}
                    parent.insert(position + offset, replacement)
            else:
                expand(child)

    for _ in range(8):
        expand(root)
    return root
