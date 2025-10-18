# api/config.py
import os
import logging
import psutil
from typing import List

logger = logging.getLogger(__name__)

# ✅ Environment Variables
gemini_flash_api_key = os.getenv("FlashAPI")

# Validate environment endpoint (only when actually running the app)
def validate_environment():
    if not gemini_flash_api_key:
        logger.warning("⚠️ FlashAPI key not set - cooking tutor will use fallback responses")
        # Don't raise error, just warn - app can run with fallback responses

# ✅ Logging Configuration
def setup_logging():
    """Configure logging for the application"""
    # Silence noisy loggers
    for name in [
        "uvicorn.error", "uvicorn.access",
        "fastapi", "starlette",
        "pymongo", "gridfs",
        "sentence_transformers", "faiss",
        "google", "google.auth",
    ]:
        logging.getLogger(name).setLevel(logging.WARNING)
    
    logging.basicConfig(
        level=logging.INFO, 
        format="%(asctime)s — %(name)s — %(levelname)s — %(message)s", 
        force=True
    )
    
    logger = logging.getLogger("cooking-tutor")
    logger.setLevel(logging.DEBUG)
    return logger

# ✅ System Resource Monitoring
def check_system_resources(logger):
    """Monitor system resources and log warnings"""
    memory = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=1)
    disk = psutil.disk_usage("/")
    
    logger.info(f"[System] 🔍 System Resources - RAM: {memory.percent}%, CPU: {cpu}%, Disk: {disk.percent}%")
    
    if memory.percent > 85:
        logger.warning("⚠️ High RAM usage detected!")
    if cpu > 90:
        logger.warning("⚠️ High CPU usage detected!")
    if disk.percent > 90:
        logger.warning("⚠️ High Disk usage detected!")

# ✅ Memory Optimization
def optimize_memory():
    """Set environment variables for memory optimization"""
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

# ✅ CORS Configuration
CORS_ORIGINS = [
    "http://localhost:5173",                    # Vite dev server
    "http://localhost:3000",                    # Another vercel local dev
    "https://cooking-tutor.vercel.app",         # ✅ Vercel frontend production URL
]

# No embedding/RAG models used in cooking tutor
