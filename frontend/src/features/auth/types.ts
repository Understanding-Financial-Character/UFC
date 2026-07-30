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

export type GroupStatus = "DRAFT" | "READY_FOR_ANALYSIS";

export interface GroupMemberResponse {
  schema_version: string;
  group_id: string;
  member_id: string;
  display_name: string;
  mbti: string;
  created_at: string;
}

export interface GroupResponse {
  schema_version: string;
  group_id: string;
  name: string;
  relationship_type: "COUPLE" | "FRIENDS" | "FAMILY" | "OTHER";
  status: GroupStatus;
  member_count: number;
  can_analyze: boolean;
  created_at: string;
  members: GroupMemberResponse[];
}

export interface CategoryResponse {
  schema_version: string;
  category_id: string;
  code: string;
  name: string;
  behavior_group: "PRACTICAL" | "EXPERIENCE" | "RELATIONSHIP" | "REGULAR" | "SAVINGS" | "OTHER";
  display_order: number;
  is_active: boolean;
}

export interface MockScenarioResponse {
  schema_version: string;
  scenario_id: string;
  name: string;
  description: string;
  transaction_count: number;
}
