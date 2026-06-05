from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from src.db.models import AppointmentModel, ProviderModel
from src.appointment_schemas import AppointmentResource, ProviderResource


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


class AppointmentStore:
    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_providers(self, *, specialty: str | None = None) -> list[ProviderResource]:
        with self._session_factory() as session:
            query = select(ProviderModel).order_by(ProviderModel.specialty, ProviderModel.name)
            if specialty:
                query = query.where(
                    func.lower(ProviderModel.specialty).contains(specialty.strip().lower())
                )
            rows = session.scalars(query).all()
            held_ids = self._held_provider_ids(session)
            return [
                ProviderResource(
                    id=row.id,
                    name=row.name,
                    specialty=row.specialty,
                    next_slot=row.next_slot,
                    available=row.id not in held_ids,
                )
                for row in rows
            ]

    def create_appointment(
        self,
        *,
        provider_id: str,
        conversation_id: str | None = None,
        notes: str | None = None,
        status: str = "held",
    ) -> AppointmentResource:
        with self._session_factory() as session:
            provider = session.get(ProviderModel, provider_id)
            if not provider:
                raise KeyError(provider_id)

            held_ids = self._held_provider_ids(session)
            if provider_id in held_ids:
                raise ValueError(f"Provider '{provider_id}' has no available slots.")

            row = AppointmentModel(
                id=str(uuid.uuid4()),
                provider_id=provider_id,
                conversation_id=conversation_id,
                notes=notes,
                status=status,
                created_at=_utc_now(),
            )
            session.add(row)
            session.commit()
            session.refresh(row)
            return self._appointment_resource(provider, row)

    def find_provider_by_name_hint(self, message: str) -> ProviderModel | None:
        with self._session_factory() as session:
            rows = session.scalars(select(ProviderModel)).all()
            for row in rows:
                if row.name.lower() in message.lower():
                    return row
                last_name = row.name.split()[-1].lower()
                if last_name in message.lower():
                    return row
            return None

    def _held_provider_ids(self, session: Session) -> set[str]:
        rows = session.scalars(
            select(AppointmentModel.provider_id).where(AppointmentModel.status == "held")
        ).all()
        return set(rows)

    def _appointment_resource(
        self,
        provider: ProviderModel,
        appointment: AppointmentModel,
    ) -> AppointmentResource:
        return AppointmentResource(
            id=appointment.id,
            provider_id=provider.id,
            provider_name=provider.name,
            specialty=provider.specialty,
            slot=provider.next_slot,
            status=appointment.status,  # type: ignore[arg-type]
            conversation_id=appointment.conversation_id,
            notes=appointment.notes,
            created_at=_iso(appointment.created_at),
        )
