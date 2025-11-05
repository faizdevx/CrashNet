import pandas as pd
from joblib import load
model = load("models/model.pkl")
def predict_row(row):
    X = pd.DataFrame([row])
    return int(model.predict(X)[0])

