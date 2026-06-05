import { AlertTriangle, ExternalLink, MessageSquare, Phone } from "lucide-react";
import type { MessageMetadata } from "@/types/chat";

interface CrisisHelplinePanelProps {
  metadata: MessageMetadata;
}

export function CrisisHelplinePanel({ metadata }: CrisisHelplinePanelProps) {
  if (!metadata.crisis_detected || metadata.helplines.length === 0) {
    return null;
  }

  return (
    <div
      className="mt-3 rounded-xl border border-amber-200 bg-amber-50 p-3"
      role="region"
      aria-label="Crisis support resources"
    >
      <div className="mb-2 flex items-center gap-2 text-amber-900">
        <AlertTriangle className="h-4 w-4 shrink-0" aria-hidden />
        <p className="text-xs font-semibold uppercase tracking-wide">
          Crisis support — reach out now
        </p>
      </div>
      <ul className="space-y-2">
        {metadata.helplines.map((helpline) => (
          <li
            key={`${helpline.name}-${helpline.phone ?? helpline.text}`}
            className="rounded-lg border border-amber-100 bg-white px-3 py-2"
          >
            <p className="text-sm font-medium text-mediassist-text">{helpline.name}</p>
            <div className="mt-1 flex flex-wrap gap-x-3 gap-y-1 text-xs text-mediassist-muted">
              {helpline.phone ? (
                <a
                  href={`tel:${helpline.phone.replace(/\s/g, "")}`}
                  className="inline-flex items-center gap-1 text-mediassist-primary hover:underline"
                >
                  <Phone className="h-3 w-3" aria-hidden />
                  {helpline.phone}
                </a>
              ) : null}
              {helpline.text ? (
                <span className="inline-flex items-center gap-1">
                  <MessageSquare className="h-3 w-3" aria-hidden />
                  Text: {helpline.text}
                </span>
              ) : null}
              {helpline.url ? (
                <a
                  href={helpline.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-mediassist-primary hover:underline"
                >
                  <ExternalLink className="h-3 w-3" aria-hidden />
                  Website
                </a>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
