from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.analysis.contracts import (
    AnalysisSourceType,
    BehaviorFeatureStatus,
    BehaviorFeatureUnit,
    ProvisionalReason,
    ResultStatus,
)
from app.db.base import Base
from app.modules.analysis_results.models import (
    AIReport,
    AIReportStatus,
    AnalysisRun,
    AnalysisRunStatus,
    BehaviorMetric,
    ConsumptionMBTIType,
)
from app.modules.analysis_results.repository import AnalysisResultRepository
from app.modules.groups.models import Group, RelationshipType
from app.modules.users.models import User

SNAPSHOT_HASH = "a" * 64


@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with session_factory() as session:
        yield session


def seed_group(db: Session) -> Group:
    user = User(
        id=str(uuid4()),
        display_name="owner",
        email_ciphertext="ciphertext",
        email_lookup_hmac=uuid4().hex,
        email_key_version="test-v1",
        password_hash="hash",
    )
    group = Group(
        id=str(uuid4()),
        owner_user_id=user.id,
        name="analysis group",
        relationship_type=RelationshipType.FRIENDS,
    )
    db.add_all([user, group])
    db.flush()
    return group


def create_run(
    db: Session,
    *,
    result_status: ResultStatus | None = ResultStatus.STANDARD,
) -> AnalysisRun:
    group = seed_group(db)
    repository = AnalysisResultRepository(db)
    analysis_run = repository.create_analysis_run(
        group_id=group.id,
        analysis_period_started_at=datetime(2026, 7, 1, tzinfo=UTC),
        analysis_period_ended_at=datetime(2026, 7, 31, tzinfo=UTC),
        source_type=AnalysisSourceType.MOCK,
        is_synthetic=True,
        input_schema_version="analysis-input-v1",
        analysis_version="analysis-persistence-test-v1",
        snapshot_hash=SNAPSHOT_HASH,
    )
    if result_status is not None:
        repository.complete_analysis_run(
            analysis_run.id,
            result_status=result_status,
            provisional_reasons=(
                []
                if result_status == ResultStatus.STANDARD
                else [ProvisionalReason.LOW_CATEGORY_COVERAGE]
            ),
        )
    return analysis_run


def test_analysis_run_lifecycle_separates_execution_and_result_status(db: Session) -> None:
    repository = AnalysisResultRepository(db)
    group = seed_group(db)

    analysis_run = repository.create_analysis_run(
        group_id=group.id,
        analysis_period_started_at=datetime(2026, 7, 1, tzinfo=UTC),
        analysis_period_ended_at=datetime(2026, 7, 31, tzinfo=UTC),
        source_type=AnalysisSourceType.CSV,
        is_synthetic=False,
        input_schema_version="analysis-input-v1",
        analysis_version="analysis-persistence-test-v1",
        snapshot_hash=SNAPSHOT_HASH,
    )

    assert analysis_run.status == AnalysisRunStatus.READY
    assert analysis_run.result_status is None

    completed = repository.complete_analysis_run(
        analysis_run.id,
        result_status=ResultStatus.PROVISIONAL,
        provisional_reasons=[ProvisionalReason.LOW_CATEGORY_COVERAGE],
    )

    assert completed.status == AnalysisRunStatus.COMPLETED
    assert completed.result_status == ResultStatus.PROVISIONAL
    assert completed.provisional_reasons == [ProvisionalReason.LOW_CATEGORY_COVERAGE.value]


