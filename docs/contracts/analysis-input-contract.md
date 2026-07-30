# Analysis Input Contract

## Purpose

Defines the structured input that backend orchestration passes into the Python analysis layer.

## Status

Implemented by AN Phase 1 for DB-independent preprocessing input. Later analysis phases may extend derived evidence contracts without passing SQLAlchemy entities into analysis functions.

## Schema Version

Target schema version: `analysis-input-v1`.

## Required Fields

- `analysisId`: analysis run id
- `groupId`: group id
- `groupPurposeType`: group purpose from the source group record
- `analysisPeriod`: inclusive analysis window
- `sourceType`: source dataset type
- `isSynthetic`: whether this run uses generated/mock data
- `members`: member id plus self-declared MBTI
- `transactions`: source-level transactions prepared for analysis preprocessing
- `schemaVersion`: `analysis-input-v1`

## Responsibility Boundary

`analysis-input-v1` is the raw analysis input boundary between backend orchestration and the Python analysis layer.

UFC uses the following ownership model:

1. FastAPI Backend reads owned source data, validates access, excludes sensitive identity fields, and builds `AnalysisInput`.
2. Analysis Preprocessing filters or classifies transaction rows by `transactionType`, `categoryCode`, source markers, and quality policy.
3. Analysis Preprocessing normalizes timestamps, category codes, and merchant keys, then computes deterministic data quality output.
4. Behavior Metric Engine consumes the preprocessed transaction set in later phases.

The Backend does not decide final feature availability, axis scores, or consumption MBTI. It also does not pass user email, username, nickname, tokens, ciphertext, secrets, or raw transaction memo text into this contract.

## Top-Level Fields

- `analysisId`: UUID string for the analysis run.
- `groupId`: UUID string for the group.
- `groupPurposeType`: canonical group purpose code: `DATE_EXPENSE`, `LIVING_EXPENSE`, `TRAVEL`, `REGULAR_MEETING`, `WEDDING_PREPARATION`, `HOBBY`, or `OTHER`.
- `analysisPeriod.startedAt`: inclusive start datetime with timezone.
- `analysisPeriod.endedAt`: inclusive end datetime with timezone.
- `sourceType`: canonical source type: `CSV`, `MOCK`, `MANUAL`, or `INTERNAL_TEST`.
- `isSynthetic`: `true` only for generated/mock/test datasets.
- `members`: members participating in the analysis.
- `transactions`: transactions in the requested analysis period.
- `schemaVersion`: `analysis-input-v1`.

`sourceType=MOCK` or `INTERNAL_TEST` requires `isSynthetic=true`. Synthetic runs must produce `PROVISIONAL` or lower-confidence result handling downstream unless blocking data sufficiency reasons make the run `INSUFFICIENT_DATA`.

## Member Fields

- `memberId`: UUID string for the group member, not the internal user id.
- `mbtiType`: validated personal MBTI type.

## Transaction Fields

- `transactionId`: source transaction id.
- `memberId`: nullable member id when a transaction can be attributed to one group member.
- `occurredAt`: transaction datetime with timezone within the inclusive `analysisPeriod`
- `amount`: positive absolute amount
- `transactionType`: `WITHDRAWAL`, `DEPOSIT`, `REFUND`, `ADJUSTMENT`, or `TRANSFER`
- `categoryCode`: normalized category code
- `behaviorGroup`: optional preclassified behavior group
- `merchantKey`: normalized merchant key, optional
- `isSharedExpense`: nullable boolean
- `isPlanned`: nullable boolean
- `isRecurring`: nullable boolean
- `sourceType`: transaction-level source marker, defaults to the top-level `sourceType` when omitted and must match the top-level value when present

`WITHDRAWAL` rows are analysis candidates. `DEPOSIT`, `REFUND`, `ADJUSTMENT`, and `TRANSFER` rows are passed so AN Phase 1 can apply a documented filtering policy, but behavior metrics must not treat them as ordinary spending.

