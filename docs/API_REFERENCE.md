# 🔧 API Reference - FoodSave AI

## 📋 Overview

The FoodSave AI API is a RESTful service built with FastAPI that provides endpoints for interacting with the multi-agent AI system. The API supports real-time chat, file uploads, RAG operations, weather data, and system monitoring.

## 🔗 Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://api.foodsave-ai.com`

## 📚 API Versioning

The API uses URL-based versioning:
- **v1**: Legacy endpoints (deprecated)
- **v2**: Current stable endpoints (recommended)

## 🔐 Authentication

Currently, the API operates without authentication for development purposes. For production deployment, JWT-based authentication will be implemented.

## 📊 Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": {
    // Response data
  },
  "message": "Operation completed successfully",
  "timestamp": "2024-12-21T10:30:00Z"
}
```

### Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "error description"
    }
  },
  "timestamp": "2024-12-21T10:30:00Z"
}
```

## 🗣️ Chat API

### POST `/api/v1/chat`

Main endpoint for interacting with AI agents.

**Request Body:**
```json
{
  "message": "What can I cook with chicken and rice?",
  "session_id": "user_123_session_456",
  "context": {
    "user_preferences": {
      "diet": "vegetarian",
      "allergies": ["nuts", "shellfish"]
    },
    "available_ingredients": ["chicken", "rice", "onions"]
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "response": "You can make a delicious chicken and rice stir-fry! Here's a recipe...",
    "agent_used": "chef_agent",
    "confidence": 0.95,
    "suggestions": [
      "Add vegetables for more nutrition",
      "Try using brown rice for better health benefits"
    ],
    "session_id": "user_123_session_456"
  },
  "message": "Response generated successfully"
}
```

### POST `/api/v2/chat/stream`

Streaming chat endpoint for real-time responses.

**Request Body:**
```json
{
  "message": "Tell me about sustainable cooking",
  "session_id": "user_123_session_456",
  "stream": true
}
```

**Response:** Server-Sent Events (SSE) stream

## 📤 File Upload API

### POST `/api/v2/upload/receipt`

Upload and process receipt images using OCR.

**Request:** Multipart form data
- `file`: Image file (JPEG, PNG, PDF)
- `session_id`: User session identifier
- `metadata`: Optional JSON metadata

**Response:**
```json
{
  "success": true,
  "data": {
    "receipt_id": "receipt_789",
    "extracted_data": {
      "store": "Walmart",
      "total": 45.67,
      "date": "2024-12-21",
      "items": [
        {
          "name": "Chicken Breast",
          "price": 12.99,
          "quantity": 1
        },
        {
          "name": "Brown Rice",
          "price": 3.49,
          "quantity": 2
        }
      ]
    },
    "confidence": 0.92,
    "processing_time": 1.23
  }
}
```

### POST `/api/v2/upload/document`

Upload documents for RAG processing.

**Request:** Multipart form data
- `file`: Document file (PDF, DOCX, TXT)
- `category`: Document category
- `tags`: Optional tags

**Response:**
```json
{
  "success": true,
  "data": {
    "document_id": "doc_456",
    "title": "Cooking Guide",
    "category": "recipes",
    "tags": ["cooking", "guide"],
    "processing_status": "completed",
    "vectorized": true
  }
}
```

## 🧠 RAG (Retrieval-Augmented Generation) API

### POST `/api/v2/rag/query`

Query the knowledge base using RAG.

**Request Body:**
```json
{
  "query": "How to make pasta carbonara?",
  "filters": {
    "category": "recipes",
    "tags": ["italian", "pasta"]
  },
  "max_results": 5
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "How to make pasta carbonara?",
    "results": [
      {
        "document_id": "doc_123",
        "title": "Classic Carbonara Recipe",
        "content": "Ingredients: spaghetti, eggs, pancetta...",
        "relevance_score": 0.95,
        "source": "cooking_guide.pdf"
      }
    ],
    "generated_answer": "Here's how to make authentic pasta carbonara...",
    "sources": ["doc_123", "doc_456"]
  }
}
```

### GET `/api/v2/rag/documents`

List all documents in the knowledge base.

**Query Parameters:**
- `category`: Filter by category
- `tags`: Filter by tags (comma-separated)
- `limit`: Number of results (default: 20)
- `offset`: Pagination offset

**Response:**
```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "document_id": "doc_123",
        "title": "Cooking Guide",
        "category": "recipes",
        "tags": ["cooking", "guide"],
        "upload_date": "2024-12-21T10:30:00Z",
        "size": 1024000
      }
    ],
    "total": 150,
    "limit": 20,
    "offset": 0
  }
}
```

### DELETE `/api/v2/rag/documents/{document_id}`

Delete a document from the knowledge base.

**Response:**
```json
{
  "success": true,
  "data": {
    "document_id": "doc_123",
    "deleted": true
  },
  "message": "Document deleted successfully"
}
```

## 🌤️ Weather API

### GET `/api/v2/weather/current`

Get current weather information.

**Query Parameters:**
- `location`: City name or coordinates
- `units`: `metric` or `imperial` (default: metric)

**Response:**
```json
{
  "success": true,
  "data": {
    "location": "Warsaw, Poland",
    "temperature": 15.5,
    "feels_like": 13.2,
    "humidity": 65,
    "description": "Partly cloudy",
    "icon": "02d",
    "timestamp": "2024-12-21T10:30:00Z"
  }
}
```

