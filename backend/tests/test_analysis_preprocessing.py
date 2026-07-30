from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal

import pytest

from app.analysis.contracts import (
    AnalysisInput,
    AnalysisMemberInput,
    AnalysisPeriod,
    AnalysisSourceType,
    AnalysisTransactionInput,
    AnalysisTransactionType,
    BehaviorGroup,
    GroupPurposeType,
    ProvisionalReason,
    ResultStatus,
)
from app.analysis.errors import AnalysisInputError
from app.analysis.preprocessing import preprocess_analysis_input


def build_transaction(
    index: int,
    *,
    transaction_type: AnalysisTransactionType = AnalysisTransactionType.WITHDRAWAL,
    category_code: str | None = "food",
    behavior_group: BehaviorGroup | None = BehaviorGroup.PRACTICAL,
    merchant_key: str | None = " Cafe Place ",
    occurred_at: datetime | None = None,
    is_excluded: bool = False,
    is_shared_expense: bool | None = None,
    is_planned: bool | None = None,
    is_recurring: bool | None = None,
    source_type: AnalysisSourceType | None = None,
) -> AnalysisTransactionInput:
    return AnalysisTransactionInput(
        transaction_id=f"txn-{index:03d}",
        group_id="group-1",
        member_id="member-1",
        occurred_at=occurred_at or datetime(2026, 7, 1, 12, index, tzinfo=UTC),
        amount=Decimal("1000.00"),
        category_code=category_code,
        behavior_group=behavior_group,
        merchant_key=merchant_key,
        transaction_type=transaction_type,
        is_shared_expense=is_shared_expense,
        is_planned=is_planned,
        is_recurring=is_recurring,
        source_type=source_type,
        is_excluded=is_excluded,
    )


def build_input(
    transactions: tuple[AnalysisTransactionInput, ...],
    *,
    started_at: datetime = datetime(2026, 7, 1, tzinfo=UTC),
    ended_at: datetime = datetime(2026, 7, 31, 23, 59, tzinfo=UTC),
    source_type: AnalysisSourceType = AnalysisSourceType.CSV,
    is_synthetic: bool = False,
) -> AnalysisInput:
    return AnalysisInput(
        analysis_id="analysis-1",
        group_id="group-1",
        group_purpose_type=GroupPurposeType.TRAVEL,
        analysis_period=AnalysisPeriod(started_at=started_at, ended_at=ended_at),
        source_type=source_type,
        is_synthetic=is_synthetic,
        members=(AnalysisMemberInput(member_id="member-1", mbti_type="ENFP"),),
        transactions=transactions,
    )


def test_preprocessing_includes_only_non_excluded_withdrawals_and_preserves_tri_state() -> None:
    transactions = (
        build_transaction(
            1,
            occurred_at=datetime(2026, 7, 1, 21, 30, tzinfo=timezone(timedelta(hours=9))),
            merchant_key="  Cafe   Place!! ",
            is_shared_expense=True,
            is_planned=None,
            is_recurring=False,
        ),
        build_transaction(2, transaction_type=AnalysisTransactionType.DEPOSIT),
        build_transaction(3, transaction_type=AnalysisTransactionType.REFUND),
        build_transaction(4, transaction_type=AnalysisTransactionType.TRANSFER),
        build_transaction(5, transaction_type=AnalysisTransactionType.ADJUSTMENT),
        build_transaction(6, is_excluded=True),
    )

    result = preprocess_analysis_input(build_input(transactions))

    assert result.included_count == 1
    assert result.excluded_count == 5
    normalized = result.normalized_transactions[0]
    assert normalized.occurred_at == datetime(2026, 7, 1, 12, 30, tzinfo=UTC)
    assert normalized.category_code == "FOOD"
    assert normalized.merchant_key == "cafe-place"
    assert normalized.is_shared_expense is True
    assert normalized.is_planned is None
    assert normalized.is_recurring is False
    assert {excluded.reason for excluded in result.excluded_transactions} == {
        "DEPOSIT_EXCLUDED_FROM_SPENDING_ANALYSIS",
        "REFUND_EXCLUDED_FROM_SPENDING_ANALYSIS",
        "TRANSFER_EXCLUDED_FROM_SPENDING_ANALYSIS",
        "ADJUSTMENT_EXCLUDED_FROM_SPENDING_ANALYSIS",
        "SOURCE_TRANSACTION_EXCLUDED",
    }


def test_quality_report_marks_standard_when_data_is_sufficient() -> None:
    transactions = tuple(
        build_transaction(
            index,
            occurred_at=datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
            + timedelta(days=(index - 1) * 2),
        )
        for index in range(1, 11)
    )

    result = preprocess_analysis_input(build_input(transactions))

    assert result.included_count == 10
    assert result.analysis_eligible is True
    assert result.result_status_candidate == ResultStatus.STANDARD
    assert result.provisional_reasons == ()
    assert result.data_quality_report.requested_period_days == 31
    assert result.data_quality_report.observed_period_days == 19
    assert result.data_quality_report.analysis_period_days == 19
    assert result.data_quality_report.category_coverage == 1.0
    assert result.data_quality_report.merchant_coverage == 1.0
    assert result.data_quality_score == 1.0


