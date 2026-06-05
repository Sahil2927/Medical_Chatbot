import type { QuickActionMode } from "@/types/chat";

export interface ConversationDto {
  id: string;
  title: string;
  mode: QuickActionMode | null;
  created_at: string;
  updated_at: string;
}

export interface MessageDto {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
  metadata?: MessageExchangeMetadataDto | null;
}

export interface ConversationListDto {
  conversations: ConversationDto[];
}

export interface MessageListDto {
  messages: MessageDto[];
}

export interface CreateConversationBody {
  title?: string;
  mode?: QuickActionMode;
  content?: string;
}

export interface CreateMessageBody {
  content: string;
  mode?: QuickActionMode;
}

export interface HelplineDto {
  name: string;
  phone: string | null;
  text: string | null;
  url: string | null;
  region: string;
}

export interface LabResultItemDto {
  test_id: string;
  name: string;
  value: number;
  unit: string;
  status: "low" | "normal" | "high" | "unknown";
  reference_range: string;
  note: string;
}

export interface MessageExchangeMetadataDto {
  crisis_detected: boolean;
  helplines: HelplineDto[];
  region: string;
  lab_results?: LabResultItemDto[];
}

export interface MessageExchangeDto {
  conversation: ConversationDto;
  user_message: MessageDto;
  assistant_message: MessageDto;
  metadata?: MessageExchangeMetadataDto | null;
}

export interface MockStatusDto {
  mock: boolean;
  version: string;
  supported_modes: QuickActionMode[];
}

export interface AttachmentDto {
  id: string;
  conversation_id: string;
  filename: string;
  content_type: string;
  size_bytes: number;
  created_at: string;
}

export interface AttachmentUploadDto {
  attachment: AttachmentDto;
  extracted_chars: number | null;
  message_exchange: MessageExchangeDto | null;
}

export interface ApiErrorBody {
  detail: string | { msg: string }[];
}
