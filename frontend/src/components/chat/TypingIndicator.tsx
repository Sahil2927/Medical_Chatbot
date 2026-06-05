export function TypingIndicator() {
  return (
    <div className="flex justify-start px-6 py-2">
      <div className="flex items-center gap-1 rounded-2xl rounded-bl-md border border-mediassist-border bg-white px-4 py-3 shadow-sm">
        <span className="h-2 w-2 animate-bounce rounded-full bg-mediassist-primary [animation-delay:-0.3s]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-mediassist-primary [animation-delay:-0.15s]" />
        <span className="h-2 w-2 animate-bounce rounded-full bg-mediassist-primary" />
      </div>
    </div>
  );
}
