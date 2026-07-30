import { skipToken } from "@reduxjs/toolkit/query";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";

import {
  useAddGroupMemberMutation,
  useApplyMockScenarioMutation,
  useCreateAnalysisMutation,
  useCreateGroupMutation,
  useGetAnalysisQuery,
  useGetLatestGroupAnalysisQuery,
  useListMockScenariosQuery,
} from "../api/baseApi";
import { useAppSelector } from "../app/hooks";
import { ToastViewport } from "../components/feedback/ToastViewport";
import type { AnalysisResponse, AnalysisRunStatus, GroupResponse } from "../features/auth/types";

type RelationshipType = GroupResponse["relationship_type"];

interface FlowState {
  relationshipType: RelationshipType;
  relationshipLabel: string;
  goalIcon: string;
  goalName: string;
  targetAmount: string;
  targetDate: string;
  monthlyAmount: string;
  groupId?: string;
  analysisId?: string;
}

const flowStorageKey = "ufc.meetingFlow";

const defaultFlow: FlowState = {
  relationshipType: "FRIENDS",
  relationshipLabel: "친구 모임",
  goalIcon: "✈",
  goalName: "제주 여행 300만원 모으기",
  targetAmount: "3000000",
  targetDate: "2026-08-31",
  monthlyAmount: "250000",
};

const demoMembers = [
  { display_name: "민지", mbti: "ENFP" },
  { display_name: "도윤", mbti: "ISTJ" },
  { display_name: "서연", mbti: "ESFJ" },
  { display_name: "지훈", mbti: "ENTP" },
];

export function StitchLandingPage() {
  const navigate = useNavigate();

  return (
    <main className="flow-page flow-landing">
      <FlowHeader title="Meeting Personality" />
      <section className="flow-hero">
        <div className="flow-copy">
          <h1>
            우리 모임통장의
            <br />
            <strong>소비 MBTI</strong>를
            <br />
            확인해보세요
          </h1>
          <p>부부, 연인, 친구 모임의 실제 지출 데이터를 기반으로 분석하는 우리만의 돈 성향</p>
        </div>

        <div className="flow-illustration" aria-hidden="true">
          <div className="mini-card mini-card--couple">
            <span>Couple</span>
            <div className="mini-photo">☕</div>
            <strong>실속파 알뜰형</strong>
          </div>
          <div className="mini-card mini-card--friends">
            <span>Friends</span>
            <div className="mini-photo">🎉</div>
            <strong>경험 확장형</strong>
            <i />
          </div>
          <div className="floating-chip">분석 중...</div>
          <div className="floating-chip floating-chip--left">근거 기반</div>
        </div>

        <div className="flow-hint">개인 MBTI와는 또 다른 우리 모임만의 소비 성향이 궁금하지 않나요?</div>
      </section>
      <FlowBottomAction label="분석 시작하기" onClick={() => navigate("/onboarding")} />
    </main>
  );
}

export function OnboardingIntroPage() {
  const navigate = useNavigate();

  return (
    <main className="flow-page flow-centered">
      <FlowHeader title="Meeting Personality" />
      <section className="onboarding-card">
        <div className="search-visual" aria-hidden="true">
          <div className="visual-grid">
            <span />
            <span />
            <span />
            <span />
          </div>
          <b>⌕</b>
        </div>
        <span className="flow-badge">QUIZ START</span>
        <h1>
          몇 가지 선택만 하면
          <br />
          우리 모임의 <strong>돈 성향</strong>을<br />
          예측해볼게요
        </h1>
        <p>평소 함께 쓰는 소비 습관을 통해 재미있는 금융 MBTI를 분석합니다.</p>
      </section>
      <FlowBottomAction label="시작하기" helper="약 2분 정도 소요됩니다" onClick={() => navigate("/flow/relationship")} />
    </main>
  );
}

