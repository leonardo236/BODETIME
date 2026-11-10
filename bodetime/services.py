from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
import re
import unicodedata

from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Database
from .models import Attendance, JobRole, WorkSchedule, Worker


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
    # Se suma la tolerancia al horario y se compara con la hora de entrada.
    threshold = (datetime.combine(date.today(), start_time) + timedelta(minutes=tolerance_minutes)).time()
    return clock_in > threshold


class BodeTimeService:
    DEFAULT_WAREHOUSE_ROLES = (
        "Almacenista",
        "Auxiliar de bodega",
        "Bodeguero",
        "Despachador de bodega",
        "Encargado de bodega",
        "Montacarguista",
        "Recepcionista de mercancía",
    )

    def __init__(self, database: Database):
        self.database = database

    @staticmethod
    def _clean_role_name(name: str) -> str:
        cleaned = " ".join(unicodedata.normalize("NFC", name).split())
        if not cleaned or len(cleaned) > 80 or not re.fullmatch(r"[\w .,'’/&():-]+", cleaned, flags=re.UNICODE):
            raise ValidationError("El cargo admite letras, números y separadores sencillos; máximo 80 caracteres.")
        return cleaned

    def list_custom_roles(self) -> list[str]:
        with self.database.session() as session:
            roles = session.scalars(select(JobRole).where(JobRole.active.is_(True)).order_by(JobRole.name))
            return [role.name for role in roles]

    def list_roles(self) -> list[str]:
        custom = self.list_custom_roles()
        default_names = {role.casefold() for role in self.DEFAULT_WAREHOUSE_ROLES}
        return list(self.DEFAULT_WAREHOUSE_ROLES) + [role for role in custom if role.casefold() not in default_names]

    def _require_existing_role(self, session, role_name: str) -> str:
        normalized = self._clean_role_name(role_name)
        for default in self.DEFAULT_WAREHOUSE_ROLES:
            if normalized.casefold() == default.casefold():
                return default
        for role in session.scalars(select(JobRole).where(JobRole.active.is_(True))):
            if normalized.casefold() == role.name.casefold():
                return role.name
        raise ValidationError("Selecciona un cargo del catálogo o agrega uno con el botón «Agregar cargo».")

    def add_custom_role(self, name: str) -> str:
        role_name = self._clean_role_name(name)
        if any(role_name.casefold() == default.casefold() for default in self.DEFAULT_WAREHOUSE_ROLES):
            raise ValidationError("Ese cargo ya está incluido en el catálogo de bodega.")
        with self.database.session() as session:
            if any(role_name.casefold() == role.name.casefold() for role in session.scalars(select(JobRole))):
                raise ValidationError("Ya existe un cargo con ese nombre.")
            role = JobRole(name=role_name, active=True)
            session.add(role)
            try:
                session.flush()
            except IntegrityError as exc:
                raise ValidationError("Ya existe un cargo con ese nombre.") from exc
            return role.name

    def remove_custom_role(self, name: str) -> None:
        role_name = self._clean_role_name(name)
        if any(role_name.casefold() == default.casefold() for default in self.DEFAULT_WAREHOUSE_ROLES):
            raise ValidationError("Los cargos incluidos por BODETIME no se pueden eliminar.")
        with self.database.session() as session:
            role = next((item for item in session.scalars(select(JobRole)) if item.name.casefold() == role_name.casefold()), None)
            if role is None:
                raise ValidationError("El cargo seleccionado ya no existe.")
            assigned = session.scalar(select(func.count()).select_from(Worker).where(Worker.role == role.name)) or 0
            if assigned:
                raise ValidationError(f"No se puede borrar: {assigned} trabajador(es) todavía tienen ese cargo.")
            session.delete(role)

    def worker_delete_info(self, worker_id: int) -> tuple[str, int]:
        with self.database.session() as session:
            worker = session.get(Worker, worker_id)
            if worker is None:
                raise ValidationError("El trabajador seleccionado ya no existe.")
            count = session.scalar(select(func.count()).select_from(Attendance).where(Attendance.worker_id == worker_id)) or 0
            return worker.full_name, count

    def delete_worker(self, worker_id: int) -> int:
        with self.database.session() as session:
            worker = session.scalar(select(Worker).where(Worker.id == worker_id).with_for_update())
            if worker is None:
                raise ValidationError("El trabajador seleccionado ya no existe.")
            deleted_attendances = session.scalar(
                select(func.count()).select_from(Attendance).where(Attendance.worker_id == worker_id)
            ) or 0
            session.execute(delete(Attendance).where(Attendance.worker_id == worker_id))
            session.delete(worker)
            return int(deleted_attendances)

    @staticmethod
    def _clean_worker(code: str, first_name: str, last_name: str, role: str, phone: str) -> dict[str, str | None]:
        def clean_space(value: str) -> str:
            return " ".join(unicodedata.normalize("NFC", value).split())

        def valid_person_name(value: str) -> bool:
            # Acepta letras Unicode y separadores habituales en nombres hispanos.
            has_letter = False
            previous_separator = True
            for char in value:
                category = unicodedata.category(char)
                if category.startswith("L"):
                    has_letter = True
                    previous_separator = False
                elif category.startswith("M") and not previous_separator:
                    continue
                elif char in " '-’.":
                    if previous_separator:
                        return False
                    previous_separator = True
                else:
                    return False
            return has_letter and not previous_separator

        fields = {
            "code": clean_space(code).upper(),
            "first_name": clean_space(first_name),
            "last_name": clean_space(last_name),
            "role": clean_space(role),
            "phone": clean_space(phone) or None,
        }
        if not fields["code"] or not fields["first_name"] or not fields["last_name"]:
            raise ValidationError("El código, los nombres y los apellidos son obligatorios.")
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9_-]{0,19}", fields["code"]):
            raise ValidationError("El código debe tener hasta 20 caracteres: letras, números, guion o guion bajo; debe iniciar con letra o número.")
        if not valid_person_name(fields["first_name"]):
            raise ValidationError("Los nombres solo pueden incluir letras, espacios, guion, apóstrofo o punto.")
        if not valid_person_name(fields["last_name"]):
            raise ValidationError("Los apellidos solo pueden incluir letras, espacios, guion, apóstrofo o punto.")
        if len(fields["first_name"]) > 80 or len(fields["last_name"]) > 80:
            raise ValidationError("Los nombres y apellidos no pueden superar 80 caracteres.")
        role = fields["role"]
        if not role or len(role) > 80 or not re.fullmatch(r"[\w .,'’/&():-]+", role, flags=re.UNICODE):
            raise ValidationError("El cargo admite hasta 80 caracteres y no puede contener símbolos inválidos.")
        if fields["phone"]:
            digits = re.sub(r"\D", "", fields["phone"])
            if (len(fields["phone"]) > 30 or not re.fullmatch(r"\+?[0-9 ()-]+", fields["phone"])
                    or not 7 <= len(digits) <= 15):
                raise ValidationError("El teléfono debe tener entre 7 y 15 dígitos y puede incluir +, espacios, guiones o paréntesis.")
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
            data["role"] = self._require_existing_role(session, str(data["role"]))
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
            data["role"] = self._require_existing_role(session, str(data["role"]))
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

    def reactivate_worker(self, worker_id: int) -> bool:
        with self.database.session() as session:
            worker = session.get(Worker, worker_id)
            if worker is None:
                raise ValidationError("El trabajador seleccionado ya no existe.")
            worker.active = True
            return True

    def attendance_today(self, worker_id: int, now: datetime | None = None) -> Attendance | None:
        moment = now or datetime.now()
        with self.database.session() as session:
            return session.scalar(select(Attendance).where(Attendance.worker_id == worker_id, Attendance.day == moment.date()))

    def mark_entry(self, worker_id: int, now: datetime | None = None) -> Attendance:
        moment = now or datetime.now()
        with self.database.session() as session:
            # El bloqueo y la restricción UNIQUE evitan dos entradas para el mismo día.
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
