# Data Quality Policy

## Goals

Preprocessing must make analysis input explicit and auditable before behavior metrics or rule-based MBTI are calculated.

## Required Checks

- Transaction amount is positive for spending records.
- Transaction timestamp is present and parseable.
- `transaction_type` is present and supported by preprocessing policy.
- `category_code` is present for spending rows that need category or behavior-group features.
- `behavior_group` is present or derivable from versioned `category_code` mapping before behavior-group metrics run.
- `group_purpose_type` uses the canonical group enum and is not replaced by derived analysis labels.
- `analysis_period` is present and includes the requested observation window.
- `source_type` and `is_synthetic` are present and internally consistent.
- Boolean behavior signals keep tri-state semantics.
- Duplicate imported rows are handled by the owning transaction input phase.
- Synthetic data is marked before analysis.

## Tri-State Boolean Policy

For `is_shared_expense`, `is_planned`, and `is_recurring`:

- `TRUE`: confirmed yes
- `FALSE`: confirmed no
- `NULL`: no data or unknown

`NULL` is not equivalent to `FALSE`. Metrics using these fields exclude NULL rows from the denominator.

## Data Sufficiency

Sparse, short-period, missing-category, missing-merchant, or synthetic data may still produce partial evidence. It must be reflected in `result_status`, `provisional_reasons`, coverage, and limitations.

AN Phase 1 uses these deterministic thresholds:

- Minimum analyzable withdrawals: `10`
- Minimum analysis period: `14` inclusive days
- Minimum category coverage: `0.70`
- Minimum merchant coverage: `0.50`

Coverage is calculated over normalized, non-excluded `WITHDRAWAL` rows only.

`analysis_eligible` is true when at least 10 normalized withdrawals exist across an observed transaction span of at least 14 days. The observed span is calculated from normalized transaction timestamps, not only from the requested analysis window.

Blocking reasons produce `result_status=INSUFFICIENT_DATA` and must prevent rule-engine or LLM execution:

- `NO_ANALYZABLE_WITHDRAWALS`
- `INSUFFICIENT_TRANSACTION_COUNT`
- `INSUFFICIENT_ANALYSIS_PERIOD`

Low category coverage, low merchant coverage, or synthetic data produce `result_status=PROVISIONAL` only when no blocking reason exists.

## Transaction Type Policy

`WITHDRAWAL` rows are the default candidates for spending behavior metrics.

`DEPOSIT`, `REFUND`, `ADJUSTMENT`, and `TRANSFER` rows must be retained through preprocessing long enough to support auditability and quality decisions, but they are excluded from ordinary spending denominators unless a later metric explicitly opts into them.

AN Phase 1 exclusion reasons:

| transaction_type | reason |
| --- | --- |
| `DEPOSIT` | `DEPOSIT_EXCLUDED_FROM_SPENDING_ANALYSIS` |
| `REFUND` | `REFUND_EXCLUDED_FROM_SPENDING_ANALYSIS` |
| `TRANSFER` | `TRANSFER_EXCLUDED_FROM_SPENDING_ANALYSIS` |
| `ADJUSTMENT` | `ADJUSTMENT_EXCLUDED_FROM_SPENDING_ANALYSIS` |
| source `is_excluded=true` | `SOURCE_TRANSACTION_EXCLUDED` |

`WITHDRAWAL` rows with source `is_excluded=false` remain analysis candidates.

## Canonical Enum Policy

Analysis input preserves DB canonical enum values:

- `group_purpose_type`: `DATE_EXPENSE`, `LIVING_EXPENSE`, `TRAVEL`, `REGULAR_MEETING`, `WEDDING_PREPARATION`, `HOBBY`, `OTHER`
- `behavior_group`: `PRACTICAL`, `EXPERIENCE`, `RELATIONSHIP`, `REGULAR`, `SAVINGS`, `OTHER`
- `source_type`: `CSV`, `MOCK`, `MANUAL`, `INTERNAL_TEST`

Analysis-only groupings must be derived into separate fields and versioned by preprocessing configuration.

## Normalization

- Datetimes must include timezone information and are normalized to UTC.
- Transactions must fall within the inclusive `analysis_period`.
- Transaction-level `source_type`, when present, must match the top-level `source_type`; one analysis run uses one source type.
- `category_code` is stripped and uppercased.
- `merchant_key` is Unicode-normalized, lowercased, separator-collapsed, and may remain `null` when unavailable.
- `is_shared_expense`, `is_planned`, and `is_recurring` remain tri-state through preprocessing.

The quality report distinguishes:

- `requested_period_days`: inclusive days in the requested analysis window
- `observed_period_days`: inclusive days between the first and last normalized withdrawal
