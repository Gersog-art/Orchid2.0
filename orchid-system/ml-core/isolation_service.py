from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest

app = FastAPI()

# Создаем простую модель для теста
try:
    model = joblib.load("/app/models/isolation_forest_v1.joblib")
except:
    print("Creating new Isolation Forest model...")
    model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
    X_train = np.random.randn(1000, 5)
    model.fit(X_train)
    joblib.dump(model, "/app/models/isolation_forest_v1.joblib")

class RequestData(BaseModel):
    features: list

@app.post("/predict")
def predict(data: RequestData):
    features = np.array(data.features).reshape(1, -1)
    prediction = model.predict(features)
    score = model.score_samples(features)
    
    return {
        "is_anomaly": prediction[0] == -1,
        "anomaly_score": float(score[0]),
        "message": "Anomaly detected" if prediction[0] == -1 else "Normal"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "model": "Isolation Forest"}
