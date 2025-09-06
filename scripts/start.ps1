# Start all services (Windows PowerShell)

param(
    [string]$Environment = "dev"
)

Write-Host "🚀 Starting YouTube Content Extractor services..." -ForegroundColor Green

if ($Environment -eq "prod") {
    Write-Host "Starting production environment..." -ForegroundColor Yellow
    docker-compose up -d
} else {
    Write-Host "Starting development environment..." -ForegroundColor Yellow
    docker-compose -f docker-compose.dev.yml up -d
}

Write-Host "✅ Services started!" -ForegroundColor Green
Write-Host "📊 Service status:" -ForegroundColor Cyan

if ($Environment -eq "prod") {
    docker-compose ps
} else {
    docker-compose -f docker-compose.dev.yml ps
}