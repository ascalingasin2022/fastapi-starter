# Database Setup Guide

This guide will help you set up the database with initial users and RBAC policies.

## Quick Start

### Step 1: Ensure PostgreSQL is Running

**Option A: Using Docker (Recommended)**
```bash
docker-compose up -d db
```

**Option B: Local PostgreSQL**
Make sure PostgreSQL is running locally on port 5432.

### Step 2: Configure Environment

Copy and edit the `.env` file:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

### Step 3: Initialize Database

**Option A: Using the shell script (Easiest)**
```bash
./scripts/run_seed.sh
```

**Option B: Using Python directly**
```bash
source venv/bin/activate
python scripts/init_db.py
```

## What Gets Created

### Users Created

1. **Admin User**
   - Email: `admin@example.com`
   - Username: `admin`
   - Password: `Admin123!`
   - Role: Admin
   - Attributes: IT department, Level 10, HQ location
   - Permissions: Full access (read/write/delete users, manage roles, manage permissions)

2. **Manager User**
   - Email: `manager@example.com`
   - Username: `manager`
   - Password: `Manager123!`
   - Role: Manager
   - Attributes: Engineering department, Level 7, US location
   - Permissions: Read/write users, read roles

3. **Regular User**
   - Email: `user@example.com`
   - Username: `user`
   - Password: `User123!`
   - Role: User
   - Attributes: Engineering department, Level 5, US location
   - Permissions: Read/write own profile

### Roles Created

- `admin` - Full administrative access
- `manager` - Managerial access
- `user` - Regular user access
- `moderator` - Content moderation access

### Casbin Policies Created

The script sets up RBAC policies in Casbin:
- Admin can manage users, roles, and permissions
- Manager can read/write users and read roles
- User can manage their own profile
- Moderator can manage content

## Testing the Setup

### 1. Login as Admin

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=Admin123!"
```

Response:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 2. Access Protected Endpoint

```bash
TOKEN="your-token-here"

curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN"
```

### 3. Check User Roles

```bash
curl -X GET "http://localhost:8000/api/v1/rbac/roles/user/admin" \
  -H "Authorization: Bearer $TOKEN"
```

## Manual Database Access

### Connect to PostgreSQL

**Using Docker:**
```bash
docker-compose exec db psql -U postgres -d fastapi_db
```

**Using local PostgreSQL:**
```bash
psql -U postgres -d fastapi_db
```

### View Users

```sql
SELECT id, email, username, is_active, is_superuser, department, level 
FROM users;
```

### View Roles

```sql
SELECT * FROM roles;
```

### View User-Role Assignments

```sql
SELECT u.email, r.name as role
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id;
```

### View Casbin Policies

```sql
SELECT * FROM casbin_rule ORDER BY ptype, v0;
```

## Resetting the Database

If you need to start fresh:

### Option 1: Drop and Recreate (Docker)

```bash
docker-compose down -v
docker-compose up -d db
# Wait a few seconds for DB to be ready
python scripts/init_db.py
```

### Option 2: Drop Schema Manually

```sql
-- Connect to PostgreSQL
DROP SCHEMA public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO public;
```

Then run the init script again:
```bash
python scripts/init_db.py
```

## Troubleshooting

### Database Connection Error

1. Check PostgreSQL is running:
   ```bash
   docker-compose ps  # For Docker
   # or
   sudo systemctl status postgresql  # For local
   ```

2. Verify `.env` file has correct database settings:
   ```env
   POSTGRES_SERVER=localhost  # or 'db' for Docker
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=fastapi_db
   ```

3. Test connection:
   ```bash
   docker-compose exec db psql -U postgres -d fastapi_db -c "SELECT 1;"
   ```

### Users Already Exist Error

If you see errors about existing users, the script will skip creating duplicates. If you want to recreate everything:

1. Drop the database tables
2. Run the init script again

### Casbin Initialization Errors

If Casbin fails to initialize:
1. Make sure PostgreSQL is accessible
2. Check the Casbin model files exist in `app/casbin/`
3. Verify the database connection string in `.env`

## Next Steps

1. Start the API server:
   ```bash
   source venv/bin/activate
   uvicorn app.main:app --reload
   ```

2. Access API documentation:
   - Swagger UI: http://localhost:8000/api/v1/docs
   - ReDoc: http://localhost:8000/api/v1/redoc

3. Test authentication and authorization with the created users!
