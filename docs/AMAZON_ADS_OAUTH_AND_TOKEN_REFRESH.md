## Amazon Advertising OAuth + AMC API: Setup and Token Refresh Guide

This guide explains how this project connects to the Amazon Advertising/AMC APIs, how OAuth tokens are stored and refreshed, and how to set it up for a new app.

### What you get
- **OAuth flow** with Amazon (login, callback, token exchange)
- **Encrypted token storage** and **automatic refresh** with background service
- **AMC API client** usage pattern (headers, marketplace, entity, bearer token)
- **Copy/paste setup steps** to reuse in a new application


## Quick start (local)
1) Set environment variables (create `.env`):

```
AMAZON_CLIENT_ID=amzn1.application-oa2-client.xxxxx
AMAZON_CLIENT_SECRET=your-secret
# Use the exact redirect URL you add in Amazon Developer Console
AMAZON_OAUTH_REDIRECT_URI=http://localhost:8001/api/auth/amazon/callback
AMAZON_SCOPE=advertising::campaign_management

# Supabase (required by this app)
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
SUPABASE_SERVICE_ROLE_KEY=...

# Stable encryption key for token at-rest encryption
FERNET_KEY=your-generated-fernet-key

# App
FRONTEND_URL=http://localhost:5173
ENVIRONMENT=development
```

To generate a Fernet key:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

2) Add the same redirect URL in the Amazon Developer Console for your app:
- Authorization URL domain: `https://www.amazon.com`
- Redirect URL: `http://localhost:8001/api/auth/amazon/callback`

3) Run the API:

```bash
python main_supabase.py
```

4) Start OAuth from the frontend or by hitting:
- `GET /api/auth/amazon/login` → returns `auth_url` to redirect the user to Amazon
- Amazon redirects back to `GET /api/auth/amazon/callback` where tokens are exchanged and stored


## Architecture overview

- **OAuth endpoints**: `amc_manager/api/supabase/amazon_auth.py`
  - Builds the Amazon authorization URL and handles the callback (code → tokens)
  - Persists tokens (encrypted) and issues an app JWT for your frontend
- **Token storage and refresh**: `amc_manager/services/token_service.py`
  - Encrypts tokens with `FERNET_KEY`, validates/refreshes on demand
- **Background token refresher**: `amc_manager/services/token_refresh_service.py`
  - Runs every 10 minutes; refreshes tokens ~15 minutes before expiry
- **Runtime wiring**: `main_supabase.py`
  - Starts the token refresh service on app startup and tracks users with tokens
- **AMC API client**: `amc_manager/services/amc_api_client.py`
  - Sends requests with the correct Amazon headers and bearer token


## OAuth flow details

### 1) Begin login
`GET /api/auth/amazon/login` builds the Amazon authorization URL, saves a CSRF `state`, and returns the URL for the client to redirect the user.

```195:217:amc_manager/api/supabase/amazon_auth.py
@router.get("/login")
async def amazon_login(redirect_uri: Optional[str] = None):
    ...
    params = {
        'client_id': client_id,
        'scope': settings.amazon_scope or 'advertising::campaign_management',
        'response_type': 'code',
        'redirect_uri': callback_url,
        'state': state
    }
    auth_url = f"https://www.amazon.com/ap/oa?{param_string}"
    return {"auth_url": auth_url, "state": state}
```

Notes
- `redirect_uri` must match what you configured in Amazon Developer Console.
- Scope defaults to `advertising::campaign_management`.

### 2) Callback and token exchange
Amazon redirects back to `GET /api/auth/amazon/callback?code=...&state=...` where the code is exchanged for tokens and stored.

```216:317:amc_manager/api/supabase/amazon_auth.py
@router.get("/callback")
async def amazon_callback(code: str = Query(...), state: str = Query(...)):
    token_url = "https://api.amazon.com/auth/o2/token"
    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': settings.amazon_client_id,
        'client_secret': settings.amazon_client_secret,
        'redirect_uri': exchange_redirect_uri
    }
    response = requests.post(token_url, data=token_data, timeout=30)
    tokens = response.json()
    success = await token_service.store_user_tokens(user['id'], tokens)
    token_refresh_service.add_user(user['id'])
    app_token = create_access_token(user['id'], user['email'])
    return RedirectResponse(url=redirect_url)
```

What’s stored
- Access and refresh tokens (encrypted)
- `expires_at` and `updated_at` timestamps


## Token storage and auto-refresh

### Encrypted storage
Tokens are encrypted at rest using Fernet. Keep `FERNET_KEY` stable across deploys.

```148:167:amc_manager/services/token_service.py
encrypted_tokens = {
    'access_token': self.encrypt_token(token_data['access_token']),
    'refresh_token': self.encrypt_token(token_data.get('refresh_token', '')),
    'token_type': token_data.get('token_type', 'bearer'),
    'expires_at': (datetime.utcnow() + timedelta(seconds=token_data.get('expires_in', 3600))).isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}
```

