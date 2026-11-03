from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Database
from .models import Attendance, WorkSchedule, Worker


class ValidationError(ValueError):
    """Una regla del dominio impide completar la operación."""


class DuplicateCodeError(ValidationError):
    pass


@dataclass(frozen=True)
class AttendanceRow:
    attendance_id: int
    worker_id: int
    code: str
    full_name: str
    day: date
    clock_in: time
    clock_out: time | None
    late: bool


@dataclass(frozen=True)
class DashboardSummary:
    active_workers: int
    present_today: int
    late_today: int
    open_shifts: int


def is_late(clock_in: time, start_time: time, tolerance_minutes: int) -> bool:
    """Compara horas locales del mismo día; el límite de tolerancia es puntual."""
    threshold = (datetime.combine(date.today(), start_time) + timedelta(minutes=tolerance_minutes)).time()
    return clock_in > threshold


class BodeTimeService:
    def __init__(self, database: Database):
        self.database = database

    @staticmethod
    def _clean_worker(code: str, first_name: str, last_name: str, role: str, phone: str) -> dict[str, str | None]:
        fields = {
            "code": code.strip().upper(),
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "role": role.strip(),
            "phone": phone.strip() or None,
        }
        if not fields["code"] or not fields["first_name"] or not fields["last_name"]:
            raise ValidationError("El código, los nombres y los apellidos son obligatorios.")
        if len(fields["code"]) > 20:
            raise ValidationError("El código no puede superar 20 caracteres.")
        if len(fields["first_name"]) > 80 or len(fields["last_name"]) > 80:
            raise ValidationError("Los nombres y apellidos no pueden superar 80 caracteres.")
        if len(fields["role"]) > 80 or (fields["phone"] and len(fields["phone"]) > 30):
            raise ValidationError("El cargo admite 80 caracteres y el teléfono 30.")
        return fields

    def list_workers(self, include_inactive: bool = True) -> list[Worker]:
        with self.database.session() as session:
            query = select(Worker).order_by(Worker.last_name, Worker.first_name)
            if not include_inactive:
                query = query.where(Worker.active.is_(True))
            return list(session.scalars(query))

    def get_worker(self, worker_id: int) -> Worker | None:
        with self.database.session() as session:
            return session.get(Worker, worker_id)

    def create_worker(self, code: str, first_name: str, last_name: str, role: str = "", phone: str = "") -> Worker:
        data = self._clean_worker(code, first_name, last_name, role, phone)
        with self.database.session() as session:
            if session.scalar(select(Worker.id).where(Worker.code == data["code"])):
                raise DuplicateCodeError("Ya existe un trabajador con ese código.")
            worker = Worker(**data, active=True)
            session.add(worker)
            try:
                session.flush()
            except IntegrityError as exc:
                raise DuplicateCodeError("Ya existe un trabajador con ese código.") from exc
            session.refresh(worker)
            return worker

    def update_worker(self, worker_id: int, code: str, first_name: str, last_name: str, role: str = "", phone: str = "") -> Worker:
        data = self._clean_worker(code, first_name, last_name, role, phone)
        with self.database.session() as session:
            worker = session.get(Worker, worker_id)
            if worker is None:
                raise ValidationError("El trabajador seleccionado ya no existe.")
            if session.scalar(select(Worker.id).where(Worker.code == data["code"], Worker.id != worker_id)):
                raise DuplicateCodeError("Ya existe otro trabajador con ese código.")
            for field, value in data.items():
                setattr(worker, field, value)
            try:
                session.flush()
            except IntegrityError as exc:
                raise DuplicateCodeError("Ya existe otro trabajador con ese código.") from exc
            session.refresh(worker)
            return worker

    def deactivate_worker(self, worker_id: int) -> bool:
        with self.database.session() as session:
            worker = session.get(Worker, worker_id)
            if worker is None:
                raise ValidationError("El trabajador seleccionado ya no existe.")
            worker.active = False
            return True

    def attendance_today(self, worker_id: int, now: datetime | None = None) -> Attendance | None:
        moment = now or datetime.now()
        with self.database.session() as session:
            return session.scalar(select(Attendance).where(Attendance.worker_id == worker_id, Attendance.day == moment.date()))

    def mark_entry(self, worker_id: int, now: datetime | None = None) -> Attendance:
        moment = now or datetime.now()
        with self.database.session() as session:
            worker = session.scalar(select(Worker).where(Worker.id == worker_id).with_for_update())
            if worker is None or not worker.active:
                raise ValidationError("Selecciona un trabajador activo.")
            existing = session.scalar(select(Attendance).where(Attendance.worker_id == worker_id, Attendance.day == moment.date()).with_for_update())
            if existing is not None:
                raise ValidationError("Este trabajador ya tiene una entrada registrada para hoy.")
            schedule = session.get(WorkSchedule, 1)
            if schedule is None:
                raise ValidationError("No hay un horario configurado. Abre Configuración y guarda el horario.")
            clock_in = moment.time().replace(microsecond=0)
            attendance = Attendance(worker_id=worker_id, day=moment.date(), clock_in=clock_in, late=is_late(clock_in, schedule.start_time, schedule.tolerance_minutes))
            session.add(attendance)
            try:
                session.flush()
            except IntegrityError as exc:
                raise ValidationError("Ya existe un marcaje de entrada para este trabajador y fecha.") from exc
            session.refresh(attendance)
            return attendance

    def mark_exit(self, worker_id: int, now: datetime | None = None) -> Attendance:
        moment = now or datetime.now()
        with self.database.session() as session:
            attendance = session.scalar(select(Attendance).where(Attendance.worker_id == worker_id, Attendance.day == moment.date()).with_for_update())
            if attendance is None:
                raise ValidationError("No se puede registrar una salida sin una entrada de hoy.")
            if attendance.clock_out is not None:
                raise ValidationError("La salida de hoy ya fue registrada.")
            exit_time = moment.time().replace(microsecond=0)
            if exit_time <= attendance.clock_in:
                raise ValidationError("La hora de salida debe ser posterior a la hora de entrada.")
            attendance.clock_out = exit_time
            session.flush()
            session.refresh(attendance)
            return attendance

    def attendance_history(self, start: date, end: date, worker_id: int | None = None) -> list[AttendanceRow]:
        if start > end:
            raise ValidationError("La fecha inicial no puede ser posterior a la fecha final.")
        with self.database.session() as session:
            query = (select(Attendance, Worker).join(Worker).where(Attendance.day.between(start, end))
                     .order_by(Attendance.day.desc(), Worker.last_name, Worker.first_name))
            if worker_id is not None:
                query = query.where(Attendance.worker_id == worker_id)
            return [AttendanceRow(a.id, w.id, w.code, w.full_name, a.day, a.clock_in, a.clock_out, a.late)
                    for a, w in session.execute(query)]

    def dashboard_summary(self, today: date | None = None) -> DashboardSummary:
        current = today or date.today()
        with self.database.session() as session:
            active = session.scalar(select(func.count()).select_from(Worker).where(Worker.active.is_(True))) or 0
            present = session.scalar(select(func.count()).select_from(Attendance).where(Attendance.day == current)) or 0
            late = session.scalar(select(func.count()).select_from(Attendance).where(Attendance.day == current, Attendance.late.is_(True))) or 0
            opened = session.scalar(select(func.count()).select_from(Attendance).where(Attendance.day == current, Attendance.clock_out.is_(None))) or 0
            return DashboardSummary(active, present, late, opened)

    def get_schedule(self) -> WorkSchedule:
        with self.database.session() as session:
            schedule = session.get(WorkSchedule, 1)
            if schedule is None:
                raise ValidationError("La configuración de horario no está inicializada.")
            return schedule

    def save_schedule(self, start_time: time, tolerance_minutes: int) -> WorkSchedule:
        if not isinstance(start_time, time):
            raise ValidationError("La hora de inicio no es válida.")
        if not 0 <= tolerance_minutes <= 240:
            raise ValidationError("La tolerancia debe estar entre 0 y 240 minutos.")
        with self.database.session() as session:
            schedule = session.get(WorkSchedule, 1)
            if schedule is None:
                schedule = WorkSchedule(id=1, start_time=start_time, tolerance_minutes=tolerance_minutes)
                session.add(schedule)
            else:
                schedule.start_time = start_time
                schedule.tolerance_minutes = tolerance_minutes
            session.flush()
            session.refresh(schedule)
            return schedule
