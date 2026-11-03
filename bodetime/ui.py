from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import Qt, QTime
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtCore import QUrl
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QDateEdit, QFileDialog, QFrame,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QSpinBox, QStackedWidget, QTableWidget, QTableWidgetItem, QTimeEdit,
    QVBoxLayout, QWidget,
)

from .reports import generate_attendance_pdf
from .services import BodeTimeService, ValidationError, AttendanceRow


STYLESHEET = """
QWidget { font-family: 'Segoe UI'; font-size: 10pt; color: #253746; }
QMainWindow, QWidget#content { background: #F4F7F9; }
QWidget#sidebar { background: #10283F; }
QLabel#brand { color: white; font-size: 20pt; font-weight: 700; padding: 2px 8px; }
QLabel#brandSub { color: #9FB5C5; font-size: 9pt; padding: 0 8px 14px; }
QPushButton#nav { color: #D7E1E8; background: transparent; border: 0; border-radius: 8px; text-align: left; padding: 12px 14px; font-size: 11pt; }
QPushButton#nav:hover { background: #1B3A53; }
QPushButton#nav[active="true"] { background: #0E8A83; color: white; font-weight: 600; }
QLabel#pageTitle { color: #10283F; font-size: 23pt; font-weight: 700; }
QLabel#muted { color: #70828E; }
QFrame#connectionBanner { background: #FFF2D8; border: 1px solid #F1D596; border-radius: 8px; }
QLabel#bannerText { color: #7A3B00; padding: 9px 10px; }
QPushButton#retryDatabase { background: #F8E5B8; color: #694000; margin: 5px; }
QMessageBox { background: #FFFFFF; }
QMessageBox QLabel { color: #253746; min-width: 360px; }
QMessageBox QPushButton { min-width: 76px; }
QFrame#card, QWidget#panel { background: white; border: 1px solid #E3EAEE; border-radius: 12px; }
QLabel#cardValue { color: #10283F; font-size: 25pt; font-weight: 700; }
QLabel#cardLabel { color: #70828E; font-size: 9pt; }
QLabel#sectionTitle { color: #10283F; font-size: 13pt; font-weight: 650; }
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox { background: white; border: 1px solid #D3DEE4; border-radius: 7px; padding: 8px 9px; min-height: 20px; selection-background-color: #0E8A83; }
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus { border: 1px solid #0E8A83; }
QPushButton { background: #E8EEF2; border: 0; border-radius: 7px; padding: 9px 15px; color: #18354C; font-weight: 600; }
QPushButton:hover { background: #DCE7EC; }
QPushButton#primary { background: #0E8A83; color: white; }
QPushButton#primary:hover { background: #0B756F; }
QPushButton#danger { background: #FCE9E7; color: #A6312A; }
QTableWidget { background: white; border: 1px solid #E3EAEE; border-radius: 8px; gridline-color: #EDF1F3; selection-background-color: #D9F0EE; selection-color: #10283F; }
QHeaderView::section { background: #F4F7F9; border: 0; border-bottom: 1px solid #DEE7EB; padding: 10px 8px; color: #607582; font-weight: 600; }
QTableWidget::item { padding: 7px; }
"""


def _label(text: str, object_name: str | None = None) -> QLabel:
    label = QLabel(text)
    if object_name:
        label.setObjectName(object_name)
    return label


def _panel() -> QWidget:
    widget = QWidget()
    widget.setObjectName("panel")
    return widget


def _table(headers: list[str]) -> QTableWidget:
    table = QTableWidget(0, len(headers))
    table.setHorizontalHeaderLabels(headers)
    table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
    table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setStretchLastSection(True)
    table.setMinimumHeight(240)
    return table


def _put(table: QTableWidget, row: int, col: int, value: object, user_data: int | None = None) -> None:
    item = QTableWidgetItem("" if value is None else str(value))
    if user_data is not None:
        item.setData(Qt.ItemDataRole.UserRole, user_data)
    table.setItem(row, col, item)


