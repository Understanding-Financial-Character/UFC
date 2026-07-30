import type { FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useLazyGetMeQuery, useLoginMutation } from "../api/baseApi";
import { ErrorState } from "../components/feedback/ErrorState";
import { ToastViewport } from "../components/feedback/ToastViewport";
import { getAuthErrorMessage } from "../features/auth/errorMessage";

type LocationState = {
  from?: { pathname?: string };
};

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const [login, { error, isLoading }] = useLoginMutation();
  const [loadSession, { isFetching: isSessionLoading }] = useLazyGetMeQuery();
  const isSubmitting = isLoading || isSessionLoading;

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await login({
      email: String(form.get("email") ?? ""),
      password: String(form.get("password") ?? ""),
    }).unwrap();
    await loadSession().unwrap();
    const state = location.state as LocationState | null;
    navigate(state?.from?.pathname ?? "/app", { replace: true });
  };

  return (
    <main className="login-page">
      <ToastViewport />
      <div className="login-shell">
        <header className="login-brand" aria-labelledby="login-title">
          <div className="login-brand-icon" aria-hidden="true">
            <span className="login-brand-dot login-brand-dot--left" />
            <span className="login-brand-dot login-brand-dot--center" />
            <span className="login-brand-dot login-brand-dot--right" />
            <span className="login-brand-body login-brand-body--left" />
            <span className="login-brand-body login-brand-body--center" />
            <span className="login-brand-body login-brand-body--right" />
          </div>
          <h1 id="login-title">모임 성향 분석</h1>
          <p>팀 협업을 위한 정교한 분석 시스템</p>
        </header>

        <section className="login-card" aria-label="로그인">
          <div className="social-login-group">
            <button className="social-login social-login--kakao" type="button">
              <span className="chat-icon" aria-hidden="true" />
              <span>카카오로 로그인</span>
            </button>
            <button className="social-login social-login--naver" type="button">
              <span className="naver-icon" aria-hidden="true">
                N
              </span>
              <span>네이버로 로그인</span>
            </button>
          </div>

          <div className="login-divider">
            <span>또는 이메일</span>
          </div>

          <form className="login-form" onSubmit={onSubmit}>
            <label>
              <span>이메일 주소</span>
              <input
                autoComplete="email"
                name="email"
                placeholder="name@company.com"
                required
                type="email"
              />
            </label>
            <label>
              <span className="login-label-row">
                <span>비밀번호</span>
                <a href="#password-help">비밀번호 찾기</a>
              </span>
              <input
                autoComplete="current-password"
                name="password"
                placeholder="비밀번호를 입력하세요"
                required
                type="password"
              />
            </label>
            <button className="login-submit" disabled={isSubmitting} type="submit">
              {isSubmitting ? "로그인 중" : "로그인"}
            </button>
          </form>

          {error ? <ErrorState message={getAuthErrorMessage(error)} title="로그인 실패" /> : null}

          <p className="login-signup-link">
            계정이 없으신가요? <Link to="/signup">회원가입</Link>
          </p>
        </section>

        <footer className="login-status" aria-label="시스템 상태">
          <span>
            <i aria-hidden="true" />
            시스템 정상
          </span>
          <span>
            <b aria-hidden="true">▣</b>
            SSL 보안 적용
          </span>
        </footer>
      </div>
    </main>
  );
}
