from bodetime.animations import frame_interval_ms
from bodetime.appearance import build_stylesheet


def test_animation_interval_tracks_common_display_refresh_rates():
    assert frame_interval_ms(60) == 17
    assert frame_interval_ms(120) == 8
    assert frame_interval_ms(165) == 8
    assert frame_interval_ms(None) == 8


def test_precise_tween_reaches_its_final_value():
    from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer

    from bodetime.animations import SmoothTween

    app = QCoreApplication.instance() or QCoreApplication([])
    values = []
    loop = QEventLoop()
    tween = SmoothTween(values.append, 0, 1, 35, 8)
    tween.finished.connect(loop.quit)
    tween.start()
    QTimer.singleShot(500, loop.quit)
    loop.exec()
    assert values[0] == 0
    assert values[-1] == 1
    assert app is not None


def test_light_theme_styles_combo_popup_and_selected_items():
    stylesheet = build_stylesheet("light", "#16877B")
    assert "QComboBox QAbstractItemView" in stylesheet
    assert "selection-background-color: #16877b" in stylesheet
    assert "background: #FFFFFF" in stylesheet


def test_dark_theme_uses_contrasting_popup_and_readable_text():
    stylesheet = build_stylesheet("dark", "#3475A8")
    assert "QComboBox QAbstractItemView" in stylesheet
    assert "background: #1D2A31" in stylesheet
    assert "color: #E8EFEB" in stylesheet
    assert "selection-color: #FFFFFF" in stylesheet


def test_invalid_accent_falls_back_to_safe_default():
    stylesheet = build_stylesheet("light", "not-a-color")
    assert "background: #16877b" in stylesheet
