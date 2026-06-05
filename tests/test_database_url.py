from src.db.session import normalize_database_url


def test_normalize_render_postgres_url():
    url = "postgres://user:pass@host.example/dbname"
    assert (
        normalize_database_url(url)
        == "postgresql+psycopg2://user:pass@host.example/dbname"
    )


def test_normalize_postgresql_url_without_driver():
    url = "postgresql://user:pass@localhost:5432/mediassist"
    assert (
        normalize_database_url(url)
        == "postgresql+psycopg2://user:pass@localhost:5432/mediassist"
    )


def test_passthrough_sqlalchemy_psycopg2_url():
    url = "postgresql+psycopg2://postgres:secret@localhost/mediassist"
    assert normalize_database_url(url) == url


def test_render_postgres_url_adds_ssl_mode(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    url = "postgres://user:pass@dpg-abc.oregon-postgres.render.com/mediassist"
    assert (
        normalize_database_url(url)
        == "postgresql+psycopg2://user:pass@dpg-abc.oregon-postgres.render.com/mediassist?sslmode=require"
    )
