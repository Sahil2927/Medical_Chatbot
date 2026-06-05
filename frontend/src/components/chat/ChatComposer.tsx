import { useRef } from "react";
import { Paperclip, Send } from "lucide-react";
import { IconButton } from "@/components/ui/IconButton";
import { cn } from "@/lib/cn";

const ACCEPTED_TYPES = ".pdf,.txt,application/pdf,text/plain";

interface ChatComposerProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  onAttach?: (file: File) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function ChatComposer({
  value,
  onChange,
  onSend,
  onAttach,
  disabled = false,
  placeholder = "Type your health question...",
}: ChatComposerProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (value.trim() && !disabled) {
      onSend();
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file && onAttach) {
      onAttach(file);
    }
    event.target.value = "";
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="border-t border-mediassist-border bg-white px-6 py-4"
    >
      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_TYPES}
        className="hidden"
        aria-hidden
        onChange={handleFileChange}
      />
      <div
        className={cn(
          "mx-auto flex max-w-3xl items-center gap-2 rounded-2xl border border-mediassist-border",
          "bg-slate-50 px-3 py-2 shadow-sm focus-within:border-mediassist-primary/50 focus-within:ring-2 focus-within:ring-mediassist-primary/20",
        )}
      >
        <IconButton
          icon={<Paperclip className="h-5 w-5" />}
          label="Attach document (PDF or plain text only)"
          disabled={disabled || !onAttach}
          size="sm"
          onClick={() => fileInputRef.current?.click()}
        />
        <input
          type="text"
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          disabled={disabled}
          maxLength={2000}
          className="min-w-0 flex-1 bg-transparent text-sm text-mediassist-text outline-none placeholder:text-mediassist-muted disabled:opacity-50"
          aria-label="Message input"
        />
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          aria-label="Send message"
          className={cn(
            "inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors",
            "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-mediassist-primary",
            "disabled:pointer-events-none disabled:opacity-40",
            value.trim() && !disabled
              ? "bg-mediassist-primary text-white hover:bg-mediassist-primary-hover"
              : "text-mediassist-muted",
          )}
        >
          <Send className="h-5 w-5" />
        </button>
      </div>
    </form>
  );
}
