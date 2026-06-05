import logging
from typing import Protocol

from src.mock.schemas import (
    ConversationResource,
    CreateConversationRequest,
    MessageExchangeResponse,
    QuickActionMode,
)
from src.features import assert_mode_enabled
from src.rag import ensure_rag_chain, invoke_rag
from src.services.appointment_service import generate_appointment_reply
from src.services.exceptions import ChatServiceError
from src.services.lab_results_service import generate_lab_results_reply
from src.services.mental_health_service import generate_mental_health_reply
from src.services.reply_types import AssistantReply

logger = logging.getLogger(__name__)

QuickActionModeType = QuickActionMode | None

DEFAULT_REPLY = (
    "MediAssist received your message. Select a quick action above or ask a health question. "
    "For education only — not medical diagnosis."
)


class ConversationStore(Protocol):
    def list_conversations(self) -> list[dict]: ...

    def get_conversation(self, conversation_id: str) -> dict | None: ...

    def list_messages(self, conversation_id: str) -> list[dict]: ...

    def create_conversation(
        self,
        *,
        title: str | None = None,
        mode: QuickActionMode | None = None,
    ) -> tuple[dict, None]: ...

    def add_message_exchange(
        self,
        conversation_id: str,
        *,
        content: str,
        assistant_content: str,
        mode: QuickActionMode | None = None,
        metadata: object | None = None,
    ) -> MessageExchangeResponse: ...


class ChatService:
    def __init__(self, store: ConversationStore) -> None:
        self._store = store

    def create_conversation(
        self,
        body: CreateConversationRequest,
    ) -> tuple[ConversationResource, MessageExchangeResponse | None]:
        assert_mode_enabled(body.mode)
        conversation, _ = self._store.create_conversation(
            title=body.title,
            mode=body.mode,
        )
        resource = ConversationResource(**conversation)
        if body.content and body.content.strip():
            exchange = self.send_message(
                conversation["id"],
                body.content.strip(),
                body.mode,
            )
            return exchange.conversation, exchange
        return resource, None

    def send_message(
        self,
        conversation_id: str,
        content: str,
        mode: QuickActionModeType = None,
    ) -> MessageExchangeResponse:
        conversation = self._store.get_conversation(conversation_id)
        if not conversation:
            raise ChatServiceError(
                f"Conversation '{conversation_id}' not found.",
                status_code=404,
            )

        effective_mode: QuickActionModeType = conversation.get("mode") or mode
        assert_mode_enabled(effective_mode)
        try:
            reply = self.generate_reply(
                content,
                effective_mode,
                conversation_id=conversation_id,
            )
        except ChatServiceError:
            raise
        except Exception as exc:
            logger.exception("Failed to generate reply for mode=%s", effective_mode)
            raise ChatServiceError(
                "Unable to generate a response. Please try again later.",
            ) from exc

        try:
            return self._store.add_message_exchange(
                conversation_id,
                content=content,
                mode=mode,
                assistant_content=reply.content,
                metadata=reply.metadata,
            )
        except KeyError as exc:
            raise ChatServiceError(
                f"Conversation '{conversation_id}' not found.",
                status_code=404,
            ) from exc

    def generate_reply(
        self,
        user_message: str,
        mode: QuickActionModeType,
        *,
        conversation_id: str | None = None,
    ) -> AssistantReply:
        if mode == "symptoms":
            return AssistantReply(content=self._symptoms_reply(user_message))
        if mode == "appointment":
            return AssistantReply(
                content=generate_appointment_reply(
                    user_message,
                    conversation_id=conversation_id,
                )
            )
        if mode == "mental_health":
            return generate_mental_health_reply(user_message)
        if mode == "lab_results":
            return generate_lab_results_reply(user_message)
        return AssistantReply(content=DEFAULT_REPLY)

    def _symptoms_reply(self, user_message: str) -> str:
        if not ensure_rag_chain():
            raise ChatServiceError(
                "Symptom checking is unavailable until the knowledge base is loaded. "
                "Please try again shortly.",
                status_code=503,
            )
        answer = invoke_rag(user_message)
        if not answer:
            raise ChatServiceError(
                "Empty response from the symptom assistant.",
                status_code=503,
            )
        return answer


def build_chat_service() -> ChatService:
    from src.persistence import get_conversation_store

    return ChatService(get_conversation_store())


chat_service = build_chat_service()
