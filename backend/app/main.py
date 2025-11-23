# ============================================================
# ESRGAN Interface - FastAPI Backend (V2 with Enhanced Logging)
# ============================================================

import asyncio
import base64
import io
import logging
import time
import uuid
from typing import AsyncGenerator, Dict, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from PIL import Image
from py_real_esrgan.model import RealESRGAN

from app.logging_utils import (
    ProcessingStage,
    create_progress_event,
    format_sse_message,
    log_error,
    log_image_info,
    log_performance,
    log_stage,
)

# ============================================================
# Logging Configuration
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("esrgan")

# ============================================================
# FastAPI Application
# ============================================================

app = FastAPI(title="ESRGAN Interface API", version="2.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Model Configuration
# ============================================================

# Global model cache
models: Dict[int, RealESRGAN] = {}

# Supported scale configurations
SCALE_CONFIGS = {
    2: "weights/RealESRGAN_x2.pth",
    4: "weights/RealESRGAN_x4.pth"
}

# Device configuration (auto-detect)
try:
    import torch
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
except ImportError:
    device = None
    logger.warning("PyTorch not available, using CPU")

def get_or_create_model(scale: int) -> RealESRGAN:
    """Get cached model or create new one for specified scale"""
    if scale not in models:
        if scale not in SCALE_CONFIGS:
            raise ValueError(f"Unsupported scale: {scale}x. Supported: {list(SCALE_CONFIGS.keys())}")
        
        logger.info(f"Loading Real-ESRGAN model | scale={scale}x | device={device}")
        models[scale] = RealESRGAN(device, scale=scale)
        models[scale].load_weights(SCALE_CONFIGS[scale], download=True)
        logger.info(f"Model loaded successfully | scale={scale}x")
    
    return models[scale]

# ============================================================
# Progress Tracking
# ============================================================

active_jobs: Dict[str, Dict] = {}

async def progress_generator(job_id: str) -> AsyncGenerator[str, None]:
    """Generate Server-Sent Events for progress updates"""
    logger.info(f"[SSE] Started progress stream | job_id={job_id}")
    
    last_stage = None
    
    while True:
        if job_id not in active_jobs:
            logger.info(f"[SSE] Job not found, closing stream | job_id={job_id}")
            break
        
        job_data = active_jobs[job_id]
        current_stage = job_data["stage"]
        
        # Only send event if stage changed
        if current_stage != last_stage:
            event = create_progress_event(
                ProcessingStage(current_stage),
                {
                    "job_id": job_id,
                    "scale": job_data.get("scale"),
                    "input_dimensions": job_data.get("input_dimensions"),
                    "output_dimensions": job_data.get("output_dimensions"),
                }
            )
            logger.info(f"[SSE] Sending event | job_id={job_id} | stage={current_stage}")
            yield format_sse_message(event)
            last_stage = current_stage
        
        # Check if completed or errored
        if current_stage in [ProcessingStage.COMPLETED.value, ProcessingStage.ERROR.value]:
            if current_stage == ProcessingStage.ERROR.value:
                error_msg = job_data.get("error_message", "Unknown error")
                logger.error(f"[SSE] Error occurred | job_id={job_id} | error={error_msg}")
                yield format_sse_message({"error": error_msg})
            logger.info(f"[SSE] Job finished, closing stream | job_id={job_id}")
            break
        
        await asyncio.sleep(0.3)  # Poll every 300ms
    
    logger.info(f"[SSE] Stream closed | job_id={job_id}")

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
    Upscale image using Real-ESRGAN with detailed progress tracking
    """
    start_time = time.time()
    
    # Generate job ID if not provided
    if not job_id:
        job_id = str(uuid.uuid4())
    
    logger.info(f"[REQUEST] New upscale request | job_id={job_id} | scale={scale}x | filename={file.filename}")
    
    # Initialize job IMMEDIATELY (before any processing)
    active_jobs[job_id] = {
        "stage": ProcessingStage.INITIALIZING.value,
        "scale": scale
    }
    logger.info(f"[JOB] Created in active_jobs | job_id={job_id}")
    
    # Give SSE connection time to establish
    await asyncio.sleep(0.2)
    
    try:
        # Stage 1: Initialize
        log_stage(ProcessingStage.INITIALIZING, {"job_id": job_id, "scale": f"{scale}x"})
        logger.info(f"[STAGE 1/9] Initializing | job_id={job_id}")
        await asyncio.sleep(0.2)
        
        # Stage 2: Validate
        active_jobs[job_id]["stage"] = ProcessingStage.VALIDATING.value
        logger.info(f"[STAGE 2/9] Validating | job_id={job_id} | content_type={file.content_type}")
        
        if scale not in SCALE_CONFIGS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported scale: {scale}x. Supported: {list(SCALE_CONFIGS.keys())}"
            )
        
        if file.content_type not in {"image/png", "image/jpeg", "image/webp", "image/jpg"}:
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file.content_type}")
        
        log_stage(ProcessingStage.VALIDATING, {"job_id": job_id, "file_type": file.content_type})
        await asyncio.sleep(0.2)
        
        # Stage 3: Load image
        active_jobs[job_id]["stage"] = ProcessingStage.LOADING_IMAGE.value
        logger.info(f"[STAGE 3/9] Loading image | job_id={job_id}")
        
        contents = await file.read()
        logger.info(f"[LOAD] Read {len(contents)} bytes | job_id={job_id}")
        
        try:
            image = Image.open(io.BytesIO(contents)).convert("RGB")
            logger.info(f"[LOAD] Image decoded | job_id={job_id}")
        except Exception as exc:
            logger.error(f"[LOAD] Failed to decode image | job_id={job_id} | error={exc}")
            raise HTTPException(status_code=400, detail="Invalid image data") from exc
        
        width, height = image.size
        output_width = width * scale
        output_height = height * scale
        
        active_jobs[job_id]["input_dimensions"] = f"{width}x{height}"
        active_jobs[job_id]["output_dimensions"] = f"{output_width}x{output_height}"
        
        log_image_info(ProcessingStage.LOADING_IMAGE, width, height, scale)
        logger.info(f"[LOAD] Dimensions: {width}x{height} → {output_width}x{output_height} | job_id={job_id}")
        await asyncio.sleep(0.2)
        
        # Stage 4: Prepare model
        active_jobs[job_id]["stage"] = ProcessingStage.PREPARING_MODEL.value
        logger.info(f"[STAGE 4/9] Preparing model | job_id={job_id} | scale={scale}x")
        log_stage(ProcessingStage.PREPARING_MODEL, {"job_id": job_id, "scale": f"{scale}x", "status": "loading"})
        
        model = get_or_create_model(scale)
        
        log_stage(ProcessingStage.PREPARING_MODEL, {"job_id": job_id, "scale": f"{scale}x", "status": "ready"})
        logger.info(f"[MODEL] Ready | job_id={job_id}")
        await asyncio.sleep(0.2)
        
        # Stage 5: Preprocessing
        active_jobs[job_id]["stage"] = ProcessingStage.PREPROCESSING.value
        logger.info(f"[STAGE 5/9] Preprocessing | job_id={job_id}")
        log_stage(ProcessingStage.PREPROCESSING, {"job_id": job_id})
        await asyncio.sleep(0.2)
        
        # Stage 6: Upscaling (THE MAIN EVENT)
        active_jobs[job_id]["stage"] = ProcessingStage.UPSCALING.value
        logger.info(f"[STAGE 6/9] ⚡ Starting AI upscaling ⚡ | job_id={job_id} | scale={scale}x")
        log_stage(ProcessingStage.UPSCALING, {"job_id": job_id, "scale": f"{scale}x"})
        
        upscale_start = time.time()
        logger.info(f"[UPSCALE] Running model.predict() | job_id={job_id}")
        
        sr_image = model.predict(image)
        
        upscale_duration = time.time() - upscale_start
        logger.info(f"[UPSCALE] ✓ Complete | duration={upscale_duration:.2f}s | job_id={job_id}")
        log_performance(ProcessingStage.UPSCALING, upscale_duration)
        await asyncio.sleep(0.2)
        
        # Stage 7: Postprocessing
        active_jobs[job_id]["stage"] = ProcessingStage.POSTPROCESSING.value
        logger.info(f"[STAGE 7/9] Postprocessing | job_id={job_id}")
        log_stage(ProcessingStage.POSTPROCESSING, {"job_id": job_id})
        await asyncio.sleep(0.2)
        
        # Stage 8: Encoding
        active_jobs[job_id]["stage"] = ProcessingStage.ENCODING.value
        logger.info(f"[STAGE 8/9] Encoding to PNG | job_id={job_id}")
        log_stage(ProcessingStage.ENCODING, {"job_id": job_id})
        
        encode_start = time.time()
        buffer = io.BytesIO()
        sr_image.save(buffer, format="PNG")
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        encode_duration = time.time() - encode_start
        
        logger.info(f"[ENCODE] Complete | duration={encode_duration:.2f}s | size={len(image_base64)} chars | job_id={job_id}")
        await asyncio.sleep(0.2)
        
        # Stage 9: Complete
        active_jobs[job_id]["stage"] = ProcessingStage.COMPLETED.value
        total_duration = time.time() - start_time
        active_jobs[job_id]["processing_time"] = f"{total_duration:.2f}s"
        
        logger.info(f"[STAGE 9/9] ✓✓✓ COMPLETED ✓✓✓ | total={total_duration:.2f}s | job_id={job_id}")
        log_performance(ProcessingStage.COMPLETED, total_duration)
        
        # Keep job alive for a bit so SSE can send completion event
        await asyncio.sleep(0.5)
        
        output_width_final, output_height_final = sr_image.size
        
        return JSONResponse({
            "success": True,
            "processedImage": f"data:image/png;base64,{image_base64}",
            "message": "Image successfully upscaled",
            "job_id": job_id,
            "metadata": {
                "input_dimensions": f"{width}x{height}",
                "output_dimensions": f"{output_width_final}x{output_height_final}",
                "scale": scale,
                "processing_time": f"{total_duration:.2f}s",
                "upscaling_time": f"{upscale_duration:.2f}s",
                "encoding_time": f"{encode_duration:.2f}s"
            }
        })
        
    except HTTPException:
        raise
    except Exception as exc:
        active_jobs[job_id]["stage"] = ProcessingStage.ERROR.value
        active_jobs[job_id]["error_message"] = str(exc)
        logger.error(f"[ERROR] Processing failed | job_id={job_id} | error={exc}", exc_info=True)
        log_error(ProcessingStage.ERROR, exc, {"job_id": job_id})
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(exc)}") from exc


@app.get("/progress/{job_id}")
async def get_progress(job_id: str):
    """
    Stream progress updates via Server-Sent Events
    Waits for job creation to handle race conditions
    """
    logger.info(f"[PROGRESS] Client connected | job_id={job_id}")
    
    # Wait up to 5 seconds for job to be created
    max_wait = 5
    wait_interval = 0.1
    waited = 0
    
    while job_id not in active_jobs and waited < max_wait:
        await asyncio.sleep(wait_interval)
        waited += wait_interval
    
    if job_id not in active_jobs:
        logger.warning(f"[PROGRESS] Job not found after {max_wait}s | job_id={job_id}")
        
        async def error_generator():
            yield format_sse_message({
                "stage": "error",
                "error": f"Job {job_id} not found"
            })
        
        return StreamingResponse(
            error_generator(),
            media_type="text/event-stream"
        )
    
    logger.info(f"[PROGRESS] Job found, starting stream | job_id={job_id}")
    return StreamingResponse(
        progress_generator(job_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.get("/scales")
async def get_scales():
    """Get available scaling factors"""
    return JSONResponse({
        "scales": list(SCALE_CONFIGS.keys()),
        "default": 4,
        "loaded": list(models.keys())
    })


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "modelLoaded": len(models) > 0,
        "device": str(device),
        "loaded_scales": list(models.keys()),
        "supported_scales": list(SCALE_CONFIGS.keys())
    })


@app.get("/")
async def root():
    """Root endpoint"""
    return JSONResponse({
        "service": "ESRGAN Interface API",
        "version": "2.0.0",
        "endpoints": {
            "upscale": "/upscale",
            "progress": "/progress/{job_id}",
            "scales": "/scales",
            "health": "/health"
        }
    })
