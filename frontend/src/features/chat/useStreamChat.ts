import { useState, useCallback, useRef } from "react";
import { EventSourceParserStream } from "eventsource-parser/stream";
import { sendChatMessage } from "../../lib/api";

export type StreamSegment =
  | { type: "text"; content: string }
  | { type: "redacted"; label: string; category: string };

interface BlockedInfo {
  message: string;
  categories: string[];
  conversationId?: string;
  messageId?: string;
}

interface StreamResult {
  conversationId?: string;
  messageId?: string;
  segments: StreamSegment[];
  error?: string | null;
  blocked?: BlockedInfo | null;
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

        if (!response.ok) {
          // 401 = auth issue (not a streaming problem), 4xx = client error — don't degrade
          if (response.status === 401) {
            setStreamError("认证失败，请重新登录");
            setIsStreaming(false);
            return null;
          }
          if (response.status >= 400 && response.status < 500) {
            setStreamError("请求错误");
            setIsStreaming(false);
            return null;
          }
          // 5xx or no body = server/connection issue — degrade to non-streaming
          if (!response.body) {
            setDegraded(true);
            setIsStreaming(false);
            const fallback = await sendChatMessage(message, modelId, conversationId);
            if (fallback.status === "allowed") {
              return {
                conversationId: fallback.conversation_id ?? undefined,
                messageId: fallback.message_id ?? undefined,
                segments: [{ type: "text", content: fallback.content }],
              };
            }
            if (fallback.status === "blocked") {
              return {
                segments: [],
                blocked: {
                  message: fallback.content,
                  categories: fallback.risk_categories ?? [],
                  conversationId: fallback.conversation_id ?? undefined,
                },
              };
            }
            setStreamError(fallback.content);
            return null;
          }
        }

        const stream = response.body
          .pipeThrough(new TextDecoderStream())
          .pipeThrough(new EventSourceParserStream());

        const reader = stream.getReader();
        let result: StreamResult = { segments: [] };
        const segments: StreamSegment[] = [];
        let errorMessage: string | null = null;

        // 600s timeout — guard model inference can be slow on CPU
        const timeout = setTimeout(() => {
          controller.abort();
        }, 600000);

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
            } else if (event.event === "blocked") {
              // Output blocked by safety policy — entire response rejected
              return {
                segments: [],
                blocked: {
                  message: data.message,
                  categories: data.categories,
                  conversationId: data.conversation_id,
                  messageId: data.message_id,
                },
              };
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
          // Timeout — auto-degrade to non-streaming
          setDegraded(true);
          setIsStreaming(false);
          try {
            const fallback = await sendChatMessage(message, modelId, conversationId);
            if (fallback.status === "allowed") {
              return {
                conversationId: fallback.conversation_id ?? undefined,
                messageId: fallback.message_id ?? undefined,
                segments: [{ type: "text", content: fallback.content }],
              };
            }
            if (fallback.status === "blocked") {
              return {
                segments: [],
                blocked: {
                  message: fallback.content,
                  categories: fallback.risk_categories ?? [],
                  conversationId: fallback.conversation_id ?? undefined,
                },
              };
            }
            setStreamError(fallback.content);
            return null;
          } catch {
            setStreamError("请求超时，请重试");
            return null;
          }
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
