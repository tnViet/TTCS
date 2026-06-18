"""Auth Service — xác thực tài khoản bác sĩ."""
from werkzeug.security import check_password_hash
from models.doctor_model import DoctorModel


def verify_doctor(username: str, password: str) -> dict | None:
    """
    Trả về dict doctor nếu đăng nhập thành công, None nếu sai.
    """
    doctor = DoctorModel.get_by_username(username)
    if doctor and check_password_hash(doctor["password_hash"], password):
        return doctor
    return None
