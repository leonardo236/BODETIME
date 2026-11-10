"""Selector de fecha con calendario flotante animado y estilo claro."""

from __future__ import annotations

import sys
import ctypes
from ctypes import wintypes

from PySide6.QtCore import QEasingCurve, QDate, QLocale, QPoint, QRect, QRectF, Qt, QParallelAnimationGroup, QPropertyAnimation, QVariantAnimation, Signal
from PySide6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath, QPalette, QPen, QRegion
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
    QGraphicsDropShadowEffect,
)

from .appearance import build_calendar_stylesheet


MONTHS = (
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
)


class CalendarSurface(QFrame):
    """Superficie clara con brillo suave; el modo clásico queda blanco sólido."""

    def __init__(self, style: str, theme_mode: str = "light", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.calendar_style = style
        self.theme_mode = theme_mode
        self.setObjectName("calendarSurface")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFrameShape(QFrame.Shape.NoFrame)

    def set_calendar_style(self, style: str) -> None:
        self.calendar_style = style
        self.update()

    def paintEvent(self, event) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(1, 1, -1, -1)
        path = QPainterPath()
        path.addRoundedRect(rect, 22, 22)
        if self.calendar_style == "classic":
            painter.fillPath(path, QColor("#FFFFFF"))
            border = QColor("#E4EAE7")
        elif self.theme_mode == "dark":
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0.0, QColor(45, 45, 48, 226))
            gradient.setColorAt(0.5, QColor(31, 31, 34, 212))
            gradient.setColorAt(1.0, QColor(24, 24, 26, 198))
            painter.fillPath(path, gradient)
            border = QColor(255, 255, 255, 72)
            painter.save()
            painter.setClipPath(path)
            painter.setPen(QPen(QColor(255, 255, 255, 36), 1))
            painter.drawLine(rect.left() + 18, rect.top() + 2, rect.right() - 18, rect.top() + 2)
            painter.restore()
        else:
            gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
            gradient.setColorAt(0.0, QColor(255, 255, 255, 226))
            gradient.setColorAt(0.48, QColor(248, 248, 250, 212))
            gradient.setColorAt(1.0, QColor(231, 232, 237, 198))
            painter.fillPath(path, gradient)
            border = QColor(255, 255, 255, 244)
            painter.save()
            painter.setClipPath(path)
            painter.setPen(QPen(QColor(255, 255, 255, 150), 1))
            painter.drawLine(rect.left() + 18, rect.top() + 2, rect.right() - 18, rect.top() + 2)
            painter.restore()
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(border, 1))
        painter.drawPath(path)
        painter.end()


