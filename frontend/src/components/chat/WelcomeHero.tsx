import { Stethoscope } from "lucide-react";

export function WelcomeHero() {
  return (
    <div className="mb-10 flex flex-col items-center text-center">
      <div
        className="mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-mediassist-primary-light"
        aria-hidden
      >
        <Stethoscope
          className="h-7 w-7 text-mediassist-primary"
          strokeWidth={2}
        />
      </div>
      <h1 className="text-2xl font-bold tracking-tight text-mediassist-text sm:text-[1.75rem]">
        Hello, I&apos;m MediAssist
      </h1>
      <p className="mt-2 max-w-md text-sm leading-relaxed text-mediassist-muted sm:text-base">
        How can I help you today? Ask me about symptoms, medications, wellness
        tips, or anything health-related.
      </p>
    </div>
  );
}
