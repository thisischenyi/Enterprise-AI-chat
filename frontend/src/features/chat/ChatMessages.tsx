import { useChatStore, type ChatMessage } from "../../stores/chatStore";
import BlockedMessage from "./BlockedMessage";

function MessageBubble({ message }: { message: ChatMessage }) {
  if (message.role === "blocked") {
    return (
      <BlockedMessage
        content={message.content}
        riskCategories={message.riskCategories}
        revisionHint={message.revisionHint}
      />
    );
  }

  if (message.role === "error") {
    return (
      <div className="mx-4 my-2 rounded-lg border border-amber-200 bg-amber-50 p-3">
        <p className="text-sm text-amber-800">{message.content}</p>
      </div>
    );
  }

  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} px-4 py-1`}>
      <div
        className={`max-w-[75%] rounded-lg px-4 py-2 text-sm ${
          isUser
            ? "bg-blue-600 text-white"
            : "bg-gray-100 text-gray-900"
        }`}
      >
        {!isUser && message.modelId && (
          <p className="mb-1 text-xs font-medium text-gray-500">{message.modelId}</p>
        )}
        <p className="whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  );
}

export default function ChatMessages() {
  const messages = useChatStore((s) => s.messages);

  if (messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center text-gray-400">
        <p>Select a model and send a message to start chatting.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto py-4">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}
    </div>
  );
}
