// ============================================================
// Image Preview Component
// ============================================================

"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ImagePreviewProps } from "@/types/props";
import { downloadBase64Image } from "@/lib/utils";

export function ImagePreview({
  originalImage,
  processedImage,
  metadata,
}: ImagePreviewProps) {
  if (!originalImage && !processedImage) {
    return null;
  }

  const handleDownload = () => {
    if (processedImage) {
      downloadBase64Image(processedImage, "upscaled-image.png");
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Image Comparison</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Original Image */}
          {originalImage && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Original
              </h3>
              <div className="relative border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-gray-50 dark:bg-gray-900">
                <img
                  src={originalImage}
                  alt="Original"
                  className="w-full h-auto"
                />
              </div>
              {metadata && (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {metadata.input_dimensions}
                </p>
              )}
            </div>
          )}

          {/* Processed Image */}
          {processedImage && (
            <div className="space-y-2">
              <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">
                Upscaled ({metadata?.scale}x)
              </h3>
              <div className="relative border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden bg-gray-50 dark:bg-gray-900">
                <img
                  src={processedImage}
                  alt="Upscaled"
                  className="w-full h-auto"
                />
              </div>
              {metadata && (
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {metadata.output_dimensions}
                </p>
              )}
            </div>
          )}
        </div>

        {/* Metadata Section */}
        {metadata && processedImage && (
          <div className="mt-6 p-4 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <h4 className="text-sm font-semibold mb-2">Processing Metrics</h4>
            <dl className="grid grid-cols-2 gap-2 text-sm">
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Scale Factor:</dt>
                <dd className="font-medium">{metadata.scale}x</dd>
              </div>
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Total Time:</dt>
                <dd className="font-medium">{metadata.processing_time}</dd>
              </div>
              <div>
                <dt className="text-gray-500 dark:text-gray-400">AI Upscaling:</dt>
                <dd className="font-medium">{metadata.upscaling_time}</dd>
              </div>
              <div>
                <dt className="text-gray-500 dark:text-gray-400">Encoding:</dt>
                <dd className="font-medium">{metadata.encoding_time}</dd>
              </div>
            </dl>
          </div>
        )}

        {/* Download Button */}
        {processedImage && (
          <div className="mt-4 flex justify-end">
            <Button onClick={handleDownload}>Download Upscaled Image</Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
