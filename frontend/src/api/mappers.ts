import type { ConversationDto, MessageDto, MessageExchangeMetadataDto } from "./types";
import type { Conversation, Message, MessageMetadata } from "@/types/chat";

function mapMetadata(dto: MessageExchangeMetadataDto): MessageMetadata {
  return {
    crisis_detected: dto.crisis_detected,
    helplines: dto.helplines,
    region: dto.region,
    lab_results: dto.lab_results,
  };
}

export function mapConversation(dto: ConversationDto): Conversation {
  return {
    id: dto.id,
    title: dto.title,
    mode: dto.mode,
    updatedAt: new Date(dto.updated_at),
  };
}

export function mapMessage(dto: MessageDto): Message {
  return {
    id: dto.id,
    role: dto.role,
    content: dto.content,
    createdAt: new Date(dto.created_at),
    metadata: dto.metadata ? mapMetadata(dto.metadata) : undefined,
  };
}

export function mapMessages(dtos: MessageDto[]): Message[] {
  return dtos.map(mapMessage);
}
