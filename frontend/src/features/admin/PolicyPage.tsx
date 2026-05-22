import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/api";
import ScannerRow from "./components/ScannerRow";
import Toast from "./components/Toast";

interface PolicyConfig {
  scanner_name: string;
  enabled: boolean;
  sensitivity: string;
}

export default function PolicyPage() {
  const queryClient = useQueryClient();
  const [toast, setToast] = useState<string | null>(null);
  const [localChanges, setLocalChanges] = useState<Record<string, Partial<PolicyConfig>>>({});

  const { data: policies = [] } = useQuery<PolicyConfig[]>({
    queryKey: ["admin", "policy"],
    queryFn: () => apiClient("/admin/policy"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ scannerName, data }: { scannerName: string; data: { enabled: boolean; sensitivity: string } }) =>
      apiClient(`/admin/policy/${scannerName}`, { method: "PUT", body: JSON.stringify(data) }),
  });

  const getEffective = (policy: PolicyConfig): PolicyConfig => {
    const changes = localChanges[policy.scanner_name];
    if (!changes) return policy;
    return { ...policy, ...changes };
  };

  const handleSave = async () => {
    const promises = policies
      .filter((p) => localChanges[p.scanner_name])
      .map((p) => {
        const effective = getEffective(p);
        return updateMutation.mutateAsync({
          scannerName: p.scanner_name,
          data: { enabled: effective.enabled, sensitivity: effective.sensitivity },
        });
      });
    await Promise.all(promises);
    queryClient.invalidateQueries({ queryKey: ["admin", "policy"] });
    setLocalChanges({});
    setToast("配置已保存");
  };

  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-900 mb-6">安全扫描器配置</h1>

      <div className="bg-white border border-gray-200 rounded-lg p-4">
        {policies.map((policy) => {
          const effective = getEffective(policy);
          return (
            <ScannerRow
              key={policy.scanner_name}
              scannerName={policy.scanner_name}
              enabled={effective.enabled}
              sensitivity={effective.sensitivity}
              onToggle={(enabled) =>
                setLocalChanges((prev) => ({
                  ...prev,
                  [policy.scanner_name]: { ...prev[policy.scanner_name], enabled },
                }))
              }
              onSensitivityChange={(sensitivity) =>
                setLocalChanges((prev) => ({
                  ...prev,
                  [policy.scanner_name]: { ...prev[policy.scanner_name], sensitivity },
                }))
              }
            />
          );
        })}
      </div>

      <div className="mt-4 flex justify-end">
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          保存配置
        </button>
      </div>

      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </div>
  );
}
