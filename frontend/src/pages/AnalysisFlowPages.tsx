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

const mockScenarioCases = [
  {
    id: "SCN-01",
    title: "여행·경험 확장형",
    expected: "ENFJ",
    summary: "공동 여행, 문화 활동, 계획 지출이 뚜렷해 경험 중심 소비 성향을 보여줍니다.",
  },
  {
    id: "SCN-02",
    title: "생활·반복 안정형",
    expected: "ISTJ",
    summary: "마트, 공과금, 반복 식비 비중이 높아 안정적인 생활 소비를 검증합니다.",
  },
  {
    id: "SCN-03",
    title: "목표 효율 추진형",
    expected: "ENTJ",
    summary: "외부 활동은 많지만 관계성보다 목적성과 효율 지표가 강하게 나타납니다.",
  },
  {
    id: "SCN-04",
    title: "계획 경계 케이스",
    expected: "ENFJ",
    summary: "JP 축 margin이 낮아 계획형과 유연형 경계 해석을 확인하는 케이스입니다.",
  },
  {
    id: "SCN-05",
    title: "균형형 대화 유도 케이스",
    expected: "ENFP",
    summary: "SN, TF 축 margin이 낮아 리포트에서 대화 질문과 한계를 함께 보여주기 좋습니다.",
  },
  {
    id: "SCN-06",
    title: "실속 반복 소비형",
    expected: "ISTJ",
    summary: "반복 가맹점과 실용 지출을 중심으로 보수적인 소비 패턴을 검증합니다.",
  },
  {
    id: "SCN-07",
    title: "탐색형 경계 케이스",
    expected: "INTP",
    summary: "EI 축 margin이 낮아 외부 활동과 개인 지출의 경계 상황을 보여줍니다.",
  },
  {
    id: "SCN-08",
    title: "데이터 부족 예외",
    expected: "보류",
    summary: "거래 8건만 포함되어 전처리에서 분석 불가와 INSUFFICIENT_DATA 처리를 확인합니다.",
  },
];

