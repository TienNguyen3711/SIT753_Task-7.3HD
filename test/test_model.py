# test/test_model.py
import joblib
import json
import numpy as np
import pandas as pd


def test_model_can_predict():
    # Load model & metadata
    model = joblib.load("model/model.pkl")
    with open("model/columns.json", "r") as f:
        cols = json.load(f)

    # Ensure model expects same number of features
    n_features_model = getattr(model, "n_features_in_", None)
    assert n_features_model is None or n_features_model == len(cols), (
        f"Model expects {n_features_model} features, but columns.json has {len(cols)}"
    )

    # Create dummy input (1 row of all zeros)
    x = pd.DataFrame([np.zeros(len(cols))], columns=cols)

    # Make prediction
    y = model.predict(x)
    assert y is not None and len(y) == 1, "Model did not return a single prediction"

    pred = float(y[0])
    assert not np.isnan(pred), "Prediction is NaN"
    assert np.isfinite(pred), "Prediction is not finite"
    assert pred >= 0, f"Prediction should be >= 0, got {pred}"
    assert isinstance(pred, float), f"Prediction should be float, got {type(pred)}"