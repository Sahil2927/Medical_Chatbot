def test_list_providers(client):
    response = client.get("/api/providers")
    assert response.status_code == 200
    providers = response.json()["providers"]
    assert len(providers) == 3
    assert all("id" in item and "next_slot" in item for item in providers)


def test_list_providers_filter_specialty(client):
    response = client.get("/api/providers", params={"specialty": "cardio"})
    assert response.status_code == 200
    providers = response.json()["providers"]
    assert len(providers) == 1
    assert providers[0]["specialty"] == "Cardiology"
    assert providers[0]["available"] is True


def test_create_appointment_hold(client):
    response = client.post(
        "/api/appointments",
        json={"provider_id": "prov-cardio-001", "notes": "Annual checkup"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["provider_id"] == "prov-cardio-001"
    assert body["status"] == "held"
    assert body["provider_name"] == "Dr. Nguyen"

    listing = client.get("/api/providers", params={"specialty": "cardio"})
    assert listing.json()["providers"][0]["available"] is False


def test_create_appointment_unknown_provider(client):
    response = client.post(
        "/api/appointments",
        json={"provider_id": "prov-missing"},
    )
    assert response.status_code == 404


def test_create_appointment_conflict_when_slot_held(client):
    first = client.post(
        "/api/appointments",
        json={"provider_id": "prov-derm-001"},
    )
    assert first.status_code == 201
    second = client.post(
        "/api/appointments",
        json={"provider_id": "prov-derm-001"},
    )
    assert second.status_code == 409


def test_appointment_mode_book_via_message(client):
    created = client.post(
        "/api/conversations",
        json={"mode": "appointment"},
    )
    conversation_id = created.json()["id"]

    response = client.post(
        f"/api/conversations/{conversation_id}/messages",
        json={"content": "Please book Dr. Nguyen for cardiology"},
    )
    assert response.status_code == 201
    reply = response.json()["assistant_message"]["content"]
    assert "hold" in reply.lower() or "Confirmation" in reply
    assert "Dr. Nguyen" in reply
