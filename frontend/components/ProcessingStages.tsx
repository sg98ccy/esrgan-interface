// ============================================================
// Processing Stages Component
// ============================================================

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProcessingStagesProps } from "@/types/props";

const STAGES = [
  { stage: "initializing" as const, description: "Initialising" },
  { stage: "validating" as const, description: "Validating" },
  { stage: "loading_image" as const, description: "Loading Image" },
  { stage: "preparing_model" as const, description: "Preparing Model" },
  { stage: "preprocessing" as const, description: "Preprocessing" },
  { stage: "upscaling" as const, description: "AI Upscaling" },
  { stage: "postprocessing" as const, description: "Postprocessing" },
  { stage: "encoding" as const, description: "Encoding" },
  { stage: "completed" as const, description: "Completed" },
];

export function ProcessingStages({
  currentStage,
  stages = STAGES,
}: ProcessingStagesProps) {
  if (!currentStage) {
    return null;
  }

  const currentIndex = stages.findIndex((s) => s.stage === currentStage);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Processing Pipeline</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {stages.map((stage, index) => {
            const isActive = stage.stage === currentStage;
            const isCompleted = currentIndex > index;
            const isFuture = currentIndex < index;

            return (
              <div
                key={stage.stage}
                className={`
                  flex items-center space-x-3 p-2 rounded-md transition-colors
                  ${isActive ? "bg-blue-50 dark:bg-blue-950/30" : ""}
                `}
              >
                {/* Status Icon */}
                <div
                  className={`
                    flex items-center justify-center w-6 h-6 rounded-full text-xs font-medium
                    ${isCompleted ? "bg-green-500 text-white" : ""}
                    ${isActive ? "bg-blue-600 text-white animate-pulse" : ""}
                    ${isFuture ? "bg-gray-200 dark:bg-gray-700 text-gray-500" : ""}
                  `}
                >
                  {isCompleted ? "✓" : index + 1}
                </div>

                {/* Stage Description */}
                <span
                  className={`
                    text-sm font-medium
                    ${isActive ? "text-blue-700 dark:text-blue-300" : ""}
                    ${isCompleted ? "text-green-700 dark:text-green-300" : ""}
                    ${isFuture ? "text-gray-500 dark:text-gray-400" : ""}
                  `}
                >
                  {stage.description}
                </span>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
