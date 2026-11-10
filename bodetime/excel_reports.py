"""Exporta reportes de asistencia a libros de Excel con datos consultados."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.table import Table, TableStyleInfo

from .services import AttendanceRow


NAVY = "17324F"
BLUE = "007AFF"
PALE_BLUE = "EAF2FC"
TEXT = "1D2733"


def generate_attendance_xlsx(
    path: str | Path,
    rows: list[AttendanceRow],
    start: date,
    end: date,
    worker_label: str = "Todos",
) -> Path:
    """Guarda las filas de asistencia que la interfaz ya recuperó de MySQL."""
    if not rows:
        raise ValueError("No hay registros para exportar a Excel.")

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Asistencia"
    sheet.sheet_view.showGridLines = False
    workbook.properties.title = "Reporte de asistencia BODETIME"
    workbook.properties.creator = "BODETIME"

    sheet.merge_cells("A1:F1")
    title = sheet["A1"]
    title.value = "BODETIME | Reporte de asistencia"
    title.font = Font(name="Aptos", size=18, bold=True, color=NAVY)
    title.alignment = Alignment(vertical="center")
    sheet.row_dimensions[1].height = 31

    sheet.merge_cells("A2:F2")
    sheet["A2"] = f"Período: {start:%d/%m/%Y} – {end:%d/%m/%Y}     Trabajador: {worker_label}"
    sheet["A2"].font = Font(name="Aptos", size=10, color=TEXT)
    sheet["A2"].alignment = Alignment(vertical="center")
    sheet.merge_cells("A3:F3")
    sheet["A3"] = f"Generado: {datetime.now():%d/%m/%Y %H:%M:%S}     Registros: {len(rows)}"
    sheet["A3"].font = Font(name="Aptos", size=9, color="657386")
    sheet["A3"].alignment = Alignment(vertical="center")
    sheet.row_dimensions[3].height = 21

    headings = ["Fecha", "Código", "Trabajador", "Entrada", "Salida", "Estado"]
    for column, label in enumerate(headings, start=1):
        cell = sheet.cell(row=5, column=column, value=label)
        cell.fill = PatternFill("solid", fgColor=NAVY)
        cell.font = Font(name="Aptos", size=10, bold=True, color="FFFFFF")
        cell.alignment = Alignment(vertical="center", horizontal="left")
    sheet.row_dimensions[5].height = 25

    for row_number, record in enumerate(rows, start=6):
        values = (
            record.day,
            record.code,
            record.full_name,
            record.clock_in,
            record.clock_out,
            "Tarde" if record.late else "A tiempo",
        )
        for column, value in enumerate(values, start=1):
            cell = sheet.cell(row=row_number, column=column, value=value)
            cell.font = Font(name="Aptos", size=10, color=TEXT)
            cell.alignment = Alignment(vertical="center")
            if column == 1:
                cell.number_format = "dd/mm/yyyy"
            elif column in (4, 5):
                cell.number_format = "hh:mm"
            if row_number % 2 == 0:
                cell.fill = PatternFill("solid", fgColor=PALE_BLUE)
        sheet.row_dimensions[row_number].height = 22

    last_row = 5 + len(rows)
    table = Table(displayName="BodeTimeAttendance", ref=f"A5:F{last_row}")
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2",
        showFirstColumn=False,
        showLastColumn=False,
        showRowStripes=True,
        showColumnStripes=False,
    )
    sheet.add_table(table)
    sheet.freeze_panes = "A6"
    for column, width in enumerate((14, 17, 34, 14, 14, 16), start=1):
        sheet.column_dimensions[chr(64 + column)].width = width
    sheet.auto_filter.ref = f"A5:F{last_row}"
    sheet.sheet_properties.pageSetUpPr.fitToPage = True
    sheet.page_setup.orientation = "landscape"
    sheet.page_setup.fitToWidth = 1
    sheet.page_setup.fitToHeight = 0
    workbook.save(destination)
    return destination
