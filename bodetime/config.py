from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL


PROJECT_ROOT = Path(__file__).resolve().parent.parent
# En instalaciones de Windows la configuración vive en AppData; al ejecutar
# desde el código fuente se mantiene el .env de la carpeta del proyecto.
APP_CONFIG_DIR = Path(os.getenv("APPDATA", str(PROJECT_ROOT))) / "BODETIME"
APP_ENV_FILE = APP_CONFIG_DIR / ".env"
SOURCE_ENV_FILE = PROJECT_ROOT / ".env"
ENV_FILE = APP_ENV_FILE if APP_ENV_FILE.exists() else SOURCE_ENV_FILE
load_dotenv(ENV_FILE)


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str
    db_charset: str = "utf8mb4"
    db_connect_timeout: int = 5
    db_create_schema: bool = True

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            db_host=os.getenv("DB_HOST", "127.0.0.1"),
            db_port=int(os.getenv("DB_PORT", "3306")),
            db_name=os.getenv("DB_NAME", "bodetime"),
            db_user=os.getenv("DB_USER", "bodetime_app"),
            db_password=os.getenv("DB_PASSWORD", ""),
            db_charset=os.getenv("DB_CHARSET", "utf8mb4"),
            db_connect_timeout=int(os.getenv("DB_CONNECT_TIMEOUT", "5")),
            db_create_schema=os.getenv("DB_CREATE_SCHEMA", "true").lower() in {"1", "true", "yes", "si"},
        )

    def database_url(self) -> URL:
        return URL.create(
            "mysql+pymysql",
            username=self.db_user,
            password=self.db_password,
            host=self.db_host,
            port=self.db_port,
            database=self.db_name,
            query={"charset": self.db_charset},
        )


def get_settings() -> Settings:
    return Settings.from_environment()
