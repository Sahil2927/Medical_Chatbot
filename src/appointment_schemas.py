from typing import Literal

from pydantic import BaseModel, Field


AppointmentStatus = Literal["held", "confirmed"]


class ProviderResource(BaseModel):
    id: str
    name: str
    specialty: str
    next_slot: str
    available: bool = True


class ProviderListResponse(BaseModel):
    providers: list[ProviderResource]


class CreateAppointmentRequest(BaseModel):
    provider_id: str = Field(..., min_length=1, max_length=64)
    conversation_id: str | None = Field(default=None, max_length=36)
    notes: str | None = Field(default=None, max_length=500)


class AppointmentResource(BaseModel):
    id: str
    provider_id: str
    provider_name: str
    specialty: str
    slot: str
    status: AppointmentStatus
    conversation_id: str | None = None
    notes: str | None = None
    created_at: str
