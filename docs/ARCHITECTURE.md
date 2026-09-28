# FoodLens - Architecture Documentation

## 📐 System Architecture

This document provides a comprehensive overview of the FoodLens system architecture, design decisions, and component interactions.

---

## 🏛️ High-Level Architecture

FoodLens follows a **three-tier architecture** pattern:

```
┌──────────────────────────────────────────────────────────────────┐
│                        Presentation Layer                         │
│  ┌────────────┐  ┌─────────────┐  ┌─────────────────────────┐   │
│  │  Web App   │  │   Chrome    │  │    Mobile Browser       │   │
│  │  (HTML/CSS │  │  Extension  │  │    (Responsive)         │   │
│  │   /JS)     │  │             │  │                         │   │
│  └────────────┘  └─────────────┘  └─────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                        Application Layer                          │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │                    Flask Web Server                        │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │  │
│  │  │   Routing    │  │ Middleware   │  │  Request/Resp   │  │  │
│  │  │   Engine     │  │  (CORS, etc) │  │   Processing    │  │  │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘  │  │
│  │                                                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐  │  │
│  │  │   Predict    │  │   History    │  │   Nutrition     │  │  │
│  │  │   Endpoint   │  │   Endpoint   │  │   Endpoint      │  │  │
│  │  └──────────────┘  └──────────────┘  └─────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
                              │ Function Calls
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                         Business Logic Layer                      │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────────┐   │
│  │   Inference    │  │   TTA Engine   │  │   Warning        │   │
│  │   Engine       │  │                │  │   System         │   │
│  │                │  │                │  │                  │   │
│  │ • Preprocess   │  │ • Base         │  │ • Confidence     │   │
│  │ • Load Model   │  │ • Flip         │  │ • Ambiguity      │   │
│  │ • Predict      │  │ • Crop         │  │ • Unknown        │   │
│  │ • Postprocess  │  │ • Aggregate    │  │ • Alerts         │   │
│  └────────────────┘  └────────────────┘  └──────────────────┘   │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐                         │
│  │   Nutrition    │  │   History      │                         │
│  │   Database     │  │   Manager      │                         │
│  │                │  │                │                         │
│  │ • Calorie      │  │ • Store Scan   │                         │
│  │   Lookup       │  │ • Retrieve     │                         │
│  │ • Ingredients  │  │ • Delete       │                         │
│  │ • Allergens    │  │ • Clear All    │                         │
│  └────────────────┘  └────────────────┘                         │
└──────────────────────────────────────────────────────────────────┘
                              │ File I/O
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                         Data Layer                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │   Model      │  │   Nutrition  │  │   Uploads &          │   │
│  │   Files      │  │   JSON DB    │  │   History Storage    │   │
│  │   (.h5)      │  │              │  │                      │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Design Principles

### 1. Separation of Concerns
Each layer has a distinct responsibility:
- **Presentation:** UI rendering and user interaction
- **Application:** HTTP handling and routing
- **Business Logic:** Core functionality and algorithms
- **Data:** Persistence and storage

### 2. Modularity
Components are loosely coupled and highly cohesive:
- Inference engine is independent of web framework
- TTA logic is isolated in dedicated module
- Nutrition database can be replaced without affecting other components

### 3. Scalability
Architecture supports horizontal scaling:
- Stateless API design enables multiple instances
- Static assets served efficiently
- Model loading optimized for memory usage

### 4. Maintainability
- Clear directory structure
- Comprehensive documentation
- Consistent coding standards
- Extensive error handling

---

## 🔧 Component Details

### Frontend Architecture

#### Technology Stack
- **HTML5:** Semantic markup
- **CSS3:** Custom properties, flexbox, grid
- **JavaScript (ES6+):** Vanilla JS, no frameworks
- **Icons:** Feather Icons (SVG)

#### File Structure
```
webapp/static/
├── css/
│   └── style.css          # All styles (800+ lines)
├── js/
│   └── main.js            # Application logic
└── images/
    └── (brand assets)
