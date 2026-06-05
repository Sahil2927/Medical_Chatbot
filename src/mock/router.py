from fastapi import APIRouter, HTTPException, status

from src.mock.schemas import (
    ConversationListResponse,
    ConversationResource,
    CreateConversationRequest,
    CreateMessageRequest,
    MessageExchangeResponse,
    MessageListResponse,
    MessageResource,
    MockStatusResponse,
)
from src.services.exceptions import ChatServiceError

router = APIRouter(prefix="/api", tags=["MediAssist API"])

SUPPORTED_MODES = ["symptoms", "appointment", "mental_health", "lab_results"]


def _http_error(exc: ChatServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.get("/mock/status", response_model=MockStatusResponse)
def mock_status() -> MockStatusResponse:
    import os

    from src.config import get_settings

    settings = get_settings()
    if not settings.enable_mock_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Not found",
        )

    persistence = (
        "memory"
        if os.getenv("USE_MEMORY_STORE", "").lower() in ("1", "true", "yes")
        else "postgresql"
    )
    enabled = [mode for mode in SUPPORTED_MODES if settings.is_mode_enabled(mode)]
    return MockStatusResponse(
        mock=False,
        version=f"phase-b7-{persistence}",
        supported_modes=enabled,
    )


@router.get("/conversations", response_model=ConversationListResponse)
def list_conversations() -> ConversationListResponse:
    from src.persistence import get_conversation_store

    store = get_conversation_store()
    conversations = [
        ConversationResource(**item) for item in store.list_conversations()
    ]
    return ConversationListResponse(conversations=conversations)


@router.post(
    "/conversations",
    response_model=ConversationResource,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    body: CreateConversationRequest,
) -> ConversationResource:
    from src.services.chat_service import build_chat_service

    service = build_chat_service()
    try:
        conversation, exchange = service.create_conversation(body)
    except ChatServiceError as exc:
        raise _http_error(exc) from exc
    if exchange is not None:
        return exchange.conversation
    return conversation


@router.get(
    "/conversations/{conversation_id}",
    response_model=ConversationResource,
)
def get_conversation(conversation_id: str) -> ConversationResource:
    from src.persistence import get_conversation_store

    store = get_conversation_store()
    conversation = store.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found.",
        )
    return ConversationResource(**conversation)


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=MessageListResponse,
)
def list_messages(conversation_id: str) -> MessageListResponse:
    from src.persistence import get_conversation_store

    store = get_conversation_store()
    if not store.get_conversation(conversation_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation '{conversation_id}' not found.",
        )
    messages = [
        MessageResource(**item)
        for item in store.list_messages(conversation_id)
    ]
    return MessageListResponse(messages=messages)


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=MessageExchangeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_message(
    conversation_id: str,
    body: CreateMessageRequest,
) -> MessageExchangeResponse:
    from src.services.chat_service import build_chat_service

    service = build_chat_service()
    try:
        return service.send_message(
            conversation_id,
            body.content.strip(),
            body.mode,
        )
    except ChatServiceError as exc:
        raise _http_error(exc) from exc
