import { FlaskConical } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import type { LabResultItem, LabResultStatus } from "@/types/chat";

interface LabResultsPanelProps {
  results: LabResultItem[];
}

const statusVariant: Record<
  LabResultStatus,
  "success" | "warning" | "danger" | "neutral" | "info"
> = {
  normal: "success",
  high: "warning",
  low: "info",
  unknown: "neutral",
};

const statusLabel: Record<LabResultStatus, string> = {
  normal: "Normal",
  high: "High",
  low: "Low",
  unknown: "Check range",
};

export function LabResultsPanel({ results }: LabResultsPanelProps) {
  if (results.length === 0) {
    return null;
  }

  return (
    <div
      className="mt-3 rounded-xl border border-mediassist-border bg-slate-50 p-3"
      role="region"
      aria-label="Parsed lab results"
    >
      <div className="mb-2 flex items-center gap-2 text-mediassist-text">
        <FlaskConical className="h-4 w-4 shrink-0 text-mediassist-primary" aria-hidden />
        <p className="text-xs font-semibold uppercase tracking-wide">
          Parsed lab values
        </p>
      </div>
      <div className="space-y-2">
        {results.map((result) => (
          <div
            key={`${result.test_id}-${result.value}`}
            className="rounded-lg border border-white bg-white px-3 py-2 shadow-sm"
          >
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-medium text-mediassist-text">{result.name}</p>
              <Badge variant={statusVariant[result.status]}>
                {statusLabel[result.status]}
              </Badge>
            </div>
            <p className="mt-1 text-sm text-mediassist-text">
              <span className="font-semibold tabular-nums">
                {result.value} {result.unit}
              </span>
              <span className="text-mediassist-muted">
                {" "}
                · ref {result.reference_range}
              </span>
            </p>
            {result.note ? (
              <p className="mt-1 text-xs leading-relaxed text-mediassist-muted">
                {result.note}
              </p>
            ) : null}
          </div>
        ))}
      </div>
    </div>
  );
}
