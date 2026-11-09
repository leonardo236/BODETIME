from __future__ import annotations

import os
import re
import secrets
import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit,
    QMessageBox, QSpinBox, QVBoxLayout,
)
from sqlalchemy import URL, create_engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

from .config import APP_CONFIG_DIR, APP_ENV_FILE, Settings
from .models import Base


def is_valid_database_name(name: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_]+", name))


class DatabaseSetupDialog(QDialog):
    """Configura MySQL una sola vez sin pedir que se edite un archivo .env."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Configurar BODETIME · MySQL")
        self.setMinimumWidth(470)
        self.setModal(True)

        layout = QVBoxLayout(self)
        intro = QLabel(
            "BODETIME necesita MySQL Server 8 instalado y en ejecución. "
            "Ingresa la cuenta administradora local de MySQL; su contraseña "
            "solo se usa para preparar la base y no se guarda."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QFormLayout()
        self.host = QLineEdit("127.0.0.1")
        self.port = QSpinBox(); self.port.setRange(1, 65535); self.port.setValue(3306)
        self.admin_user = QLineEdit("root")
        self.admin_password = QLineEdit()
        self.admin_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.database_name = QLineEdit("bodetime")
        form.addRow("Servidor MySQL", self.host)
        form.addRow("Puerto", self.port)
        form.addRow("Usuario administrador", self.admin_user)
        form.addRow("Contraseña administrador", self.admin_password)
        form.addRow("Nombre de la base", self.database_name)
        layout.addLayout(form)

        self.status = QLabel("El asistente creará la base y un usuario limitado para BODETIME.")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        buttons = QDialogButtonBox()
        self.configure_button = buttons.addButton("Probar y configurar", QDialogButtonBox.ButtonRole.AcceptRole)
        buttons.addButton(QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.configure_database)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def configure_database(self) -> None:
        host = self.host.text().strip()
        admin_user = self.admin_user.text().strip()
        db_name = self.database_name.text().strip()
        admin_password = self.admin_password.text()
        if not host or not admin_user:
            QMessageBox.warning(self, "Faltan datos", "Indica el servidor y el usuario administrador de MySQL.")
            return
        if not is_valid_database_name(db_name):
            QMessageBox.warning(self, "Nombre no válido", "Usa solo letras, números y guion bajo en el nombre de la base.")
            return

        app_password = secrets.token_urlsafe(32)
        admin_engine = None
        app_engine = None
        self.configure_button.setEnabled(False)
        self.status.setText("Conectando y preparando la base de datos…")
        QApplication.processEvents()
        try:
            admin_url = URL.create(
                "mysql+pymysql", username=admin_user, password=admin_password,
                host=host, port=self.port.value(), query={"charset": "utf8mb4"},
            )
            admin_engine = create_engine(admin_url, connect_args={"connect_timeout": 5})
            with admin_engine.begin() as connection:
                connection.execute(text(
                    f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
                    "CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
                ))
                connection.exec_driver_sql(
                    "CREATE USER IF NOT EXISTS 'bodetime_app'@'127.0.0.1' IDENTIFIED BY %s",
                    (app_password,),
                )
                connection.exec_driver_sql(
                    "ALTER USER 'bodetime_app'@'127.0.0.1' IDENTIFIED BY %s",
                    (app_password,),
                )
                connection.exec_driver_sql(
                    f"GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, ALTER, REFERENCES "
                    f"ON `{db_name}`.* TO 'bodetime_app'@'127.0.0.1'"
                )

            app_settings = Settings(host, self.port.value(), db_name, "bodetime_app", app_password)
            app_engine = create_engine(app_settings.database_url(), connect_args={"connect_timeout": 5})
            Base.metadata.create_all(app_engine)
            missing = set(Base.metadata.tables) - set(inspect(app_engine).get_table_names())
            if missing:
                raise RuntimeError("No se pudieron crear todas las tablas: " + ", ".join(sorted(missing)))

            APP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            contents = (
                "# Configuración local de BODETIME. No compartas este archivo.\n"
                f"DB_HOST={host}\nDB_PORT={self.port.value()}\nDB_NAME={db_name}\n"
                f"DB_USER=bodetime_app\nDB_PASSWORD={app_password}\n"
                "DB_CHARSET=utf8mb4\nDB_CONNECT_TIMEOUT=5\nDB_CREATE_SCHEMA=true\n"
            )
            temporary = APP_ENV_FILE.with_suffix(".env.tmp")
            temporary.write_text(contents, encoding="utf-8")
            os.replace(temporary, APP_ENV_FILE)
            self.admin_password.clear()
            QMessageBox.information(
                self, "Configuración completada",
                "MySQL quedó configurado. Se crearon la base y las tablas; "
                "la contraseña administradora no se guardó. Ya puedes abrir BODETIME.",
            )
            self.accept()
        except (SQLAlchemyError, OSError, RuntimeError) as exc:
            self.admin_password.clear()
            detail = getattr(exc, "orig", None) or exc
            self.status.setText("No se pudo completar la configuración. Comprueba que MySQL Server 8 esté iniciado.")
            QMessageBox.critical(self, "No se pudo configurar MySQL", str(detail))
        finally:
            if app_engine is not None:
                app_engine.dispose()
            if admin_engine is not None:
                admin_engine.dispose()
            self.configure_button.setEnabled(True)


def run_setup_wizard() -> int:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("BODETIME · Configuración")
    dialog = DatabaseSetupDialog()
    return 0 if dialog.exec() == QDialog.DialogCode.Accepted else 1
