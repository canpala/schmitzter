#!/usr/bin/env python3
"""Erzeugt eine einfache, großgeschriebene Anleitung (output/anleitung.pdf)
zum Ausdrucken – gedacht fuer Leute, die die App zum ersten Mal auf ihrem
Handy einrichten (z. B. per Android-Chrome "Zum Startbildschirm
hinzufuegen"). Enthaelt den Start-QR-Code aus output/qr-start.png.
"""
import pathlib

from fpdf import FPDF

ROOT = pathlib.Path(__file__).parent.parent
START_QR_PATH = ROOT / "output" / "qr-start.png"
OUTPUT_PDF = ROOT / "output" / "anleitung.pdf"

MARGIN = 12


def heading(pdf, text, size=17):
    pdf.set_font("Helvetica", "B", size)
    pdf.set_x(MARGIN)
    pdf.multi_cell(210 - 2 * MARGIN, size * 0.45, text, align="C")
    pdf.ln(2)


def step(pdf, text, size=13.5):
    pdf.set_font("Helvetica", "", size)
    pdf.set_x(MARGIN)
    pdf.multi_cell(210 - 2 * MARGIN, size * 0.42, text)


def main():
    if not START_QR_PATH.exists():
        raise SystemExit(
            "output/qr-start.png fehlt - zuerst 'python3 scripts/generate_qr.py' ausfuehren."
        )

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(False)
    pdf.add_page()
    pdf.set_y(10)

    heading(pdf, "Schmitzter - Einmal einrichten", size=22)
    pdf.ln(2)
    heading(pdf, "So richtest du das Spiel einmalig ein (Android):", size=14)
    pdf.ln(1)

    for text in [
        "1. Kamera-App oeffnen und den QR-Code unten scannen.",
        "2. Auf den Link tippen, der erscheint.",
        "3. Oben rechts im Browser auf die drei Punkte (Menue) tippen.",
        '4. "Zum Startbildschirm hinzufuegen" antippen.',
        "5. Bestaetigen - jetzt gibt es ein Schmitzter-Icon auf dem Startbildschirm.",
    ]:
        step(pdf, text)

    pdf.ln(3)
    qr_size = 42
    qr_x = (210 - qr_size) / 2
    pdf.image(str(START_QR_PATH), x=qr_x, y=pdf.get_y(), w=qr_size, h=qr_size)
    pdf.set_y(pdf.get_y() + qr_size + 6)

    heading(pdf, "So wird gespielt:", size=14)
    pdf.ln(1)

    for text in [
        "1. Schmitzter-Icon antippen.",
        '2. Auf "QR-Code scannen" tippen und Kamera erlauben.',
        "3. QR-Code auf einer Spielkarte in den Rahmen halten.",
        '4. Auf "Abspielen" tippen und raten: Titel, Interpret, Jahr?',
        '5. Wenn ihr es wisst (oder aufgeben wollt): auf "Aufdecken" tippen.',
        '6. Auf "Naechste Karte" tippen und die naechste Karte scannen.',
    ]:
        step(pdf, text)

    used = pdf.get_y()
    if used > 297 - MARGIN:
        print(f"WARNUNG: Inhalt reicht bis {used:.0f}mm, Seite ist nur 297mm hoch!")
    else:
        print(f"OK: Inhalt passt (bis {used:.0f}mm von 297mm).")

    pdf.output(str(OUTPUT_PDF))
    print(f"PDF geschrieben: {OUTPUT_PDF.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
