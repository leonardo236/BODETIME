"""Paleta y hoja de estilos de BODETIME, con preferencias por usuario."""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QFontDatabase


ACCENT_PRESETS = (
    ("Azul sistema", "#007AFF"),
    ("Índigo", "#5856D6"),
    ("Verde", "#34C759"),
    ("Turquesa", "#30B0C7"),
    ("Grafito", "#536579"),
)


def apply_platform_font(application) -> None:
    """Usa la tipografía de interfaz del sistema en vez de distribuir otra fuente."""
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont)
    if not font.family():
        font = QFont("Segoe UI")
    application.setFont(font)


def _mix(first: str, second: str, amount: float) -> str:
    """Mezcla dos colores; amount indica cuánto se conserva del primero."""
    a, b = QColor(first), QColor(second)
    return QColor(
        round(a.red() * amount + b.red() * (1 - amount)),
        round(a.green() * amount + b.green() * (1 - amount)),
        round(a.blue() * amount + b.blue() * (1 - amount)),
    ).name()


def _luminance(color: QColor) -> float:
    channels = (color.redF(), color.greenF(), color.blueF())
    linear = tuple(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4 for value in channels)
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _accent_text(color: QColor) -> str:
    dark = QColor("#172033")
    value, dark_value = _luminance(color), _luminance(dark)
    white_contrast = 1.05 / (value + 0.05)
    dark_contrast = (value + 0.05) / (dark_value + 0.05) if value >= dark_value else (dark_value + 0.05) / (value + 0.05)
    return "#FFFFFF" if white_contrast >= dark_contrast else dark.name()


