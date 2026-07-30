import { createSlice, type PayloadAction } from "@reduxjs/toolkit";

import type { MeResponse, TokenResponse } from "./types";

interface AuthState {
  accessToken: string | null;
  tokenExpiresAt: number | null;
  user: MeResponse | null;
}

const initialState: AuthState = {
  accessToken: null,
  tokenExpiresAt: null,
  user: null,
};

const expiresAtFromNow = (expiresInSeconds: number): number =>
  Date.now() + expiresInSeconds * 1000;

export const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    tokenReceived(state, action: PayloadAction<TokenResponse>) {
      state.accessToken = action.payload.access_token;
      state.tokenExpiresAt = expiresAtFromNow(action.payload.expires_in);
    },
    userReceived(state, action: PayloadAction<MeResponse>) {
      state.user = action.payload;
    },
    sessionCleared(state) {
      state.accessToken = null;
      state.tokenExpiresAt = null;
      state.user = null;
    },
  },
});

export const { sessionCleared, tokenReceived, userReceived } = authSlice.actions;
export const authReducer = authSlice.reducer;
