import { skipToken } from "@reduxjs/toolkit/query";
import { Link, useNavigate, useParams } from "react-router-dom";

import {
  useGetLatestGroupAnalysisQuery,
  useGetMeQuery,
  useListCategoriesQuery,
  useListGroupsQuery,
  useListMockScenariosQuery,
  useLogoutMutation,
} from "../api/baseApi";
import { useAppSelector } from "../app/hooks";
import { ToastViewport } from "../components/feedback/ToastViewport";
import type { AnalysisResponse, GroupResponse, MeResponse } from "../features/auth/types";

const localDemoEmail = "demo-user@example.com";
type SettingsKey = "profile" | "account" | "notifications" | "security" | "support" | "service";

const settingsItems = [
  { key: "profile" as const, label: "프로필 관리", icon: "P" },
  { key: "account" as const, label: "연결된 계좌", caption: "Mock 데이터 연결", icon: "B" },
  { key: "notifications" as const, label: "알림 설정", caption: "분석 완료 알림", icon: "N" },
  { key: "security" as const, label: "보안 및 개인정보", caption: "토큰·암호화 적용", icon: "S" },
  { key: "support" as const, label: "고객센터", caption: "데모 문의", icon: "?" },
  { key: "service" as const, label: "서비스 정보", caption: "MVP 상태", icon: "i" },
];

export function SettingsPage() {
  const navigate = useNavigate();
  const user = useAppSelector((state) => state.auth.user);
  const [logout, { isLoading }] = useLogoutMutation();

  const onLogout = async () => {
    await logout().unwrap().catch(() => undefined);
    navigate("/login", { replace: true });
  };

  return (
    <main className="settings-page">
      <ToastViewport />
      <header className="settings-topbar">
        <div>
          <button aria-label="뒤로 가기" onClick={() => navigate(-1)} type="button">
            ‹
          </button>
          <h1>설정</h1>
        </div>
        <button aria-label="검색" type="button">
          ⌕
        </button>
      </header>

      <section className="settings-profile" aria-label="프로필 요약">
        <div className="settings-avatar" aria-hidden="true">
          <span>{initialFor(user?.display_name)}</span>
          <i>✓</i>
        </div>
        <div>
          <h2>{user?.display_name ?? "데모 유저"}</h2>
          <p>{user ? `${localDemoEmail} · ${user.role}` : localDemoEmail}</p>
          <small>이메일 원문은 보안 정책상 API 응답에 포함하지 않고 데모 주소만 표시합니다.</small>
        </div>
      </section>

      <section className="settings-list" aria-label="설정 메뉴">
        {settingsItems.slice(0, 4).map(({ key: itemKey, ...item }) => (
          <SettingsItem key={item.label} to={`/settings/${itemKey}`} {...item} />
        ))}
        <hr />
        {settingsItems.slice(4).map(({ key: itemKey, ...item }) => (
          <SettingsItem key={item.label} to={`/settings/${itemKey}`} {...item} />
        ))}
      </section>

      <section className="settings-footer">
        <button disabled={isLoading} onClick={onLogout} type="button">
          <span aria-hidden="true">↪</span>
          {isLoading ? "로그아웃 중" : "로그아웃"}
        </button>
        <p>버전 2.4.0-KINETIC</p>
        <Link to="/">홈으로 돌아가기</Link>
      </section>
    </main>
  );
}

