// ============================================================
// API Type Definitions
// ============================================================

export type ProcessingStage =
  | "initializing"
  | "validating"
  | "loading_image"
  | "preparing_model"
  | "preprocessing"
  | "upscaling"
  | "postprocessing"
  | "encoding"
  | "completed"
  | "error";

export interface UpscaleMetadata {
  input_dimensions: string;
  output_dimensions: string;
  scale: number;
  processing_time: string;
  upscaling_time: string;
  encoding_time: string;
}

export interface UpscaleResponse {
  success: boolean;
  processedImage: string;
  message: string;
  job_id: string;
  metadata: UpscaleMetadata;
}

export interface ProgressEvent {
  stage: ProcessingStage;
  description: string;
  progress: number;
  timestamp: string;
  job_id?: string;
  scale?: number;
  input_dimensions?: string;
  output_dimensions?: string;
  error?: string;
}

export interface ScalesResponse {
  scales: number[];
  default: number;
  loaded: number[];
}

export interface HealthResponse {
  status: string;
  modelLoaded: boolean;
  device: string;
  loaded_scales: number[];
  supported_scales: number[];
}
