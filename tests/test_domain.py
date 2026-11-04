from datetime import date, time

import pytest

from bodetime.reports import generate_attendance_pdf
from bodetime.models import Attendance, Worker
from bodetime.services import AttendanceRow, BodeTimeService, ValidationError, is_late
from bodetime.ui import MainWindow


def test_worker_code_is_trimmed_and_uppercased():
    fields = BodeTimeService._clean_worker(" emp-1 ", " Ana ", " Pérez ", " Bodega ", " ")
    assert fields == {"code": "EMP-1", "first_name": "Ana", "last_name": "Pérez", "role": "Bodega", "phone": None}


def test_worker_requires_code_and_name():
    with pytest.raises(ValidationError, match="obligatorios"):
        BodeTimeService._clean_worker("", "Ana", "Pérez", "", "")


def test_lateness_uses_configured_grace_period_inclusively():
    assert not is_late(time(8, 10), time(8, 0), 10)
    assert is_late(time(8, 10, 1), time(8, 0), 10)


def test_orm_metadata_has_mysql_relational_constraints():
    worker_unique = [c for c in Worker.__table__.constraints if c.name == "uq_trabajadores_codigo"]
    attendance_daily = [c for c in Attendance.__table__.constraints if c.name == "uq_asistencia_trabajador_fecha"]
    foreign_keys = list(Attendance.__table__.foreign_keys)
    assert len(worker_unique) == 1
    assert len(attendance_daily) == 1
    assert len(foreign_keys) == 1
    assert foreign_keys[0].target_fullname == "trabajadores.id_trabajador"


def test_report_pdf_is_created_with_table(tmp_path):
    # Fixture sintético para verificar formato; no representa un registro real.
    row = AttendanceRow(1, 1, "TEST-001", "Prueba & <QA>", date(2026, 1, 2), time(8, 11), time(17, 0), True)
    path = generate_attendance_pdf(tmp_path / "reporte.pdf", [row], date(2026, 1, 1), date(2026, 1, 31), "Prueba & QA")
    content = path.read_bytes()
    assert content.startswith(b"%PDF-")
    assert len(content) > 1000


@pytest.mark.parametrize(
    ("detail", "expected"),
    [
        ("WinError 10013", "firewall o el antivirus"),
        ("WinError 10061", "servicio MySQL esté en ejecución"),
    ],
)
def test_mysql_connection_advice_matches_windows_socket_error(detail, expected):
    assert expected in MainWindow._connection_advice(detail)


def test_mysql_credential_advice_does_not_expose_password():
    advice = MainWindow._connection_advice("1045 Access denied")
    assert "DB_USER" in advice
    assert "DB_PASSWORD" in advice
    assert "leo123456789" not in advice
