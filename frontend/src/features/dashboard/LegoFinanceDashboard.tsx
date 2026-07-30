import type { ReactNode } from "react";

const tendencyScores = [
  { label: "계획 중심", value: 92 },
  { label: "저축 성향", value: 71 },
  { label: "관계 중심", value: 38 },
  { label: "탐험 성향", value: 15 },
];

const insights = [
  { marker: "01", text: "계획적인 소비 패턴이 매우 안정적으로 유지되고 있어요." },
  { marker: "02", text: "공동 목표에 도움이 되는 소비가 전체의 62%를 차지해요." },
  { marker: "03", text: "소액 즉흥 지출을 줄이면 목표 달성 속도가 더 빨라져요." },
];

const products = [
  { title: "여행 적금 상품", label: "목표 매칭", match: 94, accent: "suitcase" },
  { title: "자동 저축 서비스", label: "목표 매칭", match: 91, accent: "robot" },
];

const similarDna = [
  { name: "ESTJ", match: 91, color: "blue", person: "김" },
  { name: "ISTJ", match: 84, color: "red", person: "이" },
  { name: "ENTJ", match: 78, color: "yellow", person: "박" },
];

interface LegoFinanceDashboardProps {
  mode?: "preview" | "app";
  displayName?: string;
  onLogout?: () => void;
  isLoggingOut?: boolean;
}

function Studs({ count = 8 }: { count?: number }) {
  return (
    <div className="stud-row" aria-hidden="true">
      {Array.from({ length: count }).map((_, index) => (
        <span className="stud" key={index} />
      ))}
    </div>
  );
}

function Block({
  children,
  className,
  studs = 5,
}: {
  children: ReactNode;
  className: string;
  studs?: number;
}) {
  return (
    <section className={`lego-block ${className}`}>
      <Studs count={studs} />
      <div className="block-face">{children}</div>
    </section>
  );
}

export function LegoFinanceDashboard({
  mode = "preview",
  displayName,
  onLogout,
  isLoggingOut = false,
}: LegoFinanceDashboardProps) {
  return (
    <main className="lego-page">
      <div className="phone-canvas">
        <header className="mobile-status" aria-label="상태 영역">
          <strong>9:41</strong>
          <div className="status-icons" aria-hidden="true">
            <span />
            <span />
            <span />
          </div>
        </header>

        <header className="brand-header">
          <div className="brand-lockup">
            <div className="ufc-logo" aria-label="UFC">
              <span>U</span>
              <span>F</span>
              <span>C</span>
            </div>
            <div>
              <h1>Unity Finance Crew</h1>
              <p>함께 쌓아가는 우리들의 금융 여정</p>
            </div>
          </div>
          <nav className="header-actions" aria-label="대시보드 메뉴">
            <button className="icon-button notification-dot" type="button" aria-label="알림">
              <span className="bell-shape" />
            </button>
            {mode === "app" ? (
              <button className="menu-button" disabled={isLoggingOut} onClick={onLogout} type="button">
                로그아웃
              </button>
            ) : (
              <button className="icon-button" type="button" aria-label="메뉴">
                <span className="hamburger-shape" />
              </button>
            )}
          </nav>
        </header>

        {displayName ? <p className="welcome-copy">{displayName}님의 금융 블록이 준비됐어요.</p> : null}

        <Block className="hero-block block-blue" studs={9}>
          <div className="hero-copy">
            <p className="block-label">금융 DNA</p>
            <strong className="dna-type">ESTJ</strong>
            <h2>전략적 소비자</h2>
            <p>계획적이고 효율적으로 목표를 달성하는 타입이에요.</p>
          </div>
          <div className="confidence-ring" aria-label="신뢰도 91퍼센트">
            <div>
              <span>신뢰도</span>
              <strong>91</strong>
              <em>%</em>
            </div>
          </div>
        </Block>

        <div className="dashboard-grid two-column">
          <Block className="block-yellow tendency-block" studs={4}>
            <p className="block-label dark-label">성향 분석</p>
            <div className="score-list">
              {tendencyScores.map((score) => (
                <div className="score-row" key={score.label}>
                  <span>{score.label}</span>
                  <div className="score-track">
                    <span style={{ width: `${score.value}%` }} />
                  </div>
                  <strong>{score.value}%</strong>
                </div>
              ))}
            </div>
          </Block>

          <Block className="block-red insight-block" studs={5}>
            <p className="block-label">AI 인사이트</p>
            <div className="insight-list">
              {insights.map((insight) => (
                <div className="insight-row" key={insight.marker}>
                  <span>{insight.marker}</span>
                  <p>{insight.text}</p>
                </div>
              ))}
            </div>
          </Block>
        </div>

        <Block className="block-green goal-block" studs={9}>
          <div className="goal-heading">
            <div>
              <p className="block-label">목표 빌더</p>
              <h2>일본 여행 <span aria-hidden="true">✈</span></h2>
            </div>
            <div className="goal-progress">
              <strong>72%</strong>
              <span>3,600,000 / 5,000,000 원</span>
            </div>
          </div>
          <div className="brick-progress" aria-label="목표 달성률 72퍼센트">
            {Array.from({ length: 10 }).map((_, index) => (
              <span className={index < 7 ? "filled" : "empty"} key={index} />
            ))}
          </div>
          <p className="goal-date">예상 달성일 2025. 12. 03</p>
        </Block>

        <div className="dashboard-grid two-column suggestion-grid">
          <Block className="block-blue small-suggestion" studs={5}>
            <p className="block-label">최적화 제안</p>
            <div className="suggestion-content">
              <span className="suggestion-icon cup-icon" aria-hidden="true" />
              <div>
                <h2>카페 소비 줄이기</h2>
                <strong>-48,000 원</strong>
                <p>예상 절약 금액</p>
              </div>
            </div>
          </Block>

          <Block className="block-yellow small-suggestion" studs={5}>
            <p className="block-label dark-label">가속 제안</p>
            <div className="suggestion-content dark-text">
              <span className="suggestion-icon coin-icon" aria-hidden="true" />
              <div>
                <h2>월 저축액 늘리기</h2>
                <strong>+50,000 원</strong>
                <p>목표 달성 <mark>12일</mark> 단축</p>
              </div>
            </div>
          </Block>
        </div>

        <div className="dashboard-grid two-column product-grid">
          {products.map((product) => (
            <Block className="block-orange product-block" key={product.title} studs={4}>
              <p className="block-label">추천 금융 상품</p>
              <div className="product-face">
                <span className={`product-icon ${product.accent}`} aria-hidden="true" />
                <div>
                  <h2>{product.title}</h2>
                  <p>{product.label}</p>
                  <strong>{product.match}%</strong>
                </div>
                <button className="round-arrow" type="button" aria-label={`${product.title} 보기`}>
                  →
                </button>
              </div>
            </Block>
          ))}
        </div>

        <section className="similar-strip">
          <Studs count={8} />
          <h2>비슷한 금융 DNA</h2>
          <div className="similar-list">
            {similarDna.map((item) => (
              <article className={`similar-chip ${item.color}`} key={item.name}>
                <span className="avatar">{item.person}</span>
                <div>
                  <strong>{item.name}</strong>
                  <p>{item.match}% 유사도</p>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
