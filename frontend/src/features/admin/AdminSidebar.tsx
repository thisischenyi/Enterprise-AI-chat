import { NavLink } from "react-router";
import { Shield, Server, Settings, MessageSquare, LogOut } from "lucide-react";
import { useAuthStore } from "../../stores/authStore";

const navItems = [
  { to: "/admin/audit", icon: Shield, label: "审计日志" },
  { to: "/admin/models", icon: Server, label: "模型配置" },
  { to: "/admin/policy", icon: Settings, label: "安全策略" },
];

export default function AdminSidebar() {
  const logout = useAuthStore((s) => s.logout);

  return (
    <nav className="w-[220px] min-h-screen bg-gray-50 border-r border-gray-200 py-4">
      <h2 className="px-4 mb-4 text-sm font-semibold text-gray-500 uppercase">管理面板</h2>
      <ul className="space-y-1">
        {navItems.map((item) => (
          <li key={item.to}>
            <NavLink
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-2.5 text-sm ${
                  isActive
                    ? "bg-white border-l-[3px] border-blue-600 font-semibold text-gray-900"
                    : "text-gray-600 hover:bg-gray-100"
                }`
              }
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </NavLink>
          </li>
        ))}
      </ul>
      <div className="mt-auto pt-4 border-t border-gray-200 mt-8">
        <NavLink
          to="/chat"
          className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-600 hover:bg-gray-100"
        >
          <MessageSquare className="w-4 h-4" />
          返回聊天
        </NavLink>
        <button
          onClick={logout}
          className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-500 hover:bg-gray-100 w-full"
        >
          <LogOut className="w-4 h-4" />
          退出
        </button>
      </div>
    </nav>
  );
}
