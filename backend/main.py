# Main entry point - use app/main.py instead
# This file is kept for backwards compatibility
import uvicorn
from app.main import app

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"🚀 Starting server on port {port}")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True
    )