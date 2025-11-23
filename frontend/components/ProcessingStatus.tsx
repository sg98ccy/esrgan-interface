// ============================================================
// Processing Status Component
// ============================================================

"use client";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { ProcessingStatusProps } from "@/types/props";

export function ProcessingStatus({
  isProcessing,
  currentStage,
  error,
}: ProcessingStatusProps) {
  if (error) {
    return (
      <Alert variant="destructive">
        <AlertDescription>
          <strong>Error:</strong> {error}
        </AlertDescription>
      </Alert>
    );
  }

  if (!isProcessing && !currentStage) {
    return null;
  }

  const getStatusMessage = () => {
    if (!currentStage) return "Initialising...";

    const messages: Record<string, string> = {
      initializing: "Initialising upscale request...",
      validating: "Validating image file...",
      loading_image: "Loading and decoding image...",
      preparing_model: "Preparing ESRGAN model...",
      preprocessing: "Preprocessing image data...",
      upscaling: "⚡ Running AI upscaling (this may take a while)...",
      postprocessing: "Postprocessing enhanced image...",
      encoding: "Encoding result...",
      completed: "✓ Upscaling completed successfully!",
      error: "An error occurred",
    };

    return messages[currentStage] || currentStage;
  };

  const isCompleted = currentStage === "completed";

  return (
    <Alert variant={isCompleted ? "default" : "default"}>
      <AlertDescription>
        <div className="flex items-center space-x-2">
          {!isCompleted && (
            <div className="animate-spin h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full" />
          )}
          <span>{getStatusMessage()}</span>
        </div>
      </AlertDescription>
    </Alert>
  );
}
