"""Selector de fecha con calendario flotante animado y estilo claro."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QDate, QLocale, QPoint, QRect, Qt, QParallelAnimationGroup, QPropertyAnimation, Signal
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import (
    QCalendarWidget,
    QDateEdit,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QToolButton,
    QTableView,
    QVBoxLayout,
    QWidget,
    QAbstractSpinBox,
    QApplication,
)

from .appearance import build_calendar_stylesheet


MONTHS = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


class CalendarPopover(QDialog):
    """Calendario blanco que aparece como una tarjeta flotante."""

    date_selected = Signal(QDate)

    def __init__(self, accent: str, style: str, animated: bool, parent: QWidget | None = None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.accent = accent
        self.calendar_style = style
        self.animated = animated
        self._transition: QParallelAnimationGroup | None = None
        self._closing = False
        self.setObjectName("calendarPopover")
        # Solo las esquinas exteriores son transparentes; el calendario y su cuadrícula
        # se pintan con fondos sólidos para que el contenido de atrás no se filtre.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(False)
        self.setStyleSheet(build_calendar_stylesheet(accent, style))

        surface = QFrame(self)
        surface.setObjectName("calendarSurface")
        surface.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        surface.setAutoFillBackground(True)

        layout = QVBoxLayout(surface)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(8)
        eyebrow = QLabel("SELECCIONA UNA FECHA")
        eyebrow.setObjectName("calendarEyebrow")
        layout.addWidget(eyebrow)

        header = QHBoxLayout()
        self.previous_button = QToolButton()
        self.previous_button.setObjectName("calendarNav")
        self.previous_button.setText("‹")
        self.previous_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.month_label = QLabel()
        self.month_label.setObjectName("calendarMonth")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.next_button = QToolButton()
        self.next_button.setObjectName("calendarNav")
        self.next_button.setText("›")
        self.next_button.setCursor(Qt.CursorShape.PointingHandCursor)
        header.addWidget(self.previous_button)
        header.addWidget(self.month_label, 1)
        header.addWidget(self.next_button)
        layout.addLayout(header)

        self.calendar = QCalendarWidget()
        self.calendar.setObjectName("glassCalendar")
        self.calendar.setLocale(QLocale("es_NI"))
        self.calendar.setNavigationBarVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.ShortDayNames)
        self.calendar.setFirstDayOfWeek(Qt.DayOfWeek.Monday)
        self.calendar.setGridVisible(False)
        self.calendar.setMinimumSize(324, 280)
        self._apply_calendar_palette()
        self.calendar.currentPageChanged.connect(self._update_month_label)
        self.calendar.clicked.connect(self._select_date)
        self.previous_button.clicked.connect(self.calendar.showPreviousMonth)
        self.next_button.clicked.connect(self.calendar.showNextMonth)
        layout.addWidget(self.calendar)

        footer = QHBoxLayout()
        footer.addStretch(1)
        today = QPushButton("Hoy")
        today.setObjectName("calendarToday")
        today.setCursor(Qt.CursorShape.PointingHandCursor)
        today.clicked.connect(self._select_today)
        footer.addWidget(today)
        layout.addLayout(footer)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.addWidget(surface)
        self.setFixedSize(376, 414)
        self._update_month_label(self.calendar.yearShown(), self.calendar.monthShown())

    def _apply_calendar_palette(self) -> None:
        """Asegura fondos opacos en el calendario y su tabla interna."""
        background = QColor("#FBFCFB" if self.calendar_style == "glass" else "#FFFFFF")
        widgets = [self.calendar]
        calendar_view = self.calendar.findChild(QTableView)
        if calendar_view is not None:
            widgets.extend((calendar_view, calendar_view.viewport()))
        for widget in widgets:
            widget.setAutoFillBackground(True)
            widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            palette = widget.palette()
            for role in (QPalette.ColorRole.Window, QPalette.ColorRole.Base, QPalette.ColorRole.AlternateBase):
                palette.setColor(role, background)
            widget.setPalette(palette)
        if calendar_view is not None:
            calendar_view.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
            calendar_view.viewport().setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
            calendar_view.viewport().setStyleSheet(f"background-color: {background.name()};")

    def _update_month_label(self, year: int, month: int) -> None:
        self.month_label.setText(f"{MONTHS[month - 1].capitalize()} {year}")

    def show_for(self, anchor: QWidget, selected: QDate) -> None:
        self._closing = False
        if self._transition is not None:
            self._transition.stop()
            self._transition.deleteLater()
            self._transition = None
        self.calendar.setSelectedDate(selected)
        self.calendar.setCurrentPage(selected.year(), selected.month())
        anchor_rect = QRect(anchor.mapToGlobal(QPoint(0, 0)), anchor.size())
        screen = QApplication.screenAt(anchor_rect.center()) or QApplication.primaryScreen()
        available = screen.availableGeometry() if screen else QRect(anchor_rect.topLeft(), self.size())
        width, height = self.width(), self.height()
        x = min(max(anchor_rect.left(), available.left() + 8), available.right() - width - 8)
        y = anchor_rect.bottom() + 7
        if y + height > available.bottom() - 8:
            y = anchor_rect.top() - height - 7
        y = min(max(y, available.top() + 8), available.bottom() - height - 8)
        target = QRect(x, y, width, height)
        self.setGeometry(target)
        self.show()
        self.raise_()
        if not self.animated:
            return
        inset = 0.94
        initial_width, initial_height = round(width * inset), round(height * inset)
        initial = QRect(
            target.center().x() - initial_width // 2,
            target.center().y() - initial_height // 2,
            initial_width,
            initial_height,
        )
        self.setGeometry(initial)
        self._transition = QParallelAnimationGroup(self)
        geometry = QPropertyAnimation(self, b"geometry", self._transition)
        geometry.setDuration(245)
        geometry.setStartValue(initial)
        geometry.setEndValue(target)
        geometry.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._transition.addAnimation(geometry)
        self._transition.start()

    def _select_date(self, selected: QDate) -> None:
        self.date_selected.emit(selected)
        self.dismiss()

    def _select_today(self) -> None:
        today = QDate.currentDate()
        self.date_selected.emit(today)
        self.dismiss()

    def dismiss(self) -> None:
        if not self.isVisible() or not self.animated or self._closing:
            self.hide()
            return
        self._closing = True
        if self._transition is not None:
            self._transition.stop()
        start = self.geometry()
        factor = 0.96
        small_width, small_height = round(start.width() * factor), round(start.height() * factor)
        end = QRect(
            start.center().x() - small_width // 2,
            start.center().y() - small_height // 2,
            small_width,
            small_height,
        )
        self._transition = QParallelAnimationGroup(self)
        geometry = QPropertyAnimation(self, b"geometry", self._transition)
        geometry.setDuration(145)
        geometry.setStartValue(start)
        geometry.setEndValue(end)
        geometry.setEasingCurve(QEasingCurve.Type.InCubic)
        self._transition.addAnimation(geometry)
        self._transition.finished.connect(self.hide)
        self._transition.start()

    def hideEvent(self, event) -> None:
        if self._transition is not None and not self._closing:
            self._transition.stop()
        super().hideEvent(event)


class GlassDateEdit(QDateEdit):
    """Campo de fecha de solo lectura con un botón y calendario animado."""

    def __init__(
        self,
        selected: QDate,
        accent: str = "#16877B",
        calendar_style: str = "glass",
        animated: bool = True,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(selected, parent)
        self.setObjectName("glassDateEdit")
        self.setCalendarPopup(False)
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.NoButtons)
        self.setReadOnly(True)
        self.setDisplayFormat("dd/MM/yyyy")
        self.setMinimumWidth(150)
        self.accent = accent
        self.calendar_style = calendar_style
        self.animated = animated
        self._popover: CalendarPopover | None = None
        self.calendar_button = QToolButton(self)
        self.calendar_button.setObjectName("calendarTrigger")
        self.calendar_button.setText("▦")
        self.calendar_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.calendar_button.setToolTip("Abrir calendario")
        self.calendar_button.clicked.connect(self.open_calendar)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        height = min(30, max(24, self.height() - 10))
        self.calendar_button.setGeometry(self.width() - height - 6, (self.height() - height) // 2, height, height)

    def mousePressEvent(self, event) -> None:
        self.open_calendar()
        event.accept()

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Space, Qt.Key.Key_Down):
            self.open_calendar()
            event.accept()
            return
        super().keyPressEvent(event)

    def set_calendar_style(self, accent: str, style: str, animated: bool) -> None:
        self.accent = accent
        self.calendar_style = style
        self.animated = animated
        if self._popover is not None:
            self._popover.accent = accent
            self._popover.calendar_style = style
            self._popover.animated = animated
            self._popover.setStyleSheet(build_calendar_stylesheet(accent, style))
            self._popover._apply_calendar_palette()

    def open_calendar(self) -> None:
        if self._popover is None:
            self._popover = CalendarPopover(self.accent, self.calendar_style, self.animated, self.window())
            self._popover.date_selected.connect(self.setDate)
        else:
            self._popover.setStyleSheet(build_calendar_stylesheet(self.accent, self.calendar_style))
            self._popover.animated = self.animated
            self._popover._apply_calendar_palette()
        self._popover.show_for(self, self.date())
