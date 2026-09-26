# Dependencies

## Required

- Kodi with `xbmc.gui` 5.18.0 or compatible.
- `resource.images.weathericons.default`, resolved through Kodi's official repository.
- Kodi Python runtime `xbmc.python` 3.0.0.
- `service.xvault.liquid.promos` 0.1.7.

The skin declares `service.xvault.liquid.promos` and `resource.images.weathericons.default` as required add-ons. Kodi can install them automatically when the xVAULT repository and the official Kodi repository are enabled.

## Optional

- `plugin.video.xvault`.
- `script.embuary.info`, `script.globalsearch`, `plugin.video.youtube`, `plugin.library.node.editor`, `script.image.resource.select`, and optional image resource add-ons exposed by individual skin actions.

The video add-on is intentionally optional. If it is installed, clicking the Spotlight card opens the matching xVAULT TV show season page. If it is not installed, the Spotlight click falls back to a matching local Kodi library entry when one exists.

Optional add-ons are not forced during skin installation; the skin exposes install/enable actions for them where they are used.

## Runtime Data

Promo images and series metadata are fetched at runtime and stored locally inside the skin media cache. These downloaded images are not bundled into release ZIPs or committed to the project.
