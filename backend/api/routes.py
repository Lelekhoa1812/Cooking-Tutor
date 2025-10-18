# api/routes.py
import time
import os
import re
import json
import logging
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse
from .chatbot import CookingTutorChatbot

logger = logging.getLogger("routes")

# Create router
router = APIRouter()

# Initialize cooking tutor chatbot
chatbot = CookingTutorChatbot(
    model_name="gemini-2.5-flash"
)

@router.post("/chat")
async def chat_endpoint(req: Request):
    """Chat endpoint (web-search only). No DB persistence, no image handling."""
    body = await req.json()
    user_id = body.get("user_id", "anonymous")
    query_raw = body.get("query")
    query = query_raw.strip() if isinstance(query_raw, str) else ""
    lang = body.get("lang", "EN")
    search_mode = body.get("search", True)
    video_mode = body.get("video", False)
    # Optional cooking constraints
    servings = body.get("servings")
    dietary = body.get("dietary")  # e.g., ["vegetarian", "gluten-free"]
    allergens = body.get("allergens")  # e.g., ["peanuts", "shellfish"]
    equipment = body.get("equipment")  # e.g., ["oven", "cast iron skillet"]
    time_limit = body.get("time_limit_minutes")  # e.g., 30
    skill_level = body.get("skill_level")  # beginner|intermediate|advanced
    cuisine = body.get("cuisine")  # e.g., "Italian"
    structured = body.get("structured", False)
    
    start = time.time()
    try:
        answer = chatbot.chat(
            user_id,
            query,
            lang,
            search_mode,
            video_mode,
            servings=servings,
            dietary=dietary,
            allergens=allergens,
            equipment=equipment,
            time_limit_minutes=time_limit,
            skill_level=skill_level,
            cuisine=cuisine,
            structured=structured,
        )
        elapsed = time.time() - start
        
        # Handle response format (might be string or dict with videos/images)
        if isinstance(answer, dict):
            response_text = answer.get('text', '')
            video_data = answer.get('videos', [])
            image_data = answer.get('images', [])
        else:
            response_text = answer
            video_data = []
            image_data = []
        
        # Final response
        response_data = {"response": f"{response_text}\n\n(Response time: {elapsed:.2f}s)"}
        
        # Include video data if available
        if video_data:
            response_data["videos"] = video_data
        
        # Include image data if available
        if image_data:
            response_data["images"] = image_data
        
        return JSONResponse(response_data)
        
    except Exception as e:
        logger.error(f"[REQUEST] Error processing request: {e}")
        return JSONResponse({"response": "❌ Failed to get a response. Please try again."})

@router.get("/check-request/{request_id}")
async def check_request_status(request_id: str):
    """Legacy endpoint kept for compatibility; returns not supported."""
    return JSONResponse({"status": "unsupported"})

@router.get("/pending-requests/{user_id}")
async def get_pending_requests(user_id: str):
    """Legacy endpoint kept for compatibility; returns empty list."""
    return JSONResponse({"requests": []})

@router.delete("/cleanup-requests")
async def cleanup_old_requests():
    """Legacy endpoint kept for compatibility; no-op."""
    return JSONResponse({"deleted_count": 0})

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "cooking-tutor"}

