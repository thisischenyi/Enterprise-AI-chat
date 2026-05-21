import { useAuthStore } from "../../stores/authStore";

export default function AdminStubPage() {
  const user = useAuthStore((s) => s.user);

  if (!user) return null;

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full p-8 bg-white rounded-lg shadow-md text-center">
        <h1 className="text-xl font-bold text-gray-900 mb-4">Admin Dashboard</h1>
        <p className="text-gray-500 mb-6">
          This dashboard will be implemented in Phase 4
        </p>
        <div className="border-t pt-4">
          <p className="text-sm text-gray-600">
            Current admin: <span className="font-medium">{user.name}</span>
          </p>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border bg-red-100 text-red-700 border-red-300 mt-2">
            Admin
          </span>
        </div>
      </div>
    </div>
  );
}