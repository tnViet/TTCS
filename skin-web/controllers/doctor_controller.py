"""
SkinScan v2 — Doctor Controller
Routes:
  GET  /doctor/login      → Trang đăng nhập
  POST /doctor/login      → Xác thực
  GET  /doctor/logout     → Đăng xuất
  GET  /doctor/dashboard  → Dashboard (cần đăng nhập)
  GET  /doctor/api/cases  → Danh sách ca (JSON, cần đăng nhập)
  POST /doctor/api/review → Lưu phân loại + ghi chú bác sĩ
"""
from __future__ import annotations
import functools
import os

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, session, jsonify, current_app,
)

from models.doctor_model import DoctorModel
from models.prediction_model import PredictionModel, DISEASE_LABELS
from services.auth_service import verify_doctor

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")

# Danh sách 9 enum cho combo box bác sĩ
VERIFIED_DISEASE_CHOICES = [
    ("acne_rosacea",      "Mụn trứng cá & Đỏ da"),
    ("atopic_dermatitis", "Viêm da cơ địa"),
    ("bullous_disease",   "Bệnh bọng nước"),
    ("eczema",            "Chàm da"),
    ("nail_fungus",       "Nấm móng"),
    ("tinea",             "Nấm da / Hắc lào"),
    ("vitiligo",          "Bạch biến"),
    ("warts",             "Mụn cóc & Virus da"),
    ("other",             "Khác (ngoài 8 loại trên)"),
]


# ─────────────────────────────────────────────────────────────────────────────
#  Auth guard
# ─────────────────────────────────────────────────────────────────────────────
def login_required(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("doctor_id"):
            return redirect(url_for("doctor.login"))
        return view(*args, **kwargs)
    return wrapped


# ─────────────────────────────────────────────────────────────────────────────
#  Login / Logout
# ─────────────────────────────────────────────────────────────────────────────
@doctor_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("doctor_id"):
        return redirect(url_for("doctor.dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        doctor   = verify_doctor(username, password)
        if doctor:
            session.clear()
            session["doctor_id"]   = doctor["id"]
            session["doctor_name"] = doctor["full_name"]
            return redirect(url_for("doctor.dashboard"))
        error = "Tên đăng nhập hoặc mật khẩu không đúng."

    return render_template("doctor/login.html", error=error)


@doctor_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("patient.index"))


# ─────────────────────────────────────────────────────────────────────────────
#  Dashboard
# ─────────────────────────────────────────────────────────────────────────────
@doctor_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template(
        "doctor/dashboard.html",
        doctor_name=session.get("doctor_name", "Bác sĩ"),
        disease_choices=VERIFIED_DISEASE_CHOICES,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  API — Danh sách ca (AJAX)
# ─────────────────────────────────────────────────────────────────────────────
@doctor_bp.route("/api/cases")
@login_required
def api_cases():
    rows   = PredictionModel.get_all()
    result = []
    for r in rows:
        result.append({
            "id":                  r["id"],
            "patient_name":        r["patient_name"],
            "patient_phone":       r["patient_phone"],
            "model_used":          r["model_used"],
            "top_disease":         r["top_disease"],
            "top_disease_vi":      DISEASE_LABELS.get(r["top_disease"], {}).get("vi", r["top_disease"]),
            "top_confidence":      float(r["top_confidence"]),
            "top3":                r.get("top3_json", []),
            "low_confidence":      bool(r["low_confidence"]),
            "image_url":           f"/uploads/{os.path.basename(r['image_path'])}?type=original",
            "gradcam_url":         f"/uploads/{os.path.basename(r['gradcam_path'])}?type=gradcam" if r.get("gradcam_path") else None,
            "created_at":          r.get("created_at_str", ""),
            "verified_disease":    r.get("verified_disease"),
            "verified_disease_vi": r.get("verified_disease_vi"),
            "doctor_note":         r.get("doctor_note"),
            "doctor_name":         r.get("doctor_name"),
            "reviewed_at":         r.get("reviewed_at_str"),
        })
    return jsonify(result)


# ─────────────────────────────────────────────────────────────────────────────
#  API — Lưu phân loại + ghi chú bác sĩ (AJAX)
# ─────────────────────────────────────────────────────────────────────────────
@doctor_bp.route("/api/review", methods=["POST"])
@login_required
def api_review():
    data             = request.get_json(force=True)
    pred_id          = data.get("prediction_id")
    verified_disease = (data.get("verified_disease") or "").strip() or None
    doctor_note      = (data.get("doctor_note") or "").strip() or None

    if not pred_id:
        return jsonify({"error": "Thiếu prediction_id"}), 400

    # Validate enum
    valid_keys = [k for k, _ in VERIFIED_DISEASE_CHOICES]
    if verified_disease and verified_disease not in valid_keys:
        return jsonify({"error": "Giá trị verified_disease không hợp lệ"}), 400

    try:
        PredictionModel.update_doctor_review(
            pred_id          = int(pred_id),
            doctor_id        = session["doctor_id"],
            verified_disease = verified_disease,
            doctor_note      = doctor_note,
        )
    except Exception as exc:
        current_app.logger.exception("Doctor review save error")
        return jsonify({"error": str(exc)}), 500

    return jsonify({"ok": True})
