import type { FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useGetMeQuery, useSignupMutation } from "../api/baseApi";
import { ErrorState } from "../components/feedback/ErrorState";
import { ToastViewport } from "../components/feedback/ToastViewport";
import { getAuthErrorMessage } from "../features/auth/errorMessage";

export function SignupPage() {
  const navigate = useNavigate();
  const [signup, { error, isLoading }] = useSignupMutation();
  const { refetch } = useGetMeQuery(undefined, { skip: true });

  const onSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await signup({
      email: String(form.get("email") ?? ""),
      display_name: String(form.get("displayName") ?? ""),
      password: String(form.get("password") ?? ""),
    }).unwrap();
    await refetch();
    navigate("/app", { replace: true });
  };

  return (
    <main className="auth-page">
      <ToastViewport />
      <section className="auth-panel" aria-labelledby="signup-title">
        <p className="eyebrow">UFC</p>
        <h1 id="signup-title">회원가입</h1>
        <form className="auth-form" onSubmit={onSubmit}>
          <label>
            표시 이름
            <input autoComplete="name" maxLength={80} name="displayName" required />
          </label>
          <label>
            이메일
            <input autoComplete="email" name="email" required type="email" />
          </label>
          <label>
            비밀번호
            <input autoComplete="new-password" minLength={12} name="password" required type="password" />
          </label>
          <button disabled={isLoading} type="submit">
            {isLoading ? "가입 중" : "회원가입"}
          </button>
        </form>
        {error ? <ErrorState message={getAuthErrorMessage(error)} title="회원가입 실패" /> : null}
        <p className="auth-link">
          이미 계정이 있다면 <Link to="/login">로그인</Link>
        </p>
      </section>
    </main>
  );
}
