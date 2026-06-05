import { MessageSquarePlus } from "lucide-react";
import { Logo } from "@/components/brand/Logo";
import { MedicalDisclaimer } from "@/components/legal/MedicalDisclaimer";
import { Button } from "@/components/ui/Button";
import { MODE_LABELS } from "@/constants/quickActions";
import { cn } from "@/lib/cn";
import type { Conversation } from "@/types/chat";

interface SidebarProps {
  conversations: Conversation[];
  activeConversationId: string | null;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
}

export function Sidebar({
  conversations,
  activeConversationId,
  onNewConversation,
  onSelectConversation,
}: SidebarProps) {
  return (
    <aside className="flex h-full w-[280px] shrink-0 flex-col border-r border-mediassist-border bg-white">
      <div className="border-b border-mediassist-border px-5 py-5">
        <Logo />
      </div>

      <div className="px-4 py-4">
        <Button
          variant="secondary"
          size="md"
          fullWidth
          leftIcon={<MessageSquarePlus className="h-4 w-4" />}
          onClick={onNewConversation}
        >
          New Conversation
        </Button>
      </div>

      <nav
        className="flex-1 overflow-y-auto px-3 scrollbar-thin"
        aria-label="Conversation history"
      >
        {conversations.length === 0 ? (
          <p className="px-2 py-4 text-center text-xs text-mediassist-muted">
            No conversations yet. Start a new chat or pick a quick action.
          </p>
        ) : (
          <ul className="space-y-1">
            {conversations.map((conversation) => (
              <li key={conversation.id}>
                <button
                  type="button"
                  onClick={() => onSelectConversation(conversation.id)}
                  className={cn(
                    "w-full rounded-lg px-3 py-2.5 text-left transition-colors",
                    activeConversationId === conversation.id
                      ? "bg-mediassist-primary-light text-mediassist-primary"
                      : "text-mediassist-text hover:bg-slate-50",
                  )}
                >
                  <span className="block truncate text-sm font-medium">
                    {conversation.title}
                  </span>
                  {conversation.mode && (
                    <span className="mt-0.5 block text-[11px] text-mediassist-muted">
                      {MODE_LABELS[conversation.mode]}
                    </span>
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </nav>

      <div className="mt-auto border-t border-mediassist-border p-4">
        <MedicalDisclaimer />
      </div>
    </aside>
  );
}
