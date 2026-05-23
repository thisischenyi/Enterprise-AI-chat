import { QueryClient } from "@tanstack/react-query";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      retry: (failureCount, error) => {
        // Don't retry on 401 — session is invalid
        if (error instanceof AuthError) return false;
        return failureCount < 1;
      },
    },
  },
});

export class AuthError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthError";
  }
}

export async function apiClient<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  const response = await fetch(url, {
    ...options,
    credentials: "include", // Include cookies for session-based auth
    headers: {
      ...options.headers,
      ...(options.body ? { "Content-Type": "application/json" } : {}),
    },
  });

  if (response.status === 401) {
    throw new AuthError("Not authenticated");
  }

  if (!response.ok) {
    const errorBody = await response.text();
    throw new Error(`API error ${response.status}: ${errorBody}`);
  }

  // 204 No Content — no body to parse
  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}

// --- Chat API types ---

export interface ConversationSummary {
  id: string;
  title: string;
  model_id: string;
  updated_at: string;
}

export interface MessageResponse {
  id: string;
  role: string;
  content: string;
  extra?: { risk_categories?: string[] } | null;
  created_at: string;
}

export interface ChatResponse {
  status: "allowed" | "blocked" | "fail_closed";
  content: string;
  model_id?: string;
  provider_id?: string;
  risk_categories?: string[];
  revision_hint?: string;
  conversation_id?: string | null;
  message_id?: string | null;
}

export interface ModelInfo {
  id: string;
  name: string;
  description: string;
}

// --- Chat API functions ---

export async function fetchChatModels(): Promise<ModelInfo[]> {
  return apiClient<ModelInfo[]>("/chat/models");
}

export async function fetchConversations(): Promise<ConversationSummary[]> {
  return apiClient<ConversationSummary[]>("/conversations");
}

export async function deleteConversation(id: string): Promise<void> {
  return apiClient<void>(`/conversations/${id}`, { method: "DELETE" });
}

export async function fetchConversationMessages(id: string): Promise<MessageResponse[]> {
  return apiClient<MessageResponse[]>(`/conversations/${id}/messages`);
}

export async function sendChatMessage(
  message: string,
  modelId: string,
  conversationId?: string | null
): Promise<ChatResponse> {
  return apiClient<ChatResponse>("/chat/send", {
    method: "POST",
    body: JSON.stringify({
      message,
      model_id: modelId,
      ...(conversationId ? { conversation_id: conversationId } : {}),
    }),
  });
}