class CalendarPopover(QDialog):
    """Calendario que aparece como una tarjeta flotante animada."""

    date_selected = Signal(QDate)

    def __init__(self, accent: str, style: str, animated: bool, theme_mode: str = "light", parent: QWidget | None = None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.accent = accent
        self.calendar_style = style
        self.animated = animated
        self.theme_mode = theme_mode
        self._transition: QParallelAnimationGroup | None = None
        self._reveal_scale = 1.0
        self._closing = False
        self.setObjectName("calendarPopover")
        # Solo las esquinas exteriores son transparentes; el calendario y su cuadrícula
        # se pintan con fondos sólidos para que el contenido de atrás no se filtre.
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setAutoFillBackground(False)
        self.setStyleSheet(build_calendar_stylesheet(accent, style, theme_mode))

        surface = CalendarSurface(style, theme_mode, self)
        self.surface = surface
        shadow = QGraphicsDropShadowEffect(surface)
        shadow.setBlurRadius(18)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(18, 45, 48, 48))
        surface.setGraphicsEffect(shadow)

        layout = QVBoxLayout(surface)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(8)
        eyebrow = QLabel("SELECCIONA UNA FECHA")
        eyebrow.setObjectName("calendarEyebrow")
        eyebrow.setAutoFillBackground(False)
        layout.addWidget(eyebrow)

        header = QHBoxLayout()
        self.previous_button = QToolButton()
        self.previous_button.setObjectName("calendarNav")
        self.previous_button.setText("‹")
        self.previous_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.month_label = QLabel()
        self.month_label.setObjectName("calendarMonth")
        self.month_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.month_label.setAutoFillBackground(False)
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
        self.calendar.setMinimumSize(324, 210)
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
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(surface)
        self.setFixedSize(384, 352)
        self._update_month_label(self.calendar.yearShown(), self.calendar.monthShown())

    def _apply_calendar_palette(self) -> None:
        """Asegura fondos opacos en el calendario y su tabla interna."""
        if self.calendar_style == "classic" or self.theme_mode == "light":
            background = QColor("#FFFFFF" if self.calendar_style == "classic" else "#FBFBFC")
            text = QColor("#1D1D1F")
        else:
            background = QColor("#1C1C1E")
            text = QColor("#F5F5F7")
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
            palette.setColor(QPalette.ColorRole.Text, text)
            palette.setColor(QPalette.ColorRole.WindowText, text)
            widget.setPalette(palette)
        if calendar_view is not None:
            calendar_view.setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
            calendar_view.viewport().setAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent, True)
            calendar_view.viewport().setStyleSheet(f"background-color: {background.name()};")

    def _update_month_label(self, year: int, month: int) -> None:
        self.month_label.setText(f"{MONTHS[month - 1].capitalize()} {year}")

    def _enable_windows_backdrop(self) -> None:
        """Pide Desktop Acrylic para el popup; los demás Windows usan el degradado Qt."""
        self.native_blur_enabled = False
        if sys.platform != "win32":
            return
        try:
            hwnd = int(self.winId())
            dwm = ctypes.windll.dwmapi
            dwm.DwmSetWindowAttribute.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
            dwm.DwmSetWindowAttribute.restype = ctypes.c_long
            dark_mode = ctypes.c_int(1 if self.theme_mode == "dark" else 0)
            dwm.DwmSetWindowAttribute(wintypes.HWND(hwnd), 20, ctypes.byref(dark_mode), ctypes.sizeof(dark_mode))
            rounded = ctypes.c_int(2)  # DWMWCP_ROUND
            dwm.DwmSetWindowAttribute(wintypes.HWND(hwnd), 33, ctypes.byref(rounded), ctypes.sizeof(rounded))
            backdrop = ctypes.c_int(3)  # DWMSBT_TRANSIENTWINDOW: Acrylic en Windows 11 22H2+
            result = dwm.DwmSetWindowAttribute(wintypes.HWND(hwnd), 38, ctypes.byref(backdrop), ctypes.sizeof(backdrop))
            self.native_blur_enabled = result == 0
        except (AttributeError, OSError, TypeError, ValueError):
            # El material nativo no existe en versiones anteriores; el estilo Qt sigue funcionando.
            return

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
        max_x = available.right() + 1 - width - 8
        x = min(max(anchor_rect.left(), available.left() + 8), max_x)
        below = anchor_rect.bottom() + 8
        above = anchor_rect.top() - height - 8
        if below + height <= available.bottom() + 1 - 8:
            y = below
        elif above >= available.top() + 8:
            y = above
        else:
            room_below = available.bottom() + 1 - 8 - below
            room_above = anchor_rect.top() - available.top() - 8
            y = below if room_below >= room_above else above
        y = min(max(y, available.top() + 8), available.bottom() + 1 - height - 8)
        target = QRect(x, y, width, height)
        self.setGeometry(target)
        self._enable_windows_backdrop()
        self.setWindowOpacity(0.0 if self.animated else 1.0)
        if self.animated:
            self._apply_reveal(0.88)
        else:
            self.clearMask()
        self.show()
        self.raise_()
        if not self.animated:
            return
        self._transition = QParallelAnimationGroup(self)
        reveal = QVariantAnimation(self._transition)
        reveal.setDuration(310)
        reveal.setStartValue(0.88)
        reveal.setEndValue(1.0)
        reveal.setEasingCurve(QEasingCurve.Type.OutCubic)
        reveal.valueChanged.connect(lambda value: self._apply_reveal(float(value)))
        self._transition.addAnimation(reveal)
        opacity = QPropertyAnimation(self, b"windowOpacity", self._transition)
        opacity.setDuration(250)
        opacity.setStartValue(0.0)
        opacity.setEndValue(1.0)
        opacity.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._transition.addAnimation(opacity)
        self._transition.finished.connect(self.clearMask)
        self._transition.start()

    def _apply_reveal(self, scale: float) -> None:
        """Expande una máscara redondeada sin redimensionar la cuadrícula de fechas."""
        self._reveal_scale = max(0.0, min(1.0, scale))
        if self._reveal_scale >= 0.999:
            self.clearMask()
            return
        rect = QRectF(self.rect())
        inset_x = rect.width() * (1.0 - self._reveal_scale) / 2
        inset_y = rect.height() * (1.0 - self._reveal_scale) / 2
        rect.adjust(inset_x, inset_y, -inset_x, -inset_y)
        path = QPainterPath()
        radius = min(24.0, rect.width() * 0.08)
        path.addRoundedRect(rect, radius, radius)
        self.setMask(QRegion(path.toFillPolygon().toPolygon()))

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
        self._transition = QParallelAnimationGroup(self)
        reveal = QVariantAnimation(self._transition)
        reveal.setDuration(180)
        reveal.setStartValue(self._reveal_scale)
        reveal.setEndValue(0.94)
        reveal.setEasingCurve(QEasingCurve.Type.InCubic)
        reveal.valueChanged.connect(lambda value: self._apply_reveal(float(value)))
        self._transition.addAnimation(reveal)
        opacity = QPropertyAnimation(self, b"windowOpacity", self._transition)
        opacity.setDuration(160)
        opacity.setStartValue(self.windowOpacity())
        opacity.setEndValue(0.0)
        opacity.setEasingCurve(QEasingCurve.Type.InCubic)
        self._transition.addAnimation(opacity)
        self._transition.finished.connect(self._finish_dismiss)
        self._transition.start()

    def _finish_dismiss(self) -> None:
        self.clearMask()
        self.hide()

    def hideEvent(self, event) -> None:
        if self._transition is not None and not self._closing:
            self._transition.stop()
        super().hideEvent(event)


