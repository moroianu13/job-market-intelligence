#!/bin/bash

# Deployment Script for Job Market Intelligence
# Usage: ./deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
APP_NAME="job-market-intelligence"

echo "🚀 Deploying $APP_NAME to $ENVIRONMENT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Docker is required but not installed.${NC}" >&2; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo -e "${RED}Docker Compose is required but not installed.${NC}" >&2; exit 1; }

# Load environment variables
if [ -f ".env.${ENVIRONMENT}" ]; then
    echo -e "${GREEN}Loading environment variables from .env.${ENVIRONMENT}${NC}"
    export $(cat .env.${ENVIRONMENT} | grep -v '^#' | xargs)
elif [ -f ".env" ]; then
    echo -e "${YELLOW}Loading environment variables from .env${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}No .env file found!${NC}"
    exit 1
fi

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
pytest --tb=short -q || { echo -e "${RED}Tests failed!${NC}"; exit 1; }
echo -e "${GREEN}✅ All tests passed${NC}"

# Build Docker images
echo -e "${YELLOW}Building Docker images...${NC}"
docker-compose -f docker-compose.prod.yml build --parallel

# Tag images
GIT_SHA=$(git rev-parse --short HEAD)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TAG="${ENVIRONMENT}-${GIT_SHA}-${TIMESTAMP}"

echo -e "${GREEN}Tagging images with: ${TAG}${NC}"
docker tag ${APP_NAME}:latest ${APP_NAME}:${TAG}

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down

# Start new containers
echo -e "${YELLOW}Starting containers...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# Wait for services to be healthy
echo -e "${YELLOW}Waiting for services to be healthy...${NC}"
sleep 10

# Health checks
echo -e "${YELLOW}Running health checks...${NC}"
docker-compose -f docker-compose.prod.yml ps

# Check Streamlit
if curl -f http://localhost:8501/_stcore/health >/dev/null 2>&1; then
    echo -e "${GREEN}✅ Streamlit is healthy${NC}"
else
    echo -e "${RED}❌ Streamlit health check failed${NC}"
    docker-compose -f docker-compose.prod.yml logs streamlit
    exit 1
fi

# Database migration (if needed)
if [ "$ENVIRONMENT" = "production" ]; then
    echo -e "${YELLOW}Running database migrations...${NC}"
    # Add migration commands here
fi

# Backup data
echo -e "${YELLOW}Creating backup...${NC}"
BACKUP_DIR="backups/${TIMESTAMP}"
mkdir -p ${BACKUP_DIR}
docker-compose -f docker-compose.prod.yml exec -T postgres pg_dump -U admin job_intelligence > ${BACKUP_DIR}/db_backup.sql
tar -czf ${BACKUP_DIR}/data_backup.tar.gz data/curated/snapshots/

echo -e "${GREEN}✅ Backup created: ${BACKUP_DIR}${NC}"

# Show running containers
echo -e "${YELLOW}Currently running containers:${NC}"
docker-compose -f docker-compose.prod.yml ps

# Display URLs
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "📊 Streamlit UI:  ${YELLOW}http://localhost:8501${NC}"
echo -e "📈 Grafana:       ${YELLOW}http://localhost:3000${NC} (admin / ${GRAFANA_PASSWORD:-admin})"
echo -e "🔍 Prometheus:    ${YELLOW}http://localhost:9090${NC}"
echo ""
echo -e "📝 View logs:     ${YELLOW}docker-compose -f docker-compose.prod.yml logs -f${NC}"
echo -e "🛑 Stop services: ${YELLOW}docker-compose -f docker-compose.prod.yml down${NC}"
echo ""
