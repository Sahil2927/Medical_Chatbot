from dataclasses import dataclass

from src.mock.schemas import MessageExchangeMetadata


@dataclass
class AssistantReply:
    content: str
    metadata: MessageExchangeMetadata | None = None
