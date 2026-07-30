import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";

import { useAppSelector } from "../../app/hooks";
import type { UserRole } from "../../features/auth/types";

interface RoleGuardProps {
  allowedRoles: UserRole[];
  children: ReactNode;
}

export function RoleGuard({ allowedRoles, children }: RoleGuardProps) {
  const role = useAppSelector((state) => state.auth.user?.role);

  if (!role || !allowedRoles.includes(role)) {
    return <Navigate to="/403" replace />;
  }

  return <>{children}</>;
}
