# ============================================================
# Logging and Progress Tracking for ESRGAN Processing
# ============================================================

import logging
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
import json

# ============================================================
# Configure Logger
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("esrgan")


# ============================================================
# Processing Stage Definitions
# ============================================================

class ProcessingStage(str, Enum):
    """Enumeration of processing stages for frontend progress tracking"""
    INITIALIZING = "initializing"
    VALIDATING = "validating"
    LOADING_IMAGE = "loading_image"
    PREPARING_MODEL = "preparing_model"
    PREPROCESSING = "preprocessing"
    UPSCALING = "upscaling"
    POSTPROCESSING = "postprocessing"
    ENCODING = "encoding"
    COMPLETED = "completed"
    ERROR = "error"


# Stage metadata for frontend display
STAGE_METADATA: Dict[ProcessingStage, Dict[str, Any]] = {
    ProcessingStage.INITIALIZING: {
        "description": "Initializing upscale request",
        "progress": 0,
        "estimated_duration": 0.1
    },
    ProcessingStage.VALIDATING: {
        "description": "Validating image file",
        "progress": 5,
        "estimated_duration": 0.2
    },
    ProcessingStage.LOADING_IMAGE: {
        "description": "Loading and decoding image",
        "progress": 10,
        "estimated_duration": 0.5
    },
    ProcessingStage.PREPARING_MODEL: {
        "description": "Preparing ESRGAN model",
        "progress": 20,
        "estimated_duration": 0.3
    },
    ProcessingStage.PREPROCESSING: {
        "description": "Preprocessing image data",
        "progress": 30,
        "estimated_duration": 1.0
    },
    ProcessingStage.UPSCALING: {
        "description": "Running AI upscaling (this may take a while)",
        "progress": 40,
        "estimated_duration": 10.0
    },
    ProcessingStage.POSTPROCESSING: {
        "description": "Postprocessing enhanced image",
        "progress": 80,
        "estimated_duration": 1.0
    },
    ProcessingStage.ENCODING: {
        "description": "Encoding result for transfer",
        "progress": 90,
        "estimated_duration": 1.0
    },
    ProcessingStage.COMPLETED: {
        "description": "Upscaling completed successfully",
        "progress": 100,
        "estimated_duration": 0
    },
    ProcessingStage.ERROR: {
        "description": "An error occurred during processing",
        "progress": 0,
        "estimated_duration": 0
    }
}


# ============================================================
# Progress Event Generation
# ============================================================

def create_progress_event(
    stage: ProcessingStage,
    additional_info: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a progress event for streaming to frontend
    
    Args:
        stage: Current processing stage
        additional_info: Optional additional information (image dimensions, scale, etc.)
    
    Returns:
        Dictionary containing progress event data
    """
    metadata = STAGE_METADATA[stage]
    
    event = {
        "stage": stage.value,
        "description": metadata["description"],
        "progress": metadata["progress"],
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    if additional_info:
        event.update(additional_info)
    
    return event


def format_sse_message(data: Dict[str, Any]) -> str:
    """
    Format data as Server-Sent Events (SSE) message
    
    Args:
        data: Dictionary to send as SSE
    
    Returns:
        Formatted SSE string
    """
    return f"data: {json.dumps(data)}\n\n"


# ============================================================
# Logging Helper Functions
# ============================================================

def log_stage(
    stage: ProcessingStage,
    additional_info: Optional[Dict[str, Any]] = None,
    level: int = logging.INFO
):
    """
    Log a processing stage with structured information
    
    Args:
        stage: Current processing stage
        additional_info: Optional additional information
        level: Logging level (default: INFO)
    """
    metadata = STAGE_METADATA[stage]
    message = f"[{stage.value.upper()}] {metadata['description']}"
    
    if additional_info:
        info_str = " | ".join(f"{k}={v}" for k, v in additional_info.items())
        message = f"{message} | {info_str}"
    
    logger.log(level, message)


def log_error(stage: ProcessingStage, error: Exception, context: Optional[Dict[str, Any]] = None):
    """
    Log an error with context information
    
    Args:
        stage: Stage where error occurred
        error: The exception that was raised
        context: Optional context information
    """
    error_info = {
        "stage": stage.value,
        "error_type": type(error).__name__,
        "error_message": str(error),
    }
    
    if context:
        error_info.update(context)
    
    context_str = " | ".join(f"{k}={v}" for k, v in error_info.items())
    logger.error(f"[ERROR] {context_str}")


def log_image_info(stage: ProcessingStage, width: int, height: int, scale: int):
    """
    Log image dimension information
    
    Args:
        stage: Current processing stage
        width: Image width
        height: Image height
        scale: Upscaling factor
    """
    log_stage(
        stage,
        {
            "dimensions": f"{width}x{height}",
            "scale": f"{scale}x",
            "output_dimensions": f"{width*scale}x{height*scale}"
        }
    )


def log_performance(stage: ProcessingStage, duration_seconds: float):
    """
    Log performance metrics for a stage
    
    Args:
        stage: Completed processing stage
        duration_seconds: Time taken in seconds
    """
    log_stage(
        stage,
        {
            "duration": f"{duration_seconds:.2f}s",
            "status": "completed"
        }
    )
