import { useQuery } from "@tanstack/react-query";
import { fetchChatModels } from "../../lib/api";
import { useChatStore } from "../../stores/chatStore";

export default function ModelSelector() {
  const selectedModel = useChatStore((s) => s.selectedModel);
  const setSelectedModel = useChatStore((s) => s.setSelectedModel);

  const { data: models, isLoading } = useQuery({
    queryKey: ["chatModels"],
    queryFn: fetchChatModels,
  });

  if (isLoading) {
    return <div className="text-sm text-gray-500">Loading models...</div>;
  }

  if (!models || models.length === 0) {
    return (
      <div className="text-sm text-amber-600">
        No models available. Configure model providers in environment variables.
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3">
      <label htmlFor="model-select" className="text-sm font-medium text-gray-700">
        Model:
      </label>
      <select
        id="model-select"
        value={selectedModel || ""}
        onChange={(e) => setSelectedModel(e.target.value || null)}
        className="rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none"
      >
        <option value="">Select a model</option>
        {models.map((model) => (
          <option key={model.id} value={model.id}>
            {model.name}
          </option>
        ))}
      </select>
      {selectedModel && models.find((m) => m.id === selectedModel) && (
        <span className="text-xs text-gray-500">
          {models.find((m) => m.id === selectedModel)!.description}
        </span>
      )}
    </div>
  );
}
