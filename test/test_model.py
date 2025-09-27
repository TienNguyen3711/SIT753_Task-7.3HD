# test/test_model.py
import joblib
import json
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline


def test_model_can_predict():
    # Load model & metadata
    model = joblib.load("model/model.pkl")
    with open("model/columns.json", "r") as f:
        cols = json.load(f)

    # Ensure model expects same number of features (nếu model không phải pipeline)
    n_features_model = getattr(model, "n_features_in_", None)
    if n_features_model is not None:
        assert n_features_model == len(cols), (
            f"Model expects {n_features_model} features, but columns.json has {len(cols)}"
        )

    # Tạo dummy input
    if isinstance(model, Pipeline):
        # Nếu là pipeline -> dùng DataFrame với cả string & numeric
        sample = {
            "suburb": "Richmond",
            "property_type": "House",
            "number_of_bedroom": 3,
            "bathroom": 2,
            "car_park": 1,
            "land_size_sq": 250,
            "agency_name": "Ray White",
            "distance_to_landmark": 5.2,
            "bedrooms_per_land_size": 0.012,
            "bathrooms_per_bedroom": 0.67,
            "price_per_sq_meter": 8500,
            "year_week": "2025-38"
        }
        x = pd.DataFrame([sample], columns=cols)
    else:
        # Nếu không phải pipeline -> toàn số (0.0)
        x = pd.DataFrame([np.zeros(len(cols))], columns=cols)

    # Make prediction
    y = model.predict(x)
    assert y is not None and len(y) == 1, "Model did not return a single prediction"

    pred = float(y[0])
    assert np.isfinite(pred), f"Prediction is not finite: {pred}"
    assert pred >= 0, f"Prediction should be >= 0, got {pred}"
    assert pred < 10_000_000, f"Prediction seems too high: {pred}"