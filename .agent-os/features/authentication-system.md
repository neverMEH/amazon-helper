# Authentication System

## Overview

RecomAMP uses OAuth 2.0 with Amazon's Login with Amazon (LWA) service for user authentication, coupled with JWT tokens for session management and Fernet encryption for secure token storage. The system handles automatic token refresh and multi-instance account management.

## Recent Security Enhancements (2025-09-11)

### Enhanced Data Isolation Implementation
- **Security Fix**: Implemented comprehensive user-level filtering across all campaign endpoints
- **Scope**: All campaign-related API operations now automatically filter by authenticated user ID
- **Impact**: Prevents cross-user data access and ensures multi-tenant security
- **Implementation**: Backend services now enforce user-level data boundaries at the database query level
- **Testing**: Added TDD test suite to verify user isolation works correctly

## Key Components

### Backend Services
- `amc_manager/services/auth_service.py` - Core authentication logic
- `amc_manager/services/token_service.py` - Token management and refresh
- `amc_manager/core/security.py` - JWT and encryption utilities
- `amc_manager/api/supabase/auth.py` - Authentication endpoints

### Frontend Components
- `frontend/src/pages/Login.tsx` - Login interface
- `frontend/src/components/AuthCallback.tsx` - OAuth callback handler
- `frontend/src/services/auth.service.ts` - Authentication API client
- `frontend/src/contexts/AuthContext.tsx` - Authentication state management

### Database Tables
- `users` - User profiles with encrypted OAuth tokens
- `amc_instances` - Instance configurations linked to user accounts
- `amc_accounts` - Amazon account details

## Technical Implementation

### OAuth 2.0 Flow
```python
# auth_service.py - OAuth initialization
async def initiate_amazon_login(self, redirect_uri: str) -> str:
    """Generate Amazon OAuth URL"""
    params = {
        'client_id': settings.AMAZON_CLIENT_ID,
        'scope': 'cpc_advertising:campaign_management',
        'response_type': 'code',
        'redirect_uri': redirect_uri,
        'state': generate_state_token()
    }
    
    auth_url = f"{settings.AMAZON_AUTH_URL}?" + urlencode(params)
    return auth_url

async def handle_amazon_callback(self, code: str, state: str) -> dict:
    """Process OAuth callback and exchange code for tokens"""
    # Verify state parameter
    if not verify_state_token(state):
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Exchange code for tokens
    token_data = await self.exchange_code_for_tokens(code)
    
    # Get user profile from Amazon
    profile = await self.get_amazon_profile(token_data['access_token'])
    
    # Create or update user
    user = await self.create_or_update_user(profile, token_data)
    
    return user
```

### Token Management
```python
# token_service.py - Token storage and refresh
class TokenService:
    def __init__(self):
        self.cipher = Fernet(settings.FERNET_KEY)
    
    def encrypt_token(self, token: str) -> str:
        """Encrypt token for database storage"""
        return self.cipher.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token from database"""
        try:
            return self.cipher.decrypt(encrypted_token.encode()).decode()
        except Exception as e:
            raise TokenDecryptionError("Failed to decrypt token - user must re-authenticate")
    
    async def refresh_access_token(self, user_id: str) -> dict:
        """Refresh expired access token using refresh token"""
        user = self.get_user_tokens(user_id)
        refresh_token = self.decrypt_token(user['encrypted_refresh_token'])
        
        # Exchange refresh token for new access token
        response = await httpx.post(settings.AMAZON_TOKEN_URL, data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'client_id': settings.AMAZON_CLIENT_ID,
            'client_secret': settings.AMAZON_CLIENT_SECRET
        })
        
        if response.status_code == 200:
            token_data = response.json()
            await self.update_user_tokens(user_id, token_data)
            return token_data
        else:
            raise TokenRefreshError("Failed to refresh token")
```

### JWT Session Management
```python
# security.py - JWT utilities
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Validate JWT token and return current user"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = get_user_by_id(user_id)
    if user is None:
        raise credentials_exception
    
    return user
```

## Data Flow

1. **Login Initiation**: User clicks "Login with Amazon"
2. **OAuth Redirect**: Redirect to Amazon's authorization server
3. **User Authorization**: User grants permissions on Amazon's site
4. **Callback Processing**: Amazon redirects back with authorization code
5. **Token Exchange**: Exchange code for access/refresh tokens
6. **User Creation**: Create/update user profile with encrypted tokens
7. **JWT Generation**: Generate session JWT for frontend
8. **Session Management**: Frontend stores JWT, includes in API requests

## Critical Security Measures

### Token Encryption
```python
# All OAuth tokens encrypted at rest
class User:
    encrypted_access_token: str      # Fernet encrypted
    encrypted_refresh_token: str     # Fernet encrypted
    token_expires_at: datetime       # Plaintext expiry
    
# Encryption key management
FERNET_KEY = os.getenv('FERNET_KEY') or Fernet.generate_key()
```

