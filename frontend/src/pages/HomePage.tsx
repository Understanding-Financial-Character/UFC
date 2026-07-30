import { skipToken } from "@reduxjs/toolkit/query";
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  useAddGroupMemberMutation,
  useApplyMockScenarioMutation,
  useCreateAnalysisMutation,
  useCreateGroupMutation,
  useGetAnalysisQuery,
  useGetLatestGroupAnalysisQuery,
  useListCategoriesQuery,
  useListGroupsQuery,
  useListMockScenariosQuery,
  useLogoutMutation,
} from "../api/baseApi";
import { useAppSelector } from "../app/hooks";
import { ToastViewport } from "../components/feedback/ToastViewport";
import type { AnalysisResponse, GroupResponse, MemberCreateRequest } from "../features/auth/types";

interface HomePageProps {
  variant?: "user" | "admin";
}

const demoCredential = {
  email: "demo-user@example.com",
  password: "correct-password",
};

const mbtiOptions = [
  "ISTJ",
  "ISFJ",
  "INFJ",
  "INTJ",
  "ISTP",
  "ISFP",
  "INFP",
  "INTP",
  "ESTP",
  "ESFP",
  "ENFP",
  "ENTP",
  "ESTJ",
  "ESFJ",
  "ENFJ",
  "ENTJ",
];

const defaultCreateMembers: MemberCreateRequest[] = [
  { display_name: "민지", mbti: "ENFP" },
  { display_name: "도윤", mbti: "ISTJ" },
];

