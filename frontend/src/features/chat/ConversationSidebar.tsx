import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, MessageSquare, Menu, Trash2 } from "lucide-react";
import { useState } from "react";
import { fetchConversations, deleteConversation } from "../../lib/api";
import type { ConversationSummary } from "../../lib/api";
import { useChatStore } from "../../stores/chatStore";

function getDateGroup(dateStr: string): string {
  const date = new Date(dateStr);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const weekAgo = new Date(today);
  weekAgo.setDate(weekAgo.getDate() - 7);

  if (date >= today) return "Today";
  if (date >= yesterday) return "Yesterday";
  if (date >= weekAgo) return "Previous 7 days";
  return date.toLocaleString("default", { month: "long", year: "numeric" });
}

function groupConversations(conversations: ConversationSummary[]) {
  const groups: Record<string, ConversationSummary[]> = {};
  for (const conv of conversations) {
    const group = getDateGroup(conv.updated_at);
    if (!groups[group]) groups[group] = [];
    groups[group].push(conv);
  }
  return groups;
}

export default function ConversationSidebar() {
  const queryClient = useQueryClient();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const activeConversationId = useChatStore((s) => s.activeConversationId);
  const setActiveConversation = useChatStore((s) => s.setActiveConversation);
  const startNewConversation = useChatStore((s) => s.startNewConversation);

  const { data: conversations, isLoading } = useQuery({
    queryKey: ["conversations"],
    queryFn: fetchConversations,
  });

  const deleteMutation = useMutation({
    mutationFn: deleteConversation,
    onSuccess: () => {
      if (confirmDeleteId === activeConversationId) {
        setActiveConversation(null);
        useChatStore.getState().clearMessages();
      }
      setConfirmDeleteId(null);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  const grouped = conversations ? groupConversations(conversations) : {};

  const sidebarContent = (
    <div className="flex h-screen w-[280px] flex-col border-r border-gray-200 bg-gray-50">
      {/* New conversation button */}
      <div className="p-4">
        <button
          onClick={startNewConversation}
          className="flex w-full items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          <Plus size={16} />
          New conversation
        </button>
      </div>

      {/* Conversation list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading && (
          <div className="space-y-3 p-4">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-12 animate-pulse rounded bg-gray-200" />
            ))}
          </div>
        )}

        {!isLoading && conversations?.length === 0 && (
          <div className="p-4 text-center">
            <MessageSquare size={32} className="mx-auto mb-2 text-gray-400" />
            <p className="text-sm font-medium text-gray-700">No conversations yet</p>
            <p className="mt-1 text-xs text-gray-500">
              Start a new conversation to begin chatting with AI.
            </p>
          </div>
        )}

        {!isLoading &&
          Object.entries(grouped).map(([group, items]) => (
            <div key={group} className="mb-2">
              <p className="px-4 py-1 text-xs font-medium text-gray-500">{group}</p>
              {items.map((conv) => {
                const isActive = conv.id === activeConversationId;
                return (
                  <div
                    key={conv.id}
                    className="group relative flex items-center"
                  >
                    <button
                      onClick={() => {
                        setActiveConversation(conv.id);
                        useChatStore.getState().setSelectedModel(conv.model_id);
                      }}
                      className={`flex-1 px-4 py-2 text-left text-sm hover:bg-gray-100 ${
                        isActive ? "border-l-[3px] border-l-blue-600 bg-gray-100" : ""
                      }`}
                    >
                      <span className="block truncate">{conv.title}</span>
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setConfirmDeleteId(conv.id);
                      }}
                      className="absolute right-2 hidden p-1 text-gray-400 hover:text-red-600 group-hover:flex"
                      title="Delete conversation"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                );
              })}
            </div>
          ))}
      </div>

      {/* Delete confirmation dialog */}
      {confirmDeleteId && (
        <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/30">
          <div className="mx-4 rounded-lg bg-white p-4 shadow-lg">
            <p className="text-sm font-medium text-gray-900">
              确定要删除这个对话吗？
            </p>
            <p className="mt-1 text-xs text-gray-500">
              删除后无法恢复，所有消息将被清除。
            </p>
            <div className="mt-3 flex gap-2">
              <button
                onClick={() => setConfirmDeleteId(null)}
                className="rounded px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-100"
              >
                取消
              </button>
              <button
                onClick={() => deleteMutation.mutate(confirmDeleteId)}
                disabled={deleteMutation.isPending}
                className="rounded bg-red-600 px-3 py-1.5 text-sm text-white hover:bg-red-700 disabled:opacity-50"
              >
                {deleteMutation.isPending ? "删除中..." : "删除"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  return (
    <>
      {/* Mobile toggle */}
      <button
        onClick={() => setMobileOpen(!mobileOpen)}
        className="fixed left-2 top-2 z-50 rounded p-2 text-gray-600 hover:bg-gray-100 md:hidden"
      >
        <Menu size={20} />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/30 md:hidden"
          onClick={() => setMobileOpen(false)}
        >
          <div onClick={(e) => e.stopPropagation()}>{sidebarContent}</div>
        </div>
      )}

      {/* Desktop sidebar */}
      <div className="hidden md:flex">{sidebarContent}</div>
    </>
  );
}