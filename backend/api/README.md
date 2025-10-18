# API Module Structure - Cooking Tutor

## 📁 **Module Overview**

### **config.py** - Configuration Management
- Environment variables validation
- Logging configuration
- System resource monitoring
- Memory optimization settings
- CORS configuration

### **retrieval.py** - Web Search Integration
- Cooking information retrieval via web search
- Recipe suggestion system
- Smart content filtering and relevance scoring
- Web search result processing

### **chatbot.py** - Core Chatbot Logic
- CookingTutorChatbot class
- Gemini API client
- Web search integration
- Citation processing
- Memory management integration

### **routes.py** - API Endpoints
- `/chat` - Main chat endpoint
- `/health` - Health check
- `/` - Root endpoint with landing page
- Request/response handling

### **app.py** - Main Application
- FastAPI app initialization
- Middleware configuration
- Route registration
- Server startup

## 🔄 **Data Flow**

```
Request → routes.py → chatbot.py → search.py (web search)
                ↓
         memory.py (context) + utils/ (translation)
                ↓
         models/ (summarization processing)
                ↓
         Response with citations
```

## 🚀 **Benefits of Modular Structure**

1. **Separation of Concerns**: Each module has a single responsibility
2. **Easier Testing**: Individual modules can be tested in isolation
3. **Better Maintainability**: Changes to one module don't affect others
4. **Improved Readability**: Smaller files are easier to understand
5. **Reusability**: Modules can be imported and used elsewhere
6. **Scalability**: Easy to add new features without affecting existing code

## 📊 **File Sizes**

| File | Lines | Purpose |
|------|-------|---------|
| **app.py** | 50 | Main app initialization |
| **config.py** | 68 | Configuration |
| **retrieval.py** | 156 | Web search integration |
| **chatbot.py** | 203 | Chatbot logic |
| **routes.py** | 435 | API endpoints |

## 🔧 **Usage**

The modular structure maintains clean API interface:

```python
# All imports work the same way
from api.app import app
from api.chatbot import CookingTutorChatbot
from api.retrieval import retrieval_engine
```

## 🛠 **Development Benefits**

- **Easier Debugging**: Issues can be isolated to specific modules
- **Parallel Development**: Multiple developers can work on different modules
- **Code Reviews**: Smaller files are easier to review
- **Documentation**: Each module can have focused documentation
- **Testing**: Unit tests can be written for each module independently