export function SettingsDetailPage() {
  const navigate = useNavigate();
  const user = useAppSelector((state) => state.auth.user);
  const { section } = useParams();
  const activeKey = isSettingsKey(section) ? section : "profile";
  const activeItem = settingsItems.find((item) => item.key === activeKey) ?? settingsItems[0];
  const { data: me, isFetching: isRefreshingMe, refetch: refetchMe } = useGetMeQuery();
  const { data: groups = [], isLoading: isLoadingGroups } = useListGroupsQuery();
  const { data: categories = [], isLoading: isLoadingCategories } = useListCategoriesQuery();
  const { data: scenarios = [], isLoading: isLoadingScenarios } = useListMockScenariosQuery();
  const latestGroup = groups.find((group) => group.can_analyze) ?? groups[0];
  const { data: latestAnalysis, isLoading: isLoadingAnalysis } = useGetLatestGroupAnalysisQuery(
    latestGroup?.group_id ?? skipToken,
  );

  return (
    <main className="settings-page settings-detail-page">
      <ToastViewport />
      <header className="settings-topbar">
        <div>
          <button aria-label="설정으로 돌아가기" onClick={() => navigate("/settings")} type="button">
            ‹
          </button>
          <h1>{activeItem.label}</h1>
        </div>
        <Link aria-label="모임 홈" className="settings-topbar-link" to="/app">
          홈
        </Link>
      </header>

      <SettingsDetailPanel
        activeKey={activeKey}
        categoriesCount={categories.length}
        groups={groups}
        isLoadingAnalysis={isLoadingAnalysis}
        isLoadingCategories={isLoadingCategories}
        isLoadingGroups={isLoadingGroups}
        isLoadingScenarios={isLoadingScenarios}
        isRefreshingMe={isRefreshingMe}
        latestAnalysis={latestAnalysis}
        latestGroup={latestGroup}
        onRefreshProfile={() => void refetchMe()}
        scenariosCount={scenarios.length}
        title={activeItem.label}
        user={me ?? user}
      />
    </main>
  );
}

function SettingsItem({
  label,
  caption,
  icon,
  to,
}: {
  label: string;
  caption?: string;
  icon: string;
  to: string;
}) {
  return (
    <Link className="settings-item" to={to}>
      <span className="settings-item-icon" aria-hidden="true">
        {icon}
      </span>
      <span>
        <strong>{label}</strong>
        {caption ? <small>{caption}</small> : null}
      </span>
      <b aria-hidden="true">›</b>
    </Link>
  );
}

function SettingsDetailPanel({
  activeKey,
  title,
  user,
  groups,
  latestGroup,
  latestAnalysis,
  categoriesCount,
  scenariosCount,
  isLoadingGroups,
  isLoadingCategories,
  isLoadingScenarios,
  isLoadingAnalysis,
  isRefreshingMe,
  onRefreshProfile,
}: {
  activeKey: SettingsKey;
  title: string;
  user: MeResponse | null | undefined;
  groups: GroupResponse[];
  latestGroup: GroupResponse | undefined;
  latestAnalysis: AnalysisResponse | undefined;
  categoriesCount: number;
  scenariosCount: number;
  isLoadingGroups: boolean;
  isLoadingCategories: boolean;
  isLoadingScenarios: boolean;
  isLoadingAnalysis: boolean;
  isRefreshingMe: boolean;
  onRefreshProfile: () => void;
}) {
  return (
    <section className="settings-detail-panel" aria-label={`${title} 상세`}>
      <div className="settings-detail-heading">
        <span>{title}</span>
        <strong>{detailHeadline(activeKey)}</strong>
      </div>
      {activeKey === "profile" ? (
        <div className="settings-detail-grid">
          <SettingsInfo label="표시 이름" value={user?.display_name ?? "데모 유저"} />
          <SettingsInfo label="권한" value={user?.role ?? "USER"} />
          <SettingsInfo label="가입 일시" value={formatDate(user?.created_at)} />
          <button className="settings-inline-action" disabled={isRefreshingMe} onClick={onRefreshProfile} type="button">
            {isRefreshingMe ? "동기화 중" : "프로필 다시 불러오기"}
          </button>
        </div>
      ) : null}
      {activeKey === "account" ? (
        <div className="settings-detail-grid">
          <SettingsInfo label="연동 방식" value="Mock 시나리오" />
          <SettingsInfo label="사용 가능 시나리오" value={isLoadingScenarios ? "확인 중" : `${scenariosCount}개`} />
          <SettingsInfo label="연동 카테고리" value={isLoadingCategories ? "확인 중" : `${categoriesCount}개`} />
          <p>실제 은행 계좌 연결은 MVP 제외 범위이며, 현재는 백엔드 mock 거래 입력 기능으로 분석 흐름을 검증합니다.</p>
        </div>
      ) : null}
      {activeKey === "notifications" ? (
        <div className="settings-detail-grid">
          <SettingsInfo label="분석 완료" value="앱 내 상태 표시" />
          <SettingsInfo label="리포트 생성" value={isLoadingAnalysis ? "확인 중" : latestAnalysis ? analysisStatusLabel(latestAnalysis.status) : "결과 없음"} />
          <SettingsInfo label="모임 상태" value={latestGroup ? groupStatusLabel(latestGroup) : "모임 없음"} />
          <p>푸시 알림은 아직 연결하지 않았고, 현재 화면에서는 분석 진행 상태와 fallback 결과를 앱 안에서 확인합니다.</p>
        </div>
      ) : null}
      {activeKey === "security" ? (
        <div className="settings-detail-grid">
          <SettingsInfo label="인증 방식" value="Access / Refresh Token" />
          <SettingsInfo label="이메일 보호" value="암호문 + Lookup HMAC" />
          <SettingsInfo label="소유권 검증" value="사용자별 모임 접근 제한" />
          <p>설정 화면에는 password hash, token, ciphertext, 내부 사용자 ID를 표시하지 않습니다.</p>
        </div>
      ) : null}
      {activeKey === "support" ? (
        <div className="settings-detail-grid">
          <SettingsInfo label="데모 계정" value={localDemoEmail} />
          <SettingsInfo label="문의 범위" value="MVP 사용 흐름 검증" />
          <p>로그인, mock 데이터 적용, 분석 결과 표시가 실패하면 백엔드 실행 상태와 `/health`, `/ready` 상태를 먼저 확인해 주세요.</p>
        </div>
      ) : null}
      {activeKey === "service" ? (
        <div className="settings-detail-grid">
          <SettingsInfo label="참여 모임" value={isLoadingGroups ? "확인 중" : `${groups.length}개`} />
          <SettingsInfo label="분석 가능 모임" value={isLoadingGroups ? "확인 중" : `${groups.filter((group) => group.can_analyze).length}개`} />
          <SettingsInfo label="최신 분석" value={latestAnalysis ? resultStatusLabel(latestAnalysis.result_status) : "아직 없음"} />
          <Link className="settings-inline-link" to="/app">
            모임 홈에서 전체 상태 보기
          </Link>
        </div>
      ) : null}
    </section>
  );
}

