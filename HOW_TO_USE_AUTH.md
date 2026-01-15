# How to Use Authentication Token

This guide explains how to use the JWT authentication token to access protected API endpoints.

## Quick Start

### Step 1: Get Your Token

Login to get an access token:

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin123!"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Copy the `access_token` value.

## Using Token in Swagger UI (API Documentation)

### Method 1: Using the Authorize Button

1. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Open Swagger UI:**
   Navigate to: http://localhost:8000/api/v1/docs

3. **Login first:**
   - Scroll to the `/api/v1/auth/login` endpoint
   - Click "Try it out"
   - Enter credentials:
     - `username`: `admin`
     - `password`: `Admin123!`
   - Click "Execute"
   - Copy the `access_token` from the response

4. **Authorize:**
   - Click the **"Authorize"** button at the top right (🔒 icon)
   - In the popup, paste your token in the "Value" field
   - Leave the "Value" field format as is (no "Bearer" prefix needed, it's added automatically)
   - Click **"Authorize"**
   - Click **"Close"**

5. **Use Protected Endpoints:**
   - Now all protected endpoints will automatically include the token
   - Click "Try it out" on any protected endpoint
   - Click "Execute"
   - The request will be authenticated!

### Method 2: Direct Token Entry

Alternatively, you can manually add the token:

1. Click "Authorize" button
2. In the "HTTPBearer" section, enter your token
3. Click "Authorize"
4. All requests will now include: `Authorization: Bearer <your-token>`

## Using Token with cURL

### Basic Protected Request

```bash
TOKEN="your-token-here"

curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

### Storing Token in Variable

```bash
# Get token and store it
RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin123!")

# Extract token (requires jq or manual extraction)
TOKEN=$(echo $RESPONSE | jq -r '.access_token')

# Use token
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

### Full Example: Login and Access Protected Endpoint

```bash
#!/bin/bash

# Login
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin123!")

# Extract token (without jq, using sed/awk)
TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo "Token: $TOKEN"

# Use token to access protected endpoint
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json"
```

## Using Token in JavaScript/Web Applications

### Fetch API Example

```javascript
// Login function
async function login(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await fetch('http://localhost:8000/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: formData
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Store token in localStorage
    localStorage.setItem('access_token', data.access_token);
    return data.access_token;
  } else {
    throw new Error('Login failed');
  }
}

// Get token from storage
function getToken() {
  return localStorage.getItem('access_token');
}

// Authenticated request
async function getCurrentUser() {
  const token = getToken();
  
  if (!token) {
    throw new Error('No token found. Please login first.');
  }
  
  const response = await fetch('http://localhost:8000/api/v1/users/me', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    }
  });
  
  if (response.status === 401) {
    // Token expired or invalid, redirect to login
    localStorage.removeItem('access_token');
    window.location.href = '/login';
    return;
  }
  
  return await response.json();
}

// Usage
(async () => {
  try {
    // Login
    await login('admin', 'Admin123!');
    
    // Access protected endpoint
    const user = await getCurrentUser();
    console.log('Current user:', user);
  } catch (error) {
    console.error('Error:', error);
  }
})();
```

### Axios Example

```javascript
import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json'
  }
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 errors (token expired)
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Login function
async function login(username, password) {
  const formData = new URLSearchParams();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await api.post('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
  });
  
  localStorage.setItem('access_token', response.data.access_token);
  return response.data;
}

// Authenticated request
async function getCurrentUser() {
  const response = await api.get('/users/me');
  return response.data;
}

// Usage
(async () => {
  try {
    await login('admin', 'Admin123!');
    const user = await getCurrentUser();
    console.log('User:', user);
  } catch (error) {
    console.error('Error:', error);
  }
})();
```

## Using Token in Python

### Requests Library Example

```python
import requests

BASE_URL = "http://localhost:8000/api/v1"

# Login
def login(username: str, password: str) -> str:
    response = requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password}
    )
    response.raise_for_status()
    token = response.json()["access_token"]
    return token

# Authenticated request
def get_current_user(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(
        f"{BASE_URL}/users/me",
        headers=headers
    )
    response.raise_for_status()
    return response.json()

# Usage
if __name__ == "__main__":
    # Login
    token = login("admin", "Admin123!")
    print(f"Token: {token}")
    
    # Access protected endpoint
    user = get_current_user(token)
    print(f"Current user: {user}")
```

### Using Session for Multiple Requests

```python
import requests

class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.session = requests.Session()
        self.token = None
    
    def login(self, username: str, password: str):
        response = self.session.post(
            f"{self.base_url}/auth/login",
            data={"username": username, "password": password}
        )
        response.raise_for_status()
        self.token = response.json()["access_token"]
        # Set token for all future requests
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}"
        })
        return self.token
    
    def get_current_user(self):
        response = self.session.get(f"{self.base_url}/users/me")
        response.raise_for_status()
        return response.json()
    
    def get_users(self):
        response = self.session.get(f"{self.base_url}/users/")
        response.raise_for_status()
        return response.json()

# Usage
client = APIClient()
client.login("admin", "Admin123!")
user = client.get_current_user()
print(user)
```

## Using Token in Postman

1. **Login:**
   - Create a POST request to: `http://localhost:8000/api/v1/auth/login`
   - Go to "Body" tab → select "x-www-form-urlencoded"
   - Add fields:
     - `username`: `admin`
     - `password`: `Admin123!`
   - Send request
   - Copy the `access_token` from response

2. **Use Token:**
   - Create a new request (e.g., GET `/api/v1/users/me`)
   - Go to "Authorization" tab
   - Select type: "Bearer Token"
   - Paste your token in the "Token" field
   - Send request

3. **Set Collection Token (Optional):**
   - Create a Collection
   - Go to Collection → Authorization
   - Select "Bearer Token"
   - Set token variable: `{{token}}`
   - In environment, set `token` = your token value
   - All requests in collection will use this token

## Token Expiration

By default, tokens expire after 8 days (configurable in `.env` as `ACCESS_TOKEN_EXPIRE_MINUTES`).

### Handling Expired Tokens

When a token expires, you'll get a `401 Unauthorized` response:

```json
{
  "detail": "Could not validate credentials"
}
```

Solution: Login again to get a new token.

## Common Issues

### Issue: "Could not validate credentials"

**Causes:**
- Token expired
- Invalid token
- Missing "Bearer" prefix (should be: `Authorization: Bearer <token>`)
- Wrong token

**Solution:**
- Check token is correctly formatted
- Ensure "Bearer " prefix is included
- Try logging in again to get a fresh token

### Issue: "Missing authorization header"

**Causes:**
- Token not sent with request
- Header name is wrong (should be `Authorization`)

**Solution:**
- Ensure header is: `Authorization: Bearer <token>`
- Check token is included in request

### Issue: Token works in Swagger but not in curl/JavaScript

**Causes:**
- Token not properly formatted
- CORS issues (for web apps)

**Solution:**
- Check token format: `Bearer <token>` (with space)
- For web apps, ensure CORS is configured correctly in `.env`

## Testing Your Token

Test if your token is valid:

```bash
TOKEN="your-token-here"

# Test token
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN" \
  -v
```

A successful response (200) means your token is valid!

## Security Best Practices

1. **Never commit tokens to git** - Use `.env` or environment variables
2. **Use HTTPS in production** - Never send tokens over HTTP in production
3. **Store tokens securely** - Use httpOnly cookies or secure storage
4. **Handle token expiration** - Implement automatic refresh or re-login
5. **Don't expose tokens** - Don't log tokens or include them in URLs
6. **Use short expiration times** - Set reasonable token expiration in production

## Example: Complete Authentication Flow

```javascript
// Complete authentication example
class AuthService {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.token = localStorage.getItem('access_token');
  }
  
  async login(username, password) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: formData
    });
    
    if (!response.ok) {
      throw new Error('Login failed');
    }
    
    const data = await response.json();
    this.token = data.access_token;
    localStorage.setItem('access_token', this.token);
    return this.token;
  }
  
  logout() {
    this.token = null;
    localStorage.removeItem('access_token');
  }
  
  async authenticatedFetch(endpoint, options = {}) {
    if (!this.token) {
      throw new Error('Not authenticated');
    }
    
    const headers = {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json',
      ...options.headers
    };
    
    const response = await fetch(`${this.baseURL}${endpoint}`, {
      ...options,
      headers
    });
    
    if (response.status === 401) {
      this.logout();
      window.location.href = '/login';
      throw new Error('Token expired');
    }
    
    return response;
  }
}

// Usage
const auth = new AuthService('http://localhost:8000/api/v1');

// Login
await auth.login('admin', 'Admin123!');

// Make authenticated request
const response = await auth.authenticatedFetch('/users/me');
const user = await response.json();
console.log(user);
```
