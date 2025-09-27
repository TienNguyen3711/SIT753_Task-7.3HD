import threading
import time
import requests
import uvicorn
from app.main import app

def test_health_and_predict():
    # chạy API trong thread nền
    t = threading.Thread(target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error"), daemon=True)
    t.start()

    # chờ API sẵn sàng
    start = time.time()
    while time.time() - start < 10:
        try:
            r = requests.get("http://127.0.0.1:8000/health")
            if r.status_code == 200 and r.json().get("status") == "ok":
                break
        except requests.exceptions.ConnectionError:
            pass
        time.sleep(0.5)
    else:
        assert False, "API did not become healthy in time"

    # test /health
    r = requests.get("http://127.0.0.1:8000/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

    # test /predict với payload cố định
    payload = {
        "features": {
            "suburb": "Box Hill",
            "property_type": "Unit",
            "number_of_bedroom": 4,
            "bathroom": 1,
            "car_park": 1,
            "land_size_sq": 730,
            "agency_name": "Harcourts",
            "distance_to_landmark": 2.16,
            "bedrooms_per_land_size": 0.019,
            "bathrooms_per_bedroom": 1.0,
            "price_per_sq_meter": 10751,
            "year_week": "2025-38"
        }
    }
    r2 = requests.post("http://127.0.0.1:8000/predict", json=payload)
    assert r2.status_code == 200, f"Predict failed: {r2.text}"

    data = r2.json()
    assert "prediction" in data
    assert "latency_sec" in data
    assert data["latency_sec"] >= 0
