# 🩺 Skin Disease Detection

Hệ thống phát hiện và phân loại bệnh da liễu tự động sử dụng **EfficientNetB0** và **Transfer Learning**, tích hợp **Grad-CAM** để giải thích trực quan kết quả chẩn đoán.

> ⚠️ **Disclaimer**: Hệ thống này chỉ mang tính tham khảo, không thay thế chẩn đoán của bác sĩ chuyên khoa.

---

## 📋 Tổng quan

| Thông số | Chi tiết |
|---|---|
| Model | EfficientNetB0 (Transfer Learning) |
| Số lớp bệnh | 11 classes |
| Tổng ảnh | 9.493 ảnh |
| Test Accuracy | **71.2%** |
| Framework | TensorFlow 2.20 / Keras |
| Web | Flask (chạy local) |

---

## 🛠️ Tech Stack

- **Model**: TensorFlow 2.20 / Keras, EfficientNetB0
- **Augmentation**: Albumentations
- **Web**: Flask, HTML/CSS (Notion Design System)
- **Training**: Google Colab T4 GPU
- **Explainability**: Grad-CAM

---

## 📊 Dataset

| Nguồn | Link | Ảnh dùng |
|---|---|---|
| DermNet | [Kaggle](https://www.kaggle.com/datasets/shubhamgoel27/dermnet) | ~7.000 |
| 20 Skin Diseases | [Kaggle](https://www.kaggle.com/datasets/haroonalam16/20-skin-diseases-dataset) | ~2.500 |

> **Lưu ý về bias**: Dataset chủ yếu ảnh da trắng (nguồn gốc châu Âu). Độ chính xác có thể thấp hơn với da vàng/da tối.

---

## 📈 Kết quả

```
Test Accuracy  : 71.2%
Test Loss      : 1.0661
Macro F1       : 0.69
Weighted F1    : 0.71
```

---

## 🦠 11 bệnh được hỗ trợ

| Class | Tên tiếng Việt | F1-score |
|---|---|---|
| nail_fungus | Nấm móng | 0.87 |
| acne_rosacea | Mụn trứng cá & Đỏ da | 0.81 |
| alopecia | Rụng tóc | 0.77 |
| warts | Mụn cóc & Virus da | 0.72 |
| eczema | Chàm da | 0.70 |
| tinea | Nấm da / Hắc lào | 0.70 |
| urticaria | Mề đay | 0.70 |
| atopic_dermatitis | Viêm da cơ địa | 0.61 |
| bullous_disease | Bệnh bọng nước | 0.60 |
| scabies | Ghẻ / Ký sinh trùng | 0.59 |
| drug_eruptions | Phát ban do thuốc | 0.56 |

---

## 🏗️ Kiến trúc

```
Input (224×224×3, RGB, 0-255)
    ↓
EfficientNetB0 Backbone (pretrained ImageNet)
    ↓
GlobalAveragePooling2D
    ↓
BatchNormalization → Dropout(0.4)
    ↓
Dense(256, ReLU) → Dropout(0.3)
    ↓
Dense(11, Softmax)
    ↓
Top-3 predictions + Grad-CAM heatmap
```

---

## 📁 Cấu trúc project

```
Skin Disease Detection/
├── skin-web/               ← Flask web app
│   ├── app.py              ← Backend chính
│   ├── requirements.txt
│   ├── templates/
│   │   └── index.html      ← Giao diện
│   └── static/
│       └── style.css
├── models/                
│   ├── skin_disease_model_v3.keras
│   └── class_names.json
├── skin_data/              
├── skin_disease_v3.ipynb   ← Notebook train Colab
├── prepare_data.py         ← Script chuẩn bị data
├── .gitignore
└── README.md
```

---

## 🧠 Huấn luyện model

Sử dụng notebook `skin_disease_v3.ipynb` trên Google Colab:

### Chiến lược huấn luyện 3 giai đoạn

| Giai đoạn | Mô tả | Learning Rate | Val Accuracy |
|---|---|---|---|
| Phase 1 | Base frozen, train Custom Head | 1e-3 | 57.5% |
| Phase 2 | Fine-tune, BN frozen | 1e-5 | 61.0% |
| Phase 3 | Fine-tune, lr tăng | 1e-4 | **70.2%** |

---

## 🚀 Cài đặt và chạy

### Yêu cầu

- Python 3.11 hoặc 3.12
- Model file: `skin_disease_model_v3.keras`

### Bước 1 — Tải model

Tải 2 file sau và đặt vào thư mục `models/`:
- `skin_disease_model_v3.keras`
- `class_names.json`

> Model không được lưu trong repo do kích thước lớn (~30MB). Liên hệ tôi hoặc train lại bằng notebook.


### Bước 2 — Chạy web

```bash
python app.py
```

Mở trình duyệt: **http://localhost:5000**


