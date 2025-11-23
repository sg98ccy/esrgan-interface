// ============================================================
// Progress Bar Component
// ============================================================

"use client";

import { Progress } from "@/components/ui/progress";
import { ProgressBarProps } from "@/types/props";
import { getStageProgress, getStageDescription } from "@/lib/utils";

export function ProgressBar({ progress, stage }: ProgressBarProps) {
  const displayProgress = stage ? getStageProgress(stage) : progress;
  const description = stage ? getStageDescription(stage) : "";

  return (
    <div className="w-full space-y-2">
      <div className="flex justify-between items-center text-sm">
        <span className="text-gray-700 dark:text-gray-300">{description}</span>
        <span className="font-medium text-gray-900 dark:text-gray-100">
          {displayProgress}%
        </span>
      </div>
      <Progress value={displayProgress} />
    </div>
  );
}
