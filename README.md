# ESRGAN Interface

ESRGAN Interface provides a user-friendly web UI (Next.js) that proxies requests to a Python FastAPI backend which runs Real-ESRGAN image upscaling. The goal is to let non-technical users upload an image, watch progress via Server-Sent Events (SSE) and download a high-resolution upscaled image (base64 / data URL response).

This README documents how the repository is laid out, how to set up and run the backend and frontend on Windows, the API surface, testing and troubleshooting notes.

Quick summary:
- **Frontend:** `frontend/` — Next.js 16, React 19 UI that proxies to the backend via `api/esrgan`.
- **Backend:** `backend/` — FastAPI service that loads Real-ESRGAN model weights and exposes `/upscale`, `/progress/{job_id}`, `/scales`, and `/health`.
- **Weights:** `weights/` — model checkpoint files (for example `RealESRGAN_x2.pth`, `RealESRGAN_x4.pth`).

Compatibility: The backend expects Python 3.10+; the frontend uses Node.js / npm for Next.js. This README shows Windows `cmd.exe` commands.

## Table of Contents
- [1. Overview](#1-overview)
- [2. Repository structure](#2-repository-structure)
- [3. Prerequisites (Windows)](#3-prerequisites-windows)
- [4. Backend — install & run](#4-backend---install--run)
  - [4.1 Create & activate virtualenv](#41-create--activate-virtualenv)
  - [4.2 Install dependencies](#42-install-dependencies)
  - [4.3 Start server](#43-start-server)
- [5. Frontend — install & run](#5-frontend---install--run)
  - [5.1 Install packages](#51-install-packages)
  - [5.2 Run dev server](#52-run-dev-server)
- [6. API reference (backend)](#6-api-reference-backend)
  - [6.1 POST /upscale](#61-post-upscale)
  - [6.2 GET /progress/{job_id}](#62-get-progress)
  - [6.3 GET /scales](#63-get-scales)
  - [6.4 GET /health](#64-get-health)
- [7. Frontend integration notes](#7-frontend-integration-notes)
- [8. Weights and model files](#8-weights-and-model-files)
- [9. Testing](#9-testing)
  - [9.1 Run backend tests](#91-run-backend-tests)
- [10. Troubleshooting & tips](#10-troubleshooting--tips)
- [11. Contributing](#11-contributing)
- [12. License](#12-license)
- [13. Credits](#13-credits)

<a name="1-overview"></a>
## 1. Overview

This project wraps Real-ESRGAN into a backend API and provides a small Next.js frontend to make it easy to upload and upscale images. The backend implements detailed progress tracking using an in-memory job registry and Server-Sent Events so the UI can show the user what is happening (initialising, validating, loading image, preparing model, upscaling, encoding, etc.).

<a name="2-repository-structure"></a>
## 2. Repository structure

- `backend/` — FastAPI server and tests
  - `app/main.py` — main FastAPI app and endpoints (`/upscale`, `/progress/{job_id}`, `/scales`, `/health`)
  - `requirements.txt` — Python dependencies
  - `weights/` — expected model files (the repo also contains a top-level `weights/` folder)
  - `tests/` — pytest tests for backend
- `frontend/` — Next.js (React + TypeScript) UI
  - `app/` — Next.js app routes and API proxy handler (`app/api/esrgan/route.ts` proxy)
  - `lib/api.ts` — client used by UI: `upscaleImage()`, `connectToProgressStream()`, `getScales()`, `checkHealth()`
- `weights/` — model checkpoints used by backend (e.g. `RealESRGAN_x4.pth`)
- `README.md` — this file (updated)

<a name="3-prerequisites-windows"></a>
## 3. Prerequisites (Windows)

- Install Python (3.10+) and ensure `python` and `pip` are on PATH.
- Install Node.js + npm (recommended LTS).
- (Optional, GPU) Install a PyTorch build that supports your GPU.

<a name="4-backend---install--run"></a>
## 4. Backend — install & run

4.1 Prerequisite step: open a `cmd.exe` terminal and change to the repo root.

### 4.1 Create & activate virtualenv (recommended)

```cmd
python -m venv .venv
.\.venv\Scripts\activate
```

### 4.2 Install dependencies

```cmd
pip install -r backend\requirements.txt
```

### 4.3 Start server (development)

```cmd
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Notes:
- The backend auto-detects the device using PyTorch; if CUDA is available and PyTorch supports it, it will use `cuda`, otherwise it will use CPU.
- The code caches loaded Real-ESRGAN models per scale. Supported scales are 2x and 4x by default and are configured in `app/main.py` via the `SCALE_CONFIGS` mapping.

<a name="5-frontend---install--run"></a>
## 5. Frontend — install & run

### 5.1 Install packages

```cmd
cd frontend
npm install
```

### 5.2 Run dev server

```cmd
npm run dev
```

### 5.3 Open UI

Open the UI in a browser at `http://localhost:3000`.

Notes:
- The frontend proxies API calls through `GET/POST /api/esrgan` (see `frontend/app/api/esrgan/route.ts`). The UI client (`frontend/lib/api.ts`) also uses `BACKEND_URL` to connect directly to the backend for SSE progress streams. You can set `window.BACKEND_URL` at runtime or update the proxy to point to your backend host.

<a name="6-api-reference-backend"></a>
## 6. API reference (backend)

### 6.1 POST /upscale — Upscale an image

- Request: `multipart/form-data` with fields:
  - `file` — image file (`image/png`, `image/jpeg`, `image/webp`)
  - `scale` — integer scale factor (2 or 4). Default is 4 if omitted.
  - `job_id` — (optional) a client-generated job id to correlate SSE and response.
- Response: JSON with keys: `success`, `processedImage` (data URL, PNG base64), `message`, `job_id`, and `metadata` (dimensions, timings).

### 6.2 GET /progress/{job_id} — Server-Sent Events progress stream

- Use EventSource in the browser to receive incremental JSON messages describing processing stage changes (the frontend implements `connectToProgressStream()` in `frontend/lib/api.ts`).

### 6.3 GET /scales — returns supported scaling factors and loaded models

### 6.4 GET /health — health and device info

Example: upload via `curl` directly to the backend (for quick tests):

```cmd
curl -v -X POST "http://localhost:8000/upscale" -F "file=@path\to\image.png" -F "scale=4"
```

Example response snippet (successful):

```json
{
  "success": true,
  "processedImage": "data:image/png;base64,...",
  "job_id": "...",
  "metadata": { "input_dimensions": "W x H", "output_dimensions": "W' x H'", "processing_time": "X.XXs" }
}
```

<a name="7-frontend-integration-notes"></a>
## 7. Frontend integration notes

- The Next.js API route `frontend/app/api/esrgan/route.ts` acts as a proxy. The UI client calls `POST /api/esrgan?endpoint=upscale` and the proxy forwards this to the backend. This avoids CORS and serverless timeout issues for uploads while the frontend connects directly to the backend SSE endpoint for progress.
- In development, ensure the backend is running at `http://localhost:8000` (the frontend `lib/api.ts` defaults to that URL). You can override the backend URL at runtime through `window.BACKEND_URL` or by modifying the proxy route.

<a name="8-weights-and-model-files"></a>
## 8. Weights and model files

- Put Real-ESRGAN weight files in `weights/` (top-level) or `backend/weights/` depending on your setup. `app/main.py` expects `weights/RealESRGAN_x2.pth` and `weights/RealESRGAN_x4.pth` by default (see `SCALE_CONFIGS` in `backend/app/main.py`).
- The code uses `RealESRGAN(...).load_weights(path, download=True)` so if the weight is not present the library may attempt to download it.

<a name="9-testing"></a>
## 9. Testing

Backend tests use `pytest`.

### 9.1 Run backend tests

To run backend tests (from repo root):

```cmd
cd backend
pytest -v
```

Note: tests will require the Python dependencies in `backend/requirements.txt`.

<a name="10-troubleshooting--tips"></a>
## 10. Troubleshooting & tips

- If you see CUDA/torch errors, confirm your PyTorch installation matches your CUDA runtime. If CUDA isn't available the backend will fall back to CPU.
- If model loading fails, check that the expected `weights/*.pth` files are present or allow the library to download them.
- Large images may be slow to process on CPU. For faster results install a GPU-capable PyTorch build.
- If the frontend fails to receive SSE messages, confirm the `BACKEND_URL` that the browser knows about points to a running backend and that the backend is reachable from the browser.

<a name="11-contributing"></a>
## 11. Contributing

- Feel free to open issues or PRs. For code changes, run unit tests in `backend/tests/` and ensure the frontend builds (`npm run build` in `frontend/`).

<a name="12-license"></a>
## 12. License

- See `LICENSE` at the repository root.

<a name="13-credits"></a>
## 13. Credits

- This project uses and builds on the Real-ESRGAN work. See the original repository: https://github.com/xinntao/Real-ESRGAN

BibTeX (please cite when appropriate):

```bibtex
@InProceedings{wang2021realesrgan,
    author    = {Xintao Wang and Liangbin Xie and Chao Dong and Ying Shan},
    title     = {Real-ESRGAN: Training Real-World Blind Super-Resolution with Pure Synthetic Data},
    booktitle = {International Conference on Computer Vision Workshops (ICCVW)},
    date      = {2021}
}
```
