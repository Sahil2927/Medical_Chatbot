def test_upload_txt_lab_results_interprets(client):
    created = client.post("/api/conversations", json={"mode": "lab_results"})
    conversation_id = created.json()["id"]

    response = client.post(
        f"/api/conversations/{conversation_id}/attachments",
        files={"file": ("labs.txt", "glucose 126 mg/dL\n", "text/plain")},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["attachment"]["filename"] == "labs.txt"
    assert body["extracted_chars"] is not None
    exchange = body["message_exchange"]
    assert exchange is not None
    assert exchange["metadata"]["lab_results"][0]["test_id"] == "glucose"
    assert "126" in exchange["assistant_message"]["content"]


def test_upload_unsupported_type(client):
    created = client.post("/api/conversations", json={})
    conversation_id = created.json()["id"]

    response = client.post(
        f"/api/conversations/{conversation_id}/attachments",
        files={"file": ("data.exe", b"binary", "application/octet-stream")},
    )
    assert response.status_code == 422


def test_upload_image_rejected(client):
    created = client.post("/api/conversations", json={"mode": "lab_results"})
    conversation_id = created.json()["id"]

    response = client.post(
        f"/api/conversations/{conversation_id}/attachments",
        files={"file": ("scan.png", b"\x89PNG", "image/png")},
    )
    assert response.status_code == 422
    assert "pdf" in response.json()["detail"].lower()


def test_upload_empty_text_rejected(client):
    created = client.post("/api/conversations", json={"mode": "lab_results"})
    conversation_id = created.json()["id"]

    response = client.post(
        f"/api/conversations/{conversation_id}/attachments",
        files={"file": ("blank.txt", "   \n", "text/plain")},
    )
    assert response.status_code == 422
    assert "no text" in response.json()["detail"].lower()


def test_upload_unknown_conversation(client):
    response = client.post(
        "/api/conversations/missing-id/attachments",
        files={"file": ("a.txt", "hello", "text/plain")},
    )
    assert response.status_code == 404
