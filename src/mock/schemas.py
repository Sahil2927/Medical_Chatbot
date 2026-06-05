from typing import Literal

from pydantic import BaseModel, Field

QuickActionMode = Literal["symptoms", "appointment", "mental_health", "lab_results"]


class ConversationResource(BaseModel):
    id: str
    title: str
    mode: QuickActionMode | None = None
    created_at: str
    updated_at: str


class HelplineResource(BaseModel):
    name: str
    phone: str | None = None
    text: str | None = None
    url: str | None = None
    region: str = "US"


class LabResultItem(BaseModel):
    test_id: str
    name: str
    value: float
    unit: str
    status: Literal["low", "normal", "high", "unknown"]
    reference_range: str
    note: str


class MessageExchangeMetadata(BaseModel):
    crisis_detected: bool = False
    helplines: list[HelplineResource] = []
    region: str = "US"
    lab_results: list[LabResultItem] = []


class MessageResource(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: str
    metadata: MessageExchangeMetadata | None = None


class ConversationListResponse(BaseModel):
    conversations: list[ConversationResource]


class MessageListResponse(BaseModel):
    messages: list[MessageResource]


class CreateConversationRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    mode: QuickActionMode | None = None
    content: str | None = Field(default=None, max_length=2000)


class CreateMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000)
    mode: QuickActionMode | None = None


class MessageExchangeResponse(BaseModel):
    conversation: ConversationResource
    user_message: MessageResource
    assistant_message: MessageResource
    metadata: MessageExchangeMetadata | None = None


class MockStatusResponse(BaseModel):
    mock: bool = False
    version: str = "phase-b2"
    supported_modes: list[QuickActionMode]


class ErrorResponse(BaseModel):
    detail: str