```

#### Key Features
- **Single Page Application (SPA) feel:** Smooth transitions between views
- **State Management:** Simple state object with reactive updates
- **Event-Driven:** Event listeners for user interactions
- **Async/Await:** Non-blocking API calls
- **Error Boundaries:** Graceful error handling

#### CSS Architecture
```css
/* Custom Properties (Design Tokens) */
:root {
  --color-primary: #10b981;
  --color-primary-dark: #059669;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.1);
  --radius-lg: 0.5rem;
}

/* Component Classes */
.btn { ... }
.btn--primary { ... }
.btn--large { ... }

/* Utility Classes */
.text-center { ... }
.mt-4 { ... }
```

---

### Backend Architecture

#### Flask Application Structure

```python
# app.py - Main application file

from flask import Flask, render_template, request, jsonify
from inference import predict_food
from nutrition.database import get_nutrition_info

app = Flask(__name__)

# Configuration
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/predict', methods=['POST'])
def api_predict():
    # Validation
    if 'image' not in request.files:
        return jsonify({'error': 'No image provided'}), 400
    
    # Processing
    image = request.files['image']
    result = predict_food(image)
    
    # Enrichment
    nutrition = get_nutrition_info(result['lead_class'])
    result['nutrition'] = nutrition
    
    return jsonify(result)
```

#### Request Flow

```
User Upload → [Flask Route] → [Validation] → [Preprocessing] 
                                           ↓
[Response] ← [Postprocessing] ← [Prediction] ← [Model Inference]
    ↓
[JSON] → [Frontend] → [Display]
```

---

### Deep Learning Pipeline

#### Model Architecture

```
Input (224x224x3)
    ↓
Stem Convolution
    ↓
Multiple MBConv Blocks (EfficientNetB0)
    ↓
Global Average Pooling
    ↓
Dropout (0.2)
    ↓
Dense Layer (101 classes, softmax)
    ↓
Output Probabilities
```

#### Training Pipeline

```python
# src/models/train_model.py

def train_model():
    # 1. Data Loading
    train_data = load_dataset('train')
    val_data = load_dataset('validation')
    
    # 2. Data Augmentation
    datagen = ImageDataGenerator(
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        zoom_range=0.2
    )
    
    # 3. Model Creation
    base_model = EfficientNetB0(
        weights='imagenet',
        include_top=False,
        input_shape=(224, 224, 3)
    )
    
    # Freeze base layers
    base_model.trainable = False
    
    # Add custom head
    x = GlobalAveragePooling2D()(base_model.output)
    x = Dropout(0.2)(x)
    output = Dense(101, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=output)
    
    # 4. Compilation
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    # 5. Training
    history = model.fit(
        datagen.flow(train_data, batch_size=32),
        validation_data=val_data,
        epochs=50,
        callbacks=[
            EarlyStopping(patience=10),
            ReduceLROnPlateau(factor=0.5, patience=5)
        ]
    )
    
    # 6. Save Model
    model.save('models/foodlens_model.h5')
```

#### Inference Pipeline

```python
# inference.py

