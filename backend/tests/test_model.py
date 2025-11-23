# backend/tests/test_model.py
# ============================
# RealESRGAN model smoke tests
# ============================

from pathlib import Path

import pytest
import torch
from PIL import Image
from py_real_esrgan.model import RealESRGAN


@pytest.fixture(scope="session")
def esrgan_model() -> RealESRGAN:
    """
    Session scoped fixture that loads the RealESRGAN model once.

    This keeps tests fast by avoiding repeated weight loading.
    Uses GPU if available for actual performance testing.
    """
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    scale = 4

    # Report device being used
    if device.type == "cuda":
        print(f"\n[ESRGAN] Using GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("\n[ESRGAN] Using CPU")

    model = RealESRGAN(device, scale=scale)
    model.load_weights("weights/RealESRGAN_x4.pth", download=True)
    model.model.eval()

    return model


def test_model_upscales_size(esrgan_model: RealESRGAN):
    """
    Basic functional test.
    A small 32x32 image should be upscaled to 128x128 for scale 4.
    Verifies GPU is actually being used if available.
    """
    w, h = 32, 32
    img = Image.new("RGB", (w, h), color=(50, 100, 150))

    # Verify model is on correct device
    model_device = next(esrgan_model.model.parameters()).device
    print(f"\n[MODEL DEVICE] {model_device}")

    with torch.no_grad():
        out = esrgan_model.predict(img)

    assert out.size == (w * 4, h * 4)
    
    # Confirm GPU was used if available
    if torch.cuda.is_available():
        assert model_device.type == "cuda", "GPU available but model not using it"


@pytest.mark.slow
def test_model_inference_runs_and_saves_output(esrgan_model: RealESRGAN, tmp_path: Path):
    """
    Heavier smoke test that times a small inference and writes the
    result to a temporary directory for visual inspection when needed.
    Marked as slow so it can be excluded from quick runs.
    """
    w, h = 64, 64
    img = Image.new("RGB", (w, h), color=(120, 160, 200))

    with torch.no_grad():
        out = esrgan_model.predict(img)

    assert out.size == (w * 4, h * 4)

    output_path = tmp_path / "sr_test.png"
    out.save(output_path)

    assert output_path.exists()
    assert output_path.stat().st_size > 0


@pytest.mark.slow
def test_real_image_upscaling(esrgan_model: RealESRGAN):
    """
    Integration test using actual test image from fixtures/input/.
    Upscales test-image-1.png and saves result to fixtures/output/.
    Verifies real-world ESRGAN performance with actual images.
    """
    # Path to test fixtures
    fixtures_dir = Path(__file__).parent / "fixtures"
    input_dir = fixtures_dir / "input"
    output_dir = fixtures_dir / "output"
    
    input_path = input_dir / "test-image-1.png"
    output_path = output_dir / "test-image-1-upscaled.png"
    
    # Skip if test image not present
    if not input_path.exists():
        pytest.skip(f"Test image not found: {input_path}")
    
    # Load input image
    img = Image.open(input_path).convert("RGB")
    original_size = img.size
    print(f"\n[INPUT] {input_path.name} - {original_size[0]}x{original_size[1]}")
    
    # Perform upscaling
    with torch.no_grad():
        upscaled = esrgan_model.predict(img)
    
    # Save output
    output_dir.mkdir(parents=True, exist_ok=True)
    upscaled.save(output_path)
    
    upscaled_size = upscaled.size
    print(f"[OUTPUT] {output_path.name} - {upscaled_size[0]}x{upscaled_size[1]}")
    print(f"[SCALE] {upscaled_size[0]/original_size[0]:.1f}x")
    
    # Verify upscaling worked
    assert upscaled_size[0] == original_size[0] * 4
    assert upscaled_size[1] == original_size[1] * 4
    assert output_path.exists()
    assert output_path.stat().st_size > 0
