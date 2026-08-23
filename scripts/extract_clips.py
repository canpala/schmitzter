#!/usr/bin/env python3
"""Extrahiert fuer jeden Song in songs.json einen kurzen, werbefreien
Audio-Clip (ab chorusStart, CLIP_DURATION_SEC lang) und speichert ihn
lokal unter audio/<id>.mp3.

Die App spielt diese lokalen MP3s direkt ab (HTML5 <audio>) statt den
Song live per YouTube-iFrame einzubetten. Das umgeht YouTube-Werbung,
Laender-Sperren und diverse iFrame-Eigenheiten, bedeutet aber auch: die
Clips werden als Dateien im Repository gespeichert (siehe README fuer die
bewusste Abwaegung dazu).

Voraussetzungen: yt-dlp und ein ffmpeg-Binary. Beides wird ueber
scripts/requirements.txt (yt-dlp, imageio-ffmpeg) als reine
Python-Pakete installiert, kein Homebrew/System-ffmpeg noetig.
"""
import json
import pathlib
import subprocess
import sys

import imageio_ffmpeg

CLIP_DURATION_SEC = 22  # sollte zu PLAY_DURATION_MS in app.js passen
FADE_OUT_SEC = 1

ROOT = pathlib.Path(__file__).parent.parent
SONGS_FILE = ROOT / "songs.json"
AUDIO_DIR = ROOT / "audio"


def extract_clip(song, ffmpeg_path):
    start = song["chorusStart"]
    end = start + CLIP_DURATION_SEC
    url = f"https://www.youtube.com/watch?v={song['youtubeId']}"
    raw_path = AUDIO_DIR / f"_{song['id']}_raw.mp3"
    out_path = AUDIO_DIR / f"{song['id']}.mp3"

    print(f"{song['id']}: {song['title']} ({start}s-{end}s) …")

    dl_cmd = [
        "yt-dlp",
        "-f", "bestaudio/best",
        # YouTube erzwingt fuer den Standard-"web"-Client aktuell SABR-
        # Streaming, wodurch die zurueckgegebenen Download-URLs mit 403
        # abgelehnt werden. Der "android"-Client liefert (Stand heute)
        # noch funktionierende direkte URLs. Falls das in Zukunft wieder
        # bricht: `yt-dlp -U` (Update) probieren, das Feld hier ist die
        # uebliche erste Anlaufstelle bei yt-dlp-Github-Issues.
        "--extractor-args", "youtube:player_client=android",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "5",
        "--download-sections", f"*{start}-{end}",
        "--force-keyframes-at-cuts",
        "--ffmpeg-location", ffmpeg_path,
        "-o", str(raw_path.with_suffix("")) + ".%(ext)s",
        url,
    ]
    result = subprocess.run(dl_cmd, capture_output=True, text=True)
    if result.returncode != 0 or not raw_path.exists():
        last_line = result.stderr.strip().splitlines()[-1] if result.stderr else "unbekannter Fehler"
        print(f"  FEHLER beim Download: {last_line}")
        return False

    fade_start = max(0, CLIP_DURATION_SEC - FADE_OUT_SEC)
    fade_cmd = [
        ffmpeg_path,
        "-y",
        "-i", str(raw_path),
        "-af", f"afade=t=out:st={fade_start}:d={FADE_OUT_SEC}",
        str(out_path),
    ]
    result2 = subprocess.run(fade_cmd, capture_output=True, text=True)
    raw_path.unlink(missing_ok=True)

    if result2.returncode != 0:
        last_line = result2.stderr.strip().splitlines()[-1] if result2.stderr else "unbekannter Fehler"
        print(f"  FEHLER beim Fade-out: {last_line}")
        return False

    print(f"  -> {out_path.relative_to(ROOT)}")
    return True


def main():
    songs = json.loads(SONGS_FILE.read_text(encoding="utf-8"))
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

    ok = 0
    failed = []
    for song in songs:
        if extract_clip(song, ffmpeg_path):
            ok += 1
        else:
            failed.append(song["id"])

    print(f"\n{ok}/{len(songs)} Clips erstellt.")
    if failed:
        print(f"Fehlgeschlagen: {failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
