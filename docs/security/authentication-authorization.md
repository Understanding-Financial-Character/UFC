# Authentication and Authorization

## Phase 0 Position

Authentication and authorization behavior is not implemented in Phase 0.

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
