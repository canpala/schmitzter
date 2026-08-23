# Schmitzter

Ein selbstgebautes Hitster-Musik-Ratespiel: physische Karten mit QR-Code,
die per In-App-Kamera-Scan erkannt werden. Die App spielt einen kurzen,
werbefreien Songausschnitt ab dem Refrain ab, ohne vorher Titel, Interpret
oder Songbild zu verraten. Man kann jederzeit während der Wiedergabe
aufdecken (Titel/Interpret/Jahr), der Ausschnitt läuft dabei einfach bis
zum Ende weiter.

Reines privates Party-/Geschenkprojekt, kein kommerzielles Produkt.

## Wie es funktioniert

1. Startseite zeigt das Schmitzter-Logo und einen "📷 QR-Code scannen"-Button.
2. Antippen → Kamera öffnet sich in der App (kein Umweg über die
   System-Kamera-App), QR-Code der physischen Karte in den Rahmen halten.
3. Karte erkannt → nur ein Play-Button erscheint, keine Songinfos.
4. Antippen → ein lokaler Audio-Clip (`audio/<id>.mp3`, schon auf den
   Refrain zugeschnitten) spielt ab.
5. Während der Wiedergabe kann jederzeit auf "🔍 Aufdecken" getippt werden
   → zeigt Titel, Interpret, Jahr. Der Ausschnitt läuft einfach bis zu
   seinem Ende weiter.
6. "➡️ Nächste Karte" → Kamera öffnet sich direkt wieder für die nächste
   Karte.

Der QR-Scan läuft komplett clientseitig über die Kamera und die
Bibliothek [jsQR](https://github.com/cozmo/jsQR) (lokal eingebunden,
keine Verbindung zu Drittanbietern nötig).

**Wichtig:** Kamera-Zugriff (`getUserMedia`) funktioniert im Browser nur
über eine sichere Verbindung – also HTTPS oder `localhost`. Über eine
rohe LAN-IP oder einen `.local`-Hostnamen lässt sich der QR-Scanner
**nicht** testen (siehe Abschnitt "Hosten" unten für Details, wie man das
trotzdem lokal testet). Die Audio-Wiedergabe selbst hat diese
Einschränkung nicht.

### Warum lokale Audio-Clips statt YouTube-Embed?

Ein früherer Ansatz hat den Song live per YouTube-IFrame-Player
eingebettet. Das brachte mehrere Probleme mit sich, die für ein
zuverlässiges Partyspiel störend waren:

- YouTube kann vor dem Video Werbung einblenden (abhängig von der
  Monetarisierung des jeweiligen Videos) – nicht kontrollierbar über die
  Embed-Parameter.
- Manche Videos sind in bestimmten Ländern für Embeds gesperrt.
- YouTube weist Embed-Anfragen von einer rohen LAN-IP-Adresse teils
  pauschal als "Embedding gesperrt" zurück.
- iOS Safari blockiert Ton-Autoplay in frisch erzeugten Cross-Origin-
  iFrames, was einen Vorlade-Trick nötig machte.

Deshalb werden die Songausschnitte jetzt einmalig per
`scripts/extract_clips.py` aus YouTube extrahiert und als kleine MP3-
Dateien lokal unter `audio/` abgelegt. Die App spielt sie ganz normal
per HTML5 `<audio>` ab – kein YouTube-Zugriff mehr zur Laufzeit, keine
Werbung, keine Länder-Sperren, keine iFrame-Eigenheiten.

**Bewusste Abwägung:** Dadurch landen kurze (ca. 20–25 Sekunden)
Ausschnitte urheberrechtlich geschützter Musik als Dateien im
(öffentlichen) GitHub-Repository. Für ein kleines privates
Geschenkprojekt ist das Risiko sehr gering, aber es ist bewusst so
entschieden worden statt versehentlich zu passieren.

## Für andere Personen einrichten (z. B. am Handy anderer Mitspieler)

