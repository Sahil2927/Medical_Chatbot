import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Brain,
  Calendar,
  FlaskConical,
} from "lucide-react";
import type { QuickActionDefinition, QuickActionMode } from "@/types/chat";

export interface QuickActionConfig extends QuickActionDefinition {
  icon: LucideIcon;
}

export const QUICK_ACTIONS: QuickActionConfig[] = [
  {
    mode: "symptoms",
    title: "Check Symptoms",
    subtitle: "Describe what you're feeling",
    starterMessage: "I'd like to check my symptoms.",
    icon: Activity,
  },
  {
    mode: "appointment",
    title: "Book Appointment",
    subtitle: "Find the right specialist",
    starterMessage: "I need to book an appointment.",
    icon: Calendar,
  },
  {
    mode: "mental_health",
    title: "Mental Health Check-in",
    subtitle: "Talk about how you're feeling",
    starterMessage: "I'd like a mental health check-in.",
    icon: Brain,
  },
  {
    mode: "lab_results",
    title: "Review Lab Results",
    subtitle: "Understand your test results",
    starterMessage: "I want help reviewing my lab results.",
    icon: FlaskConical,
  },
];

export const MODE_LABELS: Record<QuickActionMode, string> = {
  symptoms: "Symptoms",
  appointment: "Appointment",
  mental_health: "Mental Health",
  lab_results: "Lab Results",
};
