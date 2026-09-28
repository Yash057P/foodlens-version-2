# FoodLens - Developer Guide

Comprehensive guide for developers working on the FoodLens project.

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)
- Git
- Node.js 16+ (optional, for frontend tooling)

### Installation

```bash
# Clone the repository
git clone https://github.com/foodlens/foodlens.git
cd foodlens

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Verify installation
python scripts/verify_installation.py

# Run the application
cd webapp
python app.py
```

Visit `http://localhost:5000` in your browser.

---

## 📁 Project Structure

```
foodlens/
├── src/                      # Source code
│   ├── data/                 # Data processing
│   ├── models/               # Model definitions & training
│   ├── utils/                # Utility functions
│   └── nutrition/            # Nutrition database
│
├── webapp/                   # Web application
│   ├── app.py                # Flask application
│   ├── inference.py          # Inference logic
│   ├── static/               # Static assets
│   └── templates/            # HTML templates
│
├── scripts/                  # Operational scripts
├── tests/                    # Test suite
├── docs/                     # Documentation
└── docker/                   # Docker configuration
```

---

## 🛠️ Development Workflow

### Setting Up Development Environment

```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black flake8 mypy pylint

# Configure pre-commit hooks (optional)
pip install pre-commit
pre-commit install
```

### Code Style Guidelines

#### Python (PEP 8)

```python
# Good
def predict_food(image_file):
    """Predict food class from image."""
    if not image_file:
        raise ValueError("Image file is required")
    
    predictions = model.predict(image_file)
    return format_predictions(predictions)


# Bad
def PredictFood(ImageFile):
    if not ImageFile:
        raise ValueError("image file is required")
    predictions=model.predict(ImageFile)
    return predictions
```

#### JavaScript (ES6+)

```javascript
// Good
const predictFood = async (imageFile) => {
  try {
    const formData = new FormData();
    formData.append('image', imageFile);
    
    const response = await fetch('/api/predict', {
      method: 'POST',
      body: formData
    });
    
    return await response.json();
  } catch (error) {
    console.error('Prediction failed:', error);
    throw error;
  }
};

// Bad
function predictFood(imageFile) {
  var formData = new FormData();
  formData.append('image', imageFile);
  fetch('/api/predict', {method: 'POST', body: formData})
    .then(function(response) {return response.json();});
}
```

#### CSS (BEM Methodology)

```css
/* Good */
.food-card { }
.food-card__image { }
.food-card__title { }
.food-card__title--highlighted { }
.food-card:hover .food-card__image { }

/* Bad */
.foodCard { }
.foodCardImage { }
.foodCardTitle { }
.foodCard .foodCardImage { }
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=src --cov-report=html

# Run specific test file
pytest tests/test_api.py -v

# Run tests matching pattern
pytest -k "test_predict" -v
```

### Code Formatting

```bash
# Format Python code
black src/ webapp/ scripts/

# Sort imports
isort src/ webapp/ scripts/

# Lint code
flake8 src/ webapp/ scripts/
pylint src/

# Type checking
mypy src/
```

---

## 🔧 Common Development Tasks

### Adding a New API Endpoint

1. **Define the route in `webapp/app.py`:**

```python
@app.route('/api/v2/new-endpoint', methods=['POST'])
def new_endpoint():
    """Description of endpoint functionality."""
    # Validate input
    if 'required_field' not in request.json:
        return jsonify({'error': 'Missing required field'}), 400
    
    # Process request
    result = process_data(request.json)
    
    # Return response
    return jsonify({
        'success': True,
        'data': result
    }), 200
```

2. **Add tests in `tests/test_api.py`:**

```python
def test_new_endpoint():
    response = client.post('/api/v2/new-endpoint', json={})
    assert response.status_code == 400
    
    response = client.post('/api/v2/new-endpoint', 
                          json={'required_field': 'value'})
    assert response.status_code == 200
```

3. **Update API documentation in `docs/API_REFERENCE.md`**

### Adding a New Food Class

1. **Prepare dataset images** for the new class

