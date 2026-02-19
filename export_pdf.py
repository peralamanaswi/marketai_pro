from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
import textwrap

def make_pdf(title: str, content: str) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, height - 50, title)

    c.setFont("Helvetica", 10)
    y = height - 80

    for line in content.split("\n"):
        wrapped = textwrap.wrap(line, width=110)
        for w in wrapped:
            if y < 60:
                c.showPage()
                c.setFont("Helvetica", 10)
                y = height - 50
            c.drawString(40, y, w)
            y -= 14

    c.save()
    buffer.seek(0)
    return buffer.read()
