from typing import Literal

QuickActionMode = Literal["symptoms", "appointment", "mental_health", "lab_results"]

MODE_LABELS: dict[QuickActionMode, str] = {
    "symptoms": "Check Symptoms",
    "appointment": "Book Appointment",
    "mental_health": "Mental Health Check-in",
    "lab_results": "Review Lab Results",
}
