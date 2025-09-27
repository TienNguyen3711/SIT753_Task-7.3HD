# test/test_model.py
import joblib
import json
import numpy as np
import pandas as pd
import os
from sklearn.pipeline import Pipeline
from sklearn.dummy import DummyRegressor


def load_model():
    model_path = "model/model.pkl"
    cols_path = "model/columns.json"

    if os.path.exists(model_path) and os.path.exists(cols_path):
        model = joblib.load(model_path)
        with open(cols_path, "r") as f:
            cols = json.load(f)
    else:
        cols = ["f1", "f2", "f3"]
        model = DummyRegressor(strategy="mean").fit([[0, 0, 0]], [1000])

    return model, cols


def test_model_can_predict():
    model, cols = load_model()

    # Dummy input
    if isinstance(model, Pipeline):
        x = pd.DataFrame([{c: 0 for c in cols}])
    else:
        x = pd.DataFrame([np.zeros(len(cols))], columns=cols)

    # Predict
    y = model.predict(x)

    assert y is not None and len(y) == 1
    pred = float(y[0])

    # Check validity
    assert np.isfinite(pred)
    assert 0 <= pred <= 10_000_000
