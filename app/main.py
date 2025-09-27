# app/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Any
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
IS_PIPELINE = False  # flag để check model có phải sklearn.pipeline không

# Prometheus metrics
PRED_REQUESTS = Counter("pred_requests_total", "Total prediction requests")
PRED_LATENCY = Histogram("pred_latency_seconds", "Prediction latency in seconds")


class Payload(BaseModel):
    features: Dict[str, Any] = Field(
        ..., example={
            "suburb": "Richmond",
            "property_type": "House",
            "number_of_bedroom": 3,
            "bathroom": 2
        }
    )


@app.on_event("startup")
def load_model():
    """Load model và metadata khi app khởi động"""
    global model, FEATURE_COLUMNS, IS_PIPELINE
    try:
        MODEL_PATH = "model/model.pkl"
        COLUMNS_PATH = "model/columns.json"
        model = joblib.load(MODEL_PATH)
        with open(COLUMNS_PATH, "r") as f:
            FEATURE_COLUMNS = json.load(f)

        # check xem model có phải pipeline không
        from sklearn.pipeline import Pipeline
        IS_PIPELINE = isinstance(model, Pipeline)

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
        if IS_PIPELINE:
            # Nếu model là pipeline sklearn -> đưa dict vào, pipeline sẽ tự xử lý
            X = [payload.features]
            y_pred = model.predict(X)[0]
        else:
            # Nếu không phải pipeline -> fallback: ép về float theo FEATURE_COLUMNS
            x = [float(payload.features.get(col, 0.0)) for col in FEATURE_COLUMNS]
            y_pred = model.predict([x])[0]

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")

    latency = time.time() - start
    PRED_LATENCY.observe(latency)

    return {"prediction": float(y_pred), "latency_sec": latency}