@router.get("/")
async def root():
    """Root endpoint - Landing page with redirect to main app"""
    
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cooking Tutor API</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow: hidden;
                position: relative;
            }
            
            /* Animated background particles */
            .particles {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                overflow: hidden;
                z-index: 1;
            }
            
            .particle {
                position: absolute;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 50%;
                animation: float 6s ease-in-out infinite;
            }
            
            .particle:nth-child(1) { width: 80px; height: 80px; top: 20%; left: 10%; animation-delay: 0s; }
            .particle:nth-child(2) { width: 120px; height: 120px; top: 60%; left: 80%; animation-delay: 2s; }
            .particle:nth-child(3) { width: 60px; height: 60px; top: 80%; left: 20%; animation-delay: 4s; }
            .particle:nth-child(4) { width: 100px; height: 100px; top: 10%; left: 70%; animation-delay: 1s; }
            .particle:nth-child(5) { width: 90px; height: 90px; top: 40%; left: 50%; animation-delay: 3s; }
            
            @keyframes float {
                0%, 100% { transform: translateY(0px) rotate(0deg); opacity: 0.7; }
                50% { transform: translateY(-20px) rotate(180deg); opacity: 1; }
            }
            
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 24px;
                padding: 3rem 2rem;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                max-width: 500px;
                width: 90%;
                position: relative;
                z-index: 2;
                animation: slideUp 0.8s ease-out;
            }
            
            @keyframes slideUp {
                from {
                    opacity: 0;
                    transform: translateY(50px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
            
            .logo {
                width: 80px;
                height: 80px;
                background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
                border-radius: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
                margin: 0 auto 1.5rem;
                animation: pulse 2s ease-in-out infinite;
            }
            
            @keyframes pulse {
                0%, 100% { transform: scale(1); }
                50% { transform: scale(1.05); }
            }
            
            .logo i {
                font-size: 2rem;
                color: white;
            }
            
            h1 {
                color: white;
                font-size: 2.5rem;
                font-weight: 700;
                margin-bottom: 0.5rem;
                background: linear-gradient(135deg, #ffffff 0%, #f0f9ff 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
            }
            
            .subtitle {
                color: rgba(255, 255, 255, 0.8);
                font-size: 1.1rem;
                margin-bottom: 2rem;
                font-weight: 400;
            }
            
            .version {
                color: rgba(255, 255, 255, 0.6);
                font-size: 0.9rem;
                margin-bottom: 2rem;
                font-weight: 300;
            }
            
            .redirect-btn {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 1rem 2rem;
                border-radius: 12px;
                font-size: 1.1rem;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 0.5rem;
                box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
                position: relative;
                overflow: hidden;
            }
            
            .redirect-btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                transition: left 0.5s;
            }
            
            .redirect-btn:hover::before {
                left: 100%;
            }
            
            .redirect-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 12px 30px rgba(102, 126, 234, 0.4);
            }
            
            .redirect-btn:active {
                transform: translateY(0);
            }
            
            .redirect-btn i {
                font-size: 1.2rem;
                transition: transform 0.3s ease;
            }
            
            .redirect-btn:hover i {
                transform: translateX(3px);
            }
            
            .features {
                margin-top: 2rem;
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 1rem;
            }
            
            .feature {
                color: rgba(255, 255, 255, 0.7);
                font-size: 0.9rem;
                font-weight: 500;
            }
            
            .feature i {
                display: block;
                font-size: 1.5rem;
                margin-bottom: 0.5rem;
                color: rgba(255, 255, 255, 0.9);
            }
            
            @media (max-width: 768px) {
                .container {
                    padding: 2rem 1.5rem;
                    margin: 1rem;
                }
                
                h1 {
                    font-size: 2rem;
                }
                
                .subtitle {
                    font-size: 1rem;
                }
                
                .redirect-btn {
                    padding: 0.8rem 1.5rem;
                    font-size: 1rem;
                }
            }
        </style>
    </head>
    <body>
        <div class="particles">
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
            <div class="particle"></div>
        </div>
        
        <div class="container">
            <div class="logo">
                <i class="fas fa-utensils"></i>
            </div>
            
            <h1>Cooking Tutor</h1>
            <p class="subtitle">AI-Powered Cooking Lessons & Recipe Guidance</p>
            <p class="version">API Version 1.0.0</p>
            
            <a href="/" class="redirect-btn" target="_blank">
                <i class="fas fa-external-link-alt"></i>
                Open Frontend
            </a>
            
            <div class="features">
                <div class="feature">
                    <i class="fas fa-seedling"></i>
                    Friendly
                </div>
                <div class="feature">
                    <i class="fas fa-list-ol"></i>
                    Step-by-step
                </div>
                <div class="feature">
                    <i class="fas fa-globe"></i>
                    Multi-Language
                </div>
            </div>
        </div>
        
        <script>
            // Add some interactive effects
            document.addEventListener('DOMContentLoaded', function() {
                const btn = document.querySelector('.redirect-btn');
                const particles = document.querySelectorAll('.particle');
                
                // Add click animation
                btn.addEventListener('click', function(e) {
                    // Create ripple effect
                    const ripple = document.createElement('span');
                    const rect = this.getBoundingClientRect();
                    const size = Math.max(rect.width, rect.height);
                    const x = e.clientX - rect.left - size / 2;
                    const y = e.clientY - rect.top - size / 2;
                    
                    ripple.style.cssText = `
                        position: absolute;
                        width: ${size}px;
                        height: ${size}px;
                        left: ${x}px;
                        top: ${y}px;
                        background: rgba(255, 255, 255, 0.3);
                        border-radius: 50%;
                        transform: scale(0);
                        animation: ripple 0.6s ease-out;
                        pointer-events: none;
                    `;
                    
                    this.appendChild(ripple);
                    
                    setTimeout(() => {
                        ripple.remove();
                    }, 600);
                });
                
                // Add CSS for ripple animation
                const style = document.createElement('style');
                style.textContent = `
                    @keyframes ripple {
                        to {
                            transform: scale(2);
                            opacity: 0;
                        }
                    }
                `;
                document.head.appendChild(style);
                
                // Animate particles on mouse move
                document.addEventListener('mousemove', function(e) {
                    const x = e.clientX / window.innerWidth;
                    const y = e.clientY / window.innerHeight;
                    
                    particles.forEach((particle, index) => {
                        const speed = (index + 1) * 0.5;
                        const xOffset = (x - 0.5) * speed * 20;
                        const yOffset = (y - 0.5) * speed * 20;
                        
                        particle.style.transform = `translate(${xOffset}px, ${yOffset}px)`;
                    });
                });
            });
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)
