// ============================================================
// Component Props Type Definitions
// ============================================================

import { ProcessingStage, UpscaleMetadata } from "./api";

export interface ImageUploadProps {
  onImageSelect: (file: File | null) => void;
  selectedFile: File | null;
  disabled?: boolean;
}

export interface ImagePreviewProps {
  originalImage: string | null;
  processedImage: string | null;
  metadata: UpscaleMetadata | null;
}

export interface ProcessingStatusProps {
  isProcessing: boolean;
  currentStage: ProcessingStage | null;
  error: string | null;
}

export interface ProgressBarProps {
  progress: number;
  stage: ProcessingStage | null;
}

export interface ProcessingStagesProps {
  currentStage: ProcessingStage | null;
  stages?: {
    stage: ProcessingStage;
    description: string;
  }[];
}

export interface ProcessingMetadataProps {
  metadata: UpscaleMetadata | null;
}