def predict_food(image_file):
    start_time = time.time()
    
    # 1. Load and preprocess image
    img = load_image(image_file, target_size=(224, 224))
    img_array = img_to_array(img)
    img_array = preprocess_input(img_array)
    
    # 2. Apply Test-Time Augmentation
    predictions = []
    
    # Base prediction
    pred_base = model.predict(img_array[np.newaxis, ...])
    predictions.append(pred_base)
    
    # Horizontal flip
    img_flipped = np.fliplr(img_array)
    pred_flip = model.predict(img_flipped[np.newaxis, ...])
    predictions.append(pred_flip)
    
    # Random crop
    img_cropped = random_crop(img_array, size=200)
    img_cropped = resize(img_cropped, (224, 224))
    pred_crop = model.predict(img_cropped[np.newaxis, ...])
    predictions.append(pred_crop)
    
    # 3. Aggregate predictions
    final_pred = np.mean(predictions, axis=0)
    
    # 4. Extract top 3 predictions
    top_indices = np.argsort(final_pred[0])[::-1][:3]
    predictions_list = []
    
    for idx in top_indices:
        predictions_list.append({
            'class': class_names[idx],
            'confidence': float(final_pred[0][idx]),
            'rank': len(predictions_list) + 1
        })
    
    # 5. Generate warnings
    warnings = generate_warnings(predictions_list)
    
    # 6. Calculate processing time
    processing_time = (time.time() - start_time) * 1000
    
    return {
        'predictions': predictions_list,
        'lead_class': class_names[top_indices[0]],
        'warnings': warnings,
        'processing_time_ms': processing_time
    }
```

---

### Test-Time Augmentation (TTA) System

#### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   TTA Controller                         │
└─────────────────────────────────────────────────────────┘
              │              │              │
              ▼              ▼              ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   Base      │ │   Flip      │ │   Crop      │
    │  Predictor  │ │  Predictor  │ │  Predictor  │
    └─────────────┘ └─────────────┘ └─────────────┘
              │              │              │
              └──────────────┴──────────────┘
                             │
                             ▼
                  ┌───────────────────┐
                  │   Aggregator      │
                  │   (Mean/Majority) │
                  └───────────────────┘
                             │
                             ▼
                  ┌───────────────────┐
                  │  Final Prediction │
                  └───────────────────┘
```

#### Implementation

```python
# src/utils/tta.py

class TTAEngine:
    def __init__(self, model, n_augmentations=3):
        self.model = model
        self.n_augmentations = n_augmentations
    
    def predict(self, image):
        """Apply TTA and return aggregated prediction"""
        augmented_images = self._augment(image)
        predictions = []
        
        for aug_img in augmented_images:
            pred = self.model.predict(aug_img)
            predictions.append(pred)
        
        return self._aggregate(predictions)
    
    def _augment(self, image):
        """Generate augmented versions of input image"""
        augmented = [image]  # Base
        
        # Horizontal flip
        flipped = np.fliplr(image)
        augmented.append(flipped)
        
        # Random crop
        cropped = self._random_crop(image)
        augmented.append(cropped)
        
        return augmented
    
    def _aggregate(self, predictions):
        """Aggregate predictions using mean"""
        return np.mean(predictions, axis=0)
```

---

### Smart Warning System

#### Decision Tree

```
Prediction Received
        │
        ▼
Is top confidence < 0.50?
    ├── Yes → Trigger "Low Confidence" warning
    └── No
        │
        ▼
Is (top_conf - second_conf) < 0.10?
    ├── Yes → Trigger "Ambiguous Prediction" warning
    └── No
        │
        ▼
Are all confidences < 0.30?
    ├── Yes → Suggest "Unknown Food"
    └── No
        │
        ▼
No warnings needed
```

#### Implementation

```python
# src/utils/warnings.py

def generate_warnings(predictions):
    warnings = []
    
    top_conf = predictions[0]['confidence']
    second_conf = predictions[1]['confidence'] if len(predictions) > 1 else 0
    
    # Low confidence warning
    if top_conf < 0.50:
        warnings.append({
            'type': 'low_confidence',
            'message': 'Low confidence prediction. Results may be inaccurate.',
            'severity': 'warning'
        })
    
    # Ambiguous prediction warning
    if (top_conf - second_conf) < 0.10:
        warnings.append({
            'type': 'ambiguous',
            'message': 'Similar alternatives detected. Consider manual verification.',
            'severity': 'info'
        })
    
    # Unknown food alert
    if all(p['confidence'] < 0.30 for p in predictions):
        warnings.append({
            'type': 'unknown',
            'message': 'Food item not recognized. May not be in our database.',
            'severity': 'error'
        })
    
    return warnings
```

