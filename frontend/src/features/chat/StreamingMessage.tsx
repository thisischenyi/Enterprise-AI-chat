import type { StreamSegment } from "./useStreamChat";

interface StreamingMessageProps {
  segments: StreamSegment[];
  isStreaming: boolean;
}

export default function StreamingMessage({ segments, isStreaming }: StreamingMessageProps) {
  return (
    <div className="rounded-lg bg-gray-50 px-4 py-3 text-gray-900">
      {segments.map((seg, i) =>
        seg.type === "text" ? (
          <span key={i}>{seg.content}</span>
        ) : (
          <span
            key={i}
            className="bg-red-50 text-red-700 border border-red-200 rounded px-2 py-0.5 text-sm font-semibold"
          >
            {seg.label}
          </span>
        )
      )}
      {isStreaming && (
        <span className="animate-pulse text-gray-400">|</span>
      )}
    </div>
  );
}
