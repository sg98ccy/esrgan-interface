from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from py_real_esrgan.model import RealESRGAN
from PIL import Image
import torch
import io
import base64
import asyncio
from typing import Optional, AsyncGenerator, Dict
import time
import uuid

from .logging_utils import (
    ProcessingStage,
    create_progress_event,
    format_sse_message,
    log_stage,
    log_error,
    log_image_info,
    log_performance
)

app = FastAPI()

# Allow local Next.js front end in development
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Model Management
# ============================================================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Model cache: scale -> model instance
models: Dict[int, RealESRGAN] = {}

# Supported scales and their model weights
SCALE_CONFIGS = {
    2: "weights/RealESRGAN_x2.pth",
    4: "weights/RealESRGAN_x4.pth",
}

# Initialize default 4x model at startup
models[4] = RealESRGAN(device, scale=4)
models[4].load_weights(SCALE_CONFIGS[4], download=True)
log_stage(ProcessingStage.INITIALIZING, {"default_scale": "4x", "device": str(device)})


def get_or_create_model(scale: int) -> RealESRGAN:
    """Get cached model or create new one for specified scale"""
    if scale not in models:
        if scale not in SCALE_CONFIGS:
            raise ValueError(f"Unsupported scale: {scale}x. Supported: {list(SCALE_CONFIGS.keys())}")
        
        log_stage(ProcessingStage.PREPARING_MODEL, {"scale": f"{scale}x", "status": "loading"})
        models[scale] = RealESRGAN(device, scale=scale)
        models[scale].load_weights(SCALE_CONFIGS[scale], download=True)
        log_stage(ProcessingStage.PREPARING_MODEL, {"scale": f"{scale}x", "status": "ready"})
    
    return models[scale]


# ============================================================
# Progress Tracking (In-Memory Store)
# ============================================================

# Store progress for active jobs: job_id -> progress_data
active_jobs: Dict[str, Dict] = {}