def test_analysis_results_can_be_persisted_and_loaded(db: Session) -> None:
    repository = AnalysisResultRepository(db)
    analysis_run = create_run(db)

    metric = repository.add_behavior_metric(
        analysis_run_id=analysis_run.id,
        feature_code="CATEGORY_CONCENTRATION",
        status=BehaviorFeatureStatus.AVAILABLE,
        raw_value=Decimal("0.6400"),
        normalized_score=Decimal("0.8200"),
        unit=BehaviorFeatureUnit.AMOUNT_RATIO,
        sample_count=37,
        unavailable_reason=None,
        evidence=[
            "FOOD 카테고리가 전체 지출의 64%를 차지",
        ],
        metric_metadata={
            "axisContributions": [
                {
                    "axis": "EI",
                    "pole": "E",
                    "weight": 0.30,
                    "contribution": 21.4,
                }
            ]
        },
        schema_version="behavior-metrics-v1",
        calculation_version="behavior-metrics-test-v1",
    )
    result = repository.save_consumption_mbti_result(
        analysis_run_id=analysis_run.id,
        mbti_type=ConsumptionMBTIType.ENFP,
        ei_score=Decimal("0.6400"),
        sn_score=Decimal("0.5200"),
        tf_score=Decimal("0.4800"),
        jp_score=Decimal("0.7000"),
        confidence_level="MEDIUM",
        confidence_score=Decimal("0.6400"),
        coverage=Decimal("0.8500"),
        limitations=[],
        result_metadata={"rule": "deterministic"},
        schema_version="consumption-mbti-v1",
        rule_version="rule-test-v1",
    )
    report = repository.save_ai_report(
        analysis_run_id=analysis_run.id,
        status=AIReportStatus.FALLBACK_COMPLETED,
        report_content={"headline": "ENFP 소비 리포트"},
        model_name="template",
        prompt_version="grounded-report-v1",
        latency_ms=12,
        fallback_used=True,
        fallback_reason="LLMTimeoutError",
        repair_attempted=False,
        validation_result={"schema": True},
        failure_reason=None,
        schema_version="grounded-ai-report-v1",
    )
    db.commit()

    loaded_run = db.get(AnalysisRun, analysis_run.id)
    assert loaded_run is not None
    assert loaded_run.status == AnalysisRunStatus.COMPLETED
    assert loaded_run.result_status == ResultStatus.STANDARD
    assert loaded_run.snapshot_hash == SNAPSHOT_HASH
    assert metric.raw_value == Decimal("0.6400")
    assert metric.normalized_score == Decimal("0.8200")
    assert metric.unit == BehaviorFeatureUnit.AMOUNT_RATIO
    assert metric.sample_count == 37
    assert metric.snapshot_hash == analysis_run.snapshot_hash
    assert result.axis_score_directions["EI"]["high"] == "E"
    assert result.result_status == ResultStatus.STANDARD
    assert report.status == AIReportStatus.FALLBACK_COMPLETED
    assert report.snapshot_hash == analysis_run.snapshot_hash


def test_insufficient_data_does_not_store_forced_mbti(db: Session) -> None:
    repository = AnalysisResultRepository(db)
    analysis_run = create_run(db, result_status=ResultStatus.INSUFFICIENT_DATA)

    with pytest.raises(ValueError):
        repository.save_consumption_mbti_result(
            analysis_run_id=analysis_run.id,
            mbti_type=ConsumptionMBTIType.ENFP,
            ei_score=None,
            sn_score=None,
            tf_score=None,
            jp_score=None,
            confidence_level="LOW",
            confidence_score=Decimal("0.1000"),
            coverage=Decimal("0.1000"),
            limitations=["거래 데이터가 부족합니다."],
            result_metadata={},
            schema_version="consumption-mbti-v1",
            rule_version="rule-test-v1",
        )

    result = repository.save_consumption_mbti_result(
        analysis_run_id=analysis_run.id,
        mbti_type=None,
        ei_score=None,
        sn_score=None,
        tf_score=None,
        jp_score=None,
        confidence_level="LOW",
        confidence_score=Decimal("0.1000"),
        coverage=Decimal("0.1000"),
        limitations=["거래 데이터가 부족합니다."],
        result_metadata={},
        schema_version="consumption-mbti-v1",
        rule_version="rule-test-v1",
    )

    assert result.mbti_type is None


