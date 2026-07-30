import os
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.db.base import Base
from app.main import create_app
from app.modules.transactions.service import ensure_seed_categories


def build_client(database_url: str = "sqlite+pysqlite:///:memory:") -> TestClient:
    engine_kwargs: dict[str, object] = {}
    if database_url.startswith("sqlite"):
        engine_kwargs = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
    engine = create_engine(
        database_url,
        **engine_kwargs,
    )
    Base.metadata.create_all(bind=engine)
    testing_session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with testing_session_local() as seed_session:
        ensure_seed_categories(seed_session)
    app = create_app()

    def override_get_db() -> Generator[Session, None, None]:
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


def build_sqlite_client() -> TestClient:
    return build_client()


def build_postgres_client() -> TestClient:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for PostgreSQL domain integration tests.")
    engine = create_engine(database_url)
    user_columns = {column["name"] for column in inspect(engine).get_columns("users")}
    if "email_ciphertext" not in user_columns:
        pytest.skip("Phase 3 PostgreSQL migration is required for this integration test.")
    return build_client(database_url)


def create_user(client: TestClient, display_name: str = "owner") -> dict[str, str]:
    email = f"user-{uuid4().hex}@example.com"
    response = client.post(
        "/api/v1/auth/signup",
        json={"email": email, "display_name": display_name, "password": "correct-password"},
    )
    assert response.status_code == 201
    token_body = response.json()
    me_response = client.get(
        "/api/v1/me",
        headers={"Authorization": f"Bearer {token_body['access_token']}"},
    )
    assert me_response.status_code == 200
    return {
        "user_id": str(me_response.json()["user_id"]),
        "access_token": str(token_body["access_token"]),
        "refresh_token": str(token_body["refresh_token"]),
        "email": email,
    }


def auth_headers(user: dict[str, str]) -> dict[str, str]:
    return {"Authorization": f"Bearer {user['access_token']}"}


def create_group(client: TestClient, user: dict[str, str]) -> dict[str, object]:
    response = client.post(
        "/api/v1/groups",
        headers=auth_headers(user),
        json={"name": "여행 모임", "relationship_type": "FRIENDS"},
    )
    assert response.status_code == 201
    return response.json()


def add_member(
    client: TestClient, user: dict[str, str], group_id: str, name: str, mbti: str
) -> dict[str, object]:
    response = client.post(
        f"/api/v1/groups/{group_id}/members",
        headers=auth_headers(user),
        json={"display_name": name, "mbti": mbti},
    )
    assert response.status_code == 201
    return response.json()


def test_user_group_and_members_can_be_created_and_group_becomes_ready() -> None:
    client = build_sqlite_client()
    user = create_user(client)
    group = create_group(client, user)

    assert group["member_count"] == 0
    assert group["status"] == "DRAFT"
    assert group["can_analyze"] is False

    first_member = add_member(client, user, str(group["group_id"]), "민지", "ENFP")
    second_member = add_member(client, user, str(group["group_id"]), "준호", "ISTJ")

    assert first_member["mbti"] == "ENFP"
    assert second_member["display_name"] == "준호"

    response = client.get(
        f"/api/v1/groups/{group['group_id']}", headers=auth_headers(user)
    )

    assert response.status_code == 200
    body = response.json()
    assert body["member_count"] == 2
    assert body["status"] == "READY_FOR_ANALYSIS"
    assert body["can_analyze"] is True
    assert [member["mbti"] for member in body["members"]] == ["ENFP", "ISTJ"]


