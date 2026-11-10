import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate, QEventLoop, QSettings, QTimer
from PySide6.QtWidgets import QApplication, QLabel

from bodetime.animations import SmoothTween
from bodetime.appearance import build_calendar_stylesheet, build_stylesheet
from bodetime.calendar import GlassDateEdit
from bodetime.splash import SplashScreen
from bodetime.ui import MainWindow
from bodetime.updater import ReleaseInfo


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_tween_reaches_final_value_using_qt_animation_engine():
    app = _app()
    values = []
    loop = QEventLoop()
    tween = SmoothTween(values.append, 0, 1, 35)
    tween.finished.connect(loop.quit)
    tween.start()
    QTimer.singleShot(500, loop.quit)
    loop.exec()
    assert values
    assert all(0 <= value <= 1 for value in values)
    assert values[-1] == 1
    tween.deleteLater()
    assert app is not None


def test_light_theme_styles_combo_popup_and_selected_items():
    stylesheet = build_stylesheet("light", "#16877B")
    assert "QComboBox QAbstractItemView" in stylesheet
    assert "selection-background-color: #16877b" in stylesheet
    assert "background: #FFFFFF" in stylesheet


def test_dark_theme_uses_contrasting_popup_and_readable_text():
    stylesheet = build_stylesheet("dark", "#3475A8")
    assert "QComboBox QAbstractItemView" in stylesheet
    assert "background: #253840" in stylesheet
    assert "color: #E8EFEB" in stylesheet
    assert "selection-color: #FFFFFF" in stylesheet


def test_invalid_accent_falls_back_to_safe_default():
    stylesheet = build_stylesheet("light", "not-a-color")
    assert "background: #16877b" in stylesheet


def test_calendar_date_field_keeps_qdateedit_api_and_selects_a_date():
    app = _app()
    picker = GlassDateEdit(QDate(2026, 11, 9), animated=False)
    picker.resize(190, 42)
    picker.show()
    picker.open_calendar()
    app.processEvents()
    popover = picker._popover
    assert popover is not None and popover.isVisible()
    assert popover.month_label.text() == "Noviembre 2026"
    selected = QDate(2026, 12, 24)
    popover._select_date(selected)
    app.processEvents()
    assert picker.date() == selected
    picker.set_calendar_style("#3475A8", "classic", False)
    assert "background: #FFFFFF" in popover.styleSheet()
    picker.close()
    assert app is not None


def test_calendar_style_has_glass_and_classic_light_surfaces():
    glass = build_calendar_stylesheet("#4D9469", "glass")
    classic = build_calendar_stylesheet("#4D9469", "classic")
    assert "background: #F7FAF9" in glass
    assert "background: #FFFFFF" in classic
    assert "selection-background-color: #4d9469" in classic


def test_update_button_flow_starts_download_after_manual_search(tmp_path):
    app = _app()
    settings = QSettings(str(tmp_path / "preferences.ini"), QSettings.Format.IniFormat)
    window = MainWindow(object(), database_error="MySQL sin conexión", preferences=settings)
    release = ReleaseInfo(
        version="1.0.8",
        tag="v1.0.8",
        notes_url="https://example.invalid/release",
        installer_url="https://example.invalid/installer.exe",
        installer_sha256="0" * 64,
        installer_size=1024,
    )
    install_started = []
    window.start_update_download = lambda: install_started.append(True)
    window._install_after_update_check = True
    window._update_check_finished(release, manual=True)
    loop = QEventLoop()
    QTimer.singleShot(400, loop.quit)
    loop.exec()
    assert window.latest_release == release
    assert not window.update_banner.isHidden()
    assert install_started == [True]
    window.close()
    app.processEvents()


def test_splash_displays_bodetime_brand_and_can_close_without_animation():
    app = _app()
    splash = SplashScreen(animated=False)
    assert splash.findChild(QLabel, "splashTitle").text() == "BODETIME"
    splash.animate_in()
    assert splash.isVisible()
    splash.fade_out()
    assert not splash.isVisible()
    assert app is not None
