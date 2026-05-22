import { useState, useCallback, useRef } from "react";
import { EventSourceParserStream } from "eventsource-parser/stream";
import { sendChatMessage } from "../../lib/api";

export type StreamSegment =
  | { type: "text"; content: string }
  | { type: "redacted"; label: string; category: string };

interface StreamResult {
  conversationId?: string;
  messageId?: string;
  segments: StreamSegment[];
  error?: string | null;
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
            segments: [],
          };
        }

        const stream = response.body
          .pipeThrough(new TextDecoderStream())
          .pipeThrough(new EventSourceParserStream());

        const reader = stream.getReader();
        let result: StreamResult = { segments: [] };
        const segments: StreamSegment[] = [];
        let errorMessage: string | null = null;

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
              const seg: StreamSegment = { type: "text", content: data.content };
              segments.push(seg);
              setStreamContent((prev) => [...prev, seg]);
            } else if (event.event === "redacted") {
              const seg: StreamSegment = { type: "redacted", label: data.label, category: data.category };
              segments.push(seg);
              setStreamContent((prev) => [...prev, seg]);
            } else if (event.event === "done") {
              result = {
                conversationId: data.conversation_id,
                messageId: data.message_id,
                segments,
              };
              break;
            } else if (event.event === "error") {
              errorMessage = data.message;
              setStreamError(data.message);
              break;
            }
          }
        } finally {
          clearTimeout(timeout);
          reader.releaseLock();
        }

        setIsStreaming(false);
        return { ...result, error: errorMessage };
      } catch (err) {
        if ((err as Error).name === "AbortError") {
          // Timeout — auto-degrade
          setDegraded(true);
          setIsStreaming(false);
          const fallback = await sendChatMessage(message, modelId, conversationId);
          return {
            conversationId: fallback.conversation_id ?? undefined,
            messageId: fallback.message_id ?? undefined,
            segments: [],
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
