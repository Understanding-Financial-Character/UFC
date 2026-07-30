from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.modules.analysis_results.models import (
    AIReport,
    AIReportStatus,
    AnalysisRun,
    AnalysisRunStatus,
    AnalysisSourceType,
    BehaviorMetric,
    ConsumptionMBTIType,
    ResultStatus,
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
    result_status: ResultStatus = ResultStatus.STANDARD,
) -> AnalysisRun:
    group = seed_group(db)
    return AnalysisResultRepository(db).create_analysis_run(
        group_id=group.id,
        status=AnalysisRunStatus.COMPLETED,
        result_status=result_status,
        provisional_reasons=[] if result_status == ResultStatus.STANDARD else ["LOW_COVERAGE"],
        analysis_period_started_at=datetime(2026, 7, 1, tzinfo=UTC),
        analysis_period_ended_at=datetime(2026, 7, 31, tzinfo=UTC),
        source_type=AnalysisSourceType.MOCK,
        is_synthetic=True,
        input_schema_version="analysis-input-v1",
        analysis_version="analysis-persistence-test-v1",
        snapshot_hash=SNAPSHOT_HASH,
    )


def test_analysis_results_can_be_persisted_and_loaded(db: Session) -> None:
    repository = AnalysisResultRepository(db)
    analysis_run = create_run(db)

    metric = repository.add_behavior_metric(
        analysis_run_id=analysis_run.id,
        metric_code="CATEGORY_CONCENTRATION",
        metric_value=Decimal("0.6400"),
        is_available=True,
        unavailable_reason=None,
        evidence=[
            {
                "metric": "CATEGORY_CONCENTRATION",
                "value": 0.64,
                "basis": "FOOD 카테고리가 전체 지출의 64%를 차지",
            }
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
        snapshot_hash=SNAPSHOT_HASH,
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
        snapshot_hash=SNAPSHOT_HASH,
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
        validation_result={"schema": True},
        failure_reason=None,
        schema_version="grounded-ai-report-v1",
        snapshot_hash=SNAPSHOT_HASH,
    )
    db.commit()

    loaded_run = db.get(AnalysisRun, analysis_run.id)
    assert loaded_run is not None
    assert loaded_run.status == AnalysisRunStatus.COMPLETED
    assert loaded_run.result_status == ResultStatus.STANDARD
    assert loaded_run.snapshot_hash == SNAPSHOT_HASH
    assert metric.metric_metadata["axisContributions"][0]["pole"] == "E"
    assert result.axis_score_directions["EI"]["high"] == "E"
    assert report.status == AIReportStatus.FALLBACK_COMPLETED


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
            snapshot_hash=SNAPSHOT_HASH,
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
        snapshot_hash=SNAPSHOT_HASH,
    )

    assert result.mbti_type is None


def test_repository_validates_axis_contribution_shape(db: Session) -> None:
    repository = AnalysisResultRepository(db)
    analysis_run = create_run(db)

    with pytest.raises(ValueError):
        repository.add_behavior_metric(
            analysis_run_id=analysis_run.id,
            metric_code="CATEGORY_CONCENTRATION",
            metric_value=Decimal("0.6400"),
            is_available=True,
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
            snapshot_hash=SNAPSHOT_HASH,
        )


def test_database_constraints_reject_duplicate_metric_and_invalid_ai_report(db: Session) -> None:
    repository = AnalysisResultRepository(db)
    analysis_run = create_run(db)
    kwargs = {
        "analysis_run_id": analysis_run.id,
        "metric_code": "CATEGORY_CONCENTRATION",
        "metric_value": Decimal("0.6400"),
        "is_available": True,
        "unavailable_reason": None,
        "evidence": [],
        "metric_metadata": {},
        "schema_version": "behavior-metrics-v1",
        "calculation_version": "behavior-metrics-test-v1",
        "snapshot_hash": SNAPSHOT_HASH,
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
            validation_result={},
            failure_reason=None,
            schema_version="grounded-ai-report-v1",
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
        metric_code="REPEAT_MERCHANT_RATIO",
        metric_value=Decimal("0.4200"),
        is_available=True,
        unavailable_reason=None,
        evidence=[],
        metric_metadata={},
        schema_version="behavior-metrics-v1",
        calculation_version="behavior-metrics-test-v1",
        snapshot_hash=SNAPSHOT_HASH,
    )
    db.commit()

    assert [run.id for run in repository.list_group_analysis_runs(analysis_run.group_id)] == [
        analysis_run.id
    ]
    assert [
        metric.metric_code for metric in repository.list_behavior_metrics(analysis_run.id)
    ] == ["REPEAT_MERCHANT_RATIO"]
    assert db.scalar(select(BehaviorMetric.metric_code)) == "REPEAT_MERCHANT_RATIO"
