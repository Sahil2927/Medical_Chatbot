from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.orm import Session, sessionmaker

from src.constants.modes import MODE_LABELS, QuickActionMode
from src.db.models import ConversationModel, MessageModel
from src.db.metadata_codec import deserialize_metadata, serialize_metadata
from src.mock.schemas import (
    ConversationResource,
    MessageExchangeMetadata,
    MessageExchangeResponse,
    MessageResource,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


def _conversation_to_dict(row: ConversationModel) -> dict:
    return {
        "id": row.id,
        "title": row.title,
        "mode": row.mode,
        "created_at": _iso(row.created_at),
        "updated_at": _iso(row.updated_at),
    }


def _message_to_dict(row: MessageModel) -> dict:
    payload = {
        "id": row.id,
        "conversation_id": row.conversation_id,
        "role": row.role,
        "content": row.content,
        "created_at": _iso(row.created_at),
    }
    metadata = deserialize_metadata(row.metadata_json)
    if metadata is not None:
        payload["metadata"] = metadata
    return payload


class PostgresConversationStore:
    """PostgreSQL-backed conversation persistence (SQLite supported for tests)."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def list_conversations(self) -> list[dict]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(ConversationModel).order_by(ConversationModel.updated_at.desc())
            ).all()
            return [_conversation_to_dict(row) for row in rows]

    def get_conversation(self, conversation_id: str) -> dict | None:
        with self._session_factory() as session:
            row = session.get(ConversationModel, conversation_id)
            return _conversation_to_dict(row) if row else None

    def list_messages(self, conversation_id: str) -> list[dict]:
        with self._session_factory() as session:
            rows = session.scalars(
                select(MessageModel)
                .where(MessageModel.conversation_id == conversation_id)
                .order_by(MessageModel.created_at.asc())
            ).all()
            return [_message_to_dict(row) for row in rows]

    def create_conversation(
        self,
        *,
        title: str | None = None,
        mode: QuickActionMode | None = None,
    ) -> tuple[dict, None]:
        now = _utc_now()
        resolved_title = title or (MODE_LABELS[mode] if mode else "New conversation")
        row = ConversationModel(
            id=str(uuid.uuid4()),
            title=resolved_title,
            mode=mode,
            created_at=now,
            updated_at=now,
        )
        with self._session_factory() as session:
            session.add(row)
            session.commit()
            session.refresh(row)
            return _conversation_to_dict(row), None

    def add_message_exchange(
        self,
        conversation_id: str,
        *,
        content: str,
        assistant_content: str,
        mode: QuickActionMode | None = None,
        metadata: MessageExchangeMetadata | None = None,
    ) -> MessageExchangeResponse:
        with self._session_factory() as session:
            conversation = session.get(ConversationModel, conversation_id)
            if not conversation:
                raise KeyError(conversation_id)

            if mode and not conversation.mode:
                conversation.mode = mode

            message_count = session.scalar(
                select(func.count())
                .select_from(MessageModel)
                .where(MessageModel.conversation_id == conversation_id)
            ) or 0
            if message_count == 0:
                conversation.title = self._title_from_first_message(
                    conversation.mode,
                    content,
                )

            user_row = MessageModel(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role="user",
                content=content,
                created_at=_utc_now(),
            )
            assistant_row = MessageModel(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                role="assistant",
                content=assistant_content,
                metadata_json=serialize_metadata(metadata),
                created_at=_utc_now(),
            )
            session.add_all([user_row, assistant_row])
            conversation.updated_at = assistant_row.created_at
            session.commit()
            session.refresh(conversation)
            session.refresh(user_row)
            session.refresh(assistant_row)

            conversation_dict = _conversation_to_dict(conversation)
            return MessageExchangeResponse(
                conversation=ConversationResource(**conversation_dict),
                user_message=MessageResource(**_message_to_dict(user_row)),
                assistant_message=MessageResource(**_message_to_dict(assistant_row)),
                metadata=metadata,
            )

    def _title_from_first_message(
        self,
        mode: str | None,
        content: str,
    ) -> str:
        if mode and mode in MODE_LABELS:
            return MODE_LABELS[mode]  # type: ignore[index]
        trimmed = content.strip()
        return trimmed[:36] + "…" if len(trimmed) > 36 else trimmed or "New conversation"