def test_repository_validates_axis_contribution_shape(db: Session) -> None:
    repository = AnalysisResultRepository(db)
    analysis_run = create_run(db)

    with pytest.raises(ValueError):
        repository.add_behavior_metric(
            analysis_run_id=analysis_run.id,
            feature_code="CATEGORY_CONCENTRATION",
            status=BehaviorFeatureStatus.AVAILABLE,
            raw_value=Decimal("0.6400"),
            normalized_score=Decimal("0.8200"),
            unit=BehaviorFeatureUnit.AMOUNT_RATIO,
            sample_count=37,
            unavailable_reason=None,
            evidence=[],
            metric_metadata={
                "axisContributions": [
                    {
                        "axis": "EI",
                        "pole": "N",
                        "weight": 0.30,
                        "contribution": 21.4,
                    }
                ]
            },
            schema_version="behavior-metrics-v1",
            calculation_version="behavior-metrics-test-v1",
        )


def test_repository_rejects_inconsistent_behavior_feature_payloads(db: Session) -> None:
    repository = AnalysisResultRepository(db)
    analysis_run = create_run(db)

    with pytest.raises(ValueError):
        repository.add_behavior_metric(
            analysis_run_id=analysis_run.id,
            feature_code="NEW_MERCHANT_RATIO",
            status=BehaviorFeatureStatus.UNAVAILABLE,
            raw_value=Decimal("0.6400"),
            normalized_score=Decimal("0.8200"),
            unit=BehaviorFeatureUnit.COUNT_RATIO,
            sample_count=37,
            unavailable_reason="INSUFFICIENT_SAMPLE",
            evidence=[],
            metric_metadata={},
            schema_version="behavior-metrics-v1",
            calculation_version="behavior-metrics-test-v1",
        )

    with pytest.raises(ValueError):
        repository.add_behavior_metric(
            analysis_run_id=analysis_run.id,
            feature_code="REPEAT_MERCHANT_RATIO",
            status=BehaviorFeatureStatus.AVAILABLE,
            raw_value=Decimal("0.6400"),
            normalized_score=Decimal("0.8200"),
            unit=BehaviorFeatureUnit.COUNT_RATIO,
            sample_count=37,
            unavailable_reason="SHOULD_NOT_EXIST",
            evidence=[],
            metric_metadata={},
            schema_version="behavior-metrics-v1",
            calculation_version="behavior-metrics-test-v1",
        )


