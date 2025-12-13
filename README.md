# 📊 Subscription Tracker

A modern subscription and recurring payment tracking application with an **agentic interface** powered by Claude AI. Features a beautiful Next.js frontend with Tailwind CSS, FastAPI backend, and PostgreSQL database - all running in Docker containers.

## ✨ Features

- 🎯 **Modern UI/UX**: Beautiful, responsive interface built with Next.js 14, TypeScript, and Tailwind CSS
- 🤖 **AI-Powered Assistant**: Natural language commands using Claude API (e.g., "Add Netflix for $15.99 monthly")
- 📝 **Flexible Tracking**: Support for daily, weekly, biweekly, monthly, quarterly, and yearly subscriptions
- 💰 **Smart Analytics**: Automatic spending calculations, summaries, and upcoming payment alerts
- 📊 **Category Organization**: Organize subscriptions by category (Entertainment, Health, etc.)
- 🐳 **Docker Ready**: Multi-container setup with PostgreSQL, FastAPI, and Next.js
- 🚀 **Production Ready**: Deployable to GCP Cloud Run with minimal configuration

## 🏗️ Architecture

This application uses a microservices architecture with separate containers:

- **Frontend**: Next.js 14 + TypeScript + Tailwind CSS (Port 3002)
- **Backend**: FastAPI + SQLAlchemy 2.0 (Port 8001)
- **Database**: PostgreSQL 15 (Port 5433)

All containers communicate via a Docker bridge network.

## 🚀 Quick Start with Docker (Recommended)

### Prerequisites

- Docker Desktop
- Claude API Key from [Anthropic](https://console.anthropic.com/)

### Setup

1. **Clone and enter the project**
```bash
cd subscription-tracker
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your Claude API key:
# ANTHROPIC_API_KEY=sk-ant-api03-...
```

3. **Start all services**
```bash
docker-compose up --build
```

4. **Access the application**
- **Frontend**: http://localhost:3002
- **Backend API**: http://localhost:8001
- **API Docs (Swagger)**: http://localhost:8001/docs

### Stopping the Services

```bash
# Stop all containers
docker-compose down

# Stop and remove volumes (clean database)
docker-compose down -v
```

---

## 🔧 Local Development (Without Docker)

### Backend Setup

```bash
# Create and activate virtual environment
python -m venv .venv

# For Fish shell
source .venv/bin/activate.fish

# For Bash/Zsh
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Set environment variables
export DATABASE_URL=sqlite+aiosqlite:///./subscriptions.db
export ANTHROPIC_API_KEY=sk-ant-api03-...

# Run the backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8001
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env.local
echo "NEXT_PUBLIC_API_URL=http://localhost:8001" > .env.local

# Run development server
npm run dev
```

The frontend will be available at http://localhost:3000

---

## 🤖 Using the AI Assistant

The AI Assistant allows you to manage subscriptions using natural language. Here are some example commands:

### Adding Subscriptions
```
"Add Netflix subscription for $15.99 monthly"
"Subscribe to Spotify Premium for $9.99 monthly"
"Add therapy sessions for $150 biweekly"
"New subscription Disney+ $7.99 monthly category entertainment"
```

### Viewing Subscriptions
```
"Show all my subscriptions"
"List active subscriptions"
"What are my subscriptions?"
```

### Analytics
```
"How much am I spending per month?"
"Show my spending summary"
"What's my total monthly cost?"
```

### Upcoming Payments
```
"What's due this week?"
"Show upcoming payments"
"What payments are coming up?"
```

### Managing Subscriptions
```
"Cancel my gym membership"
"Delete Netflix subscription"
"Update therapy sessions to $160"
```

---

## 📚 API Documentation

Once the backend is running, visit http://localhost:8001/docs for interactive API documentation.

### Main Endpoints

- `GET /api/subscriptions` - List all subscriptions
- `POST /api/subscriptions` - Create a new subscription
- `GET /api/subscriptions/{id}` - Get a specific subscription
- `PUT /api/subscriptions/{id}` - Update a subscription
- `DELETE /api/subscriptions/{id}` - Delete a subscription
- `GET /api/subscriptions/summary` - Get spending summary
- `POST /api/agent/execute` - Execute natural language command

---

## 🧪 Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/unit -v
pytest tests/integration -v
pytest tests/agent -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

---

## 📦 Deployment to GCP Cloud Run

### Prerequisites

- Google Cloud account
- `gcloud` CLI installed and configured
- Project created in GCP Console

### Deploy Backend

```bash
# Set your project
gcloud config set project YOUR_PROJECT_ID

# Deploy backend
gcloud run deploy subscription-tracker-backend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="ANTHROPIC_API_KEY=sk-ant-..." \
  --set-env-vars="DATABASE_URL=postgresql+asyncpg://..."
```

### Deploy Frontend

```bash
cd frontend

gcloud run deploy subscription-tracker-frontend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="NEXT_PUBLIC_API_URL=https://your-backend-url.run.app"
```

See `deploy/gcp/README.md` for detailed deployment instructions.

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query (TanStack Query)
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Date Handling**: date-fns

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11+
- **ORM**: SQLAlchemy 2.0 (async)
- **Validation**: Pydantic v2
- **Database**: PostgreSQL / SQLite
- **Migrations**: Alembic
- **AI**: Anthropic Claude API

### DevOps
- **Containerization**: Docker
- **Orchestration**: Docker Compose
- **CI/CD**: GitHub Actions (optional)
- **Deployment**: GCP Cloud Run

---

## 📁 Project Structure

See [CLAUDE.md](./CLAUDE.md) for detailed project structure and development guide.

---

## 🤝 Contributing

This is a personal project, but suggestions and feedback are welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - feel free to use this project for your own subscription tracking needs!

---

## 🙏 Acknowledgments

- Built with [Claude AI](https://anthropic.com) for the agentic interface
- UI inspired by modern SaaS dashboards
- Icons by [Lucide](https://lucide.dev/)

---

**Built with ❤️ using Next.js, FastAPI, and Claude AI**
