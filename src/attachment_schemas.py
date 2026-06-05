from pydantic import BaseModel

from src.mock.schemas import MessageExchangeResponse


class AttachmentResource(BaseModel):
    id: str
    conversation_id: str
    filename: str
    content_type: str
    size_bytes: int
    created_at: str


class AttachmentUploadResponse(BaseModel):
    attachment: AttachmentResource
    extracted_chars: int | None = None
    message_exchange: MessageExchangeResponse | None = None
