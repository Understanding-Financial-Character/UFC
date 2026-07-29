# API Contracts

## Purpose

This document defines how UFC manages API contracts during MVP development.

Contracts are documented before implementation and updated in the same PR as any API behavior change.

## Contract Ownership

- Backend owns request validation, response shape, status codes, and persistence semantics.
- Frontend consumes documented contracts and should not depend on undocumented response fields.
- AI analysis consumes backend-defined analysis input and output contracts.

## Change Rules

- Additive optional fields are allowed when documented.
- Required field changes require contract update, implementation update, and verification evidence.
- Removing or renaming fields requires an ADR or explicit phase decision note.
- Error responses must follow `docs/contracts/error-contract.md`.
- Analysis inputs and outputs must follow the dedicated analysis contract documents.

## Initial MVP API Areas

- Groups and members
- Member MBTI registration
- Transaction upload or mock scenario selection
- Analysis request and status
- Spending MBTI result
- AI report retrieval
- Share card metadata

## Contract Version

Current draft contract version: `1.0`.

All versioned response examples include `schema_version`.

## First Vertical Slice Endpoints

The first backend implementation slice must finalize and implement these contracts before frontend or AI integration depends on them.

## Phase 2 User and Group Authorization

Until full login is implemented, BE Phase 2 uses:

- User creation: `POST /api/v1/users`
- Header-identified MVP group endpoints: required `X-UFC-User-Id` header
- Ownership rule: only the group owner may read or mutate a group and its members
- Inaccessible group response: `404 NOT_FOUND`

This temporary identity approach is recorded in `docs/decisions/ADR-0003-phase-2-user-identity.md`.

## Backend Foundation Endpoints

These endpoints are implemented before domain APIs so Docker, database, and OpenAPI readiness can be verified.

### Health Check

- Method and path: `GET /health`
- Sync or async: Sync
- Idempotency: Safe read
- Resource owner: Public infrastructure check
- Success status: `200 OK`
- Error codes: `INTERNAL_ERROR`

Response:

```json
{
  "status": "ok"
}
```

### Readiness Check

- Method and path: `GET /ready`
- Sync or async: Sync
- Idempotency: Safe read
- Resource owner: Public infrastructure check
- Success status: `200 OK`
- Error codes: `DATABASE_UNAVAILABLE`, `INTERNAL_ERROR`

Response:

```json
{
  "status": "ready"
}
```

### API Metadata

- Method and path: `GET /api/v1/meta`
- Sync or async: Sync
- Idempotency: Safe read
- Resource owner: Public API metadata
- Success status: `200 OK`
- Error codes: `INTERNAL_ERROR`

Response:

```json
{
  "name": "UFC API",
  "version": "0.1.0",
  "environment": "local"
}
```

### OpenAPI Schema

- Method and path: `GET /api/v1/openapi.json`
- Sync or async: Sync
- Idempotency: Safe read
- Resource owner: Public API metadata during MVP development
- Success status: `200 OK`
- Error codes: `INTERNAL_ERROR`

### Create User

- Method and path: `POST /users`
- Sync or async: Sync
- Idempotency: Not required for MVP
- Resource owner: Public MVP signup
- Success status: `201 Created`
- Error codes: `VALIDATION_ERROR`, `INTERNAL_ERROR`

Request:

```json
{
  "display_name": "민지"
}
```

Response:

```json
{
  "schema_version": "1.0",
  "user_id": "uuid",
  "display_name": "민지",
  "created_at": "2026-07-29T00:00:00Z"
}
```

Field rules:

- `display_name`: string, required, 1-80 characters after trimming whitespace; blank values are rejected

### Create Group

- Method and path: `POST /groups`
- Sync or async: Sync
- Idempotency: Not required for MVP
- Resource owner: Header-identified MVP user creating the group
- Success status: `201 Created`
- Error codes: `VALIDATION_ERROR`, `NOT_FOUND`, `INTERNAL_ERROR`
- Required headers: `X-UFC-User-Id`

Request:

```json
{
  "name": "여행 모임",
  "relationship_type": "FRIENDS"
}
```

Response:

```json
{
  "schema_version": "1.0",
  "group_id": "uuid",
  "name": "여행 모임",
  "relationship_type": "FRIENDS",
  "status": "DRAFT",
  "member_count": 0,
  "can_analyze": false,
  "created_at": "2026-07-29T00:00:00Z",
  "members": []
}
```

Field rules:

