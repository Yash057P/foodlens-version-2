"""FoodLens Flask application.

Routes:
  GET  /           -> responsive web UI
  POST /api/predict -> image upload -> {top3, ingredients, warnings}
  GET  /api/classes -> 101-class list
  GET  /api/health  -> heartbeat
"""
import json
import os
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from inference import FoodLensModel

app = Flask(
    __name__,
    static_folder=str(Path(__file__).resolve().parent / "static"),
    template_folder=str(Path(__file__).resolve().parent / "templates"),
)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB

# load model once at startup
lens = FoodLensModel()

@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response



@app.get("/")
def index():
    return send_from_directory(str(app.template_folder), "index.html")


@app.get("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/classes")
def classes():
    return jsonify(lens.class_map)


@app.post("/api/predict")
def predict():
    if "image" not in request.files:
        return jsonify({"status": "error", "message": "No image provided"}), 400
    raw = request.files["image"].read()
    if len(raw) == 0:
        return jsonify({"status": "error", "message": "Empty image"}), 400
    out = lens.predict_bytes(raw)
    return jsonify(out)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "0") == "1")