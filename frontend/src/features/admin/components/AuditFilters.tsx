interface AuditFiltersProps {
  timeRange: string;
  onTimeRangeChange: (v: string) => void;
  action: string;
  onActionChange: (v: string) => void;
  riskCategory: string;
  onRiskCategoryChange: (v: string) => void;
}

const timeRangeOptions = [
  { value: "today", label: "今天" },
  { value: "7d", label: "近7天" },
  { value: "30d", label: "近30天" },
];

export default function AuditFilters({
  timeRange,
  onTimeRangeChange,
  action,
  onActionChange,
  riskCategory,
  onRiskCategoryChange,
}: AuditFiltersProps) {
  return (
    <div className="flex items-center gap-4 mb-4 flex-wrap">
      <div className="flex rounded border border-gray-300 overflow-hidden">
        {timeRangeOptions.map((opt) => (
          <button
            key={opt.value}
            onClick={() => onTimeRangeChange(opt.value)}
            className={`px-3 py-1.5 text-sm ${
              timeRange === opt.value
                ? "bg-blue-600 text-white"
                : "bg-white text-gray-700 hover:bg-gray-50"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>

      <select
        value={action}
        onChange={(e) => onActionChange(e.target.value)}
        className="border border-gray-300 rounded h-9 text-sm px-2"
      >
        <option value="">全部动作</option>
        <option value="allow">允许</option>
        <option value="block">拦截</option>
        <option value="fail_closed">兜底拦截</option>
      </select>

      <select
        value={riskCategory}
        onChange={(e) => onRiskCategoryChange(e.target.value)}
        className="border border-gray-300 rounded h-9 text-sm px-2"
      >
        <option value="">全部风险类别</option>
        <option value="pii">PII</option>
        <option value="prompt_injection">提示注入</option>
        <option value="jailbreak">越狱</option>
        <option value="toxicity">有害内容</option>
      </select>
    </div>
  );
}
