import type { MessageMetadata as MessageMetadataType } from "@/types/chat";
import { CrisisHelplinePanel } from "./CrisisHelplinePanel";
import { LabResultsPanel } from "./LabResultsPanel";

interface MessageMetadataProps {
  metadata: MessageMetadataType;
}

export function MessageMetadata({ metadata }: MessageMetadataProps) {
  const hasCrisis = metadata.crisis_detected && metadata.helplines.length > 0;
  const hasLabResults = (metadata.lab_results?.length ?? 0) > 0;

  if (!hasCrisis && !hasLabResults) {
    return null;
  }

  return (
    <div className="space-y-0">
      {hasCrisis ? <CrisisHelplinePanel metadata={metadata} /> : null}
      {hasLabResults ? <LabResultsPanel results={metadata.lab_results!} /> : null}
    </div>
  );
}
