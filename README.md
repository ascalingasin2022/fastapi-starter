# FastAPI RBAC/ABAC/ReBAC Implementation Guide

Complete implementation of Role-Based Access Control (RBAC), Attribute-Based Access Control (ABAC), and Relationship-Based Access Control (ReBAC) using Casbin, PostgreSQL, and Docker.

## 🎯 Features

- **RBAC (Role-Based Access Control)**: Users are assigned roles, and roles have permissions
- **ABAC (Attribute-Based Access Control)**: Access control based on user attributes (department, level, location)
- **ReBAC (Relationship-Based Access Control)**: Access control based on resource relationships
- **Casbin Integration**: Powerful authorization library supporting all three models
- **PostgreSQL**: Reliable database for storing policies and user data
- **Docker**: Containerized deployment for easy setup
- **Redis**: Caching and session management
- **JWT Authentication**: Secure token-based authentication
- **FastAPI**: Modern, fast Python web framework

## 📁 Project Structure

```
.
├── app/
│   ├── api/v1/endpoints/
│   │   ├── auth.py           # Authentication endpoints
│   │   └── rbac.py           # RBAC management endpoints
│   ├── casbin/
│   │   ├── rbac_model.conf   # RBAC model configuration
│   │   ├── abac_model.conf   # ABAC model configuration
│   │   ├── rebac_model.conf  # ReBAC model configuration
│   │   └── rbac_policy.csv   # Initial RBAC policies
│   ├── core/
│   │   ├── config.py         # Application configuration
│   │   ├── security.py       # Security utilities
│   │   └── casbin_enforcer.py # Casbin enforcer setup
│   ├── db/
│   │   ├── base_class.py     # SQLAlchemy base
│   │   └── session.py        # Database session
│   ├── middlewares/
│   │   └── auth_middleware.py # Authorization middleware
│   ├── models/
│   │   └── user.py           # User, Role, Permission models
│   └── schemas/
│       ├── auth.py           # Authentication schemas
│       └── rbac.py           # RBAC schemas
├── alembic/
│   └── versions/
│       └── 001_initial_migration.py
├── docker-compose.yml
├── Dockerfile
├── main.py
├── requirements.txt
└── .env.example
```

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/ascalingasin2022/fastapi-starter
cd fastapi-starter

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Copy environment file
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file with your settings:

```env
SECRET_KEY=your-super-secret-key-min-32-characters
POSTGRES_PASSWORD=your-secure-password
```

### 3. Start Services with Docker

```bash
# Build and start all services
docker-compose up -d

# Check services status
docker-compose ps

# View logs
docker-compose logs -f app
```

### 4. Run Database Migrations

```bash
# Run migrations
docker-compose exec app alembic upgrade head

# Or manually create tables (the app does this on startup)
```

### 5. Access the Application

- **API Documentation**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 📚 Usage Guide

### Authentication

#### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "username": "admin",
    "password": "StrongPassword123!",
    "full_name": "Admin User",
    "department": "IT",
    "level": 5,
    "location": "HQ"
  }'
```

#### 2. Login

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=StrongPassword123!"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### RBAC Operations

#### Assign Role to User

```bash
curl -X POST "http://localhost:8000/api/v1/rbac/roles/assign" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "role": "admin"
  }'
```

#### Get User Roles

```bash
curl -X GET "http://localhost:8000/api/v1/rbac/roles/user/admin" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

#### Assign Permission to Role

```bash
curl -X POST "http://localhost:8000/api/v1/rbac/permissions/assign" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role": "editor",
    "resource": "/api/v1/documents",
    "action": "POST"
  }'
```

#### Check Permission

```bash
curl -X POST "http://localhost:8000/api/v1/rbac/check-permission" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "resource": "/api/v1/users",
    "action": "GET"
  }'
```

## 🔐 Access Control Models

### RBAC (Role-Based Access Control)

Users are assigned roles, and permissions are granted to roles.

**Example Flow:**
1. Create role: `admin`
2. Assign permissions to role: `admin` can `GET`, `POST`, `PUT`, `DELETE` on `/api/v1/users`
3. Assign role to user: User `alice` gets role `admin`
4. User `alice` now has all admin permissions

**Model Configuration** (`rbac_model.conf`):
```ini
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
```

### ABAC (Attribute-Based Access Control)

Access is granted based on user attributes like department, level, or location.

**Example Rules:**
- Users with `level >= 3` can access sensitive documents
- Users in `department == "Finance"` can access financial reports
- Users at `location == "HQ"` can approve requests