class MainWindow(QMainWindow):
    PAGES = ["Inicio", "Trabajadores", "Asistencia", "Reportes", "Configuración"]

    def __init__(self, service: BodeTimeService, database_error: str | None = None):
        super().__init__()
        self.service = service
        self.database_error = database_error
        self.setWindowTitle("BODETIME | Control de asistencia")
        self.setMinimumSize(1120, 740)
        self.resize(1320, 820)
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(16, 26, 16, 18)
        side.setSpacing(7)
        side.addWidget(_label("BODETIME", "brand"))
        side.addWidget(_label("CONTROL DE ASISTENCIA", "brandSub"))
        self.nav_buttons: list[QPushButton] = []
        for index, page in enumerate(self.PAGES):
            button = QPushButton(f"  {['⌂', '♙', '◷', '▤', '⚙'][index]}     {page}")
            button.setObjectName("nav")
            button.setProperty("active", index == 0)
            button.clicked.connect(lambda checked=False, idx=index: self.navigate(idx))
            side.addWidget(button)
            self.nav_buttons.append(button)
        side.addStretch(1)
        side.addWidget(_label("UNAN · León\nIngeniería en Sistemas", "brandSub"))

        self.content = QWidget()
        self.content.setObjectName("content")
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(28, 22, 28, 22)
        content_layout.setSpacing(16)
        self.banner = QFrame()
        self.banner.setObjectName("connectionBanner")
        self.banner.setVisible(False)
        banner_layout = QHBoxLayout(self.banner)
        banner_layout.setContentsMargins(8, 4, 8, 4)
        self.banner_text = QLabel()
        self.banner_text.setObjectName("bannerText")
        self.banner_text.setWordWrap(True)
        retry = QPushButton("Reintentar conexión")
        retry.setObjectName("retryDatabase")
        retry.clicked.connect(self.retry_database)
        banner_layout.addWidget(self.banner_text, 1)
        banner_layout.addWidget(retry)
        content_layout.addWidget(self.banner)
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack, 1)
        root_layout.addWidget(self.sidebar)
        root_layout.addWidget(self.content, 1)
        self.setCentralWidget(root)

        self._build_dashboard()
        self._build_workers()
        self._build_attendance()
        self._build_reports()
        self._build_settings()
        if database_error:
            self.set_database_error(database_error)
        else:
            self.refresh_all()

    def navigate(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setProperty("active", i == index)
            button.style().unpolish(button)
            button.style().polish(button)
        if index == 0:
            self.refresh_dashboard()
        elif index == 1:
            self.refresh_workers()
        elif index == 2:
            self.refresh_attendance_workers()
            self.refresh_attendance_history()
        elif index == 4:
            self.refresh_settings()

    def set_database_error(self, message: str) -> None:
        self.database_error = message
        self.banner_text.setText("MySQL no está disponible. Puedes seguir navegando; las operaciones con datos se habilitarán cuando el servidor responda. " + message)
        self.banner.setVisible(True)
        self.statusBar().showMessage("MySQL desconectado")

    def clear_database_error(self) -> None:
        self.database_error = None
        self.banner.setVisible(False)
        self.statusBar().showMessage("Conectado a MySQL", 5000)

    @staticmethod
    def _error_detail(error: Exception) -> str:
        original = getattr(error, "orig", None)
        return str(original) if original is not None else str(error)

    def retry_database(self) -> None:
        try:
            self.service.database.initialize()
            self.clear_database_error()
            self.refresh_all()
            QMessageBox.information(self, "Conexión restablecida", "BODETIME se conectó a MySQL y actualizó las pantallas.")
        except Exception as exc:
            self.set_database_error(self._error_detail(exc))
            QMessageBox.warning(self, "MySQL no disponible", "No se pudo conectar con el servidor. Comprueba que MySQL Server esté iniciado y que el archivo .env tenga los datos correctos.\n\n" + self._error_detail(exc))

    def _guard(self, callback, *args):
        try:
            result = callback(*args)
            self.clear_database_error()
            return result
        except ValidationError as exc:
            QMessageBox.warning(self, "Revisa la información", str(exc))
        except Exception as exc:
            detail = self._error_detail(exc)
            self.set_database_error(detail)
            QMessageBox.warning(self, "MySQL no disponible", "No se pudo completar la operación. Comprueba el estado del servidor y la conexión configurada.\n\n" + detail)
        return None

    def refresh_all(self) -> None:
        self.refresh_dashboard(silent=True)
        self.refresh_workers(silent=True)
        self.refresh_attendance_workers(silent=True)
        self.refresh_attendance_history(silent=True)
        self.refresh_report_workers(silent=True)
        self.refresh_settings(silent=True)

    def _build_dashboard(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(_label("Panel principal", "pageTitle"))
        layout.addWidget(_label("Resumen actualizado desde la base de datos", "muted"))
        cards = QHBoxLayout()
        self.dashboard_values: list[QLabel] = []
        for title in ["Trabajadores activos", "Asistencias de hoy", "Llegadas tarde", "Turnos abiertos"]:
            card = QFrame()
            card.setObjectName("card")
            box = QVBoxLayout(card)
            box.setContentsMargins(18, 16, 18, 16)
            value = _label("—", "cardValue")
            self.dashboard_values.append(value)
            box.addWidget(value)
            box.addWidget(_label(title, "cardLabel"))
            cards.addWidget(card)
        layout.addLayout(cards)
        bar = QHBoxLayout()
        bar.addWidget(_label("Marcajes de hoy", "sectionTitle"))
        bar.addStretch(1)
        refresh = QPushButton("Actualizar")
        refresh.clicked.connect(self.refresh_dashboard)
        bar.addWidget(refresh)
        layout.addLayout(bar)
        self.dashboard_table = _table(["Fecha", "Código", "Trabajador", "Entrada", "Salida", "Estado"])
        layout.addWidget(self.dashboard_table, 1)
        self.stack.addWidget(page)

    def refresh_dashboard(self, silent: bool = False) -> None:
        try:
            summary = self.service.dashboard_summary()
            for label, value in zip(self.dashboard_values, [summary.active_workers, summary.present_today, summary.late_today, summary.open_shifts]):
                label.setText(str(value))
            rows = self.service.attendance_history(date.today(), date.today())
            self._fill_attendance_table(self.dashboard_table, rows)
            self.clear_database_error()
        except Exception as exc:
            self.set_database_error(self._error_detail(exc))

    def _build_workers(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(_label("Trabajadores", "pageTitle"))
        layout.addWidget(_label("Administra los registros del personal de la bodega", "muted"))
        panel = _panel()
        form = QVBoxLayout(panel)
        form.setContentsMargins(18, 16, 18, 16)
        form.addWidget(_label("Datos del trabajador", "sectionTitle"))
        fields = QHBoxLayout()
        self.worker_code = QLineEdit(); self.worker_code.setPlaceholderText("Ej. EMP-001")
        self.worker_first = QLineEdit(); self.worker_first.setPlaceholderText("Nombres *")
        self.worker_last = QLineEdit(); self.worker_last.setPlaceholderText("Apellidos *")
        self.worker_role = QLineEdit(); self.worker_role.setPlaceholderText("Cargo")
        self.worker_phone = QLineEdit(); self.worker_phone.setPlaceholderText("Teléfono")
        for field, caption in [(self.worker_code, "Código *"), (self.worker_first, "Nombres *"), (self.worker_last, "Apellidos *"), (self.worker_role, "Cargo"), (self.worker_phone, "Teléfono")]:
            group = QVBoxLayout(); group.addWidget(_label(caption, "muted")); group.addWidget(field); fields.addLayout(group, 1)
        form.addLayout(fields)
        buttons = QHBoxLayout()
        self.worker_save = QPushButton("Guardar trabajador"); self.worker_save.setObjectName("primary"); self.worker_save.clicked.connect(self.save_worker)
        clear = QPushButton("Limpiar"); clear.clicked.connect(self.clear_worker_form)
        edit = QPushButton("Cargar selección"); edit.clicked.connect(self.load_selected_worker)
        deactivate = QPushButton("Desactivar"); deactivate.setObjectName("danger"); deactivate.clicked.connect(self.deactivate_selected_worker)
        for button in [self.worker_save, clear, edit, deactivate]: buttons.addWidget(button)
        buttons.addStretch(1)
        form.addLayout(buttons)
        layout.addWidget(panel)
        layout.addWidget(_label("Personal registrado", "sectionTitle"))
        self.workers_table = _table(["Código", "Nombres", "Apellidos", "Cargo", "Teléfono", "Estado"])
        self.workers_table.itemSelectionChanged.connect(self._worker_selection_changed)
        layout.addWidget(self.workers_table, 1)
        self.editing_worker_id: int | None = None
        self.stack.addWidget(page)

    def _worker_selection_changed(self) -> None:
        self.worker_save.setText("Guardar cambios" if self.workers_table.currentRow() >= 0 and self.editing_worker_id else "Guardar trabajador")

    def refresh_workers(self, silent: bool = False) -> None:
        try:
            workers = self.service.list_workers()
            self.workers_table.setRowCount(0)
            for worker in workers:
                row = self.workers_table.rowCount(); self.workers_table.insertRow(row)
                for col, value in enumerate([worker.code, worker.first_name, worker.last_name, worker.role, worker.phone or "—", "Activo" if worker.active else "Inactivo"]):
                    _put(self.workers_table, row, col, value, worker.id if col == 0 else None)
            self.clear_database_error()
        except Exception as exc:
            self.set_database_error(self._error_detail(exc))

    def save_worker(self) -> None:
        values = (self.worker_code.text(), self.worker_first.text(), self.worker_last.text(), self.worker_role.text(), self.worker_phone.text())
        if self.editing_worker_id is None:
            worker = self._guard(self.service.create_worker, *values)
            message = "El trabajador se registró correctamente."
        else:
            worker = self._guard(self.service.update_worker, self.editing_worker_id, *values)
            message = "Los datos del trabajador se actualizaron correctamente."
        if worker:
            QMessageBox.information(self, "Operación completada", message)
            self.clear_worker_form(); self.refresh_workers(); self.refresh_dashboard(); self.refresh_attendance_workers(); self.refresh_report_workers()

    def clear_worker_form(self) -> None:
        for field in [self.worker_code, self.worker_first, self.worker_last, self.worker_role, self.worker_phone]: field.clear()
        self.editing_worker_id = None
        self.worker_save.setText("Guardar trabajador")
        self.workers_table.clearSelection()

    def load_selected_worker(self) -> None:
        row = self.workers_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selecciona un registro", "Elige un trabajador de la tabla para editarlo."); return
        worker_id = self.workers_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        worker = self._guard(self.service.get_worker, worker_id)
        if worker:
            self.editing_worker_id = worker.id
            self.worker_code.setText(worker.code); self.worker_first.setText(worker.first_name); self.worker_last.setText(worker.last_name)
            self.worker_role.setText(worker.role); self.worker_phone.setText(worker.phone or "")
            self.worker_save.setText("Guardar cambios")

    def deactivate_selected_worker(self) -> None:
        row = self.workers_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selecciona un registro", "Elige un trabajador para desactivarlo."); return
        worker_id = self.workers_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        name = f"{self.workers_table.item(row, 1).text()} {self.workers_table.item(row, 2).text()}"
        answer = QMessageBox.question(self, "Confirmar desactivación", f"¿Desactivar a {name}? Se conservarán sus asistencias históricas.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if answer == QMessageBox.StandardButton.Yes and self._guard(self.service.deactivate_worker, worker_id):
            QMessageBox.information(self, "Operación completada", "El trabajador fue desactivado.")
            self.clear_worker_form(); self.refresh_workers(); self.refresh_dashboard(); self.refresh_attendance_workers(); self.refresh_report_workers()

    def _build_attendance(self) -> None:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(_label("Asistencia", "pageTitle"))
        layout.addWidget(_label("Los marcajes se registran con la hora del sistema y no se pueden duplicar en el día", "muted"))
        panel = _panel(); box = QHBoxLayout(panel); box.setContentsMargins(18, 15, 18, 15)
        self.att_worker = QComboBox(); self.att_worker.setMinimumWidth(280)
        box.addWidget(_label("Trabajador", "muted")); box.addWidget(self.att_worker, 1)
        entry = QPushButton("Registrar entrada"); entry.setObjectName("primary"); entry.clicked.connect(self.mark_entry)
        exit_button = QPushButton("Registrar salida"); exit_button.clicked.connect(self.mark_exit)
        box.addWidget(entry); box.addWidget(exit_button)
        layout.addWidget(panel)
        filters = QHBoxLayout(); filters.addWidget(_label("Historial de asistencia", "sectionTitle")); filters.addStretch(1)
        self.att_start = QDateEdit(); self.att_start.setCalendarPopup(True); self.att_start.setDisplayFormat("dd/MM/yyyy"); self.att_start.setDate(date.today() - timedelta(days=30))
        self.att_end = QDateEdit(); self.att_end.setCalendarPopup(True); self.att_end.setDisplayFormat("dd/MM/yyyy"); self.att_end.setDate(date.today())
        self.att_filter_worker = QComboBox()
        self.att_filter_worker.addItem("Todos los trabajadores", None)
        apply = QPushButton("Filtrar"); apply.clicked.connect(self.refresh_attendance_history)
        for text, widget in [("Desde", self.att_start), ("Hasta", self.att_end), ("Trabajador", self.att_filter_worker)]: filters.addWidget(_label(text, "muted")); filters.addWidget(widget)
        filters.addWidget(apply); layout.addLayout(filters)
        self.attendance_table = _table(["Fecha", "Código", "Trabajador", "Entrada", "Salida", "Estado"])
        layout.addWidget(self.attendance_table, 1)
        self.stack.addWidget(page)

    def refresh_attendance_workers(self, silent: bool = False) -> None:
        try:
            workers = self.service.list_workers(include_inactive=False)
            current = self.att_worker.currentData()
            self.att_worker.clear()
            for w in workers: self.att_worker.addItem(f"{w.code} · {w.full_name}", w.id)
            if current is not None:
                index = self.att_worker.findData(current)
                if index >= 0: self.att_worker.setCurrentIndex(index)
            self.att_filter_worker.blockSignals(True)
            selected = self.att_filter_worker.currentData()
            self.att_filter_worker.clear(); self.att_filter_worker.addItem("Todos los trabajadores", None)
            for w in workers: self.att_filter_worker.addItem(f"{w.code} · {w.full_name}", w.id)
            idx = self.att_filter_worker.findData(selected); self.att_filter_worker.setCurrentIndex(max(idx, 0))
            self.att_filter_worker.blockSignals(False)
            self.clear_database_error()
        except Exception as exc:
            self.set_database_error(self._error_detail(exc))

    def _fill_attendance_table(self, table: QTableWidget, rows: list[AttendanceRow]) -> None:
        table.setRowCount(0)
        for record in rows:
            row = table.rowCount(); table.insertRow(row)
            values = [record.day.strftime("%d/%m/%Y"), record.code, record.full_name, record.clock_in.strftime("%H:%M:%S"), record.clock_out.strftime("%H:%M:%S") if record.clock_out else "Pendiente", "Tarde" if record.late else "A tiempo"]
            for col, value in enumerate(values): _put(table, row, col, value)

    def refresh_attendance_history(self, silent: bool = False) -> None:
        try:
            worker_id = self.att_filter_worker.currentData()
            rows = self.service.attendance_history(self.att_start.date().toPython(), self.att_end.date().toPython(), worker_id)
            self._fill_attendance_table(self.attendance_table, rows)
            self.clear_database_error()
        except Exception as exc:
            self.set_database_error(self._error_detail(exc))

    def mark_entry(self) -> None:
        worker_id = self.att_worker.currentData()
        if worker_id is None:
            QMessageBox.warning(self, "No hay trabajadores", "Registra y activa al menos un trabajador antes de marcar asistencia."); return
        result = self._guard(self.service.mark_entry, worker_id)
        if result:
            QMessageBox.information(self, "Entrada registrada", f"Entrada registrada a las {result.clock_in:%H:%M:%S}.")
            self.refresh_attendance_history(); self.refresh_dashboard()

    def mark_exit(self) -> None:
        worker_id = self.att_worker.currentData()
        if worker_id is None:
            QMessageBox.warning(self, "No hay trabajadores", "Registra y activa al menos un trabajador antes de marcar asistencia."); return
        result = self._guard(self.service.mark_exit, worker_id)
        if result:
            QMessageBox.information(self, "Salida registrada", f"Salida registrada a las {result.clock_out:%H:%M:%S}.")
            self.refresh_attendance_history(); self.refresh_dashboard()

    def _build_reports(self) -> None:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(_label("Reportes", "pageTitle"))
        layout.addWidget(_label("Consulta datos de MySQL y genera un PDF con los filtros aplicados", "muted"))
        panel = _panel(); box = QVBoxLayout(panel); box.setContentsMargins(20, 20, 20, 20)
        box.addWidget(_label("Criterios del reporte", "sectionTitle"))
        filters = QHBoxLayout()
        self.report_start = QDateEdit(); self.report_start.setCalendarPopup(True); self.report_start.setDisplayFormat("dd/MM/yyyy"); self.report_start.setDate(date.today() - timedelta(days=30))
        self.report_end = QDateEdit(); self.report_end.setCalendarPopup(True); self.report_end.setDisplayFormat("dd/MM/yyyy"); self.report_end.setDate(date.today())
        self.report_worker = QComboBox(); self.report_worker.addItem("Todos los trabajadores", None); self.report_worker.setMinimumWidth(280)
        for text, widget in [("Desde", self.report_start), ("Hasta", self.report_end), ("Trabajador", self.report_worker)]:
            group = QVBoxLayout(); group.addWidget(_label(text, "muted")); group.addWidget(widget); filters.addLayout(group, 1)
        box.addLayout(filters)
        actions = QHBoxLayout(); actions.addStretch(1)
        generate = QPushButton("Generar PDF"); generate.setObjectName("primary"); generate.clicked.connect(self.generate_report)
        actions.addWidget(generate); box.addLayout(actions)
        layout.addWidget(panel)
        layout.addWidget(_label("El PDF incluye encabezados, período, filtro de trabajador y hora de generación.", "muted"))
        self.stack.addWidget(page)

    def refresh_report_workers(self, silent: bool = False) -> None:
        try:
            workers = self.service.list_workers()
            selected = self.report_worker.currentData()
            self.report_worker.clear(); self.report_worker.addItem("Todos los trabajadores", None)
            for worker in workers: self.report_worker.addItem(f"{worker.code} · {worker.full_name}{'' if worker.active else ' (inactivo)'}", worker.id)
            idx = self.report_worker.findData(selected); self.report_worker.setCurrentIndex(max(idx, 0))
            self.clear_database_error()
        except Exception as exc:
            self.set_database_error(self._error_detail(exc))

    def generate_report(self) -> None:
        start, end = self.report_start.date().toPython(), self.report_end.date().toPython()
        rows = self._guard(self.service.attendance_history, start, end, self.report_worker.currentData())
        if rows is None: return
        if not rows:
            QMessageBox.information(self, "Sin resultados", "No hay asistencias para esos filtros. No se generó un PDF vacío."); return
        suggested = Path.home() / "Documents" / f"BODETIME_asistencia_{start:%Y%m%d}_{end:%Y%m%d}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Guardar reporte PDF", str(suggested), "Documento PDF (*.pdf)")
        if not path: return
        if not path.lower().endswith(".pdf"): path += ".pdf"
        worker_label = self.report_worker.currentText() if self.report_worker.currentData() is not None else "Todos"
        try:
            result = generate_attendance_pdf(path, rows, start, end, worker_label)
        except Exception as exc:
            QMessageBox.critical(self, "Error al generar el PDF", str(exc)); return
        answer = QMessageBox.information(self, "Reporte generado", f"Se generó el reporte con {len(rows)} registros.\n\n{result}\n\n¿Deseas abrirlo ahora?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
        if answer == QMessageBox.StandardButton.Yes: QDesktopServices.openUrl(QUrl.fromLocalFile(str(result)))

    def _build_settings(self) -> None:
        page = QWidget(); layout = QVBoxLayout(page); layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(_label("Configuración", "pageTitle"))
        layout.addWidget(_label("Define el horario laboral y la tolerancia aplicada a las tardanzas", "muted"))
        panel = _panel(); box = QVBoxLayout(panel); box.setContentsMargins(22, 22, 22, 22); box.setSpacing(15)
        box.addWidget(_label("Horario de trabajo", "sectionTitle"))
        row = QHBoxLayout()
        self.schedule_time = QTimeEdit(); self.schedule_time.setDisplayFormat("HH:mm")
        self.schedule_tolerance = QSpinBox(); self.schedule_tolerance.setRange(0, 240); self.schedule_tolerance.setSuffix(" minutos")
        for text, widget in [("Hora oficial de entrada", self.schedule_time), ("Tolerancia de tardanza", self.schedule_tolerance)]:
            group = QVBoxLayout(); group.addWidget(_label(text, "muted")); group.addWidget(widget); row.addLayout(group)
        row.addStretch(1); box.addLayout(row)
        save = QPushButton("Guardar configuración"); save.setObjectName("primary"); save.clicked.connect(self.save_settings); box.addWidget(save, 0, Qt.AlignmentFlag.AlignLeft)
        box.addWidget(_label("Una llegada se marca tarde cuando supera la hora de inicio más la tolerancia. El cambio se aplica a los marcajes futuros.", "muted"))
        self.schedule_status = _label("El horario debe confirmarse con la bodega antes de guardar.", "muted")
        box.addWidget(self.schedule_status)
        layout.addWidget(panel); layout.addStretch(1)
        self.stack.addWidget(page)

    def refresh_settings(self, silent: bool = False) -> None:
        try:
            schedule = self.service.get_schedule()
            self.schedule_time.setTime(QTime(schedule.start_time.hour, schedule.start_time.minute))
            self.schedule_tolerance.setValue(schedule.tolerance_minutes)
            self.schedule_status.setText(f"Configuración vigente: {schedule.start_time:%H:%M} · tolerancia de {schedule.tolerance_minutes} minutos.")
            self.clear_database_error()
        except ValidationError as exc:
            self.schedule_status.setText(str(exc))
        except Exception as exc:
            if not silent: self._guard(lambda: (_ for _ in ()).throw(exc))

    def save_settings(self) -> None:
        qtime = self.schedule_time.time()
        schedule = self._guard(self.service.save_schedule, qtime.toPython(), self.schedule_tolerance.value())
        if schedule:
            self.schedule_status.setText(f"Configuración vigente: {schedule.start_time:%H:%M} · tolerancia de {schedule.tolerance_minutes} minutos.")
            QMessageBox.information(self, "Configuración guardada", "El horario y la tolerancia se guardaron correctamente.")


def run_app(service: BodeTimeService, database_error: str | None = None) -> int:
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("BODETIME")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    window = MainWindow(service, database_error)
    window.show()
    return app.exec()
