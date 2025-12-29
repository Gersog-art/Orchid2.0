#!/bin/bash

echo "Quick start for Orchid System..."
echo "================================="

# Create required directories
mkdir -p ml-core/models ml-core/training_data
mkdir -p data/{postgres,redis,rabbitmq}

# Create dummy ML models if they don't exist
if [ ! -f "ml-core/models/isolation_forest_v1.joblib" ]; then
    echo "Creating dummy ML models..."
    python3 -c "
import joblib
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier

# Create dummy Isolation Forest model
if_model = IsolationForest(n_estimators=10, contamination=0.1, random_state=42)
X_dummy = np.random.randn(100, 8)
if_model.fit(X_dummy)
joblib.dump(if_model, 'ml-core/models/isolation_forest_v1.joblib')

# Create dummy Random Forest model
rf_model = RandomForestClassifier(n_estimators=10, random_state=42)
y_dummy = np.random.choice(['normal', 'sqli', 'xss'], 100)
rf_model.fit(X_dummy, y_dummy)
joblib.dump(rf_model, 'ml-core/models/random_forest_v1.joblib')
print('Dummy models created')
"
fi

# Build and start services
echo "Building and starting Docker services..."
docker-compose down 2>/dev/null
docker-compose build --no-cache ml-isolation-forest ml-random-forest
docker-compose up -d rabbitmq postgres redis

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Check RabbitMQ
for i in {1..30}; do
    if docker-compose exec rabbitmq rabbitmqctl status >/dev/null 2>&1; then
        echo "✓ RabbitMQ is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "✗ RabbitMQ failed to start"
        exit 1
    fi
    echo "Waiting for RabbitMQ... ($i/30)"
    sleep 2
done

# Start ML services
docker-compose up -d ml-isolation-forest ml-random-forest orchid-core orchid-admin

echo ""
echo "========================================="
echo "Orchid System Started!"
echo "========================================="
echo ""
echo "Services:"
echo "- RabbitMQ Management: http://localhost:15672"
echo "  Username: ${RABBITMQ_USER:-orchid_admin}"
echo "  Password: ${RABBITMQ_PASS:-SecurePass123!}"
echo "- Isolation Forest API: http://localhost:8001/health"
echo "- Random Forest API: http://localhost:8002/health"
echo "- Admin Panel: http://localhost:3000"
echo ""
echo "To stop: docker-compose down"
echo "To view logs: docker-compose logs -f"