- `name`: string, required, 1-80 characters after trimming whitespace; blank values are rejected
- `relationship_type`: enum, required, one of `COUPLE`, `FRIENDS`, `FAMILY`, `OTHER`
- `member_count`: integer, required, range 0-4
- `created_at`: ISO 8601 datetime, required
- `status`: enum, required, one of `DRAFT`, `READY_FOR_ANALYSIS`
- `can_analyze`: boolean, required; true when the group has 2-4 members and every member has MBTI
- Analysis execution status is not stored on `Group`; later analysis phases must use a separate analysis run status.

### List Groups

- Method and path: `GET /groups`
- Sync or async: Sync
- Idempotency: Safe read
- Resource owner: Header-identified MVP user
- Success status: `200 OK`
- Error codes: `VALIDATION_ERROR`, `INTERNAL_ERROR`
- Required headers: `X-UFC-User-Id`

Response: array of Create Group response objects.

### Get Group

- Method and path: `GET /groups/{groupId}`
- Sync or async: Sync
- Idempotency: Safe read
- Resource owner: Group owner
- Success status: `200 OK`
- Error codes: `VALIDATION_ERROR`, `NOT_FOUND`, `INTERNAL_ERROR`
- Required headers: `X-UFC-User-Id`

Response: Create Group response object, including `members`.

### Update Group

- Method and path: `PATCH /groups/{groupId}`
- Sync or async: Sync
- Idempotency: Not required for MVP
- Resource owner: Group owner
- Success status: `200 OK`
- Error codes: `VALIDATION_ERROR`, `NOT_FOUND`, `INTERNAL_ERROR`
- Required headers: `X-UFC-User-Id`

Request fields are optional individually, but at least one field must be provided:

```json
{
  "name": "가족 여행",
  "relationship_type": "FAMILY"
}
```

Response: Create Group response object.

### Add Group Member

- Method and path: `POST /groups/{groupId}/members`
- Sync or async: Sync
- Idempotency: Not required for MVP
- Resource owner: Group owner or authorized group member
- Success status: `201 Created`
- Error codes: `VALIDATION_ERROR`, `NOT_FOUND`, `CONFLICT`, `INTERNAL_ERROR`
- Required headers: `X-UFC-User-Id`

Request:

```json
{
  "display_name": "민지",
  "mbti": "ENFP"
}
```

Response:

```json
{
  "schema_version": "1.0",
  "group_id": "uuid",
  "member_id": "uuid",
  "display_name": "민지",
  "mbti": "ENFP",
  "created_at": "2026-07-29T00:00:00Z"
}
```

Field rules:

- `groupId`: UUID path parameter, required
- `display_name`: string, required, 1-40 characters
- `mbti`: enum, required, one of the 16 MBTI types
- Group member count must not exceed 4.
- Group status becomes `READY_FOR_ANALYSIS` when member count is 2-4 and every member has MBTI.
- Group status returns to `DRAFT` when member count is below 2.
- `display_name` is trimmed before validation and storage; blank values are rejected.
- Duplicate `display_name` values are rejected within the same group after normalization.

### Update Group Member

- Method and path: `PATCH /groups/{groupId}/members/{memberId}`
- Sync or async: Sync
- Idempotency: Not required for MVP
- Resource owner: Group owner
- Success status: `200 OK`
- Error codes: `VALIDATION_ERROR`, `NOT_FOUND`, `CONFLICT`, `INTERNAL_ERROR`
- Required headers: `X-UFC-User-Id`

Request fields are optional individually, but at least one field must be provided:

```json
{
  "display_name": "민지2",
  "mbti": "ENTP"
}
```

Response: Add Group Member response object.

### Delete Group Member

- Method and path: `DELETE /groups/{groupId}/members/{memberId}`
- Sync or async: Sync
- Idempotency: Not required for MVP
- Resource owner: Group owner
- Success status: `204 No Content`
- Error codes: `VALIDATION_ERROR`, `NOT_FOUND`, `INTERNAL_ERROR`
- Required headers: `X-UFC-User-Id`

### Upload Transactions

- Method and path: `POST /groups/{groupId}/transactions:upload`
- Sync or async: Sync for MVP validation and accepted record persistence
- Idempotency: Recommended via client-supplied upload checksum in backend phase
- Resource owner: Authorized group member
- Success status: `201 Created`
- Error codes: `VALIDATION_ERROR`, `NOT_FOUND`, `CONFLICT`, `INTERNAL_ERROR`

Request:

```json
{
  "schema_version": "1.0",
  "source_type": "MOCK_SCENARIO",
  "scenario_id": "friends-travel-001",
  "transactions": []
}
```

Response:

