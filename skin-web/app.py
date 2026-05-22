
import os
import json
import base64
import io
import numpy as np
import cv2
import tensorflow as tf
from flask import Flask, render_template, request, jsonify
from PIL import Image

BASE_DIR    = r"C:\Skin Disease Detection"
MODEL_PATH  = r"models\best_final.keras"
CLASS_JSON  = r"models\class_names.json"
IMG_SIZE    = (224, 224)
CONFIDENCE_THRESHOLD = 0.60

CLASS_DISPLAY = {
    "acne_rosacea":       {"vi": "Mụn trứng cá & Đỏ da",     "icon": "🔴"},
    "eczema":             {"vi": "Chàm da",                    "icon": "🟠"},
    "atopic_dermatitis":  {"vi": "Viêm da cơ địa",            "icon": "🟡"},
    "tinea":              {"vi": "Nấm da / Hắc lào",          "icon": "🟤"},
    "urticaria":          {"vi": "Mề đay",                     "icon": "🩷"},
    "warts":              {"vi": "Mụn cóc & Virus da",         "icon": "🔵"},
    "bullous_disease":    {"vi": "Bệnh bọng nước",            "icon": "💧"},
    "alopecia":           {"vi": "Rụng tóc",                   "icon": "💇"},
    "nail_fungus":        {"vi": "Nấm móng",                   "icon": "💅"},
    "scabies":            {"vi": "Ghẻ / Ký sinh trùng",       "icon": "🔍"},
    "drug_eruptions":     {"vi": "Phát ban do thuốc",          "icon": "💊"},
}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

model      = None
CLASS_NAMES = []
grad_model  = None   


def load_model():
    global model, CLASS_NAMES, grad_model

    with open(CLASS_JSON, "r", encoding="utf-8") as f:
        CLASS_NAMES = json.load(f)
    print(f"[OK] {len(CLASS_NAMES)} classes: {CLASS_NAMES}")

    model = tf.keras.models.load_model(MODEL_PATH)
    print(f"[OK] Model loaded: {MODEL_PATH}")


    last_conv  = model.get_layer("top_conv")
    grad_model = tf.keras.Model(
        inputs=model.inputs,
        outputs=[last_conv.output, model.output]
    )
    print("[OK] Grad-CAM model ready")



def compute_gradcam(img_array, class_idx):
    """
    img_array: shape (1, 224, 224, 3), float32, range 0-255
    Trả về: heatmap (224, 224), float [0,1]
    """
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_array, training=False)
        class_score = predictions[:, class_idx]

    grads   = tape.gradient(class_score, conv_outputs)
    weights = tf.reduce_mean(grads, axis=(0, 1, 2))
    cam     = tf.reduce_sum(conv_outputs[0] * weights, axis=-1)
    cam     = tf.nn.relu(cam).numpy()
    cam     = cv2.resize(cam, (224, 224))
    cam     = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
    return cam


def overlay_gradcam(original_img_array, cam, alpha=0.4):
    """
    original_img_array: (224, 224, 3) uint8
    cam: (224, 224) float [0,1]
    Trả về: (224, 224, 3) uint8 overlay
    """
    heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    overlay = heatmap * alpha + original_img_array * (1 - alpha)
    return np.uint8(np.clip(overlay, 0, 255))


def numpy_to_base64(img_array):
    """Chuyển numpy array (H,W,3) uint8 → base64 string để hiển thị trên web."""
    img_pil = Image.fromarray(img_array)
    buf = io.BytesIO()
    img_pil.save(buf, format="PNG")
    buf.seek(0)
    return "data:image/png;base64," + base64.b64encode(buf.read()).decode("utf-8")



def predict(img_bytes):
    # Load ảnh gốc (giữ 0-255 cho Grad-CAM và hiển thị)
    img_pil     = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img_resized = np.array(img_pil.resize(IMG_SIZE))          # uint8 0-255
    img_input   = np.expand_dims(img_resized.astype(np.float32), axis=0)

    # Predict
    preds      = model.predict(img_input, verbose=0)[0]
    top_idx    = int(np.argmax(preds))
    top_conf   = float(preds[top_idx])
    top_name   = CLASS_NAMES[top_idx]
    display    = CLASS_DISPLAY.get(top_name, {"vi": top_name, "icon": "❓"})

  
    top5 = []
    for i in np.argsort(preds)[::-1][:5]:
        name = CLASS_NAMES[i]
        d    = CLASS_DISPLAY.get(name, {"vi": name, "icon": "❓"})
        top5.append({
            "class_en":   name,
            "class_vi":   d["vi"],
            "icon":       d["icon"],
            "confidence": round(float(preds[i]) * 100, 1),
        })

    # Grad-CAM
    cam         = compute_gradcam(img_input, top_idx)
    cam_overlay = overlay_gradcam(img_resized, cam)

    # Chuyển ảnh sang base64
    original_b64 = numpy_to_base64(img_resized)
    gradcam_b64  = numpy_to_base64(cam_overlay)

    return {
        "results":    top5,
        "top": {
            "class_en":   top_name,
            "class_vi":   display["vi"],
            "icon":       display["icon"],
            "confidence": round(top_conf * 100, 1),
        },
        "original_img": original_b64,
        "gradcam_img":  gradcam_b64,
        "low_confidence": top_conf < CONFIDENCE_THRESHOLD,
    }



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

    result = predict(file.read())
    return jsonify(result)


@app.route("/health")
def health():
    return jsonify({"status": "ok", "classes": len(CLASS_NAMES)})


if __name__ == "__main__":
    load_model()
    print("\n  Mở trình duyệt: http://localhost:5000\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
