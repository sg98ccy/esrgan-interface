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
    Sending a valid PNG should return an upscaled PNG image.
    """
    img_bytes = _create_dummy_png()

    files = {"file": ("test.png", img_bytes, "image/png")}
    response = client.post("/api/upscale", files=files)

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"

    out_bytes = response.content
    out_img = Image.open(BytesIO(out_bytes))

    # Should be at least larger than input in each dimension
    assert out_img.size[0] >= 16 * 2
    assert out_img.size[1] >= 16 * 2


def test_upscale_endpoint_rejects_non_image():
    """
    Non image payloads should be rejected with a 400 error.
    """
    files = {"file": ("test.txt", b"not an image", "text/plain")}
    response = client.post("/api/upscale", files=files)

    assert response.status_code == 400