2. **Update data loading script:**

```python
# src/data/create_dataset.py
CLASSES = [
    'existing_class_1',
    'existing_class_2',
    'new_food_class',  # Add here
]
```

3. **Retrain the model:**

```bash
python src/models/train_model.py --include-new-classes
```

4. **Add nutrition information:**

```python
# src/nutrition/database.py
NUTRITION_DB['new_food_class'] = {
    'calories_per_100g': 150,
    'ingredients': ['ingredient1', 'ingredient2'],
    'allergens': ['allergen1']
}
```

5. **Update frontend class list** if displayed to users

### Modifying the Model Architecture

```python
# src/models/create_model.py

def create_model(num_classes=101, dropout_rate=0.2):
    """Create EfficientNetB0 model with custom head."""
    
    # Load base model
    base_model = EfficientNetB0(
        weights='imagenet',
        include_top=False,
        input_shape=(224, 224, 3)
    )
    
    # Freeze base layers (optional)
    base_model.trainable = False
    
    # Build custom head
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = Dropout(dropout_rate)(x)
    x = Dense(256, activation='relu')(x)  # Added dense layer
    x = BatchNormalization()(x)           # Added batch norm
    output = Dense(num_classes, activation='softmax')(x)
    
    model = Model(inputs=base_model.input, outputs=output)
    
    return model
```

### Customizing TTA Strategy

```python
# src/utils/tta.py

class CustomTTAEngine(TTAEngine):
    def _augment(self, image):
        """Custom augmentation strategy."""
        augmented = [image]  # Base
        
        # Add rotation
        rotated = rotate_image(image, angle=15)
        augmented.append(rotated)
        
        # Add brightness adjustment
        brighter = adjust_brightness(image, factor=1.2)
        augmented.append(brighter)
        
        return augmented
```

---

## 🐛 Debugging Tips

### Common Issues and Solutions

#### Issue: Model Not Loading

```python
# Debug steps
import tensorflow as tf
print(f"TensorFlow version: {tf.__version__}")

try:
    model = load_model('models/foodlens_model.h5')
    print("Model loaded successfully")
except Exception as e:
    print(f"Error loading model: {e}")
    # Check file exists
    import os
    print(f"Model file exists: {os.path.exists('models/foodlens_model.h5')}")
```

#### Issue: Slow Inference

```python
# Profile inference time
import time
import cProfile

@cProfile.Profile()
def profile_inference():
    start = time.time()
    result = predict_food(image)
    end = time.time()
    print(f"Inference took: {end - start:.3f}s")
    return result
```

#### Issue: Memory Leaks

```python
# Monitor memory usage
import tracemalloc
from tensorflow import keras

tracemalloc.start()

# Run inference multiple times
for i in range(100):
    predict_food(image)
    keras.backend.clear_session()  # Clear session

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory: {current / 1024 / 1024:.2f} MB")
print(f"Peak memory: {peak / 1024 / 1024:.2f} MB")
tracemalloc.stop()
```

### Logging Best Practices

```python
import logging

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

# Use in code
def predict_food(image_file):
    logger.debug(f"Processing image: {image_file.filename}")
    
    try:
        result = model.predict(image_file)
        logger.info(f"Prediction successful: {result['lead_class']}")
        return result
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}", exc_info=True)
        raise
```

---

## 📊 Performance Optimization

### Optimizing Inference

```python
# Enable mixed precision for GPU
from tensorflow.keras import mixed_precision

mixed_precision.set_global_policy('mixed_float16')

# Optimize model for inference
optimized_model = tf.function(
    model.call,
    input_signature=[tf.TensorSpec(shape=[None, 224, 224, 3], dtype=tf.float32)]
)
```

### Caching Strategies

```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=128)
def get_cached_prediction(image_hash):
    """Cache predictions by image hash."""
    return model.predict_by_hash(image_hash)

def predict_with_cache(image):
    image_hash = hashlib.md5(image.tobytes()).hexdigest()
    return get_cached_prediction(image_hash)
```

### Batch Processing

