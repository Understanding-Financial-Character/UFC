import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, field_validator
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.api.dependencies import get_db
from app.main import create_app


class SensitivePayload(BaseModel):
    account_number: int


class ValidatorPayload(BaseModel):
    value: str

    @field_validator("value")
    @classmethod
    def reject_value(cls, value: str) -> str:
        raise ValueError("custom validator failed")


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


def test_openapi_contains_foundation_paths_only_once() -> None:
    client = build_client("sqlite+pysqlite:///:memory:")

    response = client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/health" in paths
    assert "/ready" in paths
    assert "/api/v1/meta" in paths
    assert "/api/v1/health" not in paths
    assert "/api/v1/ready" not in paths


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


def test_validation_error_does_not_echo_input() -> None:
    app = create_app()

    @app.post("/test/sensitive-validation")
    def sensitive_validation(payload: SensitivePayload) -> dict[str, bool]:
        return {"ok": bool(payload)}

    client = TestClient(app)

    response = client.post(
        "/test/sensitive-validation",
        json={"account_number": "acct-secret-123"},
    )

    assert response.status_code == 400
    body_text = response.text
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert "acct-secret-123" not in body_text
    assert body["error"]["details"]["errors"] == [
        {
            "field": "body.account_number",
            "type": "int_parsing",
            "message": (
                "Input should be a valid integer, unable to parse string as an integer"
            ),
        }
    ]


def test_custom_validator_error_is_json_serializable() -> None:
    app = create_app()

    @app.post("/test/custom-validator")
    def custom_validator(payload: ValidatorPayload) -> dict[str, bool]:
        return {"ok": bool(payload)}

    client = TestClient(app)

    response = client.post("/test/custom-validator", json={"value": "blocked"})

    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["details"]["errors"] == [
        {
            "field": "body.value",
            "type": "value_error",
            "message": "Value error, custom validator failed",
        }
    ]


def test_invalid_inbound_trace_id_is_replaced() -> None:
    client = build_client("sqlite+pysqlite:///:memory:")
    invalid_trace_id = "x" * 65

    response = client.get("/health", headers={"X-Trace-Id": invalid_trace_id})

    assert response.status_code == 200
    trace_id = response.headers["x-trace-id"]
    assert trace_id != invalid_trace_id
    assert trace_id == response.headers["x-trace-id"]


def test_unhandled_exception_response_and_log_include_trace_id(caplog: pytest.LogCaptureFixture) -> None:
    app = create_app()

    @app.get("/test/unhandled")
    def unhandled() -> None:
        raise RuntimeError("boom")

    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/test/unhandled", headers={"X-Trace-Id": "trace-log-1"})

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.json()["error"]["traceId"] == "trace-log-1"
    assert any(
        record.message == "Unhandled request exception"
        and getattr(record, "trace_id", None) == "trace-log-1"
        for record in caplog.records
    )


def test_database_dependency_closes_session_on_failure() -> None:
    app = create_app()
    closed = {"value": False}

    class BrokenSession:
        def execute(self, statement: object) -> None:
            raise SQLAlchemyError("database unavailable")

        def close(self) -> None:
            closed["value"] = True

    def override_get_db() -> Generator[BrokenSession, None, None]:
        db = BrokenSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    response = client.get("/ready")

    assert response.status_code == 503
    assert closed["value"] is True