export function RelationshipSelectionPage() {
  const navigate = useNavigate();
  const [selected, setSelected] = useState<RelationshipType>(loadFlow().relationshipType);
  const options = [
    {
      value: "COUPLE" as const,
      label: "부부/연인",
      body: "데이트, 생활비, 결혼 자금 등 둘만의 소중한 미래를 설계해요.",
      icon: "♡",
    },
    {
      value: "FRIENDS" as const,
      label: "친구 모임",
      body: "여행, 취미 활동, 친목 도모 등 다양한 사람들과 즐겁게 모아요.",
      icon: "👥",
    },
    {
      value: "FAMILY" as const,
      label: "가족",
      body: "생활비, 기념일, 여행처럼 가족 단위 지출을 함께 살펴봐요.",
      icon: "⌂",
    },
    {
      value: "OTHER" as const,
      label: "기타 모임",
      body: "스터디, 동료, 프로젝트 모임처럼 목적이 다양한 소비를 분석해요.",
      icon: "◎",
    },
  ];

  const onNext = () => {
    const chosen = options.find((option) => option.value === selected) ?? options[1];
    saveFlow({ relationshipType: chosen.value, relationshipLabel: chosen.label });
    navigate("/flow/goal");
  };

  return (
    <main className="flow-page">
      <FlowHeader title="Meeting Personality" backTo="/onboarding" />
      <FlowProgress step={1} label="Relationship" />
      <section className="flow-question">
        <h1>
          누구와 함께
          <br />
          돈을 모으고 있나요?
        </h1>
        <p>관계에 따라 소비 성향 분석 결과가 달라집니다. 가장 잘 어울리는 모임을 선택해 주세요.</p>
      </section>
      <div className="choice-list">
        {options.map((option) => (
          <button
            className={`choice-tile${selected === option.value ? " choice-tile--active" : ""}`}
            key={option.value}
            onClick={() => setSelected(option.value)}
            type="button"
          >
            <span className="choice-icon">{option.icon}</span>
            <span>
              <strong>{option.label}</strong>
              <small>{option.body}</small>
            </span>
            <b>{selected === option.value ? "✓" : ""}</b>
          </button>
        ))}
      </div>
      <FlowBottomAction label="다음 단계로" onClick={onNext} />
    </main>
  );
}

export function GoalSetupPage() {
  const navigate = useNavigate();
  const [flow, setFlow] = useState<FlowState>(loadFlow());

  const update = (patch: Partial<FlowState>) => {
    setFlow((current) => ({ ...current, ...patch }));
  };

  const onSubmit = () => {
    saveFlow(flow);
    navigate("/flow/summary");
  };

  return (
    <main className="flow-page">
      <FlowHeader title="Meeting Personality" backTo="/flow/relationship" />
      <FlowProgress step={2} label="Goal" />
      <section className="flow-question">
        <h1>목표 상세 설정</h1>
        <p>친구들과 함께 달성할 멋진 목표를 완성해볼까요?</p>
      </section>
      <section className="goal-form">
        <div className="emoji-picker">
          {["✈", "🍲", "🎁", "⌂", "🎉"].map((icon) => (
            <button
              className={flow.goalIcon === icon ? "selected" : ""}
              key={icon}
              onClick={() => update({ goalIcon: icon })}
              type="button"
            >
              {icon}
            </button>
          ))}
        </div>
        <FormField label="모임 목표 이름">
          <input value={flow.goalName} onChange={(event) => update({ goalName: event.target.value })} />
        </FormField>
        <FormField label="최종 목표 금액 (KRW)">
          <input inputMode="numeric" value={flow.targetAmount} onChange={(event) => update({ targetAmount: event.target.value })} />
        </FormField>
        <FormField label="목표 날짜">
          <input type="date" value={flow.targetDate} onChange={(event) => update({ targetDate: event.target.value })} />
        </FormField>
        <FormField label="매월 저축할 금액">
          <input inputMode="numeric" value={flow.monthlyAmount} onChange={(event) => update({ monthlyAmount: event.target.value })} />
        </FormField>
        <div className="motivation-row">
          <span>심리적 동기부여 알림</span>
          <b>ON</b>
        </div>
      </section>
      <FlowBottomAction label="완료" onClick={onSubmit} />
    </main>
  );
}

export function GoalSummaryPage() {
  const navigate = useNavigate();
  const flow = loadFlow();

  return (
    <main className="flow-page flow-centered">
      <FlowHeader title="Meeting Personality" backTo="/flow/goal" />
      <section className="summary-complete">
        <div className="complete-mark">✓</div>
        <h1>
          모임 생성이
          <br />
          완료되었습니다!
        </h1>
        <article className="goal-card">
          <div className="goal-icon">{flow.goalIcon}</div>
          <h2>{flow.goalName}</h2>
          <p>{flow.relationshipLabel}</p>
          <div>
            <span>목표 금액</span>
            <strong>{formatWon(flow.targetAmount)}</strong>
          </div>
          <small>소비 MBTI 분석 대기 중</small>
        </article>
      </section>
      <FlowBottomAction label="소비 데이터 연결하기" helper="나중에 할 수도 있어요" onClick={() => navigate("/flow/data")} />
    </main>
  );
}

