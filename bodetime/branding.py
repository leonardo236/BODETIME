"""Isotipo vectorial de un búho, dibujado en blanco y negro."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget


def draw_bodetime_mark(painter: QPainter, rect: QRectF, accent: str) -> None:
    """Dibuja el búho vigilante de BODETIME con formas simples y alto contraste."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.translate(rect.topLeft())
    painter.scale(rect.width(), rect.height())

    ink = QColor("#111111")

    tile = QPainterPath()
    tile.addRoundedRect(QRectF(0.02, 0.02, 0.96, 0.96), 0.29, 0.29)
    painter.fillPath(tile, QColor("#FFFFFF"))
    painter.setPen(QPen(ink, 0.022))
    painter.drawPath(tile)

    # La silueta con dos puntas forma las plumas de la cabeza del búho.
    owl = QPainterPath()
    owl.moveTo(0.17, 0.73)
    owl.cubicTo(0.16, 0.61, 0.17, 0.51, 0.19, 0.42)
    owl.lineTo(0.16, 0.24)
    owl.quadTo(0.15, 0.16, 0.25, 0.19)
    owl.cubicTo(0.37, 0.20, 0.44, 0.25, 0.50, 0.34)
    owl.cubicTo(0.56, 0.25, 0.63, 0.20, 0.75, 0.19)
    owl.quadTo(0.85, 0.16, 0.84, 0.24)
    owl.lineTo(0.81, 0.42)
    owl.cubicTo(0.83, 0.51, 0.84, 0.61, 0.83, 0.73)
    owl.cubicTo(0.66, 0.90, 0.34, 0.90, 0.17, 0.73)
    owl.closeSubpath()
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(ink)
    painter.drawPath(owl)

    # Los ojos blancos y las pupilas negras hacen la figura reconocible incluso pequeña.
    for center_x in (0.36, 0.64):
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QPointF(center_x, 0.47), 0.13, 0.13)
        painter.setBrush(ink)
        painter.drawEllipse(QPointF(center_x, 0.47), 0.055, 0.055)
        painter.setBrush(QColor("#FFFFFF"))
        painter.drawEllipse(QPointF(center_x - 0.018, 0.45), 0.014, 0.014)

    # Un pico pequeño y dos trazos de pluma completan la marca sin añadir letras.
    beak = QPainterPath()
    beak.moveTo(0.46, 0.59)
    beak.lineTo(0.54, 0.59)
    beak.lineTo(0.50, 0.69)
    beak.closeSubpath()
    painter.setBrush(QColor("#FFFFFF"))
    painter.drawPath(beak)
    painter.setPen(QPen(QColor("#FFFFFF"), 0.025, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    painter.drawLine(QPointF(0.27, 0.68), QPointF(0.42, 0.75))
    painter.drawLine(QPointF(0.58, 0.75), QPointF(0.73, 0.68))
    painter.restore()


class BrandMark(QWidget):
    """Isotipo vectorial adaptable a la barra lateral y a la pantalla de inicio."""

    def __init__(self, size: int, accent: str = "#007AFF", object_name: str = "brandMark", parent=None) -> None:
        super().__init__(parent)
        self.accent = accent
        self.setObjectName(object_name)
        self.setFixedSize(size, size)
        self.setAccessibleName("Isotipo BODETIME en blanco y negro, búho vigilante")
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
