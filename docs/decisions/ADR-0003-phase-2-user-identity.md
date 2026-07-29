# ADR-0003. Phase 2 User Identity

## Status

Accepted

## Context

BE Phase 2 needs user signup, group ownership checks, and member management before the MVP implements a full login flow.

`docs/security/authentication-authorization.md` requires an MVP authentication approach to be selected before domain APIs are implemented.

## Decision

BE Phase 2 uses a local `User` record plus a temporary request header for API ownership checks:

- `POST /api/v1/users` creates a basic local user with `display_name`.
- Header-identified MVP group endpoints require `X-UFC-User-Id`.
- A group is accessible only when `groups.owner_user_id` matches `X-UFC-User-Id`.
- Inaccessible or missing groups return `NOT_FOUND` to avoid exposing another user's resources.

This is not a password, session, OAuth, or JWT implementation. It exists only to support MVP domain ownership while login is not yet in scope.

The header is not an authentication boundary. A service using this Phase 2 implementation must not be exposed to an untrusted public environment before real authentication replaces the temporary header principal.

## Consequences

- Frontend and tests can create a user first and pass the returned `user_id` in `X-UFC-User-Id`.
- Future authentication work must replace the header-derived user id with a real authenticated principal, for example by changing the API dependency from `CurrentUserId` to `CurrentPrincipal` and passing `authenticated_user.id` into the existing owner checks.
- Group ownership remains backend-owned and does not depend on frontend-side filtering.
