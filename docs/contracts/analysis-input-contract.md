# Analysis Input Contract

## Purpose

Defines the structured input that deterministic analysis and AI report generation may consume.

## Schema Version

Current implemented schema version: `analysis-input-v1`.

## Required Fields

- `schemaVersion`: string, required, current value `analysis-input-v1`
- `analysisId`: internal analysis identifier, required
- `groupId`: internal group identifier, required
- `members`: member identifiers and self-declared MBTI values, required, minimum 1
- `transactions`: normalized transaction records, required, may be empty

## Transaction Fields

- `occurredAt`: transaction date and time, required
- `amount`: positive spending amount, required
- `category`: category enum, required
- `merchantKey`: normalized merchant key, optional
- `isRecurring`: recurring marker, optional
- `isPlanned`: planned spending marker, optional

Implemented category values:

- `FOOD`
- `CAFE`
- `TRANSPORT`
- `SHOPPING`
- `GROCERY`
- `CULTURE`
- `TRAVEL`
- `HEALTH`
- `EDUCATION`
- `HOUSING`
- `FINANCE`
- `OTHER`

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
      "isRecurring": false,
      "isPlanned": true
    }
  ],
  "schemaVersion": "analysis-input-v1"
}
```

## Data Constraints

- Real account numbers are not accepted.
- Raw personal identifiers should be excluded unless needed for MVP behavior.
- Synthetic data must be marked as synthetic.
- Uploaded data must be validated before analysis.
- `memberId` values must be unique within one analysis input.
- Missing `merchantKey`, `isRecurring`, or `isPlanned` values are not inferred from UI needs.

## Status

AI Phase 1 implements this contract as Pydantic schemas under `backend/app/analysis`.