```json
{
  "schema_version": "1.0",
  "group_id": "uuid",
  "upload_id": "uuid",
  "source_type": "MOCK_SCENARIO",
  "accepted_count": 42,
  "rejected_count": 0,
  "status": "COMPLETED"
}
```

Field rules:

- `source_type`: enum, required, one of `MOCK_SCENARIO`, `CSV_UPLOAD`, `MANUAL_ENTRY`
- `scenario_id`: string, optional, required when `source_type` is `MOCK_SCENARIO`
- `transactions`: array, optional for mock scenario, required for upload or manual entry
- `status`: enum, required, one of `COMPLETED`, `PARTIALLY_COMPLETED`, `FAILED`

### Create Analysis

- Method and path: `POST /groups/{groupId}/analyses`
- Sync or async: Async result creation
- Idempotency: Recommended for repeated requests with the same group and period
- Resource owner: Authorized group member
- Success status: `202 Accepted`
- Error codes: `VALIDATION_ERROR`, `NOT_FOUND`, `CONFLICT`, `INTERNAL_ERROR`

Request:

```json
{
  "schema_version": "1.0",
  "period_start": "2026-05-01",
  "period_end": "2026-07-29"
}
```

Response:

```json
{
  "schema_version": "1.0",
  "analysis_id": "uuid",
  "group_id": "uuid",
  "status": "PENDING",
  "created_at": "2026-07-29T00:00:00Z"
}
```

Field rules:

- `period_start`: ISO 8601 date, required
- `period_end`: ISO 8601 date, required, must be greater than or equal to `period_start`
- `status`: enum, required, one of `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`

### Get Analysis

- Method and path: `GET /analyses/{analysisId}`
- Sync or async: Sync lookup
- Idempotency: Safe read
- Resource owner: Authorized member of the analysis group
- Success status: `200 OK`
- Error codes: `NOT_FOUND`, `INTERNAL_ERROR`

Response:

```json
{
  "schema_version": "1.0",
  "analysis_id": "uuid",
  "group_id": "uuid",
  "status": "COMPLETED",
  "result_status": "PROVISIONAL",
  "provisional_reasons": ["INSUFFICIENT_TRANSACTION_COUNT"],
  "confidence": {
    "level": "LOW",
    "score": 0.42
  },
  "spending_mbti": "ENFP",
  "limitations": []
}
```

This response must follow `docs/contracts/analysis-output-contract.md`.

`PENDING`, `RUNNING`, `COMPLETED`, and `FAILED` analysis states are returned as `200 OK` lookup responses. Limited but usable data is not an API error; it is represented as `result_status: "PROVISIONAL"` with `provisional_reasons`.

### Get AI Report

- Method and path: `GET /analyses/{analysisId}/report`
- Sync or async: Sync lookup after generation
- Idempotency: Safe read
- Resource owner: Authorized member of the analysis group
- Success status: `200 OK`
- Error codes: `NOT_FOUND`, `AI_REPORT_UNAVAILABLE`, `INTERNAL_ERROR`

Response:

```json
{
  "schema_version": "1.0",
  "analysis_id": "uuid",
  "report_id": "uuid",
  "status": "COMPLETED",
  "summary": "최근 3개월 동안 이 모임은 새로운 장소와 공동 경험 소비가 두드러졌습니다.",
  "sections": [
    {
      "title": "주요 특징",
      "body": "주말 외식과 여행 카테고리 비중이 높았습니다."
    }
  ],
  "limitations": ["거래 건수가 적어 잠정 결과입니다."]
}
```

Field rules:

- `status`: enum, required, one of `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`
- `summary`: string, required when `status` is `COMPLETED`
- `sections`: array, required when `status` is `COMPLETED`
- `limitations`: array of strings, required, may be empty

`PENDING`, `RUNNING`, `COMPLETED`, and `FAILED` report states are returned as `200 OK` lookup responses when the report resource exists. Temporary LLM service failure uses `AI_REPORT_UNAVAILABLE`.

## Versioning Rules

- `schema_version` versions the individual response schema, not the whole API surface.
- Additive optional fields do not require a major version change.
- Removing, renaming, or changing the meaning or type of a field requires a major version change.
- Analysis output schema may evolve independently from group, upload, or report response schemas.
- URI versioning is not used during the MVP.
- If independent schema tracking becomes hard to read, schema values may move from `1.0` to namespaced values such as `analysis-output/1.0`.

## Status

Phase 0 defines management rules and a first vertical slice draft. Backend phase must convert these drafts into concrete Pydantic schemas before implementation.