Die App braucht keinen Account und keine Installation aus einem App-Store
– sie läuft direkt im Browser unter `https://canpala.github.io/schmitzter/`.
Damit sie sich trotzdem wie eine "echte" App anfühlt (Icon auf dem
Startbildschirm, kein URL-Eintippen nötig), gibt es:

- Ein Web-App-Manifest (`manifest.json`) + Icons (`icons/`), damit
  Android-Chrome "Zum Startbildschirm hinzufügen" anbietet und die App
  dann mit eigenem Icon und ohne Browser-Adressleiste startet.
- Einen Start-QR-Code (`output/qr-start.png`, wird von
  `scripts/generate_qr.py` miterzeugt), der nur die Startseite öffnet
  (ohne Song-ID) – zum einmaligen Öffnen mit der normalen Handykamera.
- Eine ausdruckbare Anleitung (`output/anleitung.pdf`, per
  `scripts/generate_instructions_pdf.py`) mit großer Schrift: Start-QR-Code
  scannen → "Zum Startbildschirm hinzufügen" → fertig, plus eine kurze
  Spielanleitung. Praktisch, um sie ausgedruckt neben die Spielkarten zu
  legen.

```bash
python3 scripts/generate_instructions_pdf.py
```

## Projektstruktur

```
├── index.html / app.js / styles.css   Die Web-App
├── manifest.json                      Web-App-Manifest (Startbildschirm-Icon)
├── icons/                             App-Icons (192px/512px)
├── songs.json                         Zentrale Songdatenbank
├── audio/                             Songausschnitte als MP3 (<id>.mp3)
├── vendor/jsQR.min.js                 QR-Decoder-Bibliothek (lokal, kein CDN)
├── scripts/
│   ├── generate_qr.py                 Erzeugt QR-Codes aus songs.json + Start-QR
│   ├── generate_cards_pdf.py          Baut das druckfertige Karten-PDF
│   ├── extract_clips.py               Extrahiert Audio-Clips aus YouTube
│   ├── generate_instructions_pdf.py   Baut die Einrichtungs-Anleitung (PDF)
│   └── requirements.txt
└── output/                            Generierte QR-Codes + PDFs (nicht eingecheckt)
```

## Neue Songs hinzufügen

1. In `songs.json` einen neuen Eintrag ergänzen:

   ```json
   {
     "id": "006",
     "youtubeId": "<YouTube-Video-ID>",
     "title": "Songtitel",
     "artist": "Interpret",
     "year": 2020,
     "chorusStart": 60
   }
   ```

   - `id`: fortlaufende, eigene Kennung (erscheint in der URL/im QR-Code –
     **nicht** die YouTube-ID, damit die URL keine Songinfos verrät).
   - `youtubeId`: aus der YouTube-URL (`youtube.com/watch?v=<hier>`), wird
     nur einmalig zur Audio-Extraktion gebraucht, nicht mehr zur Laufzeit.
   - `chorusStart`: Sekunde, ab der der Refrain beginnt – manuell im Video
     nachschauen und eintragen.

2. Audio-Clip extrahieren, QR-Code und PDF neu generieren (siehe unten).

