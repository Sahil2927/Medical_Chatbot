"""Lab results mode — parser + JSON reference ranges, optional Pinecone RAG (B6)."""

import logging

from src.lab_results_rag import ensure_lab_results_chain, invoke_lab_results_rag
from src.mock.schemas import LabResultItem, MessageExchangeMetadata
from src.services.lab_parser import parse_lab_values
from src.services.lab_reference import interpret_result
from src.services.reply_types import AssistantReply

logger = logging.getLogger(__name__)

_NO_VALUES_REPLY = (
    "To review lab results, describe the test name and value "
    "(for example: 'hemoglobin 10.5 g/dL' or 'glucose 126 mg/dL'). "
    "I can provide general educational context only — always discuss official "
    "results with your clinician."
)

_FOOTER = (
    "Reference ranges vary by lab, age, and sex. Compare these values with "
    "the ranges printed on your report and follow up with your healthcare provider."
)


def _build_lab_rag_query(user_message: str, interpreted: list) -> str:
    summary = "; ".join(
        f"{r.display_name} {r.value} {r.unit} ({r.status})" for r in interpreted
    )
    return (
        f"User message: {user_message}\n"
        f"Parsed lab values: {summary}\n"
        "Provide brief educational context for these results."
    )


def _invoke_lab_rag_safe(query: str) -> str | None:
    try:
        content = invoke_lab_results_rag(query)
        return content.strip() or None
    except Exception:
        logger.exception("Lab results RAG failed — using parser output only")
        return None


def generate_lab_results_reply(user_message: str) -> AssistantReply:
    parsed = parse_lab_values(user_message)
    if not parsed:
        if ensure_lab_results_chain():
            narrative = _invoke_lab_rag_safe(user_message)
            if narrative:
                return AssistantReply(content=f"{narrative}\n\n{_FOOTER}")
        return AssistantReply(content=_NO_VALUES_REPLY)

    interpreted = [
        interpret_result(item.test, item.value, item.unit or item.test.default_unit)
        for item in parsed
    ]

    lines = [
        "Here is general educational context for what you shared (not a diagnosis):",
        "",
    ]
    for result in interpreted:
        status_label = result.status.upper() if result.status != "unknown" else "CHECK UNIT/RANGE"
        lines.append(
            f"- {result.display_name}: {result.value} {result.unit} "
            f"[{status_label}] — {result.note}"
        )
        lines.append(f"  Reference (typical): {result.reference_range}")

    if ensure_lab_results_chain():
        narrative = _invoke_lab_rag_safe(_build_lab_rag_query(user_message, interpreted))
        if narrative:
            lines.extend(["", "Additional context from the knowledge base:", "", narrative])

    lines.extend(["", _FOOTER])

    metadata = MessageExchangeMetadata(
        lab_results=[
            LabResultItem(
                test_id=r.test_id,
                name=r.display_name,
                value=r.value,
                unit=r.unit,
                status=r.status,
                reference_range=r.reference_range,
                note=r.note,
            )
            for r in interpreted
        ]
    )

    return AssistantReply(content="\n".join(lines), metadata=metadata)
