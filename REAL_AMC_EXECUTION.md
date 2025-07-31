# Real AMC Execution Guide

## Overview

The system now supports REAL Amazon Marketing Cloud query execution in addition to simulated results. All the necessary components are already implemented:

- ✅ **Amazon OAuth Token Management** (`token_service.py`)
- ✅ **AMC API Client** (`api_client.py`) 
- ✅ **Workflow Execution Service** (`workflow_service.py`)
- ✅ **Entity ID Management** (stored in `amc_accounts` table)

## Enabling Real AMC Execution

### 1. Set Environment Variable

```bash
export AMC_USE_REAL_API=true
```

Or add to your `.env` file:
```
AMC_USE_REAL_API=true
```

### 2. Ensure User Has Valid Amazon Token

Users must authenticate with Amazon (not just local login):

```python
# Check if user has valid Amazon token
from amc_manager.services.token_service import token_service

token = await token_service.get_valid_token(user_id)
if not token:
    # User needs to re-authenticate with Amazon
```

### 3. Execute Workflows

Once enabled, workflow execution will:
1. Get user's Amazon OAuth token (auto-refresh if needed)
2. Look up entity ID for the AMC instance
3. Create execution via AMC API
4. Poll for status updates
5. Retrieve and store results

## How It Works

### Token Flow
1. User authenticates with Amazon OAuth
2. Tokens are encrypted and stored in database
3. `token_service` automatically refreshes expired tokens
4. Valid token is passed to AMC API calls

### Execution Flow
1. `execute_workflow()` is called
2. System checks `AMC_USE_REAL_API` flag
3. If true, calls `_execute_real_amc_query()`:
   - Gets valid Amazon token
   - Looks up entity ID from instance
   - Makes AMC API call to create execution
   - Polls for completion
   - Retrieves and stores results
4. If false, uses `_simulate_amc_execution()` for testing

### API Endpoints Used
- `POST /amc/instances/{instance_id}/workflows/{workflow_id}/executions` - Create execution
- `GET /amc/instances/{instance_id}/executions/{execution_id}/status` - Check status
- `GET /amc/instances/{instance_id}/executions/{execution_id}/results` - Get results

## Requirements

### 1. Valid Amazon OAuth Tokens
Users must have authenticated with Amazon and have valid tokens stored.

### 2. AMC Instance Access
User must have permission to execute queries on the AMC instance.

### 3. Proper Entity ID
Each AMC instance must have the correct entity ID in the database.

## Testing

### 1. Test with Simulation First
```bash
# Default mode - uses simulation
python main_supabase.py
```

### 2. Test Token Validity
```python
# Check if tokens work
python scripts/validate_tokens.py
```

### 3. Enable Real Execution
```bash
export AMC_USE_REAL_API=true
python main_supabase.py
```

## Troubleshooting

### "No valid Amazon OAuth token"
- User needs to re-authenticate with Amazon
- Check token expiration in database
- Verify refresh token is still valid

### "AMC instance not found"
- Verify instance_id exists in database
- Check entity_id is set for the AMC account

### "AMC API error"
- Check API response for specific error
- Verify user has permission for the instance
- Check if query syntax is valid for AMC

### Rate Limiting
- AMC API has rate limits
- System includes retry logic with exponential backoff
- Check `api_client.py` for rate limit handling

## Configuration

### Environment Variables
- `AMC_USE_REAL_API` - Enable real execution (default: false)
- `AMAZON_CLIENT_ID` - Amazon app client ID
- `AMAZON_CLIENT_SECRET` - Amazon app client secret
- `ENCRYPTION_KEY` - For token encryption

### Database Requirements
- `auth_tokens` stored in user records
- `entity_id` stored in `amc_accounts` table
- `instance_id` linked to accounts

## Security

- Tokens are encrypted using Fernet encryption
- Tokens are never logged or exposed
- Automatic token refresh prevents expired token usage
- Service role used for database operations

## Next Steps

1. **Production Deployment**
   - Set `AMC_USE_REAL_API=true` in production
   - Monitor execution logs
   - Set up error alerting

2. **S3 Integration** (if needed)
   - AMC can output to S3
   - Add S3 download functionality
   - Parse large result sets

3. **Performance Optimization**
   - Cache frequently used queries
   - Implement result pagination
   - Add query cost estimation