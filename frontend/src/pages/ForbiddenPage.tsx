import { Link } from "react-router-dom";

export function ForbiddenPage() {
  return (
    <main className="auth-page">
      <section className="auth-panel" aria-labelledby="forbidden-title">
        <p className="eyebrow">403</p>
        <h1 id="forbidden-title">접근 권한이 없습니다</h1>
        <p>현재 계정으로는 이 화면을 볼 수 없습니다.</p>
        <Link className="button-link" to="/app">
          앱으로 돌아가기
        </Link>
      </section>
    </main>
  );
}