def test_group_member_count_must_not_exceed_four() -> None:
    client = build_sqlite_client()
    user = create_user(client)
    group = create_group(client, user)

    for index, mbti in enumerate(["ENFP", "ISTJ", "INTP", "ESFJ"], start=1):
        add_member(client, user, str(group["group_id"]), f"member-{index}", mbti)

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/members",
        headers=auth_headers(user),
        json={"display_name": "member-5", "mbti": "ENTJ"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CONFLICT"


def test_group_returns_to_draft_when_member_count_drops_below_two() -> None:
    client = build_sqlite_client()
    user = create_user(client)
    group = create_group(client, user)
    first_member = add_member(client, user, str(group["group_id"]), "민지", "ENFP")
    add_member(client, user, str(group["group_id"]), "준호", "ISTJ")

    response = client.delete(
        f"/api/v1/groups/{group['group_id']}/members/{first_member['member_id']}",
        headers=auth_headers(user),
    )
    assert response.status_code == 204

    group_response = client.get(
        f"/api/v1/groups/{group['group_id']}", headers=auth_headers(user)
    )
    assert group_response.status_code == 200
    assert group_response.json()["member_count"] == 1
    assert group_response.json()["status"] == "DRAFT"
    assert group_response.json()["can_analyze"] is False


def test_member_mbti_must_be_valid() -> None:
    client = build_sqlite_client()
    user = create_user(client)
    group = create_group(client, user)

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/members",
        headers=auth_headers(user),
        json={"display_name": "민지", "mbti": "ABCD"},
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_other_users_cannot_access_group() -> None:
    client = build_sqlite_client()
    owner = create_user(client, "owner")
    other_user = create_user(client, "other")
    group = create_group(client, owner)

    response = client.get(
        f"/api/v1/groups/{group['group_id']}", headers=auth_headers(other_user)
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_unknown_user_cannot_list_groups() -> None:
    client = build_sqlite_client()

    response = client.get("/api/v1/groups", headers={"Authorization": "Bearer invalid-token"})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"


def test_member_can_be_updated_and_deleted() -> None:
    client = build_sqlite_client()
    user = create_user(client)
    group = create_group(client, user)
    member = add_member(client, user, str(group["group_id"]), "민지", "ENFP")

    update_response = client.patch(
        f"/api/v1/groups/{group['group_id']}/members/{member['member_id']}",
        headers=auth_headers(user),
        json={"display_name": "민지2", "mbti": "ENTP"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["display_name"] == "민지2"
    assert update_response.json()["mbti"] == "ENTP"

    delete_response = client.delete(
        f"/api/v1/groups/{group['group_id']}/members/{member['member_id']}",
        headers=auth_headers(user),
    )
    assert delete_response.status_code == 204


def test_names_are_trimmed_and_blank_names_are_rejected() -> None:
    client = build_sqlite_client()
    user = create_user(client, " owner ")
    group_response = client.post(
        "/api/v1/groups",
        headers=auth_headers(user),
        json={"name": "  여행 모임  ", "relationship_type": "FRIENDS"},
    )
    assert group_response.status_code == 201
    assert group_response.json()["name"] == "여행 모임"

    member_response = client.post(
        f"/api/v1/groups/{group_response.json()['group_id']}/members",
        headers=auth_headers(user),
        json={"display_name": " 민지 ", "mbti": "ENFP"},
    )
    assert member_response.status_code == 201
    assert member_response.json()["display_name"] == "민지"

    blank_response = client.post(
        "/api/v1/auth/signup",
        json={
            "email": f"blank-{uuid4().hex}@example.com",
            "display_name": "   ",
            "password": "correct-password",
        },
    )
    assert blank_response.status_code == 400
    assert blank_response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_empty_patch_requests_are_rejected() -> None:
    client = build_sqlite_client()
    user = create_user(client)
    group = create_group(client, user)
    member = add_member(client, user, str(group["group_id"]), "민지", "ENFP")

    group_response = client.patch(
        f"/api/v1/groups/{group['group_id']}",
        headers=auth_headers(user),
        json={},
    )
    assert group_response.status_code == 400
    assert group_response.json()["error"]["code"] == "VALIDATION_ERROR"

    member_response = client.patch(
        f"/api/v1/groups/{group['group_id']}/members/{member['member_id']}",
        headers=auth_headers(user),
        json={"display_name": None, "mbti": None},
    )
    assert member_response.status_code == 400
    assert member_response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_duplicate_member_name_returns_conflict() -> None:
    client = build_sqlite_client()
    user = create_user(client)
    group = create_group(client, user)
    first_member = add_member(client, user, str(group["group_id"]), "민지", "ENFP")
    add_member(client, user, str(group["group_id"]), "준호", "ISTJ")

    create_response = client.post(
        f"/api/v1/groups/{group['group_id']}/members",
        headers=auth_headers(user),
        json={"display_name": "민지", "mbti": "ISTJ"},
    )
    update_response = client.patch(
        f"/api/v1/groups/{group['group_id']}/members/{first_member['member_id']}",
        headers=auth_headers(user),
        json={"display_name": "준호"},
    )

    assert create_response.status_code == 409
    assert create_response.json()["error"]["code"] == "CONFLICT"
    assert update_response.status_code == 409
    assert update_response.json()["error"]["code"] == "CONFLICT"


def test_postgres_user_group_member_flow() -> None:
    client = build_postgres_client()
    user = create_user(client, "pg-owner")
    group = create_group(client, user)
    add_member(client, user, str(group["group_id"]), "pg-member-1", "ENFP")
    add_member(client, user, str(group["group_id"]), "pg-member-2", "ISTJ")

    response = client.get(
        f"/api/v1/groups/{group['group_id']}",
        headers=auth_headers(user),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["member_count"] == 2
    assert body["status"] == "READY_FOR_ANALYSIS"
    assert body["can_analyze"] is True
    assert {member["mbti"] for member in body["members"]} == {"ENFP", "ISTJ"}


def test_postgres_concurrent_add_member_stops_at_four() -> None:
    client = build_postgres_client()
    user = create_user(client, "pg-concurrent-owner")
    group = create_group(client, user)
    for index, mbti in enumerate(["ENFP", "ISTJ", "INTP"], start=1):
        add_member(client, user, str(group["group_id"]), f"pg-existing-{index}", mbti)

    def add_concurrent_member(member_name: str) -> int:
        response = client.post(
            f"/api/v1/groups/{group['group_id']}/members",
            headers=auth_headers(user),
            json={"display_name": member_name, "mbti": "ENTJ"},
        )
        return response.status_code

    with ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(add_concurrent_member, ["pg-race-1", "pg-race-2"]))

    group_response = client.get(
        f"/api/v1/groups/{group['group_id']}",
        headers=auth_headers(user),
    )

    assert sorted(statuses) == [201, 409]
    assert group_response.status_code == 200
    assert group_response.json()["member_count"] == 4
