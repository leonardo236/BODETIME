from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import Session, sessionmaker

from .config import Settings
from .models import Base


class Database:
    def __init__(self, settings: Settings):
        self.engine: Engine = create_engine(
            settings.database_url(),
            pool_pre_ping=True,
            pool_recycle=1800,
            connect_args={"connect_timeout": settings.db_connect_timeout},
        )
        self._sessions = sessionmaker(bind=self.engine, expire_on_commit=False, class_=Session)
        self.create_schema = settings.db_create_schema

    def initialize(self) -> None:
        with self.engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        if self.create_schema:
            Base.metadata.create_all(self.engine)
        missing = set(Base.metadata.tables) - set(inspect(self.engine).get_table_names())
        if missing:
            raise RuntimeError("Faltan tablas en la base de datos: " + ", ".join(sorted(missing)) + ". Ejecuta schema.sql o activa DB_CREATE_SCHEMA.")

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._sessions()
        try:
            # begin confirma al terminar; si hay una excepción, SQLAlchemy revierte.
            with session.begin():
                yield session
        finally:
            session.close()

    def close(self) -> None:
        self.engine.dispose()
