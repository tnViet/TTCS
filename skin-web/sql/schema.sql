

CREATE DATABASE IF NOT EXISTS skinscan_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE skinscan_db;

-- ────────────────────────────────────────────────────────────
--  1. DOCTORS
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS doctors (
    id            INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50)  UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(100) NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  2. PREDICTIONS (gộp bệnh nhân + kết quả AI + feedback bác sĩ)
-- ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS predictions (
    id               INT AUTO_INCREMENT PRIMARY KEY,

    -- Thông tin bệnh nhân (nhập khi upload)
    patient_name     VARCHAR(100) NOT NULL,
    patient_phone    VARCHAR(20)  NOT NULL,

    -- Đường dẫn ảnh trên disk
    image_path       VARCHAR(500) NOT NULL,
    gradcam_path     VARCHAR(500),

    -- Mô hình AI đã dùng
    model_used       ENUM('densenet121', 'effnetv2b0') NOT NULL DEFAULT 'densenet121',

    -- Kết quả AI
    top_disease      VARCHAR(100) NOT NULL,
    top_confidence   DECIMAL(5,2) NOT NULL,
    top3_json        JSON         NOT NULL,
    low_confidence   BOOLEAN      NOT NULL DEFAULT FALSE,

    -- Phản hồi của bác sĩ (NULL cho đến khi bác sĩ xem xét)
    verified_disease ENUM(
        'acne_rosacea',
        'atopic_dermatitis',
        'bullous_disease',
        'eczema',
        'nail_fungus',
        'tinea',
        'vitiligo',
        'warts',
        'other'
    ) DEFAULT NULL,
    doctor_note      TEXT         DEFAULT NULL,
    doctor_id        INT          DEFAULT NULL,
    reviewed_at      TIMESTAMP    NULL DEFAULT NULL,

    created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_phone (patient_phone),
    INDEX idx_created (created_at),
    FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
