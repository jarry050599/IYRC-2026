from __future__ import annotations

from io import BytesIO

import qrcode
from reportlab.lib.utils import ImageReader
from reportlab.lib.units import mm
from reportlab.pdfgen.canvas import Canvas


def slot_codes() -> list[str]:
    return [f"{cabinet}{number:03d}" for cabinet in ("A", "B") for number in range(1, 151)]


def labels_pdf(codes: list[str] | None = None) -> BytesIO:
    output = BytesIO()
    canvas = Canvas(output, pagesize=(50 * mm, 12 * mm))
    for code in codes or slot_codes():
        qr = qrcode.QRCode(version=1, box_size=8, border=1)
        qr.add_data(code)
        qr.make(fit=True)
        image = BytesIO()
        qr.make_image(fill_color="black", back_color="white").save(image, format="PNG")
        image.seek(0)
        canvas.drawImage(ImageReader(image), 1 * mm, 1 * mm, 10 * mm, 10 * mm,
                         preserveAspectRatio=True, mask="auto")
        canvas.setFont("Helvetica-Bold", 12)
        canvas.setFillGray(0)
        canvas.drawString(14 * mm, 5.1 * mm, code)
        canvas.setFont("Helvetica", 5.5)
        canvas.setFillGray(.45)
        canvas.drawString(14 * mm, 2.7 * mm, "MAKER SPACE STORAGE")
        canvas.showPage()
    canvas.save()
    output.seek(0)
    return output
