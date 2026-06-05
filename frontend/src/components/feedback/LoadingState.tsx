import { Loader2 } from "lucide-react";
import { cn } from "@/lib/cn";

interface LoadingStateProps {
  label?: string;
  className?: string;
}

export function LoadingState({
  label = "Loading…",
  className,
}: LoadingStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 py-16 text-mediassist-muted",
        className,
      )}
      role="status"
      aria-live="polite"
    >
      <Loader2 className="h-8 w-8 animate-spin text-mediassist-primary" />
      <p className="text-sm">{label}</p>
    </div>
  );
}
