# token_service.py

## Purpose
Secure token management service for Amazon OAuth tokens. Handles encryption, storage, validation, and refresh of OAuth tokens using Fernet symmetric encryption. Critical for maintaining secure authentication state across the application.

## Dependencies
### External Dependencies
- cryptography.fernet: Symmetric encryption for token security
- requests: 2.31.0+ - HTTP client for OAuth token operations
- datetime: builtin - Token expiration handling
- json: builtin - Token data serialization

### Internal Dependencies
- ../core/logger_simple: Application logging
- ../config/settings: Configuration management
- db_service: Database operations for token storage

## Exports
### Classes
- `TokenService`: Main service class for token management

### Functions
- `encrypt_tokens()`: Encrypt tokens for secure storage
- `decrypt_tokens()`: Decrypt stored tokens
- `update_user_tokens()`: Store encrypted tokens in database
- `get_user_tokens()`: Retrieve and decrypt user tokens
- `validate_token()`: Check token validity and expiration
- `refresh_access_token()`: Refresh expired access tokens
- `get_user_profiles()`: Fetch Amazon advertising profiles
- `is_token_expired()`: Check token expiration status

### Constants
- `TOKEN_ENDPOINT`: "https://api.amazon.com/auth/o2/token"
- `PROFILE_ENDPOINT`: "https://advertising-api.amazon.com/v2/profiles"
- `TOKEN_BUFFER_MINUTES`: 15 (refresh buffer before expiration)

## Usage Examples
```python
# Initialize service
service = TokenService()

# Encrypt and store tokens
tokens = {
    "access_token": "Bearer_xyz123",
    "refresh_token": "refresh_abc456",
    "expires_in": 3600
}
await service.update_user_tokens(user_id, tokens)

# Retrieve and decrypt tokens
user_tokens = await service.get_user_tokens(user_id)

# Check token validity
is_valid = await service.validate_token(user_id)

# Refresh expired token
new_tokens = await service.refresh_access_token(user_id)

# Get user advertising profiles
profiles = await service.get_user_profiles(user_id)
```

## Relationships
### Used By
- amc_api_client_with_retry.py: Token refresh for API calls
- token_refresh_service.py: Background token refresh
- amc_manager/api/supabase/auth.py: Authentication endpoints
- All AMC API operations requiring authentication

### Uses
- db_service.py: Database operations for token storage
- settings.py: Fernet key configuration
- Amazon OAuth API: Token refresh operations

## Side Effects
- Database writes for token storage
- Encryption/decryption operations
- Network calls to Amazon OAuth API
- Log generation for security events
- Environment variable reading for encryption key

## Testing Considerations
### Key Scenarios
- Token encryption/decryption accuracy
- Key generation and persistence
- Token expiration detection
- Refresh token flow
- Profile fetching with valid tokens
- Error handling for invalid tokens

### Edge Cases
- Missing or corrupted encryption key
- Malformed token data
- Network failures during refresh
- Expired refresh tokens
- Invalid token responses from Amazon
- Database connection failures

### Mocking Requirements
- Mock Amazon OAuth API responses
- Token data with various expiration times
- Fernet encryption operations
- Database operation mocks

## Performance Notes
### Optimizations
- In-memory caching of Fernet instance
- Efficient JSON serialization
- Minimal database queries
- Batch token operations

### Bottlenecks
- Encryption/decryption overhead
- Network latency for token refresh
- Database I/O for token storage
- JSON parsing for large token objects

### Monitoring Points
- Token refresh frequency
- Encryption operation times
- Database connection usage
- OAuth API response times

## Critical Implementation Patterns

### Secure Token Encryption
```python
def encrypt_tokens(self, tokens: Dict[str, Any]) -> str:
    """Encrypt tokens using Fernet symmetric encryption"""
    if not self.fernet:
        raise ValueError("Encryption not available - invalid Fernet key")
    
    # Serialize and encrypt
    token_json = json.dumps(tokens)
    encrypted = self.fernet.encrypt(token_json.encode())
    return encrypted.decode()

def decrypt_tokens(self, encrypted_tokens: str) -> Optional[Dict[str, Any]]:
    """Decrypt tokens with error handling"""
    if not self.fernet:
        logger.error("Cannot decrypt - Fernet not initialized")
        return None
    
    try:
        decrypted = self.fernet.decrypt(encrypted_tokens.encode())
        return json.loads(decrypted.decode())
    except Exception as e:
        logger.error(f"Token decryption failed: {e}")
        # Clear corrupted tokens
        return None
```

