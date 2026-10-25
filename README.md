# xVAULT Liquid

Kodi skin fuer eine tvOS-26-inspirierte Wohnzimmeroberflaeche: grosser Serien-Promo-Slider, Liquid-Glass-aehnliche Controls, Dock-Navigation und Estuary als stabile Kodi-Basis.

## Enthalten

- `skin.xvault.liquid`: installierbarer Kodi-Skin auf Basis von Estuary.
- `service.xvault.liquid.promos`: Companion-Service fuer aktuelle deutsche Film- und Serien-Backdrops und Spotlight-Metadaten.
- `repository.xvault`: Repository-Add-on fuer den ZIP-Einstieg in Kodi.
- `dist/addons.xml` und `dist/addons.xml.md5`: fertige Kodi-Repository-Metadaten.
- `dist/xvault-repo-upload-0.2.0.zip`: Upload-Paket fuer den xVAULT-Repo-Webroot ohne HTML/Pages.

## Funktionen

- Liquid-Videonavigation fuer Serien, Staffeln, Episoden und Filme mit Fanart, Posterreihe und Listenansicht.
- Gemeinsame Seitenleiste und Master-Detail-Ansichten fuer Favoriten, Musik, Programme und Add-on-Verwaltung.
- Dauerhaft sichtbare linke Navigation auch auf Home, in Einstellungen samt Unterseiten, Dateimanager, Bildern, Spielen, Wiedergabelisten, Wetter und TV-Menues sowie den Medien- und Add-on-Detailansichten. Vollbild-Wiedergabe bleibt unveraendert; modale Eingabedialoge behalten ihren eigenen Fokus.
- Poster mit Bewertung, Gesehen-Markierung und Fortschritt, sofern diese Metadaten vom Anbieter oder der Bibliothek geliefert werden.
- Detailansicht mit nativer Besetzung, Staffelzugriff und unverzerrter Artwork-Vollbildansicht.
- Fokusmodus fuer einen ruhigen Hintergrund, Ansichtsoptionen als seitlicher Drawer und Suche nach installierten Anbietern.
- Add-on-Zentrale mit direkten Schnellzugriffen auf installierte Video-Add-ons.
- Synchroner Spotlight-Bereich: Hintergrundbild, Serientitel, Rang/Anbieter und Serienbeschreibung wechseln gemeinsam.
- Spotlight folgt dem Dock-Fokus: Serien zeigt Serien, Filme zeigt Filme, ohne den Bereich zu oeffnen. Beide Listen behalten ihre Position; andere Dock-Eintraege und der Wechsel zum Spotlight behalten den zuletzt gewaehlten Typ.
- Die Dock-Links Filme und Serien oeffnen direkt die entsprechenden Kategorien von `plugin.video.xvault` statt der lokalen Kodi-Bibliothek. Fuer diese beiden Links muss xVAULT Video installiert und aktiviert sein.
- Film-Spotlight oeffnet bei lokalem Bibliotheks-Fallback die Filminfo, bei JustWatch-Highlights die passende xVAULT-Filmsuche. Es startet keine Wiedergabe automatisch.
- Klickbares Spotlight: Bei installiertem `plugin.video.xvault` oeffnet xVAULT direkt die Serien-/Staffelseite zur aktuellen Spotlight-Serie.
- Fallback ohne xVAULT: Der Service sucht in der lokalen Kodi-Bibliothek nach einem passenden Serientitel.
- Fullscreen-Cover fuer Promo-Bilder: Backdrops fuellen den Screen, bleiben proportional und werden mittig gecroppt.
- Dynamisches Home-Overlay: Topbar, Spotlight, Bibliotheksreihe und Dock verwenden relative Breiten/Anker statt starrer 1920px-Werte.
- Lokale Fallback-Promos: Der Home-Screen sieht sofort gefuellt aus, auch ohne Netzwerk.

## Kodi-Installation

### Direkt aus ZIP installieren

1. In Kodi: Add-ons -> Aus ZIP-Datei installieren.
2. `dist/skin.xvault.liquid-0.2.0.zip` auswaehlen.
3. Danach Skin wechseln: Einstellungen -> Interface -> Skin -> `xVAULT Liquid`.