`behaviorGroup` values use the canonical category behavior group enum: `PRACTICAL`, `EXPERIENCE`, `RELATIONSHIP`, `REGULAR`, `SAVINGS`, and `OTHER`. When omitted or `null`, AN Phase 1 preserves the missing value. Later metrics that depend on behavior-group evidence must treat those rows as unavailable rather than zero.

If Analysis needs broader derived classifications, it must create separate derived fields instead of changing the source enum. Example derived fields:

- `groupPurposeBehavior`: `SOCIAL`, `PRACTICAL`, `EXPERIENCE`, `PLANNED_EVENT`, or `OTHER`
- `savingEducationCategory`: derived from category codes when a feature needs education and savings to be considered together

MVP `groupPurposeBehavior` mapping:

| groupPurposeType | groupPurposeBehavior |
| --- | --- |
| `DATE_EXPENSE` | `SOCIAL` |
| `LIVING_EXPENSE` | `PRACTICAL` |
| `TRAVEL` | `EXPERIENCE` |
| `REGULAR_MEETING` | `SOCIAL` |
| `WEDDING_PREPARATION` | `PLANNED_EVENT` |
| `HOBBY` | `EXPERIENCE` |
| `OTHER` | `OTHER` |

Tri-state boolean meaning:

- `true`: confirmed yes
- `false`: confirmed no
- `null`: data missing or unknown

`null` must not be treated as `false`.

## Example

```json
{
  "analysisId": "uuid",
  "groupId": "uuid",
  "groupPurposeType": "TRAVEL",
  "analysisPeriod": {
    "startedAt": "2026-07-01T00:00:00+09:00",
    "endedAt": "2026-07-31T23:59:59+09:00"
  },
  "sourceType": "MOCK",
  "isSynthetic": true,
  "members": [
    {
      "memberId": "uuid",
      "mbtiType": "INTJ"
    }
  ],
  "transactions": [
    {
      "transactionId": "uuid",
      "memberId": "uuid",
      "occurredAt": "2026-07-01T12:30:00+09:00",
      "amount": 32000,
      "transactionType": "WITHDRAWAL",
      "categoryCode": "FOOD",
      "behaviorGroup": "RELATIONSHIP",
      "merchantKey": "restaurant-a",
      "isSharedExpense": true,
      "isPlanned": null,
      "isRecurring": false,
      "sourceType": "MOCK"
    }
  ],
  "schemaVersion": "analysis-input-v1"
}
```

## Data Constraints

- Real account numbers are not accepted.
- User email, username, nickname, token, ciphertext, and secrets must be excluded.
- Full transaction arrays must not be forwarded to Qwen3.
- Uploaded data must be validated before analysis.
- Synthetic data must be marked before result generation.
- Analysis period and source type must be present before data-quality scoring.
- Category-to-behavior mapping must be versioned by the analysis layer before any later metric derives behavior evidence.

## AN Phase 1 Output

`preprocess_analysis_input()` returns:

- `normalized_transactions`: non-excluded `WITHDRAWAL` rows sorted by `occurred_at` and `transaction_id`
- `included_count`
- `excluded_count`
- `requested_period_days`
- `observed_period_days`
- `data_quality_score`
- `analysis_eligible`
- `result_status_candidate`: `STANDARD`, `PROVISIONAL`, or `INSUFFICIENT_DATA`
- `provisional_reasons`
- `limitations`

`DEPOSIT`, `REFUND`, `TRANSFER`, `ADJUSTMENT`, and source-excluded rows are returned as excluded audit entries and are not included in ordinary spending denominators.

`INSUFFICIENT_DATA` means analysis must not invoke rule-engine or LLM judgment. It is used for no analyzable withdrawals, fewer than 10 normalized withdrawals, or fewer than 14 observed transaction days. `PROVISIONAL` means analysis is eligible but limited by coverage or synthetic data.
