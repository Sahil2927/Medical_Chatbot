import { AppShell } from "@/components/layout/AppShell";
import { ChatHeader } from "@/components/layout/ChatHeader";
import { ChatComposer } from "@/components/chat/ChatComposer";
import { MessageList } from "@/components/chat/MessageList";
import { TypingIndicator } from "@/components/chat/TypingIndicator";
import { WelcomeScreen } from "@/components/chat/WelcomeScreen";
import { ErrorBanner } from "@/components/feedback/ErrorBanner";
import { LoadingState } from "@/components/feedback/LoadingState";
import { useChat } from "@/hooks/useChat";

export function ChatPage() {
  const {
    conversations,
    activeConversationId,
    activeMessages,
    showWelcome,
    draft,
    setDraft,
    isLoading,
    isSending,
    error,
    dismissError,
    sendUserMessage,
    handleQuickAction,
    startNewConversation,
    selectConversation,
    attachFile,
  } = useChat();

  return (
    <AppShell
      conversations={conversations}
      activeConversationId={activeConversationId}
      onNewConversation={startNewConversation}
      onSelectConversation={(id) => {
        void selectConversation(id);
      }}
    >
      <ChatHeader />
      {error && <ErrorBanner message={error} onDismiss={dismissError} />}
      {isLoading ? (
        <LoadingState label="Connecting to MediAssist…" />
      ) : showWelcome ? (
        <WelcomeScreen
          onQuickAction={(mode, starter) => {
            void handleQuickAction(mode, starter);
          }}
        />
      ) : (
        <>
          <MessageList messages={activeMessages} />
          {isSending && <TypingIndicator />}
        </>
      )}
      <ChatComposer
        value={draft}
        onChange={setDraft}
        onSend={() => {
          void sendUserMessage(draft);
        }}
        disabled={isLoading || isSending}
        onAttach={(file) => {
          void attachFile(file);
        }}
      />
    </AppShell>
  );
}
