import { Plus } from "lucide-react";
import { cn } from "@/lib/cn";

interface LogoProps {
  compact?: boolean;
  className?: string;
}

export function Logo({ compact = false, className }: LogoProps) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-mediassist-primary text-white shadow-sm">
        <Plus className="h-5 w-5" strokeWidth={2.5} />
      </div>
      {!compact && (
        <span className="text-lg font-semibold tracking-tight text-mediassist-text">
          MediAssist
        </span>
      )}
    </div>
  );
}
