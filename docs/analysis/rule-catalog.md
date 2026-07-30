# Consumption MBTI Rule Catalog

## Axis Definitions

| Axis | Low pole | High pole | Meaning |
| --- | --- | --- | --- |
| EI | I | E | 생활 and repeat spending vs shared and external activity spending |
| SN | S | N | concrete, practical, concentrated spending vs diverse, culture, experience spending |
| TF | T | F | purpose and efficiency spending vs relationship, anniversary, shared experience spending |
| JP | J | P | planned, recurring, stable spending vs spontaneous, new, volatile spending |

Score direction:

- EI score: higher means E
- SN score: higher means N
- TF score: higher means F
- JP score: higher means P

The same direction contract is recorded in `backend/app/analysis/constants.py`.

## Rule Engine Principles

- Use only calculable features.
- Exclude impossible MVP signals such as living-area distance, restaurant quality, discounts, and payback.
- Treat unavailable features as unavailable, not as zero.
- Renormalize remaining weights over available features.
- Calculate coverage for each axis.
- Defer axis judgment when coverage is too low.
- Produce final MBTI only when all four axes are available.
- Mark mock-data results as `PROVISIONAL`.

AN Phase 3 implements `consumption-mbti-v1` in `backend/app/analysis/rules/consumption-mbti-v1.yaml`.

Configured thresholds:

- `axis coverage >= 0.70`: standard axis evidence
- `0.50 <= axis coverage < 0.70`: axis can be decided, but result is provisional
- `axis coverage < 0.50`: axis decision is deferred
- `axis margin < 5.0`: `LOW_AXIS_SCORE_MARGIN`

Unavailable features are removed from the axis denominator and the remaining weights are renormalized.

## Implemented Axis Inputs

EI high means E:

- E signals: `SHARED_EXPENSE_RATIO`, `WEEKEND_SOCIAL_SPENDING_RATIO`, `NIGHT_SPENDING_RATIO`, `TRAVEL_EXPERIENCE_RATIO`
- I signals: `PRACTICAL_SPENDING_RATIO`

SN high means N:

- N signals: `CATEGORY_DIVERSITY_SCORE`, `EXPERIENCE_SPENDING_RATIO`, `TRAVEL_EXPERIENCE_RATIO`
- S signals: `CATEGORY_CONCENTRATION`, `PRACTICAL_SPENDING_RATIO`

TF high means F:

- F signals: `RELATIONSHIP_SPENDING_RATIO`, `SHARED_EXPERIENCE_RATIO`, `GIFT_ANNIVERSARY_RATIO`, `SHARED_EXPENSE_RATIO`
- T signals: `SAVING_EDUCATION_RATIO`

JP high means P:

- P signals: `REPEAT_MERCHANT_RATIO`, `WEEKLY_EXPENSE_VOLATILITY`, `OUTLIER_RATIO`
- J signals: `PLANNED_EXPENSE_RATIO`, `RECURRING_EXPENSE_RATIO`

Unavailable MVP signals such as living-area distance, restaurant quality, discounts, payback, and true new-merchant status without historical baseline are excluded from the rule version.

## Output Rules

`consumption_mbti_results.mbti_type` is nullable. When data is insufficient, preserve axis scores and limitations instead of forcing a type.

`mbti_type` is generated only when EI, SN, TF, and JP are all decided. If any axis is deferred, `result_status=INSUFFICIENT_DATA`.

## Versioning

Rule sets must have a version. Future changes to feature weights, thresholds, or pole mapping require a new rule version and verification against golden scenarios.
