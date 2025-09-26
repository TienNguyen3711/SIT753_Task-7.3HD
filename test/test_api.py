import multiprocessing
import time
import requests
import json
import subprocess
import os
import threading
import uvicorn
from app.main import app

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")

def test_health_and_predict():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(1)

    r = requests.get("http://127.0.0.1:8000/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"

    payload = {"features": {}}  # tối thiểu: cho phép trống → fill 0
    r2 = requests.post("http://127.0.0.1:8000/predict", json=payload)
    assert r2.status_code == 200
    assert "prediction" in r2.json()
    assert "latency_sec" in r2.json()
    assert r2.json()["latency_sec"] >= 0