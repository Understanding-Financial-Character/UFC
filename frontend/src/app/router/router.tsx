import { createBrowserRouter } from "react-router-dom";

import { ProtectedRoute } from "../../components/guards/ProtectedRoute";
import { RoleGuard } from "../../components/guards/RoleGuard";
import { ForbiddenPage } from "../../pages/ForbiddenPage";
import { HomePage } from "../../pages/HomePage";
import { LoginPage } from "../../pages/LoginPage";
import { NotFoundPage } from "../../pages/NotFoundPage";
import { SettingsPage } from "../../pages/SettingsPage";
import { SignupPage } from "../../pages/SignupPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <HomePage />,
  },
  {
    path: "/login",
    element: <LoginPage />,
  },
  {
    path: "/signup",
    element: <SignupPage />,
  },
  {
    path: "/403",
    element: <ForbiddenPage />,
  },
  {
    path: "/app",
    element: (
      <ProtectedRoute>
        <HomePage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/admin",
    element: (
      <ProtectedRoute>
        <RoleGuard allowedRoles={["ADMIN"]}>
          <HomePage variant="admin" />
        </RoleGuard>
      </ProtectedRoute>
    ),
  },
  {
    path: "/settings",
    element: (
      <ProtectedRoute>
        <SettingsPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "*",
    element: <NotFoundPage />,
  },
]);
