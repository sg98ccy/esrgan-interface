// ============================================================
// Processing Metadata Component
// ============================================================

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProcessingMetadataProps } from "@/types/props";

export function ProcessingMetadata({ metadata }: ProcessingMetadataProps) {
  if (!metadata) {
    return null;
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Processing Metrics</CardTitle>
      </CardHeader>
      <CardContent>
        <dl className="grid grid-cols-2 gap-4">
          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
              Input Dimensions
            </dt>
            <dd className="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-100">
              {metadata.input_dimensions}
            </dd>
          </div>

          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
              Output Dimensions
            </dt>
            <dd className="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-100">
              {metadata.output_dimensions}
            </dd>
          </div>

          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
              Scale Factor
            </dt>
            <dd className="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-100">
              {metadata.scale}x
            </dd>
          </div>

          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
              Total Processing Time
            </dt>
            <dd className="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-100">
              {metadata.processing_time}
            </dd>
          </div>

          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
              AI Upscaling Time
            </dt>
            <dd className="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-100">
              {metadata.upscaling_time}
            </dd>
          </div>

          <div>
            <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">
              Encoding Time
            </dt>
            <dd className="mt-1 text-lg font-semibold text-gray-900 dark:text-gray-100">
              {metadata.encoding_time}
            </dd>
          </div>
        </dl>
      </CardContent>
    </Card>
  );
}
