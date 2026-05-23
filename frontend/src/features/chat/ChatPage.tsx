import { useEffect } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { fetchConversationMessages } from "../../lib/api";
import { useChatStore } from "../../stores/chatStore";
import { useAuthStore } from "../../stores/authStore";
import { useStreamChat } from "./useStreamChat";
import ConversationSidebar from "./ConversationSidebar";
import ModelSelector from "./ModelSelector";
import ChatMessages from "./ChatMessages";
import ChatInput from "./ChatInput";
import StreamingMessage from "./StreamingMessage";
import { Settings, LogOut } from "lucide-react";

export default function ChatPage() {
  const queryClient = useQueryClient();
  const selectedModel = useChatStore((s) => s.selectedModel);
  const addMessage = useChatStore((s) => s.addMessage);
  const setLoading = useChatStore((s) => s.setLoading);
  const activeConversationId = useChatStore((s) => s.activeConversationId);
  const setActiveConversation = useChatStore((s) => s.setActiveConversation);
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);

  const { streamMessage, isStreaming, streamContent, degraded, reset } =
    useStreamChat();

  // Fetch messages when a conversation is selected
  const { data: conversationMessages, error: conversationError } = useQuery({
    queryKey: ["conversations", activeConversationId, "messages"],
    queryFn: () => fetchConversationMessages(activeConversationId!),
    enabled: !!activeConversationId,
  });

  // Clear stale conversation if we get a 403 (e.g. different user session)
  useEffect(() => {
    if (conversationError && conversationError.message.includes("403")) {
      setActiveConversation(null);
    }
  }, [conversationError, setActiveConversation]);

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
          riskCategories: msg.extra?.risk_categories,
        });
      }
    }
  }, [conversationMessages, activeConversationId]);

  const handleSend = async (message: string) => {
    if (!selectedModel) return;

    addMessage({
      id: crypto.randomUUID(),
      role: "user",
      content: message,
    });

    setLoading(true);
    reset();

    const result = await streamMessage(message, selectedModel, activeConversationId);

    setLoading(false);

    if (result?.conversationId && !activeConversationId) {
      setActiveConversation(result.conversationId);
      useChatStore.getState().addMessage({
        id: crypto.randomUUID(),
        role: "user",
        content: message,
      });
    }

    if (!result) {
      // Stream failed (error was set inside hook state, nothing to display here)
    } else if (result.error) {
      addMessage({
        id: crypto.randomUUID(),
        role: "error",
        content: result.error,
      });
    } else if (result.blocked) {
      // Output blocked by safety policy — show block message persistently
      if (result.blocked.conversationId && !activeConversationId) {
        setActiveConversation(result.blocked.conversationId);
      }
      addMessage({
        id: result.blocked.messageId || crypto.randomUUID(),
        role: "blocked",
        content: result.blocked.message,
        riskCategories: result.blocked.categories,
      });
    } else if (result) {
      // Use result.segments (not streamContent state) to avoid stale closure
      const finalContent = result.segments
        .map((seg) => (seg.type === "text" ? seg.content : seg.label))
        .join("");
      if (finalContent) {
        addMessage({
          id: result.messageId || crypto.randomUUID(),
          role: "model",
          content: finalContent,
        });
      }
    }

    queryClient.invalidateQueries({ queryKey: ["conversations"] });
  };

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      <ConversationSidebar />

      {/* Chat area */}
      <div className="flex flex-1 flex-col">
        {/* Model selector header */}
        <div className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3">
          <ModelSelector />
          <div className="flex items-center gap-3">
            {user?.role === "admin" && (
              <a
                href="/admin"
                className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:text-indigo-800 font-medium"
              >
                <Settings className="w-4 h-4" />
                管理后台
              </a>
            )}
            <button
              onClick={logout}
              className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
            >
              <LogOut className="w-4 h-4" />
              退出
            </button>
          </div>
        </div>

        {/* Messages area */}
        <ChatMessages />

        {/* Streaming message in progress */}
        {isStreaming && streamContent.length > 0 && (
          <div className="px-4 py-2">
            <StreamingMessage segments={streamContent} isStreaming={isStreaming} />
          </div>
        )}

        {/* Auto-degrade notice */}
        {degraded && (
          <div className="px-4 py-1">
            <span className="text-sm italic text-gray-500">
              连接中断，已切换为非流式模式
            </span>
          </div>
        )}

        {/* Input area */}
        <ChatInput onSend={handleSend} />
      </div>
    </div>
  );
}
