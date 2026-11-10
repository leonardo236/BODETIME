"""Pantalla breve de inicio para la aplicación de escritorio."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


class SplashScreen(QWidget):
    """Ventana compacta translúcida que acompaña el inicio de BODETIME."""

    def __init__(self, animated: bool = True) -> None:
        super().__init__(None, Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.animated = animated
        self.setObjectName("splashRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(520, 330)
        self.setWindowOpacity(0.0 if animated else 1.0)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 20)
        card = QFrame()
        card.setObjectName("splashCard")
        card.setStyleSheet("""
            QFrame#splashCard { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #122A3C, stop:0.55 #173D49, stop:1 #205B59); border: 1px solid rgba(255,255,255,100); border-top: 1px solid rgba(255,255,255,180); border-radius: 28px; }
            QLabel#splashEyebrow { color: #A8D5C8; font: 700 9pt 'Segoe UI'; letter-spacing: 2px; }
            QLabel#splashTitle { color: white; font: 700 27pt 'Segoe UI'; letter-spacing: 1px; }
            QLabel#splashSubtitle { color: #BCD3D5; font: 10pt 'Segoe UI'; }
            QLabel#splashStatus { color: #D6E6E4; font: 9pt 'Segoe UI'; }
            QFrame#splashMark { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #4BC5B3, stop:1 #7FCE9E); border: 1px solid rgba(255,255,255,180); border-radius: 20px; }
            QLabel#splashGlyph { color: white; font: 800 30pt 'Segoe UI'; }
            QProgressBar { max-height: 5px; background: rgba(235,255,250,42); border: 0; border-radius: 2px; }
            QProgressBar::chunk { background: #8DE1C8; border-radius: 2px; }
        """)
        shadow = QGraphicsDropShadowEffect(card)
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 16)
        shadow.setColor(QColor(0, 10, 18, 115))
        card.setGraphicsEffect(shadow)
        content = QVBoxLayout(card)
        content.setContentsMargins(34, 28, 34, 26)
        content.setSpacing(0)

        brand = QHBoxLayout()
        brand.setSpacing(18)
        mark = QFrame()
        mark.setObjectName("splashMark")
        mark.setFixedSize(70, 70)
        mark_layout = QVBoxLayout(mark)
        mark_layout.setContentsMargins(0, 0, 0, 0)
        glyph = QLabel("B")
        glyph.setObjectName("splashGlyph")
        glyph.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mark_layout.addWidget(glyph)
        wordmark = QVBoxLayout()
        wordmark.setSpacing(1)
        eyebrow = QLabel("GESTIÓN DE ASISTENCIA")
        eyebrow.setObjectName("splashEyebrow")
        title = QLabel("BODETIME")
        title.setObjectName("splashTitle")
        wordmark.addWidget(eyebrow)
        wordmark.addWidget(title)
        brand.addWidget(mark)
        brand.addLayout(wordmark, 1)
        content.addStretch(2)
        content.addLayout(brand)

        subtitle = QLabel("Personas, jornadas y reportes en un solo lugar.")
        subtitle.setObjectName("splashSubtitle")
        content.addWidget(subtitle)
        content.addStretch(2)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)
        content.addWidget(self.progress)
        content.addSpacing(12)
        self.status = QLabel("Preparando tu espacio de trabajo…")
        self.status.setObjectName("splashStatus")
        content.addWidget(self.status)
        outer.addWidget(card)

        screen = self.screen()
        if screen is not None:
            self.move(screen.availableGeometry().center() - self.rect().center())
        self._fade: QPropertyAnimation | None = None

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        gloss = QLinearGradient(10, 10, self.width() - 10, self.height() - 10)
        gloss.setColorAt(0.0, QColor(255, 255, 255, 24))
        gloss.setColorAt(0.38, QColor(255, 255, 255, 0))
        gloss.setColorAt(1.0, QColor(116, 237, 211, 16))
        path = QPainterPath()
        path.addRoundedRect(8, 8, self.width() - 16, self.height() - 16, 31, 31)
        painter.fillPath(path, QBrush(gloss))
        painter.setPen(QPen(QColor(255, 255, 255, 35), 1))
        painter.drawPath(path)
        flare = QLinearGradient(QPointF(0, 0), QPointF(self.width(), self.height()))
        flare.setColorAt(0.0, QColor(122, 244, 216, 18))
        flare.setColorAt(0.6, QColor(122, 244, 216, 0))
        flare.setColorAt(1.0, QColor(108, 173, 255, 20))
        painter.fillRect(self.rect(), QBrush(flare))

    def set_status(self, text: str) -> None:
        self.status.setText(text)

    def animate_in(self) -> None:
        self.show()
        if not self.animated:
            return
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(360)
        self._fade.setStartValue(0.0)
        self._fade.setEndValue(1.0)
        self._fade.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._fade.start()

    def fade_out(self) -> None:
        if not self.isVisible():
            return
        if self._fade is not None:
            self._fade.stop()
        if not self.animated:
            self.close()
            return
        self._fade = QPropertyAnimation(self, b"windowOpacity", self)
        self._fade.setDuration(230)
        self._fade.setStartValue(self.windowOpacity())
        self._fade.setEndValue(0.0)
        self._fade.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._fade.finished.connect(self.close)
        self._fade.start()
