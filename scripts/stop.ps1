# Stop all services (Windows PowerShell)

param(
    [string]$Environment = "dev"
)

Write-Host "🛑 Stopping YouTube Content Extractor services..." -ForegroundColor Red

if ($Environment -eq "prod") {
    Write-Host "Stopping production environment..." -ForegroundColor Yellow
    docker-compose down
} else {
    Write-Host "Stopping development environment..." -ForegroundColor Yellow
    docker-compose -f docker-compose.dev.yml down
}

Write-Host "✅ Services stopped!" -ForegroundColor Green