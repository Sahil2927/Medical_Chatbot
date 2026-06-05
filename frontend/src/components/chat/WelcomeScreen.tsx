import { QuickActionGrid } from "./QuickActionGrid";
import { WelcomeHero } from "./WelcomeHero";
import type { QuickActionMode } from "@/types/chat";

interface WelcomeScreenProps {
  onQuickAction: (mode: QuickActionMode, starterMessage: string) => void;
}

export function WelcomeScreen({ onQuickAction }: WelcomeScreenProps) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center px-6 py-10">
      <WelcomeHero />
      <QuickActionGrid onSelect={onQuickAction} />
    </div>
  );
}
