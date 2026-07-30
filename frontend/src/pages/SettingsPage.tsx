import { Link, useNavigate } from "react-router-dom";

import { useLogoutMutation } from "../api/baseApi";
import { useAppSelector } from "../app/hooks";
import { ToastViewport } from "../components/feedback/ToastViewport";

const localDemoEmail = "demo-user@example.com";
const settingsItems = [
  { label: "프로필 관리", icon: "P" },
  { label: "연결된 계좌", caption: "오픈뱅킹", icon: "B" },
  { label: "알림 설정", icon: "N" },
  { label: "보안 및 개인정보", icon: "S" },
  { label: "고객센터", icon: "?" },
  { label: "서비스 정보", icon: "i" },
];

export function SettingsPage() {
  const navigate = useNavigate();
  const user = useAppSelector((state) => state.auth.user);
  const [logout, { isLoading }] = useLogoutMutation();

  const onLogout = async () => {
    await logout().unwrap().catch(() => undefined);
    navigate("/login", { replace: true });
  };

  return (
    <main className="settings-page">
      <ToastViewport />
      <header className="settings-topbar">
        <div>
          <button aria-label="뒤로 가기" onClick={() => navigate(-1)} type="button">
            ‹
          </button>
          <h1>설정</h1>
        </div>
        <button aria-label="검색" type="button">
          ⌕
        </button>
      </header>

      <section className="settings-profile" aria-label="프로필 요약">
        <div className="settings-avatar" aria-hidden="true">
          <span>{initialFor(user?.display_name)}</span>
          <i>✓</i>
        </div>
        <div>
          <h2>{user?.display_name ?? "Alex Rivera"}</h2>
          <p>{user ? `${localDemoEmail} · ${user.role}` : localDemoEmail}</p>
        </div>
      </section>

      <section className="settings-list" aria-label="설정 메뉴">
        {settingsItems.slice(0, 4).map((item) => (
          <SettingsItem key={item.label} {...item} />
        ))}
        <hr />
        {settingsItems.slice(4).map((item) => (
          <SettingsItem key={item.label} {...item} />
        ))}
      </section>

      <section className="settings-footer">
        <button disabled={isLoading} onClick={onLogout} type="button">
          <span aria-hidden="true">↪</span>
          {isLoading ? "로그아웃 중" : "로그아웃"}
        </button>
        <p>버전 2.4.0-KINETIC</p>
        <Link to="/">홈으로 돌아가기</Link>
      </section>
    </main>
  );
}

function SettingsItem({
  label,
  caption,
  icon,
}: {
  label: string;
  caption?: string;
  icon: string;
}) {
  return (
    <button className="settings-item" type="button">
      <span className="settings-item-icon" aria-hidden="true">
        {icon}
      </span>
      <span>
        <strong>{label}</strong>
        {caption ? <small>{caption}</small> : null}
      </span>
      <b aria-hidden="true">›</b>
    </button>
  );
}

function initialFor(displayName: string | undefined): string {
  const trimmed = displayName?.trim();
  return trimmed ? trimmed.slice(0, 1).toUpperCase() : "A";
}
