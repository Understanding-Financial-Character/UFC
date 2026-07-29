import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies import get_db
from app.main import create_app


def build_client(database_url: str) -> TestClient:
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def test_health_check() -> None:
    client = build_client("sqlite+pysqlite:///:memory:")

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["x-trace-id"]


def test_ready_check_uses_database() -> None:
    client = build_client("sqlite+pysqlite:///:memory:")

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_check_uses_configured_postgres_database() -> None:
    if not os.getenv("DATABASE_URL"):
        pytest.skip("DATABASE_URL is required for configured database integration test.")

    client = TestClient(create_app())

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_api_meta() -> None:
    client = build_client("sqlite+pysqlite:///:memory:")

    response = client.get("/api/v1/meta")

    assert response.status_code == 200
    assert response.json()["name"] == "UFC API"
    assert response.json()["version"] == "0.1.0"
    assert response.json()["environment"]


def test_error_response_includes_trace_id() -> None:
    app = create_app()

    class BrokenSession:
        def execute(self, statement: object) -> None:
            raise SQLAlchemyError("database unavailable")

        def close(self) -> None:
            return None

    def override_get_db() -> Generator[BrokenSession, None, None]:
        yield BrokenSession()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.get("/ready", headers={"X-Trace-Id": "test-trace-id"})

    assert response.status_code == 503
    body = response.json()
    assert body["error"]["code"] == "DATABASE_UNAVAILABLE"
    assert body["error"]["message"] == "Database is not ready."
    assert body["error"]["traceId"] == "test-trace-id"