### Token Expiration Handling
```python
def is_token_expired(self, tokens: Dict[str, Any], buffer_minutes: int = 15) -> bool:
    """Check if token needs refresh with buffer"""
    if not tokens.get('expires_at'):
        return True
    
    expires_at = datetime.fromisoformat(tokens['expires_at'])
    buffer_time = datetime.utcnow() + timedelta(minutes=buffer_minutes)
    
    return expires_at <= buffer_time
```

### Automatic Token Refresh
```python
async def refresh_access_token(self, user_id: str) -> Optional[Dict[str, Any]]:
    """Refresh access token using refresh token"""
    current_tokens = await self.get_user_tokens(user_id)
    if not current_tokens or not current_tokens.get('refresh_token'):
        logger.error(f"No refresh token available for user {user_id}")
        return None
    
    refresh_payload = {
        'grant_type': 'refresh_token',
        'refresh_token': current_tokens['refresh_token'],
        'client_id': settings.AMAZON_CLIENT_ID,
        'client_secret': settings.AMAZON_CLIENT_SECRET
    }
    
    try:
        response = requests.post(self.token_endpoint, data=refresh_payload)
        response.raise_for_status()
        
        new_tokens = response.json()
        new_tokens['expires_at'] = (
            datetime.utcnow() + timedelta(seconds=new_tokens['expires_in'])
        ).isoformat()
        
        # Store refreshed tokens
        await self.update_user_tokens(user_id, new_tokens)
        return new_tokens
        
    except requests.RequestException as e:
        logger.error(f"Token refresh failed for user {user_id}: {e}")
        return None
```

### Fernet Key Management
```python
def _get_fernet(self) -> Optional[Fernet]:
    """Initialize Fernet with key management"""
    try:
        # Try multiple environment variable names
        key = (settings.fernet_key or 
               os.getenv('FERNET_KEY') or 
               os.getenv('ENCRYPTION_KEY'))
        
        if not key:
            # Generate new key if none exists
            key = Fernet.generate_key().decode()
            logger.warning("Generated new encryption key. Set FERNET_KEY env var!")
            # In production, this should fail rather than generate
        
        fernet = Fernet(key.encode() if isinstance(key, str) else key)
        logger.info("Fernet encryption initialized successfully")
        return fernet
        
    except (ValueError, TypeError) as e:
        logger.error(f"Fernet initialization failed: {e}")
        return None
```

## Security Considerations

### Encryption Standards
- Uses Fernet (AES 128 in CBC mode with HMAC SHA256)
- Keys must be 32 URL-safe base64-encoded bytes
- Automatic token clearing on decryption failure
- No plaintext token storage

### Key Management
```python
# Production key management
FERNET_KEY = os.getenv('FERNET_KEY')
if not FERNET_KEY:
    raise ValueError("FERNET_KEY environment variable required")

# Key rotation strategy
def rotate_fernet_key(old_key: str, new_key: str):
    """Safely rotate encryption keys"""
    old_fernet = Fernet(old_key)
    new_fernet = Fernet(new_key)
    
    # Re-encrypt all tokens with new key
    for user_tokens in get_all_encrypted_tokens():
        decrypted = old_fernet.decrypt(user_tokens['encrypted'])
        re_encrypted = new_fernet.encrypt(decrypted)
        update_user_tokens(user_tokens['user_id'], re_encrypted)
```

### Token Validation
```python
async def validate_token(self, user_id: str) -> bool:
    """Comprehensive token validation"""
    tokens = await self.get_user_tokens(user_id)
    if not tokens:
        return False
    
    # Check expiration
    if self.is_token_expired(tokens):
        logger.info(f"Token expired for user {user_id}")
        return False
    
    # Validate with Amazon API
    try:
        headers = {
            'Authorization': f"Bearer {tokens['access_token']}",
            'Amazon-Advertising-API-ClientId': settings.AMAZON_CLIENT_ID
        }
        response = requests.get(self.profile_endpoint, headers=headers)
        return response.status_code == 200
        
    except requests.RequestException:
        return False
```

## Error Handling Strategies

### Decryption Failures
```python
def decrypt_tokens(self, encrypted_tokens: str) -> Optional[Dict[str, Any]]:
    """Decrypt with comprehensive error handling"""
    try:
        decrypted = self.fernet.decrypt(encrypted_tokens.encode())
        return json.loads(decrypted.decode())
    except InvalidToken:
        logger.error("Invalid encryption token - possibly corrupted")
        return None
    except json.JSONDecodeError:
        logger.error("Token data corrupted - invalid JSON")
        return None
    except Exception as e:
        logger.error(f"Unexpected decryption error: {e}")
        return None
```

