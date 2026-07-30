# Feature Catalog

## Field Guide

Each feature records:

- `metric_code`
- `status`: `AVAILABLE` or `UNAVAILABLE`
- Description
- Input fields
- Calculation
- Amount-based or count-based
- Output range
- Minimum sample
- NULL handling
- Evidence format
- MBTI axes used

Unavailable features are excluded from rule scoring. They are not converted to zero.

AN Phase 2 output schema version is `behavior-features-v1`. It consumes preprocessed `NormalizedTransaction` rows and does not depend on SQLAlchemy, FastAPI, or DB sessions.

## MVP Feature Candidates

| metric_code | Description | Input fields | Calculation | Basis | Range | Minimum sample | NULL handling | Evidence format | Axes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SHARED_EXPENSE_RATIO` | Shared spending share | `amount`, `is_shared_expense` | shared amount / marked amount | Amount | 0-1 | 1 marked transaction | Exclude NULL marker rows | Shared spending is X% of marked spending | EI, TF |
| `WEEKEND_SOCIAL_SPENDING_RATIO` | Weekend social spending share | `occurred_at`, `category_code`, `group_purpose_behavior`, `amount` | weekend social-derived spending amount / total amount | Amount | 0-1 | 1 transaction | Required date/category or derived group purpose only | Weekend social spending is X% | EI |
| `NIGHT_SPENDING_RATIO` | Night spending share | `occurred_at`, `amount` | night amount / total amount | Amount | 0-1 | 1 transaction | Required datetime only | Night spending is X% | EI, JP |
| `TRAVEL_EXPERIENCE_RATIO` | Travel and experience share | `group_purpose_type`, `behavior_group`, `amount` | travel-purpose experience amount / total amount | Amount | 0-1 | 1 transaction | Required group purpose and behavior group | Travel/experience is X% | EI, SN |
| `PRACTICAL_SPENDING_RATIO` | Practical category spending share | `behavior_group`, `amount` | practical behavior amount / total amount | Amount | 0-1 | 1 transaction | Required behavior group only | Practical spending is X% | SN, TF |
| `CATEGORY_CONCENTRATION` | Largest category concentration | `category_code`, `amount` | max category amount / total amount | Amount | 0-1 | 1 transaction | Required category code only | Top category is X% | SN |
| `CATEGORY_DIVERSITY_SCORE` | Category diversity | `category_code`, `amount` | normalized category entropy | Amount | 0-1 | 2 categories | Required category code only | Category diversity score is X | SN, JP |
| `NEW_MERCHANT_RATIO` | New merchant share | `merchant_key`, historical marker | new merchant count / merchant-countable transactions | Count | 0-1 | 2 merchant-key rows | Exclude NULL merchant rows | New merchants are X% | SN, JP |
| `REPEAT_MERCHANT_RATIO` | Repeat merchant share | `merchant_key` | repeat merchant transaction count / merchant-key rows | Count | 0-1 | 2 merchant-key rows | Exclude NULL merchant rows | Repeat merchants are X% | JP |
| `EXPERIENCE_SPENDING_RATIO` | Culture/experience spending share | `behavior_group`, `amount` | experience behavior amount / total amount | Amount | 0-1 | 1 transaction | Required behavior group only | Experience spending is X% | SN, TF |
| `SAVING_EDUCATION_RATIO` | Saving and education share | `behavior_group`, `category_code`, `amount` | savings behavior plus education category amount / total amount | Amount | 0-1 | 1 transaction | Required behavior group or education category code | Saving/education is X% | TF, JP |
| `RELATIONSHIP_SPENDING_RATIO` | Relationship spending share | `behavior_group`, `amount` | relationship behavior amount / total amount | Amount | 0-1 | 1 transaction | Required behavior group only | Relationship spending is X% | TF |
| `SHARED_EXPERIENCE_RATIO` | Shared experience share | `behavior_group`, `is_shared_expense`, `amount` | shared experience amount / marked amount | Amount | 0-1 | 1 marked transaction | Exclude NULL marker rows | Shared experience is X% | EI, TF |
| `GIFT_ANNIVERSARY_RATIO` | Gift and anniversary share | `category_code`, `behavior_group`, `amount` | gift/anniversary amount / total amount | Amount | 0-1 | 1 transaction | Required category code or behavior group | Gift/anniversary is X% | TF |
| `PLANNED_EXPENSE_RATIO` | Planned spending share | `is_planned`, `amount` | planned amount / marked amount | Amount | 0-1 | 1 marked transaction | Exclude NULL marker rows | Planned spending is X% | JP |
| `RECURRING_EXPENSE_RATIO` | Recurring spending share | `is_recurring`, `amount` | recurring amount / marked amount | Amount | 0-1 | 1 marked transaction | Exclude NULL marker rows | Recurring spending is X% | JP |
| `WEEKLY_EXPENSE_VOLATILITY` | Weekly spending volatility | `occurred_at`, `amount` | stddev weekly totals / average weekly total, capped at 1 | Amount | 0-1 | 2 weeks | Required date only | Weekly volatility is X | JP |
| `OUTLIER_RATIO` | Outlier transaction share | `amount` | outlier count / transaction count | Count | 0-1 | 5 transactions | Required amount only | Outlier transactions are X% | JP |

## AN Phase 2 Implementation Notes

- Amount ratios use amount denominators; merchant and outlier ratios use count denominators.
- `is_shared_expense`, `is_planned`, and `is_recurring` rows with `NULL` markers are excluded from each marker-specific denominator.
- Night spending is `18:00 <= local occurred_at.hour` or `local occurred_at.hour < 06:00` after converting UTC-normalized timestamps to the analysis timezone.
- Weekend spending uses Saturday and Sunday in the analysis timezone. MVP timezone is `Asia/Seoul`.
- `WEEKEND_SOCIAL_SPENDING_RATIO` uses strong social signals only: `behavior_group=RELATIONSHIP`, `category_code=GATHERING`, or `is_shared_expense=true`.
- `NEW_MERCHANT_RATIO` is unavailable until a merchant baseline before the analysis period exists.
- `REPEAT_MERCHANT_RATIO` counts visits after the first occurrence within the analysis window.
- `WEEKLY_EXPENSE_VOLATILITY` uses observation start/end context, includes calendar weeks with no spending as zero, stores raw CV in `raw_value`, and caps `normalized_score` at `1.0`.
- `OUTLIER_RATIO` uses a median/MAD threshold, with a median-based fallback when MAD is zero.
- Feature output records `behavior-policy-v1` and `category-map-v2` alongside `behavior-features-v1`.

## Preprocessing Inputs

The feature engine consumes preprocessed spending rows. AN Phase 1 is responsible for:

- filtering or separately classifying `transaction_type` values such as `DEPOSIT`, `REFUND`, `ADJUSTMENT`, and `TRANSFER`
- deriving `behavior_group` from `category_code` when the backend adapter did not provide it
- deriving broader analysis-only fields such as `group_purpose_behavior` without replacing canonical source enums
- carrying `group_purpose_type`, `analysis_period`, `source_type`, and `is_synthetic` into data-quality and uncertainty calculations
- preserving `transaction_id` and nullable `member_id` for evidence traceability without exposing internal user ids to Qwen3
