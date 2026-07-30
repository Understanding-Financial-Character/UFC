import { useNavigate } from "react-router-dom";

import { useLogoutMutation } from "../api/baseApi";
import { useAppSelector } from "../app/hooks";
import { EmptyState } from "../components/feedback/EmptyState";
import { ToastViewport } from "../components/feedback/ToastViewport";

interface HomePageProps {
  variant?: "user" | "admin";
}

export function HomePage({ variant = "user" }: HomePageProps) {
  const navigate = useNavigate();
  const user = useAppSelector((state) => state.auth.user);
  const [logout, { isLoading }] = useLogoutMutation();

  const onLogout = async () => {
    await logout().unwrap().catch(() => undefined);
    navigate("/login", { replace: true });
  };

  return (
    <main className="app-shell">
      <ToastViewport />
      <header className="topbar">
        <div>
          <p className="eyebrow">UFC</p>
          <h1>{variant === "admin" ? "관리자 콘솔" : "그룹 준비"}</h1>
        </div>
        <div className="user-menu">
          <span>{user?.display_name}</span>
          <button disabled={isLoading} onClick={onLogout} type="button">
            로그아웃
          </button>
        </div>
      </header>
      <EmptyState
        title="인증 기반이 준비되었습니다"
        message="다음 프론트엔드 Phase에서 그룹과 멤버 입력 흐름이 이 화면에 연결됩니다."
      />
    </main>
  );
}
