# Dependencies

## Required

- Kodi with `xbmc.gui` 5.18.0 or compatible.
- `resource.images.weathericons.default` >= 1.0.0, shipped with standard Kodi installations and available through Kodi's official repository.
- Kodi Python runtime `xbmc.python` 3.0.0.
- `plugin.video.xvault` >= `2026.10.24.1`, required since skin 0.2.1. Kodi installs a missing copy or upgrades an older copy through the enabled xVAULT repository. A sufficient installed version is reused.

Before installing the skin ZIP on a fresh system, install `repository.xvault-1.0.3.zip` once and allow Kodi to refresh it. Its metadata and packages use `https://xvault.repowork.de/`. Both this repository and Kodi's official repository must be enabled and reachable. Kodi resolves dependencies before extracting the skin: neither a service inside the skin nor dependency ZIPs next to it can bootstrap an unknown repository at that stage. Without the repository (or a sufficient installed xVAULT Video), native ZIP installation cannot resolve the new requirement.

The skin ZIP embeds the promo code from `service.xvault.liquid.promos/service.py` and starts it through its own `xbmc.service` extension. A separately installed companion add-on is not required. Kodi resolves the declared Python, GUI and weather-icon requirements using its installed components or official repository.

The separate companion remains available for existing installations. If it is enabled, the embedded launcher delegates rotation to it; Spotlight actions always use the bundled code. Optional add-ons are not required for ZIP installation.

## Optional

- `script.embuary.info`, `script.globalsearch`, `plugin.video.youtube`, `plugin.library.node.editor`, `script.image.resource.select`, and optional image resource add-ons exposed by individual skin actions.

The video add-on is required; other optional integrations remain optional. The promo code retains local-library fallbacks for development or unavailable integrations at runtime.

Optional add-ons are not forced during skin installation; the skin exposes install/enable actions for them where they are used.

## Release Validation

The build refreshes official xVAULT metadata (falling back to previously fetched metadata if unavailable), downloads the required video package over HTTPS, validates ZIP integrity and exact manifest identity/version, and includes it in the repository upload bundle. Missing non-Kodi required packages now fail validation even when they are not maintained in this source tree. Uploading the bundle to the repository host is a separate deployment step.

## Runtime Data

Promo images and metadata are stored in `special://profile/addon_data/skin.xvault.liquid/promos`, outside the replaceable add-on folder, with movies isolated in `movies/`. Failed downloads keep the last working cache. Fallback artwork remains inside the skin. Downloads are not bundled into release ZIPs or committed. Existing companion installations should also be updated to 0.2.0 for focus-aware movie and series rotation.
