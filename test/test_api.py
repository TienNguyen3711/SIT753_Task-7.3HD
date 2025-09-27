import time
import requests
import threading
import uvicorn
import random
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


def random_payload():
    suburbs = ["Richmond", "Box Hill", "South Yarra", "St Kilda"]
    property_types = ["House", "Unit", "Apartment", "Townhouse"]
    agencies = ["Ray White", "Domain", "Jellis Craig", "Harcourts"]

    # Luôn trả về 1 dict (không bị list bọc ngoài)
    return {
        "features": {
            "suburb": random.choice(suburbs),
            "property_type": random.choice(property_types),
            "number_of_bedroom": random.randint(1, 5),
            "bathroom": random.randint(1, 3),
            "car_park": random.randint(0, 2),
            "land_size_sq": random.randint(100, 800),
            "agency_name": random.choice(agencies),
            "distance_to_landmark": round(random.uniform(1, 15), 2),
            "bedrooms_per_land_size": round(random.uniform(0.005, 0.02), 3),
            "bathrooms_per_bedroom": round(random.uniform(0.3, 1.5), 2),
            "price_per_sq_meter": random.randint(5000, 12000),
            "year_week": "2025-38"
        }
    }


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

    # Test /predict với payload random (luôn đúng format)
    payload = random_payload()
    r2 = requests.post("http://127.0.0.1:8000/predict", json=payload)
    assert r2.status_code == 200, f"Predict failed: {r2.text}"

    data = r2.json()
    assert "prediction" in data
    assert "latency_sec" in data
    assert isinstance(data["prediction"], (int, float))
    assert isinstance(data["latency_sec"], (int, float))
    assert data["latency_sec"] >= 0
