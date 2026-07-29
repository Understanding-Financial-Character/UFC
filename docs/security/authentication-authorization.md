# Authentication and Authorization

## Phase 0 Position

Authentication and authorization behavior is not implemented in Phase 0.

## BE Phase 2 Position

BE Phase 2 uses the local user plus temporary `X-UFC-User-Id` approach accepted in `docs/decisions/ADR-0003-phase-2-user-identity.md`.

This supports group owner verification before full login is implemented. It must not be treated as production authentication.

`X-UFC-User-Id` is not an authentication boundary because a caller can supply any known user id. Services using this Phase 2 implementation must remain limited to controlled MVP development or demo environments until real authentication replaces the temporary header principal.

## MVP Requirements To Resolve Before Implementation

- User identity model
- Group membership model
- Member invitation or access model
- Authorization checks for group, transaction, analysis, and report resources
- Share card access rules

Backend implementation must not start until the MVP chooses one authentication approach and records it in an ADR:

- Local user plus session
- JWT-based login
- Demo account with limited mock authentication

## Baseline Rules

- Users may access only groups they belong to.
- Analysis results inherit access from the group.
- AI reports inherit access from the analysis result.
- Share links must not expose raw transaction data.
- Share links must have an access and expiration policy before implementation.

## Exclusions

- Bank account authorization
- Transfer authorization
- Credit bureau authorization
