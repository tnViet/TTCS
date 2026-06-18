"""
AI Service v2 — Quản lý 2 mô hình, dự đoán top 3 và Grad-CAM.

Các module-level singleton được khởi tạo qua init_models(app).
"""
from __future__ import annotations
import io
import json
import os
import uuid

import cv2
import numpy as np
import tensorflow as tf
from PIL import Image


# App chỉ dùng model để inference (predict), không cần compile lại.
# Khi load dùng compile=False để bỏ qua custom loss SparseCategoricalFocalLoss.

# ---------------------------------------------------------------------------
# Hiển thị tên bệnh (8 class + vitiligo đã có trong model)
# ---------------------------------------------------------------------------
CLASS_DISPLAY: dict[str, dict] = {
    "acne_rosacea":      {"vi": "Mụn trứng cá & Đỏ da",  "en": "Acne & Rosacea",      "icon": "🔴"},
    "atopic_dermatitis": {"vi": "Viêm da cơ địa",         "en": "Atopic Dermatitis",    "icon": "🟡"},
    "bullous_disease":   {"vi": "Bệnh bọng nước",         "en": "Bullous Disease",      "icon": "💧"},
    "eczema":            {"vi": "Chàm da",                 "en": "Eczema",               "icon": "🟠"},
    "nail_fungus":       {"vi": "Nấm móng",                "en": "Nail Fungus",          "icon": "💅"},
    "tinea":             {"vi": "Nấm da / Hắc lào",       "en": "Tinea (Ringworm)",     "icon": "🟤"},
    "vitiligo":          {"vi": "Bạch biến",               "en": "Vitiligo",             "icon": "⬜"},
    "warts":             {"vi": "Mụn cóc & Virus da",     "en": "Warts (HPV)",          "icon": "🔵"},
}

# ---------------------------------------------------------------------------
# Singleton storage cho 2 model
# ---------------------------------------------------------------------------
_registry: dict[str, dict] = {}
#  _registry["densenet121"] = {
#      "model":       <keras model>,
#      "grad_model":  <grad-cam sub-model>,
#      "class_names": [...],
#  }

_img_size: tuple[int, int] = (224, 224)
_conf_threshold: float = 0.50



def init_models(app) -> None:
    """Load cả 2 model Keras và build Grad-CAM sub-model."""
    global _img_size, _conf_threshold
    _img_size       = app.config["IMG_SIZE"]
    _conf_threshold = app.config["CONFIDENCE_THRESHOLD"]

  
    tf.config.run_functions_eagerly(True)

    for key, cfg in app.config["MODELS"].items():
        path       = cfg["path"]
        class_json = cfg["class_json"]

        if not os.path.exists(path):
            print(f"[AI] ⚠️  Không tìm thấy model: {path}")
            continue

        with open(class_json, "r", encoding="utf-8") as f:
            class_names = json.load(f)

     
        model = tf.keras.models.load_model(path, compile=False)

    
        gap_layer           = model.get_layer("gap")
        conv_output_tensor  = gap_layer.input   
        grad_model = tf.keras.Model(
            inputs=model.input,
            outputs=[conv_output_tensor, model.output],
        )

        _registry[key] = {
            "model":      model,
            "grad_model": grad_model,
            "class_names": class_names,
            "label":      cfg["label"],
        }
        print(f"[AI] OK  {key} loaded - {len(class_names)} classes - Grad-CAM: gap.input")



def _compute_gradcam(grad_model, img_array: np.ndarray, class_idx: int) -> np.ndarray:
    """Tính Grad-CAM heatmap [0,1] — y hệt notebook."""
    img_tensor = tf.cast(img_array, tf.float32)
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(img_tensor, training=False)
        tape.watch(conv_outputs)   # watch trên conv_output (không phải variable)
        class_channel = predictions[:, class_idx]

    grads         = tape.gradient(class_channel, conv_outputs)
    pooled_grads  = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_out_np   = conv_outputs[0].numpy()
    pooled_np     = pooled_grads.numpy()

    heatmap = np.sum(conv_out_np * pooled_np, axis=-1)
    heatmap = np.maximum(heatmap, 0)
    heatmap = heatmap / (np.max(heatmap) + 1e-8)

    heatmap = cv2.resize(heatmap.astype("float32"), (_img_size[1], _img_size[0]))
    return heatmap


def _overlay_gradcam(img_rgb: np.ndarray, cam: np.ndarray, alpha: float = 0.45) -> np.ndarray:
    heatmap = cv2.applyColorMap(np.uint8(255 * cam), cv2.COLORMAP_JET)
    heatmap = cv2.cvtColor(heatmap, cv2.COLOR_BGR2RGB)
    overlay = heatmap * alpha + img_rgb * (1 - alpha)
    return np.uint8(np.clip(overlay, 0, 255))


