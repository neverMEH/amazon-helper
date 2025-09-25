# Snowflake Configuration Fix Script
# This script will update your Snowflake configuration with the correct credentials

Write-Host "Snowflake Configuration Fix" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green
Write-Host ""

# Your Snowflake credentials from the config file
$snowflakeConfig = @{
    account_identifier = "MUMZYBN-CN28961"
    warehouse = "AMC_WH"
    database = "AMC_DB"
    schema = "PUBLIC"
    role = "AMC_DB_OWNER_ROLE"
    username = "NICK_PADILLA"
    password = "6O[B%Vke@>6xB8IYcBCG"
}

Write-Host "Updating Snowflake configuration with:" -ForegroundColor Yellow
Write-Host "Account: $($snowflakeConfig.account_identifier)"
Write-Host "Warehouse: $($snowflakeConfig.warehouse)"
Write-Host "Database: $($snowflakeConfig.database)"
Write-Host "Schema: $($snowflakeConfig.schema)"
Write-Host "Role: $($snowflakeConfig.role)"
Write-Host "Username: $($snowflakeConfig.username)"
Write-Host ""

# Convert to JSON
$jsonBody = $snowflakeConfig | ConvertTo-Json

Write-Host "Attempting to update Snowflake configuration..." -ForegroundColor Yellow

try {
    # First, try to get existing configurations
    Write-Host "Checking existing Snowflake configurations..." -ForegroundColor Cyan
    $getResponse = Invoke-RestMethod -Uri "http://localhost:8001/api/snowflake/config" -Method GET -ContentType "application/json"
    
    if ($getResponse) {
        Write-Host "Found existing configuration, updating..." -ForegroundColor Green
        
        # Update existing configuration
        $updateResponse = Invoke-RestMethod -Uri "http://localhost:8001/api/snowflake/config" -Method PUT -Body $jsonBody -ContentType "application/json"
        
        if ($updateResponse) {
            Write-Host "✅ Snowflake configuration updated successfully!" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to update Snowflake configuration" -ForegroundColor Red
        }
    } else {
        Write-Host "No existing configuration found, creating new one..." -ForegroundColor Yellow
        
        # Create new configuration
        $createResponse = Invoke-RestMethod -Uri "http://localhost:8001/api/snowflake/config" -Method POST -Body $jsonBody -ContentType "application/json"
        
        if ($createResponse) {
            Write-Host "✅ Snowflake configuration created successfully!" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to create Snowflake configuration" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "Testing Snowflake connection..." -ForegroundColor Cyan
    
    # Test the connection
    $testResponse = Invoke-RestMethod -Uri "http://localhost:8001/api/snowflake/test-connection" -Method POST -ContentType "application/json"
    
    if ($testResponse.success) {
        Write-Host "✅ Snowflake connection test successful!" -ForegroundColor Green
        Write-Host "Connection details: $($testResponse.details)" -ForegroundColor Green
    } else {
        Write-Host "❌ Snowflake connection test failed: $($testResponse.error)" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "This might be because:" -ForegroundColor Yellow
    Write-Host "1. The API server is not running (start with ./start_services.sh)" -ForegroundColor Yellow
    Write-Host "2. The Snowflake API endpoints are not available" -ForegroundColor Yellow
    Write-Host "3. There's an authentication issue" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Verify the Snowflake configuration in the application settings" -ForegroundColor White
Write-Host "2. Try running a new report with Snowflake enabled" -ForegroundColor White
Write-Host "3. Check the execution details for Snowflake status" -ForegroundColor White
Write-Host "4. If still having issues, check the server logs for Snowflake errors" -ForegroundColor White