```python
def batch_predict(images, batch_size=32):
    """Process multiple images in batches."""
    results = []
    
    for i in range(0, len(images), batch_size):
        batch = images[i:i + batch_size]
        batch_predictions = model.predict(batch)
        results.extend(batch_predictions)
    
    return results
```

---

## 🧪 Testing Guidelines

### Unit Tests

```python
# tests/test_inference.py

import pytest
from src.utils.image_processing import preprocess_image

def test_preprocess_image_valid():
    image = create_test_image(224, 224)
    processed = preprocess_image(image)
    
    assert processed.shape == (224, 224, 3)
    assert processed.dtype == np.float32
    assert 0 <= processed.min() <= 1
    assert 0 <= processed.max() <= 1

def test_preprocess_image_invalid_size():
    image = create_test_image(100, 100)
    
    with pytest.raises(ValueError):
        preprocess_image(image, require_size=(224, 224))
```

### Integration Tests

```python
# tests/test_api.py

import pytest

def test_predict_endpoint(client, test_image):
    response = client.post(
        '/api/predict',
        data={'image': test_image},
        content_type='multipart/form-data'
    )
    
    assert response.status_code == 200
    data = response.get_json()
    
    assert data['success'] is True
    assert 'predictions' in data
    assert len(data['predictions']) == 3
    assert 'nutrition' in data
```

### End-to-End Tests

```python
# tests/e2e/test_workflow.py

def test_full_prediction_workflow(browser):
    # Navigate to app
    browser.get('http://localhost:5000')
    
    # Upload image
    upload_element = browser.find_element(By.ID, 'upload-zone')
    upload_element.send_keys('test_images/pizza.jpg')
    
    # Wait for results
    WebDriverWait(browser, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, 'prediction-result'))
    )
    
    # Verify results displayed
    results = browser.find_elements(By.CLASS_NAME, 'prediction-result')
    assert len(results) >= 1
```

---

## 📦 Building for Production

### Environment Configuration

```python
# config.py

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE', 10)) * 1024 * 1024
    ENABLE_TTA = os.environ.get('ENABLE_TTA', 'true').lower() == 'true'
    MODEL_PATH = os.environ.get('MODEL_PATH', 'models/foodlens_model.h5')

class ProductionConfig(Config):
    DEBUG = False
    ENV = 'production'
    
class DevelopmentConfig(Config):
    DEBUG = True
    ENV = 'development'
```

### Docker Build

```dockerfile
# docker/Dockerfile

FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment variables
ENV FLASK_ENV=production
ENV ENABLE_TTA=true

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "webapp.app:app"]
```

### CI/CD Pipeline Example

```yaml
# .github/workflows/ci.yml

name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      run: pytest tests/ -v --cov=src
    
    - name: Lint code
      run: |
        flake8 src/ webapp/
        black --check src/ webapp/
  
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to production
      run: |
        # Deployment commands here
        echo "Deploying to production..."
```

---

## 📚 Additional Resources

### Internal Documentation
- [Architecture Guide](ARCHITECTURE.md)
- [API Reference](API_REFERENCE.md)
- [Model Card](MODEL_CARD.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)

### External Resources
- [Flask Documentation](https://flask.palletsprojects.com/)
- [TensorFlow Guide](https://www.tensorflow.org/guide)
- [EfficientNet Paper](https://arxiv.org/abs/1905.11946)
- [Food-101 Dataset](https://data.vision.ee.ethz.ch/cvl/food-101/)

### Community
- GitHub Discussions
- Stack Overflow (tag: foodlens)
- Discord community (link TBD)

---

## 🤝 Contributing

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure they pass
5. Format code (`black`, `flake8`)
6. Commit with conventional commits
7. Push to your fork
8. Open a Pull Request

### Commit Message Format

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

**Example:**
```
feat(model): add support for batch prediction

Implement batch processing for multiple images to improve throughput.

Closes #123
```

---

**Guide Version:** 1.0.0  
**Last Updated:** September 2024  
**Maintained By:** FoodLens Development Team
