# Analysis Input Contract

## Purpose

Defines the structured input that backend orchestration passes into the Python analysis layer.

## Status

Target contract. Concrete implementation is owned by AN Phase 1 and AN Phase 2. PR #6 is tracked separately and is not merged into `main`.

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
3. Analysis Preprocessing derives `behaviorGroup` from `categoryCode` using a versioned category-behavior mapping when `behaviorGroup` is not provided.
4. Behavior Metric Engine consumes the preprocessed transaction set.

The Backend does not decide final feature availability, axis scores, or consumption MBTI. It also does not pass user email, username, nickname, tokens, ciphertext, secrets, or raw transaction memo text into this contract.

## Top-Level Fields

- `analysisId`: UUID string for the analysis run.
- `groupId`: UUID string for the group.
- `groupPurposeType`: group purpose code, such as `GENERAL`, `TRAVEL`, `LIVING`, `EVENT`, or `OTHER`.
- `analysisPeriod.startedAt`: inclusive start datetime.
- `analysisPeriod.endedAt`: inclusive end datetime.
- `sourceType`: `MANUAL_UPLOAD`, `MOCK_GENERATED`, `SEED`, or `INTERNAL_TEST`.
- `isSynthetic`: `true` only for generated/mock/test datasets.
- `members`: members participating in the analysis.
- `transactions`: transactions in the requested analysis period.
- `schemaVersion`: `analysis-input-v1`.

`sourceType=MOCK_GENERATED` or `INTERNAL_TEST` requires `isSynthetic=true`. Synthetic runs must produce `PROVISIONAL` or lower-confidence result handling downstream.

## Member Fields

- `memberId`: UUID string for the group member, not the internal user id.
- `mbtiType`: validated personal MBTI type.

## Transaction Fields

- `transactionId`: source transaction id.
- `memberId`: nullable member id when a transaction can be attributed to one group member.
- `occurredAt`: transaction datetime
- `amount`: positive absolute amount
- `transactionType`: `WITHDRAWAL`, `DEPOSIT`, `REFUND`, `ADJUSTMENT`, or `TRANSFER`
- `categoryCode`: normalized category code
- `behaviorGroup`: optional preclassified behavior group
- `merchantKey`: normalized merchant key, optional
- `isSharedExpense`: nullable boolean
- `isPlanned`: nullable boolean
- `isRecurring`: nullable boolean
- `sourceType`: transaction-level source marker, defaults to the top-level `sourceType` when omitted

`WITHDRAWAL` rows are analysis candidates. `DEPOSIT`, `REFUND`, `ADJUSTMENT`, and `TRANSFER` rows are passed so AN Phase 1 can apply a documented filtering policy, but behavior metrics must not treat them as ordinary spending.

`behaviorGroup` values are owned by the analysis feature catalog. Allowed MVP groups include `PRACTICAL`, `EXPERIENCE`, `RELATIONSHIP`, `SAVING_EDUCATION`, `SOCIAL`, and `OTHER`. When omitted or `null`, Analysis Preprocessing derives it from `categoryCode`; when derivation is impossible, dependent features become unavailable rather than zero.

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
    "startedAt": "2026-07-01T00:00:00",
    "endedAt": "2026-07-31T23:59:59"
  },
  "sourceType": "MOCK_GENERATED",
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
      "occurredAt": "2026-07-01T12:30:00",
      "amount": 32000,
      "transactionType": "WITHDRAWAL",
      "categoryCode": "FOOD",
      "behaviorGroup": "RELATIONSHIP",
      "merchantKey": "restaurant-a",
      "isSharedExpense": true,
      "isPlanned": null,
      "isRecurring": false,
      "sourceType": "MOCK_GENERATED"
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
- Category-to-behavior mapping must be versioned by the analysis layer.
