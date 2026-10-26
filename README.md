# xVAULT Liquid

Kodi skin fuer eine tvOS-26-inspirierte Wohnzimmeroberflaeche: grosser Serien-Promo-Slider, Liquid-Glass-aehnliche Controls, Dock-Navigation und Estuary als stabile Kodi-Basis.

## Enthalten

- `skin.xvault.liquid`: installierbarer Kodi-Skin auf Basis von Estuary.
- `service.xvault.liquid.promos`: Companion-Service fuer aktuelle deutsche Film- und Serien-Backdrops und Spotlight-Metadaten.
- `repository.xvault`: Repository-Add-on fuer den ZIP-Einstieg in Kodi.
- `dist/addons.xml` und `dist/addons.xml.md5`: fertige Kodi-Repository-Metadaten.
- `dist/xvault-repo-upload-0.2.2.zip`: Upload-Paket fuer den xVAULT-Repo-Webroot ohne HTML/Pages, einschliesslich des geprueften offiziellen xVAULT-Video-ZIPs.

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

### Aus ZIP installieren

1. In Kodi: Add-ons -> Aus ZIP-Datei installieren.
2. Einmalig `dist/repository.xvault-1.0.3.zip` installieren oder ein vorhandenes xVAULT Repository darauf aktualisieren. Es verwendet `https://xvault.repowork.de/`.
3. Repository-Aktualisierung abwarten; das xVAULT Repository und das offizielle Kodi-Repository muessen aktiviert und erreichbar sein.
4. `dist/skin.xvault.liquid-0.2.2.zip` auswaehlen. Kodi installiert `plugin.video.xvault` automatisch als Pflichtabhaengigkeit, falls noch keine ausreichend aktuelle Version vorhanden ist.
5. Danach Skin wechseln: Einstellungen -> Interface -> Skin -> `xVAULT Liquid`.

Der Promo-Dienst ist im Skin-ZIP enthalten; ein separates Service-ZIP ist nicht erforderlich. Fuer die automatische xVAULT-Installation ist dagegen das xVAULT Repository erforderlich. Kodi prueft Pflichtabhaengigkeiten vor dem Auspacken des Skins und findet keine beliebigen ZIPs daneben oder darin. Ohne eingerichtetes Repository kann das Skin-ZIP xVAULT daher nicht selbst installieren. Fehlende Wettericons kann Kodi aus seinem offiziellen Repository aufloesen. Kodi muss `xbmc.gui` 5.18.0 unterstuetzen. Die Einstellung fuer unbekannte Quellen muss ZIP-Installationen erlauben.

Ein bereits installierter und aktivierter separater Promo-Service uebernimmt weiterhin die Rotation; der integrierte Dienst startet dann keine zweite Rotation. Erweiterungen wie YouTube bleiben optional; xVAULT Video ist ab Skin-Version 0.2.1 eine Pflichtabhaengigkeit.

### Aus dem xVAULT Repository

1. In Kodi: Add-ons -> Aus ZIP-Datei installieren.
2. `dist/repository.xvault-1.0.3.zip` installieren, falls das aktuelle xVAULT Repository noch nicht vorhanden ist.
3. Nach Veroeffentlichung der neuen Skin-Version auf dem Repository-Webserver aus dem xVAULT Repository `xVAULT Liquid` installieren. Kodi installiert fehlendes xVAULT Video automatisch mit.
4. Der Promo-Dienst ist bereits im Skin enthalten.
5. Kodi laedt ausserdem das Standardpaket `resource.images.weathericons.default` aus dem offiziellen Kodi-Repository nach, falls es noch fehlt.
6. Danach Skin wechseln: Einstellungen -> Interface -> Skin -> `xVAULT Liquid`.

## Abhaengigkeiten

- Kodi mit `xbmc.gui` 5.18.0 oder kompatibel.
- `xbmc.python` 3.0.0 fuer den Promo-Service.
- `resource.images.weathericons.default` fuer die Skin-Weather-Icons.
- Der Promo-Dienst wird direkt im Skin-ZIP mitgeliefert. `service.xvault.liquid.promos` ist fuer bestehende Installationen weiterhin verfuegbar, aber keine Pflichtabhaengigkeit mehr.
- `plugin.video.xvault` >= `2026.10.24.1` ist verpflichtend und wird von Kodi aus dem eingerichteten xVAULT Repository nachinstalliert bzw. bei Bedarf aktualisiert. Eine passende bereits vorhandene Version wird weiterverwendet.

