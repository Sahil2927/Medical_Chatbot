"""Mental health mode — crisis detection, helpline metadata, Groq / optional RAG."""

import logging

from src.mental_health_llm import invoke_mental_health_chat
from src.mental_health_rag import ensure_mental_health_chain, invoke_mental_health_rag
from src.services.crisis_detector import (
    build_crisis_metadata,
    detect_crisis,
    format_crisis_message,
)
from src.services.mental_health_routing import (
    is_corrupted_mental_health_reply,
    should_use_mental_health_rag,
)
from src.services.reply_types import AssistantReply

logger = logging.getLogger(__name__)

_FALLBACK_SUPPORTIVE = (
    "Thank you for sharing how you're feeling. "
    "Regular sleep, gentle movement, and talking with someone you trust can sometimes help. "
    "If low mood or anxiety persists or affects daily life, consider speaking with a "
    "licensed mental health professional. "
    "In the U.S., you can call or text 988 for the Suicide & Crisis Lifeline."
)


def _generate_supportive_reply(user_message: str) -> str:
    if ensure_mental_health_chain() and should_use_mental_health_rag(user_message):
        content = invoke_mental_health_rag(user_message)
        if not is_corrupted_mental_health_reply(content):
            return content
        logger.warning(
            "Mental health RAG reply looked corrupted — falling back to direct Groq"
        )
    return invoke_mental_health_chat(user_message)


def generate_mental_health_reply(user_message: str) -> AssistantReply:
    if detect_crisis(user_message):
        return AssistantReply(
            content=format_crisis_message(),
            metadata=build_crisis_metadata(),
        )

    try:
        content = _generate_supportive_reply(user_message)
    except Exception:
        logger.exception("Mental health generation failed — using fallback copy")
        content = _FALLBACK_SUPPORTIVE

    if not content.strip():
        content = _FALLBACK_SUPPORTIVE

    return AssistantReply(content=content, metadata=None)
