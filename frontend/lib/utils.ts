// ============================================================
// Utility Functions
// ============================================================

import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format file size in human-readable format
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";

  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

/**
 * Create a preview URL from File object
 */
export function createPreviewUrl(file: File): string {
  return URL.createObjectURL(file);
}

/**
 * Revoke a preview URL to free memory
 */
export function revokePreviewUrl(url: string): void {
  URL.revokeObjectURL(url);
}

/**
 * Download a base64 image
 */
export function downloadBase64Image(
  base64Data: string,
  filename: string = "upscaled-image.png"
): void {
  const link = document.createElement("a");
  link.href = base64Data;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

/**
 * Get stage progress percentage from stage name
 */
export function getStageProgress(stage: string): number {
  const progressMap: Record<string, number> = {
    initializing: 0,
    validating: 5,
    loading_image: 10,
    preparing_model: 20,
    preprocessing: 30,
    upscaling: 40,
    postprocessing: 80,
    encoding: 90,
    completed: 100,
    error: 0,
  };

  return progressMap[stage] || 0;
}

/**
 * Get human-readable stage description
 */
export function getStageDescription(stage: string): string {
  const descriptionMap: Record<string, string> = {
    initializing: "Initialising upscale request",
    validating: "Validating image file",
    loading_image: "Loading and decoding image",
    preparing_model: "Preparing ESRGAN model",
    preprocessing: "Preprocessing image data",
    upscaling: "Running AI upscaling (this may take a while)",
    postprocessing: "Postprocessing enhanced image",
    encoding: "Encoding result for transfer",
    completed: "Upscaling completed successfully",
    error: "An error occurred during processing",
  };

  return descriptionMap[stage] || stage;
}