Der Service aktualisiert die Promobilder im Hintergrund maximal alle 8 Stunden. Die Live-Daten stammen von `https://www.justwatch.com/de/Serien` und `https://www.justwatch.com/de/Filme`; TVmaze bleibt ausschliesslich fuer Serien als technische Reserve im Code. Heruntergeladene Promo-Bilder sind nur lokaler Runtime-Cache und werden nicht in Release-ZIPs gebuendelt.

Der Live-Cache liegt in Kodi unter `special://profile/addon_data/skin.xvault.liquid/promos` (Filme separat im Unterordner `movies`) und bleibt bei Skin-Updates erhalten. Fehlende Bilder erzwingen einen neuen Download; bei Netzwerkfehlern bleiben vorhandene Bilder erhalten. Ohne Film-Cache werden lokale Filme mit Fanart verwendet, andernfalls ein neutraler Leerzustand. Einen bereits installierten separaten Promo-Service ebenfalls auf `0.2.0` aktualisieren und Kodi danach neu starten.

## Release bauen

```powershell
python .\tools\build_release.py
```

Das erzeugt:

- `dist/repository.xvault-1.0.3.zip`
- `dist/service.xvault.liquid.promos-0.2.0.zip`
- `dist/skin.xvault.liquid-0.2.2.zip`
- `dist/plugin.video.xvault-<Repository-Version>.zip` (vom offiziellen HTTPS-Repository geladen und geprueft)
- `dist/addons.xml`
- `dist/addons.xml.md5`
- `dist/xvault-repo-upload-0.2.2.zip`

Der Build bricht ab, wenn eine lokale Pflichtabhaengigkeit zwar in einer `addon.xml` steht, aber nicht in `dist/addons.xml` oder im Upload-Paket enthalten ist.
Zusaetzlich laedt er aktuelle Repository-Metadaten und das benoetigte xVAULT-Video-Paket von `https://xvault.repowork.de/`. Bei fehlendem Paket, beschaedigtem ZIP oder abweichender Add-on-ID/Version bricht der Build ab. Er prueft ausserdem Skin-Einstiegspunkte und den eingebetteten Promo-Code. Das Upload-Paket ist fuer den Webserver bestimmt und kein direkt installierbares Kodi-Add-on-ZIP. Ein lokaler Build aktualisiert den Webserver nicht automatisch.

## Fernbedienung

- Steuerkreuz bewegt den sichtbaren Fokus; OK oeffnet den markierten Eintrag oder fuehrt dessen Aktion aus. Native Kodi-Wiedergabeaktionen bleiben erhalten.
- Home startet einmal pro Sitzung bei Serien. Hoch/Runter folgt Spotlight, vorhandener Bibliotheksreihe und Dock. Leere Reihen werden uebersprungen; am unteren Rand bleibt der Fokus im Dock.
- In vertikalen Liquid-Listen blaettern Hoch/Runter ohne Sprung in Kopfzeile oder Optionen. Links oeffnet den Fokus der Seitenleiste, Rechts die Ansichtsoptionen. An Listenenden wird nicht zum anderen Ende gesprungen.
- In Posterreihen blaettern Links/Rechts, Links am Anfang fuehrt zur Seitenleiste und Hoch zum Optionssymbol. OK am Optionssymbol oeffnet die Ansichtsoptionen.
- Zurueck in Seitenleiste oder Ansichtsoptionen bringt den Fokus zum Inhalt, ohne den Ordner zu verlassen. Zurueck im Inhalt verwendet Kodis normale Ordner-/Fensterhistorie; modale Suche und Infofenster schliessen mit Zurueck.
- Serien und Filme in der Seitenleiste oeffnen dieselben xVAULT-Kategorien wie das Home-Dock. Die Seitenleiste bleibt in den Menues sichtbar; Beschriftungen folgen ihrem Fokus.
- Info und Kontextmenue verwenden weiterhin Kodis native Belegung der jeweiligen Fernbedienung. Die Wiedergabesteuerung wird nicht durch globale Keymaps ueberschrieben.

## Entwicklung

Assets neu erzeugen:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\generate_assets.ps1
```

Live-Promos ausserhalb von Kodi vorbefuellen:

```powershell
python .\service.xvault.liquid.promos\service.py --force
```
