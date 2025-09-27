from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Any
import joblib
import json
import time
import os
from datetime import datetime
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

app = FastAPI(title="Housing Price Prediction API", version="1.0.0")

# ----------------------
# Global vars cho model và feature columns
# ----------------------
model = None
FEATURE_COLUMNS: List[str] = []
IS_PIPELINE = False

# Fake DB cho user & prediction history
users = {}          # username -> password
predictions = []    # list lưu lịch sử dự đoán

# ----------------------
# Prometheus metrics
# ----------------------
PRED_REQUESTS = Counter("pred_requests_total", "Total prediction requests")
PRED_LATENCY = Histogram("pred_latency_seconds", "Prediction latency in seconds")


# ----------------------
# Schemas
# ----------------------
class Payload(BaseModel):
    features: Dict[str, Any] = Field(
        ...,
        example={
            "suburb": "Richmond",
            "property_type": "House",
            "number_of_bedroom": 3,
            "bathroom": 2
        }
    )

class User(BaseModel):
    username: str
    password: str


# ----------------------
# Load model khi app startup
# ----------------------
@app.on_event("startup")
def load_model():
    global model, FEATURE_COLUMNS, IS_PIPELINE
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        MODEL_PATH = os.path.join(current_dir, "..", "model", "model.pkl")
        COLUMNS_PATH = os.path.join(current_dir, "..", "model", "columns.json")

        model = joblib.load(MODEL_PATH)
        with open(COLUMNS_PATH, "r") as f:
            FEATURE_COLUMNS = json.load(f)

        from sklearn.pipeline import Pipeline
        IS_PIPELINE = isinstance(model, Pipeline)
        print("Model và metadata đã được tải thành công!")

    except Exception as e:
        print(f"Lỗi khi tải model. Kiểm tra: {MODEL_PATH} và {COLUMNS_PATH}")
        raise RuntimeError(f"Failed to load model or columns: {e}")


# ----------------------
# Auth Endpoints
# ----------------------
@app.post("/auth/register")
def register(user: User):
    if user.username in users:
        raise HTTPException(status_code=400, detail="User already exists")
    users[user.username] = user.password
    return {"message": "✅ User registered successfully"}

@app.post("/auth/login")
def login(user: User):
    if users.get(user.username) != user.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    return {"token": "fake-jwt-token", "message": "✅ Login success"}


# ----------------------
# Prediction + CRUD History
# ----------------------
@app.post("/predict")
def predict(payload: Payload):
    if model is None or not FEATURE_COLUMNS:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start = time.time()
    PRED_REQUESTS.inc()

    try:
        if IS_PIPELINE:
            X = [payload.features]
            y_pred = model.predict(X)[0]
        else:
            x = [float(payload.features.get(col, 0.0)) for col in FEATURE_COLUMNS]
            y_pred = model.predict([x])[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")

    latency = time.time() - start
    PRED_LATENCY.observe(latency)

    # Lưu lịch sử
    record = {
        "id": len(predictions) + 1,
        "features": payload.features,
        "prediction": float(y_pred),
        "timestamp": datetime.now().isoformat()
    }
    predictions.append(record)

    return {"prediction": float(y_pred), "latency_sec": latency}


@app.get("/predictions")
def get_predictions():
    return predictions


@app.delete("/predictions/{pred_id}")
def delete_prediction(pred_id: int):
    global predictions
    predictions = [p for p in predictions if p["id"] != pred_id]
    return {"message": f"Prediction {pred_id} deleted"}


# ----------------------
# Model Info
# ----------------------
@app.get("/model/info")
def model_info():
    return {
        "model_name": "Housing Price Model",
        "version": "1.0.0",
        "features": FEATURE_COLUMNS,
        "is_pipeline": IS_PIPELINE
    }


# ----------------------
# Health & Metrics
# ----------------------
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
