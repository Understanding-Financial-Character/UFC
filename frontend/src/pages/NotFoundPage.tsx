import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <main className="auth-page">
      <section className="auth-panel" aria-labelledby="not-found-title">
        <p className="eyebrow">404</p>
        <h1 id="not-found-title">화면을 찾을 수 없습니다</h1>
        <Link className="button-link" to="/app">
          앱으로 돌아가기
        </Link>
      </section>
    </main>
  );
}
