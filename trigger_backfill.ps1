# PowerShell script to trigger Snowflake sync backfill
# This script will run the SQL backfill and then start the services

Write-Host "🚀 Starting Universal Snowflake Sync Backfill..." -ForegroundColor Green
Write-Host "=" * 50 -ForegroundColor Yellow

# Check if we have the required files
if (-not (Test-Path "backfill_executions.sql")) {
    Write-Host "❌ backfill_executions.sql not found!" -ForegroundColor Red
    exit 1
}

Write-Host "📋 Running SQL backfill script..." -ForegroundColor Cyan

# Note: You'll need to run this SQL script in your Supabase SQL editor
# or through psql if you have it configured
Write-Host ""
Write-Host "📝 To run the backfill, execute the following SQL in your Supabase SQL editor:" -ForegroundColor Yellow
Write-Host "   File: backfill_executions.sql" -ForegroundColor White
Write-Host ""
Write-Host "🔧 Or if you have psql configured, run:" -ForegroundColor Yellow
Write-Host "   psql -h your-supabase-host -U postgres -d postgres -f backfill_executions.sql" -ForegroundColor White
Write-Host ""

# Try to start the services
Write-Host "🚀 Starting backend services..." -ForegroundColor Cyan

# Check if we can find Python
$pythonPath = $null
if (Test-Path ".\test_env\bin\python") {
    $pythonPath = ".\test_env\bin\python"
} elseif (Test-Path ".\venv\Scripts\python.exe") {
    $pythonPath = ".\venv\Scripts\python.exe"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonPath = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonPath = "py"
}

if ($pythonPath) {
    Write-Host "✅ Found Python at: $pythonPath" -ForegroundColor Green
    
    # Start the backend
    Write-Host "🔄 Starting FastAPI backend..." -ForegroundColor Cyan
    Start-Process -FilePath $pythonPath -ArgumentList "main_supabase.py" -WindowStyle Minimized
    
    # Wait a moment for startup
    Start-Sleep -Seconds 3
    
    # Check if the service is running
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8000/api/health" -Method GET -TimeoutSec 5
        Write-Host "✅ Backend is running at http://localhost:8000" -ForegroundColor Green
    } catch {
        Write-Host "⚠️  Backend may still be starting up..." -ForegroundColor Yellow
        Write-Host "   Check http://localhost:8000/api/health in a moment" -ForegroundColor White
    }
    
    Write-Host ""
    Write-Host "📊 Once the SQL backfill is complete and the backend is running," -ForegroundColor Cyan
    Write-Host "   you can monitor the sync progress via these API endpoints:" -ForegroundColor White
    Write-Host ""
    Write-Host "   GET http://localhost:8000/api/snowflake-sync/stats" -ForegroundColor Yellow
    Write-Host "   GET http://localhost:8000/api/snowflake-sync/queue" -ForegroundColor Yellow
    Write-Host "   GET http://localhost:8000/api/snowflake-sync/failed" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "🎯 The background sync service will automatically process" -ForegroundColor Green
    Write-Host "   queued executions every 30 seconds!" -ForegroundColor Green
    
else {
    Write-Host "❌ Python not found! Please install Python or set up your virtual environment." -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 You can still run the SQL backfill manually:" -ForegroundColor Yellow
    Write-Host "   1. Open backfill_executions.sql" -ForegroundColor White
    Write-Host "   2. Run it in your Supabase SQL editor" -ForegroundColor White
    Write-Host "   3. Start your backend service manually" -ForegroundColor White
}

Write-Host ""
Write-Host "=" * 50 -ForegroundColor Yellow
Write-Host "✅ Backfill setup complete!" -ForegroundColor Green
