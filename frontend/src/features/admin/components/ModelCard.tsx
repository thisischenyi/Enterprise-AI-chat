interface ModelConfig {
  id: string;
  name: string;
  provider_type: string;
  endpoint_url: string;
  model_id: string;
  api_key_masked: string;
  enabled: boolean;
}

interface ModelCardProps {
  model: ModelConfig;
  onEdit: (model: ModelConfig) => void;
}

export type { ModelConfig };

export default function ModelCard({ model, onEdit }: ModelCardProps) {
  return (
    <div
      className={`bg-white border border-gray-200 rounded-lg p-4 ${
        !model.enabled ? "opacity-50" : ""
      }`}
    >
      <div className="flex justify-between items-start mb-2">
        <h3 className="font-semibold text-gray-900">{model.name}</h3>
        <span
          className={`text-xs px-2 py-0.5 rounded ${
            model.enabled
              ? "bg-green-100 text-green-700"
              : "bg-gray-100 text-gray-500"
          }`}
        >
          {model.enabled ? "启用" : "禁用"}
        </span>
      </div>
      <p className="text-sm text-gray-500 mb-1">{model.provider_type}</p>
      <p className="text-sm text-gray-500 mb-1 truncate">{model.endpoint_url}</p>
      <p className="text-sm text-gray-400 mb-3">{model.api_key_masked}</p>
      <button
        onClick={() => onEdit(model)}
        className="text-sm text-blue-600 hover:text-blue-800"
      >
        编辑模型
      </button>
    </div>
  );
}