export function ConsumptionDataConnectionPage() {
  const navigate = useNavigate();
  const user = useAppSelector((state) => state.auth.user);
  const [flowError, setFlowError] = useState<string | null>(null);
  const [flowMessage, setFlowMessage] = useState<string | null>(null);
  const [createGroup, { isLoading: isCreatingGroup }] = useCreateGroupMutation();
  const [addGroupMember] = useAddGroupMemberMutation();
  const [applyMockScenario, { isLoading: isApplyingMock }] = useApplyMockScenarioMutation();
  const [createAnalysis, { isLoading: isCreatingAnalysis }] = useCreateAnalysisMutation();
  const { data: scenarios = [] } = useListMockScenariosQuery();
  const isLoading = isCreatingGroup || isApplyingMock || isCreatingAnalysis;

  const runDemoAnalysis = async () => {
    if (!user) {
      navigate("/login", { state: { from: { pathname: "/flow/data" } } });
      return;
    }

    const flow = loadFlow();
    setFlowError(null);
    setFlowMessage("모임과 구성원 정보를 준비하는 중입니다.");
    try {
      const group = await createGroup({
        name: flow.goalName || "Mock Insight Group",
        relationship_type: flow.relationshipType,
      }).unwrap();

      for (const member of demoMembers) {
        await addGroupMember({ groupId: group.group_id, body: member }).unwrap();
      }

      setFlowMessage("mock-v2 소비 데이터를 연결하는 중입니다.");
      await applyMockScenario({ groupId: group.group_id, scenarioId: scenarios[0]?.scenario_id ?? "mock-v2" }).unwrap();

      setFlowMessage("규칙 기반 분석과 Qwen 리포트를 생성하는 중입니다.");
      const analysis = await createAnalysis({
        groupId: group.group_id,
        body: { period_start: "2026-05-01", period_end: "2026-07-31" },
      }).unwrap();

      saveFlow({ groupId: group.group_id, analysisId: analysis.analysis_id });
      navigate(`/analysis/loading?analysisId=${analysis.analysis_id}&groupId=${group.group_id}`);
    } catch (error) {
      setFlowError(errorMessage(error));
      setFlowMessage(null);
    }
  };

  return (
    <main className="flow-page">
      <ToastViewport />
      <FlowHeader title="Meeting Personality" backTo="/flow/summary" />
      <FlowProgress step={3} label="Connect" />
      <section className="data-connect-hero">
        <div className="bank-visual">▣</div>
        <h1>우리 모임의 소비 성향 분석</h1>
        <p>카드/계좌 소비 데이터를 바탕으로 우리 모임의 소비 성향을 분석합니다.</p>
      </section>
      <section className="connect-options">
        <button className="connect-primary" disabled type="button">
          <span>내 금융기관 연결하기</span>
          <small>마이데이터 연동은 MVP 제외 범위입니다</small>
        </button>
        <button onClick={runDemoAnalysis} disabled={isLoading} type="button">
          <span>{isLoading ? "mock 데이터 분석 중" : "mock-v2 데이터로 분석하기"}</span>
          <small>완료된 백엔드 분석 API를 사용해 결과까지 생성합니다</small>
        </button>
        <button onClick={() => navigate("/app")} type="button">
          <span>내 모임 대시보드 보기</span>
          <small>이미 생성된 모임과 최신 분석 결과를 확인합니다</small>
        </button>
      </section>
      {flowMessage ? <p className="flow-callout">{flowMessage}</p> : null}
      {flowError ? <p className="flow-callout flow-callout--error">{flowError}</p> : null}
      <p className="privacy-note">데이터는 분석용으로만 사용되며 안전하게 보호됩니다.</p>
    </main>
  );
}