class GlassDateEdit(QDateEdit):
    """Campo de fecha de solo lectura con un botón y calendario animado."""

    def __init__(
        self,
        selected: QDate,
        accent: str = "#007AFF",
        calendar_style: str = "glass",
        animated: bool = True,
        theme_mode: str = "light",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(selected, parent)
        self.setObjectName("glassDateEdit")
        self.setCalendarPopup(False)
        # Qt reserva el campo de texto al activar los subcontroles; el QSS los oculta.
        self.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.UpDownArrows)
        self.setReadOnly(True)
        self.setDisplayFormat("dd/MM/yyyy")
        self.setMinimumWidth(150)
        self.accent = accent
        self.calendar_style = calendar_style
        self.animated = animated
        self.theme_mode = theme_mode
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

    def set_calendar_style(self, accent: str, style: str, animated: bool, theme_mode: str | None = None) -> None:
        self.accent = accent
        self.calendar_style = style
        self.animated = animated
        if theme_mode in {"light", "dark"}:
            self.theme_mode = theme_mode
        if self._popover is not None:
            self._popover.accent = accent
            self._popover.calendar_style = style
            self._popover.animated = animated
            self._popover.theme_mode = self.theme_mode
            self._popover.setStyleSheet(build_calendar_stylesheet(accent, style, self.theme_mode))
            self._popover.surface.set_calendar_style(style)
            self._popover.surface.theme_mode = self.theme_mode
            self._popover._apply_calendar_palette()

    def open_calendar(self) -> None:
        if self._popover is None:
            self._popover = CalendarPopover(self.accent, self.calendar_style, self.animated, self.theme_mode, self.window())
            self._popover.date_selected.connect(self.setDate)
        else:
            self._popover.theme_mode = self.theme_mode
            self._popover.setStyleSheet(build_calendar_stylesheet(self.accent, self.calendar_style, self.theme_mode))
            self._popover.animated = self.animated
            self._popover.surface.set_calendar_style(self.calendar_style)
            self._popover.surface.theme_mode = self.theme_mode
            self._popover._apply_calendar_palette()
        self._popover.show_for(self, self.date())
