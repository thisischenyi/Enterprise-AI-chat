import { useMutation } from "@tanstack/react-query";
import { sendChatMessage } from "../../lib/api";
import { useChatStore } from "../../stores/chatStore";
import ModelSelector from "./ModelSelector";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";

export default function ChatPage() {
  const selectedModel = useChatStore((s) => s.selectedModel);
  const addMessage = useChatStore((s) => s.addMessage);
  const setLoading = useChatStore((s) => s.setLoading);

  const sendMutation = useMutation({
    mutationFn: ({ message, modelId }: { message: string; modelId: string }) =>
      sendChatMessage(message, modelId),
    onMutate: () => setLoading(true),
    onSettled: () => setLoading(false),
  });

  const handleSend = (message: string) => {
    if (!selectedModel) return;

    // Add user message
    addMessage({
      id: crypto.randomUUID(),
      role: "user",
      content: message,
    });

    sendMutation.mutate(
      { message, modelId: selectedModel },
      {
        onSuccess: (response) => {
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
            // fail_closed
            addMessage({
              id: crypto.randomUUID(),
              role: "error",
              content: response.content,
            });
          }
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
    <div className="flex h-screen flex-col">
      {/* Model selector header */}
      <div className="border-b border-gray-200 bg-white px-4 py-3">
        <ModelSelector />
      </div>

      {/* Messages area */}
      <ChatMessages />

      {/* Input area */}
      <ChatInput onSend={handleSend} />
    </div>
  );
}
