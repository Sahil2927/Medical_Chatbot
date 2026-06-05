import json

from src.mock.schemas import MessageExchangeMetadata


def serialize_metadata(metadata: MessageExchangeMetadata | None) -> str | None:
    if metadata is None:
        return None
    return metadata.model_dump_json()


def deserialize_metadata(raw: str | None) -> MessageExchangeMetadata | None:
    if not raw:
        return None
    return MessageExchangeMetadata.model_validate(json.loads(raw))
