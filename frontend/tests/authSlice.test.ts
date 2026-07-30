import { describe, expect, it } from "vitest";

import { authReducer, sessionCleared, tokenReceived, userReceived } from "../src/features/auth/authSlice";
import type { MeResponse, TokenResponse } from "../src/features/auth/types";

const tokenResponse: TokenResponse = {
  schema_version: "1.0",
  access_token: "access-token",
  refresh_token: "refresh-token-that-stays-out-of-redux",
  token_type: "bearer",
  expires_in: 900,
};

const userResponse: MeResponse = {
  schema_version: "1.0",
  user_id: "user-id",
  display_name: "Minji",
  role: "USER",
  created_at: "2026-07-29T00:00:00Z",
};

describe("authReducer", () => {
  it("stores access token metadata without storing the refresh token", () => {
    const state = authReducer(undefined, tokenReceived(tokenResponse));

    expect(state.accessToken).toBe("access-token");
    expect(state.tokenExpiresAt).toBeGreaterThan(Date.now());
    expect(JSON.stringify(state)).not.toContain(tokenResponse.refresh_token);
  });

  it("stores the authenticated user and clears the in-memory session", () => {
    const withToken = authReducer(undefined, tokenReceived(tokenResponse));
    const withUser = authReducer(withToken, userReceived(userResponse));
    const cleared = authReducer(withUser, sessionCleared());

    expect(withUser.user?.role).toBe("USER");
    expect(cleared.accessToken).toBeNull();
    expect(cleared.tokenExpiresAt).toBeNull();
    expect(cleared.user).toBeNull();
  });
});
