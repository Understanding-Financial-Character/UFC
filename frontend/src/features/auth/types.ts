export type UserRole = "USER" | "ADMIN";

export interface TokenResponse {
  schema_version: string;
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface SignupRequest {
  email: string;
  display_name: string;
  password: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface LogoutRequest {
  refresh_token: string;
}

export interface LogoutResponse {
  status: "ok";
}

export interface MeResponse {
  schema_version: string;
  user_id: string;
  display_name: string;
  role: UserRole;
  created_at: string;
}

export interface ApiErrorPayload {
  error?: {
    code?: string;
    message?: string;
    details?: Record<string, unknown>;
    traceId?: string | null;
  };
}
