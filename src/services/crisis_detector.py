import json
import re
from pathlib import Path

from src.mock.schemas import HelplineResource, MessageExchangeMetadata

_HELPLINES_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "crisis_helplines.json"

CRISIS_KEYWORDS = (
    "suicide",
    "suicidal",
    "kill myself",
    "killing myself",
    "self-harm",
    "self harm",
    "hurt myself",
    "end my life",
    "want to die",
    "don't want to live",
    "do not want to live",
)

_CRISIS_PATTERNS = (
    re.compile(r"\b(want|going)\s+to\s+(die|kill\s+myself)\b", re.IGNORECASE),
    re.compile(r"\bno\s+reason\s+to\s+live\b", re.IGNORECASE),
)


def detect_crisis(message: str) -> bool:
    lowered = message.lower()
    if any(keyword in lowered for keyword in CRISIS_KEYWORDS):
        return True
    return any(pattern.search(message) for pattern in _CRISIS_PATTERNS)


def load_helplines() -> list[HelplineResource]:
    with _HELPLINES_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return [HelplineResource(**row) for row in data["helplines"]]


def build_crisis_metadata() -> MessageExchangeMetadata:
    with _HELPLINES_PATH.open(encoding="utf-8") as handle:
        data = json.load(handle)
    return MessageExchangeMetadata(
        crisis_detected=True,
        helplines=load_helplines(),
        region=data.get("default_region", "US"),
    )


def format_crisis_message() -> str:
    return (
        "I'm really glad you reached out. If you are in immediate danger or thinking about harming yourself, "
        "please contact emergency services now. In the U.S., you can call or text 988 for the Suicide & Crisis Lifeline.\n\n"
        "You deserve support from a trained counselor or someone you trust. "
        "I am an educational assistant, not a therapist, and cannot provide crisis counseling."
    )
