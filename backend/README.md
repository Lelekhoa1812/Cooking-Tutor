---
title: Cooking Tutor
emoji: 👨‍🍳
colorFrom: orange
colorTo: red
sdk: docker
sdk_version: latest
license: apache-2.0
short_description: CookTut with WebSearch, Memory, Multilingual
---

# Cooking Tutor Backend

An intelligent cooking assistant that provides personalized recipe guidance, cooking techniques, and culinary tips with multilingual support (English, Vietnamese, Chinese).

## 🚀 Features

- **Smart Recipe Recommendations**: Get personalized recipes based on available ingredients
- **Multilingual Support**: English, Vietnamese (Tiếng Việt), and Chinese (中文)
- **Cooking Techniques**: Step-by-step guidance for various cooking methods
- **Ingredient Substitutions**: Smart suggestions for ingredient alternatives
- **Dietary Accommodations**: Support for various dietary preferences and restrictions
- **Web Search Integration**: Real-time cooking information from trusted sources
- **Memory System**: Contextual conversation continuity

## 🛠️ Technical Stack

- **Backend**: FastAPI with Python 3.9+
- **AI Models**: Google Gemini Flash API
- **Memory**: FAISS + Sentence Transformers for semantic search
- **Translation**: HuggingFace Transformers (VietAI/envit5-translation, Helsinki-NLP/opus-mt-zh-en)
- **Web Search**: DuckDuckGo + specialized cooking engines
- **Deployment**: Docker container on HuggingFace Spaces

## 🏃‍♂️ Quick Start

The API is automatically deployed and running on HuggingFace Spaces. You can interact with it through the web interface or API endpoints.

### API Endpoints

- `GET /` - Health check
- `POST /chat` - Main chat endpoint
- `GET /health` - System health status

### Example Usage

```python
import requests

# Chat with the cooking tutor
response = requests.post("https://your-space-url.hf.space/chat", json={
    "user_id": "user123",
    "query": "How do I make perfect pasta?",
    "lang": "EN"
})

print(response.json())
```

## 🌍 Multilingual Support

The cooking tutor supports three languages:

- **English (EN)**: Full feature support
- **Vietnamese (VI)**: Complete Vietnamese language support
- **Chinese (ZH)**: Simplified Chinese support

## 🔧 Environment Variables

Required environment variables for deployment:

```bash
FlashAPI=your_gemini_api_key
```

## 📚 API Documentation

### Chat Endpoint

**POST** `/chat`

Request body:
```json
{
    "user_id": "string",
    "query": "string",
    "lang": "EN|VI|ZH",
    "search_mode": true,
    "video_mode": false,
    "servings": 4,
    "dietary": ["vegetarian"],
    "allergens": ["nuts"],
    "equipment": ["oven", "stovetop"],
    "time_limit_minutes": 30,
    "skill_level": "beginner|intermediate|advanced",
    "cuisine": "italian",
    "structured": false
}
```

Response:
```json
{
    "response": "string",
    "videos": [
        {
            "title": "string",
            "url": "string",
            "thumbnail": "string",
            "source": "string"
        }
    ]
}
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI        │    │   AI Models     │
│   (Vercel)      │◄──►│   Backend        │◄──►│   (Gemini)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Search &       │
                       │   Memory         │
                       │   Systems        │
                       └──────────────────┘
```

## 🔍 Search & Memory

- **Web Search**: Real-time cooking information from multiple sources
- **Memory Management**: Short-term and long-term memory for conversation context
- **Content Processing**: Advanced content extraction and summarization
- **Citation System**: Proper source attribution with inline citations

## 🚀 Deployment

This space is configured for Docker deployment on HuggingFace Spaces:

- **Port**: 7860
- **Base Image**: Python 3.9
- **Auto-deploy**: Enabled on push to main branch

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

## 📞 Support

For support or questions, please open an issue in the repository.