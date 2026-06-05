import { Badge } from "@/components/ui/Badge";
import { Logo } from "@/components/brand/Logo";

export function ChatHeader() {
  return (
    <header className="flex items-center justify-between border-b border-mediassist-border bg-white px-6 py-4">
      <Logo />
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
