import { AlertTriangle } from "lucide-react";
import { MEDICAL_DISCLAIMER } from "@/constants/disclaimer";

export function MedicalDisclaimer() {
  return (
    <div className="rounded-lg border border-amber-200/80 bg-amber-50/90 p-3">
      <div className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold text-amber-800">
        <AlertTriangle className="h-3.5 w-3.5 shrink-0" aria-hidden />
        Medical Disclaimer
      </div>
      <p className="text-[11px] leading-relaxed text-amber-900/90">
        {MEDICAL_DISCLAIMER}
      </p>
    </div>
  );
}
