# Backend API Endpoints Documentation

This document catalogs all the Python/FastAPI endpoints that our COSMIC application needs to interact with.

## Chat Endpoints

### POST /api/chat
- **Description**: Send a chat message and receive a response
- **Request Body**:
  ```json
  {
    "prompt": "User message here",
    "model": "optional_model_name"
  }
  ```
- **Response**: Streaming text response
- **Notes**: Returns a streaming response with chunks of text

### POST /api/memory_chat
- **Description**: Chat with memory/context preservation
- **Request Body**:
  ```json
  {
    "message": "User message here",
    "session_id": "unique_session_identifier",
    "usePerplexity": false,
    "useBielik": true,
    "agent_states": {}
  }
  ```
- **Response**: Streaming NDJSON with text chunks
- **Notes**: Maintains conversation history based on session_id

## Pantry Endpoints

### GET /api/pantry/products
- **Description**: Get all products in the pantry
- **Response**: 
  ```json
  [
    {
      "id": 1,
      "name": "Product Name",
      "unified_category": "Category"
    }
  ]
  ```

## OCR Endpoints

### POST /api/ocr
- **Description**: Upload receipt image for OCR processing
- **Request**: Multipart form with file field named "file"
- **Response**:
  ```json
  {
    "items": [
      {
        "name": "Item name",
        "quantity": 1.0,
        "price": 10.5,
        "category": "Category"
      }
    ],
    "total": 10.5,
    "store_name": "Store Name",
    "date": "2023-01-01"
  }
  ```

## Weather Endpoints

### GET /api/weather
- **Description**: Get current weather data
- **Response**:
  ```json
  {
    "temperature": 25.0,
    "description": "Sunny",
    "humidity": 60,
    "wind_speed": 5.0,
    "location": "City Name"
  }
  ```

## Data Mapping

### Python to Rust Type Mapping

| Python Type | Rust Type |
|-------------|-----------|
| str | String |
| int | i32 or i64 |
| float | f32 or f64 |
| bool | bool |
| List[T] | Vec<T> |
| Dict[K, V] | HashMap<K, V> |
| Optional[T] | Option<T> |
| datetime | chrono::DateTime<Utc> |

## Implementation Notes

1. All endpoints use JSON for request/response unless specified otherwise
2. Authentication is not yet implemented but will be added in future iterations
3. Error responses follow standard HTTP status codes
4. Streaming responses use text/plain or application/x-ndjson content types 