### GET `/api/v2/weather/forecast`

Get weather forecast.

**Query Parameters:**
- `location`: City name or coordinates
- `days`: Number of days (1-7, default: 5)
- `units`: `metric` or `imperial`

**Response:**
```json
{
  "success": true,
  "data": {
    "location": "Warsaw, Poland",
    "forecast": [
      {
        "date": "2024-12-22",
        "temperature": {
          "min": 8.5,
          "max": 16.2
        },
        "description": "Sunny",
        "icon": "01d"
      }
    ]
  }
}
```

## 💾 Backup API

### POST `/api/v2/backup/create`

Create a system backup.

**Request Body:**
```json
{
  "backup_type": "full",
  "description": "Weekly backup",
  "include_data": true,
  "include_config": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "backup_id": "backup_20241221_103000",
    "backup_type": "full",
    "size": 52428800,
    "created_at": "2024-12-21T10:30:00Z",
    "status": "completed"
  }
}
```

### GET `/api/v2/backup/list`

List all available backups.

**Response:**
```json
{
  "success": true,
  "data": {
    "backups": [
      {
        "backup_id": "backup_20241221_103000",
        "backup_type": "full",
        "size": 52428800,
        "created_at": "2024-12-21T10:30:00Z",
        "status": "completed"
      }
    ]
  }
}
```

### POST `/api/v2/backup/restore/{backup_id}`

Restore from a backup.

**Response:**
```json
{
  "success": true,
  "data": {
    "backup_id": "backup_20241221_103000",
    "restored": true,
    "restored_at": "2024-12-21T11:00:00Z"
  }
}
```

## 📊 Monitoring API

### GET `/health`

Basic health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-21T10:30:00Z",
  "version": "2.0.0"
}
```

### GET `/ready`

Readiness check for Kubernetes deployments.

**Response:**
```json
{
  "status": "ready",
  "checks": {
    "database": "healthy",
    "ollama": "healthy",
    "vector_store": "healthy"
  },
  "timestamp": "2024-12-21T10:30:00Z"
}
```

### GET `/metrics`

Prometheus metrics endpoint.

**Response:** Prometheus format metrics

### GET `/api/v1/status`

Detailed system status.

**Response:**
```json
{
  "success": true,
  "data": {
    "system": {
      "status": "healthy",
      "uptime": 86400,
      "version": "2.0.0"
    },
    "agents": {
      "chef_agent": "healthy",
      "weather_agent": "healthy",
      "ocr_agent": "healthy",
      "rag_agent": "healthy"
    },
    "services": {
      "database": "connected",
      "ollama": "running",
      "vector_store": "ready"
    },
    "performance": {
      "memory_usage": 1342177280,
      "cpu_usage": 15.5,
      "active_connections": 5
    }
  }
}
```

### GET `/api/v1/alerts`

Get active system alerts.

**Response:**
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "alert_id": "alert_123",
        "severity": "warning",
        "message": "High memory usage detected",
        "created_at": "2024-12-21T10:25:00Z",
        "resolved": false
      }
    ]
  }
}
```

## 🚨 Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `VALIDATION_ERROR` | Invalid request data | 400 |
| `AUTHENTICATION_ERROR` | Authentication required | 401 |
| `AUTHORIZATION_ERROR` | Insufficient permissions | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |
| `INTERNAL_ERROR` | Server error | 500 |
| `SERVICE_UNAVAILABLE` | Service temporarily unavailable | 503 |

## ⚡ Rate Limiting

- **Chat API**: 100 requests per minute per session
- **Upload API**: 10 requests per minute per session
- **RAG API**: 50 requests per minute per session
- **Weather API**: 60 requests per minute per session

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640087400
```

## 📝 Examples

### Python Example

```python
import requests
import json

# Chat with AI
response = requests.post(
    "http://localhost:8000/api/v1/chat",
    json={
        "message": "What can I cook with chicken?",
        "session_id": "user_123"
    }
)

if response.status_code == 200:
    data = response.json()
    print(f"AI Response: {data['data']['response']}")
```

### JavaScript Example

```javascript
// Chat with AI
const response = await fetch('http://localhost:8000/api/v1/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        message: 'What can I cook with chicken?',
        session_id: 'user_123'
    })
});

const data = await response.json();
console.log(`AI Response: ${data.data.response}`);
```

### cURL Example

```bash
# Chat with AI
curl -X POST "http://localhost:8000/api/v1/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What can I cook with chicken?",
    "session_id": "user_123"
  }'

# Upload receipt
curl -X POST "http://localhost:8000/api/v2/upload/receipt" \
  -F "file=@receipt.jpg" \
  -F "session_id=user_123"
```

## 🔄 WebSocket Support

For real-time communication, WebSocket endpoints are available:

- `ws://localhost:8000/ws/chat` - Real-time chat
- `ws://localhost:8000/ws/status` - System status updates

## 📚 Additional Resources

- [Interactive API Documentation](http://localhost:8000/docs) - Swagger UI
- [Alternative Documentation](http://localhost:8000/redoc) - ReDoc
- [OpenAPI Schema](http://localhost:8000/openapi.json) - OpenAPI specification

---

**Last Updated**: 2024-12-21
**API Version**: 2.0.0
