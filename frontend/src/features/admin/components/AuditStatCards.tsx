import SparklineChart from "./SparklineChart";

interface AuditStatsData {
  total_events: number;
  total_blocks: number;
  block_rate_percent: number;
  most_active_user_id: string | null;
  daily_counts_7d: { date: string; count: number }[];
}

export default function AuditStatCards({ stats }: { stats: AuditStatsData | undefined }) {
  if (!stats) return null;

  const cards = [
    { label: "今日事件", value: stats.total_events, color: "" },
    { label: "今日拦截", value: stats.total_blocks, color: stats.total_blocks > 0 ? "text-red-600" : "" },
    { label: "拦截率", value: `${stats.block_rate_percent}%`, color: stats.block_rate_percent > 20 ? "text-amber-500" : "" },
    { label: "最活跃用户", value: stats.most_active_user_id?.slice(0, 8) || "-", color: "" },
  ];

  return (
    <div className="flex gap-4 mb-6 flex-wrap">
      {cards.map((card) => (
        <div key={card.label} className="flex-1 min-w-[180px] bg-gray-50 border border-gray-200 rounded-lg p-6">
          <p className="text-sm text-gray-500 mb-1">{card.label}</p>
          <p className={`text-[28px] font-semibold ${card.color}`}>{card.value}</p>
        </div>
      ))}
      <div className="flex-1 min-w-[180px] bg-gray-50 border border-gray-200 rounded-lg p-6">
        <p className="text-sm text-gray-500 mb-1">7日趋势</p>
        <SparklineChart data={stats.daily_counts_7d} />
      </div>
    </div>
  );
}
