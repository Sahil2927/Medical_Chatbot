from src.mock.schemas import LabResultItem, MessageExchangeMetadata
from src.db.session import get_session_factory, init_db, reset_engine_cache
from src.persistence import reset_conversation_store
from src.persistence.conversation_store import PostgresConversationStore


def test_assistant_message_metadata_persists_and_reloads(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    reset_engine_cache()
    reset_conversation_store()
    init_db()
    store = PostgresConversationStore(get_session_factory())

    conversation, _ = store.create_conversation(mode="lab_results")
    metadata = MessageExchangeMetadata(
        lab_results=[
            LabResultItem(
                test_id="glucose",
                name="Glucose",
                value=126.0,
                unit="mg/dL",
                status="high",
                reference_range="70–99 mg/dL",
                note="Above typical fasting range.",
            )
        ]
    )
    exchange = store.add_message_exchange(
        conversation["id"],
        content="glucose 126 mg/dL",
        assistant_content="Educational reply",
        mode="lab_results",
        metadata=metadata,
    )

    assert exchange.metadata is not None
    assert exchange.assistant_message.metadata is not None
    assert exchange.assistant_message.metadata.lab_results[0].test_id == "glucose"

    messages = store.list_messages(conversation["id"])
    assistant = messages[1]
    assert assistant["metadata"] is not None
    assert assistant["metadata"].lab_results[0].status == "high"


def test_lab_results_api_message_list_includes_metadata(client):
    created = client.post("/api/conversations", json={"mode": "lab_results"})
    conversation_id = created.json()["id"]

    client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "glucose 126 mg/dL"},
    )

    listed = client.get(f"/api/conversations/{conversation_id}/messages")
    assert listed.status_code == 200
    messages = listed.json()["messages"]
    assistant = next(item for item in messages if item["role"] == "assistant")
    assert assistant.get("metadata") is not None
    assert len(assistant["metadata"]["lab_results"]) == 1
    assert assistant["metadata"]["lab_results"][0]["test_id"] == "glucose"