### State Parameter Validation
```python
def generate_state_token() -> str:
    """Generate secure state parameter for CSRF protection"""
    return secrets.token_urlsafe(32)

def verify_state_token(state: str) -> bool:
    """Verify state parameter (implement based on storage method)"""
    # In production, store states in cache/database with expiry
    return True  # Simplified for example
```

### CORS and Security Headers
```python
# main_supabase.py - Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    return response
```

## Amazon OAuth Scopes

### Required Scopes
```python
AMAZON_SCOPES = [
    'cpc_advertising:campaign_management',  # Core advertising API
    'cpc_advertising:read_campaigns',       # Campaign data access
    'cpc_advertising:modify_campaigns',     # Campaign management
    'advertising::campaign_management',     # AMC access
]
```

### Scope Validation
```python
def validate_token_scopes(token: str, required_scopes: List[str]) -> bool:
    """Validate token has required scopes for operation"""
    token_info = decode_amazon_token(token)
    token_scopes = token_info.get('scope', '').split()
    
    return all(scope in token_scopes for scope in required_scopes)
```

## Error Handling Patterns

### Token Expiry Handling
```python
async def make_authenticated_request(user_id: str, url: str, **kwargs):
    """Make API request with automatic token refresh"""
    user = get_user_by_id(user_id)
    access_token = decrypt_token(user['encrypted_access_token'])
    
    # Check if token is expired
    if datetime.utcnow() >= user['token_expires_at']:
        # Refresh token before request
        new_tokens = await refresh_access_token(user_id)
        access_token = new_tokens['access_token']
    
    headers = kwargs.get('headers', {})
    headers['Authorization'] = f'Bearer {access_token}'
    
    return await httpx.request(url=url, headers=headers, **kwargs)
```

### Common Error Scenarios
```python
class AuthenticationError(Exception):
    """Base authentication error"""
    pass

class TokenExpiredException(AuthenticationError):
    """Access token expired"""
    pass

class TokenDecryptionError(AuthenticationError):
    """Failed to decrypt stored tokens"""
    pass

class TokenRefreshError(AuthenticationError):
    """Failed to refresh access token"""
    pass
```

## Frontend Integration

### Authentication Context
```typescript
// AuthContext.tsx - Global authentication state
interface AuthContextType {
  user: User | null;
  login: () => void;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      // Verify token and get user info
      authService.verifyToken(token)
        .then(setUser)
        .catch(() => logout());
    }
    setIsLoading(false);
  }, []);
  
  const login = () => {
    window.location.href = '/api/auth/login';
  };
  
  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
    window.location.href = '/login';
  };
  
  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user, isLoading }}>
      {children}
    </AuthContext.Provider>
  );
};
```

### API Client with Token Handling
```typescript
// api.service.ts - Axios interceptor for token management
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response?.status === 401) {
      // Token expired, redirect to login
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

## Background Token Refresh Service

### Automatic Refresh
```python
# token_refresh_service.py - Background service
class TokenRefreshService:
    async def refresh_expiring_tokens(self):
        """Refresh tokens that expire within 10 minutes"""
        cutoff_time = datetime.utcnow() + timedelta(minutes=10)
        
        expiring_users = self.db.table('users')\
            .select('id, encrypted_refresh_token, token_expires_at')\
            .lte('token_expires_at', cutoff_time.isoformat())\
            .is_('encrypted_refresh_token', 'not.null')\
            .execute()
        
        for user in expiring_users.data:
            try:
                await self.token_service.refresh_access_token(user['id'])
                logger.info(f"Refreshed token for user {user['id']}")
            except TokenRefreshError as e:
                logger.warning(f"Failed to refresh token for user {user['id']}: {e}")
                # Could disable user or send notification
```

## Interconnections

### With Instance Management
- Users can only access their configured AMC instances
- Instance credentials tied to user's OAuth tokens
- Multi-account support through instance association

### With Workflow Execution
- All API calls use user's decrypted access tokens
- Automatic token refresh before AMC operations
- Error handling for authentication failures

### With Background Services
- Services execute under user context with their tokens
- Token refresh service maintains valid authentication
- Schedule execution uses stored user credentials

## Testing Considerations

### Unit Tests
```python
def test_token_encryption():
    # Test encryption/decryption round trip
    
def test_jwt_generation():
    # Test JWT creation and validation
    
def test_oauth_flow():
    # Mock Amazon OAuth responses
```

### Integration Tests
```python
async def test_full_auth_flow():
    # Test complete OAuth flow with mocked Amazon
    
async def test_token_refresh():
    # Test automatic token refresh
```

### Security Tests
```python
def test_state_parameter_validation():
    # Test CSRF protection
    
def test_token_expiry_handling():
    # Test expired token scenarios
```

## Monitoring and Debugging

### Authentication Metrics
- Track login success/failure rates
- Monitor token refresh frequency
- Alert on authentication errors

### Debug Tools
```bash
# Check user token status
python scripts/check_user_tokens.py <user_id>

# Test token refresh
python scripts/refresh_user_token.py <user_id>

# Validate JWT tokens
python scripts/validate_jwt.py <token>
```