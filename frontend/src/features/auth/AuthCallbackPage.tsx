import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { useAuthStore } from "../../stores/authStore";
import { Loader2 } from "lucide-react";

export default function AuthCallbackPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const handleCallback = useAuthStore((s) => s.handleCallback);
  const error = useAuthStore((s) => s.error);

  const stateToken = searchParams.get("state_token") || "";
  const role = (searchParams.get("role") || "employee") as "employee" | "admin";

  useEffect(() => {
    if (!stateToken) {
      navigate("/login", { replace: true });
      return;
    }

    handleCallback(stateToken, role)
      .then(() => {
        navigate("/", { replace: true });
      })
      .catch(() => {
        // Error is stored in auth state, redirect to login after brief delay
        setTimeout(() => {
          navigate("/login", { replace: true });
        }, 2000);
      });
  }, [stateToken, role, handleCallback, navigate]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="max-w-md w-full p-8 bg-white rounded-lg shadow-md text-center">
          <p className="text-red-600 font-medium">Authentication failed: {error}</p>
          <p className="text-sm text-gray-500 mt-2">Redirecting to login page...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full p-8 bg-white rounded-lg shadow-md text-center">
        <Loader2 className="w-8 h-8 text-indigo-600 mx-auto mb-4 animate-spin" />
        <p className="text-gray-600">Completing authentication...</p>
      </div>
    </div>
  );
}