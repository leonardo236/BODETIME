import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QDate, QEventLoop, QSettings, QTime, QTimer, Qt
from PySide6.QtWidgets import QAbstractSpinBox, QApplication, QLabel, QTableView

from bodetime.animations import SmoothTween
from bodetime.appearance import build_calendar_stylesheet, build_stylesheet
from bodetime.branding import application_icon
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
    assert "background: #2C2C2E" in stylesheet
    assert "color: #F5F5F7" in stylesheet
    assert "selection-color: #FFFFFF" in stylesheet


def test_invalid_accent_falls_back_to_safe_default():
    stylesheet = build_stylesheet("light", "not-a-color")
    assert "background: #007aff" in stylesheet


def test_default_appearance_uses_apple_inspired_system_blue_and_light_surface():
    stylesheet = build_stylesheet()
    assert "background: #007aff" in stylesheet
    assert "background: #F5F5F7" in stylesheet
    assert "QStackedWidget { background: #F5F5F7; border: 0; }" in stylesheet


def test_application_icon_uses_only_black_and_white():
    image = application_icon("#007AFF").pixmap(128, 128).toImage()
    pixels = [
        image.pixelColor(x, y)
        for x in range(image.width())
        for y in range(image.height())
        if image.pixelColor(x, y).alpha() > 0
    ]
    assert pixels
    assert all(color.red() == color.green() == color.blue() for color in pixels)


def test_calendar_date_field_keeps_qdateedit_api_and_selects_a_date():
    app = _app()
    app.setStyle("Fusion")
    app.setStyleSheet(build_stylesheet())
    picker = GlassDateEdit(QDate(2026, 11, 9), animated=False)
    picker.resize(190, 42)
    picker.show()
    app.processEvents()
    assert picker.text() == "09/11/2026"
    assert picker.lineEdit().text() == "09/11/2026"
    assert picker.lineEdit().width() > 100
    picker.open_calendar()
    app.processEvents()
    popover = picker._popover
    assert popover is not None and popover.isVisible()
    assert popover.month_label.text() == "Noviembre 2026"
    assert popover.month_label.autoFillBackground() is False
    assert popover.findChild(QLabel, "calendarEyebrow").autoFillBackground() is False
    anchor = picker.mapToGlobal(picker.rect().topLeft())
    assert abs(popover.x() - anchor.x()) <= 8
    assert popover.height() <= 360
    selected = QDate(2026, 12, 24)
    popover._select_date(selected)
    app.processEvents()
    assert picker.date() == selected
    picker.set_calendar_style("#3475A8", "classic", False)
    assert popover.surface.calendar_style == "classic"
    assert "background-color: #FFFFFF" in popover.styleSheet()
    picker.set_calendar_style("#3475A8", "glass", False, "dark")
    assert "background-color: #1C1C1E" in popover.styleSheet()
    assert popover.surface.theme_mode == "dark"
    picker.close()
    assert app is not None


def test_calendar_style_has_glass_and_classic_light_surfaces():
    assert "QCalendarWidget#glassCalendar" not in build_stylesheet("dark", "#16877B")
    glass = build_calendar_stylesheet("#4D9469", "glass")
    classic = build_calendar_stylesheet("#4D9469", "classic")
    assert "background-color: #FBFBFC" in glass
    assert "background-color: #FFFFFF" in classic
    assert "QFrame#calendarSurface { background: transparent;" in glass
    assert "QLabel#calendarMonth, QLabel#calendarEyebrow { background: transparent; }" in glass
    assert "selection-background-color: #4d9469" in classic
    dark = build_calendar_stylesheet("#3475A8", "glass", "dark")
    assert "background-color: #1C1C1E" in dark
    assert "color: #F5F5F7" in dark


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
    assert "#fbfbfc" in calendar_view.viewport().styleSheet()
    picker.set_calendar_style("#3475A8", "classic", False)
    assert "#ffffff" in calendar_view.viewport().styleSheet()
    assert calendar_view.viewport().palette().color(calendar_view.viewport().backgroundRole()).name() == "#ffffff"
    picker.set_calendar_style("#3475A8", "glass", False, "dark")
    assert "#1c1c1e" in calendar_view.viewport().styleSheet()
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
    assert window.brand_mark.accessibleName() == "Isotipo BODETIME en blanco y negro, con B y dial de tiempo"
    window.close()
    app.processEvents()


def test_schedule_fields_show_values_without_narrow_internal_editors(tmp_path):
    app = _app()
    settings = QSettings(str(tmp_path / "flat-inputs.ini"), QSettings.Format.IniFormat)
    window = MainWindow(object(), database_error="MySQL sin conexión", preferences=settings)
    assert window.schedule_time.buttonSymbols() == QAbstractSpinBox.ButtonSymbols.UpDownArrows
    assert window.schedule_tolerance.buttonSymbols() == QAbstractSpinBox.ButtonSymbols.UpDownArrows
    window.schedule_time.setTime(QTime(6, 0))
    window.schedule_tolerance.setValue(15)
    window.show()
    app.processEvents()
    assert window.schedule_time.text() == "06:00"
    assert window.schedule_time.lineEdit().text() == "06:00"
    assert window.schedule_time.lineEdit().width() >= 100
    assert window.schedule_tolerance.text() == "15 minutos"
    assert window.schedule_tolerance.lineEdit().text() == "15 minutos"
    assert window.schedule_tolerance.lineEdit().width() >= 100
    assert "QTimeEdit#scheduleTime::up-button" in build_stylesheet()
    window.close()
    app.processEvents()


def test_update_button_flow_starts_download_after_manual_search(tmp_path):
    app = _app()
    settings = QSettings(str(tmp_path / "preferences.ini"), QSettings.Format.IniFormat)
    window = MainWindow(object(), database_error="MySQL sin conexión", preferences=settings)
    release = ReleaseInfo(
        version="1.1.3",
        tag="v1.1.3",
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
