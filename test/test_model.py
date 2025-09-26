import joblib, json
import numpy as np


def test_model_can_predict():
    model = joblib.load("model/model.pkl")
    cols = json.load(open("model/columns.json"))
    x = np.zeros(len(cols))
    y = model.predict([x])[0]
    assert isinstance(float(y), float)
    assert y >= 0
