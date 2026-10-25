from pathlib import Path
import runpy
import sys


def main():
    import xbmc

    spotlight = "--open-spotlight" in sys.argv or "open_spotlight" in sys.argv
    if not spotlight and xbmc.getCondVisibility(
        "System.AddonIsEnabled(service.xvault.liquid.promos)"
    ):
        return

    root = Path(__file__).resolve().parent
    script = root / "resources" / "lib" / "promos.py"
    if not script.is_file():
        # Source checkouts share the companion source; release ZIPs embed it.
        script = root.parent / "service.xvault.liquid.promos" / "service.py"
    runpy.run_path(str(script), run_name="__main__")


if __name__ == "__main__":
    main()
