// ============================================================
// API Client for ESRGAN Backend
// ============================================================

import {
  UpscaleResponse,
  ProgressEvent,
  ScalesResponse,
  HealthResponse,
} from "@/types/api";

// ============================================================
// Configuration
// ============================================================

// API routes are proxied through Next.js /api routes
const API_PREFIX = "/api/esrgan";

// For direct backend connection (optional, for SSE)
const BACKEND_URL =
  (typeof window !== "undefined" && (window as any).BACKEND_URL) ||
  "http://localhost:8000";

// ============================================================
// API Client Functions
// ============================================================

/**
 * Upload and upscale an image
 */
export async function upscaleImage(
  file: File,
  scale: number = 4,
  jobId?: string
): Promise<UpscaleResponse> {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("scale", scale.toString());

  if (jobId) {
    formData.append("job_id", jobId);
  }

  // Use Next.js API proxy and specify backend endpoint via query param
  const response = await fetch(`${API_PREFIX}?endpoint=upscale`, {
    method: "POST",
    body: formData,
  });
  

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || `Upload failed: ${response.statusText}`
    );
  }

  return response.json();
}

/**
 * Connect to Server-Sent Events stream for progress updates
 * Note: SSE connects directly to backend to avoid Next.js timeout issues
 */
export function connectToProgressStream(
  jobId: string,
  onProgress: (event: ProgressEvent) => void,
  onError: (error: Error) => void,
  onComplete: () => void
): EventSource {
  const eventSource = new EventSource(`${BACKEND_URL}/progress/${jobId}`);

  let _streamFinished = false;

  eventSource.onmessage = (event) => {
    try {
      const data: ProgressEvent = JSON.parse(event.data);

      if (data.error) {
        _streamFinished = true;
        onError(new Error(data.error));
        try {
          eventSource.close();
        } catch (e) {}
        return;
      }

      onProgress(data);

      // Close connection when completed or errored
      if (data.stage === "completed" || data.stage === "error") {
        _streamFinished = true;
        setTimeout(() => {
          try {
            eventSource.close();
          } catch (e) {}
          try {
            onComplete();
          } catch (e) {}
        }, 500);
      }
    } catch (err) {
      onError(
        err instanceof Error ? err : new Error("Failed to parse progress event")
      );
    }
  };

  eventSource.onerror = (err) => {
    // EventSource fires `onerror` when the connection is broken or closed.
    // Distinguish a normal/expected close from a real network error:
    // - readyState === 2 (CLOSED) often indicates the server closed the stream
    //   after sending completion — treat this as successful completion.
    // If the stream already delivered a terminal event (completed/error),
    // treat this onerror as a normal close and do not surface an error.
    if (_streamFinished) {
      console.debug("SSE onerror after terminal event — treating as closed");
      try {
        onComplete();
      } catch (e) {}
    } else if (eventSource.readyState === EventSource.CLOSED) {
      // If the connection is closed and we didn't see a terminal event,
      // treat it as a non-diagnostic close (some servers close without final message).
      console.debug("SSE closed by server without terminal event");
      try {
        onComplete();
      } catch (e) {}
    } else {
      console.error("SSE connection error:", err);
      onError(new Error("Connection to server lost"));
    }

    // Ensure the connection is cleaned up
    try {
      eventSource.close();
    } catch (e) {
      /* ignore */
    }
  };

  return eventSource;
}

/**
 * Get available scaling factors
 */
export async function getScales(): Promise<ScalesResponse> {
  const response = await fetch(`${API_PREFIX}?endpoint=scales`);

  if (!response.ok) {
    throw new Error(`Failed to fetch scales: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Check backend health status
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_PREFIX}?endpoint=health`);

  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Validate image file before upload
 */
export function validateImageFile(file: File): {
  valid: boolean;
  error?: string;
} {
  const maxSize = 20 * 1024 * 1024; // 20MB
  const allowedTypes = ["image/png", "image/jpeg", "image/jpg", "image/webp"];

  if (!allowedTypes.includes(file.type)) {
    return {
      valid: false,
      error: `Unsupported file type: ${file.type}. Please upload PNG, JPEG, or WebP images.`,
    };
  }

  if (file.size > maxSize) {
    return {
      valid: false,
      error: `File too large: ${(file.size / 1024 / 1024).toFixed(2)}MB. Maximum size is 20MB.`,
    };
  }

  return { valid: true };
}

/**
 * Generate a unique job ID
 */
export function generateJobId(): string {
  return `job_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
}
