from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

ANALYSIS_INPUT_SCHEMA_VERSION = "analysis-input-v1"
BEHAVIOR_FEATURE_SCHEMA_VERSION = "behavior-features-v1"
BEHAVIOR_FEATURE_POLICY_VERSION = "behavior-policy-v1"
CATEGORY_MAPPING_VERSION = "category-map-v2"
CONSUMPTION_MBTI_SCHEMA_VERSION = "consumption-mbti-v1"


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


SYNTHETIC_SOURCE_TYPES = frozenset(
    {
        AnalysisSourceType.MOCK,
        AnalysisSourceType.INTERNAL_TEST,
    }
)


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


class BehaviorFeatureCode(str, enum.Enum):
    SHARED_EXPENSE_RATIO = "SHARED_EXPENSE_RATIO"
    WEEKEND_SOCIAL_SPENDING_RATIO = "WEEKEND_SOCIAL_SPENDING_RATIO"
    NIGHT_SPENDING_RATIO = "NIGHT_SPENDING_RATIO"
    TRAVEL_EXPERIENCE_RATIO = "TRAVEL_EXPERIENCE_RATIO"
    PRACTICAL_SPENDING_RATIO = "PRACTICAL_SPENDING_RATIO"
    CATEGORY_CONCENTRATION = "CATEGORY_CONCENTRATION"
    CATEGORY_DIVERSITY_SCORE = "CATEGORY_DIVERSITY_SCORE"
    NEW_MERCHANT_RATIO = "NEW_MERCHANT_RATIO"
    REPEAT_MERCHANT_RATIO = "REPEAT_MERCHANT_RATIO"
    EXPERIENCE_SPENDING_RATIO = "EXPERIENCE_SPENDING_RATIO"
    SAVING_EDUCATION_RATIO = "SAVING_EDUCATION_RATIO"
    RELATIONSHIP_SPENDING_RATIO = "RELATIONSHIP_SPENDING_RATIO"
    SHARED_EXPERIENCE_RATIO = "SHARED_EXPERIENCE_RATIO"
    GIFT_ANNIVERSARY_RATIO = "GIFT_ANNIVERSARY_RATIO"
    PLANNED_EXPENSE_RATIO = "PLANNED_EXPENSE_RATIO"
    RECURRING_EXPENSE_RATIO = "RECURRING_EXPENSE_RATIO"
    WEEKLY_EXPENSE_VOLATILITY = "WEEKLY_EXPENSE_VOLATILITY"
    OUTLIER_RATIO = "OUTLIER_RATIO"


class BehaviorFeatureUnit(str, enum.Enum):
    AMOUNT_RATIO = "AMOUNT_RATIO"
    COUNT_RATIO = "COUNT_RATIO"
    SCORE = "SCORE"


class BehaviorFeatureStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


class RuleDirection(str, enum.Enum):
    HIGH = "HIGH"
    LOW = "LOW"


class ConsumptionAxis(str, enum.Enum):
    EI = "EI"
    SN = "SN"
    TF = "TF"
    JP = "JP"


class AxisDecisionStatus(str, enum.Enum):
    DECIDED = "DECIDED"
    DEFERRED = "DEFERRED"


class ConfidenceLevel(str, enum.Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


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


@dataclass(frozen=True)
class BehaviorFeatureResult:
    feature_code: BehaviorFeatureCode
    status: BehaviorFeatureStatus
    raw_value: float | None
    normalized_score: float | None
    unit: BehaviorFeatureUnit
    sample_count: int
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class BehaviorMetricsInput:
    transactions: tuple[NormalizedTransaction, ...]
    observation_started_at: datetime
    observation_ended_at: datetime
    timezone: str = "Asia/Seoul"
    source_type: AnalysisSourceType = AnalysisSourceType.CSV


@dataclass(frozen=True)
class BehaviorMetricsResult:
    schema_version: str
    policy_version: str
    category_mapping_version: str
    analysis_timezone: str
    source_type: AnalysisSourceType
    is_synthetic: bool
    features: tuple[BehaviorFeatureResult, ...]


@dataclass(frozen=True)
class RuleEngineInput:
    behavior_metrics: BehaviorMetricsResult


@dataclass(frozen=True)
class AxisContribution:
    axis: ConsumptionAxis
    feature_code: BehaviorFeatureCode
    direction: RuleDirection
    weight: float
    normalized_weight: float
    feature_score: float
    contribution_score: float
    contribution: float
    high_pole_support: float
    low_pole_support: float
    signed_contribution: float
    decided_pole_contribution: float
    evidence: tuple[str, ...]


@dataclass(frozen=True)
class AxisScoreResult:
    axis: ConsumptionAxis
    score: float | None
    coverage: float
    margin: float | None
    low_pole: str
    high_pole: str
    decided_pole: str | None
    status: AxisDecisionStatus
    provisional_reasons: tuple[str, ...]
    contributions: tuple[AxisContribution, ...]


@dataclass(frozen=True)
class Confidence:
    level: ConfidenceLevel
    score: float


@dataclass(frozen=True)
class ConsumptionMbtiResult:
    schema_version: str
    rule_version: str
    axis_scores: dict[str, float | None]
    axis_coverage: dict[str, float]
    axis_margins: dict[str, float | None]
    confidence: Confidence
    mbti_type: str | None
    primary_evidence: tuple[AxisContribution, ...]
    result_status: ResultStatus
    provisional_reasons: tuple[str, ...]
    axis_results: tuple[AxisScoreResult, ...]