export function HomePage({ variant = "user" }: HomePageProps) {
  const navigate = useNavigate();
  const user = useAppSelector((state) => state.auth.user);
  const [activeAnalysisId, setActiveAnalysisId] = useState<string | null>(null);
  const [activeGroupId, setActiveGroupId] = useState<string | null>(null);
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [createName, setCreateName] = useState("새 모임통장");
  const [createRelationship, setCreateRelationship] = useState<GroupResponse["relationship_type"]>("FRIENDS");
  const [createMembers, setCreateMembers] = useState<MemberCreateRequest[]>(defaultCreateMembers);
  const [flowMessage, setFlowMessage] = useState<string | null>(null);
  const [flowError, setFlowError] = useState<string | null>(null);
  const [logout, { isLoading: isLoggingOut }] = useLogoutMutation();
  const [createGroup, { isLoading: isCreatingGroup }] = useCreateGroupMutation();
  const [addGroupMember] = useAddGroupMemberMutation();
  const [applyMockScenario, { isLoading: isApplyingMock }] = useApplyMockScenarioMutation();
  const [createAnalysis, { isLoading: isCreatingAnalysis }] = useCreateAnalysisMutation();
  const { data: mockScenarios = [], isLoading: isMockLoading } = useListMockScenariosQuery();
  const { data: categories = [], isLoading: isCategoryLoading } = useListCategoriesQuery();
  const { data: groups = [], isLoading: isGroupLoading, refetch: refetchGroups } = useListGroupsQuery(undefined, {
    skip: !user,
  });
  const readyGroup = groups.find((group) => group.can_analyze);
  const selectedGroup = groups.find((group) => group.group_id === activeGroupId) ?? readyGroup ?? groups[0];
  const latestGroupId = selectedGroup?.group_id ?? null;
  const { data: latestAnalysis, isFetching: isFetchingLatestAnalysis } = useGetLatestGroupAnalysisQuery(latestGroupId ?? skipToken, {
    skip: !user || Boolean(activeAnalysisId),
  });
  const { data: activeAnalysis } = useGetAnalysisQuery(activeAnalysisId ?? skipToken, {
    pollingInterval: activeAnalysisId ? 3000 : 0,
  });

  useEffect(() => {
    if (!user || activeGroupId || groups.length === 0) {
      return;
    }
    setActiveGroupId((readyGroup ?? groups[0]).group_id);
  }, [activeGroupId, groups, readyGroup, user]);

  const onLogout = async () => {
    await logout().unwrap().catch(() => undefined);
    navigate("/login", { replace: true });
  };

  const startAnalysisForGroup = async (group: GroupResponse) => {
    setFlowError(null);
    setFlowMessage(`${group.name} 분석을 실행하는 중입니다.`);
    setActiveGroupId(group.group_id);
    setActiveAnalysisId(null);
    try {
      const analysis = await createAnalysis({
        groupId: group.group_id,
        body: {
          period_start: "2026-05-01",
          period_end: "2026-07-31",
        },
      }).unwrap();
      setActiveAnalysisId(analysis.analysis_id);
      setFlowMessage("분석 결과가 준비됐습니다.");
    } catch (error) {
      setFlowError(errorMessage(error));
      setFlowMessage(null);
    }
  };

  const openSelectedReport = () => {
    const analysisId = activeAnalysis?.analysis_id ?? latestAnalysis?.analysis_id;
    if (analysisId) {
      navigate(`/analysis/result?analysisId=${analysisId}&groupId=${latestGroupId}`);
      return;
    }
    if (latestGroupId) {
      navigate(`/analysis/result?groupId=${latestGroupId}`);
    }
  };

  const openGroupReport = (group: GroupResponse) => {
    setActiveGroupId(group.group_id);
    setActiveAnalysisId(null);
    navigate(`/analysis/result?groupId=${group.group_id}`);
  };

  const runMockAnalysis = async () => {
    setFlowError(null);
    setFlowMessage("데모 모임을 생성하는 중입니다.");
    try {
      const group = await createGroup({
        name: `Mock Insight ${new Date().toLocaleTimeString("ko-KR", { hour12: false })}`,
        relationship_type: "FRIENDS",
      }).unwrap();
      const demoMembers = [
        { display_name: "민지", mbti: "ENFP" },
        { display_name: "도윤", mbti: "ISTJ" },
        { display_name: "서연", mbti: "ESFJ" },
        { display_name: "지훈", mbti: "ENTP" },
      ];
      setFlowMessage("구성원 MBTI를 등록하는 중입니다.");
      for (const member of demoMembers) {
        await addGroupMember({ groupId: group.group_id, body: member }).unwrap();
      }
      setFlowMessage("mock-v2 거래 데이터를 적용하는 중입니다.");
      await applyMockScenario({ groupId: group.group_id, scenarioId: primaryScenario?.scenario_id ?? "mock-v2" }).unwrap();
      setFlowMessage("규칙 기반 소비 MBTI와 Qwen 리포트를 생성하는 중입니다.");
      const analysis = await createAnalysis({
        groupId: group.group_id,
        body: {
          period_start: "2026-05-01",
          period_end: "2026-07-31",
        },
      }).unwrap();
      setActiveGroupId(group.group_id);
      setActiveAnalysisId(analysis.analysis_id);
      setFlowMessage("데모 분석 결과가 준비됐습니다.");
    } catch (error) {
      setFlowError(errorMessage(error));
      setFlowMessage(null);
    }
  };

  const updateCreateMember = (index: number, patch: Partial<MemberCreateRequest>) => {
    setCreateMembers((current) =>
      current.map((member, memberIndex) => (memberIndex === index ? { ...member, ...patch } : member)),
    );
  };

  const addCreateMember = () => {
    setCreateMembers((current) => {
      if (current.length >= 4) {
        return current;
      }
      return [...current, { display_name: `구성원 ${current.length + 1}`, mbti: "ENFP" }];
    });
  };

  const removeCreateMember = (index: number) => {
    setCreateMembers((current) => {
      if (current.length <= 2) {
        return current;
      }
      return current.filter((_member, memberIndex) => memberIndex !== index);
    });
  };

  const createMeeting = async () => {
    const normalizedMembers = createMembers.map((member) => ({
      display_name: member.display_name.trim(),
      mbti: member.mbti,
    }));
    if (!createName.trim()) {
      setFlowError("모임 이름을 입력해 주세요.");
      return;
    }
    if (normalizedMembers.some((member) => !member.display_name)) {
      setFlowError("모든 구성원 이름을 입력해 주세요.");
      return;
    }

    setFlowError(null);
    setFlowMessage("새 모임을 생성하는 중입니다.");
    try {
      const group = await createGroup({
        name: createName.trim(),
        relationship_type: createRelationship,
      }).unwrap();
      for (const member of normalizedMembers) {
        await addGroupMember({ groupId: group.group_id, body: member }).unwrap();
      }
      await refetchGroups();
      setActiveGroupId(group.group_id);
      setActiveAnalysisId(null);
      setIsCreateOpen(false);
      setCreateName("새 모임통장");
      setCreateRelationship("FRIENDS");
      setCreateMembers(defaultCreateMembers);
      setFlowMessage(`${group.name} 모임이 생성됐습니다. mock 데이터 연결 후 분석을 실행할 수 있습니다.`);
    } catch (error) {
      setFlowError(errorMessage(error));
      setFlowMessage(null);
    }
  };

  const readyGroups = groups.filter((group) => group.can_analyze).length;
  const primaryScenario = mockScenarios[0];
  const categoryCount = categories.length;
  const isFlowLoading = isCreatingGroup || isApplyingMock || isCreatingAnalysis;
  const insightAnalysis = activeAnalysis ?? latestAnalysis;
  const hasSelectedReport = Boolean(insightAnalysis);
  const visibleGroups = activeGroupId
    ? [...groups].sort((left, right) => {
        if (left.group_id === activeGroupId) {
          return -1;
        }
        if (right.group_id === activeGroupId) {
          return 1;
        }
        return 0;
      })
    : groups;

  return (
    <main className="landing-page">
      <ToastViewport />
      <header className="landing-topbar">
        <div className="landing-topbar-brand">
          <button aria-label="이전으로" className="icon-button" type="button">
            ‹
          </button>
          <Link to="/">모임 성향 분석</Link>
        </div>
        <nav className="landing-nav" aria-label="주요 메뉴">
          <a href="#explore">탐색</a>
          <a href="#groups">모임</a>
          <a href="#insights">트렌드</a>
          <Link to={user ? "/settings" : "/login"}>프로필</Link>
        </nav>
        <div className="landing-session">
          {user ? (
            <>
              <span>{user.display_name}</span>
              <button disabled={isLoggingOut} onClick={onLogout} type="button">
                로그아웃
              </button>
            </>
          ) : (
            <>
              <Link className="text-link" to="/login">
                로그인
              </Link>
              <Link className="button-link" to="/signup">
                회원가입
              </Link>
            </>
          )}
        </div>
      </header>

      <section className="landing-hero" id="explore">
        <div>
          <span className="landing-badge">활성 모임통장</span>
          <h1>
            {variant === "admin" ? "서비스 운영" : "나의 금융"}
            <br />
            <strong>{variant === "admin" ? "대시보드" : "생태계"}</strong>
          </h1>
        </div>
        <div className="landing-summary-grid">
          <MetricCard label="연동된 카테고리" value={isCategoryLoading ? "..." : String(categoryCount)} />
          <MetricCard
            label={user ? "참여 모임" : "Mock 거래"}
            value={
              user
                ? isGroupLoading
                  ? "..."
                  : String(groups.length).padStart(2, "0")
                : isMockLoading
                  ? "..."
                  : String(primaryScenario?.transaction_count ?? 0)
            }
          />
        </div>
      </section>

      <section className="meeting-grid" id="groups" aria-label="모임 성향 카드">
        {user && groups.length > 0
          ? visibleGroups.map((group, index) => {
              const isSelected = selectedGroup?.group_id === group.group_id;
              return (
              <MeetingCard
                key={group.group_id}
                icon={["T", "W", "F", "O"][index % 4]}
                name={group.name}
                relationship={relationshipLabel(group.relationship_type)}
                mbti={isSelected ? "선택됨" : group.can_analyze ? "분석 가능" : "준비 중"}
                progress={group.can_analyze ? 100 : Math.min(group.member_count * 25, 75)}
                goal={`${group.member_count}/4명 구성`}
                highlighted={isSelected}
                actionLabel={group.can_analyze ? "분석 실행" : undefined}
                reportLabel="리포트 보기"
                onAction={group.can_analyze ? () => startAnalysisForGroup(group) : undefined}
                onReport={() => openGroupReport(group)}
              />
              );
            })
          : demoMeetings.map((meeting) => <MeetingCard key={meeting.name} {...meeting} />)}
      </section>

      <section className="landing-insights" id="insights">
        <article className="insight-panel">
          <div className="section-title">
            <span aria-hidden="true">◆</span>
            <h2>소비 성향 분석 인사이트</h2>
          </div>
          {user ? (
            <AnalysisInsight
              analysis={insightAnalysis}
              groupCount={groups.length}
              readyGroupCount={readyGroups}
              selectedGroup={selectedGroup}
              isFetching={isFetchingLatestAnalysis}
              onOpenReport={hasSelectedReport ? openSelectedReport : undefined}
              message={flowMessage}
              error={flowError}
            />
          ) : (
            <p>
              UFC는 2~4인 모임통장 소비 데이터를 바탕으로 규칙 기반 소비 MBTI와 근거 요약을 보여주는
              MVP입니다. 실제 성격 진단이나 금융 진단이 아니라, 모임 대화를 돕는 설명형 분석입니다.
            </p>
          )}
          <div className="insight-score" aria-label="예시 소비 MBTI">
            <span>{insightAnalysis?.consumption_mbti_result?.mbti_type ?? "ESTJ"}</span>
          </div>
        </article>

        <article className="mock-panel">
          <h2>Mock 데이터 준비 상태</h2>
          {primaryScenario ? (
            <p>
              `{primaryScenario.scenario_id}`에는 {primaryScenario.transaction_count}건의 synthetic 거래가
              준비되어 있습니다. 로그인 후 그룹과 구성원 4명을 만든 뒤 mock scenario를 적용할 수 있습니다.
            </p>
          ) : (
            <p>Mock scenario metadata를 불러오는 중입니다.</p>
          )}
          {user ? (
            <button className="mock-action" disabled={isFlowLoading || isMockLoading} onClick={runMockAnalysis} type="button">
              {isFlowLoading ? "데모 분석 실행 중" : "mock-v2로 분석 실행"}
            </button>
          ) : null}
          <div className="demo-login-card" id="profile">
            <span>로컬 테스트 계정</span>
            <code>{demoCredential.email}</code>
            <code>{demoCredential.password}</code>
            <Link to="/login">이 계정으로 로그인하기</Link>
          </div>
        </article>
      </section>

      {user ? null : (
        <section className="landing-cta" aria-label="시작하기">
          <Link className="button-link" to="/login">
            로그인하고 모임 보기
          </Link>
          <Link className="text-link" to="/signup">
            새 계정 만들기
          </Link>
        </section>
      )}

      <button
        className="floating-action"
        onClick={() => (user ? setIsCreateOpen(true) : navigate("/signup"))}
        type="button"
        aria-label="새 모임 만들기"
      >
        +
      </button>
      {user && isCreateOpen ? (
        <CreateMeetingPanel
          isLoading={isFlowLoading}
          members={createMembers}
          name={createName}
          onAddMember={addCreateMember}
          onClose={() => setIsCreateOpen(false)}
          onCreate={createMeeting}
          onMemberChange={updateCreateMember}
          onRemoveMember={removeCreateMember}
          onRelationshipChange={setCreateRelationship}
          onNameChange={setCreateName}
          relationship={createRelationship}
        />
      ) : null}
      <MobileNav />
    </main>
  );
}