---

## 🗄️ Data Architecture

### Nutrition Database Schema

```json
{
  "pizza": {
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
  "hamburger": {
    "calories_per_100g": 295,
    "ingredients": [
      "beef patty",
      "bun",
      "lettuce",
      "tomato",
      "condiments"
    ],
    "allergens": [
      "gluten",
      "soy"
    ]
  }
}
```

### History Storage Format

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
    }
  ]
}
```

---

## 🔐 Security Architecture

### Input Validation Pipeline

```
Image Upload
    ↓
File Type Check (JPG/PNG/JPEG)
    ↓
File Size Check (< 10MB)
    ↓
Image Dimension Validation
    ↓
Content-Type Verification
    ↓
Sanitization
    ↓
Processing
```

### CORS Configuration

```python
from flask_cors import CORS

# Development: Allow all origins
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Production: Restrict to specific domains
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://foodlens.app", "https://www.foodlens.app"],
        "methods": ["GET", "POST", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})
```

---

## 📊 Performance Optimization

### Caching Strategy

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_nutrition_info(food_class):
    """Cache nutrition lookups"""
    return nutrition_db.get(food_class, {})
```

### Model Loading Optimization

```python
# Load model once at startup
model = None

def get_model():
    global model
    if model is None:
        model = load_model('models/foodlens_model.h5')
    return model
```

### Image Preprocessing Pipeline

```python
def optimize_image_upload(image):
    # Resize if too large
    max_dimension = 1024
    if max(image.size) > max_dimension:
        ratio = max_dimension / max(image.size)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)
    
    # Compress quality
    image = image.convert('RGB')
    
    return image
```

---

## 🔄 Deployment Architecture

### Container Structure

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5000

# Run application
CMD ["python", "webapp/app.py"]
```

### Docker Compose Setup

```yaml
version: '3.8'

services:
  webapp:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - ENABLE_TTA=true
    volumes:
      - ./models:/app/models
      - ./uploads:/app/webapp/static/uploads
    restart: unless-stopped
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - webapp
```

---

## 📈 Monitoring Architecture

### Logging Strategy

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
log_handler = RotatingFileHandler(
    'logs/foodlens.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)

log_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

app.logger.addHandler(log_handler)
app.logger.setLevel(logging.INFO)
```

### Metrics Collection

```python
# Track key metrics
metrics = {
    'total_predictions': 0,
    'average_inference_time': 0.0,
    'error_count': 0,
    'warnings_triggered': 0
}

def track_prediction(processing_time, had_warning):
    metrics['total_predictions'] += 1
    metrics['average_inference_time'] = (
        (metrics['average_inference_time'] * (metrics['total_predictions'] - 1) + 
         processing_time) / metrics['total_predictions']
    )
    if had_warning:
        metrics['warnings_triggered'] += 1
```

---

## 🧩 Integration Points

### External Services

| Service | Purpose | Integration Method |
|---------|---------|-------------------|
| Food-101 Dataset | Training data | Download & preprocess |
| USDA Nutrition DB | Nutrition data | Static JSON import |
| Cloud Storage | Model backups | AWS S3 / GCS |
| CDN | Static assets | Cloudflare / AWS CloudFront |

### API Integrations (Future)

- **MyFitnessPal:** Sync nutrition data
- **Google Fit:** Export scan history
- **Apple Health:** HealthKit integration
- **Yelp API:** Restaurant menu matching

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | Sep 2024 | Initial production release |
| 0.9.0 | Aug 2024 | Beta release with TTA |
| 0.8.0 | Jul 2024 | Added smart warnings |
| 0.7.0 | Jun 2024 | Nutrition database integration |
| 0.6.0 | May 2024 | Initial model training |

---

**Document Version:** 1.0.0  
**Last Updated:** September 2024  
**Maintained By:** FoodLens Development Team
