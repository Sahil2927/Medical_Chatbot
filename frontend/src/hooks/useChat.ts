import { useCallback, useEffect, useMemo, useState } from "react";
import {
  createConversation,
  getConversationMessages,
  listConversations,
  sendMessage,
  uploadAttachment,
} from "@/api/conversations";
import { ApiError } from "@/api/client";
import { mapConversation, mapMessage, mapMessages } from "@/api/mappers";
import type { Conversation, Message, QuickActionMode } from "@/types/chat";

export function useChat() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messagesByConversation, setMessagesByConversation] = useState<
    Record<string, Message[]>
  >({});
  const [activeConversationId, setActiveConversationId] = useState<string | null>(
    null,
  );
  const [draft, setDraft] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const activeMessages = useMemo(() => {
    if (!activeConversationId) {
      return [];
    }
    return messagesByConversation[activeConversationId] ?? [];
  }, [activeConversationId, messagesByConversation]);

  const showWelcome =
    activeConversationId === null || activeMessages.length === 0;

  const refreshConversations = useCallback(async () => {
    const data = await listConversations();
    setConversations(data.conversations.map(mapConversation));
  }, []);

  const loadMessages = useCallback(async (conversationId: string) => {
    const data = await getConversationMessages(conversationId);
    setMessagesByConversation((prev) => ({
      ...prev,
      [conversationId]: mapMessages(data.messages),
    }));
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function bootstrap() {
      setIsLoading(true);
      setError(null);
      try {
        await refreshConversations();
      } catch (err) {
        if (!cancelled) {
          const message =
            err instanceof ApiError
              ? err.message
              : "Could not reach MediAssist API. Start the backend on port 8080.";
          setError(message);
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    bootstrap();
    return () => {
      cancelled = true;
    };
  }, [refreshConversations]);

  const applyExchange = useCallback(
    (
      conversationId: string,
      userMessage: Message,
      assistantMessage: Message,
      conversation?: Conversation,
    ) => {
      setMessagesByConversation((prev) => ({
        ...prev,
        [conversationId]: [
          ...(prev[conversationId] ?? []),
          userMessage,
          assistantMessage,
        ],
      }));

      if (conversation) {
        setConversations((prev) => {
          const exists = prev.some((item) => item.id === conversation.id);
          if (exists) {
            return prev.map((item) =>
              item.id === conversation.id ? conversation : item,
            );
          }
          return [conversation, ...prev];
        });
      } else {
        void refreshConversations();
      }
    },
    [refreshConversations],
  );

  const sendUserMessage = useCallback(
    async (content: string, mode?: QuickActionMode | null) => {
      const trimmed = content.trim();
      if (!trimmed || isSending) {
        return;
      }

      setIsSending(true);
      setError(null);

      try {
        let conversationId = activeConversationId;

        if (!conversationId) {
          const created = await createConversation({
            mode: mode ?? undefined,
            content: trimmed,
          });
          conversationId = created.id;
          setActiveConversationId(created.id);
          await loadMessages(conversationId);
        } else {
          const exchange = await sendMessage(conversationId, {
            content: trimmed,
            mode: mode ?? undefined,
          });
          applyExchange(
            conversationId,
            mapMessage(exchange.user_message),
            mapMessage(exchange.assistant_message),
            mapConversation(exchange.conversation),
          );
        }

        setDraft("");
        await refreshConversations();
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : "Failed to send message. Please try again.";
        setError(message);
      } finally {
        setIsSending(false);
      }
    },
    [
      activeConversationId,
      applyExchange,
      isSending,
      refreshConversations,
    ],
  );

  const handleQuickAction = useCallback(
    async (mode: QuickActionMode, starterMessage: string) => {
      if (isSending) {
        return;
      }

      setIsSending(true);
      setError(null);

      try {
        const created = await createConversation({
          mode,
          content: starterMessage,
        });
        setActiveConversationId(created.id);
        await loadMessages(created.id);
        await refreshConversations();
        setDraft("");
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : "Failed to start conversation. Please try again.";
        setError(message);
      } finally {
        setIsSending(false);
      }
    },
    [isSending, loadMessages, refreshConversations],
  );

  const startNewConversation = useCallback(() => {
    setActiveConversationId(null);
    setDraft("");
    setError(null);
  }, []);

  const selectConversation = useCallback(
    async (id: string) => {
      setActiveConversationId(id);
      setDraft("");
      setError(null);

      if (messagesByConversation[id]) {
        return;
      }

      try {
        await loadMessages(id);
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : "Failed to load messages.";
        setError(message);
      }
    },
    [loadMessages, messagesByConversation],
  );

  const dismissError = useCallback(() => setError(null), []);

  const attachFile = useCallback(
    async (file: File) => {
      if (isSending) {
        return;
      }

      setIsSending(true);
      setError(null);

      try {
        let conversationId = activeConversationId;
        if (!conversationId) {
          const created = await createConversation({ mode: "lab_results" });
          conversationId = created.id;
          setActiveConversationId(created.id);
        }

        const result = await uploadAttachment(conversationId, file);
        if (result.message_exchange) {
          applyExchange(
            conversationId,
            mapMessage(result.message_exchange.user_message),
            mapMessage(result.message_exchange.assistant_message),
            mapConversation(result.message_exchange.conversation),
          );
        } else {
          await loadMessages(conversationId);
        }
        await refreshConversations();
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : "Failed to upload file. Please try again.";
        setError(message);
      } finally {
        setIsSending(false);
      }
    },
    [
      activeConversationId,
      applyExchange,
      isSending,
      loadMessages,
      refreshConversations,
    ],
  );

  return {
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
  };
}
