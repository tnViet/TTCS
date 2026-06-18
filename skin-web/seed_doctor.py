"""
Seed script — Tạo tài khoản bác sĩ mặc định.

Chạy sau khi đã import schema.sql vào MySQL:
    python seed_doctor.py

Tài khoản mặc định:
    username : doctor
    password : Bacsi@2025
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from werkzeug.security import generate_password_hash
import pymysql
from config import Config


def seed():
    conn = pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset="utf8mb4",
    )
    try:
        with conn.cursor() as cur:
            hashed = generate_password_hash("Bacsi@2025")
            cur.execute(
                """
                INSERT INTO doctors (username, password_hash, full_name)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    password_hash = VALUES(password_hash),
                    full_name     = VALUES(full_name)
                """,
                ("doctor", hashed, "Bác sĩ Da liễu"),
            )
        conn.commit()
        print("✅  Tài khoản bác sĩ đã được tạo:")
        print("    username : doctor")
        print("    password : Bacsi@2025")
    finally:
        conn.close()


if __name__ == "__main__":
    seed()
