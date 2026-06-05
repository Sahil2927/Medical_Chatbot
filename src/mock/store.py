from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from src.constants.modes import MODE_LABELS, QuickActionMode
from src.mock.schemas import MessageExchangeResponse


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MockConversationStore:
    """In-memory store — use only when USE_MEMORY_STORE=true."""

    def __init__(self) -> None:
        self._conversations: dict[str, dict] = {}
        self._messages: dict[str, list[dict]] = {}

    def list_conversations(self) -> list[dict]:
        items = list(self._conversations.values())
        items.sort(key=lambda item: item["updated_at"], reverse=True)
        return items

    def get_conversation(self, conversation_id: str) -> dict | None:
        return self._conversations.get(conversation_id)

    def list_messages(self, conversation_id: str) -> list[dict]:
        return list(self._messages.get(conversation_id, []))

    def create_conversation(
        self,
        *,
        title: str | None = None,
        mode: QuickActionMode | None = None,
    ) -> tuple[dict, None]:
        conversation_id = str(uuid.uuid4())
        now = _utc_now_iso()
        resolved_title = title or (MODE_LABELS[mode] if mode else "New conversation")
        conversation = {
            "id": conversation_id,
            "title": resolved_title,
            "mode": mode,
            "created_at": now,
            "updated_at": now,
        }
        self._conversations[conversation_id] = conversation
        self._messages[conversation_id] = []
        return conversation, None

    def add_message_exchange(
        self,
        conversation_id: str,
        *,
        content: str,
        assistant_content: str,
        mode: QuickActionMode | None = None,
        metadata=None,
    ) -> MessageExchangeResponse:
        from src.mock.schemas import (
            ConversationResource,
            MessageExchangeMetadata,
            MessageExchangeResponse,
            MessageResource,
        )

        conversation = self._conversations.get(conversation_id)
        if not conversation:
            raise KeyError(conversation_id)

        if mode and not conversation.get("mode"):
            conversation["mode"] = mode

        messages = self._messages[conversation_id]
        if len(messages) == 0:
            conversation["title"] = self._title_from_first_message(
                conversation.get("mode"),
                content,
            )

        user_message = self._build_message(conversation_id, "user", content)
        messages.append(user_message)

        assistant_message = self._build_message(
            conversation_id,
            "assistant",
            assistant_content,
            metadata=metadata,
        )
        messages.append(assistant_message)

        conversation["updated_at"] = assistant_message["created_at"]

        return MessageExchangeResponse(
            conversation=ConversationResource(**conversation),
            user_message=MessageResource(**user_message),
            assistant_message=MessageResource(**assistant_message),
            metadata=metadata,
        )

    def _build_message(
        self,
        conversation_id: str,
        role: Literal["user", "assistant"],
        content: str,
        metadata=None,
    ) -> dict:
        payload = {
            "id": str(uuid.uuid4()),
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": _utc_now_iso(),
        }
        if metadata is not None:
            payload["metadata"] = metadata
        return payload

    def _title_from_first_message(
        self,
        mode: QuickActionMode | None,
        content: str,
    ) -> str:
        if mode:
            return MODE_LABELS[mode]
        trimmed = content.strip()
        return trimmed[:36] + "…" if len(trimmed) > 36 else trimmed or "New conversation"


mock_store = MockConversationStore()
