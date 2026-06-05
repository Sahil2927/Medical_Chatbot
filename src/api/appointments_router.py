from fastapi import APIRouter, HTTPException, Query, status

from src.db.appointment_store import AppointmentStore
from src.appointment_schemas import (
    AppointmentResource,
    CreateAppointmentRequest,
    ProviderListResponse,
    ProviderResource,
)

router = APIRouter(prefix="/api", tags=["Appointments"])


def _get_store() -> AppointmentStore:
    from src.db.session import get_session_factory

    return AppointmentStore(get_session_factory())


@router.get("/providers", response_model=ProviderListResponse)
def list_providers(
    specialty: str | None = Query(default=None, max_length=120),
) -> ProviderListResponse:
    store = _get_store()
    providers = store.list_providers(specialty=specialty)
    return ProviderListResponse(providers=providers)


@router.post(
    "/appointments",
    response_model=AppointmentResource,
    status_code=status.HTTP_201_CREATED,
)
def create_appointment(body: CreateAppointmentRequest) -> AppointmentResource:
    store = _get_store()
    try:
        return store.create_appointment(
            provider_id=body.provider_id,
            conversation_id=body.conversation_id,
            notes=body.notes,
            status="held",
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Provider '{body.provider_id}' not found.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
