# GCP Deployment Guide

## Prerequisites

1. GCP project with billing enabled
2. APIs enabled:
   - Cloud Run
   - Cloud Build
   - Secret Manager
   - Cloud SQL (for PostgreSQL)

## Setup Steps

### 1. Create PostgreSQL Instance

```bash
gcloud sql instances create subscription-tracker-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

gcloud sql databases create subscriptions \
  --instance=subscription-tracker-db

gcloud sql users create app \
  --instance=subscription-tracker-db \
  --password=YOUR_SECURE_PASSWORD
```

### 2. Store Secrets

```bash
# Database URL
echo -n "postgresql+asyncpg://app:PASSWORD@/subscriptions?host=/cloudsql/PROJECT:REGION:subscription-tracker-db" | \
  gcloud secrets create subscription-tracker-db-url --data-file=-

# Anthropic API Key
echo -n "sk-ant-your-key" | \
  gcloud secrets create anthropic-api-key --data-file=-
```

### 3. Deploy

```bash
# From project root
gcloud builds submit --config=deploy/gcp/cloudbuild.yaml
```

### 4. Connect Cloud SQL

The Cloud Run service automatically connects to Cloud SQL via Unix socket.
