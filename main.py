from __future__ import annotations

import sys

from bodetime.config import get_settings
from bodetime.database import Database
from bodetime.services import BodeTimeService
from bodetime.ui import run_app


def main() -> int:
    database = Database(get_settings())
    database_error = None
    try:
        database.initialize()
    except Exception as exc:
        database_error = str(exc.orig) if getattr(exc, "orig", None) else str(exc)
    try:
        return run_app(BodeTimeService(database), database_error)
    finally:
        database.close()


if __name__ == "__main__":
    sys.exit(main())
