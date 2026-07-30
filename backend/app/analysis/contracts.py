from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

ANALYSIS_INPUT_SCHEMA_VERSION = "analysis-input-v1"


class GroupPurposeType(str, enum.Enum):
    DATE_EXPENSE = "DATE_EXPENSE"
    LIVING_EXPENSE = "LIVING_EXPENSE"
    TRAVEL = "TRAVEL"
    REGULAR_MEETING = "REGULAR_MEETING"
    WEDDING_PREPARATION = "WEDDING_PREPARATION"
    HOBBY = "HOBBY"
    OTHER = "OTHER"


class AnalysisSourceType(str, enum.Enum):
    CSV = "CSV"
    MOCK = "MOCK"
    MANUAL = "MANUAL"
    INTERNAL_TEST = "INTERNAL_TEST"


class AnalysisTransactionType(str, enum.Enum):
    WITHDRAWAL = "WITHDRAWAL"
    DEPOSIT = "DEPOSIT"
    REFUND = "REFUND"
    ADJUSTMENT = "ADJUSTMENT"
    TRANSFER = "TRANSFER"


class BehaviorGroup(str, enum.Enum):
    PRACTICAL = "PRACTICAL"
    EXPERIENCE = "EXPERIENCE"
    RELATIONSHIP = "RELATIONSHIP"
    REGULAR = "REGULAR"
    SAVINGS = "SAVINGS"
    OTHER = "OTHER"


class ResultStatus(str, enum.Enum):
    STANDARD = "STANDARD"
    PROVISIONAL = "PROVISIONAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


class ProvisionalReason(str, enum.Enum):
    INSUFFICIENT_TRANSACTION_COUNT = "INSUFFICIENT_TRANSACTION_COUNT"
    INSUFFICIENT_ANALYSIS_PERIOD = "INSUFFICIENT_ANALYSIS_PERIOD"
    LOW_CATEGORY_COVERAGE = "LOW_CATEGORY_COVERAGE"
    LOW_MERCHANT_COVERAGE = "LOW_MERCHANT_COVERAGE"
    SYNTHETIC_DATA = "SYNTHETIC_DATA"
    NO_ANALYZABLE_WITHDRAWALS = "NO_ANALYZABLE_WITHDRAWALS"


@dataclass(frozen=True)
class AnalysisPeriod:
    started_at: datetime
    ended_at: datetime


@dataclass(frozen=True)
class AnalysisMemberInput:
    member_id: str
    mbti_type: str


@dataclass(frozen=True)
class AnalysisTransactionInput:
    transaction_id: str
    group_id: str
    member_id: str | None
    occurred_at: datetime
    amount: Decimal
    category_code: str | None
    behavior_group: BehaviorGroup | None
    merchant_key: str | None
    transaction_type: AnalysisTransactionType
    is_shared_expense: bool | None
    is_planned: bool | None
    is_recurring: bool | None
    source_type: AnalysisSourceType | None = None
    is_excluded: bool = False


@dataclass(frozen=True)
class AnalysisInput:
    analysis_id: str
    group_id: str
    group_purpose_type: GroupPurposeType
    analysis_period: AnalysisPeriod
    source_type: AnalysisSourceType
    is_synthetic: bool
    members: tuple[AnalysisMemberInput, ...]
    transactions: tuple[AnalysisTransactionInput, ...]
    schema_version: str = ANALYSIS_INPUT_SCHEMA_VERSION


@dataclass(frozen=True)
class NormalizedTransaction:
    transaction_id: str
    group_id: str
    member_id: str | None
    occurred_at: datetime
    amount: Decimal
    category_code: str | None
    behavior_group: BehaviorGroup | None
    merchant_key: str | None
    transaction_type: AnalysisTransactionType
    is_shared_expense: bool | None
    is_planned: bool | None
    is_recurring: bool | None
    source_type: AnalysisSourceType


@dataclass(frozen=True)
class ExcludedTransaction:
    transaction_id: str
    reason: str
    transaction_type: AnalysisTransactionType


@dataclass(frozen=True)
class CoverageReport:
    category_coverage: float
    merchant_coverage: float


@dataclass(frozen=True)
class DataQualityReport:
    included_count: int
    excluded_count: int
    requested_period_days: int
    observed_period_days: int
    analysis_period_days: int
    category_coverage: float
    merchant_coverage: float
    data_quality_score: float
    analysis_eligible: bool
    result_status_candidate: ResultStatus
    provisional_reasons: tuple[ProvisionalReason, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class PreprocessingResult:
    normalized_transactions: tuple[NormalizedTransaction, ...]
    excluded_transactions: tuple[ExcludedTransaction, ...]
    included_count: int
    excluded_count: int
    data_quality_score: float
    analysis_eligible: bool
    result_status_candidate: ResultStatus
    provisional_reasons: tuple[ProvisionalReason, ...]
    limitations: tuple[str, ...]
    data_quality_report: DataQualityReport
