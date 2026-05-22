import { useEffect } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { sendChatMessage, fetchConversationMessages } from "../../lib/api";
import { useChatStore } from "../../stores/chatStore";
import ConversationSidebar from "./ConversationSidebar";
import ModelSelector from "./ModelSelector";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";

export default function ChatPage() {
  const queryClient = useQueryClient();
  const selectedModel = useChatStore((s) => s.selectedModel);
  const setSelectedModel = useChatStore((s) => s.setSelectedModel);
  const addMessage = useChatStore((s) => s.addMessage);
  const setLoading = useChatStore((s) => s.setLoading);
  const activeConversationId = useChatStore((s) => s.activeConversationId);
  const setActiveConversation = useChatStore((s) => s.setActiveConversation);

  // Fetch messages when a conversation is selected
  const { data: conversationMessages } = useQuery({
    queryKey: ["conversations", activeConversationId, "messages"],
    queryFn: () => fetchConversationMessages(activeConversationId!),
    enabled: !!activeConversationId,
  });

  // Populate messages when conversation data loads
  useEffect(() => {
    if (conversationMessages && activeConversationId) {
      const store = useChatStore.getState();
      store.clearMessages();
      for (const msg of conversationMessages) {
        store.addMessage({
          id: msg.id,
          role: msg.role as "user" | "model" | "blocked" | "error",
          content: msg.content,
        });
      }
    }
  }, [conversationMessages, activeConversationId]);

  // Auto-select model when resuming a conversation
  const { data: conversations } = useQuery({
    queryKey: ["conversations"],
  });

  useEffect(() => {
    if (activeConversationId && Array.isArray(conversations)) {
      const conv = conversations.find((c: { id: string; model_id: string }) => c.id === activeConversationId);
      if (conv) {
        setSelectedModel(conv.model_id);
      }
    }
  }, [activeConversationId, conversations, setSelectedModel]);

  const sendMutation = useMutation({
    mutationFn: ({ message, modelId }: { message: string; modelId: string }) =>
      sendChatMessage(message, modelId, activeConversationId),
    onMutate: () => setLoading(true),
    onSettled: () => setLoading(false),
  });

  const handleSend = (message: string) => {
    if (!selectedModel) return;

    addMessage({
      id: crypto.randomUUID(),
      role: "user",
      content: message,
    });

    sendMutation.mutate(
      { message, modelId: selectedModel },
      {
        onSuccess: (response) => {
          // Track new conversation
          if (response.conversation_id && !activeConversationId) {
            setActiveConversation(response.conversation_id);
            // Re-add user message since setActiveConversation clears messages
            useChatStore.getState().addMessage({
              id: crypto.randomUUID(),
              role: "user",
              content: message,
            });
          }

          if (response.status === "allowed") {
            addMessage({
              id: crypto.randomUUID(),
              role: "model",
              content: response.content,
              modelId: response.model_id ?? undefined,
              providerId: response.provider_id ?? undefined,
            });
          } else if (response.status === "blocked") {
            addMessage({
              id: crypto.randomUUID(),
              role: "blocked",
              content: response.content,
              riskCategories: response.risk_categories ?? undefined,
              revisionHint: response.revision_hint ?? undefined,
            });
          } else {
            addMessage({
              id: crypto.randomUUID(),
              role: "error",
              content: response.content,
            });
          }

          // Refresh sidebar
          queryClient.invalidateQueries({ queryKey: ["conversations"] });
        },
        onError: (error) => {
          addMessage({
            id: crypto.randomUUID(),
            role: "error",
            content: error instanceof Error ? error.message : "Failed to send message",
          });
        },
      }
    );
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <ConversationSidebar />

      {/* Chat area */}
      <div className="flex flex-1 flex-col">
        {/* Model selector header */}
        <div className="border-b border-gray-200 bg-white px-4 py-3">
          <ModelSelector />
        </div>

        {/* Messages area */}
        <ChatMessages />

        {/* Input area */}
        <ChatInput onSend={handleSend} />
      </div>
    </div>
  );
}
