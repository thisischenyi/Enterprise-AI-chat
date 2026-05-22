import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import LoginPage from "./features/auth/LoginPage";
import MockOIDCPage from "./features/auth/MockOIDCPage";
import AuthCallbackPage from "./features/auth/AuthCallbackPage";
import AdminLayout from "./features/admin/AdminLayout";
import AuditPage from "./features/admin/AuditPage";
import ModelsPage from "./features/admin/ModelsPage";
import PolicyPage from "./features/admin/PolicyPage";
import ChatPage from "./features/chat/ChatPage";
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
    return <Navigate to="/chat" replace />;
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
              <Navigate to="/chat" replace />
            </ProtectedRoute>
          }
        />
        <Route
          path="/chat"
          element={
            <ProtectedRoute>
              <ChatPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <AdminRoute>
              <AdminLayout />
            </AdminRoute>
          }
        >
          <Route index element={<Navigate to="/admin/audit" replace />} />
          <Route path="audit" element={<AuditPage />} />
          <Route path="models" element={<ModelsPage />} />
          <Route path="policy" element={<PolicyPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
