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
- `members`: member id plus self-declared MBTI
- `transactions`: normalized transactions
- `schemaVersion`: `analysis-input-v1`

## Transaction Fields

- `occurredAt`: transaction datetime
- `amount`: positive spending amount
- `category`: normalized category code
- `merchantKey`: normalized merchant key, optional
- `isSharedExpense`: nullable boolean
- `isPlanned`: nullable boolean
- `isRecurring`: nullable boolean

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
  "members": [
    {
      "memberId": "uuid",
      "mbtiType": "INTJ"
    }
  ],
  "transactions": [
    {
      "occurredAt": "2026-07-01T12:30:00",
      "amount": 32000,
      "category": "FOOD",
      "merchantKey": "restaurant-a",
      "isSharedExpense": true,
      "isPlanned": null,
      "isRecurring": false
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
