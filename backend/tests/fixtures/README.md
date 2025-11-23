# Test Fixtures

This directory contains test images for ESRGAN integration testing.

## Directory Structure

```
fixtures/
├── input/          # Test input images (tracked in git)
│   └── test-image-1.png
└── output/         # Generated upscaled images (ignored by git)
    └── test-image-1-upscaled.png
```

## Usage

Place test images in `input/` and run:

```bash
cd backend
pytest tests/test_model.py::test_real_image_upscaling
```

The upscaled images will be saved to `output/` for visual inspection.

## Test Image Requirements

- **Format**: PNG, JPEG, or WebP
- **Naming**: `test-image-*.png` (or other supported extensions)
- **Size**: Any size (will be upscaled 4x)

## Integration Test

The `test_real_image_upscaling()` test:
- Loads images from `input/`
- Runs ESRGAN 4x upscaling on GPU (if available)
- Saves results to `output/`
- Verifies dimensions are exactly 4x original
- Reports input/output sizes and scale factor

## Example Output

```
[INPUT] test-image-1.png - 1844x870
[OUTPUT] test-image-1-upscaled.png - 7376x3480
[SCALE] 4.0x
```
