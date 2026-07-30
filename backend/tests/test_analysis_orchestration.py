from __future__ import annotations

import csv
import json
from io import StringIO

from fastapi.testclient import TestClient
from test_group_member_domain import (
    add_member,
    auth_headers,
    build_sqlite_client,
    create_group,
    create_user,
)

from app.ai.report_generator import ReportGenerationRequest, ReportGenerationResult
from app.core.exceptions import ApiException
from app.orchestration import analysis_service


class JsonReportGenerator:
    def generate(self, request: ReportGenerationRequest) -> ReportGenerationResult:
        content = {
            "headline": "Spending report",
            "summary": "Grounded summary from deterministic evidence.",
            "strengths": ["Uses calculated evidence."],
            "commonPoints": ["Compares member and spending MBTI separately."],
            "differences": ["Personal MBTI and spending MBTI are separate signals."],
            "observationPoints": ["Review limitations before using the result."],
            "conversationQuestions": ["Which spending pattern matched the group best?"],
            "disclaimer": "This is not a real personality or financial diagnosis.",
        }
        return ReportGenerationResult(
            text=json.dumps(content),
            provider="fake",
            model="fake-report",
            metadata={"resultStatus": request.result_status},
        )


class CountingReportGenerator(JsonReportGenerator):
    def __init__(self) -> None:
        self.call_count = 0

    def generate(self, request: ReportGenerationRequest) -> ReportGenerationResult:
        self.call_count += 1
        return super().generate(request)


def patch_report_generator(monkeypatch) -> None:
    monkeypatch.setattr(
        analysis_service,
        "build_report_generator",
        lambda _settings: JsonReportGenerator(),
    )


def setup_ready_group_with_transactions(client: TestClient) -> tuple[dict[str, str], dict[str, object]]:
    user = create_user(client)
    group = create_group(client, user)
    first_member = add_member(client, user, str(group["group_id"]), "member-1", "ENFP")
    second_member = add_member(client, user, str(group["group_id"]), "member-2", "ISTJ")
    categories = client.get("/api/v1/categories").json()
    import_response = client.post(
        f"/api/v1/groups/{group['group_id']}/transactions/import",
        headers=auth_headers(user),
        json={
            "csv_text": analysis_csv_text(
                group_id=str(group["group_id"]),
                member_ids=[str(first_member["member_id"]), str(second_member["member_id"])],
                category_ids=[str(category["category_id"]) for category in categories[:3]],
            )
        },
    )
    assert import_response.status_code == 201
    assert import_response.json()["accepted_count"] == 15
    return user, group


