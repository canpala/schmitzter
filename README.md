# Schmitzter

Ein selbstgebautes Hitster-Musik-Ratespiel: physische Karten mit QR-Code,
die per In-App-Kamera-Scan erkannt werden. Die App spielt einen kurzen
Songausschnitt ab dem Refrain über YouTube ab, ohne vorher Titel,
Interpret oder Songbild zu verraten. Man kann jederzeit während der
Wiedergabe aufdecken (Titel/Interpret/Jahr), der Ausschnitt läuft dabei
einfach bis zum Ende weiter.

Reines privates Party-/Geschenkprojekt, kein kommerzielles Produkt.

## Wie es funktioniert

1. Startseite zeigt das Schmitzter-Logo und einen "📷 QR-Code scannen"-Button.
2. Antippen → Kamera öffnet sich in der App (kein Umweg über die
   System-Kamera-App), QR-Code der physischen Karte in den Rahmen halten.
3. Karte erkannt → nur ein Play-Button erscheint, keine Songinfos.
4. Antippen → Song wird per [YouTube IFrame Player API](https://developers.google.com/youtube/iframe_api_reference)
   geladen, springt zum Refrain (`chorusStart`) und spielt ca. 20–25 Sekunden.
5. Während der Wiedergabe kann jederzeit auf "🔍 Aufdecken" getippt werden
   → zeigt Titel, Interpret, Jahr. Der Ausschnitt läuft im Hintergrund
   einfach bis zum Ende weiter (pausiert automatisch nach ca. 20–25 Sek.).
6. "➡️ Nächste Karte" → Kamera öffnet sich direkt wieder für die nächste
   Karte.

Der YouTube-Player wird bewusst klein gehalten, mit einer blickdichten
Fläche abgedeckt und schon beim Laden der Seite im Hintergrund vorbereitet
(nötig für zuverlässige Ton-Wiedergabe auf iOS Safari), damit vor dem
Abspielen/Aufdecken nichts sichtbar wird. Es wird kein YouTube-Data-API-Key
benötigt, kein Login, kein Download – alles läuft rein clientseitig über
das offizielle IFrame-Embed. Der QR-Scan läuft ebenfalls komplett
clientseitig über die Kamera und die Bibliothek [jsQR](https://github.com/cozmo/jsQR)
(lokal eingebunden, keine Internetverbindung zu Drittanbietern nötig).

**Wichtig:** Kamera-Zugriff (`getUserMedia`) funktioniert im Browser nur
über eine sichere Verbindung – also HTTPS oder `localhost`. Über eine
rohe LAN-IP oder sogar über `.local`-Hostnamen lässt sich der QR-Scanner
**nicht** testen (siehe Abschnitt "Hosten" unten für Details, wie man das
trotzdem lokal testet).

## Projektstruktur

```
├── index.html / app.js / styles.css   Die Web-App
├── songs.json                         Zentrale Songdatenbank
├── vendor/jsQR.min.js                 QR-Decoder-Bibliothek (lokal, kein CDN)
├── scripts/
│   ├── generate_qr.py                 Erzeugt QR-Codes aus songs.json
│   ├── generate_cards_pdf.py          Baut das druckfertige Karten-PDF
│   └── requirements.txt
└── output/                            Generierte QR-Codes + PDF (nicht eingecheckt)
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
   - `youtubeId`: aus der YouTube-URL (`youtube.com/watch?v=<hier>`).
   - `chorusStart`: Sekunde, ab der der Refrain beginnt – manuell im Video
     nachschauen und eintragen.

2. QR-Codes und PDF neu generieren (siehe unten).

## QR-Codes generieren

Einmalig Abhängigkeiten installieren (idealerweise in einem venv):

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r scripts/requirements.txt
```

Dann:

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

Zum Öffnen vom Handy im selben WLAN **nicht die rohe IP-Adresse** des
Rechners verwenden (`http://192.168.x.x:8765/...`) – YouTube weist
Embed-Anfragen von einer nackten IP-Adresse als Origin oft mit
Fehler 150/101 ("Embedding vom Rechteinhaber gesperrt") ab, auch wenn
das Video eigentlich frei einbettbar ist. Stattdessen den `.local`-
Hostnamen (Bonjour) des Rechners nutzen:

```bash
scutil --get LocalHostName   # z. B. "MacBook-Pro-von-Can"
```

Dann auf dem Handy:

```
http://<LocalHostName>.local:8765/?id=001
```

Falls das Handy den `.local`-Namen nicht auflöst (kommt bei manchen
Routern/Android-Versionen vor), alternativ direkt über GitHub Pages
testen (siehe unten) – dort tritt das Problem nicht auf, da es sich um
eine echte Domain handelt.

**Kamera-Scan lokal testen:** Der QR-Scanner selbst braucht zwingend
HTTPS oder `localhost` (Browser-Sicherheitsrichtlinie für Kamera-Zugriff)
– weder eine LAN-IP noch ein `.local`-Hostname reichen dafür aus. Zwei
Wege, den Scanner trotzdem vor dem Kartendruck zu testen:

- Direkt über die live gehostete GitHub-Pages-URL (siehe unten) – dort
  funktioniert die Kamera ganz normal.
- Oder lokal die Karten-Logik ohne echten Scan testen: einfach die URL
  `?id=001` direkt aufrufen (siehe oben) – das überspringt Startseite und
  Kamera und geht direkt zur Karte.

**Dauerhaft (kostenlos):**

- **GitHub Pages:** Repo-Settings → Pages → Source auf Branch `main` /
  Root stellen. App ist danach unter `https://canpala.github.io/schmitzter/`
  erreichbar.
- **Netlify:** Repo verbinden, kein Build-Command nötig (rein statisch),
  Publish-Directory = Repo-Root.

Nach dem ersten Deploy die `BASE_URL` in `scripts/generate_qr.py` prüfen
und ggf. QR-Codes neu generieren, falls sich die Domain ändert.

## Hinweise

- Kein Backend, keine Datenbank, kein API-Key nötig.
- Nutzung der YouTube-Videos nur für den privaten, nicht-kommerziellen
  Gebrauch dieses Spiels.
