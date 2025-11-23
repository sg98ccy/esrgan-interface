# backend/tests/test_env.py
# ============================
# Environment and device tests
# ============================

import sys
import torch
import pytest


def test_python_version_is_reasonable():
    """
    Sanity check that we are not on an unsupported future Python.
    Adjust these bounds if needed later.
    """
    major, minor = sys.version_info[:2]
    assert major == 3
    assert 8 <= minor <= 13


def test_torch_import_and_version():
    """
    Torch must import and expose a non empty version string.
    """
    assert hasattr(torch, "__version__")
    assert isinstance(torch.__version__, str)
    assert len(torch.__version__) > 0


def test_cpu_tensor_ops():
    """
    Basic CPU tensor operations should work without error.
    """
    device = torch.device("cpu")
    x = torch.randn(3, 3, device=device)
    y = torch.randn(3, 3, device=device)
    z = x @ y
    assert z.shape == (3, 3)


@pytest.mark.skipif(not torch.cuda.is_available(), reason="CUDA not available")
def test_cuda_tensor_ops_if_available():
    """
    If CUDA is available, verify that we can allocate and multiply
    tensors on the GPU. Skipped on CPU only machines.
    """
    device = torch.device("cuda")
    x = torch.randn(3, 3, device=device)
    y = torch.randn(3, 3, device=device)
    z = x @ y
    assert z.device.type == "cuda"
    assert z.shape == (3, 3)


def test_gpu_detection_and_utilisation():
    """
    Detect GPU availability and verify actual GPU utilisation if present.
    Reports device information for debugging.
    """
    if torch.cuda.is_available():
        device = torch.device("cuda")
        device_name = torch.cuda.get_device_name(0)
        device_count = torch.cuda.device_count()
        
        print(f"\n[GPU DETECTED] {device_name}")
        print(f"[GPU COUNT] {device_count}")
        
        # Verify actual GPU memory allocation
        x = torch.randn(1000, 1000, device=device)
        memory_allocated = torch.cuda.memory_allocated(0) / 1024**2  # MB
        
        print(f"[GPU MEMORY ALLOCATED] {memory_allocated:.2f} MB")
        
        assert x.device.type == "cuda"
        assert memory_allocated > 0
        
        # Clean up
        del x
        torch.cuda.empty_cache()
    else:
        print("\n[GPU] Not available - running on CPU")
        device = torch.device("cpu")
        x = torch.randn(1000, 1000, device=device)
        assert x.device.type == "cpu"