export function StitchLandingPage() {
  const navigate = useNavigate();
  const user = useAppSelector((state) => state.auth.user);

  return (
    <main className="flow-page flow-landing">
      <FlowHeader actionLabel={user ? "모임 홈" : "로그인"} actionTo={user ? "/app" : "/login"} title="Meeting Personality" />
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
      <FlowBottomAction
        label="분석 시작하기"
        onClick={() => navigate("/onboarding")}
        secondaryLabel={user ? "기존 모임 홈 보기" : "로그인해서 모임 보기"}
        secondaryTo={user ? "/app" : "/login"}
      />
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
      <FlowBottomAction
        label="소비 데이터 연결하기"
        helper="기존 모임은 모임 홈에서 바로 확인할 수 있어요"
        onClick={() => navigate("/flow/data")}
        secondaryLabel="모임 홈 보기"
        secondaryTo="/app"
      />
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

      saveFlow({ groupId: group.group_id });
      setFlowMessage("규칙 기반 분석과 Qwen 리포트를 생성하는 중입니다.");
      window.setTimeout(() => {
        navigate(`/analysis/loading?groupId=${group.group_id}`);
      }, 150);
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
      <section className="mock-scenario-panel" aria-label="Mock 검증 시나리오">
        <div className="result-section-heading">
          <span>mock-v2 검증 데이터</span>
          <h2>대표 시나리오를 기준으로 리포트를 확인해요</h2>
        </div>
        <div className="mock-scenario-featured">
          <span>현재 데모 적용</span>
          <strong>SCN-01 · 여행·경험 확장형</strong>
          <p>
            백엔드 mock apply API는 현재 `mock-v2`의 대표 그룹 데이터를 적용합니다. 이 흐름에서는
            여행·경험 소비와 공동 지출 근거가 선명하게 드러나는 결과 리포트를 확인할 수 있습니다.
          </p>
        </div>
        <div className="mock-scenario-grid">
          {mockScenarioCases.map((scenario) => (
            <article key={scenario.id}>
              <small>{scenario.id}</small>
              <strong>{scenario.expected}</strong>
              <span>{scenario.title}</span>
              <p>{scenario.summary}</p>
            </article>
          ))}
        </div>
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
  const groupId = params.get("groupId") ?? loadFlow().groupId;
  const { data: analysis, error } = useGetAnalysisQuery(analysisId ?? skipToken, {
    pollingInterval: 2500,
  });
  const { data: latestAnalysis } = useGetLatestGroupAnalysisQuery(groupId ?? skipToken, {
    pollingInterval: 2500,
    skip: Boolean(analysisId),
  });
  const visibleAnalysis = analysis ?? latestAnalysis;

  useEffect(() => {
    if (!visibleAnalysis) {
      return;
    }
    if (isTerminalAnalysisStatus(visibleAnalysis.status)) {
      const timer = window.setTimeout(() => {
        navigate(`/analysis/result?analysisId=${visibleAnalysis.analysis_id}`, { replace: true });
      }, 900);
      return () => window.clearTimeout(timer);
    }
  }, [visibleAnalysis, navigate]);

  const currentStep = analysisStep(visibleAnalysis);

  return (
    <main className="flow-page flow-centered">
      <FlowHeader title="Meeting Personality" backTo="/flow/data" />
      <section className="loading-panel">
        <div className="loading-orbit" aria-hidden="true">
          <span />
          <b>MBTI</b>
        </div>
        <h1>{visibleAnalysis?.status === "FAILED" ? "분석을 완료하지 못했어요" : "데이터를 분석하고 있어요"}</h1>
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
  const result = analysis.consumption_mbti_result;
  const mbti = result?.mbti_type ?? "보류";
  const availableMetrics = analysis.behavior_metrics.filter((metric) => metric.status === "AVAILABLE");
  const topMetrics = availableMetrics.slice(0, 4);
  const report = buildDisplayReport(analysis, topMetrics);
  const axisInsights = buildAxisInsights(result);
  const evidenceCards = buildEvidenceCards(analysis, availableMetrics).slice(0, 4);
  const limitations = buildLimitations(analysis);

  return (
    <>
      <nav className="result-actions" aria-label="결과 화면 이동">
        <Link to="/app">모임 홈</Link>
        <Link to="/flow/data">다시 분석</Link>
        <Link to="/settings">설정</Link>
      </nav>
      <section className="result-hero">
        <span className="flow-badge">{resultStatusLabel(analysis.result_status)}</span>
        <h1>
          우리 모임통장은 <strong>{mbti}형</strong>
        </h1>
        <div className="result-character" aria-hidden="true">
          {resultIcon(mbti)}
        </div>
        <strong className="result-title">{spendingTitle(mbti)}</strong>
        <p>{report.summary}</p>
      </section>
      <section className="result-stat-grid" aria-label="분석 신뢰도 요약">
        <ResultStatCard label="신뢰도" value={formatRatio(result?.confidence.score)} caption={confidenceLabel(result?.confidence.level)} />
        <ResultStatCard label="데이터 커버리지" value={formatRatio(result?.coverage)} caption="계산 가능 지표 기준" />
        <ResultStatCard label="분석 표본" value={`${formatInteger(totalSampleCount(availableMetrics))}건`} caption={sourceLabel(analysis)} />
      </section>
      {analysis.is_synthetic ? <MockScenarioResultCard analysis={analysis} /> : null}
      <section className="axis-card">
        <h2>소비 성향 4대 지표</h2>
        {axisInsights.map((axis) => (
          <AxisBar key={axis.label} {...axis} />
        ))}
      </section>
      <section className="evidence-section">
        <div className="result-section-heading">
          <span>핵심 근거</span>
          <h2>왜 이런 결과가 나왔나요?</h2>
        </div>
        <div className="result-grid">
          {evidenceCards.map((metric, index) => (
            <EvidenceCard key={`${metric.code}-${index}`} item={metric} />
          ))}
        </div>
      </section>
      <section className="report-card report-card--featured">
        <h2>{report.headline}</h2>
        <p className="report-lead">{report.summary}</p>
        <div className="report-columns">
          <ListBlock title="잘 맞는 소비 흐름" items={report.strengths} />
          <ListBlock title="함께 이야기할 지점" items={report.commonPoints} />
          <ListBlock title="다르게 볼 수 있는 부분" items={report.differences} />
          <ListBlock title="관찰 포인트" items={report.observationPoints} />
        </div>
      </section>
      <section className="report-card">
        <h2>다음 모임에서 던져볼 질문</h2>
        <div className="question-stack">
          {report.conversationQuestions.map((question) => (
            <p key={question}>{question}</p>
          ))}
        </div>
      </section>
      {limitations.length ? (
        <section className="report-card report-card--muted">
          <h2>해석할 때 참고할 점</h2>
          <ul>
            {limitations.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
          <p>{report.disclaimer}</p>
        </section>
      ) : (
        <section className="report-card report-card--muted">
          <p>{report.disclaimer}</p>
        </section>
      )}
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
  selected,
  coverage,
  margin,
}: {
  label: string;
  left: string;
  right: string;
  value: number | string | null | undefined;
  selected?: string;
  coverage?: number | string | null;
  margin?: number | string | null;
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
      <p>
        <strong>{selected ?? "판정 보류"}</strong>
        <span>
          점수 {formatRatio(value)} · 커버리지 {formatRatio(coverage)} · 차이 {formatAxisMargin(margin)}
        </span>
      </p>
    </div>
  );
}

function ResultStatCard({ label, value, caption }: { label: string; value: string; caption: string }) {
  return (
    <article className="result-stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
      <small>{caption}</small>
    </article>
  );
}

function MockScenarioResultCard({ analysis }: { analysis: AnalysisResponse }) {
  const scenario = scenarioForAnalysis(analysis);
  return (
    <section className="mock-result-card" aria-label="Mock 시나리오 해석">
      <div>
        <span>Mock 리포트 케이스</span>
        <strong>{scenario.id}</strong>
      </div>
      <h2>{scenario.title}</h2>
      <p>{scenario.summary}</p>
      <small>
        현재 백엔드는 `mock-v2` 단일 apply API를 제공합니다. 개별 SCN 선택은 API가 추가되면 프론트에서 바로 연결할 수 있습니다.
      </small>
    </section>
  );
}

interface EvidenceCardItem {
  code: string;
  title: string;
  value: string;
  caption: string;
  body: string;
  tone: "blue" | "red" | "green" | "yellow";
}

function EvidenceCard({ item }: { item: EvidenceCardItem }) {
  return (
    <article className={`evidence-card evidence-card--${item.tone}`}>
      <small>{item.caption}</small>
      <strong>{item.value}</strong>
      <h3>{item.title}</h3>
      <p>{item.body}</p>
    </article>
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

interface DisplayReport {
  headline: string;
  summary: string;
  strengths: string[];
  commonPoints: string[];
  differences: string[];
  observationPoints: string[];
  conversationQuestions: string[];
  disclaimer: string;
}

function buildDisplayReport(
  analysis: AnalysisResponse,
  metrics: AnalysisResponse["behavior_metrics"],
): DisplayReport {
  const content = analysis.ai_report?.report_content;
  const mbti = analysis.consumption_mbti_result?.mbti_type;
  const confidence = formatRatio(analysis.consumption_mbti_result?.confidence.score);
  const evidence = metrics.map((metric) => formatEvidenceText(metric.evidence[0] ?? metric.feature_code));
  const fallbackSummary = `${mbti ?? "보류"}형 소비 패턴은 계산 가능한 거래 근거를 바탕으로 산출됐습니다. 신뢰도는 ${confidence}이며, 현재 결과는 모임의 대화와 회고를 돕기 위한 참고용 인사이트입니다.`;

  return {
    headline: readableKorean(content?.headline) ?? `${mbti ?? "소비 성향"} 리포트`,
    summary: readableKorean(content?.summary) ?? fallbackSummary,
    strengths: koreanList(content?.strengths, [
      "공동 지출과 반복 지출의 균형을 기준으로 모임의 소비 방향이 비교적 선명하게 드러납니다.",
      evidence[0] ? `핵심 근거: ${evidence[0]}` : "계산 가능한 Feature만 사용해 결과를 산출했습니다.",
    ]),
    commonPoints: koreanList(content?.commonPoints, [
      "개인 MBTI는 참고 정보로만 사용하고, 소비 MBTI는 거래 패턴과 규칙 엔진 결과로 분리해 판단했습니다.",
      evidence[1] ? `보조 근거: ${evidence[1]}` : "데이터가 부족한 항목은 임의로 점수화하지 않았습니다.",
    ]),
    differences: koreanList(content?.differences, [
      "구성원별 성격 정보는 참고 요약으로만 사용되므로, 실제 의사결정은 모임 안에서 다시 확인하는 편이 좋습니다.",
      "특정 지표의 표본이 적으면 해당 축의 해석 강도가 낮아질 수 있습니다.",
    ]),
    observationPoints: koreanList(content?.observationPoints, [
      "다음 분석에서는 같은 기간의 반복 지출과 신규 지출 비중이 어떻게 변하는지 비교해보면 좋습니다.",
      "공동 지출과 개인 성향 지출이 섞이는 항목은 모임 규칙을 먼저 정하면 결과 해석이 쉬워집니다.",
    ]),
    conversationQuestions: koreanList(content?.conversationQuestions, [
      "이번 결과가 실제 모임의 소비 분위기와 어느 정도 맞는지 함께 이야기해보면 좋겠습니다.",
    ]),
    disclaimer:
      readableKorean(content?.disclaimer) ??
      "이 리포트는 실제 성격 진단이나 금융 진단이 아니며, 금융상품 추천 또는 신용 평가 목적으로 사용할 수 없습니다.",
  };
}

function koreanList(value: unknown, fallback: string[]): string[] {
  if (!Array.isArray(value)) {
    return fallback;
  }
  const readable = value.map((item) => readableKorean(item)).filter((item): item is string => Boolean(item));
  return readable.length ? readable : fallback;
}

function readableKorean(value: unknown): string | null {
  if (typeof value !== "string") {
    return null;
  }
  const normalized = value.trim();
  if (!normalized || /[A-Za-z]{4,}/.test(normalized)) {
    return null;
  }
  return formatEvidenceText(normalized);
}

interface AxisInsight {
  label: "EI" | "SN" | "TF" | "JP";
  left: string;
  right: string;
  value: number | string | null | undefined;
  selected: string;
  coverage: number | string | null;
  margin: number | string | null;
}

function buildAxisInsights(result: AnalysisResponse["consumption_mbti_result"]): AxisInsight[] {
  const coverage = recordFromMetadata(result?.metadata, "axisCoverage");
  const margins = recordFromMetadata(result?.metadata, "axisMargins");
  return [
    {
      label: "EI",
      left: "생활·반복",
      right: "공동·외부",
      value: result?.axis_scores.EI,
      selected: axisDecision("EI", result?.axis_scores.EI),
      coverage: valueFromRecord(coverage, "EI"),
      margin: valueFromRecord(margins, "EI"),
    },
    {
      label: "SN",
      left: "실용·집중",
      right: "다양·경험",
      value: result?.axis_scores.SN,
      selected: axisDecision("SN", result?.axis_scores.SN),
      coverage: valueFromRecord(coverage, "SN"),
      margin: valueFromRecord(margins, "SN"),
    },
    {
      label: "TF",
      left: "목적·효율",
      right: "관계·공감",
      value: result?.axis_scores.TF,
      selected: axisDecision("TF", result?.axis_scores.TF),
      coverage: valueFromRecord(coverage, "TF"),
      margin: valueFromRecord(margins, "TF"),
    },
    {
      label: "JP",
      left: "계획·안정",
      right: "즉흥·유연",
      value: result?.axis_scores.JP,
      selected: axisDecision("JP", result?.axis_scores.JP),
      coverage: valueFromRecord(coverage, "JP"),
      margin: valueFromRecord(margins, "JP"),
    },
  ];
}

function buildEvidenceCards(
  analysis: AnalysisResponse,
  metrics: AnalysisResponse["behavior_metrics"],
): EvidenceCardItem[] {
  const primaryEvidence = arrayFromMetadata(analysis.consumption_mbti_result?.metadata, "primaryEvidence")
    .map((item, index) => evidenceFromPrimary(item, index))
    .filter((item): item is EvidenceCardItem => Boolean(item));

  if (primaryEvidence.length) {
    return primaryEvidence;
  }

  return metrics.map((metric, index) => ({
    code: metric.feature_code,
    title: metricLabel(metric.feature_code),
    value: formatMetricValue(metric.normalized_score ?? metric.raw_value ?? "-", metric.unit),
    caption: `${featureGroupLabel(metric.feature_code)} · 표본 ${formatInteger(metric.sample_count)}건`,
    body: metric.evidence[0]
      ? userEvidenceText(metric.evidence[0], metric.feature_code)
      : `${metricLabel(metric.feature_code)} 지표가 이번 결과의 주요 근거로 사용됐습니다.`,
    tone: evidenceTone(metric.feature_code, index),
  }));
}

function evidenceFromPrimary(item: unknown, index: number): EvidenceCardItem | null {
  if (!isRecord(item)) {
    return null;
  }
  const code = stringValue(item.featureCode) ?? stringValue(item.metric) ?? stringValue(item.feature_code) ?? "PRIMARY_EVIDENCE";
  const axis = stringValue(item.axis);
  const score = numberish(item.featureScore) ?? numberish(item.contributionScore) ?? numberish(item.contribution);
  const evidence = Array.isArray(item.evidence) ? stringValue(item.evidence[0]) : stringValue(item.evidence);

  return {
    code,
    title: metricLabel(code),
    value: score === null ? "-" : formatRatio(score),
    caption: axis ? `${axisLabel(axis)} 핵심 근거` : featureGroupLabel(code),
    body: evidence ? userEvidenceText(evidence, code) : `${metricLabel(code)} 지표가 축 판정에 가장 크게 기여했습니다.`,
    tone: evidenceTone(code, index),
  };
}

function buildLimitations(analysis: AnalysisResponse): string[] {
  const items = [
    ...analysis.provisional_reasons.map(readableReason),
    ...(analysis.consumption_mbti_result?.limitations ?? []).map(readableReason),
  ];
  if (analysis.is_synthetic) {
    items.push("현재 결과는 Mock 데이터 기반이므로 실제 모임 소비와 다를 수 있습니다.");
  }
  if (analysis.ai_report?.fallback_used) {
    items.push("Qwen 리포트 생성이 실패해 검증된 템플릿 문장으로 대체된 항목이 있습니다.");
  }
  return Array.from(new Set(items.filter(Boolean)));
}

function scenarioForAnalysis(analysis: AnalysisResponse): (typeof mockScenarioCases)[number] {
  const mbti = analysis.consumption_mbti_result?.mbti_type;
  if (analysis.result_status === "INSUFFICIENT_DATA" || !mbti) {
    return mockScenarioCases[7];
  }
  return (
    mockScenarioCases.find((scenario) => scenario.expected === mbti) ??
    mockScenarioCases[0]
  );
}

function recordFromMetadata(metadata: Record<string, unknown> | undefined, key: string): Record<string, unknown> {
  const value = metadata?.[key];
  return isRecord(value) ? value : {};
}

function arrayFromMetadata(metadata: Record<string, unknown> | undefined, key: string): unknown[] {
  const value = metadata?.[key];
  return Array.isArray(value) ? value : [];
}

function valueFromRecord(record: Record<string, unknown>, key: string): number | string | null {
  const value = record[key];
  if (typeof value === "number" || typeof value === "string") {
    return value;
  }
  return null;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value.trim() : null;
}

function numberish(value: unknown): number | null {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : null;
}

function axisDecision(axis: AxisInsight["label"], value: number | string | null | undefined): string {
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "판정 보류";
  }
  const high = {
    EI: "공동·외부 활동형",
    SN: "다양·경험 탐색형",
    TF: "관계·공감 지향형",
    JP: "즉흥·유연 소비형",
  };
  const low = {
    EI: "생활·반복 안정형",
    SN: "실용·집중 소비형",
    TF: "목적·효율 지향형",
    JP: "계획·안정 소비형",
  };
  return numeric >= 0.5 ? high[axis] : low[axis];
}

function axisLabel(axis: string): string {
  const labels: Record<string, string> = {
    EI: "E/I 축",
    SN: "S/N 축",
    TF: "T/F 축",
    JP: "J/P 축",
  };
  return labels[axis] ?? axis;
}

function metricLabel(code: string): string {
  const labels: Record<string, string> = {
    SHARED_EXPENSE_RATIO: "공동 지출 비중",
    WEEKEND_SOCIAL_SPENDING_RATIO: "주말 사회적 소비",
    NIGHT_SPENDING_RATIO: "야간 소비 비중",
    TRAVEL_EXPERIENCE_RATIO: "여행·경험 지출",
    PRACTICAL_SPENDING_RATIO: "실용 소비 비중",
    CATEGORY_CONCENTRATION: "카테고리 집중도",
    CATEGORY_DIVERSITY_SCORE: "카테고리 다양성",
    NEW_MERCHANT_RATIO: "신규 가맹점 비중",
    REPEAT_MERCHANT_RATIO: "반복 가맹점 비중",
    EXPERIENCE_SPENDING_RATIO: "경험 소비 비중",
    SAVING_EDUCATION_RATIO: "저축·교육 비중",
    RELATIONSHIP_SPENDING_RATIO: "관계 소비 비중",
    SHARED_EXPERIENCE_RATIO: "공동 경험 소비",
    GIFT_ANNIVERSARY_RATIO: "선물·기념일 소비",
    PLANNED_EXPENSE_RATIO: "계획 지출 비중",
    RECURRING_EXPENSE_RATIO: "반복 지출 비중",
    WEEKLY_EXPENSE_VOLATILITY: "주간 지출 변동성",
    OUTLIER_RATIO: "특이 지출 비중",
  };
  return labels[code] ?? code.replace(/_/g, " ").toLowerCase();
}

function featureGroupLabel(code: string): string {
  if (code.includes("SHARED") || code.includes("WEEKEND") || code.includes("NIGHT")) {
    return "활동 패턴";
  }
  if (code.includes("CATEGORY") || code.includes("MERCHANT") || code.includes("EXPERIENCE") || code.includes("TRAVEL")) {
    return "소비 다양성";
  }
  if (code.includes("PLANNED") || code.includes("RECURRING") || code.includes("VOLATILITY") || code.includes("OUTLIER")) {
    return "계획성";
  }
  return "소비 목적";
}

function evidenceTone(code: string, index: number): EvidenceCardItem["tone"] {
  if (code.includes("WEEKEND") || code.includes("RELATIONSHIP") || code.includes("GIFT")) {
    return "red";
  }
  if (code.includes("NIGHT") || code.includes("REPEAT") || code.includes("RECURRING")) {
    return "green";
  }
  if (code.includes("TRAVEL") || code.includes("EXPERIENCE") || code.includes("CATEGORY")) {
    return "yellow";
  }
  return (["blue", "red", "green", "yellow"] as const)[index % 4];
}

function userEvidenceText(value: string, code: string): string {
  const parsed = value.match(/^.+?:\s*([\d,.]+)\s+of\s+([\d,.]+)\s+amount,\s*([\d.]+)%\./);
  if (parsed) {
    const amount = formatWonNumber(parsed[1]);
    const total = formatWonNumber(parsed[2]);
    return `${metricLabel(code)}은 전체 지출 ${total} 중 ${amount}으로, 비중은 ${parsed[3]}%입니다.`;
  }
  return formatEvidenceText(value);
}

function readableReason(value: string): string {
  const labels: Record<string, string> = {
    SYNTHETIC_DATA: "Mock 데이터 기반 결과입니다.",
    INSUFFICIENT_DATA: "일부 지표는 표본이 부족해 해석 강도가 낮습니다.",
    INSUFFICIENT_SAMPLE: "일부 지표는 최소 거래 건수를 충족하지 못했습니다.",
    LOW_COVERAGE: "계산 가능한 Feature 커버리지가 낮아 결과를 참고용으로 봐야 합니다.",
  };
  return labels[value] ?? value.replace(/_/g, " ").toLowerCase();
}

function sourceLabel(analysis: AnalysisResponse): string {
  if (analysis.is_synthetic || analysis.source_type === "MOCK" || analysis.source_type === "INTERNAL_TEST") {
    return "Mock 데이터 기준";
  }
  if (analysis.source_type === "CSV") {
    return "CSV 업로드 기준";
  }
  return "직접 입력 데이터 기준";
}

function confidenceLabel(level: string | undefined): string {
  const labels: Record<string, string> = {
    HIGH: "높은 신뢰도",
    MEDIUM: "보통 신뢰도",
    LOW: "낮은 신뢰도",
  };
  return level ? (labels[level] ?? level) : "신뢰도 미정";
}

function resultStatusLabel(status: AnalysisResponse["result_status"]): string {
  const labels: Record<string, string> = {
    STANDARD: "표준 분석",
    PROVISIONAL: "참고용 분석",
    INSUFFICIENT_DATA: "데이터 부족",
  };
  return status ? labels[status] : "결과 상태 확인 중";
}

function totalSampleCount(metrics: AnalysisResponse["behavior_metrics"]): number {
  return metrics.reduce((sum, metric) => Math.max(sum, metric.sample_count), 0);
}

function formatAxisMargin(value: number | string | null | undefined): string {
  if (value === null || value === undefined) {
    return "-";
  }
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return String(value);
  }
  return `${formatDecimal(Math.abs(numeric) * 100, 1)}p`;
}

function FlowHeader({
  title,
  backTo = "/",
  actionLabel,
  actionTo,
}: {
  title: string;
  backTo?: string;
  actionLabel?: string;
  actionTo?: string;
}) {
  return (
    <header className="flow-header">
      <Link aria-label="이전으로" to={backTo}>
        ‹
      </Link>
      <strong>{title}</strong>
      {actionLabel && actionTo ? (
        <Link className="flow-header-action" to={actionTo}>
          {actionLabel}
        </Link>
      ) : (
        <span />
      )}
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
  secondaryLabel,
  secondaryTo,
}: {
  label: string;
  helper?: string;
  onClick: () => void;
  secondaryLabel?: string;
  secondaryTo?: string;
}) {
  return (
    <div className="flow-bottom-action">
      <button onClick={onClick} type="button">
        {label}
      </button>
      {secondaryLabel && secondaryTo ? <Link to={secondaryTo}>{secondaryLabel}</Link> : null}
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

function formatWonNumber(value: string): string {
  const numeric = Number(value.replace(/,/g, ""));
  if (!Number.isFinite(numeric)) {
    return `${value}원`;
  }
  return `${numeric.toLocaleString("ko-KR", { maximumFractionDigits: 0 })}원`;
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
    return "데이터 보강이 필요한 분석";
  }
  return "함께 쓰는 경험 확장형 소비";
}

function resultIcon(mbti: string): string {
  if (mbti === "보류") {
    return "⌛";
  }
  const fourth = mbti[3];
  if (fourth === "J") {
    return "📊";
  }
  if (fourth === "P") {
    return "🧭";
  }
  return "💳";
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
