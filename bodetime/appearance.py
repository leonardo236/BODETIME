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
        "panel": "#1D2A31" if dark else "#FFFFFF",
        "panel_alt": "#223139" if dark else "#F8FAF8",
        "field": "#17252C" if dark else "#FFFFFF",
        "text": "#E8EFEB" if dark else "#24352E",
        "muted": "#A5B5AD" if dark else "#6D7E74",
        "subtle": "#82968C" if dark else "#829188",
        "border": "#34464D" if dark else "#DCE5DF",
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
        "clock_border": "#405258" if dark else "#DCE6DE",
    }
    return f"""
QWidget {{ font-family: 'Segoe UI'; font-size: 10pt; color: {colors['text']}; }}
QMainWindow, QWidget#content, QDialog {{ background: {colors['background']}; }}
QWidget#sidebar {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {sidebar_top}, stop:1 {sidebar_bottom}); }}
QFrame#brandMark {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {accent}, stop:1 {accent_hover}); border: 1px solid {colors['clock_border']}; border-radius: 14px; }}
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
QFrame#metricPanel, QWidget#panel {{ background: {colors['panel']}; border: 1px solid {colors['border']}; border-radius: 13px; }}
QFrame#metricPanel {{ background: {colors['panel']}; }}
QFrame#metricDivider {{ background: {colors['border']}; max-width: 1px; }}
QLabel#metricValue, QLabel#insightValue {{ color: {accent}; font-size: 24pt; font-weight: 750; }}
QLabel#metricLabel {{ color: {colors['text']}; font-size: 9pt; font-weight: 650; }}
QLabel#metricHint, QLabel#insightNote {{ color: {colors['subtle']}; font-size: 8pt; }}
QLabel#sectionTitle {{ color: {colors['text']}; font-size: 12pt; font-weight: 700; }}
QLabel#eyebrow {{ color: {accent}; font-size: 8pt; font-weight: 700; letter-spacing: 1.2px; }}
QLabel#heroTitle {{ color: {accent_hover}; font-size: 20pt; font-weight: 700; }}
QLabel#heroCaption, QLabel#insightLabel {{ color: {colors['muted']}; font-size: 9pt; }}
QFrame#dashboardHero {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {colors['panel_alt']}, stop:1 {colors['soft']}); border: 1px solid {colors['border']}; border-radius: 14px; }}
QFrame#heroClock {{ background: transparent; border: 1px solid {colors['clock_border']}; border-radius: 12px; }}
QLabel#clockValue {{ color: {accent}; font-size: 25pt; font-weight: 700; }}
QLabel#clockCaption {{ color: {colors['muted']}; font-size: 8pt; font-weight: 650; letter-spacing: 0.7px; }}
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
"""