def analysis_csv_text(
    *,
    group_id: str,
    member_ids: list[str],
    category_ids: list[str],
) -> str:
    output = StringIO()
    fieldnames = [
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
        "source_row_key",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for index in range(15):
        writer.writerow(
            {
                "group_id": group_id,
                "member_id": member_ids[index % len(member_ids)],
                "category_id": category_ids[index % len(category_ids)],
                "transaction_at": f"2026-07-{index + 1:02d}T12:00:00+00:00",
                "transaction_type": "WITHDRAWAL",
                "amount": str(1000 + index * 100),
                "merchant_name": f"merchant-{index % 4}",
                "is_shared_expense": "true" if index % 2 == 0 else "false",
                "is_planned": "true" if index % 3 == 0 else "false",
                "is_recurring": "true" if index % 5 == 0 else "false",
                "is_excluded": "false",
                "source_row_key": f"analysis-row-{index}",
            }
        )
    return output.getvalue()


def test_analysis_api_executes_and_persists_results(monkeypatch) -> None:
    patch_report_generator(monkeypatch)
    client = build_sqlite_client()
    user, group = setup_ready_group_with_transactions(client)

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/analyses",
        headers=auth_headers(user),
        json={"period_start": "2026-07-01", "period_end": "2026-07-15"},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["result_status"] in {"STANDARD", "PROVISIONAL", "INSUFFICIENT_DATA"}
    assert body["snapshot_hash"]
    assert len(body["behavior_metrics"]) == 18
    assert body["consumption_mbti_result"] is not None
    assert body["ai_report"]["status"] == "COMPLETED"
    assert "transactions" not in body["ai_report"]["report_content"]

    analysis_id = body["analysis_id"]
    get_response = client.get(f"/api/v1/analyses/{analysis_id}", headers=auth_headers(user))
    latest_response = client.get(
        f"/api/v1/groups/{group['group_id']}/analyses/latest",
        headers=auth_headers(user),
    )

    assert get_response.status_code == 200
    assert get_response.json()["analysis_id"] == analysis_id
    assert latest_response.status_code == 200
    assert latest_response.json()["analysis_id"] == analysis_id


def test_other_user_cannot_access_analysis(monkeypatch) -> None:
    patch_report_generator(monkeypatch)
    client = build_sqlite_client()
    owner, group = setup_ready_group_with_transactions(client)
    other_user = create_user(client, "other")

    create_response = client.post(
        f"/api/v1/groups/{group['group_id']}/analyses",
        headers=auth_headers(owner),
        json={"period_start": "2026-07-01", "period_end": "2026-07-15"},
    )
    assert create_response.status_code == 202
    analysis_id = create_response.json()["analysis_id"]

    response = client.get(f"/api/v1/analyses/{analysis_id}", headers=auth_headers(other_user))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_active_analysis_blocks_new_run(monkeypatch) -> None:
    patch_report_generator(monkeypatch)
    client = build_sqlite_client()
    user, group = setup_ready_group_with_transactions(client)

    def raise_conflict(_db, _group_id: str) -> None:
        raise ApiException(
            code="ANALYSIS_ALREADY_RUNNING",
            message="An analysis is already running for this group.",
            status_code=409,
        )

    monkeypatch.setattr(analysis_service, "prevent_concurrent_analysis", raise_conflict)

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/analyses",
        headers=auth_headers(user),
        json={"period_start": "2026-07-01", "period_end": "2026-07-15"},
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "ANALYSIS_ALREADY_RUNNING"


def test_retry_analysis_rejects_completed_run(monkeypatch) -> None:
    patch_report_generator(monkeypatch)
    client = build_sqlite_client()
    user, group = setup_ready_group_with_transactions(client)

    first_response = client.post(
        f"/api/v1/groups/{group['group_id']}/analyses",
        headers=auth_headers(user),
        json={"period_start": "2026-07-01", "period_end": "2026-07-15"},
    )
    assert first_response.status_code == 202

    retry_response = client.post(
        f"/api/v1/analyses/{first_response.json()['analysis_id']}/retry",
        headers=auth_headers(user),
    )

    assert retry_response.status_code == 409
    assert retry_response.json()["error"]["code"] == "ANALYSIS_RETRY_NOT_ALLOWED"


def test_insufficient_data_does_not_call_report_generator(monkeypatch) -> None:
    report_generator = CountingReportGenerator()
    monkeypatch.setattr(
        analysis_service,
        "build_report_generator",
        lambda _settings: report_generator,
    )
    client = build_sqlite_client()
    user = create_user(client)
    group = create_group(client, user)
    add_member(client, user, str(group["group_id"]), "member-1", "ENFP")
    add_member(client, user, str(group["group_id"]), "member-2", "ISTJ")

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/analyses",
        headers=auth_headers(user),
        json={"period_start": "2026-07-01", "period_end": "2026-07-15"},
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "COMPLETED"
    assert body["result_status"] == "INSUFFICIENT_DATA"
    assert body["ai_report"] is None
    assert body["consumption_mbti_result"] is not None
    assert report_generator.call_count == 0


def test_analysis_period_uses_kst_calendar_boundaries() -> None:
    client = build_sqlite_client()
    user = create_user(client)
    group = create_group(client, user)
    first_member = add_member(client, user, str(group["group_id"]), "member-1", "ENFP")
    second_member = add_member(client, user, str(group["group_id"]), "member-2", "ISTJ")
    category_id = client.get("/api/v1/categories").json()[0]["category_id"]
    output = StringIO()
    fieldnames = [
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
        "source_row_key",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    rows = [
        ("before", "2026-06-30T23:59:00+09:00"),
        ("start", "2026-07-01T00:00:00+09:00"),
        ("end", "2026-07-15T23:59:00+09:00"),
        ("after", "2026-07-16T00:00:00+09:00"),
    ]
    for index, (key, occurred_at) in enumerate(rows):
        writer.writerow(
            {
                "group_id": str(group["group_id"]),
                "member_id": str([first_member["member_id"], second_member["member_id"]][index % 2]),
                "category_id": str(category_id),
                "transaction_at": occurred_at,
                "transaction_type": "WITHDRAWAL",
                "amount": "1000",
                "merchant_name": f"merchant-{key}",
                "is_shared_expense": "true",
                "is_planned": "true",
                "is_recurring": "false",
                "is_excluded": "false",
                "source_row_key": f"kst-boundary-{key}",
            }
        )
    import_response = client.post(
        f"/api/v1/groups/{group['group_id']}/transactions/import",
        headers=auth_headers(user),
        json={"csv_text": output.getvalue()},
    )
    assert import_response.status_code == 201

    response = client.post(
        f"/api/v1/groups/{group['group_id']}/analyses",
        headers=auth_headers(user),
        json={"period_start": "2026-07-01", "period_end": "2026-07-15"},
    )

    assert response.status_code == 202
    metadata = response.json()["consumption_mbti_result"]["metadata"]
    assert metadata["dataQuality"]["included_count"] == 2
