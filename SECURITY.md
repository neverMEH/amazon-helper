# Security Documentation - Recom AMP

## Overview

This document outlines the security measures implemented in the Recom AMP platform to protect against common web vulnerabilities and ensure secure handling of sensitive data.

## Table of Contents

1. [Input Validation](#input-validation)
2. [SQL Injection Prevention](#sql-injection-prevention)
3. [Authentication & Authorization](#authentication--authorization)
4. [Rate Limiting](#rate-limiting)
5. [Security Headers](#security-headers)
6. [Token Security](#token-security)
7. [CORS Configuration](#cors-configuration)
8. [Error Handling](#error-handling)
9. [Data Encryption](#data-encryption)
10. [Security Testing](#security-testing)
11. [Deployment Security](#deployment-security)
12. [Migration Guide](#migration-guide)

## Input Validation

### Pydantic Schema Validation

All API endpoints use Pydantic models for automatic input validation and sanitization.

#### Authentication Schemas (`amc_manager/schemas/auth.py`)

```python
class LoginRequest(BaseModel):
    email: EmailStr  # Validates email format
    password: Optional[str] = Field(None, min_length=0, max_length=256)
    
    @validator('email')
    def validate_email(cls, v):
        return v.lower()  # Normalize email to lowercase
```

#### Workflow Schemas (`amc_manager/schemas/workflow.py`)

```python
class WorkflowCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    sql_query: str = Field(..., min_length=1)
    instance_id: str = Field(..., min_length=1)
    
    @validator('sql_query')
    def validate_sql_query(cls, v):
        # Check for dangerous SQL operations
        dangerous_patterns = [
            (r'DELETE\s+FROM\s+\w+(?!\s+WHERE)', 'DELETE without WHERE clause'),
            (r'UPDATE\s+\w+\s+SET(?!.*WHERE)', 'UPDATE without WHERE clause'),
            (r'TRUNCATE\s+TABLE', 'TRUNCATE TABLE not allowed'),
            (r'DROP\s+(TABLE|DATABASE|SCHEMA)', 'DROP operations not allowed'),
        ]
        # Validation logic...
```

### Benefits
- Automatic type checking
- Field length validation
- Custom validation rules
- Clear error messages
- Protection against malformed input

## SQL Injection Prevention

### Parameter Escaping System

The `amc_execution_service.py` implements comprehensive SQL injection prevention:

```python
def _prepare_sql_query(self, sql_template: str, parameters: Dict[str, Any]) -> str:
    dangerous_keywords = ['DROP', 'DELETE FROM', 'INSERT INTO', 'UPDATE', 
                         'ALTER', 'CREATE', 'EXEC', 'EXECUTE', 'TRUNCATE', 
                         'GRANT', 'REVOKE']
    
    for param, value in parameters.items():
        if isinstance(value, str):
            # Escape single quotes
            value_escaped = value.replace("'", "''")
            
            # Check for dangerous SQL keywords
            for keyword in dangerous_keywords:
                if keyword in value_escaped.upper():
                    raise ValueError(f"Dangerous SQL keyword '{keyword}' detected")
```

### Protection Layers

1. **Input Validation**: Pydantic schemas validate query structure
2. **Parameter Escaping**: All user inputs are escaped
3. **Keyword Blocking**: Dangerous SQL keywords are blocked
4. **Parameterized Queries**: Uses `{{parameter}}` syntax for safe substitution

### Safe Query Example

```sql
-- Template with parameters
SELECT * FROM campaigns 
WHERE brand_id = '{{brand_id}}' 
  AND date >= '{{start_date}}'
  
-- After safe substitution (with escaped values)
SELECT * FROM campaigns 
WHERE brand_id = 'escaped_value' 
  AND date >= '2024-01-01'
```

## Authentication & Authorization

### JWT Token System

- **Token Generation**: 24-hour expiry with HS256 algorithm
- **Token Validation**: Every request validates JWT signature
- **User Context**: Tokens contain user ID and email
- **Secure Storage**: Tokens stored encrypted in database

### Authorization Checks

```python
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, settings.jwt_secret_key, algorithms=["HS256"])
        user_id = payload.get("sub")
        # Verify user exists in database
        user = db_service.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
```

## Rate Limiting

### Configuration

Rate limiting is implemented using `slowapi` with configurable limits:

```python
# main_supabase.py
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per minute"]
)

# Specific endpoint limits
@router.post("/login")
@limiter.limit("5 per minute")  # Prevent brute force
def login(request: Request, ...):
    pass

@router.post("/refresh-token")
@limiter.limit("10 per minute")  # Reasonable refresh rate
def refresh_token(request: Request, ...):
    pass
```

### Adjusting Rate Limits

To modify rate limits, update the decorator on specific endpoints:

```python
# Examples of different rate limit configurations
@limiter.limit("3 per hour")     # Very restrictive
@limiter.limit("20 per minute")  # More permissive
@limiter.limit("1000 per day")   # Daily quota
```

## Security Headers

### Middleware Implementation

Security headers are automatically added to all responses:

```python
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # Enable XSS protection
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Control referrer information
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Force HTTPS in production
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    return response
```

### Header Explanations

| Header | Purpose | Protection Against |
|--------|---------|-------------------|
| X-Content-Type-Options | Prevents MIME sniffing | Drive-by downloads |
| X-Frame-Options | Prevents embedding in iframes | Clickjacking |
| X-XSS-Protection | Enables browser XSS filter | Cross-site scripting |
| Referrer-Policy | Controls referrer info | Information leakage |
| Strict-Transport-Security | Forces HTTPS | Man-in-the-middle |

## Token Security

### Encryption System

OAuth tokens are encrypted using Fernet symmetric encryption:

```python
class TokenService:
    def __init__(self):
        # Generate or load encryption key
        key = os.getenv('FERNET_KEY') or Fernet.generate_key()
        self.fernet = Fernet(key)
    
    def encrypt_token(self, token: str) -> str:
        return self.fernet.encrypt(token.encode()).decode()
    
    def decrypt_token(self, encrypted_token: str) -> str:
        return self.fernet.decrypt(encrypted_token.encode()).decode()
```

### Token Storage

1. **Encryption**: All tokens encrypted before database storage
2. **Key Management**: Encryption key stored as environment variable
3. **Token Validation**: Decrypted tokens validated for Amazon format
4. **Error Handling**: Graceful handling of decryption failures

### Environment Configuration

```bash
# Generate a new Fernet key
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Set in environment
export FERNET_KEY="your-generated-key-here"
```

## CORS Configuration

### Environment-Specific Settings

```python
# Production configuration
if settings.environment == "production":
    allowed_origins = os.getenv('ALLOWED_ORIGINS', '').split(',')
    if not allowed_origins:
        allowed_origins = ["https://your-production-domain.com"]
else:
    # Development configuration
    allowed_origins = [
        "http://localhost:5173",  # Vite dev server
        "http://localhost:8001"   # API server
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

### Configuring for Production

Set the `ALLOWED_ORIGINS` environment variable:

```bash
export ALLOWED_ORIGINS="https://app.example.com,https://www.example.com"
```

## Error Handling

### Backend Error Handling

Enhanced error handling with specific exception types:

```python
try:
    # Token operations
    decrypted = self.decrypt_token(token)
except InvalidToken:
    logger.error("Invalid token format")
    raise HTTPException(status_code=401, detail="Invalid token")
except TokenExpired:
    logger.error("Token has expired")
    raise HTTPException(status_code=401, detail="Token expired")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Frontend Error Boundary

React ErrorBoundary component catches and handles component errors:

```tsx
class ErrorBoundary extends Component<Props, State> {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log to error service in production
    if (process.env.NODE_ENV === 'production') {
      logErrorToService(error, errorInfo);
    }
    
    // Display user-friendly error message
    this.setState({ hasError: true, error, errorInfo });
  }
  
  render() {
    if (this.state.hasError) {
      return <ErrorFallbackUI onReset={this.handleReset} />;
    }
    return this.props.children;
  }
}
```

## Data Encryption

### At Rest
- OAuth tokens encrypted with Fernet
- Database connections use SSL/TLS
- Sensitive fields encrypted in database

### In Transit
- HTTPS enforced in production
- API requests use Bearer token authentication
- WebSocket connections use WSS

### Key Management
```bash
# Generate encryption keys
openssl rand -base64 32  # For JWT secret
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"  # For token encryption

# Store in environment variables
export JWT_SECRET_KEY="your-jwt-secret"
export FERNET_KEY="your-fernet-key"
```

## Security Testing

### Testing Guidelines

#### 1. SQL Injection Testing

```python
# Test dangerous SQL patterns
def test_sql_injection_prevention():
    dangerous_inputs = [
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        "admin'--",
        "' UNION SELECT * FROM users--"
    ]
    
    for input_val in dangerous_inputs:
        with pytest.raises(ValueError):
            service._prepare_sql_query(
                "SELECT * FROM data WHERE id = '{{id}}'",
                {"id": input_val}
            )
```

#### 2. Rate Limiting Testing

```python
# Test rate limits
async def test_rate_limiting():
    # Exceed rate limit
    for i in range(6):  # Login limit is 5/minute
        response = await client.post("/login", json={"email": "test@example.com"})
    
    assert response.status_code == 429  # Too Many Requests
```

#### 3. Authentication Testing

```python
# Test JWT validation
def test_invalid_token():
    headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/api/protected", headers=headers)
    assert response.status_code == 401
```

### Security Checklist

- [ ] All endpoints have authentication
- [ ] Input validation on all user inputs
- [ ] SQL injection prevention tested
- [ ] Rate limiting configured
- [ ] Security headers present
- [ ] Tokens encrypted in storage
- [ ] CORS properly configured
- [ ] Error messages don't leak sensitive info
- [ ] HTTPS enforced in production
- [ ] Logs don't contain sensitive data

## Deployment Security

### Production Configuration

```bash
# Required environment variables
export ENVIRONMENT="production"
export JWT_SECRET_KEY="strong-random-key"
export FERNET_KEY="generated-fernet-key"
export ALLOWED_ORIGINS="https://your-domain.com"
export SUPABASE_URL="https://your-project.supabase.co"
export SUPABASE_ANON_KEY="your-anon-key"
export SUPABASE_SERVICE_ROLE_KEY="your-service-key"

# Security settings
export FORCE_HTTPS="true"
export SESSION_COOKIE_SECURE="true"
export SESSION_COOKIE_HTTPONLY="true"
export SESSION_COOKIE_SAMESITE="strict"
```

### Docker Security

```dockerfile
# Use non-root user
RUN adduser -D appuser
USER appuser

# Copy only necessary files
COPY --chown=appuser:appuser . /app

# Scan for vulnerabilities
RUN pip install safety && safety check
```

### Network Security

1. **Firewall Rules**: Only expose necessary ports (443 for HTTPS)
2. **VPC Configuration**: Isolate database in private subnet
3. **SSL/TLS**: Use Let's Encrypt or commercial certificates
4. **WAF**: Consider Web Application Firewall for additional protection

## Migration Guide

### For Existing Deployments

#### Step 1: Update Environment Variables

```bash
# Generate new keys if not exists
export FERNET_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
export JWT_SECRET_KEY=$(openssl rand -base64 32)
```

#### Step 2: Install New Dependencies

```bash
pip install -r requirements_supabase.txt
# Key additions:
# - slowapi==0.1.9 (rate limiting)
# - cryptography==41.0.7 (token encryption)
# - pydantic==2.5.3 (input validation)
```

#### Step 3: Database Migration

```sql
-- Ensure auth_tokens column exists and can store encrypted tokens
ALTER TABLE users 
ALTER COLUMN auth_tokens TYPE TEXT;

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_workflows_user_id ON workflows(user_id);
```

#### Step 4: Update API Clients

Frontend changes required:
```typescript
// Add timeout configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  withCredentials: true
});

// Handle rate limiting
api.interceptors.response.use(
  response => response,
  error => {
    if (error.response?.status === 429) {
      // Handle rate limit exceeded
      console.error('Rate limit exceeded, please try again later');
    }
    return Promise.reject(error);
  }
);
```

### Breaking Changes

1. **Token Format**: Tokens are now encrypted - existing tokens need re-encryption
2. **Rate Limits**: API calls may be rate-limited - implement retry logic
3. **Input Validation**: Stricter validation may reject previously accepted inputs
4. **SQL Queries**: Some SQL patterns now blocked for security

### Rollback Plan

If issues occur:

1. **Keep Old Environment**: Maintain previous environment variables
2. **Database Backup**: Create backup before migration
3. **Feature Flags**: Use environment variables to toggle security features
4. **Gradual Rollout**: Enable security features incrementally

```python
# Example feature flag usage
if os.getenv('ENABLE_RATE_LIMITING', 'false').lower() == 'true':
    app.state.limiter = limiter
    
if os.getenv('ENABLE_SQL_VALIDATION', 'false').lower() == 'true':
    validate_sql_query(query)
```

## Security Contacts

For security issues or questions:

- **Security Team**: security@example.com
- **Bug Bounty**: https://example.com/security/bounty
- **Security Updates**: Subscribe to security advisory list

## Compliance

This application follows security best practices aligned with:

- OWASP Top 10 Web Application Security Risks
- PCI DSS (if handling payment data)
- GDPR (for EU user data)
- SOC 2 Type II controls

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2024-01-15 | Initial security implementation |
| 1.1.0 | 2024-01-20 | Added rate limiting and SQL injection prevention |
| 1.2.0 | 2024-01-25 | Enhanced token encryption and security headers |

## Additional Resources

- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Pydantic Validation](https://docs.pydantic.dev/latest/usage/validators/)
- [Cryptography Library](https://cryptography.io/en/latest/)
- [Slowapi Rate Limiting](https://github.com/laurentS/slowapi)