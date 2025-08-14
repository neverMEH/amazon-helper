# Amazon OAuth Token Auto-Refresh Implementation

## Overview

This document describes the automatic token refresh system implemented for the Amazon Advertising API integration. The system ensures users don't have to manually re-authenticate every time their Amazon OAuth tokens expire.

## Components

### 1. Backend Token Service (`amc_manager/services/token_service.py`)

The core service responsible for token management:

- **Token Encryption**: Uses Fernet encryption to securely store tokens in the database
- **Token Validation**: Checks if tokens are expired or about to expire
- **Token Refresh**: Automatically refreshes expired tokens using refresh tokens
- **Error Handling**: Clears invalid tokens if decryption fails (e.g., when encryption key changes)

Key Methods:
- `get_valid_token(user_id)`: Returns a valid access token, refreshing if necessary
- `refresh_access_token(refresh_token)`: Refreshes an expired access token
- `store_user_tokens(user_id, token_data)`: Stores encrypted tokens in the database

### 2. Token Refresh Service (`amc_manager/services/token_refresh_service.py`)

Background service that proactively refreshes tokens:

- **Periodic Refresh**: Runs every 10 minutes to check token expiry
- **Buffer Time**: Refreshes tokens 15 minutes before they expire
- **User Tracking**: Maintains a list of users with active tokens
- **Automatic Cleanup**: Removes users with invalid tokens from tracking

Key Features:
- Starts automatically when the application starts
- Tracks all users with OAuth tokens
- Refreshes tokens in parallel for efficiency
- Handles errors gracefully without stopping the service

### 3. AMC API Client with Retry (`amc_manager/services/amc_api_client_with_retry.py`)

Enhanced API client that handles authentication failures:

- **Automatic Retry**: Retries API calls with refreshed tokens on 401 errors
- **Token Refresh**: Forces token refresh on authentication failures
- **Max Retries**: Configurable retry limit (default: 2)
- **User Context**: Maintains user context for token refresh

Key Features:
- Wraps all AMC API calls with retry logic
- Transparently handles token expiry
- Returns clear error messages when authentication fails

### 4. Frontend Token Refresh (`frontend/src/services/api.ts`)

Frontend interceptor that handles token refresh:

- **Request Interceptor**: Adds Bearer token to all requests
- **Response Interceptor**: Handles 401 errors with token refresh
- **Queue Management**: Queues requests while token is being refreshed
- **Automatic Retry**: Retries original request with new token

Key Features:
- Prevents multiple simultaneous refresh attempts
- Queues requests during refresh
- Automatic logout if refresh fails
- Seamless user experience

### 5. API Endpoints

#### `/api/auth/refresh` (POST)
Refreshes both JWT and Amazon OAuth tokens:
- Creates new JWT access token
- Attempts to refresh Amazon OAuth tokens if expired
- Returns status of both refreshes

#### `/api/auth/token-status` (GET)
Checks current token status:
- Returns whether user has valid Amazon OAuth tokens
- Provides appropriate error messages
- Helps frontend determine if re-authentication is needed

## How It Works

### Initial Authentication Flow

1. User logs in with Amazon OAuth
2. Backend receives OAuth tokens (access_token, refresh_token)
3. Tokens are encrypted using Fernet encryption
4. Encrypted tokens are stored in the database
5. User is added to token refresh tracking

### Automatic Refresh Flow

1. **Background Service**: Runs every 10 minutes
   - Checks all tracked users
   - Identifies tokens expiring within 15 minutes
   - Refreshes tokens using refresh_token
   - Updates database with new tokens

2. **On-Demand Refresh**: When API call is made
   - `get_valid_token()` checks token expiry
   - If expired, uses refresh_token to get new access_token
   - Returns fresh token for API call

3. **API Call Retry**: When 401 error occurs
   - AMC API client detects 401 error
   - Forces token refresh
   - Retries API call with new token
   - Max 2 retry attempts

### Frontend Handling

1. **Request Flow**:
   - All API requests include Bearer token
   - Token is retrieved from localStorage

