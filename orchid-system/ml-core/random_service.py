from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier

app = FastAPI()

# Создаем простую модель для теста
try:
    model = joblib.load("/app/models/random_forest_v1.joblib")
except:
    print("Creating new Random Forest model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    X_train = np.random.randn(1000, 5)
    y_train = np.random.choice(['normal', 'sqli', 'xss'], 1000)
    model.fit(X_train, y_train)
    joblib.dump(model, "/app/models/random_forest_v1.joblib")

class RequestData(BaseModel):
    features: list

@app.post("/predict")
def predict(data: RequestData):
    features = np.array(data.features).reshape(1, -1)
    prediction = model.predict(features)
    probability = model.predict_proba(features)
    
    return {
        "prediction": prediction[0],
        "confidence": float(np.max(probability[0])),
        "probabilities": dict(zip(model.classes_, probability[0].tolist()))
    }

@app.get("/health")
def health():
    return {"status": "healthy", "model": "Random Forest"}
