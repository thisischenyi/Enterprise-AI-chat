export default function ActionBadge({ action }: { action: string }) {
  const styles: Record<string, string> = {
    allow: "bg-green-50 text-green-700",
    block: "bg-red-50 text-red-700",
    fail_closed: "bg-amber-50 text-amber-700",
  };
  const labels: Record<string, string> = {
    allow: "允许",
    block: "拦截",
    fail_closed: "兜底拦截",
  };

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[action] || "bg-gray-50 text-gray-700"}`}>
      {labels[action] || action}
    </span>
  );
}