2. **401 Error Handling**:
   - Interceptor catches 401 errors
   - Calls `/api/auth/refresh` endpoint
   - Updates localStorage with new token
   - Retries original request

3. **Queue Management**:
   - Multiple simultaneous 401s are queued
   - Single refresh attempt for all queued requests
   - All queued requests retry with new token

## Configuration

### Environment Variables

```bash
# Token encryption key (auto-generated if not set)
FERNET_KEY=your_fernet_key_here

# Amazon OAuth credentials
AMAZON_CLIENT_ID=your_client_id
AMAZON_CLIENT_SECRET=your_client_secret
```

### Service Configuration

```python
# Token refresh intervals
refresh_interval = 600  # Check every 10 minutes
refresh_buffer = 900    # Refresh 15 minutes before expiry

# Retry configuration
max_retries = 2  # Maximum retry attempts on 401
```

## Error Handling

### Token Decryption Errors

When the encryption key changes:
1. Decryption fails with clear error message
2. Invalid tokens are automatically cleared
3. User is removed from refresh tracking
4. User must re-authenticate

### Refresh Token Expiry

When refresh token is invalid:
1. Refresh attempt fails
2. User is removed from tracking
3. Frontend receives 401 error
4. User is redirected to login

### Network Errors

When API is unreachable:
1. Retry with exponential backoff
2. Return error after max retries
3. Preserve user session
4. Allow manual retry

## Testing

### Manual Testing

1. **Test Token Refresh**:
   ```bash
   python test_token_refresh.py
   ```

2. **Verify Background Service**:
   - Check logs for "Token refresh service started"
   - Monitor refresh attempts every 10 minutes
   - Verify successful refreshes in logs

3. **Test API Retry**:
   - Make API call with expired token
   - Verify automatic refresh and retry
   - Check for successful response

### Common Issues

1. **"Failed to decrypt token" Error**:
   - Cause: FERNET_KEY changed
   - Solution: User must re-authenticate
   - Prevention: Keep FERNET_KEY consistent

2. **"Token refresh failed" Error**:
   - Cause: Refresh token expired
   - Solution: User must re-authenticate
   - Prevention: Regular token refresh

3. **Multiple 401 Errors**:
   - Cause: Token expired during multiple requests
   - Solution: Queue management handles this
   - Prevention: Proactive background refresh

## Benefits

1. **Improved User Experience**:
   - No manual re-authentication needed
   - Seamless token refresh
   - Uninterrupted workflow

2. **Security**:
   - Tokens encrypted at rest
   - Automatic cleanup of invalid tokens
   - Limited retry attempts

3. **Reliability**:
   - Background refresh prevents expiry
   - Automatic retry on failures
   - Graceful error handling

4. **Performance**:
   - Parallel token refresh for multiple users
   - Request queuing prevents duplicate refreshes
   - Efficient retry logic

## Monitoring

### Key Metrics to Track

1. **Token Refresh Success Rate**:
   - Monitor successful vs failed refreshes
   - Alert on high failure rates

2. **Token Expiry Events**:
   - Track how often tokens expire
   - Optimize refresh intervals

3. **API Retry Rate**:
   - Monitor 401 errors and retries
   - Identify authentication issues

### Log Messages

Important log messages to monitor:

```
INFO - Token refresh service started
INFO - Refreshing tokens for X users
INFO - Successfully refreshed token for user Y
WARNING - Token for user Z expires in X seconds, refreshing...
ERROR - Failed to refresh token for user W
```

## Future Enhancements

1. **Token Refresh Webhooks**:
   - Notify users of refresh failures
   - Alert on upcoming expiry

2. **Token Analytics**:
   - Track token usage patterns
   - Optimize refresh intervals

3. **Multi-Provider Support**:
   - Support multiple OAuth providers
   - Unified token management

4. **Token Rotation**:
   - Periodic token rotation for security
   - Automatic key management

## Conclusion

The automatic token refresh system provides a robust, secure, and user-friendly solution for managing Amazon OAuth tokens. It ensures uninterrupted access to AMC APIs while maintaining security best practices.