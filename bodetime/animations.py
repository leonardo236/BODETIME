"""Animaciones ligeras basadas en el motor de animación de Qt."""

from __future__ import annotations

from typing import Callable

from PySide6.QtCore import QEasingCurve, QVariantAnimation


class SmoothTween(QVariantAnimation):
    """Anima un valor usando Qt para acompasarlo con el repintado disponible."""

    def __init__(
        self,
        setter: Callable[[float], None],
        start: float,
        end: float,
        duration_ms: int,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setStartValue(float(start))
        self.setEndValue(float(end))
        self.setDuration(max(1, duration_ms))
        self.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.valueChanged.connect(lambda value: setter(float(value)))

    def cancel(self) -> None:
        """Detiene la animación si la persona desactiva los efectos."""
        self.stop()
        self.deleteLater()
