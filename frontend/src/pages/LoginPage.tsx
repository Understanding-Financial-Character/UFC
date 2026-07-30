import type { FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { useGetMeQuery, useLoginMutation } from "../api/baseApi";
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
  const { refetch } = useGetMeQuery(undefined, { skip: true });

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await login({
      email: String(form.get("email") ?? ""),
      password: String(form.get("password") ?? ""),
    }).unwrap();
    await refetch();
    const state = location.state as LocationState | null;
    navigate(state?.from?.pathname ?? "/app", { replace: true });
  };

  return (
    <main className="auth-page">
      <ToastViewport />
      <section className="auth-panel" aria-labelledby="login-title">
        <p className="eyebrow">UFC</p>
        <h1 id="login-title">로그인</h1>
        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            이메일
            <input autoComplete="email" name="email" required type="email" />
          </label>
          <label>
            비밀번호
            <input autoComplete="current-password" name="password" required type="password" />
          </label>
          <button disabled={isLoading} type="submit">
            {isLoading ? "로그인 중" : "로그인"}
          </button>
        </form>
        {error ? <ErrorState message={getAuthErrorMessage(error)} title="로그인 실패" /> : null}
        <p className="auth-link">
          계정이 없다면 <Link to="/signup">회원가입</Link>
        </p>
      </section>
    </main>
  );
}
