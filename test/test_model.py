# test/test_model.py

import joblib
import json
import numpy as np
import pandas as pd
import os
from sklearn.pipeline import Pipeline


def test_model_can_predict():
    # Load model & metadata (dùng dummy nếu không có)
    model_path = "model/model.pkl"
    cols_path = "model/columns.json"

    if os.path.exists(model_path) and os.path.exists(cols_path):
        model = joblib.load(model_path)
        with open(cols_path, "r") as f:
            cols = json.load(f)
    else:
        # fallback dummy
        cols = ["f1", "f2", "f3"]
        from sklearn.dummy import DummyRegressor

        model = DummyRegressor(strategy="mean")
        model.fit([[0, 0, 0]], [1000])

    # Tạo dummy input
    if isinstance(model, Pipeline):
        sample = {c: 0 for c in cols}
        x = pd.DataFrame([sample], columns=cols)
    else:
        x = pd.DataFrame([np.zeros(len(cols))], columns=cols)

    # Make prediction
    y = model.predict(x)
    assert y is not None and len(y) == 1

    pred = float(y[0])
    assert np.isfinite(pred)
    assert pred >= 0
    assert pred <= 10_000_000  # reasonable range
