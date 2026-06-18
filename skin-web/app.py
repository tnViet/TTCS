"""
SkinScan v2 — Application Factory
"""
import os
from flask import Flask

from config import Config
from models import init_db
from services.ai_service import init_models
from controllers.patient_controller import patient_bp
from controllers.doctor_controller  import doctor_bp


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.from_object(config_class)

    # Đảm bảo thư mục upload tồn tại
    os.makedirs(app.config["UPLOAD_ORIGINALS"], exist_ok=True)
    os.makedirs(app.config["UPLOAD_GRADCAM"],   exist_ok=True)

    # Database
    init_db(app)

    # Blueprints
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)

    # Load cả 2 model AI (chạy 1 lần lúc khởi động)
    with app.app_context():
        init_models(app)

    return app


app = create_app()

if __name__ == "__main__":
    print("\n   SkinScan v2 đang chạy → http://localhost:5000\n")
    app.run(debug=False, host="0.0.0.0", port=5000)
