import type { LucideIcon } from "lucide-react";
import { Card } from "@/components/ui/Card";
import { cn } from "@/lib/cn";

export interface QuickActionCardProps {
  title: string;
  subtitle: string;
  icon: LucideIcon;
  onClick: () => void;
}

export function QuickActionCard({
  title,
  subtitle,
  icon: Icon,
  onClick,
}: QuickActionCardProps) {
  return (
    <Card
      interactive
      padding="md"
      role="button"
      tabIndex={0}
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick();
        }
      }}
      className={cn(
        "flex min-h-[120px] flex-col items-start gap-3",
        "bg-gradient-to-br from-white to-mediassist-primary-light/30",
      )}
    >
      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-mediassist-primary-light text-mediassist-primary">
        <Icon className="h-5 w-5" strokeWidth={2} aria-hidden />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-mediassist-text">{title}</h3>
        <p className="mt-0.5 text-xs text-mediassist-muted">{subtitle}</p>
      </div>
    </Card>
  );
}
