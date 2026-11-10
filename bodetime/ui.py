from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

from PySide6.QtCore import QDate, QRegularExpression, QSettings, Qt, QTime, QTimer, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractItemView, QAbstractSpinBox, QApplication, QCheckBox, QColorDialog, QComboBox,
    QDialog, QFileDialog, QFrame, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QHBoxLayout, QInputDialog,
    QLabel, QLineEdit, QListWidget, QMainWindow, QMessageBox, QProgressBar,
    QPushButton, QProgressDialog, QScrollArea, QSpinBox, QStackedWidget, QTableWidget,
    QTableWidgetItem, QTimeEdit, QVBoxLayout, QWidget,
)

from .animations import SmoothTween
from .appearance import ACCENT_PRESETS, apply_platform_font, build_stylesheet
from .branding import ReportMark, report_icon
from .calendar import GlassDateEdit
from .clock import ClockFace
from .excel_reports import generate_attendance_xlsx
from .reports import generate_attendance_pdf
from .splash import SplashScreen
from .services import BodeTimeService, ValidationError, AttendanceRow
from .update_tasks import InstallerDownloadTask, ReleaseCheckTask
from .updater import ReleaseInfo
from .version import APP_VERSION


def _label(text: str, object_name: str | None = None) -> QLabel:
    label = QLabel(text)
    if object_name:
        label.setObjectName(object_name)
    return label


def _panel() -> QWidget:
    widget = QWidget()
    widget.setObjectName("panel")
    shadow = QGraphicsDropShadowEffect(widget)
    shadow.setBlurRadius(24)
    shadow.setOffset(0, 7)
    shadow.setColor(QColor(20, 45, 48, 22))
    widget.setGraphicsEffect(shadow)
    return widget


def _page() -> QWidget:
    """Crea una página sin fondo propio para que se vea la superficie principal."""
    widget = QWidget()
    widget.setObjectName("pageSurface")
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
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


