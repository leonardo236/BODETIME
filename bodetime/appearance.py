"""Paleta y hoja de estilos de BODETIME, con preferencias por usuario."""

from __future__ import annotations

from PySide6.QtGui import QColor


ACCENT_PRESETS = (
    ("Verde jade", "#16877B"),
    ("Verde salvia", "#4D9469"),
    ("Azul corporativo", "#3475A8"),
    ("Lavanda", "#7865A8"),
    ("Terracota", "#B96950"),
)


def _mix(first: str, second: str, amount: float) -> str:
    """Mezcla dos colores; amount indica cuánto se conserva del primero."""
    a, b = QColor(first), QColor(second)
    return QColor(
        round(a.red() * amount + b.red() * (1 - amount)),
        round(a.green() * amount + b.green() * (1 - amount)),
        round(a.blue() * amount + b.blue() * (1 - amount)),
    ).name()


def build_stylesheet(mode: str = "light", accent: str = "#16877B") -> str:
    """Genera estilos accesibles para modo claro u oscuro y un acento elegido."""
    dark = mode == "dark"
    chosen = QColor(accent)
    if not chosen.isValid():
        chosen = QColor("#16877B")
    accent = chosen.name()
    accent_hover = chosen.lighter(118).name() if dark else chosen.darker(112).name()
    accent_text = "#FFFFFF" if chosen.lightness() < 165 else "#15251F"
    sidebar_top = "#112633" if dark else "#173440"
    sidebar_bottom = "#173640" if dark else "#214A4A"

    colors = {
        "background": "#121C22" if dark else "#F2F5F3",
        "panel": "#202F36" if dark else "#FFFFFF",
        "panel_alt": "#253840" if dark else "#F8FBF9",
        "field": "#17252C" if dark else "#FFFFFF",
        "text": "#E8EFEB" if dark else "#24352E",
        "muted": "#A5B5AD" if dark else "#6D7E74",
        "subtle": "#82968C" if dark else "#829188",
        "border": "#3A4D54" if dark else "#DFE8E3",
        "line": "#2B3B42" if dark else "#EBF0EC",
        "header": "#24343B" if dark else "#F0F4F1",
        "soft": _mix(accent, "#14262A", 0.28) if dark else _mix(accent, "#FFFFFF", 0.86),
        "soft_hover": _mix(accent, "#14262A", 0.40) if dark else _mix(accent, "#FFFFFF", 0.77),
        "sidebar_text": "#E2ECE8",
        "sidebar_muted": "#A3B8B1",
        "sidebar_hover": "#28464A" if dark else "#2A5150",
        "danger_bg": "#482C2C" if dark else "#FBEAE7",
        "danger_text": "#F3A59C" if dark else "#A63831",
        "focus": chosen.lighter(140).name() if dark else chosen.name(),
        "clock_border": "#50636A" if dark else "#E3ECE7",
    }
    return f"""
QWidget {{ font-family: 'Segoe UI'; font-size: 10pt; color: {colors['text']}; }}
QMainWindow {{ background: {colors['background']}; }}
QWidget#content {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {colors['background']}, stop:1 {colors['panel_alt']}); }}
QDialog {{ background: {colors['background']}; }}
QWidget#sidebar {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {sidebar_top}, stop:1 {sidebar_bottom}); }}
QFrame#brandMark {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {accent}, stop:0.55 {accent_hover}, stop:1 {colors['soft']}); border: 1px solid rgba(255,255,255,0.52); border-radius: 15px; }}
QLabel#brandGlyph {{ color: white; font-size: 23pt; font-weight: 800; }}
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
QFrame#metricPanel, QWidget#panel {{ background: rgba({QColor(colors['panel']).red()}, {QColor(colors['panel']).green()}, {QColor(colors['panel']).blue()}, 238); border: 1px solid rgba({QColor(colors['border']).red()}, {QColor(colors['border']).green()}, {QColor(colors['border']).blue()}, 220); border-top: 1px solid rgba(255,255,255,0.7); border-radius: 16px; }}
QFrame#metricPanel {{ background: rgba({QColor(colors['panel']).red()}, {QColor(colors['panel']).green()}, {QColor(colors['panel']).blue()}, 245); }}
QFrame#metricDivider {{ background: {colors['border']}; max-width: 1px; }}
QLabel#metricValue, QLabel#insightValue {{ color: {accent}; font-size: 24pt; font-weight: 750; }}
QLabel#metricLabel {{ color: {colors['text']}; font-size: 9pt; font-weight: 650; }}
QLabel#metricHint, QLabel#insightNote {{ color: {colors['subtle']}; font-size: 8pt; }}
QLabel#sectionTitle {{ color: {colors['text']}; font-size: 12pt; font-weight: 700; }}
QLabel#eyebrow {{ color: {accent}; font-size: 8pt; font-weight: 700; letter-spacing: 1.2px; }}
QLabel#heroTitle {{ color: {accent_hover}; font-size: 20pt; font-weight: 700; }}
QLabel#heroCaption, QLabel#insightLabel {{ color: {colors['muted']}; font-size: 9pt; }}
QFrame#dashboardHero {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba({QColor(colors['panel']).red()}, {QColor(colors['panel']).green()}, {QColor(colors['panel']).blue()}, 242), stop:0.72 {colors['soft']}, stop:1 rgba({QColor(accent).red()}, {QColor(accent).green()}, {QColor(accent).blue()}, 92)); border: 1px solid rgba({QColor(colors['border']).red()}, {QColor(colors['border']).green()}, {QColor(colors['border']).blue()}, 225); border-top: 1px solid rgba(255,255,255,0.82); border-radius: 22px; }}
QFrame#heroClock {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 rgba(255,255,255,184), stop:0.58 rgba({QColor(colors['panel']).red()}, {QColor(colors['panel']).green()}, {QColor(colors['panel']).blue()}, 158), stop:1 rgba({QColor(accent).red()}, {QColor(accent).green()}, {QColor(accent).blue()}, 31)); border: 1px solid rgba(255,255,255,194); border-top: 1px solid rgba(255,255,255,240); border-radius: 20px; }}
QLabel#clockValue {{ color: {colors['text']}; font-size: 34pt; font-weight: 600; letter-spacing: 1px; }}
QLabel#clockSeconds {{ color: {accent}; font-size: 13pt; font-weight: 700; padding-bottom: 5px; }}
QLabel#clockCaption {{ color: {colors['muted']}; font-size: 8pt; font-weight: 650; letter-spacing: 0.9px; }}
QFrame#panelHeader {{ background: transparent; }}
QProgressBar {{ background: {colors['header']}; border: 0; border-radius: 5px; height: 9px; text-align: center; }}
QProgressBar::chunk {{ background: {accent}; border-radius: 5px; }}
QLabel#accentPreview {{ background: {accent}; color: {accent_text}; border-radius: 9px; padding: 10px 15px; font-weight: 650; }}
QLineEdit, QComboBox, QDateEdit, QTimeEdit, QSpinBox {{ background: {colors['field']}; color: {colors['text']}; border: 1px solid {colors['border']}; border-radius: 8px; padding: 9px 10px; min-height: 21px; selection-background-color: {accent}; selection-color: white; }}
QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QTimeEdit:focus, QSpinBox:focus {{ border: 1px solid {colors['focus']}; }}
QLineEdit:disabled, QComboBox:disabled, QDateEdit:disabled, QTimeEdit:disabled, QSpinBox:disabled {{ color: {colors['subtle']}; background: {colors['panel_alt']}; }}
QComboBox::drop-down {{ border: 0; width: 28px; }}
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
QTableWidget {{ background: {colors['panel']}; color: {colors['text']}; border: 1px solid {colors['border']}; border-radius: 10px; gridline-color: {colors['line']}; selection-background-color: {colors['soft']}; selection-color: {colors['text']}; alternate-background-color: {colors['panel_alt']}; outline: none; }}
QHeaderView::section {{ background: {colors['header']}; border: 0; border-bottom: 1px solid {colors['border']}; padding: 11px 9px; color: {colors['muted']}; font-size: 8pt; font-weight: 700; }}
QTableWidget::item {{ padding: 9px 7px; border-bottom: 1px solid {colors['line']}; }}
QScrollArea {{ background: transparent; border: 0; }}
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
QLabel#calendarMonth {{ color: #24333A; font-size: 15pt; font-weight: 700; }}
QLabel#calendarEyebrow {{ color: {accent}; font-size: 8pt; font-weight: 700; letter-spacing: 1px; }}
"""


