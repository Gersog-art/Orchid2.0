#!/bin/bash

# Orchid System Startup Script

echo "Starting Orchid Security System..."

# Check for Docker and Docker Compose
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "Error: Docker Compose is not installed"
    exit 1
fi

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found. Using defaults."
fi

# Create required directories
mkdir -p ml-core/models ml-core/training_data
mkdir -p data/{postgres,redis,rabbitmq}

# Function to check service health
check_service() {
    local service=$1
    local port=$2
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for $service to be ready..."
    
    while [ $attempt -le $max_attempts ]; do
        if nc -z localhost $port 2>/dev/null; then
            echo "$service is ready!"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts: $service not ready yet..."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    echo "Error: $service failed to start"
    return 1
}

# Start services
echo "Starting Docker containers..."
docker-compose up -d

# Check critical services
check_service "RabbitMQ" 5672 || exit 1
check_service "PostgreSQL" 5432 || exit 1
check_service "Redis" 6379 || exit 1

# Wait for ML services
sleep 10

# Initialize ML models if needed
echo "Initializing ML models..."
docker exec orchid-ml-isolation python -c "
from isolation_service import MLService
ml = MLService()
print('Isolation Forest service ready')
"

docker exec orchid-ml-random python -c "
import sys
sys.path.append('/app')
from random_service import MLService
ml = MLService()
print('Random Forest service ready')
"

echo "========================================="
echo "Orchid System Started Successfully!"
echo "========================================="
echo ""
echo "Access the following services:"
echo "- Admin Panel: http://localhost:3000"
echo "- API Documentation: http://localhost:8080/docs"
echo "- RabbitMQ Management: http://localhost:15672"
echo "  Username: $RABBITMQ_USER"
echo "  Password: $RABBITMQ_PASS"
echo ""
echo "To integrate with Juice Shop:"
echo "1. Navigate to your Juice Shop directory"
echo "2. Run: ./orchid-system/agent/juice-shop/integrate.sh"
echo "3. Follow the integration instructions"
echo ""
echo "To stop the system: ./stop-orchid.sh"
