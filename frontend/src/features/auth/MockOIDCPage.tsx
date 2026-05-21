import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { Shield } from "lucide-react";

export default function MockOIDCPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [authorizing, setAuthorizing] = useState(true);

  const stateToken = searchParams.get("state_token") || "";
  const role = searchParams.get("role") || "employee";

  useEffect(() => {
    // Simulate the OIDC authorization delay
    const timer = setTimeout(() => {
      setAuthorizing(false);
      // "Authorized" — navigate to callback with the mock params
      navigate(
        `/auth/callback?state_token=${encodeURIComponent(stateToken)}&role=${encodeURIComponent(role)}`,
        { replace: true }
      );
    }, 1500);

    return () => clearTimeout(timer);
  }, [stateToken, role, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full p-8 bg-white rounded-lg shadow-md text-center">
        <Shield className="w-12 h-12 text-indigo-600 mx-auto mb-4" />
        <h1 className="text-xl font-bold text-gray-900 mb-2">
          Mock OIDC Provider
        </h1>
        {authorizing ? (
          <>
            <p className="text-gray-600 mb-2">Authorizing...</p>
            <p className="text-sm text-gray-500">
              Role: <span className="font-medium text-gray-700">{role}</span>
            </p>
            <div className="mt-4 flex justify-center">
              <div className="animate-spin rounded-full h-6 w-6 border-2 border-indigo-600 border-t-transparent"></div>
            </div>
          </>
        ) : (
          <p className="text-green-600 font-medium">Authorized successfully</p>
        )}
      </div>
    </div>
  );
}