def test_sparse_transactions_are_insufficient_not_provisional() -> None:
    transactions = (
        build_transaction(1, category_code=None, behavior_group=None, merchant_key=None),
        build_transaction(
            2,
            category_code="food",
            merchant_key=None,
            occurred_at=datetime(2026, 7, 3, tzinfo=UTC),
        ),
    )
    result = preprocess_analysis_input(
        build_input(
            transactions,
            started_at=datetime(2026, 7, 1, tzinfo=UTC),
            ended_at=datetime(2026, 7, 3, tzinfo=UTC),
            source_type=AnalysisSourceType.MOCK,
            is_synthetic=True,
        )
    )

    assert result.analysis_eligible is False
    assert result.result_status_candidate == ResultStatus.INSUFFICIENT_DATA
    assert result.provisional_reasons == (
        ProvisionalReason.INSUFFICIENT_TRANSACTION_COUNT,
        ProvisionalReason.INSUFFICIENT_ANALYSIS_PERIOD,
        ProvisionalReason.LOW_CATEGORY_COVERAGE,
        ProvisionalReason.LOW_MERCHANT_COVERAGE,
        ProvisionalReason.SYNTHETIC_DATA,
    )
    assert result.data_quality_report.category_coverage == 0.5
    assert result.data_quality_report.merchant_coverage == 0.0


def test_quality_report_marks_provisional_when_eligible_with_low_coverage_synthetic_data() -> None:
    transactions = tuple(
        build_transaction(
            index,
            category_code="food" if index <= 6 else None,
            merchant_key=None,
            occurred_at=datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
            + timedelta(days=(index - 1) * 2),
        )
        for index in range(1, 11)
    )
    result = preprocess_analysis_input(
        build_input(
            transactions,
            source_type=AnalysisSourceType.MOCK,
            is_synthetic=True,
        )
    )

    assert result.analysis_eligible is True
    assert result.result_status_candidate == ResultStatus.PROVISIONAL
    assert result.provisional_reasons == (
        ProvisionalReason.LOW_CATEGORY_COVERAGE,
        ProvisionalReason.LOW_MERCHANT_COVERAGE,
        ProvisionalReason.SYNTHETIC_DATA,
    )
    assert result.data_quality_report.category_coverage == 0.6
    assert result.data_quality_report.merchant_coverage == 0.0


def test_requested_period_does_not_make_short_observed_span_eligible() -> None:
    transactions = tuple(build_transaction(index) for index in range(1, 11))

    result = preprocess_analysis_input(build_input(transactions))

    assert result.included_count == 10
    assert result.data_quality_report.requested_period_days == 31
    assert result.data_quality_report.observed_period_days == 1
    assert result.analysis_eligible is False
    assert result.result_status_candidate == ResultStatus.INSUFFICIENT_DATA
    assert ProvisionalReason.INSUFFICIENT_ANALYSIS_PERIOD in result.provisional_reasons


def test_no_analyzable_withdrawals_returns_insufficient_data_without_rule_or_llm_request() -> None:
    result = preprocess_analysis_input(
        build_input((build_transaction(1, transaction_type=AnalysisTransactionType.DEPOSIT),))
    )

    assert result.normalized_transactions == ()
    assert result.analysis_eligible is False
    assert result.result_status_candidate == ResultStatus.INSUFFICIENT_DATA
    assert ProvisionalReason.NO_ANALYZABLE_WITHDRAWALS in result.provisional_reasons


def test_preprocessing_rejects_invalid_contract_inputs() -> None:
    with pytest.raises(AnalysisInputError):
        preprocess_analysis_input(
            build_input(
                (build_transaction(1),),
                started_at=datetime(2026, 7, 2, tzinfo=UTC),
                ended_at=datetime(2026, 7, 1, tzinfo=UTC),
            )
        )

    with pytest.raises(AnalysisInputError):
        preprocess_analysis_input(
            build_input(
                (build_transaction(1, occurred_at=datetime(2026, 7, 1, 12, 0)),)  # noqa: DTZ001
            )
        )

    with pytest.raises(AnalysisInputError):
        preprocess_analysis_input(
            build_input(
                (build_transaction(1),),
                source_type=AnalysisSourceType.MOCK,
                is_synthetic=False,
            )
        )

    with pytest.raises(AnalysisInputError):
        preprocess_analysis_input(
            build_input(
                (
                    build_transaction(
                        1,
                        occurred_at=datetime(2026, 6, 30, 23, 59, tzinfo=UTC),
                    ),
                )
            )
        )

    with pytest.raises(AnalysisInputError):
        preprocess_analysis_input(
            build_input((build_transaction(1, source_type=AnalysisSourceType.MOCK),))
        )
