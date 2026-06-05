"""Appointment mode — provider lookup and mock slot holds (B4)."""

import re

from src.db.appointment_store import AppointmentStore
from src.appointment_schemas import ProviderResource


_BOOKING_KEYWORDS = ("book", "schedule", "hold", "reserve", "confirm")


def generate_appointment_reply(
    user_message: str,
    *,
    conversation_id: str | None = None,
    store: AppointmentStore | None = None,
) -> str:
    if store is None:
        from src.db.session import get_session_factory

        store = AppointmentStore(get_session_factory())

    specialty_hint = _infer_specialty(user_message)
    providers = store.list_providers(specialty=specialty_hint)

    if _wants_booking(user_message):
        provider = _resolve_provider_for_booking(user_message, providers, store)
        if provider and provider.available:
            try:
                appointment = store.create_appointment(
                    provider_id=provider.id,
                    conversation_id=conversation_id,
                    notes=user_message[:500],
                    status="held",
                )
                return _format_booking_confirmation(appointment.id, appointment)
            except ValueError:
                return _format_unavailable_reply(providers)
        if provider and not provider.available:
            return _format_unavailable_reply(providers)

    return _format_provider_list_reply(providers, specialty_hint)


def _wants_booking(message: str) -> bool:
    lowered = message.lower()
    return any(keyword in lowered for keyword in _BOOKING_KEYWORDS)


def _resolve_provider_for_booking(
    message: str,
    providers: list[ProviderResource],
    store: AppointmentStore,
) -> ProviderResource | None:
    id_match = re.search(
        r"\b(prov-[a-z]+-\d{3})\b",
        message,
        flags=re.IGNORECASE,
    )
    if id_match:
        provider_id = id_match.group(1).lower()
        for provider in providers:
            if provider.id.lower() == provider_id:
                return provider

    row = store.find_provider_by_name_hint(message)
    if row:
        for provider in providers:
            if provider.id == row.id:
                return provider
    if len(providers) == 1 and providers[0].available:
        return providers[0]
    return None


def _format_provider_list_reply(
    providers: list[ProviderResource],
    specialty_hint: str | None,
) -> str:
    lines = [
        "I can help you find a specialist. Available providers (educational demo):",
        "",
    ]
    if not providers:
        lines.append("No providers match that specialty right now.")
    else:
        for provider in providers:
            status = "available" if provider.available else "slot held"
            lines.append(
                f"- [{provider.id}] {provider.specialty}: {provider.name}, "
                f"next slot {provider.next_slot} ({status})"
            )
    lines.extend(
        [
            "",
            "To hold a slot, reply with e.g. "
            "'book Dr. Nguyen' or 'schedule prov-cardio-001'.",
            "You can also POST /api/appointments with provider_id.",
        ]
    )
    if specialty_hint:
        lines.insert(1, f"(Filtered for: {specialty_hint})")
    return "\n".join(lines)


def _format_booking_confirmation(appointment_id: str, appointment) -> str:
    return (
        f"Your appointment slot is on hold (demo — not a real booking).\n\n"
        f"- Confirmation: {appointment_id}\n"
        f"- Provider: {appointment.provider_name} ({appointment.specialty})\n"
        f"- Slot: {appointment.slot}\n"
        f"- Status: {appointment.status}\n\n"
        "Contact your clinic to confirm. For API clients, "
        "POST /api/appointments created the same hold."
    )


def _format_unavailable_reply(providers: list[ProviderResource]) -> str:
    lines = [
        "That slot is not available or I could not match a provider. "
        "Try another provider:",
        "",
    ]
    for provider in providers:
        if provider.available:
            lines.append(
                f"- [{provider.id}] {provider.specialty}: {provider.name}, "
                f"next slot {provider.next_slot}"
            )
    if len(lines) == 2:
        lines.append("No open slots in the demo list. Please try again later.")
    return "\n".join(lines)


def _infer_specialty(message: str) -> str | None:
    lowered = message.lower()
    mapping: dict[str, str] = {
        "cardio": "cardiology",
        "heart": "cardiology",
        "cardiologist": "cardiology",
        "skin": "dermatology",
        "dermat": "dermatology",
        "general": "general practice",
        "gp": "general practice",
    }
    for keyword, specialty in mapping.items():
        if keyword in lowered:
            return specialty
    return None
