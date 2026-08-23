#!/usr/bin/env python3
"""Erzeugt fuer jeden Eintrag in songs.json einen QR-Code (output/qr-codes/<id>.png).

Der QR-Code kodiert die URL der gehosteten Web-App mit der Song-ID als
Query-Parameter, z. B. https://canpala.github.io/schmitzter/?id=001
"""
import json
import pathlib

import qrcode

# Basis-URL der gehosteten App anpassen, falls anders (z. B. lokales Hosting
# oder Netlify-Domain).
BASE_URL = "https://canpala.github.io/schmitzter/"

ROOT = pathlib.Path(__file__).parent.parent
SONGS_FILE = ROOT / "songs.json"
OUTPUT_DIR = ROOT / "output" / "qr-codes"


def main():
    songs = json.loads(SONGS_FILE.read_text(encoding="utf-8"))
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for song in songs:
        url = f"{BASE_URL}?id={song['id']}"
        img = qrcode.make(url)
        out_path = OUTPUT_DIR / f"{song['id']}.png"
        img.save(out_path)
        print(f"{song['id']}: {url} -> {out_path.relative_to(ROOT)}")

    print(f"\n{len(songs)} QR-Codes erzeugt in {OUTPUT_DIR.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
