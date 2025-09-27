# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List
import joblib
import json
import numpy as np
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

app = FastAPI(title="Housing Price Prediction API", version="1.0.0")

# Global vars cho model và feature columns
model = None
FEATURE_COLUMNS: List[str] = []

# Prometheus metrics
PRED_REQUESTS = Counter("pred_requests_total", "Total prediction requests")
PRED_LATENCY = Histogram("pred_latency_seconds", "Prediction latency in seconds")


class Payload(BaseModel):
    features: Dict[str, float] = Field(
        ..., example={"feature1": 0.5, "feature2": 1.2, "feature3": 3.0}
    )


@app.on_event("startup")
def load_model():
    """Load model và metadata khi app khởi động"""
    global model, FEATURE_COLUMNS
    try:
        MODEL_PATH = "model/model.pkl"
        COLUMNS_PATH = "model/columns.json"
        model = joblib.load(MODEL_PATH)
        with open(COLUMNS_PATH, "r") as f:
            FEATURE_COLUMNS = json.load(f)
    except Exception as e:
        raise RuntimeError(f"❌ Failed to load model or columns: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict")
def predict(payload: Payload):
    if model is None or not FEATURE_COLUMNS:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start = time.time()
    PRED_REQUESTS.inc()

    try:
        # build feature vector theo đúng thứ tự
        x = [float(payload.features.get(col, 0.0)) for col in FEATURE_COLUMNS]
        y_pred = model.predict([x])[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")

    latency = time.time() - start
    PRED_LATENCY.observe(latency)

    return {"prediction": float(y_pred), "latency_sec": latency}
