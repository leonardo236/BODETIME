from datetime import date, time

import pytest

from bodetime.reports import generate_attendance_pdf
from bodetime.models import Attendance, Worker
from bodetime.services import AttendanceRow, BodeTimeService, ValidationError, is_late
from bodetime.ui import MainWindow
from bodetime.setup_wizard import is_valid_database_name
from main import should_open_setup_wizard


def test_worker_code_is_trimmed_and_uppercased():
    fields = BodeTimeService._clean_worker(" emp-1 ", " Ana ", " Pérez ", " Bodega ", " ")
    assert fields == {"code": "EMP-1", "first_name": "Ana", "last_name": "Pérez", "role": "Bodega", "phone": None}


def test_worker_requires_code_and_name():
    with pytest.raises(ValidationError, match="obligatorios"):
        BodeTimeService._clean_worker("", "Ana", "Pérez", "", "")


def test_worker_fields_are_normalized_and_spanish_names_are_supported():
    fields = BodeTimeService._clean_worker(" emp_08 ", "  José   María ", "D’Arce-Gómez", " Bodega  central ", "+505 8888-7777")
    assert fields == {
        "code": "EMP_08", "first_name": "José María", "last_name": "D’Arce-Gómez",
        "role": "Bodega central", "phone": "+505 8888-7777",
    }


@pytest.mark.parametrize(
    ("code", "first", "last", "role", "phone", "message"),
    [
        ("EMP; DROP TABLE trabajadores", "Ana", "Pérez", "Bodega", "88887777", "código"),
        ("EMP-001", "Ana2", "Pérez", "Bodega", "88887777", "nombres"),
        ("EMP-001", "Ana", "Pérez!", "Bodega", "88887777", "apellidos"),
        ("EMP-001", "Ana", "Pérez", "Bodega<script>", "88887777", "cargo"),
        ("EMP-001", "Ana", "Pérez", "Bodega", "teléfono123", "teléfono"),
        ("EMP-001", "Ana", "Pérez", "Bodega", "1234", "teléfono"),
    ],
)
def test_worker_rejects_invalid_field_formats(code, first, last, role, phone, message):
    with pytest.raises(ValidationError, match=message):
        BodeTimeService._clean_worker(code, first, last, role, phone)


def test_worker_rejects_values_that_exceed_database_column_lengths():
    with pytest.raises(ValidationError, match="80 caracteres"):
        BodeTimeService._clean_worker("EMP-1", "A" * 81, "Pérez", "", "")


def test_worker_cannot_be_saved_without_a_catalog_cargo():
    with pytest.raises(ValidationError, match="cargo"):
        BodeTimeService._clean_worker("EMP-1", "Ana", "Pérez", "", "")


def test_custom_role_names_reject_markup_and_allow_warehouse_job_titles():
    assert BodeTimeService._clean_role_name("Control de inventario") == "Control de inventario"
    assert BodeTimeService._clean_role_name("Auxiliar (turno 2)") == "Auxiliar (turno 2)"
    with pytest.raises(ValidationError, match="cargo"):
        BodeTimeService._clean_role_name("Bodega<script>")


def test_default_warehouse_catalog_contains_common_positions():
    roles = {role.casefold() for role in BodeTimeService.DEFAULT_WAREHOUSE_ROLES}
    assert {"bodeguero", "almacenista", "montacarguista", "despachador de bodega"}.issubset(roles)


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


def test_setup_wizard_only_accepts_safe_mysql_database_identifiers():
    assert is_valid_database_name("bodetime_2026")
    assert not is_valid_database_name("bode-time")
    assert not is_valid_database_name("bode time; DROP DATABASE bodetime")


def test_update_installer_does_not_restart_database_setup_for_existing_users():
    assert should_open_setup_wizard(first_install_only=True, settings_file_exists=False)
    assert not should_open_setup_wizard(first_install_only=True, settings_file_exists=True)
    assert should_open_setup_wizard(first_install_only=False, settings_file_exists=True)
