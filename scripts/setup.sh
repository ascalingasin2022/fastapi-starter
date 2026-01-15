#!/bin/bash

echo "🚀 Setting up FastAPI RBAC/ABAC/ReBAC Project..."

# Create necessary directories
mkdir -p app/api/v1/endpoints
mkdir -p app/casbin
mkdir -p app/core
mkdir -p app/db
mkdir -p app/middlewares
mkdir -p app/models
mkdir -p app/schemas
mkdir -p app/services
mkdir -p app/repositories
mkdir -p alembic/versions
mkdir -p scripts
mkdir -p tests

# Create __init__.py files
touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/endpoints/__init__.py
touch app/casbin/__init__.py
touch app/core/__init__.py
touch app/db/__init__.py
touch app/middlewares/__init__.py
touch app/models/__init__.py
touch app/schemas/__init__.py
touch app/services/__init__.py
touch app/repositories/__init__.py

# Copy .env.example to .env if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file from .env.example"
fi

echo "✅ Directory structure created!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Run: docker-compose up -d"
echo "3. Run migrations: docker-compose exec app alembic upgrade head"
echo "4. Access API docs: http://localhost:8000/api/v1/docs"