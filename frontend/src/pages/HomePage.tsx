import { useNavigate } from "react-router-dom";

import { useLogoutMutation } from "../api/baseApi";
import { useAppSelector } from "../app/hooks";
import { LegoFinanceDashboard } from "../features/dashboard/LegoFinanceDashboard";

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
    <LegoFinanceDashboard
      displayName={variant === "admin" ? "관리자" : user?.display_name}
      isLoggingOut={isLoading}
      mode="app"
      onLogout={onLogout}
    />
  );
}
