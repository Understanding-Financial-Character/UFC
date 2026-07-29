# Feature Catalog

## Field Guide

Each feature records:

- `metric_code`
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

## MVP Feature Candidates

| metric_code | Description | Input fields | Calculation | Basis | Range | Minimum sample | NULL handling | Evidence format | Axes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `SHARED_EXPENSE_RATIO` | Shared spending share | `amount`, `is_shared_expense` | shared amount / marked amount | Amount | 0-1 | 1 marked transaction | Exclude NULL marker rows | Shared spending is X% of marked spending | EI, TF |
| `WEEKEND_SOCIAL_SPENDING_RATIO` | Weekend social spending share | `occurred_at`, `category`, `amount` | weekend social category amount / total amount | Amount | 0-1 | 1 transaction | Required date/category only | Weekend social spending is X% | EI |
| `NIGHT_SPENDING_RATIO` | Night spending share | `occurred_at`, `amount` | night amount / total amount | Amount | 0-1 | 1 transaction | Required datetime only | Night spending is X% | EI, JP |
| `TRAVEL_EXPERIENCE_RATIO` | Travel and experience share | `category`, `amount` | travel/experience amount / total amount | Amount | 0-1 | 1 transaction | Required category only | Travel/experience is X% | EI, SN |
| `PRACTICAL_SPENDING_RATIO` | Practical category spending share | `category`, `amount` | practical category amount / total amount | Amount | 0-1 | 1 transaction | Required category only | Practical spending is X% | SN, TF |
| `CATEGORY_CONCENTRATION` | Largest category concentration | `category`, `amount` | max category amount / total amount | Amount | 0-1 | 1 transaction | Required category only | Top category is X% | SN |
| `CATEGORY_DIVERSITY_SCORE` | Category diversity | `category`, `amount` | normalized category entropy | Amount | 0-1 | 2 categories | Required category only | Category diversity score is X | SN, JP |
| `NEW_MERCHANT_RATIO` | New merchant share | `merchant_key`, historical marker | new merchant count / merchant-countable transactions | Count | 0-1 | 2 merchant-key rows | Exclude NULL merchant rows | New merchants are X% | SN, JP |
| `REPEAT_MERCHANT_RATIO` | Repeat merchant share | `merchant_key` | repeat merchant transaction count / merchant-key rows | Count | 0-1 | 2 merchant-key rows | Exclude NULL merchant rows | Repeat merchants are X% | JP |
| `EXPERIENCE_SPENDING_RATIO` | Culture/experience spending share | `category`, `amount` | experience amount / total amount | Amount | 0-1 | 1 transaction | Required category only | Experience spending is X% | SN, TF |
| `SAVING_EDUCATION_RATIO` | Saving and education share | `category`, `amount` | saving/education amount / total amount | Amount | 0-1 | 1 transaction | Required category only | Saving/education is X% | TF, JP |
| `RELATIONSHIP_SPENDING_RATIO` | Relationship spending share | `category`, `amount` | relationship category amount / total amount | Amount | 0-1 | 1 transaction | Required category only | Relationship spending is X% | TF |
| `SHARED_EXPERIENCE_RATIO` | Shared experience share | `category`, `is_shared_expense`, `amount` | shared experience amount / marked amount | Amount | 0-1 | 1 marked transaction | Exclude NULL marker rows | Shared experience is X% | EI, TF |
| `GIFT_ANNIVERSARY_RATIO` | Gift and anniversary share | `category`, `amount` | gift/anniversary amount / total amount | Amount | 0-1 | 1 transaction | Required category only | Gift/anniversary is X% | TF |
| `PLANNED_EXPENSE_RATIO` | Planned spending share | `is_planned`, `amount` | planned amount / marked amount | Amount | 0-1 | 1 marked transaction | Exclude NULL marker rows | Planned spending is X% | JP |
| `RECURRING_EXPENSE_RATIO` | Recurring spending share | `is_recurring`, `amount` | recurring amount / marked amount | Amount | 0-1 | 1 marked transaction | Exclude NULL marker rows | Recurring spending is X% | JP |
| `WEEKLY_EXPENSE_VOLATILITY` | Weekly spending volatility | `occurred_at`, `amount` | stddev weekly totals / average weekly total, capped at 1 | Amount | 0-1 | 2 weeks | Required date only | Weekly volatility is X | JP |
| `OUTLIER_RATIO` | Outlier transaction share | `amount` | outlier count / transaction count | Count | 0-1 | 5 transactions | Required amount only | Outlier transactions are X% | JP |
