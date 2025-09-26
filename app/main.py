# app/main.py
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, List
import joblib
import json
import numpy as np
import time
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

app = FastAPI(title="Housing Price Prediction API", version="1.0.0")

# Load model + feature order
MODEL_PATH = "model/model.pkl"
COLUMNS_PATH = "model/columns.json"
model = joblib.load(MODEL_PATH)
with open(COLUMNS_PATH, "r") as f:
    FEATURE_COLUMNS: List[str] = json.load(f)

# Metrics (Monitoring)
PRED_REQUESTS = Counter("pred_requests_total", "Total prediction requests")
PRED_LATENCY = Histogram("pred_latency_seconds", "Prediction latency in seconds")


class Payload(BaseModel):
    features: Dict[str, float]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/predict")
def predict(payload: Payload):
    start = time.time()
    PRED_REQUESTS.inc()

    x = [float(payload.features.get(col, 0.0)) for col in FEATURE_COLUMNS]
    y_pred = model.predict([x])[0]
    latency = time.time() - start
    PRED_LATENCY.observe(latency)
    return {"prediction": float(y_pred), "latency_sec": latency}
