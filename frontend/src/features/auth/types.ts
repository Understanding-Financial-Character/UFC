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

export interface GroupCreateRequest {
  name: string;
  relationship_type: GroupResponse["relationship_type"];
}

export interface MemberCreateRequest {
  display_name: string;
  mbti: string;
}

export type ImportStatus = "COMPLETED" | "PARTIALLY_COMPLETED" | "FAILED";

export interface TransactionImportResponse {
  schema_version: string;
  group_id: string;
  source_type: "CSV" | "MOCK" | "MANUAL";
  accepted_count: number;
  rejected_count: number;
  status: ImportStatus;
}

export interface AnalysisCreateRequest {
  period_start: string;
  period_end: string;
}

export type AnalysisRunStatus = "PENDING" | "RUNNING" | "COMPLETED" | "PARTIALLY_COMPLETED" | "FAILED";
export type AnalysisResultStatus = "STANDARD" | "PROVISIONAL" | "INSUFFICIENT_DATA";

export interface BehaviorMetricResponse {
  feature_code: string;
  status: "AVAILABLE" | "UNAVAILABLE";
  raw_value: number | string | null;
  normalized_score: number | string | null;
  unit: string;
  sample_count: number;
  unavailable_reason: string | null;
  evidence: string[];
}

export interface ConsumptionMbtiResponse {
  mbti_type: string | null;
  result_status: AnalysisResultStatus;
  axis_scores: Record<"EI" | "SN" | "TF" | "JP", number | string | null>;
  confidence: {
    level?: string;
    score?: number | string | null;
    [key: string]: unknown;
  };
  coverage: number | string | null;
  limitations: string[];
  rule_version: string;
  metadata: Record<string, unknown>;
}

export interface AIReportResponse {
  status: "COMPLETED" | "FALLBACK_COMPLETED" | "FAILED";
  fallback_used: boolean;
  fallback_reason: string | null;
  model_name: string | null;
  prompt_version: string | null;
  report_content: {
    headline?: string;
    summary?: string;
    strengths?: string[];
    commonPoints?: string[];
    differences?: string[];
    observationPoints?: string[];
    conversationQuestions?: string[];
    disclaimer?: string;
    [key: string]: unknown;
  } | null;
}

export interface AnalysisResponse {
  schema_version: string;
  analysis_id: string;
  group_id: string;
  status: AnalysisRunStatus;
  result_status: AnalysisResultStatus | null;
  provisional_reasons: string[];
  analysis_period_started_at: string;
  analysis_period_ended_at: string;
  source_type: "CSV" | "MOCK" | "MANUAL" | "INTERNAL_TEST";
  is_synthetic: boolean;
  input_schema_version: string;
  analysis_version: string;
  snapshot_hash: string;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
  behavior_metrics: BehaviorMetricResponse[];
  consumption_mbti_result: ConsumptionMbtiResponse | null;
  ai_report: AIReportResponse | null;
}
