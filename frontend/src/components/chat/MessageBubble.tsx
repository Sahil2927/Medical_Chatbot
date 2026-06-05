import type { Message } from "@/types/chat";
import { cn } from "@/lib/cn";
import { MessageMetadata } from "./MessageMetadata";

interface MessageBubbleProps {
  message: Message;
}

function formatTime(date: Date): string {
  return date.toLocaleTimeString([], { hour: "numeric", minute: "2-digit" });
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div
      className={cn(
        "flex w-full",
        isUser ? "justify-end" : "justify-start",
      )}
    >
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed shadow-sm sm:max-w-[75%]",
          isUser
            ? "rounded-br-md bg-mediassist-primary text-white"
            : "rounded-bl-md border border-mediassist-border bg-white text-mediassist-text",
        )}
      >
        <p className="whitespace-pre-wrap break-words">{message.content}</p>
        {!isUser && message.metadata ? (
          <MessageMetadata metadata={message.metadata} />
        ) : null}
        <span
          className={cn(
            "mt-1 block text-[10px]",
            isUser ? "text-teal-100" : "text-mediassist-muted",
          )}
        >
          {formatTime(message.createdAt)}
        </span>
      </div>
    </div>
  );
}
