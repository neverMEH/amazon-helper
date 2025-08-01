# Amazon OAuth Fix Summary

## Problem
Users were getting "No valid Amazon OAuth token. Please re-authenticate with Amazon." error when trying to execute workflows because:

1. The application was using a simplified authentication system that didn't integrate with Amazon OAuth
2. No Amazon OAuth tokens were being stored when users logged in
3. The workflow execution service expected real Amazon OAuth tokens but found none

## Solution Implemented

### 1. Created Amazon OAuth Endpoints (`/root/amazon-helper/amc_manager/api/supabase/amazon_auth.py`)
- `GET /api/auth/amazon/login` - Initiates Amazon OAuth flow
- `GET /api/auth/amazon/callback` - Handles OAuth callback and stores tokens
- `POST /api/auth/amazon/refresh` - Refreshes expired tokens
- `GET /api/auth/amazon/status` - Checks if user has valid tokens

### 2. Updated Token Storage
- Tokens are encrypted using Fernet encryption before storage
- Tokens are stored in the user's `auth_tokens` field in Supabase
- Automatic token refresh when access token expires

### 3. Added Frontend Components
- `AmazonAuthStatus.tsx` - Shows OAuth status and connect button
- `AuthCallback.tsx` - Handles OAuth redirect from Amazon
- Added routes for `/auth/success` and `/auth/error`

### 4. Integration Points
- Added Amazon OAuth router to main_supabase.py
- Updated frontend to show auth status on workflows page
- Created useAuth hook for managing authentication state

## How to Use

### 1. Configure Amazon OAuth App
Create an OAuth app in Amazon Advertising Console with:
- Redirect URI: `http://localhost:8001/api/auth/amazon/callback`
- Scopes: `advertising::campaign_management`

### 2. Set Environment Variables
```bash
AMAZON_CLIENT_ID=your_client_id
AMAZON_CLIENT_SECRET=your_client_secret
AMAZON_REDIRECT_URI=http://localhost:8001/api/auth/amazon/callback
AMAZON_SCOPE=advertising::campaign_management
ENCRYPTION_KEY=your_encryption_key  # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 3. User Flow
1. User logs in with email (existing flow)
2. On workflows page, they see "Amazon account not connected" warning
3. User clicks "Connect Amazon Account" button
4. Redirected to Amazon OAuth consent page
5. After approval, redirected back to app with tokens stored
6. Can now execute workflows successfully

## Testing
Run `python test_oauth_flow.py` to verify:
- Token encryption/decryption works
- Tokens can be stored and retrieved
- User records are properly updated

## Next Steps
1. Add token refresh scheduling to proactively refresh tokens before expiry
2. Add better error handling for expired refresh tokens
3. Consider adding a user settings page to manage OAuth connections