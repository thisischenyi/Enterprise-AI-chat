import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import LoginPage from "./features/auth/LoginPage";
import MockOIDCPage from "./features/auth/MockOIDCPage";
import AuthCallbackPage from "./features/auth/AuthCallbackPage";
import UserInfo from "./features/auth/UserInfo";
import AdminStubPage from "./features/admin/AdminStubPage";
import { useAuthStore } from "./stores/authStore";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
}

export function AdminRoute({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  if (!user || user.role !== "admin") {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}

export default function AppRoutes() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/mock-oidc" element={<MockOIDCPage />} />
        <Route path="/auth/callback" element={<AuthCallbackPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <UserInfo />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <AdminRoute>
              <AdminStubPage />
            </AdminRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}