## Einmalig einrichten

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt
```

Installiert `qrcode`, `fpdf2`, `yt-dlp` und `imageio-ffmpeg` (liefert ein
fertiges ffmpeg-Binary mit, kein Homebrew/System-ffmpeg nötig).

## Audio-Clips extrahieren

```bash
python3 scripts/extract_clips.py
```

Lädt für jeden Eintrag in `songs.json` einen ca. 22-sekündigen Ausschnitt
ab `chorusStart` von YouTube, schneidet ihn mit ffmpeg zurecht (inkl.
kurzem Fade-out am Ende) und speichert ihn als `audio/<id>.mp3`.

**Hinweis:** YouTube ändert regelmäßig seine Anti-Bot-Maßnahmen, wodurch
`yt-dlp` gelegentlich kaputtgeht. Falls der Download mit einem Fehler wie
"ffmpeg exited with code 8" oder "The page needs to be reloaded"
fehlschlägt: zuerst `pip install -U yt-dlp` versuchen (neue Version), das
behebt die meisten Faelle. Der Extraktor nutzt aktuell bewusst den
`android`-Player-Client (`--extractor-args`), da der `web`-Client von
YouTube derzeit für Downloads blockiert wird – falls das in einigen
Monaten wieder anders ist, in `scripts/extract_clips.py` nachschauen.

Die Clip-Länge (Standard 22 Sekunden) lässt sich über `CLIP_DURATION_SEC`
am Anfang des Skripts anpassen – sollte grob zur bisherigen Spiellänge
passen.

## QR-Codes generieren

```bash
python3 scripts/generate_qr.py
```

Erzeugt für jeden Eintrag in `songs.json` ein PNG in `output/qr-codes/`,
das auf `https://canpala.github.io/schmitzter/?id=<id>` zeigt. Falls die
App woanders gehostet wird (lokal, Netlify, …), `BASE_URL` am Anfang von
`scripts/generate_qr.py` anpassen.

## Karten-PDF erzeugen

```bash
python3 scripts/generate_cards_pdf.py
```

Erzeugt `output/cards.pdf` mit abwechselnden Vorderseiten (QR-Code) und
Rückseiten (Jahr groß, Titel/Interpret klein) im Raster, passend für
doppelseitigen Druck. Kartengröße, Ränder, Abstände und Papierformat
lassen sich über die Konstanten am Anfang von `scripts/generate_cards_pdf.py`
einstellen (`CARD_SIZE_MM`, `MARGIN_MM`, `GAP_MM`, `PAGE_FORMAT`).

**Wichtig:** Vor dem großen Druck mit 2–3 Karten testen, ob Vorder- und
Rückseite beim doppelseitigen Drucken richtig übereinanderliegen. Je
nachdem, ob der Drucker an der langen oder kurzen Kante wendet, ggf.
`DUPLEX_EDGE` im Skript zwischen `"long"` und `"short"` umstellen.

## Hosten

**Lokal testen:**

```bash
python3 -m http.server 8765
```

Play/Aufdecken/Nächste-Karte funktionieren lokal ganz normal über die
IP-Adresse des Rechners im selben WLAN (`http://192.168.x.x:8765/?id=001`)
– die Audio-Wiedergabe hat keine Origin-Einschränkung.

**Kamera-Scan lokal testen:** Der QR-Scanner selbst braucht zwingend
HTTPS oder `localhost` (Browser-Sicherheitsrichtlinie für Kamera-Zugriff)
– eine LAN-IP reicht dafür nicht aus. Zwei Wege, den Scanner trotzdem vor
dem Kartendruck zu testen:

- Direkt über die live gehostete GitHub-Pages-URL (siehe unten) – dort
  funktioniert die Kamera ganz normal.
- Oder lokal die Karten-Logik ohne echten Scan testen: einfach die URL
  `?id=001` direkt aufrufen – das überspringt Startseite und Kamera und
  geht direkt zur Karte.

**Dauerhaft (kostenlos):**

- **GitHub Pages:** Repo-Settings → Pages → Source auf Branch `main` /
  Root stellen. App ist danach unter `https://canpala.github.io/schmitzter/`
  erreichbar.
- **Netlify:** Repo verbinden, kein Build-Command nötig (rein statisch),
  Publish-Directory = Repo-Root.

Nach dem ersten Deploy die `BASE_URL` in `scripts/generate_qr.py` prüfen
und ggf. QR-Codes neu generieren, falls sich die Domain ändert.

## Hinweise

- Kein Backend, keine Datenbank, kein YouTube-API-Key nötig.
- Nutzung der Songausschnitte nur für den privaten, nicht-kommerziellen
  Gebrauch dieses Spiels.