def build_stylesheet(mode: str = "light", accent: str = "#007AFF") -> str:
    """Genera estilos accesibles para modo claro u oscuro y un acento elegido."""
    dark = mode == "dark"
    chosen = QColor(accent)
    if not chosen.isValid():
        chosen = QColor("#007AFF")
    accent = chosen.name()
    accent_hover = chosen.lighter(118).name() if dark else chosen.darker(112).name()
    accent_text = _accent_text(chosen)
    sidebar_top = "#0B0B0C" if dark else "#171719"
    sidebar_bottom = "#1C1C1E" if dark else "#252527"

    colors = {
        "background": "#000000" if dark else "#F5F5F7",
        "panel": "#1C1C1E" if dark else "#FFFFFF",
        "panel_alt": "#2C2C2E" if dark else "#F0F0F2",
        "field": "#1C1C1E" if dark else "#FFFFFF",
        "text": "#F5F5F7" if dark else "#1D1D1F",
        "muted": "#A1A1A6" if dark else "#6E6E73",
        "subtle": "#8E8E93",
        "border": "#38383A" if dark else "#D2D2D7",
        "line": "#2C2C2E" if dark else "#E5E5EA",
        "header": "#2C2C2E" if dark else "#F2F2F7",
        "soft": _mix(accent, "#2C2C2E", 0.18) if dark else _mix(accent, "#FFFFFF", 0.12),
        "soft_hover": _mix(accent, "#38383A", 0.26) if dark else _mix(accent, "#FFFFFF", 0.20),
        "sidebar_text": "#E7EDF5",
        "sidebar_muted": "#AFBDCC",
        "sidebar_hover": "#26384D" if dark else "#2B4868",
        "danger_bg": "#482C2C" if dark else "#FBEAE7",
        "danger_text": "#F3A59C" if dark else "#A63831",
        "focus": chosen.lighter(140).name() if dark else chosen.name(),
        "clock_border": "#526071" if dark else "#E1E6ED",
    }
    return f"""
QWidget {{ font-size: 10pt; color: {colors['text']}; }}
QMainWindow {{ background: {colors['background']}; }}
QWidget#content {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {colors['background']}, stop:1 {colors['panel_alt']}); }}
QStackedWidget {{ background: {colors['background']}; border: 0; }}
QStackedWidget > QWidget#pageSurface {{ background: {colors['background']}; }}
QDialog {{ background: {colors['background']}; }}
QWidget#sidebar {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {sidebar_top}, stop:1 {sidebar_bottom}); }}
QWidget#brandMark {{ background: transparent; border: 0; }}
QLabel#brand {{ color: white; font-size: 17pt; font-weight: 750; }}
QLabel#brandSub {{ color: {colors['sidebar_muted']}; font-size: 8pt; letter-spacing: 1px; }}
QLabel#navCaption {{ color: {colors['sidebar_muted']}; font-size: 8pt; font-weight: 700; letter-spacing: 1.2px; padding: 22px 12px 7px; }}
QFrame#sideRule {{ background: {colors['clock_border']}; max-height: 1px; }}
QPushButton#nav {{ color: {colors['sidebar_text']}; background: transparent; border: 0; border-left: 3px solid transparent; border-radius: 9px; text-align: left; padding: 12px 13px; font-size: 10.5pt; }}
QPushButton#nav:hover {{ color: white; background: {colors['sidebar_hover']}; }}
QPushButton#nav:pressed {{ background: {accent}; }}
QPushButton#nav[active="true"] {{ color: {accent_text}; background: {accent}; border-left: 3px solid {colors['soft']}; font-weight: 700; }}
QLabel#pageTitle {{ color: {colors['text']}; font-size: 24pt; font-weight: 750; }}
QLabel#muted {{ color: {colors['muted']}; }}
QLabel#topContext {{ color: {colors['muted']}; font-size: 8pt; font-weight: 700; letter-spacing: 1.1px; }}
QLabel#topDate {{ color: {colors['text']}; font-size: 9pt; font-weight: 600; padding: 8px 12px; background: {colors['panel_alt']}; border: 1px solid {colors['border']}; border-radius: 8px; }}
QLabel#dashboardConnection[state="online"] {{ color: {accent_hover}; background: {colors['soft']}; border-radius: 8px; padding: 8px 12px; }}
QLabel#dashboardConnection[state="offline"] {{ color: #A7661B; background: #FFF0D5; border-radius: 8px; padding: 8px 12px; }}
QFrame#connectionBanner {{ background: #FFF4DF; border: 1px solid #F0D8A8; border-radius: 12px; }}
QLabel#bannerText {{ color: #75430C; padding: 9px 10px; }}
QPushButton#retryDatabase {{ background: #F6E4BD; color: #694000; margin: 5px; }}
QFrame#updateBanner {{ background: {colors['soft']}; border: 1px solid {colors['border']}; border-radius: 12px; }}
QLabel#updateText {{ color: {colors['text']}; padding: 9px 10px; font-weight: 600; }}
QPushButton#updateNow, QPushButton#primary {{ background: {accent}; color: {accent_text}; }}
QPushButton#updateNow {{ margin: 5px; }}
QPushButton#updateNow:hover, QPushButton#primary:hover {{ background: {accent_hover}; }}
QPushButton#updateNotes {{ background: {colors['soft']}; color: {colors['text']}; margin: 5px; }}
QPushButton#dismissUpdate {{ background: transparent; color: {colors['muted']}; padding: 7px; }}
QMessageBox {{ background: {colors['panel']}; }}
QMessageBox QLabel {{ color: {colors['text']}; min-width: 360px; }}
QMessageBox QPushButton {{ min-width: 76px; }}
QFrame#metricPanel, QWidget#panel {{ background: rgba({QColor(colors['panel']).red()}, {QColor(colors['panel']).green()}, {QColor(colors['panel']).blue()}, 238); border: 1px solid rgba({QColor(colors['border']).red()}, {QColor(colors['border']).green()}, {QColor(colors['border']).blue()}, 220); border-top: 1px solid rgba(255,255,255,179); border-radius: 16px; }}
QFrame#metricPanel {{ background: rgba({QColor(colors['panel']).red()}, {QColor(colors['panel']).green()}, {QColor(colors['panel']).blue()}, 245); }}
QFrame#metricDivider {{ background: {colors['border']}; max-width: 1px; }}
QLabel#metricValue, QLabel#insightValue {{ color: {accent}; font-size: 24pt; font-weight: 750; }}
QLabel#metricLabel {{ color: {colors['text']}; font-size: 9pt; font-weight: 650; }}
QLabel#metricHint, QLabel#insightNote {{ color: {colors['subtle']}; font-size: 8pt; }}
QLabel#sectionTitle {{ color: {colors['text']}; font-size: 12pt; font-weight: 700; }}
QLabel#eyebrow {{ color: {accent}; font-size: 8pt; font-weight: 700; letter-spacing: 1.2px; }}
QLabel#heroTitle {{ color: {accent_hover}; font-size: 20pt; font-weight: 700; }}
QLabel#heroCaption, QLabel#insightLabel {{ color: {colors['muted']}; font-size: 9pt; }}
QFrame#dashboardHero {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba({QColor(colors['panel']).red()}, {QColor(colors['panel']).green()}, {QColor(colors['panel']).blue()}, 246), stop:0.72 {colors['soft']}, stop:1 rgba({QColor(accent).red()}, {QColor(accent).green()}, {QColor(accent).blue()}, 46)); border: 1px solid rgba({QColor(colors['border']).red()}, {QColor(colors['border']).green()}, {QColor(colors['border']).blue()}, 225); border-top: 1px solid rgba(255,255,255,209); border-radius: 22px; }}
QFrame#heroClock {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba({QColor(colors['panel']).red()}, {QColor(colors['panel']).green()}, {QColor(colors['panel']).blue()}, 225), stop:0.58 rgba({QColor(colors['panel_alt']).red()}, {QColor(colors['panel_alt']).green()}, {QColor(colors['panel_alt']).blue()}, 196), stop:1 rgba({QColor(accent).red()}, {QColor(accent).green()}, {QColor(accent).blue()}, 28)); border: 1px solid rgba({QColor(colors['border']).red()}, {QColor(colors['border']).green()}, {QColor(colors['border']).blue()}, 194); border-top: 1px solid rgba(255,255,255,180); border-radius: 20px; }}
QLabel#clockValue {{ color: {colors['text']}; font-size: 34pt; font-weight: 600; letter-spacing: 1px; }}
QLabel#clockSeconds {{ color: {accent}; font-size: 13pt; font-weight: 700; padding-bottom: 5px; }}
QLabel#clockCaption {{ color: {colors['muted']}; font-size: 8pt; font-weight: 650; letter-spacing: 0.9px; }}
QFrame#panelHeader {{ background: transparent; }}
QProgressBar {{ background: {colors['header']}; border: 0; border-radius: 5px; height: 9px; text-align: center; }}
QProgressBar::chunk {{ background: {accent}; border-radius: 5px; }}
QLabel#accentPreview {{ background: {accent}; color: {accent_text}; border-radius: 9px; padding: 10px 15px; font-weight: 650; }}
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox {{ background: {colors['field']}; color: {colors['text']}; border: 1px solid {colors['border']}; border-radius: 8px; padding: 9px 10px; min-height: 21px; selection-background-color: {accent}; selection-color: white; }}
QDateEdit#glassDateEdit::up-button, QDateEdit#glassDateEdit::down-button {{ width: 0px; height: 0px; border: 0; padding: 0; }}
QDateEdit#glassDateEdit::up-arrow, QDateEdit#glassDateEdit::down-arrow {{ image: none; width: 0px; height: 0px; }}
QTimeEdit#scheduleTime::up-button, QTimeEdit#scheduleTime::down-button, QSpinBox#scheduleTolerance::up-button, QSpinBox#scheduleTolerance::down-button {{ width: 0px; height: 0px; border: 0; padding: 0; }}
QTimeEdit#scheduleTime::up-arrow, QTimeEdit#scheduleTime::down-arrow, QSpinBox#scheduleTolerance::up-arrow, QSpinBox#scheduleTolerance::down-arrow {{ image: none; width: 0px; height: 0px; }}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus {{ border: 1px solid {colors['focus']}; }}
QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled, QTimeEdit:disabled, QSpinBox:disabled {{ color: {colors['subtle']}; background: {colors['panel_alt']}; }}
QComboBox QAbstractItemView, QListView, QListWidget {{ background: {colors['panel']}; color: {colors['text']}; border: 1px solid {colors['border']}; selection-background-color: {accent}; selection-color: {accent_text}; outline: none; padding: 5px; }}
QAbstractItemView::item, QListWidget::item {{ background: {colors['panel']}; color: {colors['text']}; min-height: 30px; padding: 7px 9px; border-radius: 5px; }}
QAbstractItemView::item:hover, QListWidget::item:hover {{ background: {colors['soft_hover']}; color: {colors['text']}; }}
QAbstractItemView::item:selected, QListWidget::item:selected {{ background: {accent}; color: {accent_text}; }}
QPushButton {{ background: {colors['header']}; border: 1px solid transparent; border-radius: 8px; padding: 10px 15px; color: {colors['text']}; font-weight: 650; }}
QPushButton:hover {{ background: {colors['soft_hover']}; border-color: {colors['border']}; }}
QPushButton:pressed {{ background: {colors['soft']}; }}
QPushButton:focus {{ border: 1px solid {colors['focus']}; }}
QPushButton:disabled {{ color: {colors['subtle']}; background: {colors['header']}; border-color: transparent; }}
QPushButton#danger {{ background: {colors['danger_bg']}; color: {colors['danger_text']}; }}
QPushButton#danger:hover {{ border: 1px solid {colors['danger_text']}; }}
QPushButton#secondary {{ background: {colors['soft']}; color: {accent}; border-color: {colors['border']}; }}
QPushButton#secondary:hover {{ background: {colors['soft_hover']}; border-color: {accent}; }}
QTableWidget {{ background: {colors['panel']}; color: {colors['text']}; border: 1px solid {colors['border']}; border-radius: 10px; gridline-color: {colors['line']}; selection-background-color: {colors['soft']}; selection-color: {colors['text']}; alternate-background-color: {colors['panel_alt']}; outline: none; }}
QHeaderView::section {{ background: {colors['header']}; border: 0; border-bottom: 1px solid {colors['border']}; padding: 11px 9px; color: {colors['muted']}; font-size: 8pt; font-weight: 700; }}
QTableWidget::item {{ padding: 9px 7px; border-bottom: 1px solid {colors['line']}; }}
QScrollArea {{ background: transparent; border: 0; }}
QScrollArea QWidget#qt_scrollarea_viewport {{ background: {colors['background']}; border: 0; }}
QWidget#settingsContent {{ background: {colors['background']}; }}
QScrollBar:vertical {{ background: transparent; width: 9px; margin: 4px 1px; }}
QScrollBar::handle:vertical {{ background: {colors['border']}; border-radius: 4px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {accent}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QCheckBox {{ color: {colors['text']}; spacing: 8px; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid {colors['border']}; border-radius: 5px; background: {colors['field']}; }}
QCheckBox::indicator:checked {{ background: {accent}; border-color: {accent}; }}
QToolTip {{ background: {colors['panel']}; color: {colors['text']}; border: 1px solid {colors['border']}; padding: 5px 8px; }}
QCalendarWidget QWidget {{ background: {colors['panel']}; color: {colors['text']}; alternate-background-color: {colors['panel_alt']}; }}
QCalendarWidget QToolButton {{ background: {colors['header']}; color: {colors['text']}; border-radius: 5px; padding: 5px; }}
QCalendarWidget QAbstractItemView:enabled {{ color: {colors['text']}; selection-background-color: {accent}; selection-color: {accent_text}; }}
QToolButton#calendarTrigger {{ background: {colors['soft']}; color: {accent}; border: 1px solid {colors['border']}; border-radius: 8px; padding: 3px; font-size: 12pt; }}
QToolButton#calendarTrigger:hover {{ background: {colors['soft_hover']}; border-color: {accent}; }}
QFrame#calendarSurface {{ background: transparent; border: 0; border-radius: 22px; }}
QLabel#calendarMonth {{ color: {colors['text']}; font-size: 15pt; font-weight: 700; }}
QLabel#calendarEyebrow {{ color: {accent}; font-size: 8pt; font-weight: 700; letter-spacing: 1px; }}
"""


