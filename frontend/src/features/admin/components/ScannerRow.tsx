interface ScannerRowProps {
  scannerName: string;
  enabled: boolean;
  sensitivity: string;
  onToggle: (enabled: boolean) => void;
  onSensitivityChange: (sensitivity: string) => void;
}

const SENSITIVITY_LEVELS = ["low", "medium", "high"] as const;
const SENSITIVITY_LABELS: Record<string, string> = {
  low: "低",
  medium: "中",
  high: "高",
};
const SENSITIVITY_COLORS: Record<string, string> = {
  low: "bg-green-600",
  medium: "bg-amber-500",
  high: "bg-red-600",
};

export default function ScannerRow({
  scannerName,
  enabled,
  sensitivity,
  onToggle,
  onSensitivityChange,
}: ScannerRowProps) {
  return (
    <div className="flex items-center justify-between py-3 border-b border-gray-100">
      <span className="text-sm text-gray-800 font-medium">{scannerName}</span>

      <div className="flex items-center gap-4">
        {/* Sensitivity slider */}
        <div className="flex items-center gap-1">
          {SENSITIVITY_LEVELS.map((level) => (
            <button
              key={level}
              onClick={() => onSensitivityChange(level)}
              className={`px-2 py-0.5 text-xs rounded ${
                sensitivity === level
                  ? `${SENSITIVITY_COLORS[level]} text-white`
                  : "bg-gray-100 text-gray-500"
              }`}
            >
              {SENSITIVITY_LABELS[level]}
            </button>
          ))}
        </div>

        {/* Enable toggle */}
        <button
          onClick={() => onToggle(!enabled)}
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
  );
}
