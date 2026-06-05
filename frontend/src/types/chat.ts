export type QuickActionMode =
  | "symptoms"
  | "appointment"
  | "mental_health"
  | "lab_results";

export type LabResultStatus = "low" | "normal" | "high" | "unknown";

export interface Helpline {
  name: string;
  phone: string | null;
  text: string | null;
  url: string | null;
  region: string;
}

export interface LabResultItem {
  test_id: string;
  name: string;
  value: number;
  unit: string;
  status: LabResultStatus;
  reference_range: string;
  note: string;
}

export interface MessageMetadata {
  crisis_detected: boolean;
  helplines: Helpline[];
  region: string;
  lab_results?: LabResultItem[];
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: Date;
  metadata?: MessageMetadata;
}

export interface Conversation {
  id: string;
  title: string;
  mode: QuickActionMode | null;
  updatedAt: Date;
}

export interface QuickActionDefinition {
  mode: QuickActionMode;
  title: string;
  subtitle: string;
  starterMessage: string;
}