def test_database_constraints_reject_duplicate_metric_and_invalid_ai_report(db: Session) -> None:
    repository = AnalysisResultRepository(db)
    analysis_run = create_run(db)
    kwargs = {
        "analysis_run_id": analysis_run.id,
        "feature_code": "CATEGORY_CONCENTRATION",
        "status": BehaviorFeatureStatus.AVAILABLE,
        "raw_value": Decimal("0.6400"),
        "normalized_score": Decimal("0.8200"),
        "unit": BehaviorFeatureUnit.AMOUNT_RATIO,
        "sample_count": 37,
        "unavailable_reason": None,
        "evidence": [],
        "metric_metadata": {},
        "schema_version": "behavior-metrics-v1",
        "calculation_version": "behavior-metrics-test-v1",
    }
    repository.add_behavior_metric(**kwargs)

    with pytest.raises(IntegrityError):
        repository.add_behavior_metric(**kwargs)
    db.rollback()

    db.add(
        AIReport(
            analysis_run_id=analysis_run.id,
            status=AIReportStatus.FAILED,
            report_content=None,
            model_name="qwen3:4b",
            prompt_version="grounded-report-v1",
            latency_ms=10,
            fallback_used=False,
            repair_attempted=False,
            validation_result={},
            failure_reason=None,
            schema_version="grounded-ai-report-v1",
            snapshot_hash=SNAPSHOT_HASH,
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()


def test_database_constraints_reject_failed_run_with_result_status(db: Session) -> None:
    group = seed_group(db)
    db.add(
        AnalysisRun(
            group_id=group.id,
            status=AnalysisRunStatus.FAILED,
            result_status=ResultStatus.STANDARD,
            provisional_reasons=[],
            analysis_period_started_at=datetime(2026, 7, 1, tzinfo=UTC),
            analysis_period_ended_at=datetime(2026, 7, 31, tzinfo=UTC),
            source_type=AnalysisSourceType.CSV,
            is_synthetic=False,
            input_schema_version="analysis-input-v1",
            analysis_version="analysis-persistence-test-v1",
            snapshot_hash=SNAPSHOT_HASH,
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()


def test_database_constraints_reject_unavailable_feature_with_values(db: Session) -> None:
    analysis_run = create_run(db)
    db.add(
        BehaviorMetric(
            analysis_run_id=analysis_run.id,
            feature_code="NEW_MERCHANT_RATIO",
            status=BehaviorFeatureStatus.UNAVAILABLE,
            raw_value=Decimal("0.6400"),
            normalized_score=Decimal("0.8200"),
            unit=BehaviorFeatureUnit.COUNT_RATIO,
            sample_count=37,
            unavailable_reason="INSUFFICIENT_SAMPLE",
            evidence=[],
            metric_metadata={},
            schema_version="behavior-metrics-v1",
            calculation_version="behavior-metrics-test-v1",
            snapshot_hash=SNAPSHOT_HASH,
        )
    )

    with pytest.raises(IntegrityError):
        db.commit()


def test_repository_lists_group_runs_and_metrics(db: Session) -> None:
    repository = AnalysisResultRepository(db)
    analysis_run = create_run(db)
    repository.add_behavior_metric(
        analysis_run_id=analysis_run.id,
        feature_code="REPEAT_MERCHANT_RATIO",
        status=BehaviorFeatureStatus.AVAILABLE,
        raw_value=Decimal("0.4200"),
        normalized_score=Decimal("0.4200"),
        unit=BehaviorFeatureUnit.COUNT_RATIO,
        sample_count=12,
        unavailable_reason=None,
        evidence=[],
        metric_metadata={},
        schema_version="behavior-metrics-v1",
        calculation_version="behavior-metrics-test-v1",
    )
    db.commit()

    assert [run.id for run in repository.list_group_analysis_runs(analysis_run.group_id)] == [
        analysis_run.id
    ]
    assert [
        metric.feature_code for metric in repository.list_behavior_metrics(analysis_run.id)
    ] == ["REPEAT_MERCHANT_RATIO"]
    assert db.scalar(select(BehaviorMetric.feature_code)) == "REPEAT_MERCHANT_RATIO"


def test_result_status_and_ai_report_consistency_are_validated(db: Session) -> None:
    repository = AnalysisResultRepository(db)
    analysis_run = create_run(db, result_status=None)

    with pytest.raises(ValueError):
        repository.complete_analysis_run(
            analysis_run.id,
            result_status=ResultStatus.STANDARD,
            provisional_reasons=[ProvisionalReason.LOW_CATEGORY_COVERAGE],
        )

    with pytest.raises(ValueError):
        repository.save_ai_report(
            analysis_run_id=analysis_run.id,
            status=AIReportStatus.FALLBACK_COMPLETED,
            report_content={"headline": "fallback"},
            model_name="template",
            prompt_version="grounded-report-v1",
            latency_ms=1,
            fallback_used=False,
            fallback_reason=None,
            repair_attempted=False,
            validation_result={},
            failure_reason=None,
            schema_version="grounded-ai-report-v1",
        )


def test_postgres_analysis_persistence_schema_types() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        pytest.skip("DATABASE_URL is required for PostgreSQL schema integration test.")
    engine = create_engine(database_url)
    if engine.dialect.name != "postgresql":
        pytest.skip("PostgreSQL is required for schema integration test.")

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    assert {
        "analysis_runs",
        "behavior_metrics",
        "consumption_mbti_results",
        "ai_reports",
    }.issubset(table_names)

    enum_names = {enum["name"] for enum in inspector.get_enums()}
    assert {
        "analysis_run_status",
        "analysis_result_status",
        "analysis_source_type",
        "behavior_feature_status",
        "behavior_feature_unit",
        "consumption_mbti_type",
        "ai_report_status",
    }.issubset(enum_names)

    behavior_columns = {
        column["name"]: column["type"] for column in inspector.get_columns("behavior_metrics")
    }
    assert {"raw_value", "normalized_score", "unit", "sample_count", "status"}.issubset(
        behavior_columns
    )
    assert behavior_columns["metric_metadata"].__class__.__name__ == "JSONB"