**Model Configuration** (`abac_model.conf`):
```ini
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub_rule, obj, act

[matchers]
m = eval(p.sub_rule) && r.obj == p.obj && r.act == p.act
```

### ReBAC (Relationship-Based Access Control)

Access is based on relationships between users and resources.

**Example Scenarios:**
- Owner of a document can edit it
- Members of a team can view team resources
- Parent resources inherit permissions to child resources

**Model Configuration** (`rebac_model.conf`):
```ini
[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _
g2 = _, _

[matchers]
m = g(r.sub, p.sub) && g2(r.obj, p.obj) && r.act == p.act
```

## 🛠️ Development

### Local Development (without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start PostgreSQL and Redis locally
# Update .env with local connection strings

# Run migrations
alembic upgrade head

# Start the application
python main.py
```

### Adding New Endpoints with Authorization

```python
from fastapi import APIRouter, Request
from app.middlewares.auth_middleware import require_rbac_permission

router = APIRouter()

@router.get("/protected-resource")
@require_rbac_permission("/api/v1/protected-resource", "GET")
async def get_protected_resource(request: Request):
    """Only users with proper RBAC permissions can access this"""
    user = request.state.user
    return {"message": f"Hello {user['sub']}"}
```

### Using Different Authorization Models

```python
from app.middlewares.auth_middleware import (
    require_rbac_permission,
    require_abac_permission,
    require_rebac_permission
)

# RBAC
@require_rbac_permission("/api/v1/users", "GET")
async def rbac_endpoint(request: Request):
    pass

# ABAC
@require_abac_permission("/api/v1/sensitive", "GET")
async def abac_endpoint(request: Request):
    pass

# ReBAC
@require_rebac_permission("/api/v1/documents/123", "GET")
async def rebac_endpoint(request: Request):
    pass
```

## 🧪 Testing

### Manual Testing with Swagger UI

1. Go to http://localhost:8000/api/v1/docs
2. Register a user via `/api/v1/auth/register`
3. Login via `/api/v1/auth/login` to get token
4. Click "Authorize" and enter: `Bearer YOUR_TOKEN`
5. Test protected endpoints

### Database Management

```bash
# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d fastapi_db

# List tables
\dt

# View Casbin rules
SELECT * FROM casbin_rbac_rule;

# View users
SELECT * FROM users;
```

### Redis Management

```bash
# Access Redis CLI
docker-compose exec redis redis-cli

# List all keys
KEYS *

# Get value
GET key_name
```

## 📊 Database Schema

### Main Tables

- `users`: User accounts with attributes for ABAC
- `roles`: Role definitions
- `permissions`: Role-permission mappings
- `user_roles`: User-role associations
- `resource_relationships`: Resource relationships for ReBAC
- `casbin_rbac_rule`: RBAC policies
- `casbin_abac_rule`: ABAC policies
- `casbin_rebac_rule`: ReBAC policies

## 🔧 Troubleshooting

### Container Issues

```bash
# Restart all services
docker-compose restart

# Rebuild containers
docker-compose down
docker-compose up --build -d

# View container logs
docker-compose logs -f app
docker-compose logs -f postgres
```

### Database Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d
docker-compose exec app alembic upgrade head
```

### Permission Denied

If you get permission errors, make sure:
1. User has proper role assigned
2. Role has required permissions
3. Token is valid and not expired
4. Authorization header is correctly formatted

## 📝 Best Practices

1. **Security**:
   - Change `SECRET_KEY` in production
   - Use strong passwords
   - Enable HTTPS in production
   - Rotate JWT tokens regularly

2. **RBAC**:
   - Use meaningful role names
   - Follow principle of least privilege
   - Regularly audit role assignments

3. **ABAC**:
   - Keep attribute rules simple
   - Document attribute meanings
   - Validate attribute values

4. **ReBAC**:
   - Model relationships carefully
   - Consider inheritance hierarchies
   - Test complex relationship chains

## 🚢 Production Deployment

### Environment Variables

Set these in production:
```env
SECRET_KEY=<generate-strong-32+-char-key>
POSTGRES_PASSWORD=<strong-database-password>
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
```

### Docker Production Build

```bash
# Build optimized image
docker build -t fastapi-rbac:prod .

# Run with production settings
docker run -p 8000:8000 --env-file .env.prod fastapi-rbac:prod
```

## 📖 Additional Resources

- [Casbin Documentation](https://casbin.org/docs/overview)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- Casbin for the authorization library
- PostgreSQL and Redis communities