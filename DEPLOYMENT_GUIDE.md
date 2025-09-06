# Free Deployment Guide - YouTube Content Extractor

This guide shows you how to deploy your YouTube Content Extractor app completely **FREE** using modern cloud platforms.

## 🎯 Recommended Option: Railway + Neon

### Why This Combination?
- **Railway:** $5/month free credits (sufficient for small apps)
- **Neon:** Free PostgreSQL database (3GB storage)
- **Upstash:** Free Redis (10K commands/day)
- **Total Cost:** $0/month for development and small production use

---

## 🚀 Option 1: Railway Deployment (Recommended)

### Prerequisites
1. GitHub account with your project
2. Railway account (free signup)
3. Neon account (free PostgreSQL)

### Step 1: Prepare Your Repository

#### Create `railway.json` in project root:
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "dockerfile"
  },
  "deploy": {
    "startCommand": "docker-compose up",
    "healthcheckPath": "/health"
  }
}
```

#### Create `Dockerfile.railway` for Railway:
```dockerfile
FROM node:18-alpine AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS backend
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

COPY backend/ ./
COPY --from=frontend-build /app/frontend/build ./static

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Setup Free Database (Neon)

1. **Go to [Neon.tech](https://neon.tech)** and sign up
2. **Create a new project:** "YouTube Content Extractor"
3. **Copy connection string** (format: `postgresql://user:pass@host/db`)
4. **Create database schema:**
   ```sql
   -- Copy your database/schema.sql content here
   ```

### Step 3: Setup Free Redis (Upstash)

1. **Go to [Upstash.com](https://upstash.com)** and sign up
2. **Create Redis database:** Choose free tier
3. **Copy connection URL:** `redis://user:pass@host:port`

### Step 4: Deploy to Railway

1. **Visit [Railway.app](https://railway.app)** and sign up with GitHub
2. **Click "New Project"** → "Deploy from GitHub repo"
3. **Select your YouTube project repository**
4. **Add Environment Variables:**
   ```env
   # YouTube API
   YOUTUBE_API_KEY=AIzaSyCgV-_Z7Bku4A5khNoP0bzSH4XnArOsIko
   
   # Database (from Neon)
   DATABASE_URL=postgresql://user:pass@host.neon.tech/db
   
   # Redis (from Upstash)
   REDIS_URL=redis://user:pass@host.upstash.io:port
   
   # API Configuration
   API_HOST=0.0.0.0
   API_PORT=8000
   
   # Production settings
   ENV=production
   ```

5. **Deploy:** Railway will automatically build and deploy
6. **Get your URL:** Railway provides a free `.railway.app` domain

---

## 🚀 Option 2: Render.com (All-in-One)

### Step 1: Prepare Render Blueprint

#### Create `render.yaml` in project root:
```yaml
databases:
  - name: youtube-postgres
    databaseName: youtube_db
    user: youtube_user
    plan: free

  - name: youtube-redis
    type: redis
    plan: free

services:
  - type: web
    name: youtube-backend
    env: docker
    dockerfilePath: ./backend/Dockerfile
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: youtube-postgres
          property: connectionString
      - key: REDIS_URL
        fromDatabase:
          name: youtube-redis
          property: connectionString
      - key: YOUTUBE_API_KEY
        value: AIzaSyCgV-_Z7Bku4A5khNoP0bzSH4XnArOsIko
    buildCommand: pip install -r requirements.txt && python -m spacy download en_core_web_sm
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT

  - type: static
    name: youtube-frontend
    buildCommand: cd frontend && npm ci && npm run build
    staticPublishPath: frontend/build
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
```

### Step 2: Deploy to Render

1. **Visit [Render.com](https://render.com)** and sign up
2. **Click "New Blueprint"**
3. **Connect your GitHub repository**
4. **Render will read `render.yaml` and create all services**
5. **Free tier includes:**
   - PostgreSQL database (90 days, then $7/month)
   - Redis instance (90 days, then $7/month)
   - Web service (sleeps after 15min of inactivity)

---

## 🚀 Option 3: Fly.io (Advanced)

### Step 1: Install Fly CLI

```powershell
# Install flyctl
iwr https://fly.io/install.ps1 -useb | iex
```

### Step 2: Initialize Fly App

```powershell
# Navigate to project
cd "c:\Users\Tasmeer Jamali\OneDrive\Desktop\Youtube"

# Login to Fly.io
fly auth login

# Initialize app
fly launch --name youtube-extractor
```

### Step 3: Configure fly.toml

Fly will generate `fly.toml`. Update it:

```toml
app = "youtube-extractor"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile.production"

[env]
  PORT = "8000"
  API_HOST = "0.0.0.0"

[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true

[[services]]
  http_checks = []
  internal_port = 8000
  processes = ["app"]
  protocol = "tcp"
  script_checks = []

  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"
```

### Step 4: Add Databases

```powershell
# Create PostgreSQL
fly postgres create --name youtube-db

# Create Redis
fly redis create --name youtube-redis

# Set secrets
fly secrets set YOUTUBE_API_KEY=AIzaSyCgV-_Z7Bku4A5khNoP0bzSH4XnArOsIko
fly secrets set DATABASE_URL=<postgres-connection-string>
fly secrets set REDIS_URL=<redis-connection-string>
```

### Step 5: Deploy

```powershell
fly deploy
```

---

## 📊 Comparison Table

| Platform | Frontend | Backend | Database | Redis | Free Tier Limits | Best For |
|----------|----------|---------|----------|-------|------------------|----------|
| **Railway** | ✅ | ✅ | External | ✅ | $5/month credits | Beginners |
| **Render** | ✅ | ✅ | ✅ (90 days) | ✅ (90 days) | Limited uptime | Simple setup |
| **Fly.io** | ✅ | ✅ | ✅ | ✅ | 3 VMs, 256MB each | Advanced users |
| **Vercel + PlanetScale** | ✅ | ❌ | ✅ | External | Serverless limits | Frontend focus |

---

## 🔑 User API Key Management

### How It Works:

**Your Setup:**
- Your YouTube API key (`AIzaSyCgV-_Z7Bku4A5khNoP0bzSH4XnArOsIko`) serves as the **default fallback**
- When users don't provide their own API key, your key is used
- You maintain control and can monitor usage

**User Experience:**
- Users can **optionally** enter their own YouTube API key
- If provided, their key is used instead of yours
- This gives them unlimited quota on their own Google account
- API keys are validated in real-time

**Benefits:**
- **Scalability:** No quota limits when users provide their own keys
- **Cost Control:** Users pay for their own API usage
- **Flexibility:** Works with or without user keys
- **Privacy:** User keys are not stored permanently

### API Key Flow:

```
1. User visits your app
2. (Optional) User enters their YouTube API key
3. API key is validated in real-time ✅/❌
4. Search uses:
   - User's API key (if provided & valid)
   - Your default API key (as fallback)
5. Results returned normally
```

### For Users - Getting Their Own API Key:

**Instructions provided in the app:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable YouTube Data API v3
4. Create API Key credentials
5. Copy and paste into your app
6. Enjoy unlimited quota! 🚀

---

## 🔧 Production Configuration

### Environment Variables for Production:

```env
# Required for all platforms
# Your default YouTube API key (will be used as fallback)
YOUTUBE_API_KEY=AIzaSyCgV-_Z7Bku4A5khNoP0bzSH4XnArOsIko
DATABASE_URL=postgresql://user:pass@host:port/db
REDIS_URL=redis://user:pass@host:port
ENV=production
API_HOST=0.0.0.0
API_PORT=8000

# Optional optimizations
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
WORKERS=2
MAX_CONNECTIONS=100

# User API Key Management
# Note: Your default API key serves as fallback
# Users can provide their own keys for unlimited quota
ALLOW_USER_API_KEYS=true
```

### Docker Production Optimizations:

Create `Dockerfile.production`:

```dockerfile
# Multi-stage build for production
FROM node:18-alpine AS frontend
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --only=production
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim AS backend
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m spacy download en_core_web_sm

# Copy application
COPY backend/ ./
COPY --from=frontend /app/build ./static

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
USER app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

---

## 💰 Cost Breakdown (Monthly)

### Railway (Recommended)
- **App hosting:** $5 credits (free)
- **Database:** Neon free tier
- **Redis:** Upstash free tier
- **Total:** $0/month

### Render
- **First 90 days:** Completely free
- **After 90 days:** ~$14/month (database + redis)
- **Web service:** Free (with sleep)

### Fly.io
- **Completely free** within limits
- **3 VMs × 256MB:** Sufficient for small apps
- **PostgreSQL & Redis:** Included

---

## 🚀 Quick Start Recommendation

**For immediate deployment, I recommend Railway:**

1. **Sign up:** [railway.app](https://railway.app)
2. **Connect GitHub:** Your YouTube project repo
3. **Add environment variables**
4. **Deploy in 1 click**
5. **Get free `.railway.app` domain**

**Total setup time:** 15-20 minutes
**Cost:** $0/month (within free credits)

Your app will be live at: `https://your-app-name.railway.app`

---

## 📞 Support & Troubleshooting

### Common Issues:
1. **Build failures:** Check Dockerfile syntax
2. **Database connection:** Verify connection strings
3. **Environment variables:** Ensure all required vars are set
4. **YouTube API quota:** Monitor usage in Google Console

### Getting Help:
- **Railway:** Discord community
- **Render:** Documentation + support tickets
- **Fly.io:** Community forum

---

**Next Steps:** Choose your preferred platform and follow the specific deployment guide above! 🚀