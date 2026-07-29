# Authentication and Authorization

## Phase 0 Position

Authentication and authorization behavior is not implemented in Phase 0.

## BE Phase 2 Position

BE Phase 2 uses the local user plus temporary `X-UFC-User-Id` approach accepted in `docs/decisions/ADR-0003-phase-2-user-identity.md`.

This supports group owner verification before full login is implemented. It must not be treated as production authentication.

`X-UFC-User-Id` is not an authentication boundary because a caller can supply any known user id. Services using this Phase 2 implementation must remain limited to controlled MVP development or demo environments until real authentication replaces the temporary header principal.

## BE Phase 3 Position

BE Phase 3 replaces `X-UFC-User-Id` with signed bearer access tokens and hashed refresh tokens as recorded in `docs/decisions/ADR-0004-security-baseline.md`.

MVP roles are:

- `USER`: may access only owned groups and later owned analysis results.
- `ADMIN`: may access service operations data and masked user summaries.

Admins do not receive raw financial transaction text, raw email, password hashes, refresh token hashes, or ciphertext fields by default.

## MVP Requirements To Resolve Before Implementation

- User identity model
- Group membership model
- Member invitation or access model
- Authorization checks for group, transaction, analysis, and report resources
- Share card access rules

Backend implementation must not start until the MVP chooses one authentication approach and records it in an ADR:

- Local user plus bearer access token and hashed refresh token

## Baseline Rules

- Users may access only groups they belong to.
- User role and resource ownership must be checked together.
- Analysis results inherit access from the group.
- AI reports inherit access from the analysis result.
- Share links must not expose raw transaction data.
- Share links must have an access and expiration policy before implementation.

## Exclusions

- Bank account authorization
- Transfer authorization
- Credit bureau authorization
