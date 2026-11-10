"""Marca vectorial de BODETIME, dibujada por Qt para cualquier escala."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PySide6.QtWidgets import QWidget


def draw_report_mark(painter: QPainter, rect: QRectF, accent: str) -> None:
    """Pinta una hoja de reporte simple sobre un fondo azul redondeado."""
    painter.save()
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.translate(rect.topLeft())
    painter.scale(rect.width(), rect.height())

    color = QColor(accent)
    if not color.isValid():
        color = QColor("#007AFF")
    background = QPainterPath()
    background.addRoundedRect(QRectF(0.02, 0.02, 0.96, 0.96), 0.28, 0.28)
    gradient = QLinearGradient(QPointF(0, 0), QPointF(1, 1))
    gradient.setColorAt(0, color.lighter(112))
    gradient.setColorAt(1, color.darker(108))
    painter.fillPath(background, gradient)
    painter.setPen(QPen(QColor(255, 255, 255, 150), 0.018))
    painter.drawPath(background)

    page = QPainterPath()
    page.moveTo(0.30, 0.20)
    page.lineTo(0.57, 0.20)
    page.lineTo(0.72, 0.35)
    page.lineTo(0.72, 0.80)
    page.quadTo(0.72, 0.83, 0.69, 0.83)
    page.lineTo(0.31, 0.83)
    page.quadTo(0.28, 0.83, 0.28, 0.80)
    page.lineTo(0.28, 0.23)
    page.quadTo(0.28, 0.20, 0.30, 0.20)
    page.closeSubpath()
    painter.fillPath(page, QColor(255, 255, 255, 248))
    painter.setPen(QPen(QColor(255, 255, 255, 230), 0.018))
    painter.drawPath(page)

    fold = QPainterPath()
    fold.moveTo(0.57, 0.20)
    fold.lineTo(0.57, 0.33)
    fold.quadTo(0.57, 0.35, 0.60, 0.35)
    fold.lineTo(0.72, 0.35)
    painter.setPen(QPen(color.lighter(115), 0.018, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawPath(fold)

    ink = color.darker(110)
    painter.setPen(QPen(ink, 0.024, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
    for y, end_x in ((0.45, 0.63), (0.54, 0.63), (0.63, 0.55)):
        painter.drawLine(QPointF(0.38, y), QPointF(end_x, y))

    painter.setPen(QPen(color, 0.028, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
    painter.drawLine(QPointF(0.38, 0.73), QPointF(0.47, 0.67))
    painter.drawLine(QPointF(0.47, 0.67), QPointF(0.54, 0.71))
    painter.drawLine(QPointF(0.54, 0.71), QPointF(0.64, 0.62))
    painter.restore()


class ReportMark(QWidget):
    """Marca de la app; el tamaño se adapta a la barra lateral o al inicio."""

    def __init__(self, size: int, accent: str = "#007AFF", object_name: str = "brandMark", parent=None) -> None:
        super().__init__(parent)
        self.accent = accent
        self.setObjectName(object_name)
        self.setFixedSize(size, size)
        self.setAccessibleName("Logotipo BODETIME, hoja de reporte")
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
        draw_report_mark(painter, QRectF(self.rect()), self.accent)


def report_icon(accent: str = "#007AFF") -> QIcon:
    """Crea el icono de ventana a partir de la misma marca vectorial."""
    pixmap = QPixmap(128, 128)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    draw_report_mark(painter, QRectF(0, 0, 128, 128), accent)
    painter.end()
    return QIcon(pixmap)
