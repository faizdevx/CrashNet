import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from joblib import dump
import os

os.makedirs("models", exist_ok=True)
df = pd.read_csv("data/synthetic_example.csv")
X = df[['speed','accel','gyro','distance']]
y = df['label']
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X,y)
dump(clf, "models/model.pkl")
print("Saved models/model.pkl")
