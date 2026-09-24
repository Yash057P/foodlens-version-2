# FoodLens - Troubleshooting Guide

Common issues and solutions for FoodLens users and developers.

---

## 🔍 Quick Diagnostics

### Is the Application Running?

```bash
# Check if Flask server is running
curl http://localhost:5000/api/health

# Expected response: {"status": "ok"}
```

### Is the Model Loaded?

```bash
# Test prediction endpoint
curl -X POST http://localhost:5000/api/predict \
  -F "image=@test_image.jpg"

# If model not loaded, you'll get a 500 error
```

### Check Logs

```bash
# View application logs
tail -f webapp/foodlens.log

# Or check console output if running in foreground
```

---

## 🚨 Common Issues

### Issue 1: "No module named 'tensorflow'"

**Symptoms:**
```
ModuleNotFoundError: No module named 'tensorflow'
```

**Solution:**
```bash
# Activate virtual environment first
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import tensorflow; print(tensorflow.__version__)"
```

---

### Issue 2: Model File Not Found

**Symptoms:**
```
OSError: Unable to load model file 'models/foodlens_model.h5'
FileNotFoundError: [Errno 2] No such file or directory
```

**Solution:**
```bash
# Check if model file exists
ls -la models/

# If missing, you need to:
# Option 1: Download pre-trained model
wget <model-url> -O models/foodlens_model.h5

# Option 2: Train your own model
python src/models/train_model.py

# Verify file permissions
chmod 644 models/foodlens_model.h5
```

---

### Issue 3: CUDA/GPU Errors

**Symptoms:**
```
Could not load dynamic library 'libcudart.so'
Failed to get convolution algorithm
```

**Solution:**

**Option A: Use CPU-only mode**
```python
# Set environment variable before importing TensorFlow
import os
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
import tensorflow as tf
```

**Option B: Install GPU support properly**
```bash
# Check CUDA installation
nvcc --version
nvidia-smi

# Install correct TensorFlow version with GPU support
pip install tensorflow==2.13.0

# Verify GPU detection
python -c "import tensorflow as tf; print(tf.config.list_physical_devices('GPU'))"
```

---

### Issue 4: Memory Error During Inference

**Symptoms:**
```
ResourceExhaustedError: OOM when allocating tensor
MemoryError: Unable to allocate array
```

**Solution:**

```python
# Reduce image size before processing
from PIL import Image

def optimize_image(image_path, max_size=1024):
    img = Image.open(image_path)
    if max(img.size) > max_size:
        ratio = max_size / max(img.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    return img

# Clear TensorFlow session periodically
import tensorflow as tf
tf.keras.backend.clear_session()

# Reduce batch size if processing multiple images
batch_size = 1  # Instead of 32
```

---

### Issue 5: Slow Prediction Times

**Symptoms:**
- Predictions taking >5 seconds
- High CPU usage during inference

**Solution:**

```bash
# Disable TTA for faster results (reduces accuracy slightly)
export ENABLE_TTA=false

# Or modify in code
# inference.py
USE_TTA = False  # Change from True to False

# Optimize model
python scripts/export_model.py --optimize

# Use GPU if available
nvidia-smi  # Check GPU availability
```

---

### Issue 6: CORS Errors in Browser

**Symptoms:**
```
Access to fetch at 'http://localhost:5000/api/predict' from origin 'null' 
has been blocked by CORS policy
```

**Solution:**

```python
# webapp/app.py - Ensure CORS is enabled
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# For production, restrict origins
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com"],
        "methods": ["GET", "POST", "DELETE"],
        "allow_headers": ["Content-Type"]
    }
})
```

---

### Issue 7: Image Upload Fails

**Symptoms:**
```
400 Bad Request: No image provided
413 Payload Too Large
```

**Solution:**

```python
# Check file size limits in app.py
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB

# Verify allowed extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Client-side: Compress image before upload
const compressImage = async (file, maxSize = 1024) => {
  // Compression logic here
};
```

---

### Issue 8: Low Prediction Accuracy

**Symptoms:**
- Consistent misclassifications
- Very low confidence scores (<30%)

**Solution:**

**Improve Input Quality:**
- Use well-lit photos
- Center the food item
- Avoid mixed dishes
- Take photos from above (45° angle)

**Technical Solutions:**
```python
# Enable TTA for better accuracy
ENABLE_TTA = True

# Fine-tune model on domain-specific data
python src/models/train_model.py --fine-tune --data custom_dataset/

# Check class distribution
python scripts/analyze_results.py --show-confusion-matrix
```

---

### Issue 9: History Not Saving

**Symptoms:**
- Scan history empty after predictions
- Previous scans disappear

**Solution:**

