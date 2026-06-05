import { Badge } from "@/components/ui/Badge";
import { MODE_LABELS } from "@/constants/quickActions";
import type { QuickActionMode } from "@/types/chat";

interface ChatHeaderProps {
  conversationTitle?: string | null;
  mode?: QuickActionMode | null;
  isWelcome?: boolean;
}

export function ChatHeader({
  conversationTitle,
  mode,
  isWelcome = false,
}: ChatHeaderProps) {
  return (
    <header className="flex items-center justify-between border-b border-mediassist-border bg-white px-6 py-5">
      <div className="min-w-0 flex-1 pr-4">
        {isWelcome ? (
          <h1 className="text-base font-semibold text-mediassist-text">Welcome</h1>
        ) : conversationTitle ? (
          <>
            <h1 className="truncate text-base font-semibold text-mediassist-text">
              {conversationTitle}
            </h1>
            {mode && (
              <p className="mt-0.5 text-xs text-mediassist-muted">
                {MODE_LABELS[mode]}
              </p>
            )}
          </>
        ) : null}
      </div>
      <Badge variant="success">
        <span
          className="h-1.5 w-1.5 rounded-full bg-emerald-500"
          aria-hidden
        />
        Online
      </Badge>
    </header>
  );
}
