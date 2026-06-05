"""When to use mental health RAG vs direct Groq (clinician manuals pollute retrieval)."""

import re

_PERSONAL_SHARE = re.compile(
    r"\b("
    r"i feel|i am feeling|i've been|i have been|i'm |i am |"
    r"help me|check-in|check in|how are you|"
    r"feeling down|feeling low|can't sleep|cannot sleep"
    r")\b",
    re.IGNORECASE,
)

_EDUCATIONAL = re.compile(
    r"\b("
    r"what is|what are|explain|tell me about|how does|how do|"
    r"definition|symptoms of|signs of|difference between"
    r")\b",
    re.IGNORECASE,
)

_GENERIC_OPENERS = frozenset(
    {
        "hello",
        "hi",
        "hey",
        "good morning",
        "good afternoon",
        "good evening",
        "i'd like a mental health check-in",
        "i would like a mental health check-in",
        "mental health check-in",
    }
)

_LEAKED_CONTEXT = re.compile(
    r"("
    r"\bP:\s|"
    r"\*\*Context:\*\*|"
    r"\bin [A-Za-z][\w\s]{0,40}, \d{1,4}, \d{1,4}\b|"
    r"Chapter \d+ (will teach|in the clinician)|"
    r"clinician.s guide|"
    r"notebook computer so I could literally write"
    r")",
    re.IGNORECASE,
)


def should_use_mental_health_rag(user_message: str) -> bool:
    """Use RAG only for explicit educational questions, not check-ins or feelings."""
    text = user_message.strip()
    if not text:
        return False

    normalized = text.lower().rstrip(".!? ")
    if normalized in _GENERIC_OPENERS:
        return False

    if _PERSONAL_SHARE.search(text):
        return False

    if _EDUCATIONAL.search(text):
        return True

    words = normalized.split()
    if len(words) < 6:
        return False

    if "?" in text and len(words) >= 10:
        return True

    return False


def is_corrupted_mental_health_reply(reply: str) -> bool:
    """Detect answers that regurgitate workbook scripts or index pages."""
    text = reply.strip()
    if not text:
        return True
    if _LEAKED_CONTEXT.search(text):
        return True
    if text[0].islower() and not text.lower().startswith(("i ", "hi", "hello", "thank")):
        return True
    return False
