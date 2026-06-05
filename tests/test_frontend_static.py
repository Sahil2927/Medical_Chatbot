from pathlib import Path

from fastapi.testclient import TestClient

from src.app_factory import create_app


def test_spa_serves_built_index(tmp_path, monkeypatch):
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text(
        "<!DOCTYPE html><html><body>MediAssist SPA</body></html>",
        encoding="utf-8",
    )
    assets = dist / "assets"
    assets.mkdir()
    (assets / "app.js").write_text("export {};", encoding="utf-8")

    monkeypatch.setenv("FRONTEND_DIST", str(dist))
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("PINECONE_API_KEY", "test-pinecone-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")

    from src.config import get_settings
    from src.db.session import reset_engine_cache
    from src.persistence import reset_conversation_store

    get_settings.cache_clear()
    reset_engine_cache()
    reset_conversation_store()

    app = create_app(load_rag_on_startup=False)
    with TestClient(app) as client:
        root = client.get("/")
        assert root.status_code == 200
        assert "MediAssist SPA" in root.text

        asset = client.get("/assets/app.js")
        assert asset.status_code == 200

        api = client.get("/api/mock/status")
        assert api.status_code == 200

        client_route = client.get("/some/react/route")
        assert client_route.status_code == 200
        assert "MediAssist SPA" in client_route.text


def test_legacy_index_when_dist_missing(monkeypatch):
    monkeypatch.setenv("FRONTEND_DIST", str(Path("/nonexistent/dist/path")))
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    monkeypatch.setenv("PINECONE_API_KEY", "test-pinecone-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")

    from src.config import get_settings
    from src.db.session import reset_engine_cache
    from src.persistence import reset_conversation_store

    get_settings.cache_clear()
    reset_engine_cache()
    reset_conversation_store()

    app = create_app(load_rag_on_startup=False)
    with TestClient(app) as client:
        root = client.get("/")
        assert root.status_code == 200
        assert "chat" in root.text.lower() or root.headers.get("content-type", "").startswith(
            "text/html"
        )
