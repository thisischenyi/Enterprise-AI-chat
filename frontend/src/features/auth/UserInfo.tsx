import { useAuthStore } from "../../stores/authStore";
import { LogOut, User } from "lucide-react";

export default function UserInfo() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  if (!user) return null;

  const roleBadgeColor =
    user.role === "admin"
      ? "bg-red-100 text-red-700 border-red-300"
      : "bg-blue-100 text-blue-700 border-blue-300";

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-lg w-full p-8 bg-white rounded-lg shadow-md">
        <div className="flex items-center mb-6">
          <User className="w-8 h-8 text-indigo-600 mr-3" />
          <h1 className="text-2xl font-bold text-gray-900">
            Enterprise AI Chat
          </h1>
        </div>

        <div className="space-y-3 mb-6">
          <div className="flex items-center">
            <span className="text-sm font-medium text-gray-500 w-20">Name:</span>
            <span className="text-gray-900 font-medium">{user.name}</span>
          </div>
          <div className="flex items-center">
            <span className="text-sm font-medium text-gray-500 w-20">Email:</span>
            <span className="text-gray-900">{user.email}</span>
          </div>
          <div className="flex items-center">
            <span className="text-sm font-medium text-gray-500 w-20">Role:</span>
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${roleBadgeColor}`}>
              {user.role}
            </span>
          </div>
        </div>

        <p className="text-sm text-gray-500 mb-6">
          Chat functionality will be available in Phase 2.
        </p>

        <button
          onClick={logout}
          className="flex items-center px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-400 font-medium"
        >
          <LogOut className="w-4 h-4 mr-2" />
          Sign Out
        </button>
      </div>
    </div>
  );
}