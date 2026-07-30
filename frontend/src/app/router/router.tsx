import { createBrowserRouter } from "react-router-dom";

import { ProtectedRoute } from "../../components/guards/ProtectedRoute";
import { RoleGuard } from "../../components/guards/RoleGuard";
import {
  AnalysisLoadingPage,
  AnalysisResultPage,
  ConsumptionDataConnectionPage,
  GoalSetupPage,
  GoalSummaryPage,
  OnboardingIntroPage,
  RelationshipSelectionPage,
  StitchLandingPage,
} from "../../pages/AnalysisFlowPages";
import { ForbiddenPage } from "../../pages/ForbiddenPage";
import { HomePage } from "../../pages/HomePage";
import { LoginPage } from "../../pages/LoginPage";
import { NotFoundPage } from "../../pages/NotFoundPage";
import { SettingsPage } from "../../pages/SettingsPage";
import { SignupPage } from "../../pages/SignupPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <StitchLandingPage />,
  },
  {
    path: "/onboarding",
    element: <OnboardingIntroPage />,
  },
  {
    path: "/flow/relationship",
    element: <RelationshipSelectionPage />,
  },
  {
    path: "/flow/goal",
    element: <GoalSetupPage />,
  },
  {
    path: "/flow/summary",
    element: <GoalSummaryPage />,
  },
  {
    path: "/flow/data",
    element: <ConsumptionDataConnectionPage />,
  },
  {
    path: "/analysis/loading",
    element: (
      <ProtectedRoute>
        <AnalysisLoadingPage />
      </ProtectedRoute>
    ),
  },
  {
    path: "/analysis/result",
    element: (
      <ProtectedRoute>
        <AnalysisResultPage />
      </ProtectedRoute>
    ),
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
