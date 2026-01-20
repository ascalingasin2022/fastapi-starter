#!/bin/bash

# Database seeding script runner
# This script helps initialize the database with users

echo "🌱 Database Seeding Script"
echo "=========================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Please create one with: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "   Creating from .env.example..."
    cp .env.example .env
    echo "   Please edit .env with your database settings!"
fi

# Run the initialization script
echo "🚀 Initializing database..."
echo ""

python scripts/init_db.py

echo ""
echo "✅ Done!"
echo ""
echo "💡 Next steps:"
echo "   1. Start the API: uvicorn app.main:app --reload"
echo "   2. Test login: curl -X POST http://localhost:8000/api/v1/auth/login -d 'username=admin&password=Admin123!'"
echo "   3. Access docs: http://localhost:8000/api/v1/docs"
