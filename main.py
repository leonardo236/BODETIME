from __future__ import annotations

import sys

from PySide6.QtCore import QEventLoop, QSettings, QThread, Signal
from PySide6.QtWidgets import QApplication


def should_open_setup_wizard(first_install_only: bool, settings_file_exists: bool) -> bool:
    """El paso postinstalación no debe volver a pedir MySQL durante una actualización."""
    return not (first_install_only and settings_file_exists)


if "--configurar-base" in sys.argv:
    from bodetime.config import APP_ENV_FILE

    if should_open_setup_wizard("--setup-inicial" in sys.argv, APP_ENV_FILE.exists()):
        from bodetime.setup_wizard import run_setup_wizard

        sys.exit(run_setup_wizard())
    sys.exit(0)

from bodetime.config import get_settings
from bodetime.database import Database
from bodetime.services import BodeTimeService
from bodetime.splash import SplashScreen
from bodetime.ui import run_app


class _DatabaseStartupThread(QThread):
    """Prepara MySQL sin congelar la pantalla de inicio."""

    completed = Signal(object)

    def __init__(self, database: Database) -> None:
        super().__init__()
        self.database = database
        self.error: str | None = None

    def run(self) -> None:
        try:
            self.database.initialize()
        except Exception as exc:
            self.error = str(exc.orig) if getattr(exc, "orig", None) else str(exc)
        self.completed.emit(self.error)


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setOrganizationName("BODETIME")
    app.setApplicationName("BODETIME")
    app.setStyle("Fusion")
    preferences = QSettings("BODETIME", "BODETIME")
    animated = preferences.value("appearance/animations", True, type=bool)
    splash = SplashScreen(animated=animated)
    splash.animate_in()
    app.processEvents()

    database = Database(get_settings())
    splash.set_status("Conectando con MySQL…")
    app.processEvents()
    task = _DatabaseStartupThread(database)
    wait_for_database = QEventLoop()
    task.finished.connect(wait_for_database.quit)
    task.start()
    try:
        wait_for_database.exec()
        task.wait()
        splash.set_status("Preparando el panel de asistencia…")
        app.processEvents()
        return run_app(BodeTimeService(database), task.error, splash=splash, application=app)
    finally:
        database.close()


if __name__ == "__main__":
    sys.exit(main())