function SettingsInfo({ label, value }: { label: string; value: string }) {
  return (
    <div className="settings-info">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function initialFor(displayName: string | undefined): string {
  const trimmed = displayName?.trim();
  return trimmed ? trimmed.slice(0, 1).toUpperCase() : "데";
}

function detailHeadline(activeKey: SettingsKey): string {
  const headlines: Record<SettingsKey, string> = {
    profile: "현재 로그인된 데모 프로필을 확인합니다.",
    account: "Mock 거래 입력과 카테고리 연결 상태를 확인합니다.",
    notifications: "분석 진행과 리포트 생성 상태를 확인합니다.",
    security: "현재 적용된 인증·개인정보 보호 기준입니다.",
    support: "데모 사용 중 확인할 운영 안내입니다.",
    service: "프론트에서 연결된 MVP 기능 요약입니다.",
  };
  return headlines[activeKey];
}

function isSettingsKey(value: string | undefined): value is SettingsKey {
  return settingsItems.some((item) => item.key === value);
}

function formatDate(value: string | undefined): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

function groupStatusLabel(group: GroupResponse): string {
  if (group.can_analyze) {
    return `분석 가능 · 구성원 ${group.member_count}명`;
  }
  return `준비 중 · 구성원 ${group.member_count}명`;
}

function analysisStatusLabel(status: AnalysisResponse["status"]): string {
  const labels: Record<string, string> = {
    READY: "분석 준비",
    PENDING: "분석 대기",
    RUNNING: "분석 실행 중",
    ANALYZING: "지표 계산 중",
    REPORT_GENERATING: "리포트 생성 중",
    COMPLETED: "분석 완료",
    COMPLETED_WITH_FALLBACK: "Fallback 완료",
    PARTIALLY_COMPLETED: "부분 완료",
    FAILED: "실패",
  };
  return labels[status] ?? status;
}

function resultStatusLabel(status: AnalysisResponse["result_status"]): string {
  const labels: Record<string, string> = {
    STANDARD: "표준 결과",
    PROVISIONAL: "참고용 결과",
    INSUFFICIENT_DATA: "데이터 부족",
  };
  return status ? labels[status] : "결과 없음";
}
