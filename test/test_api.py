from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"

def test_predict_endpoint():
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
    r = client.post("/predict", json=payload)
    assert r.status_code == 200
    data = r.json()
    assert "prediction" in data
    assert isinstance(data["prediction"], float)