import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../../lib/api";
import AuditStatCards from "./components/AuditStatCards";
import AuditFilters from "./components/AuditFilters";
import AuditTable from "./components/AuditTable";
import Pagination from "./components/Pagination";

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

interface PaginatedResponse {
  events: AuditEvent[];
  total: number;
  page: number;
  page_size: number;
}

interface AuditStats {
  total_events: number;
  total_blocks: number;
  block_rate_percent: number;
  most_active_user_id: string | null;
  daily_counts_7d: { date: string; count: number }[];
}

export default function AuditPage() {
  const [timeRange, setTimeRange] = useState("today");
  const [action, setAction] = useState("");
  const [riskCategory, setRiskCategory] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const eventsQuery = useQuery({
    queryKey: ["admin-audit", timeRange, action, riskCategory, page],
    queryFn: () => {
      const params = new URLSearchParams({ time_range: timeRange, page: String(page), page_size: String(pageSize) });
      if (action) params.set("action", action);
      if (riskCategory) params.set("risk_category", riskCategory);
      return apiClient<PaginatedResponse>(`/admin/audit?${params}`);
    },
  });

  const statsQuery = useQuery({
    queryKey: ["admin-audit-stats", timeRange],
    queryFn: () => apiClient<AuditStats>(`/admin/audit/stats?time_range=${timeRange}`),
  });

  const totalPages = eventsQuery.data ? Math.ceil(eventsQuery.data.total / pageSize) : 0;

  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-900 mb-6">审计事件</h1>
      <AuditStatCards stats={statsQuery.data} />
      <AuditFilters
        timeRange={timeRange}
        onTimeRangeChange={(v) => { setTimeRange(v); setPage(1); }}
        action={action}
        onActionChange={(v) => { setAction(v); setPage(1); }}
        riskCategory={riskCategory}
        onRiskCategoryChange={(v) => { setRiskCategory(v); setPage(1); }}
      />
      <AuditTable events={eventsQuery.data?.events || []} isLoading={eventsQuery.isLoading} />
      <Pagination page={page} totalPages={totalPages} onPageChange={setPage} />
    </div>
  );
}
