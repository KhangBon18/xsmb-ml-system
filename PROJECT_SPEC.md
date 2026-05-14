# Thông Số Kỹ Thuật Dự Án (Project Specification)

## 1. Mục tiêu hệ thống
Xây dựng một hệ thống hoàn chỉnh (end-to-end) bằng Python để thu thập, chuẩn hóa, lưu trữ, phân tích, backtest và dự đoán xác suất xuất hiện của 100 số loto 2 chữ số (từ "00" đến "99") của Xổ Số Miền Bắc (XSMB).

**Lưu ý quan trọng:** Hệ thống này hoàn toàn phục vụ mục đích phân tích thống kê và nghiên cứu thuật toán Machine Learning. Hệ thống KHÔNG đưa ra bất kỳ cam kết hay đảm bảo nào về việc dự đoán chính xác kết quả xổ số.

## 2. Phạm vi MVP (Minimum Viable Product)
- **Scraping:** Thu thập kết quả XSMB từ một nguồn đáng tin cậy trong quá khứ (ví dụ 10 năm trở lại đây) và cập nhật hàng ngày.
- **Database:** Lưu trữ dữ liệu thô (raw HTML) và dữ liệu đã qua xử lý bằng SQLite.
- **Processing:** Bóc tách 27 giải mỗi ngày và trích xuất đúng loto 2 chữ số.
- **Features:** Xây dựng các đặc trưng cơ bản (features) dựa trên lịch sử xuất hiện (tần suất, chu kỳ gan, độ trễ).
- **Modeling:** 
  - Triển khai ít nhất 2 baseline models (ví dụ: Random, theo chu kỳ gan).
  - Triển khai 1 mô hình Machine Learning cơ bản (Logistic Regression hoặc Random Forest).
- **Backtesting:** Khung đánh giá mô hình bằng kỹ thuật Rolling Origin (Time-based backtesting), nghiêm ngặt chống rò rỉ dữ liệu tương lai.
- **CLI/API:** Giao diện dòng lệnh (CLI) để chạy các tác vụ và một FastAPI cơ bản phục vụ dự đoán.

## 3. Ngoài phạm vi MVP (Out of Scope)
- Cào dữ liệu theo thời gian thực (Real-time data streaming trong lúc đang quay thưởng).
- Giao diện Frontend phức tạp (Vue/React).
- Các mô hình Deep Learning tiên tiến (LSTM, Transformer) chưa cần ở giai đoạn MVP.
- Mở rộng phân tích sang xổ số miền Nam, miền Trung hoặc các loại hình xổ số khác (Vietlott).
- Tự động hóa deploy lên Cloud (chỉ dừng ở Docker Compose chạy local).

## 4. Kiến trúc tổng thể
Hệ thống tuân theo mô hình Monolithic theo hướng Modular, chia thành các luồng xử lý rõ ràng:
1. **Data Acquisition:** `xsmb.scraping` - Crawl HTML và lưu raw data.
2. **Data Storage:** `xsmb.database` - Giao tiếp SQLite.
3. **Data Processing:** `xsmb.processing` - Parsing HTML thành cấu trúc bảng, trích xuất 2 số cuối.
4. **Feature Engineering:** `xsmb.features` - Tính toán các biến độc lập.
5. **Modeling:** `xsmb.models` - Huấn luyện mô hình và thực hiện inference.
6. **Delivery:** `xsmb.api` và `xsmb.dashboard` (Streamlit).

## 5. Pipeline dữ liệu
`Raw HTML` -> `Parser` -> `Draw Results (Full)` -> `Loto 2-Digits` -> `Time-series aggregation` -> `Features Dataset` -> `ML Model` -> `Probability Predictions`.

## 6. Các module chính
- **app/:** Entry point của hệ thống (`main.py`).
- **xsmb/scraping/:** Quản lý rate limit, retry, User-Agent và lấy dữ liệu HTML.
- **xsmb/database/:** Kết nối DB, định nghĩa Schema và Data Repository.
- **xsmb/processing/:** Dọn dẹp dữ liệu, đảm bảo bảo toàn số "0" ở đầu (leading zeros), validate số lượng giải.
- **xsmb/features/:** Chứa logic tạo dataset training.
- **xsmb/models/:** Logic training, backtesting và đánh giá.
- **xsmb/api/:** Cung cấp các endpoint RESTful.

## 7. Các command dự kiến
Qua `app/main.py` bằng argparse hoặc thư viện CLI:
- `python -m app.main scrape --start-date YYYY-MM-DD --end-date YYYY-MM-DD`
- `python -m app.main process` (parse raw sang structured data)
- `python -m app.main build-features`
- `python -m app.main train --model <model_name>`
- `python -m app.main backtest --start-date YYYY-MM-DD`
- `python -m app.main predict --date YYYY-MM-DD`

## 8. Các rủi ro kỹ thuật
- **Nguồn dữ liệu thay đổi:** Cấu trúc HTML của trang web XSMB bị thay đổi, làm gãy Parser. -> *Giải pháp: Cần lưu raw HTML để có thể re-parse lại toàn bộ, thiết lập cảnh báo khi Parsing fail.*
- **Chặn IP (IP Banning):** Scraping quá nhanh. -> *Giải pháp: Tuân thủ quy tắc timeout, random sleep, sử dụng retry mechanism.*
- **Data Leakage (Rò rỉ dữ liệu):** Sử dụng thông tin của ngày `T` để dự đoán cho chính ngày `T`. -> *Giải pháp: Thiết kế Backtesting framework cô lập dữ liệu theo mốc thời gian chặt chẽ.*

## 9. Các nguyên tắc chống ảo giác mô hình (Anti-Hallucination)
- Hệ thống dựa hoàn toàn trên số liệu lịch sử tĩnh (Static historical logic), tuyệt đối không dùng các mô hình sinh ngôn ngữ (LLM) để sinh số dự đoán.
- Tất cả các kết quả dự đoán của ML model phải được thể hiện dưới dạng **Xác suất (Probability)** (VD: số "15" có 32% cơ hội ra), không trả về khẳng định kiểu "Chắc chắn ra số 15".
- Các chỉ số đánh giá (Metrics) phải được báo cáo một cách khách quan thông qua hệ thống Backtest. Đo lường Brier Score / Log Loss thay vì chỉ đo Accuracy.
