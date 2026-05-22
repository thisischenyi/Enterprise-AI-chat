import { create } from "zustand";

export interface ChatMessage {
  id: string;
  role: "user" | "model" | "blocked" | "error";
  content: string;
  modelId?: string;
  providerId?: string;
  riskCategories?: string[];
  revisionHint?: string;
}

interface ChatState {
  selectedModel: string | null;
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  activeConversationId: string | null;
  setSelectedModel: (modelId: string | null) => void;
  addMessage: (message: ChatMessage) => void;
  clearMessages: () => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setActiveConversation: (id: string | null) => void;
  startNewConversation: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  selectedModel: null,
  messages: [],
  isLoading: false,
  error: null,
  activeConversationId: null,

  setSelectedModel: (modelId) => set({ selectedModel: modelId }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  clearMessages: () => set({ messages: [] }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),
  setActiveConversation: (id) => set({ activeConversationId: id, messages: [] }),
  startNewConversation: () => set({ activeConversationId: null, messages: [] }),
}));