function CreateMeetingPanel({
  isLoading,
  members,
  name,
  relationship,
  onAddMember,
  onClose,
  onCreate,
  onMemberChange,
  onNameChange,
  onRelationshipChange,
  onRemoveMember,
}: {
  isLoading: boolean;
  members: MemberCreateRequest[];
  name: string;
  relationship: GroupResponse["relationship_type"];
  onAddMember: () => void;
  onClose: () => void;
  onCreate: () => void;
  onMemberChange: (index: number, patch: Partial<MemberCreateRequest>) => void;
  onNameChange: (value: string) => void;
  onRelationshipChange: (value: GroupResponse["relationship_type"]) => void;
  onRemoveMember: (index: number) => void;
}) {
  return (
    <div className="meeting-create-overlay" role="presentation">
      <section className="meeting-create-panel" role="dialog" aria-modal="true" aria-label="새 모임 만들기">
        <header>
          <div>
            <span>새 모임</span>
            <h2>모임통장을 추가해요</h2>
          </div>
          <button aria-label="닫기" onClick={onClose} type="button">
            ×
          </button>
        </header>
        <label className="meeting-create-field">
          <span>모임 이름</span>
          <input value={name} onChange={(event) => onNameChange(event.target.value)} />
        </label>
        <label className="meeting-create-field">
          <span>관계 유형</span>
          <select value={relationship} onChange={(event) => onRelationshipChange(event.target.value as GroupResponse["relationship_type"])}>
            <option value="FRIENDS">친구 모임</option>
            <option value="COUPLE">부부/연인</option>
            <option value="FAMILY">가족</option>
            <option value="OTHER">기타 모임</option>
          </select>
        </label>
        <div className="meeting-create-members">
          <div>
            <span>구성원 MBTI</span>
            <small>2~4명까지 추가할 수 있어요</small>
          </div>
          {members.map((member, index) => (
            <div className="meeting-create-member" key={`${index}-${member.mbti}`}>
              <input
                aria-label={`구성원 ${index + 1} 이름`}
                value={member.display_name}
                onChange={(event) => onMemberChange(index, { display_name: event.target.value })}
              />
              <select
                aria-label={`구성원 ${index + 1} MBTI`}
                value={member.mbti}
                onChange={(event) => onMemberChange(index, { mbti: event.target.value })}
              >
                {mbtiOptions.map((mbti) => (
                  <option key={mbti} value={mbti}>
                    {mbti}
                  </option>
                ))}
              </select>
              <button disabled={members.length <= 2} onClick={() => onRemoveMember(index)} type="button">
                삭제
              </button>
            </div>
          ))}
          <button className="meeting-create-add" disabled={members.length >= 4} onClick={onAddMember} type="button">
            구성원 추가
          </button>
        </div>
        <footer>
          <button className="meeting-create-secondary" onClick={onClose} type="button">
            취소
          </button>
          <button disabled={isLoading} onClick={onCreate} type="button">
            {isLoading ? "생성 중" : "모임 만들기"}
          </button>
        </footer>
      </section>
    </div>
  );
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="summary-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

interface MeetingCardProps {
  icon: string;
  name: string;
  relationship: string;
  mbti: string;
  progress: number;
  goal: string;
  highlighted?: boolean;
  actionLabel?: string;
  reportLabel?: string;
  onAction?: () => void;
  onReport?: () => void;
}

function MeetingCard({
  icon,
  name,
  relationship,
  mbti,
  progress,
  goal,
  highlighted,
  actionLabel,
  reportLabel,
  onAction,
  onReport,
}: MeetingCardProps) {
  return (
    <article className={`meeting-card-ui${highlighted ? " meeting-card-ui--highlighted" : ""}`}>
      <div className="meeting-card-body">
        <div className="meeting-card-header">
          <div className="meeting-title-row">
            <span className="meeting-icon" aria-hidden="true">
              {icon}
            </span>
            <div>
              <h2>{name}</h2>
              <p>{relationship}</p>
            </div>
          </div>
          <span className="mbti-chip">{mbti}</span>
        </div>
        <div className="progress-area">
          <div>
            <span>목표 달성률</span>
            <strong>{progress}%</strong>
          </div>
          <div className="progress-track">
            <i style={{ width: `${progress}%` }} />
          </div>
        </div>
      </div>
      <footer>
        <div>
          <span>목표 정보</span>
          <strong>{goal}</strong>
        </div>
        <div className="meeting-card-actions">
          {reportLabel && onReport ? (
            <button aria-label={`${name} ${reportLabel}`} onClick={onReport} type="button">
              리포트
            </button>
          ) : null}
          {actionLabel && onAction ? (
            <button aria-label={`${name} ${actionLabel}`} onClick={onAction} type="button">
              분석
            </button>
          ) : (
            <span className="meeting-card-hint">준비 중</span>
          )}
        </div>
      </footer>
    </article>
  );
}

function AnalysisInsight({
  analysis,
  groupCount,
  readyGroupCount,
  selectedGroup,
  isFetching,
  onOpenReport,
  message,
  error,
}: {
  analysis?: AnalysisResponse;
  groupCount: number;
  readyGroupCount: number;
  selectedGroup?: GroupResponse;
  isFetching: boolean;
  onOpenReport?: () => void;
  message: string | null;
  error: string | null;
}) {
  if (!analysis) {
    return (
      <div className="analysis-empty">
        <p>
          {selectedGroup ? `${selectedGroup.name} 모임이 선택되어 있습니다. ` : ""}
          현재 계정은 {groupCount}개 모임을 가지고 있고, 그중 {readyGroupCount}개 모임이 분석 준비
          상태입니다. 선택한 모임에서 분석을 실행하거나 mock-v2 데모 분석을 만들 수 있습니다.
        </p>
        {isFetching ? <p className="flow-status">선택한 모임의 최신 리포트를 확인하는 중입니다.</p> : null}
        <StatusLine message={message} error={error} />
      </div>
    );
  }

  const report = analysis.ai_report?.report_content;
  const result = analysis.consumption_mbti_result;
  const topEvidence = analysis.behavior_metrics
    .filter((metric) => metric.status === "AVAILABLE")
    .flatMap((metric) => metric.evidence.slice(0, 1))
    .slice(0, 3);

  return (
    <div className="analysis-summary">
      <p className="analysis-kicker">
        {selectedGroup?.name ?? "선택한 모임"} · {analysis.status} · {analysis.result_status ?? "결과 대기"} ·{" "}
        {analysis.is_synthetic ? "Mock 데이터" : "사용자 데이터"}
      </p>
      <h3>{report?.headline ?? "소비 MBTI 분석 결과"}</h3>
      <p>{report?.summary ?? "규칙 엔진 결과와 Evidence를 기반으로 분석 결과를 표시합니다."}</p>
      {result ? (
        <dl className="axis-grid">
          {(["EI", "SN", "TF", "JP"] as const).map((axis) => (
            <div key={axis}>
              <dt>{axis}</dt>
              <dd>{formatRatio(result.axis_scores[axis])}</dd>
            </div>
          ))}
        </dl>
      ) : null}
      {topEvidence.length > 0 ? (
        <ul className="evidence-list">
          {topEvidence.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      ) : null}
      {report?.conversationQuestions?.length ? (
        <p className="question-line">{report.conversationQuestions[0]}</p>
      ) : null}
      {onOpenReport ? (
        <button className="insight-report-action" onClick={onOpenReport} type="button">
          이 모임 리포트 자세히 보기
        </button>
      ) : null}
      <StatusLine message={message} error={error} />
    </div>
  );
}

function StatusLine({ message, error }: { message: string | null; error: string | null }) {
  if (!message && !error) {
    return null;
  }
  return <p className={error ? "flow-status flow-status--error" : "flow-status"}>{error ?? message}</p>;
}

function MobileNav() {
  return (
    <nav className="mobile-nav" aria-label="모바일 메뉴">
      <a href="#explore">탐색</a>
      <a className="active" href="#groups">
        모임
      </a>
      <a href="#insights">트렌드</a>
      <Link to="/settings">프로필</Link>
    </nav>
  );
}

function relationshipLabel(value: string): string {
  const labels: Record<string, string> = {
    COUPLE: "Couple",
    FAMILY: "Family",
    FRIENDS: "Friends",
    OTHER: "Group",
  };
  return labels[value] ?? "Group";
}

function formatRatio(value: number | string | null | undefined): string {
  if (value === null || value === undefined) {
    return "-";
  }
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return String(value);
  }
  return `${Math.round(numeric * 100)}%`;
}

function errorMessage(error: unknown): string {
  if (
    typeof error === "object" &&
    error !== null &&
    "data" in error &&
    typeof error.data === "object" &&
    error.data !== null &&
    "error" in error.data
  ) {
    const payload = error.data.error;
    if (
      typeof payload === "object" &&
      payload !== null &&
      "message" in payload &&
      typeof payload.message === "string"
    ) {
      return payload.message;
    }
  }
  return "요청을 처리하지 못했습니다. 백엔드 상태와 로그인 세션을 확인해 주세요.";
}

const demoMeetings: MeetingCardProps[] = [
  {
    icon: "T",
    name: "Jeju Trip",
    relationship: "Travel Squad",
    mbti: "ESTJ",
    progress: 75,
    goal: "2,000,000원",
  },
  {
    icon: "W",
    name: "Wedding Fund",
    relationship: "Couple",
    mbti: "분석 중",
    progress: 22,
    goal: "15,000,000원",
    highlighted: true,
  },
  {
    icon: "F",
    name: "Gourmet Club",
    relationship: "Friends",
    mbti: "ENFP",
    progress: 92,
    goal: "500,000원",
  },
  {
    icon: "O",
    name: "Tech Office",
    relationship: "Colleagues",
    mbti: "INTJ",
    progress: 48,
    goal: "25,000,000원",
  },
];