export function AnalysisLoadingPage() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const analysisId = params.get("analysisId") ?? loadFlow().analysisId;
  const { data: analysis, error } = useGetAnalysisQuery(analysisId ?? skipToken, {
    pollingInterval: 2500,
  });

  useEffect(() => {
    if (!analysis) {
      return;
    }
    if (isTerminalAnalysisStatus(analysis.status)) {
      const timer = window.setTimeout(() => {
        navigate(`/analysis/result?analysisId=${analysis.analysis_id}`, { replace: true });
      }, 900);
      return () => window.clearTimeout(timer);
    }
  }, [analysis, navigate]);

  const currentStep = analysisStep(analysis);

  return (
    <main className="flow-page flow-centered">
      <FlowHeader title="Meeting Personality" backTo="/flow/data" />
      <section className="loading-panel">
        <div className="loading-orbit" aria-hidden="true">
          <span />
          <b>MBTI</b>
        </div>
        <h1>{analysis?.status === "FAILED" ? "분석을 완료하지 못했어요" : "데이터를 분석하고 있어요"}</h1>
        <p>{error ? "분석 결과를 불러오지 못했습니다." : loadingCopy(currentStep)}</p>
        <div className="loading-steps">
          {["소비 카테고리 분석", "반복 지출 패턴 추출", "모임 성향 계산", "Qwen 리포트 생성"].map((label, index) => (
            <div className={index < currentStep ? "done" : ""} key={label}>
              <i>{index < currentStep ? "✓" : index + 1}</i>
              <span>{label}</span>
              <small>{index < currentStep ? "완료" : "대기 중"}</small>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}

export function AnalysisResultPage() {
  const [params] = useSearchParams();
  const analysisId = params.get("analysisId") ?? loadFlow().analysisId;
  const groupId = params.get("groupId") ?? loadFlow().groupId;
  const { data: directAnalysis } = useGetAnalysisQuery(analysisId ?? skipToken);
  const { data: latestAnalysis } = useGetLatestGroupAnalysisQuery(groupId ?? skipToken, {
    skip: Boolean(analysisId),
  });
  const analysis = directAnalysis ?? latestAnalysis;

  return (
    <main className="flow-page result-page">
      <FlowHeader title="Meeting Personality" backTo="/app" />
      {analysis ? <ResultContent analysis={analysis} /> : <ResultEmpty />}
    </main>
  );
}

function ResultContent({ analysis }: { analysis: AnalysisResponse }) {
  const report = analysis.ai_report?.report_content;
  const result = analysis.consumption_mbti_result;
  const mbti = result?.mbti_type ?? "보류";
  const topMetrics = analysis.behavior_metrics.filter((metric) => metric.status === "AVAILABLE").slice(0, 4);

  return (
    <>
      <section className="result-hero">
        <span className="flow-badge">{spendingTitle(mbti)}</span>
        <h1>
          우리 모임통장은 <strong>{mbti}형</strong>
        </h1>
        <div className="result-character" aria-hidden="true">
          ✨
        </div>
        <p>{report?.summary ?? "규칙 기반 소비 MBTI와 근거를 바탕으로 만든 분석 결과입니다."}</p>
      </section>
      <section className="axis-card">
        <h2>소비 성향 4대 지표</h2>
        <AxisBar label="EI" left="생활/반복" right="공동/외부" value={result?.axis_scores.EI} />
        <AxisBar label="SN" left="실용/집중" right="다양/경험" value={result?.axis_scores.SN} />
        <AxisBar label="TF" left="목적/효율" right="관계/공감" value={result?.axis_scores.TF} />
        <AxisBar label="JP" left="계획/안정" right="즉흥/변동" value={result?.axis_scores.JP} />
      </section>
      <section className="result-grid">
        {topMetrics.map((metric) => (
          <article key={metric.feature_code}>
            <small>{metric.feature_code}</small>
            <strong>{formatRatio(metric.normalized_score)}</strong>
            <span className="metric-detail">
              표본 {formatInteger(metric.sample_count)}건
              {metric.raw_value === null ? "" : ` · 원값 ${formatMetricValue(metric.raw_value, metric.unit)}`}
            </span>
            <p>{formatEvidenceText(metric.evidence[0] ?? "계산 가능한 근거가 저장되어 있습니다.")}</p>
          </article>
        ))}
      </section>
      <section className="report-card">
        <h2>{report?.headline ?? "Qwen 리포트"}</h2>
        <ListBlock title="강점" items={report?.strengths} />
        <ListBlock title="공통점" items={report?.commonPoints} />
        <ListBlock title="대화 질문" items={report?.conversationQuestions} />
        <p>{report?.disclaimer ?? "이 결과는 실제 성격 진단이나 금융 진단이 아닙니다."}</p>
      </section>
    </>
  );
}

function ResultEmpty() {
  return (
    <section className="result-empty">
      <h1>표시할 분석 결과가 없습니다</h1>
      <p>mock-v2 분석을 먼저 실행하거나, 로그인 후 기존 모임의 최신 분석을 확인해 주세요.</p>
      <Link to="/flow/data">소비 데이터 연결하기</Link>
    </section>
  );
}

function AxisBar({
  label,
  left,
  right,
  value,
}: {
  label: string;
  left: string;
  right: string;
  value: number | string | null | undefined;
}) {
  const percent = ratioNumber(value);
  return (
    <div className="axis-row">
      <div>
        <span>{label}</span>
        <small>{left}</small>
        <small>{right}</small>
      </div>
      <i>
        <b style={{ width: `${percent}%` }} />
      </i>
    </div>
  );
}

function ListBlock({ title, items }: { title: string; items?: string[] }) {
  if (!items?.length) {
    return null;
  }
  return (
    <div>
      <h3>{title}</h3>
      <ul>
        {items.slice(0, 3).map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function FlowHeader({ title, backTo = "/" }: { title: string; backTo?: string }) {
  return (
    <header className="flow-header">
      <Link aria-label="이전으로" to={backTo}>
        ‹
      </Link>
      <strong>{title}</strong>
      <span />
    </header>
  );
}

function FlowProgress({ step, label }: { step: number; label: string }) {
  return (
    <div className="flow-progress">
      <div>
        <span>Step {step} of 4</span>
        <span>{label}</span>
      </div>
      <i>
        <b style={{ width: `${step * 25}%` }} />
      </i>
    </div>
  );
}

function FlowBottomAction({
  label,
  helper,
  onClick,
}: {
  label: string;
  helper?: string;
  onClick: () => void;
}) {
  return (
    <div className="flow-bottom-action">
      <button onClick={onClick} type="button">
        {label}
      </button>
      {helper ? <p>{helper}</p> : null}
    </div>
  );
}

function FormField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="flow-field">
      <span>{label}</span>
      {children}
    </label>
  );
}

function loadFlow(): FlowState {
  const raw = window.sessionStorage.getItem(flowStorageKey);
  if (!raw) {
    return defaultFlow;
  }
  try {
    return { ...defaultFlow, ...(JSON.parse(raw) as Partial<FlowState>) };
  } catch {
    return defaultFlow;
  }
}

function saveFlow(patch: Partial<FlowState>) {
  const next = { ...loadFlow(), ...patch };
  window.sessionStorage.setItem(flowStorageKey, JSON.stringify(next));
}

function formatWon(value: string): string {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return value;
  }
  return `${formatInteger(numeric)}원`;
}

function formatRatio(value: number | string | null | undefined): string {
  if (value === null || value === undefined) {
    return "-";
  }
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return String(value);
  }
  return `${formatDecimal(numeric * 100, 1)}%`;
}

function formatMetricValue(value: number | string, unit: string): string {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return String(value);
  }
  if (unit.includes("RATIO")) {
    return `${formatDecimal(numeric * 100, 1)}%`;
  }
  return formatDecimal(numeric, 2);
}

function formatEvidenceText(value: string): string {
  return value.replace(/\b\d{4,}(?:\.\d+)?\b/g, (match) => {
    const numeric = Number(match);
    if (!Number.isFinite(numeric)) {
      return match;
    }
    return numeric.toLocaleString("ko-KR", {
      maximumFractionDigits: match.includes(".") ? 2 : 0,
    });
  });
}

function formatInteger(value: number): string {
  return value.toLocaleString("ko-KR", { maximumFractionDigits: 0 });
}

function formatDecimal(value: number, maximumFractionDigits: number): string {
  return value.toLocaleString("ko-KR", {
    maximumFractionDigits,
    minimumFractionDigits: 0,
  });
}

function ratioNumber(value: number | string | null | undefined): number {
  const numeric = Number(value ?? 0);
  if (!Number.isFinite(numeric)) {
    return 0;
  }
  return Math.max(0, Math.min(100, Math.round(numeric * 100)));
}

function loadingCopy(step: number): string {
  const copies = [
    "소비 카테고리를 분류하는 중...",
    "반복 지출 패턴을 추출하는 중...",
    "개인 MBTI와 소비 패턴을 비교하는 중...",
    "근거 기반 Qwen 리포트를 정리하는 중...",
  ];
  return copies[Math.min(step, copies.length - 1)];
}

function isTerminalAnalysisStatus(status: AnalysisRunStatus): boolean {
  return ["COMPLETED", "COMPLETED_WITH_FALLBACK", "PARTIALLY_COMPLETED", "FAILED"].includes(status);
}

function analysisStep(analysis: AnalysisResponse | undefined): number {
  if (!analysis) {
    return 1;
  }
  if (isTerminalAnalysisStatus(analysis.status)) {
    return 4;
  }
  if (analysis.status === "REPORT_GENERATING" || analysis.consumption_mbti_result) {
    return 3;
  }
  if (analysis.status === "ANALYZING" || analysis.behavior_metrics.length > 0) {
    return 2;
  }
  return 1;
}

function spendingTitle(mbti: string): string {
  if (mbti === "보류") {
    return "Insufficient Data";
  }
  return "Experience Expansion Creator";
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
  return "요청을 처리하지 못했습니다. 로그인 상태와 백엔드 실행 상태를 확인해 주세요.";
}
