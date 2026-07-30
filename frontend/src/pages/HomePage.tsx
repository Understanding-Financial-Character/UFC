import { Link, useNavigate } from "react-router-dom";

import {
  useListCategoriesQuery,
  useListGroupsQuery,
  useListMockScenariosQuery,
  useLogoutMutation,
} from "../api/baseApi";
import { useAppSelector } from "../app/hooks";
import { ToastViewport } from "../components/feedback/ToastViewport";

interface HomePageProps {
  variant?: "user" | "admin";
}

const demoCredential = {
  email: "demo-user@example.com",
  password: "correct-password",
};

export function HomePage({ variant = "user" }: HomePageProps) {
  const navigate = useNavigate();
  const user = useAppSelector((state) => state.auth.user);
  const [logout, { isLoading: isLoggingOut }] = useLogoutMutation();
  const { data: mockScenarios = [], isLoading: isMockLoading } = useListMockScenariosQuery();
  const { data: categories = [], isLoading: isCategoryLoading } = useListCategoriesQuery();
  const { data: groups = [], isLoading: isGroupLoading } = useListGroupsQuery(undefined, {
    skip: !user,
  });

  const onLogout = async () => {
    await logout().unwrap().catch(() => undefined);
    navigate("/login", { replace: true });
  };

  const readyGroups = groups.filter((group) => group.can_analyze).length;
  const primaryScenario = mockScenarios[0];
  const categoryCount = categories.length;

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
          <a href="#profile">프로필</a>
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
          ? groups.slice(0, 4).map((group, index) => (
              <MeetingCard
                key={group.group_id}
                icon={["T", "W", "F", "O"][index % 4]}
                name={group.name}
                relationship={relationshipLabel(group.relationship_type)}
                mbti={group.can_analyze ? "분석 가능" : "준비 중"}
                progress={group.can_analyze ? 100 : Math.min(group.member_count * 25, 75)}
                goal={`${group.member_count}/4명 구성`}
                highlighted={index === 1}
              />
            ))
          : demoMeetings.map((meeting) => <MeetingCard key={meeting.name} {...meeting} />)}
      </section>

      <section className="landing-insights" id="insights">
        <article className="insight-panel">
          <div className="section-title">
            <span aria-hidden="true">◆</span>
            <h2>소비 성향 분석 인사이트</h2>
          </div>
          {user ? (
            <p>
              현재 계정은 {groups.length}개 모임을 가지고 있고, 그중 {readyGroups}개 모임이 분석 준비 상태입니다.
              BE Phase 6 분석 실행 API가 연결되면 이 영역에서 실제 소비 MBTI와 Qwen 리포트를 표시합니다.
            </p>
          ) : (
            <p>
              UFC는 2~4인 모임통장 소비 데이터를 바탕으로 규칙 기반 소비 MBTI와 근거 요약을 보여주는
              MVP입니다. 실제 성격 진단이나 금융 진단이 아니라, 모임 대화를 돕는 설명형 분석입니다.
            </p>
          )}
          <div className="insight-score" aria-label="예시 소비 MBTI">
            <span>ESTJ</span>
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

      <Link className="floating-action" to={user ? "/app" : "/signup"} aria-label="새 모임 만들기">
        +
      </Link>
      <MobileNav />
    </main>
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
}

function MeetingCard({ icon, name, relationship, mbti, progress, goal, highlighted }: MeetingCardProps) {
  return (
    <article className={`meeting-card-ui${highlighted ? " meeting-card-ui--highlighted" : ""}`}>
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
      <footer>
        <div>
          <span>목표 정보</span>
          <strong>{goal}</strong>
        </div>
        <button aria-label={`${name} 자세히 보기`} type="button">
          ›
        </button>
      </footer>
    </article>
  );
}

function MobileNav() {
  return (
    <nav className="mobile-nav" aria-label="모바일 메뉴">
      <a href="#explore">탐색</a>
      <a className="active" href="#groups">
        모임
      </a>
      <a href="#insights">트렌드</a>
      <a href="#profile">프로필</a>
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