### Getting a valid token (with auto-refresh)
Call `get_valid_token(user_id)` to receive a bearer token. It transparently refreshes when near/after expiry (5-minute buffer), then re-encrypts and stores the new tokens.

```189:247:amc_manager/services/token_service.py
async def get_valid_token(self, user_id: str) -> Optional[str]:
    user = await db_service.get_user_by_id(user_id)
    auth_tokens = user['auth_tokens']
    access_token = self.decrypt_token(auth_tokens['access_token'])
    expires_at = datetime.fromisoformat(auth_tokens.get('expires_at', ''))
    if expires_at > datetime.utcnow() + timedelta(minutes=5):
        return access_token
    refresh_token = self.decrypt_token(auth_tokens['refresh_token'])
    new_token_data = await self.refresh_access_token(refresh_token)
    await self.store_user_tokens(user_id, new_token_data)
    return new_token_data['access_token']
```

### Background refresher
Runs every 10 minutes and refreshes tokens 15 minutes before expiry.

```18:31:amc_manager/services/token_refresh_service.py
class TokenRefreshService:
    def __init__(self):
        self.refresh_interval = 600  # 10 minutes
        self.refresh_buffer = 900    # 15 minutes
        ...
    def add_user(self, user_id: str):
        self._tracked_users.add(user_id)
```

Started at app startup:

```53:61:main_supabase.py
await token_refresh_service.start()
logger.info("✓ Token refresh service started")
```


## AMC API client usage

The AMC client sends the expected Amazon headers and your bearer token. You supply:
- `access_token` from `get_valid_token(user_id)`
- `entity_id` (Amazon advertiser account)
- `marketplace_id` (e.g., `ATVPDKIKX0DER` for US)

```57:66:amc_manager/services/amc_api_client.py
headers = {
    'Amazon-Advertising-API-ClientId': settings.amazon_client_id,
    'Authorization': f'Bearer {access_token}',
    'Amazon-Advertising-API-MarketplaceId': marketplace_id,
    'Amazon-Advertising-API-AdvertiserId': entity_id,
    'Content-Type': 'application/json'
}
```

Example: create a workflow execution

```python
from amc_manager.services.token_service import token_service
from amc_manager.services.amc_api_client import amc_api_client

async def run_amc_report(user_id: str, instance_id: str, entity_id: str, marketplace_id: str = "ATVPDKIKX0DER"):
    access_token = await token_service.get_valid_token(user_id)
    if not access_token:
        raise RuntimeError("No valid Amazon token for user")

    result = amc_api_client.create_workflow_execution(
        instance_id=instance_id,
        access_token=access_token,
        entity_id=entity_id,
        marketplace_id=marketplace_id,
        sql_query="SELECT 1 as test"
    )
    return result
```


## Environment variables

- AMAZON_CLIENT_ID
- AMAZON_CLIENT_SECRET
- AMAZON_OAUTH_REDIRECT_URI
- AMAZON_SCOPE (default: `advertising::campaign_management`)
- FERNET_KEY (stable, do not rotate casually)
- SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_ROLE_KEY
- FRONTEND_URL, ENVIRONMENT

Notes
- Some older scripts reference `AMAZON_REDIRECT_URI`. Prefer `AMAZON_OAUTH_REDIRECT_URI`; define both if you run those scripts.


## Setting up a new app (reusing this implementation)

1) Create an app in the Amazon Developer Console (Advertising API)
- Add your local and production redirect URIs
- Enable the scope `advertising::campaign_management`

2) Copy the following components or mirror their responsibilities:
- OAuth endpoints: `amc_manager/api/supabase/amazon_auth.py`
- Token service: `amc_manager/services/token_service.py`
- Background refresh service: `amc_manager/services/token_refresh_service.py`
- AMC API client: `amc_manager/services/amc_api_client.py`
- Startup hook to run the refresher: `main_supabase.py` lifespan

3) Provide environment variables and a stable `FERNET_KEY`.

4) Database layer
- This app stores tokens on the `users` table via a `db_service`. In your app, implement equivalent persistence (user store with `auth_tokens` JSON field) and wire it into the token service methods used here.

5) Frontend login
- Call `GET /api/auth/amazon/login`, redirect the browser to `auth_url`.
- On success, your backend issues an app JWT and redirects back to your SPA with a token query param.


## Failure modes and debugging
- 401s on AMC/API requests usually mean expired/invalid tokens; ensure `get_valid_token()` is used.
- Encryption errors usually indicate a missing or changed `FERNET_KEY`.
- 403 on AMC endpoints can indicate missing headers (`AdvertiserId`, `MarketplaceId`) or account access.
- Verify redirect URI exactly matches what’s in the Amazon Developer Console.


## Related references in this repo
- Token refresh design: `docs/TOKEN_REFRESH_IMPLEMENTATION.md`
- AMC client details: `docs/amc_api_client.md`


