"""
Prediction Model — CRUD cho bảng predictions (schema v2).
Bảng này chứa cả thông tin bệnh nhân lẫn feedback bác sĩ.
"""
from __future__ import annotations
import json
from .database import get_db


DISEASE_LABELS = {
    "acne_rosacea":      {"vi": "Mụn trứng cá & Đỏ da",  "en": "Acne & Rosacea"},
    "atopic_dermatitis": {"vi": "Viêm da cơ địa",         "en": "Atopic Dermatitis"},
    "bullous_disease":   {"vi": "Bệnh bọng nước",         "en": "Bullous Disease"},
    "eczema":            {"vi": "Chàm da",                 "en": "Eczema"},
    "nail_fungus":       {"vi": "Nấm móng",                "en": "Nail Fungus"},
    "tinea":             {"vi": "Nấm da / Hắc lào",       "en": "Tinea (Ringworm)"},
    "vitiligo":          {"vi": "Bạch biến",               "en": "Vitiligo"},
    "warts":             {"vi": "Mụn cóc & Virus da",     "en": "Warts (HPV)"},
    "other":             {"vi": "Khác",                    "en": "Other"},
}


class PredictionModel:

    @staticmethod
    def create(
        patient_name: str,
        patient_phone: str,
        image_path: str,
        gradcam_path: str,
        model_used: str,
        top_disease: str,
        top_confidence: float,
        top3: list,
        low_confidence: bool,
    ) -> int:
        """Tạo bản ghi dự đoán mới, trả về ID."""
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                """
                INSERT INTO predictions
                  (patient_name, patient_phone, image_path, gradcam_path,
                   model_used, top_disease, top_confidence, top3_json, low_confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    patient_name,
                    patient_phone,
                    image_path,
                    gradcam_path,
                    model_used,
                    top_disease,
                    round(float(top_confidence), 2),
                    json.dumps(top3, ensure_ascii=False),
                    int(low_confidence),
                ),
            )
            return cur.lastrowid

    @staticmethod
    def get_by_phone(phone: str) -> list[dict]:
        """Lấy tất cả dự đoán theo SĐT bệnh nhân (mới nhất trước)."""
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                """
                SELECT * FROM predictions
                WHERE patient_phone = %s
                ORDER BY created_at DESC
                """,
                (phone,),
            )
            rows = cur.fetchall()
        return [_parse_row(r) for r in rows]

    @staticmethod
    def get_all() -> list[dict]:
        """Lấy tất cả dự đoán (cho dashboard bác sĩ), mới nhất trước."""
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                """
                SELECT p.*, d.full_name AS doctor_name
                FROM predictions p
                LEFT JOIN doctors d ON d.id = p.doctor_id
                ORDER BY p.created_at DESC
                """
            )
            rows = cur.fetchall()
        return [_parse_row(r) for r in rows]

    @staticmethod
    def get_by_id(pred_id: int) -> dict | None:
        """Lấy một bản ghi theo ID."""
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                "SELECT * FROM predictions WHERE id = %s",
                (pred_id,),
            )
            row = cur.fetchone()
        return _parse_row(row) if row else None

    @staticmethod
    def update_doctor_review(
        pred_id: int,
        doctor_id: int,
        verified_disease: str | None,
        doctor_note: str | None,
    ) -> None:
        """Cập nhật phân loại và ghi chú của bác sĩ."""
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                """
                UPDATE predictions
                SET verified_disease = %s,
                    doctor_note      = %s,
                    doctor_id        = %s,
                    reviewed_at      = NOW()
                WHERE id = %s
                """,
                (verified_disease or None, doctor_note or None, doctor_id, pred_id),
            )


def _parse_row(r: dict) -> dict:
    """Parse JSON field và chuẩn hóa kiểu dữ liệu."""
    if r is None:
        return r
    if isinstance(r.get("top3_json"), str):
        r["top3_json"] = json.loads(r["top3_json"])
    if r.get("created_at"):
        r["created_at_str"] = r["created_at"].strftime("%d/%m/%Y %H:%M")
    if r.get("reviewed_at"):
        r["reviewed_at_str"] = r["reviewed_at"].strftime("%d/%m/%Y %H:%M")
    # Thêm label tiếng Việt cho verified_disease
    vd = r.get("verified_disease")
    if vd and vd in DISEASE_LABELS:
        r["verified_disease_vi"] = DISEASE_LABELS[vd]["vi"]
    return r
