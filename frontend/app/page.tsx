// ============================================================
// ESRGAN Interface - Main Page
// ============================================================

"use client";

import { useState, useEffect } from "react";
import { ImageUpload } from "@/components/ImageUpload";
import { ImagePreview } from "@/components/ImagePreview";
import { ProcessingStatus } from "@/components/ProcessingStatus";
import { ProgressBar } from "@/components/ProgressBar";
import { ProcessingStages } from "@/components/ProcessingStages";
import { ProcessingMetadata } from "@/components/ProcessingMetadata";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import {
  upscaleImage,
  connectToProgressStream,
  generateJobId,
} from "@/lib/api";
import { createPreviewUrl, revokePreviewUrl } from "@/lib/utils";
import type { ProcessingStage, UpscaleMetadata, ProgressEvent } from "@/types/api";

export default function Home() {
  // ============================================================
  // State Management
  // ============================================================

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [scale, setScale] = useState<number>(4);
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStage, setCurrentStage] = useState<ProcessingStage | null>(null);
  const [processedImage, setProcessedImage] = useState<string | null>(null);
  const [metadata, setMetadata] = useState<UpscaleMetadata | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progressConnection, setProgressConnection] = useState<EventSource | null>(null);

  // ============================================================
  // Effect: Handle Preview URL
  // ============================================================

  useEffect(() => {
    if (selectedFile) {
      const url = createPreviewUrl(selectedFile);
      setPreviewUrl(url);

      return () => {
        revokePreviewUrl(url);
      };
    } else {
      setPreviewUrl(null);
    }
  }, [selectedFile]);

  // ============================================================
  // Effect: Cleanup Progress Connection
  // ============================================================

  useEffect(() => {
    return () => {
      if (progressConnection) {
        progressConnection.close();
      }
    };
  }, [progressConnection]);

  // ============================================================
  // Handlers
  // ============================================================

  const handleImageSelect = (file: File | null) => {
    setSelectedFile(file);
    setProcessedImage(null);
    setMetadata(null);
    setError(null);
    setCurrentStage(null);
  };

  const handleReset = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
    setProcessedImage(null);
    setMetadata(null);
    setError(null);
    setCurrentStage(null);
    setIsProcessing(false);

    if (progressConnection) {
      progressConnection.close();
      setProgressConnection(null);
    }
  };

  const handleUpscale = async () => {
    if (!selectedFile) return;

    setIsProcessing(true);
    setError(null);
    setProcessedImage(null);
    setMetadata(null);
    setCurrentStage("initializing");

    const jobId = generateJobId();

    // Connect to SSE progress stream
    const eventSource = connectToProgressStream(
      jobId,
      (event: ProgressEvent) => {
        setCurrentStage(event.stage);
      },
      (err: Error) => {
        console.error("Progress stream error:", err);
        setError(err.message);
        setIsProcessing(false);
      },
      () => {
        console.log("Progress stream completed");
      }
    );

    setProgressConnection(eventSource);

    try {
      const result = await upscaleImage(selectedFile, scale, jobId);

      if (result.success) {
        setProcessedImage(result.processedImage);
        setMetadata(result.metadata);
        setCurrentStage("completed");
      } else {
        throw new Error(result.message || "Upscaling failed");
      }
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "An unknown error occurred";
      setError(errorMessage);
      setCurrentStage("error");
    } finally {
      setIsProcessing(false);
      if (eventSource) {
        setTimeout(() => eventSource.close(), 1000);
      }
    }
  };

  // ============================================================
  // Render
  // ============================================================

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-950 border-b border-gray-200 dark:border-gray-800">
        <div className="container mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            ESRGAN Image Upscaler
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Enhance your images with AI-powered super-resolution
          </p>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Upload Section */}
          <ImageUpload
            onImageSelect={handleImageSelect}
            selectedFile={selectedFile}
            disabled={isProcessing}
          />

          {/* Scale Selection */}
          {selectedFile && !isProcessing && !processedImage && (
            <Card>
              <CardContent className="pt-6">
                <Label className="text-base font-semibold mb-3 block">
                  Select Scale Factor
                </Label>
                <RadioGroup
                  value={scale.toString()}
                  onValueChange={(value) => setScale(parseInt(value))}
                >
                  <div className="flex items-center space-x-3 mb-2">
                    <RadioGroupItem value="2" id="scale-2" />
                    <Label htmlFor="scale-2">2x (Faster)</Label>
                  </div>

                  <div className="flex items-center space-x-3">
                    <RadioGroupItem value="4" id="scale-4" />
                    <Label htmlFor="scale-4">4x (Best Quality)</Label>
                  </div>
                </RadioGroup>

                <Button
                  onClick={handleUpscale}
                  disabled={!selectedFile || isProcessing}
                  className="mt-6 w-full"
                  size="lg"
                >
                  Start Upscaling ({scale}x)
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Processing Status */}
          {(isProcessing || currentStage) && (
            <ProcessingStatus
              isProcessing={isProcessing}
              currentStage={currentStage}
              error={error}
            />
          )}

          {/* Progress Bar */}
          {isProcessing && currentStage && (
            <ProgressBar progress={0} stage={currentStage} />
          )}

          {/* Processing Stages */}
          {isProcessing && currentStage && (
            <ProcessingStages currentStage={currentStage} />
          )}

          {/* Image Preview */}
          {(previewUrl || processedImage) && (
            <ImagePreview
              originalImage={previewUrl}
              processedImage={processedImage}
              metadata={metadata}
            />
          )}

          {/* Processing Metadata */}
          {metadata && <ProcessingMetadata metadata={metadata} />}

          {/* Reset Button */}
          {(processedImage || error) && (
            <div className="flex justify-center">
              <Button onClick={handleReset} variant="outline" size="lg">
                Process Another Image
              </Button>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-950">
        <div className="container mx-auto px-4 py-6 text-center text-sm text-gray-600 dark:text-gray-400">
          <p>Powered by Real-ESRGAN · Built with Next.js and FastAPI</p>
        </div>
      </footer>
    </div>
  );
}