def _arr_to_base64(arr: np.ndarray) -> str:
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG", quality=85)
    buf.seek(0)
    import base64
    return "data:image/jpeg;base64," + base64.b64encode(buf.read()).decode()


def _save_image(arr: np.ndarray, folder: str, filename: str) -> str:
    """Lưu ảnh numpy vào folder, trả về đường dẫn tuyệt đối."""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    Image.fromarray(arr).save(path, format="JPEG", quality=90)
    return path


def predict(img_bytes: bytes, model_key: str, upload_originals: str, upload_gradcam: str) -> dict:
    """
    Chạy inference trên raw image bytes.

    Returns:
        results        – Top-3 list [{class_en, class_vi, en_label, icon, confidence}]
        top            – Top-1 dict
        original_b64   – base64 data-URI (hiển thị ngay)
        gradcam_b64    – base64 data-URI
        original_path  – đường dẫn tuyệt đối ảnh gốc (lưu DB)
        gradcam_path   – đường dẫn tuyệt đối ảnh Grad-CAM (lưu DB)
        low_confidence – bool
        model_used     – key của model
    """
    if model_key not in _registry:
        # Fallback sang model đầu tiên có sẵn
        if not _registry:
            raise RuntimeError("Chưa có model nào được tải. Kiểm tra lại đường dẫn model.")
        model_key = next(iter(_registry))

    reg          = _registry[model_key]
    model        = reg["model"]
    grad_model   = reg["grad_model"]
    class_names  = reg["class_names"]

   
    img_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")

   
    orig_w, orig_h = img_pil.size
    max_display = 1600
    if max(orig_w, orig_h) > max_display:
        scale = max_display / max(orig_w, orig_h)
        img_display = img_pil.resize(
            (int(orig_w * scale), int(orig_h * scale)), Image.LANCZOS
        )
    else:
        img_display = img_pil

    img_display_arr = np.array(img_display)          

    # Resize nhỏ xuống 224×224 chỉ để chạy model
    img_resized = np.array(img_pil.resize(_img_size))  
    img_input   = np.expand_dims(img_resized.astype(np.float32), axis=0)

    # Inference
    preds    = model.predict(img_input, verbose=0)[0]
    top_idx  = int(np.argmax(preds))
    top_conf = float(preds[top_idx])
    top_name = class_names[top_idx]
    top_disp = CLASS_DISPLAY.get(top_name, {"vi": top_name, "en": top_name, "icon": "?"})

    # Top 3
    top3: list[dict] = []
    for i in np.argsort(preds)[::-1][:3]:
        name = class_names[i]
        d    = CLASS_DISPLAY.get(name, {"vi": name, "en": name, "icon": "?"})
        top3.append({
            "class_en":    name,
            "class_vi":    d["vi"],
            "en_label":    d["en"],
            "icon":        d["icon"],
            "confidence":  round(float(preds[i]) * 100, 1),
        })

    # Grad-CAM — tính trên 224×224, rồi overlay lên ảnh full-size để rõ hơn
    cam         = _compute_gradcam(grad_model, img_input, top_idx)
    cam_big     = cv2.resize(cam.astype("float32"),
                             (img_display_arr.shape[1], img_display_arr.shape[0]))
    cam_overlay = _overlay_gradcam(img_display_arr, cam_big)


    stem              = uuid.uuid4().hex
    original_filename = f"{stem}_original.jpg"
    gradcam_filename  = f"{stem}_gradcam.jpg"
    original_path     = _save_image(img_display_arr, upload_originals, original_filename)
    gradcam_path      = _save_image(cam_overlay,     upload_gradcam,   gradcam_filename)

    return {
        "results":        top3,
        "top": {
            "class_en":   top_name,
            "class_vi":   top_disp["vi"],
            "en_label":   top_disp["en"],
            "icon":       top_disp["icon"],
            "confidence": round(top_conf * 100, 1),
        },
        "original_b64":   _arr_to_base64(img_display_arr),
        "gradcam_b64":    _arr_to_base64(cam_overlay),
        "original_path":  original_path,
        "gradcam_path":   gradcam_path,
        "low_confidence": top_conf < _conf_threshold,
        "model_used":     model_key,
    }


def get_model_list() -> list[dict]:
    """Trả về danh sách model đã load (cho frontend combo box)."""
    return [
        {"key": k, "label": v["label"]}
        for k, v in _registry.items()
    ]
