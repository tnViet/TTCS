"""Doctor Model — CRUD cho bảng doctors."""
from __future__ import annotations
from .database import get_db


class DoctorModel:

    @staticmethod
    def get_by_username(username: str) -> dict | None:
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                "SELECT * FROM doctors WHERE username = %s",
                (username,),
            )
            return cur.fetchone()

    @staticmethod
    def get_by_id(doctor_id: int) -> dict | None:
        db = get_db()
        with db.cursor() as cur:
            cur.execute(
                "SELECT * FROM doctors WHERE id = %s",
                (doctor_id,),
            )
            return cur.fetchone()
