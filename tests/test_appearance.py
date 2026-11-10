import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate, QEventLoop, QSettings, QTime, QTimer, Qt
from PySide6.QtWidgets import QAbstractSpinBox, QApplication, QLabel, QTableView

from bodetime.animations import SmoothTween
from bodetime.appearance import build_calendar_stylesheet, build_stylesheet
from bodetime.calendar import GlassDateEdit
from bodetime.clock import ClockFace
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
    assert "background: #252E39" in stylesheet
    assert "color: #EEF2F7" in stylesheet
    assert "selection-color: #FFFFFF" in stylesheet


def test_invalid_accent_falls_back_to_safe_default():
    stylesheet = build_stylesheet("light", "not-a-color")
    assert "background: #007aff" in stylesheet


def test_default_appearance_uses_apple_inspired_system_blue_and_light_surface():
    stylesheet = build_stylesheet()
    assert "background: #007aff" in stylesheet
    assert "background: #F3F5F8" in stylesheet
    assert "QStackedWidget { background: #F3F5F8; border: 0; }" in stylesheet


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
    assert popover.surface.calendar_style == "classic"
    assert "background-color: #FFFFFF" in popover.styleSheet()
    picker.close()
    assert app is not None


def test_calendar_style_has_glass_and_classic_light_surfaces():
    assert "QCalendarWidget#glassCalendar" not in build_stylesheet("dark", "#16877B")
    glass = build_calendar_stylesheet("#4D9469", "glass")
    classic = build_calendar_stylesheet("#4D9469", "classic")
    assert "background-color: #FBFCFB" in glass
    assert "background-color: #FFFFFF" in classic
    assert "QFrame#calendarSurface { background: transparent;" in glass
    assert "selection-background-color: #4d9469" in classic


def test_calendar_popup_and_date_grid_use_opaque_backgrounds():
    app = _app()
    picker = GlassDateEdit(QDate(2026, 11, 9), animated=False)
    picker.open_calendar()
    app.processEvents()
    popover = picker._popover
    assert popover is not None
    assert popover.testAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
    assert popover.calendar.testAttribute(Qt.WidgetAttribute.WA_StyledBackground)
    calendar_view = popover.calendar.findChild(QTableView)
    assert calendar_view is not None
    assert calendar_view.viewport().testAttribute(Qt.WidgetAttribute.WA_StyledBackground)
    assert calendar_view.viewport().testAttribute(Qt.WidgetAttribute.WA_OpaquePaintEvent)
    assert "#fbfcfb" in calendar_view.viewport().styleSheet()
    picker.set_calendar_style("#3475A8", "classic", False)
    assert "#ffffff" in calendar_view.viewport().styleSheet()
    assert calendar_view.viewport().palette().color(calendar_view.viewport().backgroundRole()).name() == "#ffffff"
    picker.close()
    assert app is not None


def test_glass_calendar_opens_with_smooth_expand_and_fade():
    app = _app()
    picker = GlassDateEdit(QDate(2026, 11, 9), animated=True)
    picker.show()
    picker.open_calendar()
    app.processEvents()
    popover = picker._popover
    assert popover is not None and popover.isVisible()
    assert popover._transition is not None
    assert popover._transition.animationCount() == 2
    mask_start = popover.mask().boundingRect()
    assert mask_start.width() < popover.width()
    loop = QEventLoop()
    QTimer.singleShot(120, loop.quit)
    loop.exec()
    mask_middle = popover.mask().boundingRect()
    assert mask_middle.width() > mask_start.width()
    assert mask_middle.width() < popover.width()
    popover.dismiss()
    app.processEvents()
    picker.close()


def test_analog_clock_tracks_system_time_and_custom_accent():
    clock = ClockFace("#3475A8")
    time = QTime(8, 42, 17)
    clock.set_time(time)
    clock.set_accent("#4D9469")
    assert clock.time == time
    assert clock.accent.name() == "#4d9469"
    assert clock.size().width() == 54


def test_clock_mode_can_switch_without_showing_both_styles(tmp_path):
    app = _app()
    settings = QSettings(str(tmp_path / "clock-preferences.ini"), QSettings.Format.IniFormat)
    window = MainWindow(object(), database_error="MySQL sin conexión", preferences=settings)
    assert window.clock_style == "digital"
    assert window.clock_face.isHidden()
    assert not window.hero_clock.isHidden()
    window.clock_style_selector.setCurrentIndex(window.clock_style_selector.findData("analog"))
    assert window.clock_face.isHidden() is False
    assert window.hero_clock.isHidden()
    assert settings.value("appearance/clock") == "analog"
    window.clock_style_selector.setCurrentIndex(window.clock_style_selector.findData("digital"))
    assert window.clock_face.isHidden()
    assert not window.hero_clock.isHidden()
    window.close()
    app.processEvents()


def test_legacy_default_accent_migrates_and_report_mark_sets_window_icon(tmp_path):
    app = _app()
    settings = QSettings(str(tmp_path / "legacy-preferences.ini"), QSettings.Format.IniFormat)
    settings.setValue("appearance/accent", "#16877B")
    window = MainWindow(object(), database_error="MySQL sin conexión", preferences=settings)
    assert window.accent_color.lower() == "#007aff"
    assert settings.value("appearance/accent") == "#007AFF"
    assert not window.windowIcon().isNull()
    assert window.brand_mark.accessibleName() == "Logotipo BODETIME, hoja de reporte"
    window.close()
    app.processEvents()


def test_schedule_fields_use_clean_flat_inputs_without_legacy_spinner_borders(tmp_path):
    app = _app()
    settings = QSettings(str(tmp_path / "flat-inputs.ini"), QSettings.Format.IniFormat)
    window = MainWindow(object(), database_error="MySQL sin conexión", preferences=settings)
    assert window.schedule_time.buttonSymbols() == QAbstractSpinBox.ButtonSymbols.NoButtons
    assert window.schedule_tolerance.buttonSymbols() == QAbstractSpinBox.ButtonSymbols.NoButtons
    window.close()
    app.processEvents()


def test_update_button_flow_starts_download_after_manual_search(tmp_path):
    app = _app()
    settings = QSettings(str(tmp_path / "preferences.ini"), QSettings.Format.IniFormat)
    window = MainWindow(object(), database_error="MySQL sin conexión", preferences=settings)
    release = ReleaseInfo(
        version="1.1.1",
        tag="v1.1.1",
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
    assert window.generate_excel_button.text() == "Generar Excel"
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


def test_splash_entry_uses_a_soft_scale_and_fade():
    app = _app()
    splash = SplashScreen(animated=True)
    splash.animate_in()
    app.processEvents()
    assert splash.isVisible()
    assert splash._transition is not None
    assert splash._transition.animationCount() == 2
    assert splash.width() < 520
    splash.fade_out()
    loop = QEventLoop()
    QTimer.singleShot(350, loop.quit)
    loop.exec()
    assert not splash.isVisible()
