import ActionBadge from "./ActionBadge";

interface AuditEvent {
  event_id: string;
  timestamp: string;
  user_id: string;
  model_id: string;
  source: string;
  risk_categories: string[];
  policy_action: string;
  scanner_findings: Record<string, unknown>;
}

interface AuditTableProps {
  events: AuditEvent[];
  isLoading: boolean;
}

export default function AuditTable({ events, isLoading }: AuditTableProps) {
  if (isLoading) {
    return <div className="text-center py-8 text-gray-500">加载中...</div>;
  }

  if (!events.length) {
    return (
      <div className="text-center py-12 border border-gray-200 rounded-lg">
        <p className="text-gray-500 font-medium">暂无审计事件</p>
        <p className="text-gray-400 text-sm mt-1">当用户发送消息后，审计记录将显示在此处。</p>
      </div>
    );
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-gray-50 text-left">
          <tr>
            <th className="px-4 py-3 font-medium text-gray-600">时间</th>
            <th className="px-4 py-3 font-medium text-gray-600">用户</th>
            <th className="px-4 py-3 font-medium text-gray-600">模型</th>
            <th className="px-4 py-3 font-medium text-gray-600">动作</th>
            <th className="px-4 py-3 font-medium text-gray-600">风险类别</th>
            <th className="px-4 py-3 font-medium text-gray-600">来源</th>
          </tr>
        </thead>
        <tbody>
          {events.map((event) => (
            <tr key={event.event_id} className="border-t border-gray-100 hover:bg-gray-50 min-h-[44px]">
              <td className="px-4 py-3 text-gray-700">
                {new Date(event.timestamp).toLocaleString("zh-CN")}
              </td>
              <td className="px-4 py-3 text-gray-700 font-mono text-xs">
                {event.user_id.slice(0, 8)}
              </td>
              <td className="px-4 py-3 text-gray-700">{event.model_id}</td>
              <td className="px-4 py-3">
                <ActionBadge action={event.policy_action} />
              </td>
              <td className="px-4 py-3">
                {event.risk_categories.length > 0 ? (
                  <span className="text-gray-600">{event.risk_categories.join(", ")}</span>
                ) : (
                  <span className="text-gray-400">-</span>
                )}
              </td>
              <td className="px-4 py-3 text-gray-500">{event.source}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
