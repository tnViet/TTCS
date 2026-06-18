"""
SkinScan v2 — Patient Controller
Routes:
  GET  /              → Trang chủ upload ảnh
  POST /predict       → Chạy AI, lưu DB, trả JSON
  GET  /history       → Trang tra cứu lịch sử
  GET  /api/history   → API JSON lịch sử theo SĐT
  GET  /uploads/<path> → Phục vụ ảnh từ folder ngoài static
"""
from __future__ import annotations
import os

from flask import (
    Blueprint, render_template, request, jsonify,
    current_app, send_file,
)

from models.prediction_model import PredictionModel, DISEASE_LABELS
from services import ai_service

patient_bp = Blueprint("patient", __name__)


# ─────────────────────────────────────────────────────────────────────────────
#  GET /
# ─────────────────────────────────────────────────────────────────────────────
@patient_bp.route("/")
def index():
    models = ai_service.get_model_list()
    return render_template("index.html", models=models)


# ─────────────────────────────────────────────────────────────────────────────
#  POST /predict
# ─────────────────────────────────────────────────────────────────────────────
@patient_bp.route("/predict", methods=["POST"])
def predict():
    full_name    = request.form.get("full_name", "").strip()
    phone_number = request.form.get("phone_number", "").strip()
    model_choice = request.form.get("model_choice", "densenet121").strip()
    file         = request.files.get("file")

    # Validate
    if not full_name:
        return jsonify({"error": "Vui lòng nhập họ và tên."}), 400
    if not phone_number:
        return jsonify({"error": "Vui lòng nhập số điện thoại."}), 400
    if not file or file.filename == "":
        return jsonify({"error": "Chưa chọn ảnh."}), 400
    ext = (file.filename.rsplit(".", 1)[-1] or "").lower()
    if ext not in current_app.config["ALLOWED_EXTENSIONS"]:
        return jsonify({"error": "Định dạng không hỗ trợ. Dùng JPG, PNG hoặc WEBP."}), 400

    # AI inference
    try:
        img_bytes = file.read()
        result    = ai_service.predict(
            img_bytes         = img_bytes,
            model_key         = model_choice,
            upload_originals  = current_app.config["UPLOAD_ORIGINALS"],
            upload_gradcam    = current_app.config["UPLOAD_GRADCAM"],
        )
    except Exception as exc:
        current_app.logger.exception("AI prediction error")
        return jsonify({"error": f"Lỗi phân tích ảnh: {str(exc)}"}), 500

    # Lưu DB
    try:
        pred_id = PredictionModel.create(
            patient_name   = full_name,
            patient_phone  = phone_number,
            image_path     = result["original_path"],
            gradcam_path   = result["gradcam_path"],
            model_used     = result["model_used"],
            top_disease    = result["top"]["class_en"],
            top_confidence = result["top"]["confidence"],
            top3           = result["results"],
            low_confidence = result["low_confidence"],
        )
    except Exception as exc:
        current_app.logger.exception("DB save error")
        pred_id = None

    result["prediction_id"] = pred_id
    # Không trả đường dẫn tuyệt đối về client
    result.pop("original_path", None)
    result.pop("gradcam_path",  None)
    return jsonify(result)


# ─────────────────────────────────────────────────────────────────────────────
#  GET /history — trang tra cứu
# ─────────────────────────────────────────────────────────────────────────────
@patient_bp.route("/history")
def history():
    return render_template("history.html")


# ─────────────────────────────────────────────────────────────────────────────
#  GET /api/history?phone=<phone>
# ─────────────────────────────────────────────────────────────────────────────
@patient_bp.route("/api/history")
def api_history():
    phone = request.args.get("phone", "").strip()
    if not phone:
        return jsonify({"error": "Thiếu số điện thoại."}), 400

    rows = PredictionModel.get_by_phone(phone)
    if not rows:
        return jsonify([])

    records = []
    for r in rows:
        records.append({
            "id":                  r["id"],
            "patient_name":        r["patient_name"],
            "model_used":          r["model_used"],
            "top_disease":         r["top_disease"],
            "top_disease_vi":      _get_vi(r["top_disease"]),
            "top_confidence":      float(r["top_confidence"]),
            "top3":                r.get("top3_json", []),
            "low_confidence":      bool(r["low_confidence"]),
            "image_url":           f"/uploads/{os.path.basename(r['image_path'])}?type=original",
            "gradcam_url":         f"/uploads/{os.path.basename(r['gradcam_path'])}?type=gradcam" if r.get("gradcam_path") else None,
            "created_at":          r.get("created_at_str", ""),
            # Feedback bác sĩ
            "verified_disease":    r.get("verified_disease"),
            "verified_disease_vi": r.get("verified_disease_vi"),
            "doctor_note":         r.get("doctor_note"),
            "reviewed_at":         r.get("reviewed_at_str"),
        })
    return jsonify(records)


# ─────────────────────────────────────────────────────────────────────────────
#  GET /uploads/<filename>?type=original|gradcam
# ─────────────────────────────────────────────────────────────────────────────
@patient_bp.route("/uploads/<filename>")
def serve_upload(filename: str):
    img_type = request.args.get("type", "original")
    if img_type == "gradcam":
        folder = current_app.config["UPLOAD_GRADCAM"]
    else:
        folder = current_app.config["UPLOAD_ORIGINALS"]
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        return "Image not found", 404
    return send_file(path, mimetype="image/jpeg")


def _get_vi(class_en: str) -> str:
    return DISEASE_LABELS.get(class_en, {}).get("vi", class_en)
