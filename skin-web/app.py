"""
app.py — Skin Disease Detection Web (Flask)
"""
import os
import json
import tensorflow as tf
import numpy as np
from flask import Flask, render_template, request, jsonify
from PIL import Image
import io
import base64

BASE_DIR    = r"C:\Skin Disease Detection"
MODEL_PATH  = r"C:\Skin Disease Detection\models\best_final.keras"
CLASS_JSON  = r"C:\Skin Disease Detection\models\class_names.json"
IMG_SIZE    = (224, 224)


CLASS_DISPLAY = {
    "acne_rosacea":       {"vi": "Mụn trứng cá & Đỏ da",      "icon": "🔴"},
    "eczema":             {"vi": "Chàm da",                     "icon": "🟠"},
    "atopic_dermatitis":  {"vi": "Viêm da cơ địa",             "icon": "🟡"},
    "psoriasis":          {"vi": "Vảy nến",                     "icon": "🟣"},
    "tinea":              {"vi": "Nấm da / Hắc lào",           "icon": "🟤"},
    "urticaria":          {"vi": "Mề đay",                      "icon": "🩷"},
    "warts":              {"vi": "Mụn cóc & Virus da",          "icon": "🔵"},
    "contact_dermatitis": {"vi": "Viêm da tiếp xúc",           "icon": "🟢"},
    "cellulitis":         {"vi": "Viêm mô tế bào / Chốc lở",  "icon": "⚪"},
    "drug_eruptions":     {"vi": "Phát ban do thuốc",           "icon": "💊"},
    "bullous_disease":    {"vi": "Bệnh bọng nước",             "icon": "💧"},
    "alopecia":           {"vi": "Rụng tóc",                    "icon": "💇"},
    "nail_fungus":        {"vi": "Nấm móng",                    "icon": "💅"},
    "scabies":            {"vi": "Ghẻ / Ký sinh trùng",        "icon": "🔍"},
}

# ============================================================
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max

model = None
CLASS_NAMES = []

def load_model():
    """Load TF model (lazy — chỉ load khi cần)."""
    global model, CLASS_NAMES

    with open(CLASS_JSON, "r", encoding="utf-8") as f:
        CLASS_NAMES = json.load(f)
    print(f"[OK] Loaded {len(CLASS_NAMES)} classes: {CLASS_NAMES}")


    model = tf.keras.models.load_model(MODEL_PATH)
    print(f"[OK] Model loaded: {MODEL_PATH}")

def predict(img_bytes):
    """Nhận bytes ảnh → trả về list predictions."""
    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img_resized = img.resize(IMG_SIZE)
    arr = np.array(img_resized, dtype=np.float32) / 255.0
    arr = np.expand_dims(arr, axis=0)

    preds = model.predict(arr, verbose=0)[0]
    top_indices = np.argsort(preds)[::-1]

    results = []
    for idx in top_indices:
        name = CLASS_NAMES[idx]
        display = CLASS_DISPLAY.get(name, {"vi": name, "icon": "❓"})
        results.append({
            "class_en":    name,
            "class_vi":    display["vi"],
            "icon":        display["icon"],
            "confidence":  round(float(preds[idx]) * 100, 1),
        })
    return results


@app.route("/")
def index():
    return render_template("index.html", classes=CLASS_NAMES, display=CLASS_DISPLAY)

@app.route("/predict", methods=["POST"])
def predict_route():
    if "file" not in request.files:
        return jsonify({"error": "Không tìm thấy file ảnh"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Chưa chọn file"}), 400

    img_bytes = file.read()

    # Tạo base64 preview
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    mime = file.content_type or "image/jpeg"

    results = predict(img_bytes)
    return jsonify({
        "results":  results,
        "preview":  f"data:{mime};base64,{b64}",
        "top":      results[0] if results else None,
    })


@app.route("/health")
def health():
    return jsonify({"status": "ok", "classes": len(CLASS_NAMES)})


if __name__ == "__main__":
    load_model()
    print("\n  Mở trình duyệt: http://localhost:5000\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