```python
# Check write permissions on uploads folder
ls -la webapp/static/uploads/
chmod 755 webapp/static/uploads/

# Verify history file exists and is writable
ls -la webapp/data/history.json
chmod 644 webapp/data/history.json

# Check disk space
df -h

# Review history saving logic
# webapp/app.py - ensure history is being saved after each prediction
```

---

### Issue 10: Dark Mode Not Working

**Symptoms:**
- Theme toggle doesn't change appearance
- Dark mode preference not persisting

**Solution:**

```javascript
// Check localStorage in browser console
console.log(localStorage.getItem('theme'));

// Manually set theme
localStorage.setItem('theme', 'dark');
location.reload();

// Verify CSS variables are defined
// webapp/static/css/style.css
:root[data-theme="dark"] {
  --bg-primary: #1a1a2e;
  /* ... other dark theme variables */
}

// Check JavaScript event listener
// webapp/static/js/main.js
themeToggle.addEventListener('click', () => {
  // Toggle logic should be here
});
```

---

## 🔧 Development Issues

### Issue: Tests Failing

```bash
# Run tests with verbose output
pytest tests/ -v --tb=long

# Common fixes:
# 1. Install test dependencies
pip install pytest pytest-cov pytest-mock

# 2. Check test data exists
ls -la tests/fixtures/

# 3. Run specific test
pytest tests/test_api.py::test_predict_endpoint -v

# 4. Check for import errors
python -m pytest --import-mode=importlib
```

---

### Issue: Docker Build Fails

```bash
# Common Docker issues and solutions:

# Issue: Out of disk space during build
docker system prune -a
docker builder prune

# Issue: Dependency installation fails
# Check requirements.txt for version conflicts
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# Issue: Port already in use
# Change port in docker-compose.yml
ports:
  - "5001:5000"  # Use 5001 instead of 5000
```

---

### Issue: Chrome Extension Not Loading

**Symptoms:**
- Extension shows error in chrome://extensions
- Side panel doesn't open

**Solution:**

1. **Check manifest.json version**
```json
{
  "manifest_version": 3,
  "name": "FoodLens",
  // ... rest of manifest
}
```

2. **Verify permissions**
```json
"permissions": [
  "activeTab",
  "sidePanel",
  "storage"
]
```

3. **Reload extension**
   - Go to `chrome://extensions`
   - Enable "Developer mode"
   - Click refresh icon on FoodLens extension

4. **Check console for errors**
   - Right-click extension icon → "Inspect popup"
   - Check Console tab for errors

---

## 📊 Performance Issues

### Monitoring Performance

```python
# Add performance monitoring
import time
from functools import wraps

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end-start:.3f}s")
        return result
    return wrapper

@timing_decorator
def predict_food(image):
    # Existing prediction logic
    pass
```

### Profiling Memory Usage

```python
import tracemalloc

tracemalloc.start()

# Run your code
predict_food(image)

current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.2f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.2f} MB")
tracemalloc.stop()
```

---

## 🆘 Getting Help

### Before Asking for Help

1. ✅ Check this troubleshooting guide
2. ✅ Search existing GitHub issues
3. ✅ Review error messages carefully
4. ✅ Try suggested solutions
5. ✅ Gather system information

### When Reporting Issues

Include:
- Operating system and version
- Python version (`python --version`)
- TensorFlow version (`python -c "import tensorflow; print(tensorflow.__version__)"`)
- Steps to reproduce
- Error messages (full traceback)
- What you've tried

### Contact Channels

- **GitHub Issues:** For bugs and feature requests
- **Discussions:** For questions and community help
- **Documentation:** Check all docs in `/docs` folder

---

## 📝 Maintenance Tips

### Regular Maintenance Tasks

```bash
# Weekly: Clean up old uploads
find webapp/static/uploads -mtime +7 -delete

# Monthly: Update dependencies
pip list --outdated
pip install --upgrade tensorflow flask pillow

# Quarterly: Review and rotate logs
mv foodlens.log foodlens.log.old
touch foodlens.log

# Yearly: Retrain model with new data
python src/models/train_model.py --retrain
```

### Backup Strategy

```bash
#!/bin/bash
# backup.sh - Run weekly

BACKUP_DIR="/backups/foodlens_$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Backup model
cp models/foodlens_model.h5 $BACKUP_DIR/

# Backup nutrition database
cp src/nutrition/database.json $BACKUP_DIR/

# Backup history (if important)
cp webapp/data/history.json $BACKUP_DIR/

# Compress backup
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "Backup completed: $BACKUP_DIR.tar.gz"
```

---

**Document Version:** 1.0.0  
**Last Updated:** September 2024  
**Maintained By:** FoodLens Development Team
