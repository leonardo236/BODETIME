from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, QRegularExpression, Qt, QTime, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QDateEdit, QFileDialog, QFrame, QGraphicsOpacityEffect,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QProgressBar, QPushButton,
    QProgressDialog, QSpinBox, QStackedWidget, QTableWidget, QTableWidgetItem, QTimeEdit,
    QVBoxLayout, QWidget,
)

from .reports import generate_attendance_pdf
from .services import BodeTimeService, ValidationError, AttendanceRow
from .update_tasks import InstallerDownloadTask, ReleaseCheckTask
from .updater import ReleaseInfo
from .version import APP_VERSION


STYLESHEET = """
QWidget { font-family: 'Segoe UI'; font-size: 10pt; color: #303B35; }
QMainWindow, QWidget#content { background: #F3F5F1; }
QWidget#sidebar { background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #354B41, stop:1 #2B4037); }
QFrame#brandMark { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #91B395, stop:1 #71967C); border: 1px solid #A8C5A8; border-radius: 14px; }
QLabel#brandGlyph { color: white; font-size: 23pt; font-weight: 800; }
QLabel#brand { color: white; font-size: 17pt; font-weight: 750; }
QLabel#brandSub { color: #B8C8BD; font-size: 8pt; letter-spacing: 1px; }
QLabel#navCaption { color: #A0B1A5; font-size: 8pt; font-weight: 700; letter-spacing: 1.2px; padding: 22px 12px 7px; }
QFrame#sideRule { background: #52665B; max-height: 1px; }
QPushButton#nav { color: #E0E7E1; background: transparent; border: 0; border-left: 3px solid transparent; border-radius: 8px; text-align: left; padding: 12px 13px; font-size: 10.5pt; }
QPushButton#nav:hover { color: white; background: #40594C; }
QPushButton#nav[active="true"] { color: white; background: #4A6757; border-left: 3px solid #B7CBAA; font-weight: 650; }
QLabel#pageTitle { color: #2C4034; font-size: 24pt; font-weight: 750; }
QLabel#muted { color: #718077; }
QLabel#topContext { color: #78877D; font-size: 8pt; font-weight: 700; letter-spacing: 1.1px; }
QLabel#topDate { color: #43594B; font-size: 9pt; font-weight: 600; padding: 8px 12px; background: #E7ECE5; border-radius: 8px; }
QFrame#connectionBanner { background: #FFF4DF; border: 1px solid #F0D8A8; border-radius: 12px; }
QLabel#bannerText { color: #75430C; padding: 9px 10px; }
QPushButton#retryDatabase { background: #F6E4BD; color: #694000; margin: 5px; }
QFrame#updateBanner { background: #EAF0E8; border: 1px solid #D2DED1; border-radius: 12px; }
QLabel#updateText { color: #354F3D; padding: 9px 10px; font-weight: 600; }
QPushButton#updateNow { background: #5B8067; color: white; margin: 5px; }
QPushButton#updateNow:hover { background: #4E705A; }
QPushButton#updateNotes { background: #DDE7DC; color: #354B3D; margin: 5px; }
QPushButton#dismissUpdate { background: transparent; color: #5E7063; padding: 7px; }
QMessageBox { background: #FFFFFF; }
QMessageBox QLabel { color: #26392E; min-width: 360px; }
QMessageBox QPushButton { min-width: 76px; }
QFrame#metricPanel, QWidget#panel { background: #FEFEFC; border: 1px solid #DEE4DC; border-radius: 12px; }
QFrame#metricPanel { background: #FFFFFF; }
QFrame#metricDivider { background: #E5ECE3; max-width: 1px; }
QLabel#metricValue { color: #456B54; font-size: 24pt; font-weight: 750; }
QLabel#metricLabel { color: #596B5F; font-size: 9pt; font-weight: 650; }
QLabel#metricHint { color: #89978C; font-size: 8pt; }
QLabel#sectionTitle { color: #344D3D; font-size: 12pt; font-weight: 700; }
QLabel#eyebrow { color: #66836D; font-size: 8pt; font-weight: 700; letter-spacing: 1.2px; }
QLabel#heroTitle { color: #3A5945; font-size: 20pt; font-weight: 700; }
QLabel#heroCaption { color: #687C6B; font-size: 10pt; }
QFrame#dashboardHero { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #EEF2E9, stop:1 #E6ECE5); border: 1px solid #DCE4D9; border-radius: 13px; }
QFrame#heroClock { background: transparent; border: 0; }
QLabel#clockValue { color: #45654E; font-size: 25pt; font-weight: 700; }
QLabel#clockCaption { color: #6E8071; font-size: 8pt; font-weight: 650; letter-spacing: 0.7px; }
QFrame#panelHeader { background: transparent; }
QLabel#insightValue { color: #456B54; font-size: 21pt; font-weight: 750; }
QLabel#insightLabel { color: #687C6D; font-size: 9pt; }
QProgressBar { background: #E5EAE3; border: 0; border-radius: 5px; height: 9px; text-align: center; }
QProgressBar::chunk { background: #8BAA8B; border-radius: 5px; }
QLabel#insightNote { color: #7B8D7E; font-size: 8pt; }
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox { background: #FEFEFC; border: 1px solid #D4DDD3; border-radius: 8px; padding: 9px 10px; min-height: 21px; selection-background-color: #8EA78D; }
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus { border: 1px solid #819B83; }
QPushButton { background: #E8ECE6; border: 0; border-radius: 8px; padding: 10px 15px; color: #354B3D; font-weight: 650; }
QPushButton:hover { background: #DDE5DC; }
QPushButton:focus { border: 1px solid #9DB49B; }
QPushButton#primary { background: #5B8067; color: white; }
QPushButton#primary:hover { background: #4E705A; }
QPushButton#danger { background: #FCE9E7; color: #A6312A; }
QTableWidget { background: #FEFEFC; border: 1px solid #DEE4DC; border-radius: 10px; gridline-color: #EEF1EC; selection-background-color: #E4ECE3; selection-color: #344D3D; alternate-background-color: #FAFBF8; outline: none; }
QHeaderView::section { background: #F0F3EE; border: 0; border-bottom: 1px solid #DCE3DA; padding: 11px 9px; color: #68786D; font-size: 8pt; font-weight: 700; }
QTableWidget::item { padding: 9px 7px; border-bottom: 1px solid #EEF1EC; }
QScrollBar:vertical { background: transparent; width: 8px; margin: 4px 1px; }
QScrollBar::handle:vertical { background: #C5D0C4; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
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
    table.verticalHeader().setDefaultSectionSize(46)
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
    """Muestra las pantallas y delega las reglas de datos al servicio."""
    PAGES = ["Inicio", "Trabajadores", "Asistencia", "Reportes", "Configuración"]

    def __init__(self, service: BodeTimeService, database_error: str | None = None):
        super().__init__()
        self.service = service
        self.database_error = database_error
        self.setWindowTitle("BODETIME | Control de asistencia")
        self.setMinimumSize(1120, 740)
        self.resize(1320, 820)
        self.setWindowOpacity(0.0)
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(246)
        side = QVBoxLayout(self.sidebar)
        side.setContentsMargins(18, 25, 18, 18)
        side.setSpacing(6)
        brand_row = QHBoxLayout()
        brand_row.setSpacing(12)
        brand_mark = QFrame(); brand_mark.setObjectName("brandMark"); brand_mark.setFixedSize(48, 48)
        mark_layout = QVBoxLayout(brand_mark); mark_layout.setContentsMargins(0, 0, 0, 0); mark_layout.addWidget(_label("B", "brandGlyph"), 0, Qt.AlignmentFlag.AlignCenter)
        brand_row.addWidget(brand_mark)
        brand_names = QVBoxLayout(); brand_names.setSpacing(0)
        brand_names.addWidget(_label("BODETIME", "brand")); brand_names.addWidget(_label("GESTIÓN DE ASISTENCIA", "brandSub"))
        brand_row.addLayout(brand_names); brand_row.addStretch(1)
        side.addLayout(brand_row)
        side.addWidget(_label("ESPACIO DE TRABAJO", "navCaption"))
        rule = QFrame(); rule.setObjectName("sideRule"); rule.setFrameShape(QFrame.Shape.HLine); side.addWidget(rule)
        self.nav_buttons: list[QPushButton] = []
        for index, page in enumerate(self.PAGES):
            button = QPushButton(f"  {['⌂', '◉', '◷', '▤', '⚙'][index]}      {page}")
            button.setObjectName("nav")
            button.setProperty("active", index == 0)
            button.clicked.connect(lambda checked=False, idx=index: self.navigate(idx))
            side.addWidget(button)
            self.nav_buttons.append(button)
        side.addStretch(1)
        side.addWidget(_label("CONTROL INTERNO\nUNAN · LEÓN", "brandSub"))

        self.content = QWidget()
        self.content.setObjectName("content")
        self._intro_started = False
        self._intro_finished = False
        self._page_animation: QPropertyAnimation | None = None
        self._page_effect: QGraphicsOpacityEffect | None = None
        self._transition_widget: QWidget | None = None
        self.latest_release: ReleaseInfo | None = None
        self._release_check_task: ReleaseCheckTask | None = None
        self._installer_download_task: InstallerDownloadTask | None = None
        self._update_progress_dialog: QProgressDialog | None = None
        self.window_animation = QPropertyAnimation(self, b"windowOpacity", self)
        self.window_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.window_animation.finished.connect(self._finish_intro)
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(30, 20, 30, 24)
        content_layout.setSpacing(15)
        top_bar = QHBoxLayout()
        top_bar.addWidget(_label("BODEGA  /  PERSONAS Y JORNADA", "topContext"))
        top_bar.addStretch(1)
        self.top_date = _label("LEÓN · NICARAGUA", "topDate")
        top_bar.addWidget(self.top_date)
        content_layout.addLayout(top_bar)
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
        self.update_banner = QFrame()
        self.update_banner.setObjectName("updateBanner")
        self.update_banner.setVisible(False)
        update_layout = QHBoxLayout(self.update_banner)
        update_layout.setContentsMargins(8, 4, 8, 4)
        self.update_banner_text = QLabel()
        self.update_banner_text.setObjectName("updateText")
        self.update_banner_text.setWordWrap(True)
        self.update_banner_text.setMinimumWidth(240)
        self.update_now_button = QPushButton("Actualizar ahora")
        self.update_now_button.setObjectName("updateNow")
        self.update_now_button.clicked.connect(self.start_update_download)
        notes_button = QPushButton("Novedades")
        notes_button.setObjectName("updateNotes")
        notes_button.clicked.connect(self.open_release_notes)
        dismiss_button = QPushButton("×")
        dismiss_button.setObjectName("dismissUpdate")
        dismiss_button.setFixedWidth(36)
        dismiss_button.setToolTip("Ocultar aviso por ahora")
        dismiss_button.clicked.connect(lambda: self.update_banner.setVisible(False))
        update_layout.addWidget(self.update_banner_text, 1)
        update_layout.addWidget(self.update_now_button)
        update_layout.addWidget(notes_button)
        update_layout.addWidget(dismiss_button)
        content_layout.addWidget(self.update_banner)
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
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)
        self.clock_timer.start(1000)
        self.database_retry_timer = QTimer(self)
        self.database_retry_timer.setInterval(15000)
        self.database_retry_timer.timeout.connect(self._auto_retry_database)
        self.update_timer = QTimer(self)
        self.update_timer.setInterval(6 * 60 * 60 * 1000)
        self.update_timer.timeout.connect(self.check_for_updates)
        self.update_timer.start()
        self._update_clock()
        if database_error:
            self.set_database_error(database_error)
        else:
            self.refresh_all()
        QTimer.singleShot(1800, self.check_for_updates)

    def navigate(self, index: int) -> None:
        changed = self.stack.currentIndex() != index
        self.stack.setCurrentIndex(index)
        if changed and self._intro_finished:
            self._fade_current_page()
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

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if not self._intro_started:
            self._intro_started = True
            self.window_animation.setDuration(520)
            self.window_animation.setStartValue(0.0)
            self.window_animation.setEndValue(1.0)
            QTimer.singleShot(50, self.window_animation.start)

    def closeEvent(self, event) -> None:
        if hasattr(self, "update_timer"):
            self.update_timer.stop()
        tasks = [self._release_check_task, self._installer_download_task]
        if self._installer_download_task and self._installer_download_task.isRunning():
            self._installer_download_task.cancel()
        for task in tasks:
            if task and task.isRunning() and not task.wait(6500):
                event.ignore()
                self.statusBar().showMessage("Espera a que termine la tarea de actualización para cerrar BODETIME.")
                return
        super().closeEvent(event)

    def _finish_intro(self) -> None:
        self._intro_finished = True

    def _fade_current_page(self) -> None:
        if self._page_animation and self._page_animation.state() == QPropertyAnimation.State.Running:
            self._page_animation.stop()
        if self._transition_widget is not None:
            self._transition_widget.setGraphicsEffect(None)
        page = self.stack.currentWidget()
        if page is None:
            return
        effect = QGraphicsOpacityEffect(page)
        effect.setOpacity(0.72)
        page.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(220)
        animation.setStartValue(0.72)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(lambda: page.setGraphicsEffect(None))
        self._page_effect = effect
        self._transition_widget = page
        self._page_animation = animation
        animation.start()

    def check_for_updates(self, manual: bool = False) -> None:
        if self._release_check_task and self._release_check_task.isRunning():
            if manual:
                self.update_status.setText("La búsqueda de actualizaciones ya está en curso…")
            return
        if manual:
            self.update_status.setText("Buscando una versión nueva…")
            self.check_updates_button.setEnabled(False)
        task = ReleaseCheckTask(self)
        self._release_check_task = task
        task.checked.connect(lambda release: self._update_check_finished(release, manual))
        task.failed.connect(lambda message: self._update_check_failed(message, manual))
        task.finished.connect(lambda: setattr(self, "_release_check_task", None))
        task.finished.connect(task.deleteLater)
        task.start()

    def _update_check_finished(self, release: ReleaseInfo | None, manual: bool) -> None:
        self.check_updates_button.setEnabled(True)
        self.latest_release = release
        if release is None:
            self.update_banner.setVisible(False)
            self.update_status.setText(f"BODETIME {APP_VERSION} está actualizado.")
            if manual:
                QMessageBox.information(self, "BODETIME está actualizado", f"Estás usando la versión {APP_VERSION}.")
            return
        self.update_banner_text.setText(
            f"BODETIME {release.version} está disponible. Puedes instalarla ahora; tus datos locales se conservarán."
        )
        self.update_now_button.setText(f"Actualizar a {release.version}")
        self.update_banner.setVisible(True)
        self._fade_widget(self.update_banner, 220)
        self.update_status.setText(f"Versión {release.version} disponible (actual: {APP_VERSION}).")

    def _update_check_failed(self, message: str, manual: bool) -> None:
        self.check_updates_button.setEnabled(True)
        self.update_status.setText("No se pudo comprobar si hay una versión nueva.")
        if manual:
            QMessageBox.warning(self, "No se pudo buscar", message)

    def _fade_widget(self, widget: QWidget, duration: int = 200) -> None:
        effect = QGraphicsOpacityEffect(widget)
        effect.setOpacity(0.0)
        widget.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", self)
        animation.setDuration(duration)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.finished.connect(lambda: widget.setGraphicsEffect(None))
        animation.start()
        # Keep a reference while Qt animates its property.
        if not hasattr(self, "_notice_animations"):
            self._notice_animations = []
        self._notice_animations.append(animation)
        animation.finished.connect(lambda: self._notice_animations.remove(animation) if animation in self._notice_animations else None)

    def open_release_notes(self) -> None:
        if self.latest_release:
            QDesktopServices.openUrl(QUrl(self.latest_release.notes_url))

    def start_update_download(self) -> None:
        release = self.latest_release
        if release is None:
            self.check_for_updates(manual=True)
            return
        answer = QMessageBox.question(
            self,
            "Actualizar BODETIME",
            f"Se descargará y verificará la versión {release.version}. Después se abrirá el instalador de Windows y BODETIME se cerrará. Puede aparecer una solicitud de permiso del sistema.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.update_now_button.setEnabled(False)
        self._update_progress_dialog = QProgressDialog("Descargando actualización verificada…", "Cancelar", 0, 100, self)
        self._update_progress_dialog.setWindowTitle("Actualización de BODETIME")
        self._update_progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
        self._update_progress_dialog.setMinimumDuration(0)
        self._update_progress_dialog.setValue(0)
        task = InstallerDownloadTask(release)
        self._installer_download_task = task
        task.progress.connect(self._update_progress_dialog.setValue)
        self._update_progress_dialog.canceled.connect(task.cancel)
        task.ready.connect(self._update_download_ready)
        task.failed.connect(self._update_download_failed)
        task.cancelled.connect(self._update_download_cancelled)
        task.finished.connect(lambda: setattr(self, "_installer_download_task", None))
        task.finished.connect(task.deleteLater)
        task.start()

    def _close_update_progress(self) -> None:
        if self._update_progress_dialog is not None:
            self._update_progress_dialog.close()
            self._update_progress_dialog.deleteLater()
            self._update_progress_dialog = None
        self.update_now_button.setEnabled(True)

    def _update_download_ready(self, installer_path: str) -> None:
        self._close_update_progress()
        try:
            if os.name != "nt":
                raise OSError("La instalación automática está disponible en Windows.")
            os.startfile(installer_path, "runas")
        except OSError as exc:
            QMessageBox.critical(
                self,
                "No se pudo abrir el instalador",
                f"El archivo descargado y verificado sigue disponible aquí:\n{installer_path}\n\nDetalle: {exc}",
            )
            return
        QMessageBox.information(
            self,
            "Instalador iniciado",
            "Sigue los pasos del instalador. BODETIME se cerrará para completar la actualización; la base de datos no se modifica.",
        )
        QTimer.singleShot(250, QApplication.instance().quit)

    def _update_download_failed(self, message: str) -> None:
        self._close_update_progress()
        QMessageBox.warning(self, "No se pudo descargar", message)

    def _update_download_cancelled(self) -> None:
        self._close_update_progress()
        self.statusBar().showMessage("Descarga cancelada; BODETIME no se actualizó.", 6000)

    def set_database_error(self, message: str) -> None:
        self.database_error = message
        self.banner_text.setText(
            self._connection_advice(message)
            + " BODETIME volverá a intentar conectarse automáticamente cada 15 segundos."
        )
        self.banner.setVisible(True)
        if hasattr(self, "database_retry_timer") and not self.database_retry_timer.isActive():
            self.database_retry_timer.start()
        if hasattr(self, "dashboard_connection"):
            self.dashboard_connection.setText("●  SIN CONEXIÓN A MYSQL")
            self.dashboard_connection.setStyleSheet("color:#8A591D; background:#FFF0D5; border-radius:8px; padding:8px 12px;")
        self.statusBar().showMessage("MySQL desconectado")

    def clear_database_error(self) -> None:
        self.database_error = None
        if hasattr(self, "database_retry_timer"):
            self.database_retry_timer.stop()
        self.banner.setVisible(False)
        if hasattr(self, "dashboard_connection"):
            self.dashboard_connection.setText("●  MYSQL CONECTADO")
            self.dashboard_connection.setStyleSheet("color:#3C754F; background:#E7F1E4; border-radius:8px; padding:8px 12px;")
        self.statusBar().showMessage("Conectado a MySQL", 5000)

    @staticmethod
    def _error_detail(error: Exception) -> str:
        original = getattr(error, "orig", None)
        return str(original) if original is not None else str(error)

    @staticmethod
    def _connection_advice(message: str) -> str:
        detail = message.lower()
        if "10013" in detail or "wsaeacces" in detail:
            return (
                "Windows rechazó el acceso al puerto local de MySQL. Revisa si el firewall o el antivirus "
                "bloqueó Python y confirma que el puerto configurado esté permitido."
            )
        if "10061" in detail or "econnrefused" in detail:
            return (
                "No hay un servidor MySQL escuchando en la dirección y puerto configurados. "
                "En Servicios, confirma que el servicio MySQL esté en ejecución y revisa DB_HOST y DB_PORT en .env."
            )
        if "1045" in detail or "access denied" in detail:
            return "MySQL rechazó las credenciales. Revisa DB_USER y DB_PASSWORD en tu archivo .env local."
        if "1049" in detail or "unknown database" in detail:
            return "MySQL no encuentra la base de datos configurada. Revisa DB_NAME y ejecuta schema.sql."
        return "BODETIME no pudo conectarse con MySQL. Comprueba el servidor y la configuración local del archivo .env."

    def retry_database(self) -> None:
        try:
            self.service.database.initialize()
            self.clear_database_error()
            self.refresh_all()
            QMessageBox.information(self, "Conexión restablecida", "BODETIME se conectó a MySQL y actualizó las pantallas.")
        except Exception as exc:
            detail = self._error_detail(exc)
            self.set_database_error(detail)
            QMessageBox.warning(self, "MySQL no disponible", self._connection_advice(detail) + "\n\nDetalle técnico: " + detail)

    def _auto_retry_database(self) -> None:
        if not self.database_error:
            self.database_retry_timer.stop()
            return
        try:
            self.service.database.initialize()
        except Exception as exc:
            self.database_error = self._error_detail(exc)
            self.banner_text.setText(
                self._connection_advice(self.database_error)
                + " BODETIME volverá a intentar conectarse automáticamente cada 15 segundos."
            )
            return
        self.clear_database_error()
        self.refresh_all()

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
            QMessageBox.warning(self, "MySQL no disponible", self._connection_advice(detail) + "\n\nDetalle técnico: " + detail)
        return None

    def refresh_all(self) -> None:
        self.refresh_dashboard(silent=True)
        self.refresh_workers(silent=True)
        self.refresh_attendance_workers(silent=True)
        self.refresh_attendance_history(silent=True)
        self.refresh_report_workers(silent=True)
        self.refresh_settings(silent=True)

    def _update_clock(self) -> None:
        if hasattr(self, "hero_clock"):
            self.hero_clock.setText(QTime.currentTime().toString("HH:mm"))
            self.hero_date.setText(date.today().strftime("%d  ·  %m  ·  %Y"))

    def _build_dashboard(self) -> None:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(13)
        heading = QHBoxLayout()
        heading.addWidget(_label("Resumen de hoy", "pageTitle"))
        heading.addStretch(1)
        self.dashboard_connection = _label("●  MYSQL CONECTADO", "topContext")
        self.dashboard_connection.setStyleSheet("color:#3C754F; background:#E7F1E4; border-radius:8px; padding:8px 12px;")
        heading.addWidget(self.dashboard_connection)
        layout.addLayout(heading)

        hero = QFrame(); hero.setObjectName("dashboardHero")
        hero_layout = QHBoxLayout(hero); hero_layout.setContentsMargins(24, 15, 22, 15); hero_layout.setSpacing(18)
        hero_copy = QVBoxLayout(); hero_copy.setSpacing(4)
        hero_copy.addWidget(_label("CONTROL DE ASISTENCIA", "eyebrow"))
        hero_copy.addWidget(_label("Jornada laboral", "heroTitle"))
        hero_copy.addWidget(_label("Entradas, salidas y puntualidad del personal", "heroCaption"))
        hero_layout.addLayout(hero_copy, 1)
        clock_panel = QFrame(); clock_panel.setObjectName("heroClock"); clock_panel.setMinimumWidth(166)
        clock_layout = QVBoxLayout(clock_panel); clock_layout.setContentsMargins(12, 7, 8, 7); clock_layout.setSpacing(0)
        clock_layout.addWidget(_label("HORA LOCAL · LEÓN", "clockCaption"), 0, Qt.AlignmentFlag.AlignRight)
        self.hero_clock = _label("--:--", "clockValue"); self.hero_clock.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.hero_date = _label("", "clockCaption"); self.hero_date.setAlignment(Qt.AlignmentFlag.AlignRight)
        clock_layout.addWidget(self.hero_clock); clock_layout.addWidget(self.hero_date)
        hero_layout.addWidget(clock_panel)
        layout.addWidget(hero)

        metric_panel = QFrame(); metric_panel.setObjectName("metricPanel")
        metrics = QHBoxLayout(metric_panel); metrics.setContentsMargins(0, 0, 0, 0); metrics.setSpacing(0)
        self.dashboard_values: list[QLabel] = []
        metric_specs = [
            ("Trabajadores activos", "Personal habilitado"),
            ("Asistencias de hoy", "Marcajes registrados"),
            ("Llegadas tarde", "Fuera de tolerancia"),
            ("Turnos abiertos", "Sin salida registrada"),
        ]
        for index, (title, hint) in enumerate(metric_specs):
            block = QWidget(); block.setMinimumHeight(100)
            block_layout = QVBoxLayout(block); block_layout.setContentsMargins(20, 14, 15, 13); block_layout.setSpacing(1)
            value = _label("—", "metricValue"); self.dashboard_values.append(value)
            block_layout.addWidget(value)
            block_layout.addWidget(_label(title, "metricLabel"))
            block_layout.addWidget(_label(hint, "metricHint"))
            metrics.addWidget(block, 1)
            if index < len(metric_specs) - 1:
                divider = QFrame(); divider.setObjectName("metricDivider"); divider.setFrameShape(QFrame.Shape.VLine)
                metrics.addWidget(divider)
        layout.addWidget(metric_panel)

        lower = QHBoxLayout(); lower.setSpacing(13)
        activity_panel = _panel(); activity_box = QVBoxLayout(activity_panel); activity_box.setContentsMargins(17, 15, 17, 15); activity_box.setSpacing(10)
        bar = QHBoxLayout()
        bar.addWidget(_label("Registro de hoy", "sectionTitle"))
        bar.addStretch(1)
        refresh = QPushButton("Actualizar")
        refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh.clicked.connect(self.refresh_dashboard)
        bar.addWidget(refresh)
        activity_box.addLayout(bar)
        self.dashboard_table = _table(["Fecha", "Código", "Trabajador", "Entrada", "Salida", "Estado"])
        self.dashboard_table.setMinimumHeight(250)
        activity_box.addWidget(self.dashboard_table, 1)
        lower.addWidget(activity_panel, 1)

        insight = _panel(); insight.setFixedWidth(226)
        insight_box = QVBoxLayout(insight); insight_box.setContentsMargins(18, 18, 18, 18); insight_box.setSpacing(12)
        insight_box.addWidget(_label("AVANCE DE LA JORNADA", "eyebrow"))
        self.insight_ratio = _label("— / —", "insightValue")
        insight_box.addWidget(self.insight_ratio)
        insight_box.addWidget(_label("personas con entrada registrada", "insightLabel"))
        self.attendance_progress = QProgressBar(); self.attendance_progress.setRange(0, 100); self.attendance_progress.setValue(0); self.attendance_progress.setTextVisible(False)
        self.progress_animation = QPropertyAnimation(self.attendance_progress, b"value", self)
        self.progress_animation.setDuration(420)
        self.progress_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        insight_box.addWidget(self.attendance_progress)
        self.insight_percent = _label("Sin registros todavía", "insightNote")
        insight_box.addWidget(self.insight_percent)
        divider = QFrame(); divider.setObjectName("metricDivider"); divider.setFrameShape(QFrame.Shape.HLine); insight_box.addWidget(divider)
        insight_box.addWidget(_label("El resumen se actualiza desde MySQL.", "insightNote"))
        insight_box.addStretch(1)
        lower.addWidget(insight)
        layout.addLayout(lower, 1)
        self.stack.addWidget(page)

    def refresh_dashboard(self, silent: bool = False) -> None:
        try:
            summary = self.service.dashboard_summary()
            for label, value in zip(self.dashboard_values, [summary.active_workers, summary.present_today, summary.late_today, summary.open_shifts]):
                label.setText(str(value))
            marked_ratio = min(summary.present_today, summary.active_workers)
            percentage = round(marked_ratio * 100 / summary.active_workers) if summary.active_workers else 0
            self.insight_ratio.setText(f"{marked_ratio} / {summary.active_workers}")
            self.progress_animation.stop()
            self.progress_animation.setStartValue(self.attendance_progress.value())
            self.progress_animation.setEndValue(percentage)
            self.progress_animation.start()
            self.insight_percent.setText(f"{percentage}% del equipo registrado" if summary.active_workers else "Registra trabajadores para iniciar")
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
        self.worker_code = QLineEdit(); self.worker_code.setPlaceholderText("Ej. EMP-001"); self.worker_code.setMaxLength(20)
        self.worker_code.setValidator(QRegularExpressionValidator(QRegularExpression(r"[A-Za-z0-9_-]{0,20}"), self.worker_code))
        self.worker_first = QLineEdit(); self.worker_first.setPlaceholderText("Nombres *"); self.worker_first.setMaxLength(80)
        self.worker_first.setValidator(QRegularExpressionValidator(QRegularExpression(r"[\p{L}\p{M} .’'-]{0,80}"), self.worker_first))
        self.worker_last = QLineEdit(); self.worker_last.setPlaceholderText("Apellidos *"); self.worker_last.setMaxLength(80)
        self.worker_last.setValidator(QRegularExpressionValidator(QRegularExpression(r"[\p{L}\p{M} .’'-]{0,80}"), self.worker_last))
        self.worker_role = QLineEdit(); self.worker_role.setPlaceholderText("Cargo"); self.worker_role.setMaxLength(80)
        self.worker_role.setValidator(QRegularExpressionValidator(QRegularExpression(r"[\p{L}\p{M}\p{N}_ .,'’/&():-]{0,80}"), self.worker_role))
        self.worker_phone = QLineEdit(); self.worker_phone.setPlaceholderText("Teléfono"); self.worker_phone.setMaxLength(30)
        self.worker_phone.setValidator(QRegularExpressionValidator(QRegularExpression(r"\+?[0-9 ()-]{0,30}"), self.worker_phone))
        self.worker_phone.setToolTip("Entre 7 y 15 dígitos; puedes usar +, espacios, guiones o paréntesis.")
        for field, caption in [(self.worker_code, "Código *"), (self.worker_first, "Nombres *"), (self.worker_last, "Apellidos *"), (self.worker_role, "Cargo"), (self.worker_phone, "Teléfono")]:
            group = QVBoxLayout(); group.addWidget(_label(caption, "muted")); group.addWidget(field); fields.addLayout(group, 1)
        form.addLayout(fields)
        buttons = QHBoxLayout()
        self.worker_save = QPushButton("Guardar trabajador"); self.worker_save.setObjectName("primary"); self.worker_save.clicked.connect(self.save_worker)
        clear = QPushButton("Limpiar"); clear.clicked.connect(self.clear_worker_form)
        self.worker_edit = QPushButton("Editar seleccionado"); self.worker_edit.clicked.connect(self.load_selected_worker)
        self.worker_status = QPushButton("Desactivar"); self.worker_status.setObjectName("danger"); self.worker_status.clicked.connect(self.toggle_selected_worker_status)
        self.worker_edit.setEnabled(False); self.worker_status.setEnabled(False)
        for button in [self.worker_save, clear, self.worker_edit, self.worker_status]: buttons.addWidget(button)
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
        row = self.workers_table.currentRow()
        selected_id = self.workers_table.item(row, 0).data(Qt.ItemDataRole.UserRole) if row >= 0 else None
        if self.editing_worker_id is not None and selected_id != self.editing_worker_id:
            # Never save an old worker's form after the user selects a different row.
            self.editing_worker_id = None
            for field in [self.worker_code, self.worker_first, self.worker_last, self.worker_role, self.worker_phone]:
                field.clear()
        self.worker_save.setText("Guardar cambios" if self.editing_worker_id is not None else "Guardar trabajador")
        self.worker_edit.setEnabled(row >= 0)
        self.worker_status.setEnabled(row >= 0)
        if row >= 0:
            active = self.workers_table.item(row, 5).text() == "Activo"
            self.worker_status.setText("Desactivar" if active else "Reactivar")
            self.worker_status.setObjectName("danger" if active else "primary")
            self.worker_status.style().unpolish(self.worker_status)
            self.worker_status.style().polish(self.worker_status)

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
        if self.editing_worker_id is not None:
            row = self.workers_table.currentRow()
            selected_id = self.workers_table.item(row, 0).data(Qt.ItemDataRole.UserRole) if row >= 0 else None
            if selected_id != self.editing_worker_id:
                self.clear_worker_form()
                QMessageBox.warning(self, "Selección cambió", "Vuelve a cargar el trabajador que deseas editar antes de guardar.")
                return
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

    def toggle_selected_worker_status(self) -> None:
        row = self.workers_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selecciona un registro", "Elige un trabajador de la tabla primero."); return
        worker_id = self.workers_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        name = f"{self.workers_table.item(row, 1).text()} {self.workers_table.item(row, 2).text()}"
        is_active = self.workers_table.item(row, 5).text() == "Activo"
        if is_active:
            answer = QMessageBox.question(self, "Confirmar desactivación", f"¿Desactivar a {name}? Se conservarán sus asistencias históricas.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            operation = self.service.deactivate_worker
            message = "El trabajador fue desactivado. Sus asistencias históricas se conservaron."
        else:
            answer = QMessageBox.question(self, "Confirmar reactivación", f"¿Reactivar a {name} para permitir nuevos marcajes?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            if answer != QMessageBox.StandardButton.Yes:
                return
            operation = self.service.reactivate_worker
            message = "El trabajador fue reactivado."
        if self._guard(operation, worker_id):
            QMessageBox.information(self, "Operación completada", message)
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
        layout.addWidget(panel)
        update_panel = _panel()
        update_box = QVBoxLayout(update_panel)
        update_box.setContentsMargins(22, 20, 22, 20)
        update_box.setSpacing(10)
        update_box.addWidget(_label("Actualizaciones", "sectionTitle"))
        update_box.addWidget(_label("BODETIME comprueba versiones nuevas al abrirse y cada seis horas. La instalación conserva la base de datos.", "muted"))
        update_row = QHBoxLayout()
        self.update_status = _label(f"Versión instalada: {APP_VERSION}", "muted")
        update_row.addWidget(self.update_status, 1)
        self.check_updates_button = QPushButton("Buscar actualización")
        self.check_updates_button.clicked.connect(lambda: self.check_for_updates(manual=True))
        update_row.addWidget(self.check_updates_button)
        update_box.addLayout(update_row)
        layout.addWidget(update_panel)
        layout.addStretch(1)
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
