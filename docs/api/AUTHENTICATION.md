# Money Flow Authentication

Complete guide to authentication in the Money Flow API.

## Overview

Money Flow uses JWT (JSON Web Tokens) for authentication with a dual-token system:

- **Access Token**: Short-lived (15 minutes), used for API requests
- **Refresh Token**: Long-lived (7 days), used to obtain new access tokens

## Authentication Flow

```
┌──────────┐      ┌──────────┐      ┌──────────┐
│  Client  │      │   API    │      │  Redis   │
└────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                 │
     │  POST /auth/register or /auth/login
     │────────────────>│                 │
     │                 │                 │
     │  { access_token, refresh_token }  │
     │<────────────────│                 │
     │                 │                 │
     │  GET /subscriptions              │
     │  Authorization: Bearer <access>   │
     │────────────────>│                 │
     │                 │                 │
     │  { data: [...] }                  │
     │<────────────────│                 │
     │                 │                 │
     │  POST /auth/refresh               │
     │  { refresh_token }                │
     │────────────────>│                 │
     │                 │  Check blacklist │
     │                 │────────────────>│
     │                 │<────────────────│
     │  { new_access_token }             │
     │<────────────────│                 │
     │                 │                 │
     │  POST /auth/logout                │
     │────────────────>│                 │
     │                 │  Blacklist token │
     │                 │────────────────>│
     │  { success }    │                 │
     │<────────────────│                 │
```

## Endpoints

### Register

Create a new user account.

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character (!@#$%^&*)

**Response (201 Created):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "is_active": true,
    "is_verified": false,
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**Errors:**
- `400 Bad Request`: Email already registered
- `422 Unprocessable Entity`: Invalid email or weak password

### Login

Authenticate with existing credentials.

```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "is_active": true,
    "is_verified": true
  }
}
```

**Errors:**
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account deactivated

### Refresh Token

Get a new access token using the refresh token.

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Errors:**
- `401 Unauthorized`: Invalid or expired refresh token
- `401 Unauthorized`: Token has been revoked (blacklisted)

### Logout

Invalidate the current tokens.

```http
POST /api/v1/auth/logout
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "message": "Successfully logged out"
}
```

### Get Current User

Get the authenticated user's profile.

```http
GET /api/v1/auth/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "is_active": true,
  "is_verified": true,
  "role": "USER",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

## Using Tokens

### Authorization Header

Include the access token in all protected requests:

```http
GET /api/v1/subscriptions
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Token Structure

JWT tokens contain:

```json
{
  "sub": "user-id-uuid",
  "email": "user@example.com",
  "type": "access",
  "exp": 1705323600,
  "iat": 1705322700,
  "jti": "unique-token-id"
}
```

- `sub`: User ID (subject)
- `email`: User email
- `type`: Token type (`access` or `refresh`)
- `exp`: Expiration timestamp
- `iat`: Issued at timestamp
- `jti`: Unique token identifier (for blacklisting)

## Token Lifetimes

| Token Type | Lifetime | Use Case |
|------------|----------|----------|
| Access Token | 15 minutes | API requests |
| Refresh Token | 7 days | Getting new access tokens |

## Best Practices

### 1. Store Tokens Securely

**Browser (Frontend):**
```typescript
// Use httpOnly cookies or secure storage
localStorage.setItem('money_flow_access_token', token);
// Consider using sessionStorage for higher security
```

**Mobile Apps:**
- Use secure keychain (iOS) or keystore (Android)
- Never store in plain text

### 2. Handle Token Expiration

```typescript
// Axios interceptor example
axios.interceptors.response.use(
  response => response,
  async error => {
    if (error.response?.status === 401) {
      const refreshToken = getRefreshToken();
      const { data } = await axios.post('/api/v1/auth/refresh', {
        refresh_token: refreshToken
      });
      setAccessToken(data.access_token);
      // Retry original request
      error.config.headers.Authorization = `Bearer ${data.access_token}`;
      return axios(error.config);
    }
    return Promise.reject(error);
  }
);
```

### 3. Logout on Security Events

Always call logout endpoint when:
- User explicitly logs out
- Suspicious activity detected
- Password changed
- Long inactivity period

### 4. Validate Tokens Server-Side

The API validates:
- Token signature (HMAC-SHA256)
- Expiration time
- Token type matches endpoint
- Token not blacklisted
- User still active

## Error Responses

### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials"
}
```

Causes:
- Missing Authorization header
- Invalid token format
- Expired token
- Blacklisted token

### 403 Forbidden

```json
{
  "detail": "Account is deactivated"
}
```

Causes:
- User account disabled
- Insufficient permissions

## Security Features

1. **Token Blacklisting**: Logout invalidates tokens via Redis
2. **Password Hashing**: bcrypt with salt
3. **Rate Limiting**: 5 requests/minute on auth endpoints
4. **Input Validation**: Email format, password strength
5. **HTTPS Required**: Tokens only sent over encrypted connections

## Password Reset Flow

### Request Reset

```http
POST /api/v1/auth/forgot-password
Content-Type: application/json

{
  "email": "user@example.com"
}
```

Response: `200 OK` (always, to prevent email enumeration)

### Confirm Reset

```http
POST /api/v1/auth/reset-password
Content-Type: application/json

{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePassword123!"
}
```

## Code Examples

### Python

```python
import requests

# Login
response = requests.post(
    'http://localhost:8001/api/v1/auth/login',
    json={'email': 'user@example.com', 'password': 'password123'}
)
tokens = response.json()

# Make authenticated request
headers = {'Authorization': f"Bearer {tokens['access_token']}"}
subscriptions = requests.get(
    'http://localhost:8001/api/v1/subscriptions',
    headers=headers
)
```

### JavaScript/TypeScript

```typescript
const login = async (email: string, password: string) => {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  return response.json();
};

const getSubscriptions = async (accessToken: string) => {
  const response = await fetch('/api/v1/subscriptions', {
    headers: { Authorization: `Bearer ${accessToken}` }
  });
  return response.json();
};
```

### cURL

```bash
# Login
ACCESS_TOKEN=$(curl -s -X POST http://localhost:8001/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}' \
  | jq -r '.access_token')

# Use token
curl http://localhost:8001/api/v1/subscriptions \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```
