# Skin Disease Classification

## Giới thiệu

Dự án xây dựng mô hình học sâu để phân loại ảnh bệnh da liễu thành 8 lớp bệnh. Hệ thống sử dụng kỹ thuật Transfer Learning với hai kiến trúc backbone là EfficientNetV2B0 và DenseNet121, kết hợp Grad-CAM để trực quan hóa vùng ảnh mà mô hình tập trung khi đưa ra dự đoán.

## Danh sách bệnh được phân loại

Dự án hiện hỗ trợ 8 lớp bệnh:

| STT | Class name        | Tên tiếng Việt        |
| --: | ----------------- | --------------------- |
|   1 | acne_rosacea      | Mụn trứng cá và đỏ da |
|   2 | atopic_dermatitis | Viêm da cơ địa        |
|   3 | bullous_disease   | Bệnh bọng nước        |
|   4 | eczema            | Chàm da               |
|   5 | nail_fungus       | Nấm móng              |
|   6 | tinea             | Nấm da / Hắc lào      |
|   7 | vitiligo          | Bạch biến             |
|   8 | warts             | Mụn cóc và virus da   |

## Bộ dữ liệu

Bộ dữ liệu gồm tổng cộng 9.808 ảnh, được chia theo tỷ lệ 70/15/15:

| Tập dữ liệu | Số ảnh | Mục đích                              |
| ----------- | -----: | ------------------------------------- |
| Train       |  6.862 | Huấn luyện mô hình                    |
| Validation  |  1.467 | Theo dõi và lựa chọn mô hình tốt nhất |
| Test        |  1.479 | Đánh giá cuối cùng                    |

## Tổng hợp số lượng ảnh theo từng bệnh

Bảng dưới đây trình bày số lượng ảnh của từng lớp bệnh trong các tập train, validation và test.

| STT | Class name        | Tên tiếng Việt        |     Train | Validation |      Test | Tổng số ảnh |
| --: | ----------------- | --------------------- | --------: | ---------: | --------: | ----------: |
|   1 | acne_rosacea      | Mụn trứng cá và đỏ da |       773 |        165 |       167 |       1.105 |
|   2 | atopic_dermatitis | Viêm da cơ địa        |       842 |        180 |       181 |       1.203 |
|   3 | bullous_disease   | Bệnh bọng nước        |       313 |         67 |        68 |         448 |
|   4 | eczema            | Chàm da               |     1.251 |        268 |       269 |       1.788 |
|   5 | nail_fungus       | Nấm móng              |       600 |        128 |       130 |         858 |
|   6 | tinea             | Nấm da / Hắc lào      |     1.605 |        344 |       345 |       2.294 |
|   7 | vitiligo          | Bạch biến             |       718 |        153 |       155 |       1.026 |
|   8 | warts             | Mụn cóc và virus da   |       760 |        162 |       164 |       1.086 |
|     | **Tổng**          |                       | **6.862** |  **1.467** | **1.479** |   **9.808** |

Dữ liệu vẫn có sự mất cân bằng giữa các lớp, trong đó `tinea` là lớp có nhiều ảnh nhất và `bullous_disease` là lớp có ít ảnh nhất. Vì vậy, quá trình huấn luyện sử dụng `class_weight` và Focal Loss để giúp mô hình học cân bằng hơn.


## Chiến lược huấn luyện

Mô hình được huấn luyện theo 3 giai đoạn:

| Giai đoạn | Mô tả                                                    |
| --------- | -------------------------------------------------------- |
| Phase 1   | Đóng băng toàn bộ backbone, chỉ huấn luyện Custom Head   |
| Phase 2   | Mở khoảng 45% lớp cuối của backbone để fine-tune nhẹ     |
| Phase 3   | Mở khoảng 80% lớp cuối của backbone để fine-tune sâu hơn |


## Loss function

Dự án sử dụng Sparse Categorical Focal Loss.

Focal Loss giúp mô hình tập trung hơn vào các mẫu khó hoặc dễ bị phân loại sai. Điều này phù hợp với bài toán bệnh da liễu vì một số bệnh có biểu hiện gần giống nhau và dữ liệu giữa các lớp không cân bằng.

## Kết quả thực nghiệm

| Mô hình          | Test Accuracy | Macro F1 | Weighted F1 |
| ---------------- | ------------: | -------: | ----------: |
| EfficientNetV2B0 |        78.57% |   0.7826 |      0.7871 |
| DenseNet121      |        77.48% |   0.7799 |      0.7746 |

EfficientNetV2B0 đạt kết quả tổng thể cao hơn và được chọn làm mô hình chính. DenseNet121 có kết quả khá tương đồng và cho thấy khả năng phân loại ổn định ở một số lớp khó như `bullous_disease`.

## Lưu ý

Hệ thống chỉ có mục đích hỗ trợ tham khảo và học tập. Kết quả dự đoán của mô hình không thay thế cho chẩn đoán của bác sĩ chuyên khoa.
