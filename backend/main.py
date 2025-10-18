# main.py - Entry point for the Cooking Tutor API
import uvicorn
from api.app import app

if __name__ == "__main__":
    print("🍳 Starting Cooking Tutor API...")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=7860, 
        log_level="info",
        reload=False  # Set to True for development
    )
