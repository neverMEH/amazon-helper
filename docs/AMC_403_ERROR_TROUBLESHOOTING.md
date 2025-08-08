# AMC API 403 Unauthorized Error Troubleshooting Guide

## Overview
The 403 Unauthorized error when calling AMC API endpoints typically indicates an authentication or authorization issue. This guide provides specific solutions for fixing these errors, particularly when listing workflow executions.

## Root Causes and Solutions

### 1. Wrong Entity ID (Most Common)

**Problem**: Using the wrong entity ID in the `Amazon-Advertising-API-AdvertiserId` header.

**Diagnosis**:
```python
# Check what entity ID is being used
logger.info(f"Entity ID being used: {entity_id}")
logger.info(f"Instance ID: {instance_id}")

# The entity ID MUST come from the AMC instance's associated account
# NOT from a user profile or other source
```

**Solution**:
```python
# CORRECT: Get entity ID from the AMC instance's account
instance = get_instance_with_account(instance_id)
entity_id = instance['amc_accounts']['account_id']

# WRONG: Using profile_id or other IDs
entity_id = user_profile_id  # This will cause 403!
```

### 2. Token Permission Issues

**Problem**: The OAuth token doesn't have permissions for the entity ID being used.

**Diagnosis**:
- Check if the token was generated with the correct scopes
- Verify the token hasn't expired
- Ensure the token is associated with the correct advertiser account

**Solution**:
```python
# Verify token is valid and has correct scopes
from amc_manager.services.token_service import TokenService

token_service = TokenService()
decrypted_tokens = token_service.decrypt_tokens(user.auth_tokens)

# Check token expiration
if is_token_expired(decrypted_tokens):
    # Refresh the token
    new_tokens = refresh_oauth_tokens(decrypted_tokens['refresh_token'])
```

### 3. Instance Access Permissions

**Problem**: The entity ID doesn't have access to the AMC instance.

**Diagnosis**:
- Verify the entity ID is associated with the AMC instance
- Check if the instance is active and accessible

**Solution**:
```sql
-- Check instance-account association
SELECT 
    i.instance_id,
    i.name as instance_name,
    a.account_id as entity_id,
    a.account_name
FROM amc_instances i
JOIN amc_accounts a ON i.account_id = a.id
WHERE i.instance_id = 'your-instance-id';
```

### 4. Missing or Incorrect Headers

**Problem**: Required headers are missing or incorrectly formatted.

**Correct Header Format**:
```python
headers = {
    'Amazon-Advertising-API-ClientId': CLIENT_ID,       # Required
    'Authorization': f'Bearer {access_token}',          # Note: "Bearer " prefix
    'Amazon-Advertising-API-MarketplaceId': marketplace_id,  # Required
    'Amazon-Advertising-API-AdvertiserId': entity_id    # Must be correct entity ID!
}
```

**Common Mistakes**:
- Missing "Bearer " prefix in Authorization header
- Using wrong case for header names
- Missing one of the required headers
- Using profile_id instead of entity_id

## Step-by-Step Debugging Process

### 1. Verify Entity ID

```python
# Get the correct entity ID from the instance
def get_correct_entity_id(instance_id):
    client = SupabaseManager.get_client(use_service_role=True)
    
    response = client.table('amc_instances')\
        .select('*, amc_accounts(*)')\
        .eq('instance_id', instance_id)\
        .execute()
    
    if response.data:
        instance = response.data[0]
        entity_id = instance['amc_accounts']['account_id']
        logger.info(f"Correct entity ID for {instance_id}: {entity_id}")
        return entity_id
    return None
```

### 2. Test with Correct Headers

```python
# Test API call with correct headers
def test_amc_api_call(instance_id, access_token):
    # Get correct entity ID
    entity_id = get_correct_entity_id(instance_id)
    
    # Configure headers correctly
    headers = {
        'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-MarketplaceId': 'ATVPDKIKX0DER',
        'Amazon-Advertising-API-AdvertiserId': entity_id  # Correct entity ID
    }
    
    # Make API call
    url = f"https://advertising-api.amazon.com/amc/reporting/{instance_id}/workflowExecutions"
    
    response = requests.get(url, headers=headers, params={
        'minCreationTime': '2025-01-01T00:00:00'
    })
    
    return response
```

### 3. Validate Token

```python
def validate_oauth_token(access_token):
    """Check if token is valid by making a simple API call"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Amazon-Advertising-API-ClientId': settings.amazon_client_id
    }
    
    # Try a simple API call
    response = requests.get(
        'https://advertising-api.amazon.com/v2/profiles',
        headers=headers
    )
    
    if response.status_code == 401:
        logger.error("Token is expired or invalid")
        return False
    elif response.status_code == 200:
        logger.info("Token is valid")
        return True
    else:
        logger.warning(f"Unexpected status: {response.status_code}")
        return False
```

## Testing the Fix

Use the provided test script:

```bash
# Test with correct entity ID retrieval
python scripts/test_amc_403_fix.py --user-id YOUR_USER_ID --instance-id amchnfozgta

# Verify header format only
python scripts/test_amc_403_fix.py --verify-only
```

## Code Changes Required

### 1. Fix AMCAPIClient in core/api_client.py

Change from using `profile_id` to `entity_id`:

```python
# Before (WRONG):
def __init__(self, profile_id: str, marketplace_id: str):
    self.profile_id = profile_id
    # ...
    'Amazon-Advertising-API-AdvertiserId': self.profile_id

# After (CORRECT):
def __init__(self, entity_id: str, marketplace_id: str):
    self.entity_id = entity_id
    # ...
    'Amazon-Advertising-API-AdvertiserId': self.entity_id
```

### 2. Update API Endpoints to Get Entity ID from Instance

Always retrieve the entity ID from the AMC instance's associated account:

```python
# In your API endpoint
instance = get_instance_with_account(instance_id)
entity_id = instance['amc_accounts']['account_id']

# Use this entity_id for all AMC API calls
api_client.list_executions(
    instance_id=instance_id,
    entity_id=entity_id,  # From instance's account
    # ...
)
```

## Prevention

1. **Always use the AMCAPIClient from services/amc_api_client.py** which correctly retrieves entity ID from the instance
2. **Never use profile_id as entity_id** - they are different concepts
3. **Log all API calls** with headers (excluding tokens) for debugging
4. **Implement proper error handling** to catch and diagnose 403 errors early

## Quick Checklist

When you get a 403 error:

- [ ] Entity ID matches the instance's associated account?
- [ ] Token is valid and not expired?
- [ ] All 4 required headers are present?
- [ ] "Bearer " prefix in Authorization header?
- [ ] Instance is active and accessible?
- [ ] Token has correct scopes?
- [ ] Using correct marketplace ID?

## Related Error Codes

- **401**: Token expired or invalid
- **403**: Authorization issue (wrong entity ID, no access)
- **404**: Instance or execution not found
- **429**: Rate limit exceeded

## Support

If the issue persists after following this guide:

1. Check AMC API logs for detailed error messages
2. Verify instance configuration in Supabase
3. Test with a known-good instance (sandbox)
4. Check if the issue is account-specific or system-wide