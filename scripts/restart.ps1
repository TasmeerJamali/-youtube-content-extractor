# Restart all services (Windows PowerShell)

param(
    [string]$Environment = "dev"
)

Write-Host "🔄 Restarting YouTube Content Extractor services..." -ForegroundColor Yellow

if ($Environment -eq "prod") {
    Write-Host "Restarting production environment..." -ForegroundColor Yellow
    docker-compose restart
} else {
    Write-Host "Restarting development environment..." -ForegroundColor Yellow
    docker-compose -f docker-compose.dev.yml restart
}

Write-Host "✅ Services restarted!" -ForegroundColor Green
Write-Host "📊 Service status:" -ForegroundColor Cyan

if ($Environment -eq "prod") {
    docker-compose ps
} else {
    docker-compose -f docker-compose.dev.yml ps
}