### OAuth API Errors
```python
async def refresh_access_token(self, user_id: str) -> Optional[Dict[str, Any]]:
    """Refresh with comprehensive error handling"""
    try:
        response = requests.post(self.token_endpoint, data=payload)
        
        if response.status_code == 400:
            error_data = response.json()
            if error_data.get('error') == 'invalid_grant':
                logger.error(f"Refresh token expired for user {user_id}")
                await self.clear_user_tokens(user_id)
            return None
            
        elif response.status_code == 401:
            logger.error(f"Invalid client credentials")
            return None
            
        response.raise_for_status()
        return response.json()
        
    except requests.Timeout:
        logger.error("Token refresh timeout")
        return None
    except requests.ConnectionError:
        logger.error("Token refresh connection failed")
        return None
```

## Database Integration

### Token Storage Schema
```sql
-- Users table with encrypted token storage
ALTER TABLE users ADD COLUMN auth_tokens TEXT;

-- Token storage pattern
{
  "access_token": "encrypted_access_token",
  "refresh_token": "encrypted_refresh_token", 
  "expires_at": "2025-08-15T14:30:00",
  "token_type": "bearer",
  "scope": "advertising:read advertising:write"
}
```

### Database Operations
```python
async def update_user_tokens(self, user_id: str, tokens: Dict[str, Any]) -> bool:
    """Store encrypted tokens in database"""
    try:
        encrypted = self.encrypt_tokens(tokens)
        
        await db_service.execute_query(
            "UPDATE users SET auth_tokens = %s WHERE id = %s",
            (encrypted, user_id)
        )
        
        logger.info(f"Updated tokens for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update tokens for user {user_id}: {e}")
        return False

async def get_user_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve and decrypt user tokens"""
    try:
        result = await db_service.execute_query(
            "SELECT auth_tokens FROM users WHERE id = %s",
            (user_id,)
        )
        
        if not result or not result[0]['auth_tokens']:
            return None
            
        return self.decrypt_tokens(result[0]['auth_tokens'])
        
    except Exception as e:
        logger.error(f"Failed to get tokens for user {user_id}: {e}")
        return None
```

## Integration with Background Services

### Token Refresh Service Integration
```python
# Used by token_refresh_service.py
async def get_users_needing_refresh(self) -> List[str]:
    """Get users with tokens expiring soon"""
    users_to_refresh = []
    
    all_users = await db_service.execute_query(
        "SELECT id, auth_tokens FROM users WHERE auth_tokens IS NOT NULL"
    )
    
    for user in all_users:
        tokens = self.decrypt_tokens(user['auth_tokens'])
        if tokens and self.is_token_expired(tokens, buffer_minutes=15):
            users_to_refresh.append(user['id'])
    
    return users_to_refresh
```

## Configuration Options

### Environment Variables
- `FERNET_KEY`: 32-byte base64 encryption key (required)
- `AMAZON_CLIENT_ID`: OAuth client ID
- `AMAZON_CLIENT_SECRET`: OAuth client secret
- `TOKEN_REFRESH_BUFFER`: Minutes before expiry to refresh (default: 15)

### Feature Flags
- `ENABLE_TOKEN_ENCRYPTION`: Toggle encryption (default: true)
- `AUTO_CLEAR_INVALID_TOKENS`: Clear corrupted tokens (default: true)
- `LOG_TOKEN_OPERATIONS`: Enhanced logging (default: false)

## Known Issues & Workarounds

### Fernet Key Persistence
- Generated keys are not persistent across restarts
- Must set FERNET_KEY environment variable in production
- Key changes invalidate all stored tokens

### Token Refresh Race Conditions
- Multiple simultaneous refresh attempts possible
- Implement refresh locks in high-concurrency scenarios
- Background service handles most refresh scenarios

### Large Token Storage
- Encrypted tokens are larger than plaintext
- Consider database field size limits
- Monitor storage growth with user scaling

## Monitoring & Alerting

### Key Metrics
- Token refresh success rate
- Encryption/decryption performance
- Failed token validation attempts
- Key rotation events

### Alert Conditions
- High token refresh failure rate
- Fernet key initialization failures
- Unusual token validation patterns
- Database token storage failures

## Recent Updates

### 2025-08-15 Changes
- Enhanced error handling for corrupted tokens
- Improved Fernet key management
- Added comprehensive token validation
- Better logging for security events
- Automatic token cleanup on failures