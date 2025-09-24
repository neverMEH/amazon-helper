# PowerShell script to configure Snowflake credentials
# This script uses the existing API endpoints

Write-Host "Snowflake Configuration Setup" -ForegroundColor Green
Write-Host "=============================" -ForegroundColor Green
Write-Host ""

# Your Snowflake credentials
$snowflakeConfig = @{
    account_identifier = "MUMZYBN-CN28961"
    warehouse = "AMC_WH"
    database = "AMC_DB"
    schema = "PUBLIC"
    role = "AMC_DB_OWNER_ROLE"
    username = "NICK_PADILLA"
    password = ""
}

Write-Host "Your Snowflake credentials:" -ForegroundColor Yellow
Write-Host "Account: $($snowflakeConfig.account_identifier)"
Write-Host "Warehouse: $($snowflakeConfig.warehouse)"
Write-Host "Database: $($snowflakeConfig.database)"
Write-Host "Schema: $($snowflakeConfig.schema)"
Write-Host "Role: $($snowflakeConfig.role)"
Write-Host "Username: $($snowflakeConfig.username)"
Write-Host ""

# Get password from user
$password = Read-Host "Enter your Snowflake password"
$snowflakeConfig.password = $password

# Convert to JSON
$jsonBody = $snowflakeConfig | ConvertTo-Json

Write-Host ""
Write-Host "Testing API connection..." -ForegroundColor Yellow

try {
    # Test if the API is running
    $healthResponse = Invoke-RestMethod -Uri "http://localhost:8001/api/health" -Method GET
    Write-Host "✅ API is running: $($healthResponse.status)" -ForegroundColor Green
    
    # Try to create Snowflake configuration
    Write-Host "Creating Snowflake configuration..." -ForegroundColor Yellow
    
    # Note: This will fail without authentication, but we can see the structure
    try {
        $response = Invoke-RestMethod -Uri "http://localhost:8001/api/snowflake/config" -Method POST -Body $jsonBody -ContentType "application/json"
        Write-Host "✅ Snowflake configuration created successfully!" -ForegroundColor Green
        Write-Host "Configuration ID: $($response.id)" -ForegroundColor Green
    } catch {
        Write-Host "❌ API call failed: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
        Write-Host "This is expected because:" -ForegroundColor Yellow
        Write-Host "1. The Snowflake API router may not be loaded yet" -ForegroundColor Yellow
        Write-Host "2. Authentication is required" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "However, your configuration data is ready:" -ForegroundColor Green
        Write-Host $jsonBody -ForegroundColor Cyan
    }
    
} catch {
    Write-Host "❌ Cannot connect to API: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "Make sure the server is running with:" -ForegroundColor Yellow
    Write-Host "venv\bin\python main_supabase.py" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "1. Fix the API router import issue" -ForegroundColor Yellow
Write-Host "2. Use the Report Builder UI to enable Snowflake storage" -ForegroundColor Yellow
Write-Host "3. Your credentials are ready to use!" -ForegroundColor Yellow
