import { useState } from "react";
import { useNavigate } from "react-router";
import { useAuthStore } from "../../stores/authStore";
import { LogIn } from "lucide-react";

export default function LoginPage() {
  const [selectedRole, setSelectedRole] = useState<"employee" | "admin">("employee");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const login = useAuthStore((s) => s.login);
  const error = useAuthStore((s) => s.error);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const result = await login(selectedRole);
      // Navigate to mock OIDC page with state token and role as URL params
      navigate(
        `/mock-oidc?state_token=${encodeURIComponent(result.stateToken)}&role=${encodeURIComponent(selectedRole)}`,
        { replace: true }
      );
    } catch {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full p-8 bg-white rounded-lg shadow-md">
        <div className="flex items-center justify-center mb-6">
          <LogIn className="w-8 h-8 text-indigo-600 mr-2" />
          <h1 className="text-2xl font-bold text-gray-900">
            Sign In to Enterprise AI Chat
          </h1>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="role-select" className="block text-sm font-medium text-gray-700 mb-1">
              Select your role
            </label>
            <select
              id="role-select"
              value={selectedRole}
              onChange={(e) => setSelectedRole(e.target.value as "employee" | "admin")}
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 text-gray-900"
            >
              <option value="employee">Employee</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          {error && (
            <div className="text-red-600 text-sm bg-red-50 p-3 rounded-md">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {isSubmitting ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p className="mt-4 text-xs text-gray-500 text-center">
          This is a mock OIDC login for MVP demonstration purposes.
        </p>
      </div>
    </div>
  );
}