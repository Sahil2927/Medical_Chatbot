from unittest.mock import patch

from src.services.mental_health_routing import (
    is_corrupted_mental_health_reply,
    should_use_mental_health_rag,
)
from src.services.mental_health_service import generate_mental_health_reply


def test_should_not_rag_for_greeting_or_checkin():
    assert should_use_mental_health_rag("hello") is False
    assert should_use_mental_health_rag("I'd like a mental health check-in.") is False
    assert (
        should_use_mental_health_rag(
            "hello, I feel exhausted and have no confidence in myself"
        )
        is False
    )


def test_should_rag_for_educational_question():
    assert should_use_mental_health_rag("What is generalized anxiety disorder?") is True
    assert should_use_mental_health_rag("Explain cognitive behavioral therapy") is True


def test_detects_corrupted_reply():
    assert is_corrupted_mental_health_reply("sink, I feel like my heart is sinking") is True
    assert is_corrupted_mental_health_reply("P: Good. Chapter 6 will teach you") is True
    assert (
        is_corrupted_mental_health_reply(
            "Thank you for sharing. Feeling exhausted can be draining."
        )
        is False
    )


@patch(
    "src.services.mental_health_service.invoke_mental_health_chat",
    return_value="Hi — I'm glad you reached out. How have you been feeling lately?",
)
@patch(
    "src.services.mental_health_service.invoke_mental_health_rag",
    return_value="sink, I feel overwhelmed and cannot get out of bed.",
)
@patch("src.services.mental_health_service.ensure_mental_health_chain", return_value=True)
def test_personal_share_uses_direct_groq_not_rag(_ready, mock_rag, mock_chat):
    reply = generate_mental_health_reply("hello")
    assert "glad you reached out" in reply.content
    mock_chat.assert_called_once()
    mock_rag.assert_not_called()


@patch(
    "src.services.mental_health_service.invoke_mental_health_chat",
    return_value="Thank you for sharing. Low confidence is difficult.",
)
@patch(
    "src.services.mental_health_service.invoke_mental_health_rag",
    return_value="sink, I feel like my heart is sinking into the ground.",
)
@patch("src.services.mental_health_service.ensure_mental_health_chain", return_value=True)
def test_corrupted_rag_falls_back_to_groq(_ready, mock_rag, mock_chat):
    reply = generate_mental_health_reply("What is depression?")
    assert "difficult" in reply.content
    mock_rag.assert_called_once()
    mock_chat.assert_called_once()
