"""Trabajos de red para que comprobar/descargar no congele la interfaz."""

from __future__ import annotations

from threading import Event

from PySide6.QtCore import QThread, Signal

from .updater import ReleaseInfo, UpdateCancelled, download_update, get_latest_release


class ReleaseCheckTask(QThread):
    checked = Signal(object)
    failed = Signal(str)

    def run(self) -> None:
        try:
            self.checked.emit(get_latest_release())
        except Exception as exc:
            self.failed.emit(str(exc))


class InstallerDownloadTask(QThread):
    progress = Signal(int)
    ready = Signal(str)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, release: ReleaseInfo):
        super().__init__()
        self.release = release
        self.cancel_event = Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        try:
            path = download_update(self.release, self.progress.emit, self.cancel_event)
        except UpdateCancelled:
            self.cancelled.emit()
        except Exception as exc:
            self.failed.emit(str(exc))
        else:
            self.ready.emit(str(path))
