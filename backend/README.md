---
title: Cooking Tutor
emoji: 👨‍🍳
colorFrom: orange
colorTo: red
sdk: docker
sdk_version: latest
pinned: false
license: apache-2.0
short_description: Cooking Tutor WebSearch, Memory, Multilingual
---

# Cooking Tutor Backend

## At-a-glance
Production-grade cooking assistant with web search integration, conversation memory, multilingual support, and comprehensive recipe guidance.

## Key Features

### 🔍 Web Search Integration
- Curated cooking sources (AllRecipes, Food Network, Epicurious, etc.)
- Content extraction and summarization
- Citation mapping with clickable URLs
- Cooking relevance filtering

### 🧠 Memory & Retrieval
- Conversation memory with FAISS indexing
- Semantic chunking and summarization
- Context builder for conversation continuity
- Up to 20 recent summaries per user

### 🌍 Multilingual Support
- Vietnamese and Chinese translation
- Language detection and query enhancement
- Fallback handling for translation failures

### 🍳 Cooking Focus
- Specialized cooking keyword filtering
- Recipe and technique guidance
- Ingredient substitution suggestions
- Cooking time and temperature guidance

## Usage

### Running the Application
```bash
# Using main entry point
python main.py

# Or directly
python api/app.py
```

### Environment Variables
- `FlashAPI` - Gemini API key (required)
- `NVIDIA_URI` - Optional for advanced features
- `NVIDIA_RERANK_ENDPOINT` - Optional reranker endpoint

## API Endpoints

### POST `/chat`
Main chat endpoint with cooking guidance.

**Request Body:**
```json
{
  "query": "How to make perfect pasta?",
  "lang": "EN",
  "search": true,
  "user_id": "unique_user_id",
  "servings": 4,
  "dietary": ["vegetarian"],
  "skill_level": "beginner",
  "structured": true
}
```

**Response:**
```json
{
  "response": "Cooking guidance with citations <URL>",
  "response_time": "2.34s"
}
```

## Search Mode Features

When `search: true`:
1. Search curated cooking sources
2. Extract and summarize relevant content
3. Filter by cooking relevance
4. Provide citations with clickable URLs

## Memory Features

- **Conversation Continuity**: Maintains context across sessions
- **Semantic Chunking**: Groups related cooking topics
- **Usage Tracking**: Prioritizes frequently used information
- **Time Decay**: Recent conversations get higher priority

## Folders Overview
- `api/` - FastAPI app, routes, chatbot orchestration
- `models/` - Summarizer and processing models
- `memory/` - Memory manager and FAISS interfaces
- `search/` - Web search engines and processors
- `utils/` - Translation and utility functions

## Dependencies

See `requirements.txt` for complete list. Key components:
- `google-genai` - Gemini API integration
- `faiss-cpu` - Vector similarity search
- `sentence-transformers` - Text embeddings
- `transformers` - Translation models
- `requests` - Web search functionality
- `beautifulsoup4` - HTML content extraction