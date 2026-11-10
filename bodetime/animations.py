"""Animaciones breves que siguen la frecuencia real de la pantalla."""

from __future__ import annotations

from time import perf_counter
from typing import Callable

from PySide6.QtCore import QEasingCurve, QObject, QTimer, Qt, Signal


def frame_interval_ms(refresh_rate: float | None) -> int:
    """Devuelve el ritmo de repintado, limitado a un máximo de 120 Hz."""
    if refresh_rate is None or refresh_rate <= 1:
        return 8
    return max(1, round(1000 / min(refresh_rate, 120)))


class SmoothTween(QObject):
    """Actualiza una propiedad en el hilo gráfico con temporizador preciso."""

    finished = Signal()

    def __init__(
        self,
        setter: Callable[[float], None],
        start: float,
        end: float,
        duration_ms: int,
        interval_ms: int,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self._setter = setter
        self._start = float(start)
        self._end = float(end)
        self._duration_seconds = max(1, duration_ms) / 1000
        self._started_at = 0.0
        self._curve = QEasingCurve(QEasingCurve.Type.OutCubic)
        self._timer = QTimer(self)
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.setInterval(max(1, interval_ms))
        self._timer.timeout.connect(self._step)

    def start(self) -> None:
        self._started_at = perf_counter()
        self._setter(self._start)
        self._timer.start()

    def cancel(self) -> None:
        self._timer.stop()
        self.deleteLater()

    def _step(self) -> None:
        progress = min(1.0, (perf_counter() - self._started_at) / self._duration_seconds)
        eased = self._curve.valueForProgress(progress)
        self._setter(self._start + (self._end - self._start) * eased)
        if progress >= 1:
            self._timer.stop()
            self.finished.emit()
            self.deleteLater()
