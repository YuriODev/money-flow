#!/bin/bash

# Development Environment Setup Script
# This script sets up the complete development environment for the Subscription Tracker

set -e  # Exit on error

echo "🚀 Setting up Subscription Tracker development environment..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running from project root
if [ ! -f "pyproject.toml" ]; then
    echo "❌ Error: Must run from project root directory"
    exit 1
fi

# Step 1: Check Python version
echo -e "\n${BLUE}📋 Checking Python version...${NC}"
python_version=$(python --version 2>&1 | awk '{print $2}')
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${YELLOW}⚠️  Warning: Python 3.11+ recommended, found $python_version${NC}"
fi

# Step 2: Create virtual environment
echo -e "\n${BLUE}🐍 Creating Python virtual environment...${NC}"
if [ ! -d ".venv" ]; then
    python -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${YELLOW}⚠️  Virtual environment already exists${NC}"
fi

# Step 3: Activate virtual environment
echo -e "\n${BLUE}🔌 Activating virtual environment...${NC}"
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    echo -e "${GREEN}✓ Virtual environment activated${NC}"
else
    echo "❌ Error: Could not find activation script"
    exit 1
fi

# Step 4: Upgrade pip
echo -e "\n${BLUE}📦 Upgrading pip...${NC}"
pip install --upgrade pip

# Step 5: Install Python dependencies
echo -e "\n${BLUE}📚 Installing Python dependencies...${NC}"
pip install -e ".[dev]"
echo -e "${GREEN}✓ Python dependencies installed${NC}"

# Step 6: Install frontend dependencies
echo -e "\n${BLUE}🎨 Installing frontend dependencies...${NC}"
cd frontend
if [ -f "package.json" ]; then
    npm install
    echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
else
    echo "❌ Error: frontend/package.json not found"
    exit 1
fi
cd ..

# Step 7: Set up pre-commit hooks
echo -e "\n${BLUE}🪝 Setting up pre-commit hooks...${NC}"
if command -v pre-commit &> /dev/null; then
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
else
    echo -e "${YELLOW}⚠️  pre-commit not found, installing...${NC}"
    pip install pre-commit
    pre-commit install
    echo -e "${GREEN}✓ Pre-commit hooks installed${NC}"
fi

# Step 8: Check for .env file
echo -e "\n${BLUE}⚙️  Checking environment configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}⚠️  No .env file found. Creating from .env.example...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo -e "${YELLOW}⚠️  IMPORTANT: Update .env with your actual values!${NC}"
    else
        echo -e "${YELLOW}⚠️  No .env or .env.example found${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Step 9: Initialize secrets baseline
echo -e "\n${BLUE}🔒 Initializing secrets baseline...${NC}"
if [ ! -f ".secrets.baseline" ]; then
    detect-secrets scan > .secrets.baseline 2>/dev/null || echo "{}" > .secrets.baseline
    echo -e "${GREEN}✓ Secrets baseline created${NC}"
else
    echo -e "${YELLOW}⚠️  Secrets baseline already exists${NC}"
fi

# Step 10: Run pre-commit on all files (optional)
echo -e "\n${BLUE}🔍 Running pre-commit checks (optional)...${NC}"
read -p "Run pre-commit on all files? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pre-commit run --all-files || true
fi

# Step 11: Docker setup check
echo -e "\n${BLUE}🐳 Checking Docker setup...${NC}"
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker is installed${NC}"
    if command -v docker-compose &> /dev/null; then
        echo -e "${GREEN}✓ Docker Compose is installed${NC}"
    else
        echo -e "${YELLOW}⚠️  Docker Compose not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker not found (optional for development)${NC}"
fi

# Success message
echo -e "\n${GREEN}✨ Development environment setup complete!${NC}"
echo -e "\n${BLUE}Next steps:${NC}"
echo "1. Update .env file with your API keys and configuration"
echo "2. Start Docker containers: docker-compose up --build"
echo "3. Or run backend locally: uvicorn src.main:app --reload --port 8001"
echo "4. Or run frontend locally: cd frontend && npm run dev"
echo ""
echo -e "${BLUE}Documentation:${NC}"
echo "- Project guide: CLAUDE.md"
echo "- Python standards: .claude/docs/PYTHON_STANDARDS.md"
echo "- TypeScript standards: .claude/docs/TYPESCRIPT_STANDARDS.md"
echo "- Architecture: .claude/docs/ARCHITECTURE.md"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
