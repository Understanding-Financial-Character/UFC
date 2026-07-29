# Data Quality Policy

## Goals

Preprocessing must make analysis input explicit and auditable before behavior metrics or rule-based MBTI are calculated.

## Required Checks

- Transaction amount is positive for spending records.
- Transaction timestamp is present and parseable.
- Category is present after normalization.
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
