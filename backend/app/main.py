from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from py_real_esrgan.model import RealESRGAN
from PIL import Image
import torch
import io
import base64

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

# Initialise model once at startup
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = RealESRGAN(device, scale=4)
# This will download weights to a local cache if not present
model.load_weights("weights/RealESRGAN_x4.pth", download=True)


@app.post("/upscale")
async def upscale_image(file: UploadFile = File(...)):
    if file.content_type not in {"image/png", "image/jpeg", "image/webp"}:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    contents = await file.read()
    try:
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image data")

    # Run super resolution
    sr_image = model.predict(image)

    # Convert to base64 for JSON response
    buffer = io.BytesIO()
    sr_image.save(buffer, format="PNG")
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return JSONResponse({
        "success": True,
        "processedImage": f"data:image/png;base64,{image_base64}",
        "message": "Image successfully upscaled"
    })


@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "healthy",
        "modelLoaded": True,
        "device": str(device),
        "message": "ESRGAN backend is ready"
    })
