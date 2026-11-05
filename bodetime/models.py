from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Time, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


# Worker representa la tabla de personas que pueden marcar asistencia.
class Worker(Base):
    __tablename__ = "trabajadores"
    __table_args__ = (
        UniqueConstraint("codigo", name="uq_trabajadores_codigo"),
        Index("ix_trabajadores_activo_nombre", "activo", "apellidos", "nombres"),
    )

    id: Mapped[int] = mapped_column("id_trabajador", Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column("codigo", String(20), nullable=False)
    first_name: Mapped[str] = mapped_column("nombres", String(80), nullable=False)
    last_name: Mapped[str] = mapped_column("apellidos", String(80), nullable=False)
    role: Mapped[str] = mapped_column("cargo", String(80), nullable=False, default="")
    phone: Mapped[Optional[str]] = mapped_column("telefono", String(30))
    active: Mapped[bool] = mapped_column("activo", Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column("creado_en", DateTime, nullable=False, server_default=func.current_timestamp())

    attendances: Mapped[list["Attendance"]] = relationship(back_populates="worker")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class Attendance(Base):
    # La base permite un registro por trabajador y fecha.
    __tablename__ = "asistencias"
    __table_args__ = (
        UniqueConstraint("id_trabajador", "fecha", name="uq_asistencia_trabajador_fecha"),
        CheckConstraint("hora_salida IS NULL OR hora_salida > hora_entrada", name="ck_asistencia_salida_posterior"),
        Index("ix_asistencias_fecha", "fecha"),
    )

    id: Mapped[int] = mapped_column("id_asistencia", Integer, primary_key=True, autoincrement=True)
    worker_id: Mapped[int] = mapped_column("id_trabajador", ForeignKey("trabajadores.id_trabajador", ondelete="RESTRICT"), nullable=False)
    day: Mapped[date] = mapped_column("fecha", Date, nullable=False)
    clock_in: Mapped[time] = mapped_column("hora_entrada", Time, nullable=False)
    clock_out: Mapped[Optional[time]] = mapped_column("hora_salida", Time)
    late: Mapped[bool] = mapped_column("tarde", Boolean, nullable=False, default=False)
    note: Mapped[Optional[str]] = mapped_column("observacion", String(255))

    worker: Mapped[Worker] = relationship(back_populates="attendances")


class WorkSchedule(Base):
    __tablename__ = "configuracion_horario"
    __table_args__ = (
        CheckConstraint("id_configuracion = 1", name="ck_configuracion_id"),
        CheckConstraint("tolerancia_minutos BETWEEN 0 AND 240", name="ck_configuracion_tolerancia"),
    )

    id: Mapped[int] = mapped_column("id_configuracion", Integer, primary_key=True, autoincrement=False, default=1)
    start_time: Mapped[time] = mapped_column("hora_inicio", Time, nullable=False)
    tolerance_minutes: Mapped[int] = mapped_column("tolerancia_minutos", Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column("actualizado_en", DateTime, nullable=False, server_default=func.current_timestamp(), onupdate=func.current_timestamp())
