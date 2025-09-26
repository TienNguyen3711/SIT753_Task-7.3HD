import joblib
import json
import numpy as np
import pandas as pd


def test_model_can_predict():
    model = joblib.load("model/model.pkl")
    cols = json.load(open("model/columns.json"))

    # Tạo dataframe 1 hàng, với toàn bộ features = 0
    x = pd.DataFrame([np.zeros(len(cols))], columns=cols)

    y = model.predict(x)[0]

    assert isinstance(float(y), float)
    assert y >= 0
