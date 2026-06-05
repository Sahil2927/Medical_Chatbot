def test_lab_results_message_returns_metadata(client):
    created = client.post("/api/conversations", json={"mode": "lab_results"})
    conversation_id = created.json()["id"]

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "glucose 126 mg/dL"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body.get("metadata") is not None
    assert len(body["metadata"]["lab_results"]) == 1
    lab = body["metadata"]["lab_results"][0]
    assert lab["test_id"] == "glucose"
    assert lab["value"] == 126.0
    assert lab["status"] == "high"
    assert "healthcare provider" in body["assistant_message"]["content"].lower()


def test_lab_results_no_values_prompt(client):
    created = client.post("/api/conversations", json={"mode": "lab_results"})
    conversation_id = created.json()["id"]

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "Can you explain my blood work?"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body.get("metadata") is None
    assert "hemoglobin" in body["assistant_message"]["content"].lower()
