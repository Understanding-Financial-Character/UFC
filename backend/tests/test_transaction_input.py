from __future__ import annotations

import csv
from io import StringIO

from fastapi.testclient import TestClient
from test_group_member_domain import (
    add_member,
    auth_headers,
    build_postgres_client,
    build_sqlite_client,
    create_group,
    create_user,
)


def csv_text(rows: list[dict[str, object]]) -> str:
    output = StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "group_id",
            "member_id",
            "category_id",
            "transaction_at",
            "transaction_type",
            "amount",
            "merchant_name",
            "is_shared_expense",
            "is_planned",
            "is_recurring",
            "is_excluded",
            "exclusion_reason",
            "source_row_key",
        ],
    )
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def setup_group_with_member(client: TestClient) -> tuple[dict[str, str], dict[str, object], dict[str, object]]:
    user = create_user(client)
    group = create_group(client, user)
    member = add_member(client, user, str(group["group_id"]), "member-1", "ENFP")
    return user, group, member


def first_category_id(client: TestClient) -> str:
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 42
    return str(body[0]["category_id"])


def test_csv_transactions_can_be_imported_and_listed() -> None:
    client = build_sqlite_client()
    user, group, member = setup_group_with_member(client)
    category_id = first_category_id(client)

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/transactions/import",
        headers=auth_headers(user),
        json={
            "csv_text": csv_text(
                [
                    {
                        "group_id": group["group_id"],
                        "member_id": member["member_id"],
                        "category_id": category_id,
                        "transaction_at": "2026-07-01T10:00:00+09:00",
                        "transaction_type": "WITHDRAWAL",
                        "amount": "12000",
                        "merchant_name": "Cafe",
                        "is_shared_expense": "TRUE",
                        "is_planned": "",
                        "is_recurring": "",
                        "is_excluded": "FALSE",
                        "exclusion_reason": "",
                        "source_row_key": "csv-ok-1",
                    }
                ]
            )
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["accepted_count"] == 1
    assert body["rejected_count"] == 0
    assert body["source_type"] == "CSV_UPLOAD"

    list_response = client.get(
        f"/api/v1/groups/{group['group_id']}/transactions", headers=auth_headers(user)
    )
    assert list_response.status_code == 200
    assert list_response.json()[0]["source_row_key"] == "csv-ok-1"


def test_csv_import_returns_row_errors_for_bad_date_amount_and_enum() -> None:
    client = build_sqlite_client()
    user, group, member = setup_group_with_member(client)
    category_id = first_category_id(client)

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/transactions/import",
        headers=auth_headers(user),
        json={
            "csv_text": csv_text(
                [
                    {
                        "group_id": group["group_id"],
                        "member_id": member["member_id"],
                        "category_id": category_id,
                        "transaction_at": "not-a-date",
                        "transaction_type": "WITHDRAWAL",
                        "amount": "100",
                        "source_row_key": "bad-date",
                    },
                    {
                        "group_id": group["group_id"],
                        "member_id": member["member_id"],
                        "category_id": category_id,
                        "transaction_at": "2026-07-01T10:00:00",
                        "transaction_type": "WITHDRAWAL",
                        "amount": "NaN",
                        "source_row_key": "bad-amount",
                    },
                    {
                        "group_id": group["group_id"],
                        "member_id": member["member_id"],
                        "category_id": category_id,
                        "transaction_at": "2026-07-01T10:00:00+09:00",
                        "transaction_type": "PAYMENT",
                        "amount": "100",
                        "source_row_key": "bad-enum",
                    },
                ]
            )
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["accepted_count"] == 0
    assert body["rejected_count"] == 3
    error_codes = {error["code"] for row in body["rows"] for error in row["errors"]}
    assert error_codes == {"INVALID_DATETIME", "INVALID_AMOUNT", "INVALID_ENUM"}


def test_csv_import_rejects_length_overflow_invalid_uuid_and_unused_fields() -> None:
    client = build_sqlite_client()
    user, group, _member = setup_group_with_member(client)
    category_id = first_category_id(client)

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/transactions/import",
        headers=auth_headers(user),
        json={
            "csv_text": csv_text(
                [
                    {
                        "group_id": group["group_id"],
                        "member_id": "x" * 37,
                        "category_id": category_id,
                        "transaction_at": "2026-07-01T10:00:00+09:00",
                        "transaction_type": "WITHDRAWAL",
                        "amount": "100",
                        "merchant_name": "m" * 121,
                        "source_row_key": "s" * 121,
                    },
                    {
                        "group_id": group["group_id"],
                        "category_id": category_id,
                        "transaction_at": "2026-07-01T10:00:00+09:00",
                        "transaction_type": "WITHDRAWAL",
                        "amount": "100",
                        "merchant_name": "ok",
                        "source_row_key": ("same-prefix-" + "a" * 120),
                    },
                    {
                        "group_id": group["group_id"],
                        "category_id": category_id,
                        "transaction_at": "2026-07-01T10:00:00+09:00",
                        "transaction_type": "WITHDRAWAL",
                        "amount": "100",
                        "merchant_name": "ok",
                        "source_row_key": ("same-prefix-" + "a" * 119 + "b"),
                    },
                ]
            )
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["accepted_count"] == 0
    assert body["rejected_count"] == 3
    first_row_codes = {error["code"] for error in body["rows"][0]["errors"]}
    assert first_row_codes == {"MAX_LENGTH_EXCEEDED"}

    unsupported_csv = "group_id,category_id,transaction_at,transaction_type,amount,currency_code\n"
    unsupported_csv += f"{group['group_id']},{category_id},2026-07-01T10:00:00+09:00,WITHDRAWAL,100,USD\n"
    unsupported_response = client.post(
        f"/api/v1/groups/{group['group_id']}/transactions/import",
        headers=auth_headers(user),
        json={"csv_text": unsupported_csv},
    )
    assert unsupported_response.status_code == 201
    assert unsupported_response.json()["rows"][0]["errors"][0]["code"] == "CSV_UNKNOWN_FIELD"


def test_csv_import_rejects_missing_category_other_group_member_and_duplicate_key() -> None:
    client = build_sqlite_client()
    user, group, member = setup_group_with_member(client)
    other_group = create_group(client, user)
    other_member = add_member(client, user, str(other_group["group_id"]), "other", "ISTJ")
    category_id = first_category_id(client)

    first_response = client.post(
        f"/api/v1/groups/{group['group_id']}/transactions/import",
        headers=auth_headers(user),
        json={
            "csv_text": csv_text(
                [
                    {
                        "group_id": group["group_id"],
                        "member_id": member["member_id"],
                        "category_id": category_id,
                        "transaction_at": "2026-07-01T10:00:00+09:00",
                        "transaction_type": "WITHDRAWAL",
                        "amount": "100",
                        "source_row_key": "dup-key",
                    }
                ]
            )
        },
    )
    assert first_response.status_code == 201
    assert first_response.json()["accepted_count"] == 1

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/transactions/import",
        headers=auth_headers(user),
        json={
            "csv_text": csv_text(
                [
                    {
                        "group_id": group["group_id"],
                        "member_id": member["member_id"],
                        "category_id": "00000000-0000-4000-8000-000000000001",
                        "transaction_at": "2026-07-01T10:00:00+09:00",
                        "transaction_type": "WITHDRAWAL",
                        "amount": "100",
                        "source_row_key": "missing-category",
                    },
                    {
                        "group_id": group["group_id"],
                        "member_id": other_member["member_id"],
                        "category_id": category_id,
                        "transaction_at": "2026-07-01T10:00:00+09:00",
                        "transaction_type": "WITHDRAWAL",
                        "amount": "100",
                        "source_row_key": "other-member",
                    },
                    {
                        "group_id": group["group_id"],
                        "member_id": member["member_id"],
                        "category_id": category_id,
                        "transaction_at": "2026-07-01T10:00:00+09:00",
                        "transaction_type": "WITHDRAWAL",
                        "amount": "100",
                        "source_row_key": "dup-key",
                    },
                ]
            )
        },
    )

    assert response.status_code == 201
    codes = {row["errors"][0]["code"] for row in response.json()["rows"]}
    assert codes == {"CATEGORY_NOT_FOUND", "MEMBER_NOT_IN_GROUP", "DUPLICATE_SOURCE_ROW_KEY"}


def test_other_user_cannot_access_group_transactions() -> None:
    client = build_sqlite_client()
    owner, group, _member = setup_group_with_member(client)
    other_user = create_user(client, "other")
    category_id = first_category_id(client)

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/transactions/import",
        headers=auth_headers(other_user),
        json={
            "csv_text": csv_text(
                [
                    {
                        "group_id": group["group_id"],
                        "category_id": category_id,
                        "transaction_at": "2026-07-01T10:00:00+09:00",
                        "transaction_type": "WITHDRAWAL",
                        "amount": "100",
                        "source_row_key": "forbidden",
                    }
                ]
            )
        },
    )

    assert owner["user_id"] != other_user["user_id"]
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_nullable_behavior_fields_are_preserved_and_excluded_transactions_update() -> None:
    client = build_sqlite_client()
    user, group, _member = setup_group_with_member(client)
    category_id = first_category_id(client)

    import_response = client.post(
        f"/api/v1/groups/{group['group_id']}/transactions/import",
        headers=auth_headers(user),
        json={
            "csv_text": csv_text(
                [
                    {
                        "group_id": group["group_id"],
                        "category_id": category_id,
                        "transaction_at": "2026-07-01T10:00:00+09:00",
                        "transaction_type": "WITHDRAWAL",
                        "amount": "100",
                        "is_shared_expense": "",
                        "is_planned": "",
                        "is_recurring": "",
                        "is_excluded": "FALSE",
                        "source_row_key": "nullable-fields",
                    }
                ]
            )
        },
    )
    transaction_id = import_response.json()["rows"][0]["transaction_id"]

    list_response = client.get(
        f"/api/v1/groups/{group['group_id']}/transactions", headers=auth_headers(user)
    )
    transaction = list_response.json()[0]
    assert transaction["is_shared_expense"] is None
    assert transaction["is_planned"] is None
    assert transaction["is_recurring"] is None

    patch_response = client.patch(
        f"/api/v1/groups/{group['group_id']}/transactions/{transaction_id}",
        headers=auth_headers(user),
        json={"is_excluded": True, "exclusion_reason": "test duplicate"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["is_excluded"] is True
    assert patch_response.json()["exclusion_reason"] == "test duplicate"

    delete_response = client.delete(
        f"/api/v1/groups/{group['group_id']}/transactions/{transaction_id}",
        headers=auth_headers(user),
    )
    assert delete_response.status_code == 204


def test_mock_scenario_can_be_applied_to_group() -> None:
    client = build_sqlite_client()
    user, group, _member = setup_group_with_member(client)
    for index, mbti in enumerate(["ISTJ", "ENTP", "ESFJ"], start=2):
        add_member(client, user, str(group["group_id"]), f"member-{index}", mbti)

    scenarios_response = client.get("/api/v1/mock-scenarios")
    assert scenarios_response.status_code == 200
    assert scenarios_response.json()[0]["scenario_id"] == "mock-v2"

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/mock-scenarios/mock-v2/apply",
        headers=auth_headers(user),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["source_type"] == "MOCK"
    assert body["accepted_count"] > 0
    assert body["rejected_count"] == 0


def test_mock_scenario_rejects_member_count_mismatch() -> None:
    client = build_sqlite_client()
    user, group, _member = setup_group_with_member(client)

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/mock-scenarios/mock-v2/apply",
        headers=auth_headers(user),
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "MOCK_MEMBER_COUNT_MISMATCH"


def test_postgres_transaction_import_preserves_nullable_fields() -> None:
    client = build_postgres_client()
    user, group, member = setup_group_with_member(client)
    category_id = first_category_id(client)

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/transactions/import",
        headers=auth_headers(user),
        json={
            "csv_text": csv_text(
                [
                    {
                        "group_id": group["group_id"],
                        "member_id": member["member_id"],
                        "category_id": category_id,
                        "transaction_at": "2026-07-01T10:00:00+09:00",
                        "transaction_type": "WITHDRAWAL",
                        "amount": "12000",
                        "is_shared_expense": "",
                        "is_planned": "",
                        "is_recurring": "",
                        "source_row_key": "pg-nullable-fields",
                    }
                ]
            )
        },
    )

    assert response.status_code == 201
    assert response.json()["accepted_count"] == 1

    list_response = client.get(
        f"/api/v1/groups/{group['group_id']}/transactions", headers=auth_headers(user)
    )
    assert list_response.status_code == 200
    transaction = list_response.json()[0]
    assert transaction["transaction_type"] == "WITHDRAWAL"
    assert transaction["is_shared_expense"] is None
    assert transaction["is_planned"] is None
    assert transaction["is_recurring"] is None
