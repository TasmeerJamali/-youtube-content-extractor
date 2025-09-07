# YouTube Content Extractor - Restart Guide

## Prerequisites

1. Docker Desktop installed and running
2. YouTube API key configured in `.env` file

## Step-by-Step Restart Process

### 1. Navigate to Project Directory
```powershell
cd "c:\Users\Tasmeer Jamali\OneDrive\Desktop\Youtube"
```

### 2. Clean Up Any Existing Containers (if needed)
```powershell
docker-compose down
docker container prune -f
```

### 3. Start Docker Services
```powershell
docker-compose up -d
```

### 4. Verify Services are Running
```powershell
docker-compose ps
```

All services should show "Up" status:
- youtube-postgres-1 (Database) - Port 5432
- youtube-redis-1 (Cache) - Port 6379
- youtube-backend-1 (API Server) - Port 8001
- youtube-frontend-1 (Web Interface) - Port 3000

### 5. Verify Health Status
```powershell
Invoke-WebRequest -Uri http://localhost:8001/health -Method GET
```

### 6. Access the Application

- **Frontend (Web Interface)**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

### 7. Test the Application

1. Open http://localhost:3000 in your browser
2. Try searching for "Cristiano Ronaldo" or any topic
3. Verify filters work (Content Type, Language, Region)
4. Check that transcripts and comments checkboxes work
5. Test trending page with different regions/categories
6. Explore analytics page features

## Environment Configuration

Ensure `.env` file exists in project root with:
```
YOUTUBE_API_KEY=AIzaSyCgV-_Z7Bku4A5khNoP0bzSH4XnArOsIko
SECRET_KEY=your-secret-key-here
```

## Troubleshooting

### If containers fail to start:

1. **Check for orphaned containers**:
   ```powershell
   docker ps -a
   ```
   
2. **Remove orphaned containers**:
   ```powershell
   docker rm -f youtube-nginx-1 youtube-backend-dev-1  # if they exist
   ```

3. **Clean up and restart**:
   ```powershell
   docker-compose down
   docker container prune -f
   docker-compose up -d
   ```

### If API requests fail:

1. **Check backend logs**:
   ```powershell
   docker-compose logs backend
   ```

2. **Verify YouTube API key**:
   - Ensure `.env` file exists with valid YOUTUBE_API_KEY

3. **Check for quota exceeded errors**:
   - YouTube API has daily quota limits (10,000 units/day)
   - If exceeded, wait until quota resets (midnight PST)
   - Error message: "Quota exceeded. Used: XXXX, Limit: 10000"

4. **Test backend directly**:
   ```powershell
   Invoke-WebRequest -Uri http://localhost:8001/health
   ```

### If frontend shows errors:

1. **Check frontend logs**:
   ```powershell
   docker-compose logs frontend
   ```

2. **Verify API connection**:
   - Backend should respond at http://localhost:8001
   - Check REACT_APP_API_URL environment variable

### Port Conflicts:

If you get "port already allocated" errors:
```powershell
# Find processes using the ports
netstat -ano | findstr :8001
netstat -ano | findstr :3000

# Kill orphaned containers
docker ps -a
docker rm -f <container-name>
```

## Stopping the Application

```powershell
docker-compose down
```

## Project Structure

- `/backend` - FastAPI server with YouTube Data API integration
- `/frontend` - React TypeScript web interface with Tailwind CSS
- `/database` - PostgreSQL schema and migrations
- `docker-compose.yml` - Container orchestration (no nginx)
- `.env` - Environment variables (API keys)

## Features Available

✅ **Search Page**: Advanced YouTube content search with comprehensive filters
✅ **Trending Page**: Regional trending videos with category filtering
✅ **Analytics Page**: Multi-tab analytics with trends, insights, competitors, content gaps
✅ **Video Transcripts**: Automatic transcript extraction using YouTube captions API
✅ **Top Comments**: Comment extraction with error handling
✅ **Advanced Filters**: Content type, language, region, duration, publication date
✅ **Responsive UI**: Mobile-friendly interface with proper checkbox functionality

## Port Configuration

- Frontend: 3000 (React dev server via serve)
- Backend: 8001 (FastAPI mapped from container port 8000)
- PostgreSQL: 5432
- Redis: 6379

## Recent Fixes Applied

- ✅ Removed nginx service to eliminate configuration conflicts
- ✅ Fixed checkbox functionality by removing nested label elements
- ✅ Implemented proper video transcript fetching
- ✅ Enhanced comment extraction with error handling
- ✅ Added comprehensive analytics dashboard
- ✅ Created functional trends page with filtering
- ✅ Cleaned up orphaned containers and port conflicts
- ✅ Fixed duplicate React import causing TypeScript errors
- ✅ Enhanced transcript UI with better "no transcript available" messaging
- ✅ Added API quota limit warnings and tooltips
- ✅ Improved user experience when YouTube API quota is exceeded

---

**Note**: Always ensure Docker Desktop is running before executing docker-compose commands. The application uses Docker containers for consistent deployment across different environments.