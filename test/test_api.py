# test/test_api.py
import time
import requests
import threading
import uvicorn
from app.main import app


def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")


def wait_for_health(timeout=10):
    """Poll /health until API is ready or timeout"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get("http://127.0.0.1:8000/health")
            if r.status_code == 200 and r.json().get("status") == "ok":
                return True
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.5)
    return False


def test_health_and_predict():
    # Start API in background
    t = threading.Thread(target=run_server, daemon=True)
    t.start()

    # Wait until /health is up
    assert wait_for_health(), "API did not become healthy in time"

    # Test /health
    r = requests.get("http://127.0.0.1:8000/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # Test /predict
    payload = {"features": {}}  # empty features -> defaults to zeros
    r2 = requests.post("http://127.0.0.1:8000/predict", json=payload)
    assert r2.status_code == 200, f"Predict failed: {r2.text}"
    data = r2.json()
    assert "prediction" in data
    assert "latency_sec" in data
    assert data["latency_sec"] >= 0
    assert isinstance(float(data["prediction"]), float)
    assert data["prediction"] >= 0 