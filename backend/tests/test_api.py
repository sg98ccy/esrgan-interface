# backend/tests/test_api.py
# ============================
# FastAPI endpoint tests
# ============================

from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image

from app.main import app


client = TestClient(app)


def _create_dummy_png(width: int = 16, height: int = 16) -> bytes:
    img = Image.new("RGB", (width, height), color=(10, 20, 30))
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def test_upscale_endpoint_returns_png():
    """
    Sending a valid PNG should return a JSON response with base64 image.
    """
    img_bytes = _create_dummy_png()

    files = {"file": ("test.png", img_bytes, "image/png")}
    data = {"scale": "4"}
    response = client.post("/upscale", files=files, data=data)

    assert response.status_code == 200
    result = response.json()
    
    assert result["success"] is True
    assert "processedImage" in result
    assert result["processedImage"].startswith("data:image/png;base64,")
    assert "metadata" in result
    assert result["metadata"]["scale"] == 4


def test_upscale_endpoint_rejects_non_image():
    """
    Non image payloads should be rejected with a 400 error.
    """
    files = {"file": ("test.txt", b"not an image", "text/plain")}
    response = client.post("/upscale", files=files)

    assert response.status_code == 400
    result = response.json()
    assert "Unsupported file type" in result["detail"]
