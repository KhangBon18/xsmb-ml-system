# 02 — Product Requirements

---

## 1. Mục tiêu MVP

Xây dựng hệ thống Python end-to-end phục vụ **nghiên cứu thống kê** và **phân tích xác suất** cho XSMB, với khả năng:

1. Thu thập kết quả XSMB từ nguồn đáng tin cậy (≥ 10 năm lịch sử).
2. Lưu trữ raw HTML, parse, validate, normalize dữ liệu.
3. Hỗ trợ **3 target types** riêng biệt: `loto_2d_all_prizes`, `db_2cang`, `db_3cang`.
4. Sinh feature dataset không rò rỉ tương lai.
5. Huấn luyện baseline models + ít nhất 1 ML model cho mỗi target type.
6. Backtest nghiêm ngặt theo thời gian (walk-forward).
7. Xuất ranking xác suất qua CLI.
8. Không đưa ra cam kết hay hứa hẹn dự đoán chính xác.

---

## 2. Ngoài phạm vi MVP

- ❌ Real-time streaming (crawl khi đang quay thưởng)
- ❌ Frontend SPA (React/Vue)
- ❌ Deep Learning (LSTM, Transformer)
- ❌ Xổ số miền Nam, miền Trung, Vietlott
- ❌ Cloud deployment (chỉ local/Docker)
- ❌ Multi-source crawling (MVP dùng 1 source, adapter pattern chuẩn bị cho mở rộng)
- ❌ Tối ưu trading/staking strategy
- ❌ Push notification

---

## 3. Personas

### 3.1. Researcher (Nghiên cứu viên)

- Muốn phân tích tần suất, pattern lịch sử.
- Cần dữ liệu sạch, đúng format.
- Quan tâm calibration, Brier score.
- Thành thạo Python, đọc CSV/JSON.

### 3.2. Developer (Lập trình viên)

- Muốn mở rộng feature, thêm model, custom backtest.
- Cần code modular, test coverage tốt.
- Cần CLI rõ ràng.

### 3.3. Analyst (Phân tích viên)

- Muốn xem ranking xác suất hàng ngày.
- Cần báo cáo backtest dễ đọc.
- Dùng CLI hoặc Streamlit dashboard (post-MVP).

---

## 4. User Stories

### Data Acquisition
- **US-01:** "Là researcher, tôi muốn crawl kết quả XSMB từ ngày A đến ngày B, để có raw data cho phân tích."
- **US-02:** "Là researcher, tôi muốn re-parse raw HTML đã lưu khi parser được cải tiến, mà không cần crawl lại."

### Data Quality
- **US-03:** "Là developer, tôi muốn system validate rằng mỗi ngày có đúng 27 giải và reject ngày thiếu/thừa."
- **US-04:** "Là developer, tôi muốn tất cả số xổ số được lưu dạng string để không mất leading zero."

### Target Extraction
- **US-05:** "Là researcher, tôi muốn extract loto 2D từ toàn bộ 27 giải (loto_2d_all_prizes)."
- **US-06:** "Là researcher, tôi muốn extract đề 2 càng (db_2cang) từ giải Đặc biệt riêng biệt."
- **US-07:** "Là researcher, tôi muốn extract đề 3 càng (db_3cang) từ giải Đặc biệt riêng biệt."

### Feature Engineering
- **US-08:** "Là researcher, tôi muốn sinh features (tần suất, gan, rolling) cho từng target type mà không rò rỉ dữ liệu tương lai."

### Modeling
- **US-09:** "Là researcher, tôi muốn train baseline models (random, frequency, gap) cho mỗi target type."
- **US-10:** "Là researcher, tôi muốn train Logistic Regression + tree model cho mỗi target type."
- **US-11:** "Là researcher, tôi muốn so sánh ML model với baseline qua backtest."

### Backtesting
- **US-12:** "Là researcher, tôi muốn chạy walk-forward backtest cho mỗi target type với expanding window."
- **US-13:** "Là analyst, tôi muốn xem báo cáo backtest (Brier, P@K, Hit@K) dạng CSV."

### Prediction
- **US-14:** "Là analyst, tôi muốn chạy prediction cho ngày mai và xem ranking top-K numbers."

### CLI
- **US-15:** "Là developer, tôi muốn chạy toàn bộ pipeline qua CLI commands riêng biệt."

---

## 5. Acceptance Criteria

### AC-01: Data Ingestion
- [ ] Crawl 1 ngày trả về raw HTML.
- [ ] Raw HTML được lưu vào DB trước khi parse.
- [ ] Parse ra đúng 27 prize entries.
- [ ] Mỗi entry có `prize_tier`, `prize_index`, `winning_number` (string).

### AC-02: Validation
- [ ] Ngày có ≠ 27 entries bị REJECT.
- [ ] `winning_number` có sai độ dài bị REJECT.
- [ ] Ký tự không phải số bị REJECT.
- [ ] Leading zeros preserved.

### AC-03: Target Extraction
- [ ] `loto_2d_all_prizes`: 27 entries → 100 rows (label = hit/no-hit).
- [ ] `db_2cang`: special prize → 100 rows (1 positive, 99 negative).
- [ ] `db_3cang`: special prize → 1000 rows (1 positive, 999 negative).
- [ ] Targets KHÔNG ĐƯỢC trộn lẫn.

### AC-04: Features
- [ ] Tất cả features chỉ dùng data `< target_date`.
- [ ] Unit test chống leakage pass.
- [ ] Feature builder chạy cho cả 3 target types.

### AC-05: Baselines
- [ ] Random baseline cho uniform probability.
- [ ] Frequency baseline dùng tần suất window.
- [ ] Gap baseline dùng gan hiện tại.
- [ ] Mỗi baseline output 100 (hoặc 1000) probabilities.

### AC-06: ML Models
- [ ] Logistic Regression trained + calibrated.
- [ ] Tree model trained + calibrated.
- [ ] Model lưu vào `data/models/`.

### AC-07: Backtest
- [ ] Walk-forward, no random split.
- [ ] Metrics: Brier Score, Log Loss, P@K, Hit@K, Avg@K.
- [ ] Report CSV sinh đúng format.
- [ ] Baseline so sánh bao gồm.

### AC-08: CLI
- [ ] `scrape`, `process`, `build-features`, `train`, `backtest`, `predict` commands chạy.
- [ ] `--target` flag phân biệt 3 target types.

---

## 6. Non-Functional Requirements

### 6.1. Reproducibility
- Cùng data, cùng config → cùng kết quả features, cùng backtest metrics.
- Random seed phải được set và ghi log.

### 6.2. Logging
- Dùng Python `logging`, không dùng `print()` trong library modules.
- Log levels: DEBUG, INFO, WARNING, ERROR.
- Mỗi phase (scrape, process, train) log ít nhất: start, end, count records, errors.

### 6.3. Deterministic Pipeline
- Pipeline phải idempotent: chạy lại cùng command với cùng data range → không thay đổi kết quả.

### 6.4. No Leakage
- Feature computation: `WHERE draw_date < target_date`.
- Backtest: train chỉ trên data trước test date.
- Scaler fit chỉ trên train data.

### 6.5. Performance
- `loto_2d_all_prizes` dataset: ~365K rows/10 năm → xử lý dưới 1 phút trên laptop.
- `db_3cang` dataset: ~3.65M rows/10 năm → batch processing, target dưới 10 phút.

### 6.6. Data Safety
- Timeout: 10 giây/request.
- Retry: 3 lần với exponential backoff.
- Sleep giữa requests: 1-3 giây.
- User-Agent rõ ràng.
- Raw HTML cached.