Der Promo-Dienst ist im Skin-ZIP enthalten. Das xVAULT Repository und ein separates Service-ZIP werden dafuer nicht benoetigt. Python und die Standard-Wettericons gehoeren zur regulaeren Kodi-Installation; fehlende Wettericons kann Kodi aus seinem offiziellen Repository aufloesen. Kodi muss `xbmc.gui` 5.18.0 unterstuetzen. Die Einstellung fuer unbekannte Quellen muss ZIP-Installationen erlauben.

Ein bereits installierter und aktivierter separater Promo-Service uebernimmt weiterhin die Rotation; der integrierte Dienst startet dann keine zweite Rotation. Optionale Erweiterungen wie xVAULT Video oder YouTube werden bei Bedarf separat installiert.

### Aus dem xVAULT Repository

1. In Kodi: Add-ons -> Aus ZIP-Datei installieren.
2. `dist/repository.xvault-1.0.2.zip` installieren, falls das xVAULT Repository noch nicht vorhanden ist.
3. Aus dem xVAULT Repository `xVAULT Liquid` installieren.
4. Der Promo-Dienst ist bereits im Skin enthalten.
5. Kodi laedt ausserdem das Standardpaket `resource.images.weathericons.default` aus dem offiziellen Kodi-Repository nach, falls es noch fehlt.
6. Danach Skin wechseln: Einstellungen -> Interface -> Skin -> `xVAULT Liquid`.

## Abhaengigkeiten

- Kodi mit `xbmc.gui` 5.18.0 oder kompatibel.
- `xbmc.python` 3.0.0 fuer den Promo-Service.
- `resource.images.weathericons.default` fuer die Skin-Weather-Icons.
- Der Promo-Dienst wird direkt im Skin-ZIP mitgeliefert. `service.xvault.liquid.promos` ist fuer bestehende Installationen weiterhin verfuegbar, aber keine Pflichtabhaengigkeit mehr.
- `plugin.video.xvault` ist optional. Es wird nicht automatisch installiert und nur genutzt, wenn es bereits vorhanden ist.

Der Service aktualisiert die Promobilder im Hintergrund maximal alle 8 Stunden. Die Live-Daten stammen von `https://www.justwatch.com/de/Serien` und `https://www.justwatch.com/de/Filme`; TVmaze bleibt ausschliesslich fuer Serien als technische Reserve im Code. Heruntergeladene Promo-Bilder sind nur lokaler Runtime-Cache und werden nicht in Release-ZIPs gebuendelt.

Der Live-Cache liegt in Kodi unter `special://profile/addon_data/skin.xvault.liquid/promos` (Filme separat im Unterordner `movies`) und bleibt bei Skin-Updates erhalten. Fehlende Bilder erzwingen einen neuen Download; bei Netzwerkfehlern bleiben vorhandene Bilder erhalten. Ohne Film-Cache werden lokale Filme mit Fanart verwendet, andernfalls ein neutraler Leerzustand. Einen bereits installierten separaten Promo-Service ebenfalls auf `0.2.0` aktualisieren und Kodi danach neu starten.

## Release bauen

```powershell
python .\tools\build_release.py
```

Das erzeugt:

- `dist/repository.xvault-1.0.2.zip`
- `dist/service.xvault.liquid.promos-0.2.0.zip`
- `dist/skin.xvault.liquid-0.2.0.zip`
- `dist/addons.xml`
- `dist/addons.xml.md5`
- `dist/xvault-repo-upload-0.2.0.zip`

Der Build bricht ab, wenn eine lokale Pflichtabhaengigkeit zwar in einer `addon.xml` steht, aber nicht in `dist/addons.xml` oder im Upload-Paket enthalten ist.
Zusaetzlich prueft er die ZIP-Integritaet, Skin-Einstiegspunkte und den eingebetteten Promo-Code. Das Upload-Paket ist fuer den Webserver bestimmt und kein direkt installierbares Kodi-Add-on-ZIP.

## Entwicklung

Assets neu erzeugen:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\generate_assets.ps1
```

Live-Promos ausserhalb von Kodi vorbefuellen:

```powershell
python .\service.xvault.liquid.promos\service.py --force
```