class JobRolesDialog(QDialog):
    """Permite mantener las opciones personalizadas del catálogo de cargos."""

    def __init__(self, service: BodeTimeService, parent=None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("Cargos de bodega")
        self.setMinimumSize(520, 430)
        layout = QVBoxLayout(self)
        layout.addWidget(_label("Catálogo de cargos", "sectionTitle"))
        layout.addWidget(_label("Agrega los puestos que usa tu bodega. Los cambios quedan disponibles para los demás usuarios de esta base de datos.", "muted"))
        self.roles = QListWidget()
        self.roles.setObjectName("roleList")
        self.roles.setAlternatingRowColors(True)
        layout.addWidget(self.roles, 1)
        form = QHBoxLayout()
        self.new_role = QLineEdit()
        self.new_role.setPlaceholderText("Ej. Control de inventario")
        self.new_role.setMaxLength(80)
        self.new_role.setValidator(QRegularExpressionValidator(QRegularExpression(r"[\p{L}\p{M}\p{N}_ .,'’/&():-]{0,80}"), self.new_role))
        add = QPushButton("Agregar cargo")
        add.setObjectName("primary")
        add.clicked.connect(self.add_role)
        self.new_role.returnPressed.connect(self.add_role)
        form.addWidget(self.new_role, 1)
        form.addWidget(add)
        layout.addLayout(form)
        self.status = _label("Los cargos base no se pueden borrar. Un cargo en uso tampoco se puede quitar.", "muted")
        layout.addWidget(self.status)
        buttons = QHBoxLayout()
        remove = QPushButton("Quitar cargo")
        remove.setObjectName("danger")
        remove.clicked.connect(self.remove_role)
        close = QPushButton("Cerrar")
        close.clicked.connect(self.accept)
        buttons.addWidget(remove)
        buttons.addStretch(1)
        buttons.addWidget(close)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self) -> None:
        try:
            self.roles.clear()
            for role in self.service.list_custom_roles():
                self.roles.addItem(role)
        except Exception as exc:
            QMessageBox.critical(self, "No se pudieron cargar los cargos", str(exc))

    def add_role(self) -> None:
        try:
            self.service.add_custom_role(self.new_role.text())
        except ValidationError as exc:
            QMessageBox.warning(self, "Cargo no válido", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "No se pudo guardar el cargo", str(exc))
            return
        role = " ".join(self.new_role.text().split())
        self.new_role.clear()
        self.refresh()
        self.status.setText(f"«{role}» ya está disponible en el selector de trabajadores.")

    def remove_role(self) -> None:
        selected = self.roles.currentItem()
        if selected is None:
            QMessageBox.warning(self, "Selecciona un cargo", "Elige un cargo personalizado de la lista.")
            return
        role = selected.text()
        answer = QMessageBox.question(
            self, "Eliminar cargo", f"¿Eliminar el cargo «{role}» del catálogo?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.service.remove_custom_role(role)
        except ValidationError as exc:
            QMessageBox.warning(self, "No se puede eliminar", str(exc))
            return
        except Exception as exc:
            QMessageBox.critical(self, "No se pudo eliminar el cargo", str(exc))
            return
        self.refresh()
        self.status.setText(f"Se quitó «{role}» del catálogo.")


class MainWindow(QMainWindow):
    """Muestra las pantallas y delega las reglas de datos al servicio."""
    PAGES = ["Inicio", "Trabajadores", "Asistencia", "Reportes", "Configuración"]

    def __init__(self, service: BodeTimeService, database_error: str | None = None, preferences: QSettings | None = None):
        super().__init__()
        self.service = service
        self.database_error = database_error
        self.preferences = preferences or QSettings("BODETIME", "BODETIME")
        self.theme_mode = str(self.preferences.value("appearance/mode", "light"))
        if self.theme_mode not in {"light", "dark"}:
            self.theme_mode = "light"
        saved_accent_value = self.preferences.value("appearance/accent")
        if saved_accent_value is None or str(saved_accent_value).lower() == "#16877b":
            self.accent_color = "#007AFF"
            if saved_accent_value is not None:
                self.preferences.setValue("appearance/accent", self.accent_color)
                self.preferences.sync()
        else:
            saved_accent = QColor(str(saved_accent_value))
            self.accent_color = saved_accent.name() if saved_accent.isValid() else "#007AFF"
        self.motion_enabled = self.preferences.value("appearance/animations", True, type=bool)
        self.calendar_style = str(self.preferences.value("appearance/calendar", "glass"))
        if self.calendar_style not in {"glass", "classic"}:
            self.calendar_style = "glass"
        self.clock_style = str(self.preferences.value("appearance/clock", "digital"))
        if self.clock_style not in {"digital", "analog"}:
            self.clock_style = "digital"
        self.date_pickers: list[GlassDateEdit] = []
        self._active_tweens: set[SmoothTween] = set()
        self._widget_tweens: dict[QWidget, tuple[SmoothTween, QGraphicsOpacityEffect]] = {}
        self._progress_tween: SmoothTween | None = None
        self._page_effect: QGraphicsOpacityEffect | None = None
        self._intro_started = False
        self._intro_finished = False
        self._install_after_update_check = False
        app = QApplication.instance()
        if app:
            apply_platform_font(app)
            app.setStyleSheet(build_stylesheet(self.theme_mode, self.accent_color))
        self.setWindowIcon(report_icon(self.accent_color))
        self.setWindowTitle("BODETIME | Control de asistencia")
        self.setMinimumSize(1120, 740)
        self.resize(1320, 820)
        self.setWindowOpacity(0.0 if self.motion_enabled else 1.0)
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
        brand_mark = ReportMark(52, self.accent_color, "brandMark", self.sidebar)
        self.brand_mark = brand_mark
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
        self.latest_release: ReleaseInfo | None = None
        self._release_check_task: ReleaseCheckTask | None = None
        self._installer_download_task: InstallerDownloadTask | None = None
        self._update_progress_dialog: QProgressDialog | None = None
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
        if changed and self._intro_finished and self.motion_enabled:
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
            if self.motion_enabled:
                QTimer.singleShot(25, lambda: self._start_tween(self.setWindowOpacity, 0.0, 1.0, 420, self._finish_intro))
            else:
                self.setWindowOpacity(1.0)
                self._finish_intro()

    def _apply_appearance(self) -> None:
        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet(self.theme_mode, self.accent_color))
        self.setWindowIcon(report_icon(self.accent_color))
        if hasattr(self, "brand_mark"):
            self.brand_mark.set_accent(self.accent_color)
        if hasattr(self, "clock_face"):
            self.clock_face.set_accent(self.accent_color)
        self.preferences.setValue("appearance/mode", self.theme_mode)
        self.preferences.setValue("appearance/accent", self.accent_color)
        self.preferences.sync()
        if hasattr(self, "clock_face"):
            self.clock_face.set_accent(self.accent_color)
        if hasattr(self, "accent_preview"):
            self.accent_preview.setText(f"Acento actual · {self.accent_color.upper()}")
        for picker in self.date_pickers:
            picker.set_calendar_style(self.accent_color, self.calendar_style, self.motion_enabled)

    def _on_theme_changed(self, _index: int) -> None:
        selected = self.theme_selector.currentData()
        if selected in {"light", "dark"}:
            self.theme_mode = selected
            self._apply_appearance()

    def _populate_accent_selector(self, selected_color: str) -> None:
        self.accent_selector.blockSignals(True)
        self.accent_selector.clear()
        preset_colors = {color.lower() for _, color in ACCENT_PRESETS}
        if selected_color.lower() not in preset_colors:
            self.accent_selector.addItem(f"Personalizado · {selected_color.upper()}", selected_color)
        for name, color in ACCENT_PRESETS:
            self.accent_selector.addItem(name, color)
        self.accent_selector.addItem("Elegir otro color…", "__custom__")
        index = self.accent_selector.findData(selected_color)
        self.accent_selector.setCurrentIndex(index if index >= 0 else 0)
        self.accent_selector.blockSignals(False)

    def _on_accent_activated(self, index: int) -> None:
        selected = self.accent_selector.itemData(index)
        if selected == "__custom__":
            chosen = QColorDialog.getColor(QColor(self.accent_color), self, "Elige el color principal")
            if not chosen.isValid():
                self._populate_accent_selector(self.accent_color)
                return
            selected = chosen.name()
        if isinstance(selected, str) and QColor(selected).isValid():
            self.accent_color = QColor(selected).name()
            self._populate_accent_selector(self.accent_color)
            self._apply_appearance()

    def _on_animations_toggled(self, enabled: bool) -> None:
        self.motion_enabled = enabled
        self.preferences.setValue("appearance/animations", enabled)
        self.preferences.sync()
        for picker in self.date_pickers:
            picker.set_calendar_style(self.accent_color, self.calendar_style, enabled)
        if enabled:
            return
        for tween in list(self._active_tweens):
            self._cancel_tween(tween)
        for widget, (_, effect) in list(self._widget_tweens.items()):
            if widget.graphicsEffect() is effect:
                widget.setGraphicsEffect(None)
        self._widget_tweens.clear()
        self.setWindowOpacity(1.0)
        self._finish_intro()
        self.preferences.setValue("appearance/animations", False)
        self.preferences.sync()

    def _on_calendar_style_changed(self, _index: int) -> None:
        style = self.calendar_style_selector.currentData()
        if style not in {"glass", "classic"}:
            return
        self.calendar_style = style
        self.preferences.setValue("appearance/calendar", style)
        self.preferences.sync()
        for picker in self.date_pickers:
            picker.set_calendar_style(self.accent_color, style, self.motion_enabled)

    def _on_clock_style_changed(self, _index: int) -> None:
        style = self.clock_style_selector.currentData()
        if style not in {"digital", "analog"}:
            return
        self.clock_style = style
        self.preferences.setValue("appearance/clock", style)
        self.preferences.sync()
        self._apply_clock_style()

    def _apply_clock_style(self) -> None:
        if not hasattr(self, "clock_face"):
            return
        digital = self.clock_style == "digital"
        self.clock_face.setVisible(not digital)
        self.hero_clock.setVisible(digital)
        self.hero_seconds.setVisible(digital)

    def _start_tween(self, setter, start: float, end: float, duration: int, on_finished=None) -> SmoothTween | None:
        if not self.motion_enabled:
            setter(float(end))
            if on_finished:
                on_finished()
            return None
        tween = SmoothTween(setter, start, end, duration, self)
        self._active_tweens.add(tween)
        tween.finished.connect(lambda current=tween: self._active_tweens.discard(current))
        if on_finished:
            tween.finished.connect(on_finished)
        tween.start()
        return tween

    def _cancel_tween(self, tween: SmoothTween | None) -> None:
        if tween is not None:
            tween.cancel()
            self._active_tweens.discard(tween)

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
        page = self.stack.currentWidget()
        if page is None:
            return
        self._fade_widget(page, duration=200, start=0.84)

    def _fade_widget(self, widget: QWidget, duration: int = 190, start: float = 0.0) -> None:
        if not self.motion_enabled:
            return
        previous = self._widget_tweens.pop(widget, None)
        if previous:
            self._cancel_tween(previous[0])
            if widget.graphicsEffect() is previous[1]:
                widget.setGraphicsEffect(None)
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

        def finish() -> None:
            active = self._widget_tweens.get(widget)
            if active and active[1] is effect:
                self._widget_tweens.pop(widget, None)
                if widget.graphicsEffect() is effect:
                    widget.setGraphicsEffect(None)

        tween = self._start_tween(effect.setOpacity, start, 1.0, duration, finish)
        if tween:
            self._widget_tweens[widget] = (tween, effect)

    def check_for_updates(self, manual: bool = False, install_if_available: bool = False) -> None:
        self._install_after_update_check = self._install_after_update_check or install_if_available
        if self._release_check_task and self._release_check_task.isRunning():
            if manual:
                self.update_status.setText("La búsqueda sigue en curso; te preguntaré si deseas instalarla.")
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
            self._install_after_update_check = False
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
        install_now = self._install_after_update_check
        self._install_after_update_check = False
        if install_now:
            QTimer.singleShot(250, self.start_update_download)

    def _update_check_failed(self, message: str, manual: bool) -> None:
        self._install_after_update_check = False
        self.check_updates_button.setEnabled(True)
        self.update_status.setText("No se pudo comprobar si hay una versión nueva.")
        if manual:
            QMessageBox.warning(self, "No se pudo buscar", message)

    def open_release_notes(self) -> None:
        if self.latest_release:
            QDesktopServices.openUrl(QUrl(self.latest_release.notes_url))

    def start_update_download(self) -> None:
        if self._installer_download_task and self._installer_download_task.isRunning():
            self.statusBar().showMessage("La actualización ya se está descargando.", 5000)
            return
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
        self.check_updates_button.setEnabled(False)
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
        self.check_updates_button.setEnabled(True)

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
            self.dashboard_connection.setProperty("state", "offline")
            self.dashboard_connection.style().unpolish(self.dashboard_connection)
            self.dashboard_connection.style().polish(self.dashboard_connection)
        self.statusBar().showMessage("MySQL desconectado")

    def clear_database_error(self) -> None:
        self.database_error = None
        if hasattr(self, "database_retry_timer"):
            self.database_retry_timer.stop()
        self.banner.setVisible(False)
        if hasattr(self, "dashboard_connection"):
            self.dashboard_connection.setText("●  MYSQL CONECTADO")
            self.dashboard_connection.setProperty("state", "online")
            self.dashboard_connection.style().unpolish(self.dashboard_connection)
            self.dashboard_connection.style().polish(self.dashboard_connection)
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
            now = QTime.currentTime()
            today = date.today()
            weekdays = ("LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO", "DOMINGO")
            months = ("ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE")
            self.hero_clock.setText(now.toString("HH:mm"))
            self.hero_seconds.setText(now.toString("ss"))
            if hasattr(self, "clock_face"):
                self.clock_face.set_time(now)
            self.hero_date.setText(f"{weekdays[today.weekday()]}  ·  {today.day} {months[today.month - 1]}")

    def _build_dashboard(self) -> None:
        page = _page()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(13)
        heading = QHBoxLayout()
        heading.addWidget(_label("Resumen de hoy", "pageTitle"))
        heading.addStretch(1)
        self.dashboard_connection = _label("●  MYSQL CONECTADO", "dashboardConnection")
        self.dashboard_connection.setProperty("state", "online")
        heading.addWidget(self.dashboard_connection)
        layout.addLayout(heading)

        hero = QFrame(); hero.setObjectName("dashboardHero")
        hero_shadow = QGraphicsDropShadowEffect(hero)
        hero_shadow.setBlurRadius(30); hero_shadow.setOffset(0, 10); hero_shadow.setColor(QColor(20, 45, 48, 24))
        hero.setGraphicsEffect(hero_shadow)
        hero_layout = QHBoxLayout(hero); hero_layout.setContentsMargins(24, 15, 22, 15); hero_layout.setSpacing(18)
        hero_copy = QVBoxLayout(); hero_copy.setSpacing(4)
        hero_copy.addWidget(_label("CONTROL DE ASISTENCIA", "eyebrow"))
        hero_copy.addWidget(_label("Jornada laboral", "heroTitle"))
        hero_copy.addWidget(_label("Entradas, salidas y puntualidad del personal", "heroCaption"))
        hero_layout.addLayout(hero_copy, 1)
        clock_panel = QFrame(); clock_panel.setObjectName("heroClock"); clock_panel.setMinimumWidth(238)
        clock_shadow = QGraphicsDropShadowEffect(clock_panel)
        clock_shadow.setBlurRadius(22); clock_shadow.setOffset(0, 6); clock_shadow.setColor(QColor(20, 45, 48, 20))
        clock_panel.setGraphicsEffect(clock_shadow)
        clock_layout = QVBoxLayout(clock_panel); clock_layout.setContentsMargins(16, 9, 16, 9); clock_layout.setSpacing(0)
        clock_layout.addWidget(_label("HORA LOCAL · LEÓN", "clockCaption"), 0, Qt.AlignmentFlag.AlignRight)
        clock_row = QHBoxLayout(); clock_row.setSpacing(8)
        self.clock_face = ClockFace(self.accent_color)
        clock_row.addWidget(self.clock_face, 0, Qt.AlignmentFlag.AlignVCenter)
        clock_text = QVBoxLayout(); clock_text.setContentsMargins(0, 0, 0, 0); clock_text.setSpacing(0)
        self.hero_clock = _label("--:--", "clockValue"); self.hero_clock.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.hero_seconds = _label("00", "clockSeconds"); self.hero_seconds.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        digits = QHBoxLayout(); digits.setContentsMargins(0, 0, 0, 0); digits.setSpacing(2)
        digits.addStretch(1); digits.addWidget(self.hero_clock); digits.addWidget(self.hero_seconds, 0, Qt.AlignmentFlag.AlignBottom)
        clock_text.addLayout(digits)
        self.hero_date = _label("", "clockCaption"); self.hero_date.setAlignment(Qt.AlignmentFlag.AlignRight)
        clock_text.addWidget(self.hero_date)
        clock_row.addLayout(clock_text, 1)
        clock_layout.addLayout(clock_row)
        self._apply_clock_style()
        hero_layout.addWidget(clock_panel)
        layout.addWidget(hero)

        metric_panel = QFrame(); metric_panel.setObjectName("metricPanel")
        metric_shadow = QGraphicsDropShadowEffect(metric_panel)
        metric_shadow.setBlurRadius(22); metric_shadow.setOffset(0, 7); metric_shadow.setColor(QColor(20, 45, 48, 18))
        metric_panel.setGraphicsEffect(metric_shadow)
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
        self._progress_tween = None
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
            self._cancel_tween(self._progress_tween)
            self._progress_tween = self._start_tween(
                lambda value: self.attendance_progress.setValue(round(value)),
                self.attendance_progress.value(), percentage, 420,
                lambda: setattr(self, "_progress_tween", None),
            )
            self.insight_percent.setText(f"{percentage}% del equipo registrado" if summary.active_workers else "Registra trabajadores para iniciar")
            rows = self.service.attendance_history(date.today(), date.today())
            self._fill_attendance_table(self.dashboard_table, rows)
            self.clear_database_error()
        except Exception as exc:
            self.set_database_error(self._error_detail(exc))

    def _build_workers(self) -> None:
        page = _page()
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
        self.worker_role = QComboBox(); self.worker_role.setMinimumWidth(150); self.worker_role.setEditable(False)
        self.worker_role.view().setObjectName("cargoPopup")
        self.worker_role.view().setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.worker_role.view().setFrameShape(QFrame.Shape.NoFrame)
        self.worker_role.view().setLineWidth(0)
        self.worker_role.addItem("Selecciona un cargo *", None)
        for role in BodeTimeService.DEFAULT_WAREHOUSE_ROLES:
            self.worker_role.addItem(role, role)
        self.add_cargo_button = QPushButton("+ Cargo")
        self.add_cargo_button.setToolTip("Agregar un cargo nuevo al catálogo compartido")
        self.add_cargo_button.clicked.connect(self.add_worker_role)
        cargo_field = QWidget()
        cargo_layout = QHBoxLayout(cargo_field)
        cargo_layout.setContentsMargins(0, 0, 0, 0)
        cargo_layout.setSpacing(6)
        cargo_layout.addWidget(self.worker_role, 1)
        cargo_layout.addWidget(self.add_cargo_button)
        self.worker_phone = QLineEdit(); self.worker_phone.setPlaceholderText("Teléfono"); self.worker_phone.setMaxLength(30)
        self.worker_phone.setValidator(QRegularExpressionValidator(QRegularExpression(r"\+?[0-9 ()-]{0,30}"), self.worker_phone))
        self.worker_phone.setToolTip("Entre 7 y 15 dígitos; puedes usar +, espacios, guiones o paréntesis.")
        for field, caption in [(self.worker_code, "Código *"), (self.worker_first, "Nombres *"), (self.worker_last, "Apellidos *"), (cargo_field, "Cargo"), (self.worker_phone, "Teléfono")]:
            group = QVBoxLayout(); group.addWidget(_label(caption, "muted")); group.addWidget(field); fields.addLayout(group, 1)
        form.addLayout(fields)
        buttons = QHBoxLayout()
        self.worker_save = QPushButton("Guardar trabajador"); self.worker_save.setObjectName("primary"); self.worker_save.clicked.connect(self.save_worker)
        clear = QPushButton("Limpiar"); clear.clicked.connect(self.clear_worker_form)
        self.worker_edit = QPushButton("Editar seleccionado"); self.worker_edit.clicked.connect(self.load_selected_worker)
        self.worker_status = QPushButton("Desactivar"); self.worker_status.setObjectName("danger"); self.worker_status.clicked.connect(self.toggle_selected_worker_status)
        self.worker_delete = QPushButton("Eliminar definitivo"); self.worker_delete.setObjectName("danger"); self.worker_delete.clicked.connect(self.delete_selected_worker)
        self.worker_edit.setEnabled(False); self.worker_status.setEnabled(False); self.worker_delete.setEnabled(False)
        for button in [self.worker_save, clear, self.worker_edit, self.worker_status, self.worker_delete]: buttons.addWidget(button)
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
            for field in [self.worker_code, self.worker_first, self.worker_last, self.worker_phone]:
                field.clear()
            self.worker_role.setCurrentIndex(0)
        self.worker_save.setText("Guardar cambios" if self.editing_worker_id is not None else "Guardar trabajador")
        self.worker_edit.setEnabled(row >= 0)
        self.worker_status.setEnabled(row >= 0)
        self.worker_delete.setEnabled(row >= 0)
        if row >= 0:
            active = self.workers_table.item(row, 5).text() == "Activo"
            self.worker_status.setText("Desactivar" if active else "Reactivar")
            self.worker_status.setObjectName("danger" if active else "primary")
            self.worker_status.style().unpolish(self.worker_status)
            self.worker_status.style().polish(self.worker_status)

    def refresh_workers(self, silent: bool = False) -> None:
        try:
            self.refresh_worker_roles()
            workers = self.service.list_workers()
            self.workers_table.setRowCount(0)
            for worker in workers:
                row = self.workers_table.rowCount(); self.workers_table.insertRow(row)
                for col, value in enumerate([worker.code, worker.first_name, worker.last_name, worker.role, worker.phone or "—", "Activo" if worker.active else "Inactivo"]):
                    _put(self.workers_table, row, col, value, worker.id if col == 0 else None)
            self.clear_database_error()
        except Exception as exc:
            self.set_database_error(self._error_detail(exc))

    def refresh_worker_roles(self) -> None:
        selected_role = self.worker_role.currentData() or ""
        self.worker_role.blockSignals(True)
        self.worker_role.clear()
        self.worker_role.addItem("Selecciona un cargo *", None)
        for role in self.service.list_roles():
            self.worker_role.addItem(role, role)
        index = self.worker_role.findData(selected_role) if selected_role else 0
        self.worker_role.setCurrentIndex(max(index, 0))
        self.worker_role.blockSignals(False)

    def save_worker(self) -> None:
        if self.editing_worker_id is not None:
            row = self.workers_table.currentRow()
            selected_id = self.workers_table.item(row, 0).data(Qt.ItemDataRole.UserRole) if row >= 0 else None
            if selected_id != self.editing_worker_id:
                self.clear_worker_form()
                QMessageBox.warning(self, "Selección cambió", "Vuelve a cargar el trabajador que deseas editar antes de guardar.")
                return
        values = (self.worker_code.text(), self.worker_first.text(), self.worker_last.text(), self.worker_role.currentData() or "", self.worker_phone.text())
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
        for field in [self.worker_code, self.worker_first, self.worker_last, self.worker_phone]: field.clear()
        self.worker_role.setCurrentIndex(0)
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
            role_index = self.worker_role.findData(worker.role)
            self.worker_role.setCurrentIndex(role_index if role_index >= 0 else 0)
            if role_index < 0:
                QMessageBox.warning(self, "Cargo fuera del catálogo", f"El cargo «{worker.role}» ya no está autorizado. Selecciona un cargo disponible antes de guardar.")
            self.worker_phone.setText(worker.phone or "")
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

    def _date_picker(self, selected: date) -> GlassDateEdit:
        picker = GlassDateEdit(
            QDate(selected.year, selected.month, selected.day),
            accent=self.accent_color,
            calendar_style=self.calendar_style,
            animated=self.motion_enabled,
        )
        self.date_pickers.append(picker)
        return picker

    def add_worker_role(self) -> None:
        name, accepted = QInputDialog.getText(
            self, "Agregar cargo", "Nombre del nuevo cargo de bodega:", QLineEdit.EchoMode.Normal,
        )
        if not accepted:
            return
        role = self._guard(self.service.add_custom_role, name)
        if not role:
            return
        self.refresh_worker_roles()
        index = self.worker_role.findData(role)
        if index >= 0:
            self.worker_role.setCurrentIndex(index)
        self.statusBar().showMessage(f"Cargo «{role}» agregado y seleccionado.", 6000)

    def manage_job_roles(self) -> None:
        dialog = JobRolesDialog(self.service, self)
        dialog.exec()
        self.refresh_worker_roles()

    def delete_selected_worker(self) -> None:
        row = self.workers_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Selecciona un trabajador", "Elige el trabajador que deseas eliminar.")
            return
        worker_id = self.workers_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        info = self._guard(self.service.worker_delete_info, worker_id)
        if info is None:
            return
        full_name, history_count = info
        warning = (
            f"¿Eliminar definitivamente a {full_name}?\n\n"
            f"También se borrarán {history_count} registro(s) de asistencia. Esta acción no se puede deshacer."
        )
        answer = QMessageBox.warning(
            self, "Eliminar trabajador y su historial", warning,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        deleted_count = self._guard(self.service.delete_worker, worker_id)
        if deleted_count is None:
            return
        QMessageBox.information(self, "Trabajador eliminado", f"El registro y {deleted_count} asistencia(s) asociada(s) se eliminaron definitivamente.")
        self.clear_worker_form()
        self.refresh_workers(); self.refresh_dashboard(); self.refresh_attendance_workers(); self.refresh_report_workers()

    def _build_attendance(self) -> None:
        page = _page(); layout = QVBoxLayout(page); layout.setContentsMargins(0, 0, 0, 0)
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
        self.att_start = self._date_picker(date.today() - timedelta(days=30))
        self.att_end = self._date_picker(date.today())
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
        page = _page(); layout = QVBoxLayout(page); layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(_label("Reportes", "pageTitle"))
        layout.addWidget(_label("Consulta MySQL y exporta los marcajes filtrados a PDF o Excel", "muted"))
        panel = _panel(); box = QVBoxLayout(panel); box.setContentsMargins(20, 20, 20, 20)
        box.addWidget(_label("Criterios del reporte", "sectionTitle"))
        filters = QHBoxLayout()
        self.report_start = self._date_picker(date.today() - timedelta(days=30))
        self.report_end = self._date_picker(date.today())
        self.report_worker = QComboBox(); self.report_worker.addItem("Todos los trabajadores", None); self.report_worker.setMinimumWidth(280)
        for text, widget in [("Desde", self.report_start), ("Hasta", self.report_end), ("Trabajador", self.report_worker)]:
            group = QVBoxLayout(); group.addWidget(_label(text, "muted")); group.addWidget(widget); filters.addLayout(group, 1)
        box.addLayout(filters)
        actions = QHBoxLayout(); actions.addStretch(1)
        self.generate_excel_button = QPushButton("Generar Excel")
        self.generate_excel_button.setObjectName("secondary")
        self.generate_excel_button.clicked.connect(self.generate_excel_report)
        self.generate_pdf_button = QPushButton("Generar PDF")
        self.generate_pdf_button.setObjectName("primary")
        self.generate_pdf_button.clicked.connect(self.generate_report)
        actions.addWidget(self.generate_excel_button)
        actions.addWidget(self.generate_pdf_button)
        box.addLayout(actions)
        layout.addWidget(panel)
        layout.addWidget(_label("Los archivos incluyen encabezados, fechas, filtro de trabajador y hora de generación.", "muted"))
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

    def _report_data_for_export(self):
        start, end = self.report_start.date().toPython(), self.report_end.date().toPython()
        rows = self._guard(self.service.attendance_history, start, end, self.report_worker.currentData())
        if rows is None:
            return None
        if not rows:
            QMessageBox.information(self, "Sin resultados", "No hay asistencias para esos filtros. No se generó un archivo vacío.")
            return None
        worker_label = self.report_worker.currentText() if self.report_worker.currentData() is not None else "Todos"
        return start, end, rows, worker_label

    def generate_report(self) -> None:
        report = self._report_data_for_export()
        if report is None:
            return
        start, end, rows, worker_label = report
        suggested = Path.home() / "Documents" / f"BODETIME_asistencia_{start:%Y%m%d}_{end:%Y%m%d}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Guardar reporte PDF", str(suggested), "Documento PDF (*.pdf)")
        if not path:
            return
        if not path.lower().endswith(".pdf"): path += ".pdf"
        try:
            result = generate_attendance_pdf(path, rows, start, end, worker_label)
        except Exception as exc:
            QMessageBox.critical(self, "Error al generar el PDF", str(exc)); return
        answer = QMessageBox.information(self, "Reporte generado", f"Se generó el reporte con {len(rows)} registros.\n\n{result}\n\n¿Deseas abrirlo ahora?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
        if answer == QMessageBox.StandardButton.Yes: QDesktopServices.openUrl(QUrl.fromLocalFile(str(result)))

    def generate_excel_report(self) -> None:
        report = self._report_data_for_export()
        if report is None:
            return
        start, end, rows, worker_label = report
        suggested = Path.home() / "Documents" / f"BODETIME_asistencia_{start:%Y%m%d}_{end:%Y%m%d}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "Guardar reporte Excel", str(suggested), "Libro de Excel (*.xlsx)")
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            result = generate_attendance_xlsx(path, rows, start, end, worker_label)
        except Exception as exc:
            QMessageBox.critical(self, "Error al generar Excel", str(exc)); return
        answer = QMessageBox.information(self, "Reporte Excel generado", f"Se exportaron {len(rows)} registros.\n\n{result}\n\n¿Deseas abrir el archivo ahora?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
        if answer == QMessageBox.StandardButton.Yes: QDesktopServices.openUrl(QUrl.fromLocalFile(str(result)))

    def _build_settings(self) -> None:
        page = _page()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        content.setObjectName("settingsContent")
        content.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 2, 0)
        scroll.setWidget(content)
        page_layout.addWidget(scroll)
        layout.addWidget(_label("Configuración", "pageTitle"))
        subtitle = _label("Personaliza la apariencia y los valores de la jornada", "muted")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)

        appearance_panel = _panel()
        appearance_box = QVBoxLayout(appearance_panel)
        appearance_box.setContentsMargins(20, 16, 20, 16)
        appearance_box.setSpacing(10)
        appearance_box.addWidget(_label("Apariencia", "sectionTitle"))
        appearance_row = QHBoxLayout()
        theme_group = QVBoxLayout()
        theme_group.addWidget(_label("Tema", "muted"))
        self.theme_selector = QComboBox()
        self.theme_selector.addItem("Claro", "light")
        self.theme_selector.addItem("Oscuro", "dark")
        self.theme_selector.setCurrentIndex(max(0, self.theme_selector.findData(self.theme_mode)))
        self.theme_selector.currentIndexChanged.connect(self._on_theme_changed)
        theme_group.addWidget(self.theme_selector)
        appearance_row.addLayout(theme_group)

        accent_group = QVBoxLayout()
        accent_group.addWidget(_label("Color principal", "muted"))
        self.accent_selector = QComboBox()
        self._populate_accent_selector(self.accent_color)
        self.accent_selector.activated.connect(self._on_accent_activated)
        accent_group.addWidget(self.accent_selector)
        appearance_row.addLayout(accent_group)
        appearance_row.addStretch(1)

        self.animations_toggle = QCheckBox("Transiciones suaves")
        self.animations_toggle.setChecked(self.motion_enabled)
        self.animations_toggle.toggled.connect(self._on_animations_toggled)
        appearance_row.addWidget(self.animations_toggle, 0, Qt.AlignmentFlag.AlignVCenter)
        appearance_box.addLayout(appearance_row)
        calendar_row = QHBoxLayout()
        calendar_group = QVBoxLayout()
        calendar_group.addWidget(_label("Estilo del calendario", "muted"))
        self.calendar_style_selector = QComboBox()
        self.calendar_style_selector.addItem("Cristal claro", "glass")
        self.calendar_style_selector.addItem("Blanco clásico", "classic")
        self.calendar_style_selector.setCurrentIndex(max(0, self.calendar_style_selector.findData(self.calendar_style)))
        self.calendar_style_selector.currentIndexChanged.connect(self._on_calendar_style_changed)
        calendar_group.addWidget(self.calendar_style_selector)
        calendar_row.addLayout(calendar_group)
        calendar_note = _label("El calendario se abre como una tarjeta flotante y ofrece un acceso rápido a Hoy.", "muted")
        calendar_note.setWordWrap(True)
        calendar_row.addWidget(calendar_note, 1, Qt.AlignmentFlag.AlignVCenter)
        appearance_box.addLayout(calendar_row)
        clock_row = QHBoxLayout()
        clock_group = QVBoxLayout()
        clock_group.addWidget(_label("Estilo del reloj", "muted"))
        self.clock_style_selector = QComboBox()
        self.clock_style_selector.addItem("Digital", "digital")
        self.clock_style_selector.addItem("Analógico", "analog")
        self.clock_style_selector.setCurrentIndex(max(0, self.clock_style_selector.findData(self.clock_style)))
        self.clock_style_selector.currentIndexChanged.connect(self._on_clock_style_changed)
        clock_group.addWidget(self.clock_style_selector)
        clock_row.addLayout(clock_group)
        clock_note = _label("El panel muestra un solo estilo de reloj a la vez.", "muted")
        clock_note.setWordWrap(True)
        clock_row.addWidget(clock_note, 1, Qt.AlignmentFlag.AlignVCenter)
        appearance_box.addLayout(clock_row)
        preview_row = QHBoxLayout()
        self.accent_preview = _label(f"Acento actual · {self.accent_color.upper()}", "accentPreview")
        self.accent_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.accent_preview.setMaximumWidth(280)
        preview_row.addWidget(self.accent_preview)
        preview_note = _label("Puedes cambiar el tema y el color en cualquier momento.", "muted")
        preview_note.setWordWrap(True)
        preview_row.addWidget(preview_note, 1)
        appearance_box.addLayout(preview_row)
        animation_note = _label("Las transiciones son breves, se pueden desactivar y usan el motor de animación de Qt.", "muted")
        animation_note.setWordWrap(True)
        appearance_box.addWidget(animation_note)
        layout.addWidget(appearance_panel)

        panel = _panel(); box = QVBoxLayout(panel); box.setContentsMargins(22, 18, 22, 18); box.setSpacing(12)
        box.addWidget(_label("Horario de trabajo", "sectionTitle"))
        row = QHBoxLayout()
        self.schedule_time = QTimeEdit(); self.schedule_time.setDisplayFormat("HH:mm")
        self.schedule_time.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.schedule_tolerance = QSpinBox(); self.schedule_tolerance.setRange(0, 240); self.schedule_tolerance.setSuffix(" minutos")
        self.schedule_tolerance.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        for text, widget in [("Hora oficial de entrada", self.schedule_time), ("Tolerancia de tardanza", self.schedule_tolerance)]:
            group = QVBoxLayout(); group.addWidget(_label(text, "muted")); group.addWidget(widget); row.addLayout(group)
        row.addStretch(1); box.addLayout(row)
        save = QPushButton("Guardar configuración"); save.setObjectName("primary"); save.clicked.connect(self.save_settings); box.addWidget(save, 0, Qt.AlignmentFlag.AlignLeft)
        schedule_note = _label("Una llegada se marca tarde cuando supera la hora de inicio más la tolerancia. El cambio se aplica a los marcajes futuros.", "muted")
        schedule_note.setWordWrap(True)
        box.addWidget(schedule_note)
        self.schedule_status = _label("El horario debe confirmarse con la bodega antes de guardar.", "muted")
        self.schedule_status.setWordWrap(True)
        box.addWidget(self.schedule_status)
        layout.addWidget(panel)
        roles_panel = _panel()
        roles_box = QHBoxLayout(roles_panel)
        roles_box.setContentsMargins(20, 15, 20, 15)
        roles_box.addWidget(_label("Cargos de bodega", "sectionTitle"))
        role_note = _label("Los cargos nuevos se comparten mediante MySQL.", "muted")
        role_note.setWordWrap(True)
        roles_box.addWidget(role_note, 1)
        self.manage_roles_button = QPushButton("Editar cargos")
        self.manage_roles_button.setObjectName("primary")
        self.manage_roles_button.clicked.connect(self.manage_job_roles)
        roles_box.addWidget(self.manage_roles_button)
        layout.addWidget(roles_panel)

        update_panel = _panel()
        update_box = QVBoxLayout(update_panel)
        update_box.setContentsMargins(20, 15, 20, 15)
        update_box.setSpacing(8)
        update_box.addWidget(_label("Actualizaciones", "sectionTitle"))
        update_note = _label("Buscar e instalar consulta las versiones publicadas y, si hay una nueva, descarga el instalador verificado para completar la actualización. Tus datos se conservan.", "muted")
        update_note.setWordWrap(True)
        update_box.addWidget(update_note)
        update_row = QHBoxLayout()
        self.update_status = _label(f"Versión instalada: {APP_VERSION}", "muted")
        update_row.addWidget(self.update_status, 1)
        self.check_updates_button = QPushButton("Buscar e instalar")
        self.check_updates_button.setObjectName("primary")
        self.check_updates_button.setToolTip("Busca una versión nueva y te pregunta antes de descargarla")
        self.check_updates_button.clicked.connect(lambda: self.check_for_updates(manual=True, install_if_available=True))
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


def run_app(
    service: BodeTimeService,
    database_error: str | None = None,
    splash: SplashScreen | None = None,
    application: QApplication | None = None,
) -> int:
    app = application or QApplication.instance() or QApplication([])
    app.setOrganizationName("BODETIME")
    app.setApplicationName("BODETIME")
    app.setStyle("Fusion")
    window = MainWindow(service, database_error)
    window.show()
    if splash is not None:
        QTimer.singleShot(140, splash.fade_out)
    return app.exec()
