import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cn } from "@/lib/cn";

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  icon: ReactNode;
  label: string;
  size?: "sm" | "md";
}

export function IconButton({
  icon,
  label,
  size = "md",
  className,
  ...props
}: IconButtonProps) {
  const sizeClass = size === "sm" ? "h-9 w-9" : "h-10 w-10";

  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-lg text-mediassist-muted",
        "transition-colors hover:bg-slate-100 hover:text-mediassist-primary",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-mediassist-primary",
        "disabled:pointer-events-none disabled:opacity-40",
        sizeClass,
        className,
      )}
      {...props}
    >
      {icon}
    </button>
  );
}
