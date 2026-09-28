# FoodLens - API Reference

Complete API documentation for the FoodLens REST API.

## Base URL

**Development:** `http://localhost:5000/api`  
**Production:** `https://api.foodlens.app/v1`

---

## Authentication

Currently, the API is open and does not require authentication. For production deployments, consider implementing API key authentication or OAuth2.

---

## Endpoints

### Health Check

Verify the API is running and healthy.

**Endpoint:** `GET /api/health`

**Request:**
```bash
curl http://localhost:5000/api/health
```

**Response (200 OK):**
```json
{
  "status": "ok"
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "Service unavailable"
}
```

---

### Get Food Classes

Retrieve the list of all supported food classes.

**Endpoint:** `GET /api/classes`

**Request:**
```bash
curl http://localhost:5000/api/classes
```

**Response (200 OK):**
```json
{
  "classes": [
    "apple_pie",
    "baby_back_ribs",
    "bagel",
    "baklava",
    "beef_carpaccio",
    "... (96 more)"
  ],
  "count": 101
}
```

---

### Predict Food

Upload an image and get food predictions with nutrition information.

**Endpoint:** `POST /api/predict`

**Content-Type:** `multipart/form-data`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `image` | File | Yes | Image file (JPG, PNG, JPEG) |

**Request:**
```bash
curl -X POST http://localhost:5000/api/predict \
  -F "image=@pizza.jpg"
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "predictions": [
    {
      "class": "pizza",
      "confidence": 0.8742,
      "rank": 1
    },
    {
      "class": "hamburger",
      "confidence": 0.0821,
      "rank": 2
    },
    {
      "class": "french_fries",
      "confidence": 0.0234,
      "rank": 3
    }
  ],
  "lead_class": "pizza",
  "nutrition": {
    "calories_per_100g": 266,
    "ingredients": [
      "flour",
      "tomato sauce",
      "cheese",
      "toppings"
    ],
    "allergens": [
      "gluten",
      "dairy"
    ]
  },
  "warnings": [],
  "processing_time_ms": 423
}
```

**Error Responses:**

*400 Bad Request - No Image:*
```json
{
  "success": false,
  "error": "No image provided"
}
```

*400 Bad Request - Invalid Format:*
```json
{
  "success": false,
  "error": "Invalid file type. Allowed: png, jpg, jpeg"
}
```

*413 Payload Too Large:*
```json
{
  "success": false,
  "error": "File too large. Maximum size: 10MB"
}
```

*500 Internal Server Error:*
```json
{
  "success": false,
  "error": "Prediction failed. Please try again."
}
```

---

### Get Nutrition Information

Retrieve nutrition data for a specific food class.

**Endpoint:** `GET /api/nutrition/<food_class>`

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `food_class` | String | Yes | Food class name (e.g., "pizza") |

**Request:**
```bash
curl http://localhost:5000/api/nutrition/pizza
```

**Success Response (200 OK):**
```json
{
  "food_class": "pizza",
  "calories_per_100g": 266,
  "ingredients": [
    "flour",
    "tomato sauce",
    "cheese",
    "toppings"
  ],
  "allergens": [
    "gluten",
    "dairy"
  ]
}
```

**Error Response (404 Not Found):**
```json
{
  "error": "Food class not found"
}
```

---

### Get Scan History

Retrieve user's scan history.

**Endpoint:** `GET /api/history`

**Request:**
```bash
curl http://localhost:5000/api/history
```

**Success Response (200 OK):**
```json
{
  "scans": [
    {
      "id": "scan_1727012345",
      "timestamp": "2024-09-22T14:30:00Z",
      "prediction": "pizza",
      "confidence": 0.8742,
      "image_path": "/static/uploads/scan_1727012345.jpg",
      "nutrition": {
        "calories_per_100g": 266
      }
    },
    {
      "id": "scan_1727011000",
      "timestamp": "2024-09-22T14:10:00Z",
      "prediction": "hamburger",
      "confidence": 0.9123,
      "image_path": "/static/uploads/scan_1727011000.jpg",
      "nutrition": {
        "calories_per_100g": 295
      }
    }
  ],
  "count": 2
}
```

---

### Clear Scan History

Delete all scan history.

**Endpoint:** `DELETE /api/history`

**Request:**
```bash
curl -X DELETE http://localhost:5000/api/history
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "History cleared successfully"
}
```

---

## Response Schema

### Prediction Object

```typescript
interface Prediction {
  class: string;           // Food class name
  confidence: number;      // Confidence score (0.0 - 1.0)
  rank: number;            // Ranking (1 = highest confidence)
}
```

### Nutrition Object

```typescript
interface Nutrition {
  calories_per_100g: number;
  ingredients: string[];
  allergens: string[];
}
```

### Warning Object

```typescript
interface Warning {
  type: 'low_confidence' | 'ambiguous' | 'unknown';
  message: string;
  severity: 'info' | 'warning' | 'error';
}
```

### Scan Object

```typescript
interface Scan {
  id: string;              // Unique scan identifier
  timestamp: string;       // ISO 8601 datetime
  prediction: string;      // Lead class name
  confidence: number;      // Confidence score
  image_path: string;      // Path to stored image
  nutrition?: Nutrition;   // Optional nutrition data
}
```

---

## Error Codes

| HTTP Status | Code | Description |
|-------------|------|-------------|
| 200 | OK | Request successful |
| 400 | BAD_REQUEST | Invalid request parameters |
| 404 | NOT_FOUND | Resource not found |
| 413 | PAYLOAD_TOO_LARGE | File exceeds size limit |
| 500 | INTERNAL_ERROR | Server error |

---

## Rate Limiting

For production deployments, implement rate limiting:

- **Free tier:** 100 requests/hour
- **Premium tier:** 1000 requests/hour
- **Enterprise:** Custom limits

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1695398400
```

**429 Too Many Requests:**
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 3600
}
```

---

## CORS

Cross-Origin Resource Sharing is enabled for all endpoints.

**Default Configuration (Development):**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Methods: GET, POST, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type
```

**Production Configuration:**
```
Access-Control-Allow-Origin: https://foodlens.app
Access-Control-Allow-Credentials: true
```

---

## Versioning

API version is included in the URL path for production:

- Current version: `/v1/`
- Previous versions remain available for 12 months

---

## SDKs & Libraries

### JavaScript Example

```javascript
async function predictFood(imageFile) {
  const formData = new FormData();
  formData.append('image', imageFile);
  
  const response = await fetch('http://localhost:5000/api/predict', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  
  if (result.success) {
    console.log('Top prediction:', result.predictions[0]);
    console.log('Nutrition:', result.nutrition);
  } else {
    console.error('Prediction failed:', result.error);
  }
}
```

### Python Example

```python
import requests

def predict_food(image_path):
    files = {'image': open(image_path, 'rb')}
    response = requests.post(
        'http://localhost:5000/api/predict',
        files=files
    )
    
    result = response.json()
    
    if result['success']:
        print(f"Top prediction: {result['predictions'][0]['class']}")
        print(f"Confidence: {result['predictions'][0]['confidence']:.2%}")
        print(f"Calories: {result['nutrition']['calories_per_100g']} per 100g")
    
    return result
```

### cURL Examples

See individual endpoint documentation above for cURL examples.

---

## Changelog

### v1.0.0 (September 2024)
- Initial public release
- Food prediction endpoint
- Nutrition database integration
- Scan history management
- Smart warning system

---

**API Version:** 1.0.0  
**Last Updated:** September 2024  
**Maintained By:** FoodLens Development Team
