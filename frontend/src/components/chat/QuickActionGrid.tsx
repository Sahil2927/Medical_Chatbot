import { QUICK_ACTIONS } from "@/constants/quickActions";
import type { QuickActionMode } from "@/types/chat";
import { QuickActionCard } from "./QuickActionCard";

interface QuickActionGridProps {
  onSelect: (mode: QuickActionMode, starterMessage: string) => void;
}

export function QuickActionGrid({ onSelect }: QuickActionGridProps) {
  return (
    <div className="grid w-full max-w-3xl grid-cols-1 gap-4 sm:grid-cols-2">
      {QUICK_ACTIONS.map((action) => (
        <QuickActionCard
          key={action.mode}
          title={action.title}
          subtitle={action.subtitle}
          icon={action.icon}
          onClick={() => onSelect(action.mode, action.starterMessage)}
        />
      ))}
    </div>
  );
}
