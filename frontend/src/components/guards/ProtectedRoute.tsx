import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";

import { useGetMeQuery } from "../../api/baseApi";
import { useAppSelector } from "../../app/hooks";
import { refreshTokenStorage } from "../../features/auth/tokenStorage";
import { Loading } from "../feedback/Loading";

interface ProtectedRouteProps {
  children: ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation();
  const { accessToken, user } = useAppSelector((state) => state.auth);
  const hasRefreshToken = Boolean(refreshTokenStorage.get());
  const shouldLoadSession = Boolean(accessToken || hasRefreshToken) && !user;
  const { isFetching } = useGetMeQuery(undefined, { skip: !shouldLoadSession });

  if (!accessToken && !hasRefreshToken) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  if (!user && isFetching) {
    return <Loading label="세션을 확인하는 중입니다" />;
  }

  if (!user && !isFetching) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <>{children}</>;
}
