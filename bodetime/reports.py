from __future__ import annotations

from html import escape
from datetime import date, datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .services import AttendanceRow


FOREST = colors.HexColor("#244A35")
LEAF = colors.HexColor("#6D9F5E")
PALE = colors.HexColor("#EFF5EC")
INK = colors.HexColor("#2E4035")


def generate_attendance_pdf(path: str | Path, rows: list[AttendanceRow], start: date, end: date, worker_label: str = "Todos") -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("BodeTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=18, leading=22, textColor=FOREST, alignment=TA_LEFT, spaceAfter=4)
    subtitle = ParagraphStyle("BodeSubtitle", parent=styles["Normal"], fontSize=9, leading=13, textColor=INK)
    body = ParagraphStyle("BodeBody", parent=styles["Normal"], fontSize=8, leading=10, textColor=INK)
    flow = [Paragraph("BODETIME | Reporte de asistencia", title),
            Paragraph(f"Período: {start:%d/%m/%Y} – {end:%d/%m/%Y} &nbsp;&nbsp; Trabajador: {escape(worker_label)}", subtitle),
            Paragraph(f"Generado: {datetime.now():%d/%m/%Y %H:%M:%S} &nbsp;&nbsp; Registros: {len(rows)}", subtitle), Spacer(1, 14)]
    data = [["Fecha", "Código", "Trabajador", "Entrada", "Salida", "Estado"]]
    for row in rows:
        data.append([row.day.strftime("%d/%m/%Y"), row.code, Paragraph(escape(row.full_name), body),
                     row.clock_in.strftime("%H:%M"), row.clock_out.strftime("%H:%M") if row.clock_out else "Pendiente",
                     "Tarde" if row.late else "A tiempo"])
    table = Table(data, colWidths=[1.0 * inch, 1.0 * inch, 4.5 * inch, 1.05 * inch, 1.05 * inch, 1.3 * inch], repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FOREST), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, 0), 8),
        ("ALIGN", (0, 0), (-1, 0), "LEFT"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D6E0E5")),
        ("LINEBELOW", (0, 0), (-1, 0), 1.2, LEAF), ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("LEFTPADDING", (0, 0), (-1, -1), 7), ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    flow.append(table)

    def footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#D6E0E5"))
        canvas.line(doc.leftMargin, 0.52 * inch, doc.pagesize[0] - doc.rightMargin, 0.52 * inch)
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#627582"))
        canvas.drawString(doc.leftMargin, 0.34 * inch, "BODETIME · Control de asistencia")
        canvas.drawRightString(doc.pagesize[0] - doc.rightMargin, 0.34 * inch, f"Página {doc.page}")
        canvas.restoreState()

    document = SimpleDocTemplate(str(destination), pagesize=landscape(letter), rightMargin=0.48*inch, leftMargin=0.48*inch, topMargin=0.48*inch, bottomMargin=0.72*inch, title="Reporte de asistencia BODETIME", author="BODETIME")
    document.build(flow, onFirstPage=footer, onLaterPages=footer)
    return destination
