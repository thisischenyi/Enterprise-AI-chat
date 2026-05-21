import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import LoginPage from "./features/auth/LoginPage";
import MockOIDCPage from "./features/auth/MockOIDCPage";
import AuthCallbackPage from "./features/auth/AuthCallbackPage";
import UserInfo from "./features/auth/UserInfo";
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
  if (!user || user.role !== "admin") {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}

export function AdminPlaceholder() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full p-8 bg-white rounded-lg shadow-md text-center">
        <h1 className="text-xl font-bold text-gray-900 mb-2">Admin Dashboard</h1>
        <p className="text-gray-500">Coming in Phase 4</p>
      </div>
    </div>
  );
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
            <ProtectedRoute>
              <AdminRoute>
                <AdminPlaceholder />
              </AdminRoute>
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}