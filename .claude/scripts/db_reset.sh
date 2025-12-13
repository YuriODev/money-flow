#!/bin/bash

# Database Reset Script
# WARNING: This will delete all data and reinitialize the database

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${RED}⚠️  DATABASE RESET SCRIPT${NC}"
echo -e "${YELLOW}This will delete all data in the database!${NC}\n"

# Confirm action
read -p "Are you sure you want to reset the database? (yes/NO) " -r
echo
if [[ ! $REPLY =~ ^yes$ ]]; then
    echo "Aborted."
    exit 0
fi

# Check if running in Docker or local
if [ -f "docker-compose.yml" ]; then
    echo -e "${BLUE}🐳 Docker environment detected${NC}"
    read -p "Reset Docker database? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Stopping containers...${NC}"
        docker-compose down

        echo -e "${BLUE}Removing database volume...${NC}"
        docker volume rm subscription-tracker_postgres_data 2>/dev/null || true

        echo -e "${BLUE}Starting containers...${NC}"
        docker-compose up -d db

        echo -e "${BLUE}Waiting for database to be ready...${NC}"
        sleep 5

        echo -e "${BLUE}Running migrations...${NC}"
        docker-compose exec backend alembic upgrade head

        echo -e "${GREEN}✓ Docker database reset complete${NC}"
        exit 0
    fi
fi

# Local database reset
echo -e "${BLUE}Resetting local database...${NC}"

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
    else
        echo -e "${RED}❌ Error: Virtual environment not found${NC}"
        exit 1
    fi
fi

# Read database URL from .env
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}❌ Error: .env file not found${NC}"
    exit 1
fi

# Drop all tables using Alembic
echo -e "${BLUE}Downgrading database...${NC}"
alembic downgrade base

# Run migrations
echo -e "${BLUE}Running migrations...${NC}"
alembic upgrade head

# Optional: Seed with sample data
read -p "Load sample data? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -f "scripts/seed_data.py" ]; then
        echo -e "${BLUE}Loading sample data...${NC}"
        python scripts/seed_data.py
        echo -e "${GREEN}✓ Sample data loaded${NC}"
    else
        echo -e "${YELLOW}⚠️  scripts/seed_data.py not found${NC}"
    fi
fi

echo -e "\n${GREEN}✨ Database reset complete!${NC}"
