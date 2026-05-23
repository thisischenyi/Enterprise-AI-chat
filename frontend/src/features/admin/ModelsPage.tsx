import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../../lib/api";
import ModelCard from "./components/ModelCard";
import ModelEditModal from "./components/ModelEditModal";
import ConfirmDialog from "./components/ConfirmDialog";
import Toast from "./components/Toast";
import type { ModelConfig } from "./components/ModelCard";

export default function ModelsPage() {
  const queryClient = useQueryClient();
  const [editingModel, setEditingModel] = useState<ModelConfig | null>(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState<ModelConfig | null>(null);
  const [toast, setToast] = useState<string | null>(null);

  const { data: models = [] } = useQuery<ModelConfig[]>({
    queryKey: ["admin", "models"],
    queryFn: () => apiClient("/admin/models"),
  });

  const createMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiClient("/admin/models", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "models"] });
      setShowCreateModal(false);
      setToast("配置已保存");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      apiClient(`/admin/models/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "models"] });
      setEditingModel(null);
      setToast("配置已保存");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) =>
      apiClient(`/admin/models/${id}`, { method: "DELETE" }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["admin", "models"] });
      setConfirmDelete(null);
      setToast("配置已保存");
    },
  });

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-xl font-semibold text-gray-900">模型供应商配置</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          添加模型
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {models.map((model) => (
          <ModelCard key={model.id} model={model} onEdit={setEditingModel} onDelete={setConfirmDelete} />
        ))}
      </div>

      {showCreateModal && (
        <ModelEditModal
          model={null}
          onSave={(data) => createMutation.mutate(data)}
          onCancel={() => setShowCreateModal(false)}
        />
      )}

      {editingModel && (
        <ModelEditModal
          model={editingModel}
          onSave={(data) => updateMutation.mutate({ id: editingModel.id, data })}
          onCancel={() => setEditingModel(null)}
        />
      )}

      {confirmDelete && (
        <ConfirmDialog
          message="确认禁用此模型？禁用后用户将无法选择该模型。"
          onConfirm={() => deleteMutation.mutate(confirmDelete.id)}
          onCancel={() => setConfirmDelete(null)}
        />
      )}

      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </div>
  );
}
