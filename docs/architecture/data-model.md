# UFC Data Model Baseline

## Scope

This document is the target MVP table design. It does not mean every table is implemented today. New models and migrations must be introduced only in their owning phase.

## Canonical Tables

Source data:

- `users`
- `groups`
- `group_members`
- `categories`
- `transactions`

Analysis result data:

- `analysis_runs`
- `behavior_metrics`
- `consumption_mbti_results`
- `ai_reports`

## Implemented Today

Implemented by completed backend phases:

- `users`
- `groups`
- `group_members`
- `member_personalities`
- `refresh_tokens`

`member_personalities` and `refresh_tokens` are real supporting tables from BE Phase 2 and BE Phase 3. They are not counted in the final 9 table MVP analysis domain list above, but they remain part of the implemented schema and must not be removed.

## Table Design

### users

Implemented BE Phase 3 email storage:

- `email_ciphertext`
- `email_lookup_hmac`
- `email_key_version`

Documentation may use `email_lookup_hash` as the conceptual lookup field name, but the current implementation field is `email_lookup_hmac`. Plaintext `email` must not be stored or made unique. Signup duplicate checks use the normalized email lookup HMAC.

### groups

Owns group metadata and owner user id. `Group.status` currently stores readiness only: `DRAFT` or `READY_FOR_ANALYSIS`. Analysis execution status belongs to `analysis_runs`, not `groups`.

### group_members

Owns member display labels inside a group. The current implementation stores personal MBTI in `member_personalities`; future data-model cleanup may fold or retain this supporting table by explicit migration decision only.

### categories

Target owner for category code, display label, and classification metadata used by transaction normalization and analysis.

Status: not implemented.

### transactions

Target owner for normalized transaction records. Boolean behavior signals are tri-state:

- `is_shared_expense BOOLEAN NULL`
- `is_planned BOOLEAN NULL`
- `is_recurring BOOLEAN NULL`

Meaning:

- `TRUE`: confirmed yes
- `FALSE`: confirmed no
- `NULL`: no data or unknown

`NULL` must not be interpreted as `FALSE`.

Status: not implemented.

### analysis_runs

Owns analysis execution lifecycle and result quality:

- `status`: execution status
- `result_status`: output quality status
- `provisional_reasons`: structured reason list

`result_status` values:

- `STANDARD`
- `PROVISIONAL`
- `INSUFFICIENT_DATA`

Status: not implemented.

### behavior_metrics

Owns calculated feature and metric outputs. A single flat `contribution_weight` is not enough for axis contribution. Axis contribution data must be stored in a structured shape:

```json
{
  "axisContributions": [
    {
      "axis": "EI",
      "pole": "E",
      "weight": 0.30,
      "contribution": 21.4
    }
  ]
}
```

Status: not implemented on `main`. PR #6 targets this area and is tracked as Analysis / AN Phase 2.

### consumption_mbti_results

Owns rule-engine output. Data insufficiency must not force a final type, so `mbti_type` is nullable.

Axis score direction is fixed:

- EI score: higher means E
- SN score: higher means N
- TF score: higher means F
- JP score: higher means P

These directions are also recorded in `backend/app/analysis/constants.py`.

Status: not implemented.

### ai_reports

Owns Qwen3 4B report generation status and generated text. Qwen failure must not invalidate the deterministic rule-based consumption MBTI result.

Report status values:

- `COMPLETED`
- `FALLBACK_COMPLETED`
- `FAILED`

The table must track fallback usage, model name, prompt version, and validation result.

Status: not implemented.
