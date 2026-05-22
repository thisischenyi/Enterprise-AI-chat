import { useState, useCallback, useRef } from "react";
import { EventSourceParserStream } from "eventsource-parser/stream";
import { sendChatMessage } from "../../lib/api";

export type StreamSegment =
  | { type: "text"; content: string }
  | { type: "redacted"; label: string; category: string };

interface StreamResult {
  conversationId?: string;
  messageId?: string;
}

export function useStreamChat() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamContent, setStreamContent] = useState<StreamSegment[]>([]);
  const [streamError, setStreamError] = useState<string | null>(null);
  const [degraded, setDegraded] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    setStreamContent([]);
    setStreamError(null);
    setDegraded(false);
  }, []);

  const streamMessage = useCallback(
    async (
      message: string,
      modelId: string,
      conversationId?: string | null
    ): Promise<StreamResult | null> => {
      reset();
      setIsStreaming(true);
      const controller = new AbortController();
      abortRef.current = controller;

      const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api";

      try {
        const response = await fetch(`${API_BASE}/chat/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          signal: controller.signal,
          body: JSON.stringify({
            message,
            model_id: modelId,
            ...(conversationId ? { conversation_id: conversationId } : {}),
          }),
        });

        if (!response.ok || !response.body) {
          // Auto-degrade to non-streaming
          setDegraded(true);
          setIsStreaming(false);
          const fallback = await sendChatMessage(message, modelId, conversationId);
          return {
            conversationId: fallback.conversation_id ?? undefined,
            messageId: fallback.message_id ?? undefined,
          };
        }

        const stream = response.body
          .pipeThrough(new TextDecoderStream())
          .pipeThrough(new EventSourceParserStream());

        const reader = stream.getReader();
        let result: StreamResult = {};

        // 30s timeout
        const timeout = setTimeout(() => {
          controller.abort();
        }, 30000);

        try {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const event = value;
            const data = JSON.parse(event.data);

            if (event.event === "chunk") {
              setStreamContent((prev) => [
                ...prev,
                { type: "text", content: data.content },
              ]);
            } else if (event.event === "redacted") {
              setStreamContent((prev) => [
                ...prev,
                { type: "redacted", label: data.label, category: data.category },
              ]);
            } else if (event.event === "done") {
              result = {
                conversationId: data.conversation_id,
                messageId: data.message_id,
              };
              break;
            } else if (event.event === "error") {
              setStreamError(data.message);
              break;
            }
          }
        } finally {
          clearTimeout(timeout);
          reader.releaseLock();
        }

        setIsStreaming(false);
        return result;
      } catch (err) {
        if ((err as Error).name === "AbortError") {
          // Timeout — auto-degrade
          setDegraded(true);
          setIsStreaming(false);
          const fallback = await sendChatMessage(message, modelId, conversationId);
          return {
            conversationId: fallback.conversation_id ?? undefined,
            messageId: fallback.message_id ?? undefined,
          };
        }
        setStreamError(
          err instanceof Error ? err.message : "Stream failed"
        );
        setIsStreaming(false);
        return null;
      }
    },
    [reset]
  );

  return { streamMessage, isStreaming, streamContent, streamError, degraded, reset };
}
