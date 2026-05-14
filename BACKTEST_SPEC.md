# Kỹ Thuật Backtest (Backtest Specification)

## 1. Mục tiêu Backtest
Đánh giá năng lực của các mô hình trong điều kiện mô phỏng môi trường thực tế lịch sử. Mục đích là để trả lời câu hỏi: *"Nếu trong quá khứ ta sử dụng thuật toán này hàng ngày, thì hiệu suất thu được là bao nhiêu?"* nhằm tránh sự lạc quan thái quá (over-optimism) và kiểm soát rủi ro rò rỉ dữ liệu tương lai (future leakage).

## 2. Rolling Backtest là gì?
Rolling Backtest (hay Walk-Forward Validation) là kỹ thuật đánh giá mô hình chuỗi thời gian, mô phỏng quá trình thời gian trôi đi:
- Bắt đầu với một "cửa sổ" dữ liệu huấn luyện ban đầu (VD: 5 năm đầu tiên).
- Tại mỗi bước `t` (có thể là từng ngày, hoặc từng tháng để tiết kiệm chi phí tính toán):
  1. Train/Cập nhật mô hình trên dữ liệu từ ngày `0` đến ngày `t-1`.
  2. Thực hiện dự đoán xác suất cho ngày `t`.
  3. Lưu lại kết quả dự đoán và nhãn thực tế (label thực sự diễn ra vào ngày `t`).
  4. Trượt cửa sổ sang bước `t+1` (dữ liệu ngày `t` lúc này trở thành lịch sử và được đưa vào tập huấn luyện tiếp theo).

## 3. Cách tránh Future Leakage (Rò rỉ tương lai)
Chìa khóa cốt lõi của Backtest framework:
- Hàm sinh Features nhận tham số `target_date`. Khi tạo row dữ liệu cho `target_date`, câu query DB hoặc bộ lọc DataFrame **PHẢI** kèm theo điều kiện nghiêm ngặt: `WHERE draw_date < target_date`.
- Ở mỗi vòng lặp `t` trong lúc backtest, tập testing chỉ có duy nhất các bản ghi của ngày `t`.
- Không sử dụng các phép tính Global Scaling (như min-max scaler của toàn bộ dữ liệu) trước khi chia tách, mà phải fit Scaler chỉ trên tập huấn luyện tại thời điểm `t-1`.

## 4. Các Metrics Đánh Giá
Hệ thống sử dụng các thang đo phân loại và xếp hạng:
- **`Brier Score`**: Đo lường sai số bình phương trung bình giữa dự đoán xác suất `p` và kết quả thực tế `y` (0 hoặc 1). Số càng nhỏ càng tốt. Đây là metric chính để đánh giá calibration.
- **`Log Loss`**: Đo lường độ tin cậy của xác suất dự đoán (phạt nặng nếu đoán xác suất rất cao nhưng sai).
- **`Precision@K`**: Trong top K số được mô hình cho điểm xác suất cao nhất, có bao nhiêu phần trăm là trúng thật. (VD: K=5, dự đoán 5 con, trúng 2 con -> Precision@5 = 40%).
- **`Hit_rate@K`**: Khả năng "bắt trúng" ít nhất 1 con loto nếu chọn đánh K con có xác suất cao nhất. (Trúng >=1 con tính là 1, xịt toàn bộ tính là 0).
- **`Avg_hits@K`**: Số nháy trúng trung bình nếu chọn K con đứng đầu. (Phân biệt với Precision vì loto có thể nổ nhiều nháy).

## 5. Format Report CSV
Quá trình backtest sẽ sinh ra dữ liệu chi tiết ở cấp độ từng con số mỗi ngày, lưu tại `data/reports/backtest_raw_<model>_<timestamp>.csv`:
```csv
backtest_date,model_name,target_number,predicted_prob,actual_label,actual_hits
2023-11-01,LogisticReg,68,0.354,1,1
2023-11-01,LogisticReg,15,0.321,0,0
...
```
Và một file Report Tổng Hợp (`backtest_summary.csv`):
```csv
backtest_date,model_name,precision@5,hit_rate@5,avg_hits@5,brier_score
2023-11-01,LogisticReg,0.20,1.0,1.0,0.185
...
```

## 6. Cách so sánh Baseline vs ML Model
Sau khi hoàn tất quá trình backtest chạy qua nhiều tháng/năm, ta lấy giá trị trung bình (Average) của các metrics trên file summary report để so sánh.
- **Nguyên tắc:** Một mô hình ML chỉ được coi là "hữu ích" trong MVP nếu `Precision@K` hoặc `Hit_rate@K` của nó vượt qua các Baseline Models (Random Baseline và Frequency Baseline).
- Nếu mô hình phức tạp (XGBoost) không đánh bại được mô hình đơn giản (Frequency Baseline), ta ưu tiên sự đơn giản và loại bỏ mô hình phức tạp.
