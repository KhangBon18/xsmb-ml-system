# Thông Số Mô Hình (Model Specification)

## 1. Định nghĩa bài toán ML
Bài toán được thiết lập dưới dạng **Phân loại nhị phân (Binary Classification)**.
Thay vì cố gắng dự đoán chính xác "27 số nào sẽ ra" (điều này là bất khả thi), hệ thống sẽ đánh giá độc lập từng con số loto từ "00" đến "99".
Mục tiêu: Với một ngày mục tiêu (`target_date`) và một con số loto cụ thể `N`, tính toán xác suất `P(y=1)` - tức xác suất con số `N` sẽ xuất hiện **ít nhất một lần** trong 27 giải của ngày `target_date`.

## 2. Một row training là gì?
Tập dữ liệu huấn luyện (Training Dataset) được xây dựng theo cấu trúc: mỗi ngày quay thưởng tạo ra đúng **100 rows**, tương ứng với 100 con số từ "00" đến "99".
Cấu trúc một row:
`[target_date, loto_number, feature_1, feature_2, ..., label]`

## 3. Label là gì?
- `label = 1`: Nếu `loto_number` có xuất hiện (nằm trong 27 kết quả) vào ngày `target_date`.
- `label = 0`: Nếu `loto_number` không xuất hiện vào ngày `target_date`.
*(Lưu ý: Bất kể số đó về 1 nháy, 2 nháy hay n nháy, label vẫn chỉ là 1, vì đây là bài toán phân loại nhị phân xuất hiện/không xuất hiện).*

## 4. Feature Groups
Các nhóm đặc trưng (Features) phải được tính toán **CHỈ SỬ DỤNG DỮ LIỆU CỦA CÁC NGÀY < `target_date`**.
1. **Frequency Features (Tần suất):** Số lần `loto_number` xuất hiện trong $X$ ngày qua (Vd: 10 ngày, 30 ngày, 100 ngày).
2. **Gap/Gan Features (Khoảng cách):**
   - Số ngày liên tiếp chưa xuất hiện tính đến trước `target_date` (Chu kỳ gan hiện tại).
   - Khoảng gan cực đại lịch sử của số đó.
3. **Rolling Stats (Thống kê trượt):**
   - Trung bình số nháy mỗi khi xuất hiện.
   - Nhịp điệu (VD: trung bình khoảng cách giữa các lần xuất hiện trong 3 tháng qua).

## 5. Baseline Models
Trước khi dùng Machine Learning, phải có các Baseine để so sánh:
- **Random Baseline:** Dự đoán ngẫu nhiên xác suất đều (VD: khoảng 0.23 đến 0.27) cho mọi con số.
- **Frequency Baseline:** Số nào về nhiều nhất trong 30 ngày qua sẽ được gán xác suất cao nhất.
- **Gan Baseline:** Số nào có chu kỳ gan hiện tại tiến gần (hoặc vượt) gan cực đại lịch sử sẽ được gán xác suất cao nhất.

## 6. ML Models dùng trong MVP
- **Logistic Regression:** Mô hình tuyến tính tốt, dễ giải thích, trả về xác suất tốt (well-calibrated).
- **Random Forest / XGBoost cơ bản:** Mô hình phi tuyến để bắt các tương tác đặc trưng, độ phức tạp thấp để tránh overfitting.

## 7. Quy tắc Split theo thời gian (Time-based Split)
**TUYỆT ĐỐI KHÔNG DÙNG RANDOM SPLIT** (không dùng train_test_split có xáo trộn). Do đây là dữ liệu chuỗi thời gian, việc chia ngẫu nhiên sẽ làm rò rỉ dữ liệu tương lai vào quá khứ.
- **Tập Train:** Mọi `target_date` từ năm $Y_1$ đến ngày $D$.
- **Tập Validation/Test:** Mọi `target_date` > $D$.

## 8. Quy tắc Calibration
Xác suất trả ra từ mô hình phải sát với xác suất thực tế trên tập dữ liệu lớn. (Ví dụ: Tập hợp các con số được dự đoán có xác suất 30% thì tỷ lệ xuất hiện thực tế của chúng cũng phải xấp xỉ 30%).
- Nếu dùng RandomForest/XGBoost, bắt buộc bọc qua `CalibratedClassifierCV` (Isotonic hoặc Platt Scaling) để nắn lại output probabilities.

## 9. Output Prediction Format
Kết quả trả về từ API/Model cho ngày `target_date` là một List các Dictionary, sắp xếp theo `probability` giảm dần:
```json
[
  {
    "number": "68",
    "probability": 0.354,
    "current_gap": 15,
    "freq_30d": 2
  },
  {
    "number": "86",
    "probability": 0.312,
    "current_gap": 4,
    "freq_30d": 8
  },
  ... (đủ 100 số)
]
```
