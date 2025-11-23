# ============================================================
# Tests for Progress Tracking and SSE Endpoints
# Simplified version with comprehensive logging
# ============================================================

import pytest
import json
from fastapi.testclient import TestClient
from PIL import Image
import io

from app.main import app, active_jobs
from app.logging_utils import ProcessingStage


# ============================================================
# Test Client Setup
# ============================================================

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_image():
    """Create a small test image"""
    img = Image.new("RGB", (32, 32), color="red")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


@pytest.fixture(autouse=True)
def cleanup_jobs():
    """Clean up active_jobs after each test"""
    yield
    active_jobs.clear()


# ============================================================
# Simple Progress Tests
# ============================================================

def test_progress_basic(client):
    """Test basic progress endpoint with existing job"""
    print("\n[TEST] test_progress_basic")
    job_id = "test-job-1"
    
    active_jobs[job_id] = {
        "stage": ProcessingStage.COMPLETED.value,
        "scale": 4
    }
    print(f"[TEST] Created job: {job_id}")
    
    with client.stream("GET", f"/progress/{job_id}") as response:
        print(f"[TEST] Response status: {response.status_code}")
        assert response.status_code == 200
        
        event_count = 0
        for line in response.iter_lines():
            if line.startswith("data:"):
                event_count += 1
                data = json.loads(line[6:])
                print(f"[TEST] Event: {data}")
                assert data["stage"] == ProcessingStage.COMPLETED.value
                break
        
        print(f"[TEST] Received {event_count} events")
        assert event_count >= 1


def test_progress_nonexistent_job(client):
    """Test progress endpoint with job that doesn't exist"""
    print("\n[TEST] test_progress_nonexistent_job")
    job_id = "fake-job"
    
    with client.stream("GET", f"/progress/{job_id}", timeout=6) as response:
        print(f"[TEST] Response status: {response.status_code}")
        assert response.status_code == 200
        
        for line in response.iter_lines():
            if line.startswith("data:"):
                data = json.loads(line[6:])
                print(f"[TEST] Event: {data}")
                if "error" in data:
                    print("[TEST] Error event received")
                    assert data["stage"] == "error"
                    break


# ============================================================
# Integration Tests
# ============================================================

def test_upscale_endpoint(client, sample_image):
    """Test upscale endpoint returns success"""
    print("\n[TEST] test_upscale_endpoint")
    
    files = {"file": ("test.png", sample_image, "image/png")}
    data = {"scale": "4"}
    
    print("[TEST] Submitting upscale request")
    response = client.post("/upscale", files=files, data=data)
    
    print(f"[TEST] Response status: {response.status_code}")
    assert response.status_code == 200
    
    result = response.json()
    print(f"[TEST] Success: {result.get('success')}")
    assert result["success"] is True
    assert "metadata" in result
    print(f"[TEST] Metadata: {result['metadata']}")


def test_upscale_with_2x_scale(client, sample_image):
    """Test 2x upscaling"""
    print("\n[TEST] test_upscale_with_2x_scale")
    
    sample_image.seek(0)
    files = {"file": ("test_2x.png", sample_image, "image/png")}
    data = {"scale": "2"}
    
    print("[TEST] Submitting 2x upscale request")
    response = client.post("/upscale", files=files, data=data)
    
    print(f"[TEST] Response status: {response.status_code}")
    assert response.status_code == 200
    
    result = response.json()
    print(f"[TEST] Scale: {result['metadata']['scale']}")
    assert result["metadata"]["scale"] == 2


def test_upscale_with_4x_scale(client, sample_image):
    """Test 4x upscaling"""
    print("\n[TEST] test_upscale_with_4x_scale")
    
    sample_image.seek(0)
    files = {"file": ("test_4x.png", sample_image, "image/png")}
    data = {"scale": "4"}
    
    print("[TEST] Submitting 4x upscale request")
    response = client.post("/upscale", files=files, data=data)
    
    print(f"[TEST] Response status: {response.status_code}")
    assert response.status_code == 200
    
    result = response.json()
    print(f"[TEST] Scale: {result['metadata']['scale']}")
    assert result["metadata"]["scale"] == 4


# ============================================================
# Endpoint Tests
# ============================================================

def test_scales_endpoint(client):
    """Test /scales endpoint"""
    print("\n[TEST] test_scales_endpoint")
    
    response = client.get("/scales")
    print(f"[TEST] Response status: {response.status_code}")
    assert response.status_code == 200
    
    data = response.json()
    print(f"[TEST] Available scales: {data['scales']}")
    assert 2 in data["scales"]
    assert 4 in data["scales"]


def test_health_endpoint(client):
    """Test /health endpoint"""
    print("\n[TEST] test_health_endpoint")
    
    response = client.get("/health")
    print(f"[TEST] Response status: {response.status_code}")
    assert response.status_code == 200
    
    data = response.json()
    print(f"[TEST] Health status: {data['status']}")
    print(f"[TEST] Device: {data['device']}")
    assert data["status"] == "healthy"
