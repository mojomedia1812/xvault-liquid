# Dependencies

## Required

- Kodi with `xbmc.gui` 5.18.0 or compatible.
- `resource.images.weathericons.default` >= 1.0.0, shipped with standard Kodi installations and available through Kodi's official repository.
- Kodi Python runtime `xbmc.python` 3.0.0.
The skin ZIP embeds the promo code from `service.xvault.liquid.promos/service.py` and starts it through its own `xbmc.service` extension. Direct ZIP installation does not require the xVAULT repository or a separately installed companion add-on. Kodi resolves the declared Python, GUI and weather-icon requirements using its installed components or official repository. It cannot discover arbitrary dependency ZIPs next to the selected ZIP.

The separate companion remains available for existing installations. If it is enabled, the embedded launcher delegates rotation to it; Spotlight actions always use the bundled code. Optional add-ons are not required for ZIP installation.

## Optional

- `plugin.video.xvault`.
- `script.embuary.info`, `script.globalsearch`, `plugin.video.youtube`, `plugin.library.node.editor`, `script.image.resource.select`, and optional image resource add-ons exposed by individual skin actions.

The video add-on is intentionally optional. If it is installed, clicking the Spotlight card opens the matching xVAULT TV show season page. If it is not installed, the Spotlight click falls back to a matching local Kodi library entry when one exists.

Optional add-ons are not forced during skin installation; the skin exposes install/enable actions for them where they are used.

## Runtime Data

Promo images and metadata are stored in `special://profile/addon_data/skin.xvault.liquid/promos`, outside the replaceable add-on folder, with movies isolated in `movies/`. Failed downloads keep the last working cache. Fallback artwork remains inside the skin. Downloads are not bundled into release ZIPs or committed. Existing companion installations should also be updated to 0.2.0 for focus-aware movie and series rotation.
