# xVAULT Liquid

Kodi skin fuer eine tvOS-26-inspirierte Wohnzimmeroberflaeche: grosser Serien-Promo-Slider, Liquid-Glass-aehnliche Controls, Dock-Navigation und Estuary als stabile Kodi-Basis.

## Enthalten

- `skin.xvault.liquid`: installierbarer Kodi-Skin auf Basis von Estuary.
- `service.xvault.liquid.promos`: Companion-Service fuer aktuelle deutsche Serien-Backdrops und Spotlight-Metadaten.
- `repository.xvault`: Repository-Add-on fuer den ZIP-Einstieg in Kodi.
- `dist/addons.xml` und `dist/addons.xml.md5`: fertige Kodi-Repository-Metadaten.
- `dist/xvault-repo-upload-0.1.8.zip`: Upload-Paket fuer den xVAULT-Repo-Webroot ohne HTML/Pages.

## Funktionen

- Synchroner Spotlight-Bereich: Hintergrundbild, Serientitel, Rang/Anbieter und Serienbeschreibung wechseln gemeinsam.
- Klickbares Spotlight: Bei installiertem `plugin.video.xvault` oeffnet xVAULT direkt die Serien-/Staffelseite zur aktuellen Spotlight-Serie.
- Fallback ohne xVAULT: Der Service sucht in der lokalen Kodi-Bibliothek nach einem passenden Serientitel.
- Fullscreen-Cover fuer Promo-Bilder: Backdrops fuellen den Screen, bleiben proportional und werden mittig gecroppt.
- Dynamisches Home-Overlay: Topbar, Spotlight, Bibliotheksreihe und Dock verwenden relative Breiten/Anker statt starrer 1920px-Werte.
- Lokale Fallback-Promos: Der Home-Screen sieht sofort gefuellt aus, auch ohne Netzwerk.

## Kodi-Installation

### Aus dem xVAULT Repository

1. In Kodi: Add-ons -> Aus ZIP-Datei installieren.
2. `dist/repository.xvault-1.0.2.zip` installieren, falls das xVAULT Repository noch nicht vorhanden ist.
3. Aus dem xVAULT Repository `xVAULT Liquid` installieren.
4. Der Promo-Service `service.xvault.liquid.promos` wird als Skin-Abhaengigkeit automatisch mitinstalliert.
5. Kodi laedt ausserdem das Standardpaket `resource.images.weathericons.default` aus dem offiziellen Kodi-Repository nach, falls es noch fehlt.
6. Danach Skin wechseln: Einstellungen -> Interface -> Skin -> `xVAULT Liquid`.

### Manueller Test

Installiere diese beiden ZIPs nacheinander:

- `dist/service.xvault.liquid.promos-0.1.7.zip`
- `dist/skin.xvault.liquid-0.1.8.zip`

## Abhaengigkeiten

- Kodi mit `xbmc.gui` 5.18.0 oder kompatibel.
- `xbmc.python` 3.0.0 fuer den Promo-Service.
- `resource.images.weathericons.default` fuer die Skin-Weather-Icons.
- `service.xvault.liquid.promos` wird vom Skin automatisch benoetigt und mitinstalliert.
- `plugin.video.xvault` ist optional. Es wird nicht automatisch installiert und nur genutzt, wenn es bereits vorhanden ist.

Der Service aktualisiert die Promobilder maximal alle 8 Stunden. Die Live-Daten stammen bevorzugt von `https://www.justwatch.com/de/Serien`; TVmaze bleibt als technische Reserve im Code. Heruntergeladene Promo-Bilder sind nur lokaler Runtime-Cache und werden nicht in Release-ZIPs gebuendelt.

## Release bauen

```powershell
python .\tools\build_release.py
```

Das erzeugt:

- `dist/repository.xvault-1.0.2.zip`
- `dist/service.xvault.liquid.promos-0.1.7.zip`
- `dist/skin.xvault.liquid-0.1.8.zip`
- `dist/addons.xml`
- `dist/addons.xml.md5`
- `dist/xvault-repo-upload-0.1.8.zip`

Der Build bricht ab, wenn eine lokale Pflichtabhaengigkeit zwar in einer `addon.xml` steht, aber nicht in `dist/addons.xml` oder im Upload-Paket enthalten ist.

## Entwicklung

Assets neu erzeugen:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\generate_assets.ps1
```

Live-Promos ausserhalb von Kodi vorbefuellen:

```powershell
python .\service.xvault.liquid.promos\service.py --force
```
