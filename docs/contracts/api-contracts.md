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

## Phase 3 Authentication and Authorization

BE Phase 3 replaces `X-UFC-User-Id` with bearer access tokens issued by the auth APIs:

- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/me`
- `GET /api/v1/admin/users`

Protected user APIs require:

```http
Authorization: Bearer <access_token>
```

Refresh tokens are opaque random tokens. Only their SHA-256 hashes are stored.

Email is stored as `email_ciphertext`, `email_lookup_hmac`, and `email_key_version`. API responses must not expose these storage fields.

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

### Create User (Deprecated By Phase 3)

- Method and path: `POST /users`
- Status: Not mounted in BE Phase 3; use `POST /auth/signup`.

### Signup

- Method and path: `POST /auth/signup`
- Sync or async: Sync
- Idempotency: Not required for MVP
- Resource owner: Public signup
- Success status: `201 Created`
- Error codes: `VALIDATION_ERROR`, `CONFLICT`, `INTERNAL_ERROR`

Request:

```json
{
  "email": "minji@example.com",
  "display_name": "민지",
  "password": "correct-password"
}
```

Response:

```json
{
  "schema_version": "1.0",
  "access_token": "opaque-signed-token",
  "refresh_token": "opaque-random-token",
  "token_type": "bearer",
  "expires_in": 900
}
```

Field rules:

- `email`: email string, required; normalized to lowercase for lookup
- `display_name`: string, required, 1-80 characters after trimming whitespace; blank values are rejected
- `password`: string, required, 12-128 characters; stored only as Argon2id hash

### Login

- Method and path: `POST /auth/login`
- Sync or async: Sync
- Idempotency: Not required
- Resource owner: Public credential exchange
- Success status: `200 OK`
- Error codes: `VALIDATION_ERROR`, `AUTHENTICATION_REQUIRED`, `RATE_LIMITED`, `INTERNAL_ERROR`

Request:

```json
{
  "email": "minji@example.com",
  "password": "correct-password"
}
```

Response: Signup token response.

### Refresh Token

- Method and path: `POST /auth/refresh`
- Sync or async: Sync
- Idempotency: Not required
- Resource owner: Token holder
- Success status: `200 OK`
- Error codes: `VALIDATION_ERROR`, `AUTHENTICATION_REQUIRED`, `INTERNAL_ERROR`

Request:

```json
{
  "refresh_token": "opaque-random-token"
}
```

Response: Signup token response. The used refresh token is revoked and replaced in one transaction. Reusing a revoked refresh token returns `401 AUTHENTICATION_REQUIRED` and revokes active tokens in the same refresh token family. If reuse is detected during a concurrent refresh, a token returned by the successful request can also be revoked and the client must require login again.

### Logout

- Method and path: `POST /auth/logout`
- Sync or async: Sync
- Idempotency: Effectively idempotent
- Resource owner: Token holder
- Success status: `200 OK`
- Error codes: `VALIDATION_ERROR`, `INTERNAL_ERROR`

Request:

```json
{
  "refresh_token": "opaque-random-token"
}
```

Response:

```json
{
  "status": "ok"
}
```

### Me

- Method and path: `GET /me`
- Sync or async: Sync
- Idempotency: Safe read
- Resource owner: Authenticated user
- Success status: `200 OK`
- Error codes: `AUTHENTICATION_REQUIRED`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

Response:

```json
{
  "schema_version": "1.0",
  "user_id": "uuid",
  "display_name": "민지",
  "role": "USER",
  "created_at": "2026-07-29T00:00:00Z"
}
```

### Admin User Summary

- Method and path: `GET /admin/users`
- Sync or async: Sync
- Idempotency: Safe read
- Resource owner: ADMIN
- Success status: `200 OK`
- Error codes: `AUTHENTICATION_REQUIRED`, `PERMISSION_DENIED`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

Response:

```json
[
  {
    "schema_version": "1.0",
    "user_id": "uuid",
    "display_name": "민지",
    "masked_email": "m***i@example.com",
    "role": "USER",
    "failed_login_count": 0,
    "created_at": "2026-07-29T00:00:00Z"
  }
]
```

### Create Group

- Method and path: `POST /groups`
- Sync or async: Sync
- Idempotency: Not required for MVP
- Resource owner: Authenticated USER or ADMIN creating the group
- Success status: `201 Created`
- Error codes: `VALIDATION_ERROR`, `AUTHENTICATION_REQUIRED`, `NOT_FOUND`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

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
- Resource owner: Authenticated USER or ADMIN
- Success status: `200 OK`
- Error codes: `VALIDATION_ERROR`, `AUTHENTICATION_REQUIRED`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

Response: array of Create Group response objects.

### Get Group

- Method and path: `GET /groups/{groupId}`
- Sync or async: Sync
- Idempotency: Safe read
- Resource owner: Group owner
- Success status: `200 OK`
- Error codes: `VALIDATION_ERROR`, `AUTHENTICATION_REQUIRED`, `NOT_FOUND`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

Response: Create Group response object, including `members`.

### Update Group

- Method and path: `PATCH /groups/{groupId}`
- Sync or async: Sync
- Idempotency: Not required for MVP
- Resource owner: Group owner
- Success status: `200 OK`
- Error codes: `VALIDATION_ERROR`, `AUTHENTICATION_REQUIRED`, `NOT_FOUND`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

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
- Error codes: `VALIDATION_ERROR`, `AUTHENTICATION_REQUIRED`, `NOT_FOUND`, `CONFLICT`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

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
- Error codes: `VALIDATION_ERROR`, `AUTHENTICATION_REQUIRED`, `NOT_FOUND`, `CONFLICT`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

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
- Error codes: `VALIDATION_ERROR`, `AUTHENTICATION_REQUIRED`, `NOT_FOUND`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

### List Categories

- Method and path: `GET /categories`
- Sync or async: Sync
- Idempotency: Safe read
- Resource owner: Public category metadata
- Success status: `200 OK`
- Error codes: `INTERNAL_ERROR`

Response:

```json
[
  {
    "schema_version": "1.0",
    "category_id": "uuid",
    "code": "FOOD",
    "name": "식비",
    "behavior_group": "PRACTICAL",
    "display_order": 1,
    "is_active": true
  }
]
```

Field rules:

- Categories are seeded by migration `20260730_0004` from immutable revision data at `backend/migrations/data/20260730_0004_categories.csv`.
- `behavior_group` is stored for later analysis feature calculation, but BE Phase 4 does not calculate features or MBTI scores.
- `behavior_group`: enum, one of `PRACTICAL`, `EXPERIENCE`, `RELATIONSHIP`, `REGULAR`, `SAVINGS`, `OTHER`.

### List Mock Scenarios

- Method and path: `GET /mock-scenarios`
- Sync or async: Sync
- Idempotency: Safe read
- Resource owner: Public mock metadata
- Success status: `200 OK`
- Error codes: `INTERNAL_ERROR`

Response:

```json
[
  {
    "schema_version": "1.0",
    "scenario_id": "mock-v2",
    "name": "Mock Transactions V2",
    "description": "Synthetic group-account transactions for BE Phase 4.",
    "transaction_count": 358
  }
]
```

### Apply Mock Scenario

- Method and path: `POST /groups/{groupId}/mock-scenarios/{scenarioId}/apply`
- Sync or async: Sync for MVP validation and accepted record persistence
- Idempotency: `source_row_key` prevents duplicate application within the same group
- Resource owner: Group owner
- Success status: `201 Created`
- Error codes: `AUTHENTICATION_REQUIRED`, `NOT_FOUND`, `CONFLICT`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

Response: Transaction Import response.

Field rules:

- Supported `scenarioId`: `mock-v2`.
- Mock source rows are loaded from `backend/app/modules/transactions/fixtures/transactions_mock_v2.csv`.
- Mock rows are projected into the target group; when source member ids do not exist in that group, active target members are assigned deterministically by order.
- Mock data is synthetic only and must not contain account numbers, card numbers, or bank authentication data.

### Import Transactions

- Method and path: `POST /groups/{groupId}/transactions/import`
- Sync or async: Sync for MVP validation and accepted record persistence
- Idempotency: `source_row_key` prevents duplicate import within the same group
- Resource owner: Group owner
- Success status: `201 Created`
- Error codes: `VALIDATION_ERROR`, `AUTHENTICATION_REQUIRED`, `NOT_FOUND`, `CONFLICT`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

Request:

```json
{
  "csv_text": "group_id,member_id,category_id,transaction_at,..."
}
```

Response:

```json
{
  "schema_version": "1.0",
  "group_id": "uuid",
  "source_type": "CSV_UPLOAD",
  "accepted_count": 1,
  "rejected_count": 1,
  "status": "PARTIALLY_COMPLETED",
  "rows": [
    {
      "row_number": 2,
      "source_row_key": "SCN-01-TXN-0001",
      "status": "ACCEPTED",
      "transaction_id": "uuid",
      "errors": []
    },
    {
      "row_number": 3,
      "source_row_key": "bad-row",
      "status": "REJECTED",
      "transaction_id": null,
      "errors": [
        {
          "field": "amount",
          "code": "AMOUNT_NOT_POSITIVE",
          "message": "amount must be positive."
        }
      ]
    }
  ]
}
```

Field rules:

- Accepted CSV fields: `group_id`, `member_id`, `category_id`, `transaction_at`, `transaction_type`, `amount`, `merchant_name`, `description`, `is_shared_expense`, `is_planned`, `is_recurring`, `is_excluded`, `exclusion_reason`, `source_row_key`.
- `group_id`: optional. When present, it must be a valid UUID and must match the `{groupId}` path parameter. When blank or omitted, the import uses the path group.
- `transaction_type`: enum, required, one of `DEPOSIT`, `WITHDRAWAL`.
- `amount`: positive decimal. Direction is represented only by `transaction_type`, not negative amounts.
- `amount`: must not exceed `999999999999.99`, matching the `Numeric(14, 2)` storage contract.
- All transaction amounts in the MVP CSV contract are interpreted as KRW. The CSV contract does not accept a currency field.
- `is_shared_expense`, `is_planned`, and `is_recurring`: nullable booleans. Blank cells are persisted as `null`, not `false`.
- `is_excluded`: boolean, defaults to false when the CSV cell is blank.
- `exclusion_reason`: required when `is_excluded` is true.
- `member_id`: optional; when present it must reference an `ACTIVE` member in the target group.
- `category_id`: optional; when present it must reference an active category.
- `source_row_key`: optional, but when present it must be unique within the same group.
- `member_id` and `category_id`: when present, must be valid UUID strings.
- `transaction_at`: must include a timezone offset, for example `2026-07-01T10:00:00+09:00` or `2026-07-01T01:00:00Z`.
- Text fields that exceed their contract length are rejected with row-level validation errors; values are not silently truncated.
- CSV headers containing account, card, bank auth, or token-like fields are rejected. The backend must not log full CSV raw text.
- `status`: enum, one of `COMPLETED`, `PARTIALLY_COMPLETED`, `FAILED`.

### List Transactions

- Method and path: `GET /groups/{groupId}/transactions`
- Sync or async: Sync
- Idempotency: Safe read
- Resource owner: Group owner
- Success status: `200 OK`
- Error codes: `AUTHENTICATION_REQUIRED`, `NOT_FOUND`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

Response:

```json
[
  {
    "schema_version": "1.0",
    "transaction_id": "uuid",
    "group_id": "uuid",
    "member_id": "uuid",
    "category_id": "uuid",
    "transaction_at": "2026-06-01T23:05:00+09:00",
    "transaction_type": "WITHDRAWAL",
    "amount": "31400.00",
    "merchant_name": "예술의전당",
    "description": null,
    "is_shared_expense": true,
    "is_planned": true,
    "is_recurring": false,
    "is_excluded": false,
    "exclusion_reason": null,
    "source_type": "CSV_UPLOAD",
    "source_row_key": "SCN-01-TXN-0001",
    "created_at": "2026-07-30T00:00:00Z"
  }
]
```

### Update Transaction

- Method and path: `PATCH /groups/{groupId}/transactions/{transactionId}`
- Sync or async: Sync
- Idempotency: Not required for MVP
- Resource owner: Group owner
- Success status: `200 OK`
- Error codes: `VALIDATION_ERROR`, `AUTHENTICATION_REQUIRED`, `NOT_FOUND`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

Request fields are optional individually, but at least one field must be provided.

### Delete Transaction

- Method and path: `DELETE /groups/{groupId}/transactions/{transactionId}`
- Sync or async: Sync
- Idempotency: Not required for MVP
- Resource owner: Group owner
- Success status: `204 No Content`
- Error codes: `AUTHENTICATION_REQUIRED`, `NOT_FOUND`, `INTERNAL_ERROR`
- Required headers: `Authorization: Bearer <access_token>`

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
