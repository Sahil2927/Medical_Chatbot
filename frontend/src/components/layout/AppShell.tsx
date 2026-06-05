import type { ReactNode } from "react";
import { Sidebar } from "./Sidebar";
import type { Conversation } from "@/types/chat";

interface AppShellProps {
  children: ReactNode;
  conversations: Conversation[];
  activeConversationId: string | null;
  onNewConversation: () => void;
  onSelectConversation: (id: string) => void;
}

export function AppShell({
  children,
  conversations,
  activeConversationId,
  onNewConversation,
  onSelectConversation,
}: AppShellProps) {
  return (
    <div className="flex h-full min-h-screen">
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewConversation={onNewConversation}
        onSelectConversation={onSelectConversation}
      />
      <main className="flex min-w-0 flex-1 flex-col bg-mediassist-canvas">
        {children}
      </main>
    </div>
  );
}
