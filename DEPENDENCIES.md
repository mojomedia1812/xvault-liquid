# Dependencies

## Required

- Kodi with `xbmc.gui` 5.18.0 or compatible.
- Kodi Python runtime `xbmc.python` 3.0.0.
- `service.xvault.liquid.promos` 0.1.7.

The skin declares `service.xvault.liquid.promos` as a required add-on, so Kodi can install it automatically when both add-ons are available through the same repository metadata.

## Optional

- `plugin.video.xvault`.

The video add-on is intentionally optional. If it is installed, clicking the Spotlight card opens the matching xVAULT TV show season page. If it is not installed, the Spotlight click falls back to a matching local Kodi library entry when one exists.

## Runtime Data

Promo images and series metadata are fetched at runtime and stored locally inside the skin media cache. These downloaded images are not bundled into release ZIPs or committed to the project.
