"""
SkinScan — Application Configuration v2
Chỉnh DB_* để khớp với MySQL/XAMPP của bạn.
"""
import os

# Thư mục chứa file này (skin-web/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Thư mục gốc dự án (Skin Disease Detection/)
ROOT_DIR = os.path.dirname(BASE_DIR)


class Config:
    # ── Bảo mật ────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get("SECRET_KEY", "skinscan-v2-secret-2025-changeme")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # ── MySQL / XAMPP ───────────────────────────────────────────────────────
    DB_HOST     = os.environ.get("DB_HOST",     "localhost")
    DB_PORT     = int(os.environ.get("DB_PORT", "3306"))
    DB_USER     = os.environ.get("DB_USER",     "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_NAME     = os.environ.get("DB_NAME",     "skinscan_db")

    # ── 2 Model AI ──────────────────────────────────────────────────────────
    MODELS = {
        "densenet121": {
            "path":       os.path.join(ROOT_DIR, "models", "densenet121", "best_final.keras"),
            "class_json": os.path.join(ROOT_DIR, "models", "densenet121", "class_names.json"),
            "label":      "DenseNet-121",
            "desc":       "Mô hình chính xác cao",
        },
        "effnetv2b0": {
            "path":       os.path.join(ROOT_DIR, "models", "effnetv2b0", "best_final.keras"),
            "class_json": os.path.join(ROOT_DIR, "models", "effnetv2b0", "class_names.json"),
            "label":      "EfficientNetV2-B0",
            "desc":       "Mô hình tốc độ nhanh",
        },
    }

    IMG_SIZE             = (224, 224)
    CONFIDENCE_THRESHOLD = 0.50   # dưới ngưỡng này → báo low_confidence

    # ── Lưu ảnh (ngoài thư mục skin-web) ──────────────────────────────────
    UPLOAD_BASE      = os.path.join(ROOT_DIR, "uploads")
    UPLOAD_ORIGINALS = os.path.join(UPLOAD_BASE, "originals")
    UPLOAD_GRADCAM   = os.path.join(UPLOAD_BASE, "gradcam")

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "bmp"}
