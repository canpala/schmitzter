#!/usr/bin/env python3
"""Baut aus den QR-Codes ein druckfertiges PDF fuer doppelseitigen Druck.

Layout: Vorderseiten-Seiten (QR-Code) und Rueckseiten-Seiten (Jahr gross,
Titel/Interpret klein) wechseln sich ab, sodass beim direkten
doppelseitigen Drucken Vorder- und Rueckseite pro Karte zusammenpassen.

Vor dem grossen Druck unbedingt mit 2-3 Karten testen und ggf. DUPLEX_EDGE
anpassen (haengt davon ab, ob der Drucker an der langen oder kurzen Kante
wendet).
"""
import json
import pathlib

from fpdf import FPDF

# --- Konfiguration ---------------------------------------------------------
PAGE_FORMAT = "A4"      # "A4" oder "Letter"
CARD_SIZE_MM = 65       # quadratische Karten, Kantenlaenge in mm
MARGIN_MM = 10          # Seitenrand
GAP_MM = 4              # Abstand zwischen Karten
DUPLEX_EDGE = "long"    # "long" oder "short" -> Spiegelung der Rueckseiten
# ---------------------------------------------------------------------------

ROOT = pathlib.Path(__file__).parent.parent
SONGS_FILE = ROOT / "songs.json"
QR_DIR = ROOT / "output" / "qr-codes"
OUTPUT_PDF = ROOT / "output" / "cards.pdf"

PAGE_SIZES_MM = {"A4": (210.0, 297.0), "Letter": (215.9, 279.4)}


def grid_dims(page_w, page_h):
    usable_w = page_w - 2 * MARGIN_MM
    usable_h = page_h - 2 * MARGIN_MM
    cols = max(1, int((usable_w + GAP_MM) // (CARD_SIZE_MM + GAP_MM)))
    rows = max(1, int((usable_h + GAP_MM) // (CARD_SIZE_MM + GAP_MM)))
    return cols, rows


def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def grid_origin(cols, rows, page_w, page_h):
    grid_w = cols * CARD_SIZE_MM + (cols - 1) * GAP_MM
    grid_h = rows * CARD_SIZE_MM + (rows - 1) * GAP_MM
    return (page_w - grid_w) / 2, (page_h - grid_h) / 2


def draw_front_page(pdf, songs_chunk, cols, rows, page_w, page_h):
    pdf.add_page()
    x0, y0 = grid_origin(cols, rows, page_w, page_h)

    for idx, song in enumerate(songs_chunk):
        r, c = divmod(idx, cols)
        x = x0 + c * (CARD_SIZE_MM + GAP_MM)
        y = y0 + r * (CARD_SIZE_MM + GAP_MM)

        qr_path = QR_DIR / f"{song['id']}.png"
        if qr_path.exists():
            pdf.image(str(qr_path), x=x, y=y, w=CARD_SIZE_MM, h=CARD_SIZE_MM)
        pdf.rect(x, y, CARD_SIZE_MM, CARD_SIZE_MM)


def draw_back_page(pdf, songs_chunk, cols, rows, page_w, page_h):
    pdf.add_page()
    x0, y0 = grid_origin(cols, rows, page_w, page_h)

    for idx, song in enumerate(songs_chunk):
        r, c = divmod(idx, cols)
        # Spiegelung, damit Vorder- und Rueckseite beim doppelseitigen
        # Drucken an der richtigen Position landen.
        if DUPLEX_EDGE == "long":
            c = cols - 1 - c
        else:
            r = rows - 1 - r

        x = x0 + c * (CARD_SIZE_MM + GAP_MM)
        y = y0 + r * (CARD_SIZE_MM + GAP_MM)

        pdf.rect(x, y, CARD_SIZE_MM, CARD_SIZE_MM)

        pdf.set_xy(x, y + CARD_SIZE_MM * 0.28)
        pdf.set_font("Helvetica", "B", 28)
        pdf.multi_cell(CARD_SIZE_MM, 12, str(song["year"]), align="C")

        pdf.set_xy(x + 2, y + CARD_SIZE_MM * 0.58)
        pdf.set_font("Helvetica", "B", 9)
        pdf.multi_cell(CARD_SIZE_MM - 4, 4, song["title"], align="C")

        pdf.set_xy(x + 2, y + CARD_SIZE_MM * 0.8)
        pdf.set_font("Helvetica", "", 8)
        pdf.multi_cell(CARD_SIZE_MM - 4, 4, song["artist"], align="C")


def main():
    songs = json.loads(SONGS_FILE.read_text(encoding="utf-8"))
    if not songs:
        print("songs.json ist leer, nichts zu tun.")
        return

    page_w, page_h = PAGE_SIZES_MM[PAGE_FORMAT]
    cols, rows = grid_dims(page_w, page_h)
    per_page = cols * rows
    print(f"Layout: {cols}x{rows} = {per_page} Karten pro Seite")

    missing = [s["id"] for s in songs if not (QR_DIR / f"{s['id']}.png").exists()]
    if missing:
        print(f"Warnung: keine QR-Codes gefunden fuer IDs {missing}. "
              f"Erst generate_qr.py ausfuehren.")

    pdf = FPDF(orientation="P", unit="mm", format=PAGE_FORMAT)
    pdf.set_auto_page_break(False)
    pdf.set_line_width(0.2)

    for songs_chunk in chunk(songs, per_page):
        draw_front_page(pdf, songs_chunk, cols, rows, page_w, page_h)
        draw_back_page(pdf, songs_chunk, cols, rows, page_w, page_h)

    OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(OUTPUT_PDF))
    print(f"PDF geschrieben: {OUTPUT_PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
