from __future__ import annotations

import sys


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
from bodetime.ui import run_app


def main() -> int:
    database = Database(get_settings())
    database_error = None
    try:
        # Si MySQL no responde, la ventana muestra el aviso y sigue disponible.
        database.initialize()
    except Exception as exc:
        database_error = str(exc.orig) if getattr(exc, "orig", None) else str(exc)
    try:
        return run_app(BodeTimeService(database), database_error)
    finally:
        database.close()


if __name__ == "__main__":
    sys.exit(main())
