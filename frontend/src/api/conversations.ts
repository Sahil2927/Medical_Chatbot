import { apiRequest } from "./client";
import { apiFormRequest } from "./client";
import type {
  AttachmentUploadDto,
  ConversationDto,
  ConversationListDto,
  CreateConversationBody,
  CreateMessageBody,
  MessageExchangeDto,
  MessageListDto,
  MockStatusDto,
} from "./types";

export function fetchMockStatus(): Promise<MockStatusDto> {
  return apiRequest<MockStatusDto>("/api/mock/status");
}

export function listConversations(): Promise<ConversationListDto> {
  return apiRequest<ConversationListDto>("/api/conversations");
}

export function createConversation(
  body: CreateConversationBody,
): Promise<ConversationDto> {
  return apiRequest<ConversationDto>("/api/conversations", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export function getConversationMessages(
  conversationId: string,
): Promise<MessageListDto> {
  return apiRequest<MessageListDto>(
    `/api/conversations/${conversationId}/messages`,
  );
}

export function sendMessage(
  conversationId: string,
  body: CreateMessageBody,
): Promise<MessageExchangeDto> {
  return apiRequest<MessageExchangeDto>(
    `/api/conversations/${conversationId}/messages`,
    {
      method: "POST",
      body: JSON.stringify(body),
    },
  );
}

export function uploadAttachment(
  conversationId: string,
  file: File,
): Promise<AttachmentUploadDto> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFormRequest<AttachmentUploadDto>(
    `/api/conversations/${conversationId}/attachments`,
    formData,
  );
}
