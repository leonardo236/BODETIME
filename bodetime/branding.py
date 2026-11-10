"""Marca vectorial BODETIME: un monograma B que recorre un dial de tiempo."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget


def draw_bodetime_mark(painter: QPainter, rect: QRectF, accent: str) -> None:
    """Dibuja un símbolo propio de BODETIME sin depender de imágenes externas."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.translate(rect.topLeft())
    painter.scale(rect.width(), rect.height())

    color = QColor(accent)
    if not color.isValid():
        color = QColor("#007AFF")

    tile = QPainterPath()
    tile.addRoundedRect(QRectF(0.02, 0.02, 0.96, 0.96), 0.29, 0.29)
    gradient = QLinearGradient(QPointF(0.08, 0.03), QPointF(0.92, 0.98))
    gradient.setColorAt(0.0, QColor("#17191F"))
    gradient.setColorAt(0.58, QColor("#20232B"))
    gradient.setColorAt(1.0, color.darker(205))
    painter.fillPath(tile, gradient)
    painter.setPen(QPen(QColor(255, 255, 255, 66), 0.018))
    painter.drawPath(tile)

    # La órbita incompleta sugiere un ciclo de jornada en movimiento.
    dial = QRectF(0.13, 0.13, 0.74, 0.74)
    orbit = QPainterPath()
    orbit.arcMoveTo(dial, 43)
    orbit.arcTo(dial, 43, 292)
    painter.setPen(QPen(color.lighter(132), 0.036, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawPath(orbit)

    # Trazo único inspirado en una B y en la curva de un reloj analógico.
    monogram = QPainterPath()
    monogram.moveTo(0.34, 0.25)
    monogram.lineTo(0.34, 0.75)
    monogram.cubicTo(0.76, 0.78, 0.78, 0.55, 0.42, 0.50)
    monogram.cubicTo(0.78, 0.45, 0.76, 0.22, 0.34, 0.25)
    painter.setPen(QPen(QColor("#F6F7FA"), 0.057, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawPath(monogram)

    # El punto de contraste funciona como centro del dial y detalle de marca.
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(color.lighter(125))
    painter.drawEllipse(QPointF(0.42, 0.50), 0.036, 0.036)
    painter.setBrush(QColor("#F6F7FA"))
    painter.drawEllipse(QPointF(0.77, 0.23), 0.032, 0.032)
    painter.restore()


class BrandMark(QWidget):
    """Isotipo vectorial adaptable a la barra lateral y a la pantalla de inicio."""

    def __init__(self, size: int, accent: str = "#007AFF", object_name: str = "brandMark", parent=None) -> None:
        super().__init__(parent)
        self.accent = accent
        self.setObjectName(object_name)
        self.setFixedSize(size, size)
        self.setAccessibleName("Marca BODETIME, monograma y dial de tiempo")
        self.setToolTip("BODETIME")

    def sizeHint(self) -> QSize:
        return self.size()

    def set_accent(self, accent: str) -> None:
        color = QColor(accent)
        if color.isValid():
            self.accent = color.name()
            self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        draw_bodetime_mark(painter, QRectF(self.rect()), self.accent)


def application_icon(accent: str = "#007AFF") -> QIcon:
    """Crea el icono de la ventana a partir de la misma marca vectorial."""
    pixmap = QPixmap(128, 128)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    draw_bodetime_mark(painter, QRectF(0, 0, 128, 128), accent)
    painter.end()
    return QIcon(pixmap)
