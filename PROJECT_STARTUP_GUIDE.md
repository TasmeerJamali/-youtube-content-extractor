# YouTube Content Extractor - Project Startup Guide

This guide provides step-by-step instructions for starting the YouTube Content Extractor project after shutting down or restarting your PC.

## Prerequisites

Before starting the project, ensure you have the following installed:
- **Docker Desktop** (required for containerized services)
- **Node.js 16+** (for frontend development)
- **PowerShell** (for running scripts)

## Step-by-Step Startup Process

### 1. Start Docker Desktop

1. **Open Docker Desktop**
   - Click on the Docker Desktop icon in your taskbar or Start menu
   - Wait for Docker Desktop to fully start (the Docker icon in the system tray should show "Docker Desktop is running")
   - Ensure Docker Engine is running and ready

### 2. Navigate to Project Directory

Open PowerShell and navigate to your project directory:

```powershell
cd "c:\Users\Tasmeer Jamali\OneDrive\Desktop\Youtube"
```

### 3. Start Docker Services

Start the essential backend services (PostgreSQL, Redis, Backend API):

```powershell
docker-compose up -d
```

**What this command does:**
- Starts PostgreSQL database container
- Starts Redis cache container
- Starts Backend API container (FastAPI)
- Runs all containers in detached mode (background)

**Expected output:**
```
Creating network "youtube_default" with the default driver
Creating youtube_postgres_1 ... done
Creating youtube_redis_1    ... done
Creating youtube_backend_1  ... done
```

### 4. Verify Docker Containers

Check that all containers are running properly:

```powershell
docker-compose ps
```

**Expected output:**
All services should show "Up" status:
```
Name                    Command               State           Ports
------------------------------------------------------------------------
youtube_backend_1      uvicorn app.main:app --host ...   Up      0.0.0.0:8001->8000/tcp
youtube_postgres_1     docker-entrypoint.sh postgres    Up      0.0.0.0:5432->5432/tcp
youtube_redis_1        docker-entrypoint.sh redis ...   Up      0.0.0.0:6379->6379/tcp
```

### 5. Start Frontend Development Server

Open a **NEW PowerShell window** (keep the first one open) and run:

```powershell
# Navigate to frontend directory
cd "c:\Users\Tasmeer Jamali\OneDrive\Desktop\Youtube\frontend"

# Start React development server
npm start
```

**What this command does:**
- Starts React TypeScript development server
- Enables hot reload for frontend changes
- Serves frontend on http://localhost:3000

**Expected output:**
```
Compiled successfully!

You can now view the app in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

### 6. Verify Application Access

Once both services are running, verify access to:

#### Frontend Application
- **URL:** http://localhost:3000
- **Features:** Search interface, video results, transcript functionality

#### Backend API Documentation
- **URL:** http://localhost:8001/docs
- **Features:** Interactive API documentation (Swagger UI)

#### Backend API Health Check
- **URL:** http://localhost:8001/health
- **Expected response:** `{"status": "healthy"}`

## Alternative Startup Methods

### Using PowerShell Scripts (If Available)

If you have PowerShell scripts in the `scripts/` directory:

```powershell
# Navigate to project root
cd "c:\Users\Tasmeer Jamali\OneDrive\Desktop\Youtube"

# Run restart script
.\scripts\restart.ps1
```

### Manual Docker Commands

If you prefer individual container management:

```powershell
# Start specific services
docker-compose up -d postgres redis backend

# Check logs for specific service
docker-compose logs backend

# Restart specific service
docker-compose restart backend
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Docker Desktop Not Running
**Error:** `Cannot connect to the Docker daemon`
**Solution:** 
- Start Docker Desktop application
- Wait for it to fully initialize
- Try the command again

#### 2. Port Already in Use
**Error:** `Port 3000 is already in use`
**Solution:**
```powershell
# Set different port for frontend
$env:PORT=3001
npm start
```

#### 3. Docker Containers Not Starting
**Error:** Container creation issues
**Solution:**
```powershell
# Clean up containers and restart
docker-compose down
docker-compose up -d --build
```

#### 4. Node Modules Issues
**Error:** Module not found errors
**Solution:**
```powershell
cd frontend
npm install
npm start
```

#### 5. Backend API Not Responding
**Solution:**
```powershell
# Check backend logs
docker-compose logs backend

# Restart backend service
docker-compose restart backend
```

## Environment Configuration

### Required Environment Variables

Ensure your `.env` file in the project root contains:

```env
# YouTube API Configuration
YOUTUBE_API_KEY=AIzaSyCgV-_Z7Bku4A5khNoP0bzSH4XnArOsIko

# Database Configuration
DATABASE_URL=postgresql://youtube_user:youtube_pass@localhost:5432/youtube_db

# Redis Configuration  
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

## Project Structure Overview

```
Youtube/
├── .env                    # Environment variables
├── docker-compose.yml     # Docker services configuration
├── backend/               # Python FastAPI backend
│   ├── app/              # Application code
│   └── Dockerfile        # Backend container config
├── frontend/             # React TypeScript frontend
│   ├── src/              # Source code
│   ├── package.json      # Dependencies
│   └── Dockerfile        # Frontend container config
├── database/             # Database schema
└── scripts/              # PowerShell automation scripts
```

## Service Architecture

### Running Services After Startup:

1. **PostgreSQL Database** (Port 5432)
   - Stores application data
   - Accessible via Docker network

2. **Redis Cache** (Port 6379)
   - Caches YouTube API responses
   - Improves performance

3. **Backend API** (Port 8001)
   - FastAPI application
   - Handles YouTube API integration
   - Provides REST endpoints

4. **Frontend Development Server** (Port 3000)
   - React TypeScript application
   - Hot reload enabled
   - Connects to backend API

## Performance Notes

- **Startup Time:** ~2-3 minutes for full stack
- **Docker Container Memory:** ~1-2GB total
- **Frontend Hot Reload:** Changes reflect instantly
- **API Response Time:** < 2 seconds for most queries

## Shutdown Process

To properly shut down the project:

```powershell
# Stop frontend (Ctrl+C in frontend terminal)
# Stop Docker services
docker-compose down
```

## Support

If you encounter issues:
1. Check Docker Desktop status
2. Verify all ports are available
3. Review container logs: `docker-compose logs [service-name]`
4. Restart individual services: `docker-compose restart [service-name]`

---

**Last Updated:** $(Get-Date -Format "yyyy-MM-dd")
**Project:** YouTube Content Extractor
**Environment:** Windows 24H2 with PowerShell