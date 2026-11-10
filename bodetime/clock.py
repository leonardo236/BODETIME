"""Reloj analógico compacto para acompañar el reloj digital del panel."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QSize, Qt, QTime
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QWidget


class ClockFace(QWidget):
    """Dibuja una esfera ligera que usa la hora local del sistema."""

    def __init__(self, accent: str = "#007AFF", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.accent = QColor(accent)
        self.time = QTime.currentTime()
        self.setFixedSize(54, 54)
        self.setAccessibleName("Reloj analógico local")
        self.setToolTip("Hora local")

    def sizeHint(self) -> QSize:
        return QSize(54, 54)

    def set_time(self, value: QTime) -> None:
        self.time = value
        self.update()

    def set_accent(self, value: str) -> None:
        color = QColor(value)
        if color.isValid():
            self.accent = color
            self.update()

    def paintEvent(self, _event) -> None:
        side = min(self.width(), self.height())
        radius = side / 2 - 2
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.translate(self.width() / 2, self.height() / 2)

        face = QColor(255, 255, 255, 116)
        painter.setPen(QPen(QColor(255, 255, 255, 205), 1.2))
        painter.setBrush(face)
        painter.drawEllipse(QPointF(0, 0), radius, radius)

        for tick in range(60):
            major = tick % 5 == 0
            painter.save()
            painter.rotate(tick * 6)
            color = QColor(self.accent)
            color.setAlpha(175 if major else 62)
            painter.setPen(QPen(color, 1.7 if major else 0.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(0, -radius + 5), QPointF(0, -radius + (10 if major else 7)))
            painter.restore()

        hour_angle = ((self.time.hour() % 12) + self.time.minute() / 60) * 30
        minute_angle = (self.time.minute() + self.time.second() / 60) * 6
        second_angle = self.time.second() * 6
        self._draw_hand(painter, hour_angle, radius * 0.43, QColor("#263B53"), 3.2)
        self._draw_hand(painter, minute_angle, radius * 0.65, QColor("#38516D"), 2.2)
        self._draw_hand(painter, second_angle, radius * 0.72, self.accent, 1.1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self.accent)
        painter.drawEllipse(QPointF(0, 0), 2.5, 2.5)

    @staticmethod
    def _draw_hand(painter: QPainter, angle: float, length: float, color: QColor, width: float) -> None:
        painter.save()
        painter.rotate(angle)
        painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawLine(QPointF(0, 4), QPointF(0, -length))
        painter.restore()
