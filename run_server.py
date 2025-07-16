#!/usr/bin/env python3
import sys
import os
import uvicorn

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting Truth Engine Server...")
    print("📍 Dashboard: http://127.0.0.1:8000")
    print("📊 Analytics: http://127.0.0.1:8000/analytics")
    print("⏹️  Press Ctrl+C to stop")
    print("-" * 50)
    
    uvicorn.run(
        "webapp.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
