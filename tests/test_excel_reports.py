import os
from datetime import date, time
from types import SimpleNamespace

import pytest
from PySide6.QtCore import QDate, QSettings
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from openpyxl import load_workbook

from bodetime.excel_reports import generate_attendance_xlsx
from bodetime.services import AttendanceRow
from bodetime.ui import MainWindow

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def test_attendance_excel_export_has_real_report_fields_and_filterable_table(tmp_path):
    # Datos ficticios de prueba; nunca son registros de trabajadores reales.
    row = AttendanceRow(1, 1, "TEST-001", "Prueba de Excel", date(2026, 5, 4), time(8, 12), None, True)
    path = generate_attendance_xlsx(
        tmp_path / "reporte.xlsx", [row], date(2026, 5, 1), date(2026, 5, 31), "Personal de prueba"
    )

    workbook = load_workbook(path, data_only=False)
    sheet = workbook["Asistencia"]
    assert sheet["A1"].value == "BODETIME | Reporte de asistencia"
    assert sheet["A2"].value.endswith("Personal de prueba")
    assert [sheet.cell(row=5, column=column).value for column in range(1, 7)] == [
        "Fecha", "Código", "Trabajador", "Entrada", "Salida", "Estado"
    ]
    assert sheet["A6"].value.date() == date(2026, 5, 4)
    assert sheet["D6"].value == time(8, 12)
    assert sheet["E6"].value is None
    assert sheet["F6"].value == "Tarde"
    assert sheet.freeze_panes == "A6"
    assert list(sheet.tables) == ["BodeTimeAttendance"]
    assert path.stat().st_size > 1000


def test_attendance_excel_export_rejects_empty_reports(tmp_path):
    with pytest.raises(ValueError, match="No hay registros"):
        generate_attendance_xlsx(tmp_path / "vacío.xlsx", [], date(2026, 5, 1), date(2026, 5, 31))


def test_reports_screen_exports_filtered_service_rows_to_excel(monkeypatch, tmp_path):
    app = QApplication.instance() or QApplication([])
    row = AttendanceRow(1, 7, "TEST-001", "Persona de prueba", date(2026, 5, 4), time(8, 12), None, False)
    calls = []

    def attendance_history(start, end, worker_id):
        calls.append((start, end, worker_id))
        return [row]

    service = SimpleNamespace(attendance_history=attendance_history)
    settings = QSettings(str(tmp_path / "report-preferences.ini"), QSettings.Format.IniFormat)
    window = MainWindow(service, database_error="Base de datos simulada", preferences=settings)
    window.report_start.setDate(QDate(2026, 5, 1))
    window.report_end.setDate(QDate(2026, 5, 31))
    window.report_worker.addItem("TEST-001 · Persona de prueba", 7)
    window.report_worker.setCurrentIndex(window.report_worker.count() - 1)
    destination = tmp_path / "reporte-desde-la-interfaz.xlsx"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(destination), ""))
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: QMessageBox.StandardButton.No)

    window.generate_excel_report()

    assert calls == [(date(2026, 5, 1), date(2026, 5, 31), 7)]
    sheet = load_workbook(destination, data_only=True)["Asistencia"]
    assert sheet["B6"].value == "TEST-001"
    assert sheet["C6"].value == "Persona de prueba"
    window.close()
    app.processEvents()
