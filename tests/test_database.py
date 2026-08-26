from app.database import normalize_database_url

def test_render_postgres_url_uses_psycopg3_driver():
    assert normalize_database_url("postgresql://user:pass@host/db") == "postgresql+psycopg://user:pass@host/db"

def test_explicit_or_sqlite_urls_are_unchanged():
    assert normalize_database_url("postgresql+psycopg://host/db") == "postgresql+psycopg://host/db"
    assert normalize_database_url("sqlite:///./test.db") == "sqlite:///./test.db"