def build_calendar_stylesheet(accent: str = "#16877B", style: str = "glass") -> str:
    """Hoja clara del calendario flotante, con vidrio suave o blanco clásico."""
    color = QColor(accent)
    if not color.isValid():
        color = QColor("#16877B")
    accent = color.name()
    # El calendario sigue siendo opaco para proteger el contraste; la tarjeta exterior
    # aporta el brillo de cristal y el modo clásico queda blanco puro.
    surface = "#FBFCFB" if style == "glass" else "#FFFFFF"
    alternate = "#F4F7F5" if style == "glass" else "#F7F8F7"
    return f"""
QDialog#calendarPopover {{ background: transparent; }}
QFrame#calendarSurface {{ background: transparent; border: 0; border-radius: 22px; }}
QLabel#calendarMonth {{ color: #26343A; font-family: 'Segoe UI'; font-size: 15pt; font-weight: 700; }}
QLabel#calendarEyebrow {{ color: {accent}; font-family: 'Segoe UI'; font-size: 8pt; font-weight: 700; letter-spacing: 1px; }}
QCalendarWidget#glassCalendar {{ background-color: {surface}; color: #26343A; }}
QCalendarWidget#glassCalendar QWidget {{ background-color: {surface}; color: #26343A; alternate-background-color: {alternate}; }}
QCalendarWidget#glassCalendar QTableView {{ background-color: {surface}; border: 0; outline: none; selection-background-color: {accent}; selection-color: white; gridline-color: transparent; }}
QCalendarWidget#glassCalendar QAbstractItemView:enabled {{ color: #26343A; background-color: {surface}; selection-background-color: {accent}; selection-color: white; alternate-background-color: {alternate}; }}
QCalendarWidget#glassCalendar QTableView QWidget#qt_scrollarea_viewport {{ background-color: {surface}; }}
QCalendarWidget#glassCalendar QTableView::item {{ padding: 5px; border: 0; border-radius: 0; background-color: {surface}; color: #26343A; }}
QCalendarWidget#glassCalendar QTableView::item:hover {{ background-color: #EDF3F0; color: #26343A; border-radius: 9px; }}
QCalendarWidget#glassCalendar QTableView::item:selected {{ background-color: {accent}; color: white; border-radius: 9px; }}
QCalendarWidget#glassCalendar QHeaderView::section {{ background-color: #FBFCFB; color: #75837D; border: 0; padding: 6px; font-weight: 650; }}
QCalendarWidget#glassCalendar QToolButton {{ background: transparent; color: #34464B; border: 0; border-radius: 8px; padding: 5px; }}
QCalendarWidget#glassCalendar QToolButton:hover {{ background: #EDF3F0; color: {accent}; }}
QToolButton#calendarNav {{ min-width: 34px; min-height: 34px; background: #F2F5F4; color: #34464B; border: 1px solid #E3E9E6; border-radius: 12px; font-size: 15pt; }}
QToolButton#calendarNav:hover {{ color: {accent}; border-color: {accent}; }}
QPushButton#calendarToday {{ background: rgba({color.red()}, {color.green()}, {color.blue()}, 26); color: {accent}; border: 1px solid rgba({color.red()}, {color.green()}, {color.blue()}, 56); border-radius: 12px; padding: 8px 15px; font-weight: 650; }}
QPushButton#calendarToday:hover {{ background: rgba({color.red()}, {color.green()}, {color.blue()}, 46); }}
"""
