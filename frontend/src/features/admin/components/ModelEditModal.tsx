import { useState, useEffect } from "react";
import type { ModelConfig } from "./ModelCard";

interface ModelEditModalProps {
  model: ModelConfig | null; // null = create mode
  onSave: (data: Record<string, unknown>) => void;
  onCancel: () => void;
}

export default function ModelEditModal({ model, onSave, onCancel }: ModelEditModalProps) {
  const [name, setName] = useState("");
  const [providerType, setProviderType] = useState("qwen");
  const [endpointUrl, setEndpointUrl] = useState("");
  const [modelId, setModelId] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [enabled, setEnabled] = useState(true);

  useEffect(() => {
    if (model) {
      setName(model.name);
      setProviderType(model.provider_type);
      setEndpointUrl(model.endpoint_url);
      setModelId(model.model_id);
      setEnabled(model.enabled);
      setApiKey("");
    }
  }, [model]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const data: Record<string, unknown> = {
      name,
      provider_type: providerType,
      endpoint_url: endpointUrl,
      model_id: modelId,
      enabled,
    };
    if (apiKey) {
      data.api_key = apiKey;
    }
    onSave(data);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-lg p-6 max-w-[480px] w-full mx-4"
      >
        <h2 className="text-lg font-semibold mb-4">
          {model ? "编辑模型" : "添加模型"}
        </h2>

        <div className="space-y-3">
          <div>
            <label className="block text-sm text-gray-700 mb-1">名称</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">供应商类型</label>
            <select
              value={providerType}
              onChange={(e) => setProviderType(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
            >
              <option value="qwen">qwen</option>
              <option value="openai_compatible">openai_compatible</option>
            </select>
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">Endpoint URL</label>
            <input
              type="text"
              value={endpointUrl}
              onChange={(e) => setEndpointUrl(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">Model ID</label>
            <input
              type="text"
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-gray-700 mb-1">
              API Key{model ? "（留空则不修改）" : ""}
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder={model ? model.api_key_masked : ""}
              className="w-full border border-gray-300 rounded-lg px-3 py-2"
              {...(!model ? { required: true } : {})}
            />
          </div>

          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-700">启用</label>
            <button
              type="button"
              onClick={() => setEnabled(!enabled)}
              className={`w-10 h-5 rounded-full transition-colors ${
                enabled ? "bg-green-600" : "bg-gray-300"
              }`}
            >
              <div
                className={`w-4 h-4 bg-white rounded-full shadow transform transition-transform ${
                  enabled ? "translate-x-5" : "translate-x-0.5"
                }`}
              />
            </button>
          </div>
        </div>

        <div className="flex justify-end gap-3 mt-6">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            放弃修改
          </button>
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            保存配置
          </button>
        </div>
      </form>
    </div>
  );
}
