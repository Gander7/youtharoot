#!/bin/bash

# Integration Test Runner with PostgreSQL
# This script sets up PostgreSQL testing environment and runs integration tests

set -e  # Exit on any error

echo "🧪 Starting Integration Tests with PostgreSQL"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.test.yml"
SERVICE_NAME="test-postgres"
MAX_WAIT_TIME=30

# Functions
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    # docker compose -f $COMPOSE_FILE down -v
    echo -e "${GREEN}✅ Cleanup complete${NC}"
}

wait_for_db() {
    echo -e "${BLUE}⏳ Waiting for PostgreSQL to be ready...${NC}"
    local count=0
    while ! docker compose -f $COMPOSE_FILE exec -T $SERVICE_NAME pg_isready -U test_user -d test_youth_attendance; do
        count=$((count + 1))
        if [ $count -gt $MAX_WAIT_TIME ]; then
            echo -e "${RED}❌ PostgreSQL failed to start within $MAX_WAIT_TIME seconds${NC}"
            cleanup
            exit 1
        fi
        echo -e "${YELLOW}⏳ Waiting for database... (attempt $count/$MAX_WAIT_TIME)${NC}"
        sleep 1
    done
    echo -e "${GREEN}✅ PostgreSQL is ready!${NC}"
}

# Trap cleanup on script exit
trap cleanup EXIT

# Main execution
echo -e "${BLUE}🐳 Starting PostgreSQL test container...${NC}"
docker compose -f $COMPOSE_FILE up -d

# Wait for database to be ready
wait_for_db

# Set environment to use PostgreSQL
export DATABASE_TYPE=postgresql
export DATABASE_URL=postgresql://test_user:test_password@localhost:5433/test_youth_attendance
export ADMIN_PASSWORD=test_admin_password123

echo -e "${BLUE}🔧 Running database setup...${NC}"
# Initialize database tables
python -c "
from app.database import init_database
from app.repositories import init_repositories
print('✅ Initializing database...')
init_database()
print('✅ Initializing repositories...')
init_repositories()
print('✅ Database setup complete!')
"

echo -e "${BLUE}🧪 Running integration tests...${NC}"

# Run tests excluding messaging features that aren't implemented yet
if python -m pytest tests/ -v --tb=short; then
    echo -e "${GREEN}🎉 All integration tests passed!${NC}"
else
    echo -e "${RED}❌ Some integration tests failed${NC}"
    exit 1
fi

echo -e "${BLUE}📊 Running tests with coverage...${NC}"
python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

echo -e "${GREEN}✅ Integration testing complete!${NC}"
echo -e "${BLUE}📊 Coverage report generated in htmlcov/index.html${NC}"