async def progress_generator(job_id: str) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events for progress updates"""
    log_stage(ProcessingStage.INITIALIZING, {"job_id": job_id, "type": "SSE stream started"})
    
    while True:
        if job_id not in active_jobs:
            # Job not found or completed
            break
        
        job_data = active_jobs[job_id]
        
        # Send current progress
        event = create_progress_event(
            ProcessingStage(job_data["stage"]),
            {
                "job_id": job_id,
                "scale": job_data.get("scale"),
                "dimensions": job_data.get("dimensions"),
            }
        )
        yield format_sse_message(event)
        
        # Check if completed or errored
        if job_data["stage"] in [ProcessingStage.COMPLETED.value, ProcessingStage.ERROR.value]:
            if job_data["stage"] == ProcessingStage.ERROR.value:
                yield format_sse_message({"error": job_data.get("error_message", "Unknown error")})
            break
        
        await asyncio.sleep(0.5)  # Poll every 500ms
    
    # Cleanup
    if job_id in active_jobs:
        del active_jobs[job_id]
    
    log_stage(ProcessingStage.COMPLETED, {"job_id": job_id, "type": "SSE stream closed"})


# ============================================================
# API Endpoints
# ============================================================

@app.post("/upscale")
async def upscale_image(
    file: UploadFile = File(...),
    scale: Optional[int] = Form(4),
    job_id: Optional[str] = Form(None)
):
    """
    Upscale image using Real-ESRGAN
    
    Parameters:
    - file: Image file (PNG, JPEG, WebP)
    - scale: Upscaling factor (2 or 4, default: 4)
    - job_id: Optional job ID for progress tracking
    """
    start_time = time.time()
    
    # Generate job ID if not provided
    if not job_id:
        job_id = str(uuid.uuid4())
    
    # Initialize job tracking
    active_jobs[job_id] = {"stage": ProcessingStage.INITIALIZING.value, "scale": scale}
    log_stage(ProcessingStage.INITIALIZING, {"job_id": job_id, "scale": f"{scale}x"})
    
    try:
        # Validate scale
        active_jobs[job_id]["stage"] = ProcessingStage.VALIDATING.value
        if scale not in SCALE_CONFIGS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported scale: {scale}x. Supported scales: {list(SCALE_CONFIGS.keys())}"
            )
        
        # Validate file type
        if file.content_type not in {"image/png", "image/jpeg", "image/webp"}:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        log_stage(ProcessingStage.VALIDATING, {"job_id": job_id, "file_type": file.content_type})
        
        # Load image
        active_jobs[job_id]["stage"] = ProcessingStage.LOADING_IMAGE.value
        contents = await file.read()
        
        try:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid image data") from exc
        
        width, height = image.size
        active_jobs[job_id]["dimensions"] = f"{width}x{height}"
        log_image_info(ProcessingStage.LOADING_IMAGE, width, height, scale)
        
        # Get or load model
        active_jobs[job_id]["stage"] = ProcessingStage.PREPARING_MODEL.value
        model = get_or_create_model(scale)
        
        # Preprocessing
        active_jobs[job_id]["stage"] = ProcessingStage.PREPROCESSING.value
        log_stage(ProcessingStage.PREPROCESSING, {"job_id": job_id})
        preprocess_time = time.time()
        
        # Run upscaling
        active_jobs[job_id]["stage"] = ProcessingStage.UPSCALING.value
        log_stage(ProcessingStage.UPSCALING, {"job_id": job_id, "scale": f"{scale}x"})
        upscale_start = time.time()
        
        sr_image = model.predict(image)
        
        upscale_duration = time.time() - upscale_start
        log_performance(ProcessingStage.UPSCALING, upscale_duration)
        
        # Postprocessing
        active_jobs[job_id]["stage"] = ProcessingStage.POSTPROCESSING.value
        log_stage(ProcessingStage.POSTPROCESSING, {"job_id": job_id})
        
        # Encoding
        active_jobs[job_id]["stage"] = ProcessingStage.ENCODING.value
        log_stage(ProcessingStage.ENCODING, {"job_id": job_id})
        
        buffer = io.BytesIO()
        sr_image.save(buffer, format="PNG")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        # Mark as completed
        active_jobs[job_id]["stage"] = ProcessingStage.COMPLETED.value
        total_duration = time.time() - start_time
        log_performance(ProcessingStage.COMPLETED, total_duration)
        
        output_width, output_height = sr_image.size
        
        return JSONResponse({
            "success": True,
            "processedImage": f"data:image/png;base64,{image_base64}",
            "message": "Image successfully upscaled",
            "job_id": job_id,
            "metadata": {
                "input_dimensions": f"{width}x{height}",
                "output_dimensions": f"{output_width}x{output_height}",
                "scale": scale,
                "processing_time": f"{total_duration:.2f}s",
                "upscaling_time": f"{upscale_duration:.2f}s"
            }
        })
        
    except HTTPException:
        raise
    except Exception as exc:
        active_jobs[job_id]["stage"] = ProcessingStage.ERROR.value
        active_jobs[job_id]["error_message"] = str(exc)
        log_error(ProcessingStage.ERROR, exc, {"job_id": job_id})
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(exc)}") from exc


@app.get("/progress/{job_id}")
async def get_progress(job_id: str):
    """
    Stream progress updates for a specific job using Server-Sent Events
    Wait for job to be created if not immediately available (handles race condition)
    """
    # Wait up to 5 seconds for job to be created
    max_wait = 5
    wait_interval = 0.1
    waited = 0
    
    while job_id not in active_jobs and waited < max_wait:
        await asyncio.sleep(wait_interval)
        waited += wait_interval
    
    if job_id not in active_jobs:
        # Send error event and close
        async def error_generator():
            yield format_sse_message({
                "error": "Job not found or expired",
                "stage": "error"
            })
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    return StreamingResponse(
        progress_generator(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "modelLoaded": True,
        "device": str(device),
        "loaded_scales": list(models.keys()),
        "supported_scales": list(SCALE_CONFIGS.keys()),
        "message": "ESRGAN backend is ready"
    })


@app.get("/scales")
async def get_available_scales():
    """Get available upscaling factors"""
    return JSONResponse({
        "scales": list(SCALE_CONFIGS.keys()),
        "default": 4,
        "loaded": list(models.keys())
    })