def build_calendar_stylesheet(accent: str = "#007AFF", style: str = "glass", theme_mode: str = "light") -> str:
    """Estilos neutros y legibles para las variantes de cristal y blanco."""
    color = QColor(accent)
    if not color.isValid():
        color = QColor("#007AFF")
    accent = color.name()
    accent_text = _accent_text(color)
    dark = theme_mode == "dark" and style != "classic"
    surface = "#1C1C1E" if dark else "#FBFBFC" if style == "glass" else "#FFFFFF"
    alternate = "#2C2C2E" if dark else "#F0F0F2" if style == "glass" else "#F7F7F8"
    text = "#F5F5F7" if dark else "#1D1D1F"
    muted = "#A1A1A6" if dark else "#6E6E73"
    hover = "#38383A" if dark else "#E9E9EC"
    nav_background = "#2C2C2E" if dark else "#F2F2F7"
    nav_border = "#38383A" if dark else "#D2D2D7"
    return f"""
QDialog#calendarPopover {{ background: transparent; }}
QFrame#calendarSurface {{ background: transparent; border: 0; border-radius: 22px; }}
QLabel#calendarMonth {{ color: {text}; font-size: 15pt; font-weight: 700; }}
QLabel#calendarEyebrow {{ color: {accent}; font-size: 8pt; font-weight: 700; letter-spacing: 1px; }}
QLabel#calendarMonth, QLabel#calendarEyebrow {{ background: transparent; }}
QCalendarWidget#glassCalendar {{ background-color: {surface}; color: {text}; }}
QCalendarWidget#glassCalendar QWidget {{ background-color: {surface}; color: {text}; alternate-background-color: {alternate}; }}
QCalendarWidget#glassCalendar QTableView {{ background-color: {surface}; color: {text}; border: 0; outline: none; selection-background-color: {accent}; selection-color: {accent_text}; gridline-color: transparent; }}
QCalendarWidget#glassCalendar QAbstractItemView:enabled {{ color: {text}; background-color: {surface}; selection-background-color: {accent}; selection-color: {accent_text}; alternate-background-color: {alternate}; }}
QCalendarWidget#glassCalendar QTableView QWidget#qt_scrollarea_viewport {{ background-color: {surface}; }}
QCalendarWidget#glassCalendar QTableView::item {{ padding: 4px; border: 0; border-radius: 0; background-color: {surface}; color: {text}; }}
QCalendarWidget#glassCalendar QTableView::item:hover {{ background-color: {hover}; color: {text}; border-radius: 9px; }}
QCalendarWidget#glassCalendar QTableView::item:selected {{ background-color: {accent}; color: {accent_text}; border-radius: 9px; }}
QCalendarWidget#glassCalendar QHeaderView::section {{ background-color: {surface}; color: {muted}; border: 0; padding: 4px; font-weight: 650; }}
QCalendarWidget#glassCalendar QToolButton {{ background: transparent; color: {text}; border: 0; border-radius: 8px; padding: 5px; }}
QCalendarWidget#glassCalendar QToolButton:hover {{ background: {hover}; color: {accent}; }}
QToolButton#calendarNav {{ min-width: 34px; min-height: 34px; background: {nav_background}; color: {text}; border: 1px solid {nav_border}; border-radius: 12px; font-size: 15pt; }}
QToolButton#calendarNav:hover {{ color: {accent}; border-color: {accent}; }}
QPushButton#calendarToday {{ background: rgba({color.red()}, {color.green()}, {color.blue()}, 26); color: {accent}; border: 1px solid rgba({color.red()}, {color.green()}, {color.blue()}, 56); border-radius: 12px; padding: 8px 15px; font-weight: 650; }}
QPushButton#calendarToday:hover {{ background: rgba({color.red()}, {color.green()}, {color.blue()}, 46); }}
"""
