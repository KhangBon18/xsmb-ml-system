# 13 — Risk Register

---

## Risk Matrix

| ID | Risk | Likelihood | Impact | Severity | Mitigation | Owner |
|:---|:---|:---|:---|:---|:---|:---|
| R01 | **Nguồn dữ liệu thay đổi HTML** — Trang web thay đổi cấu trúc HTML, parser gãy | Trung bình | Cao | 🔴 | Lưu raw HTML, adapter pattern per source, monitor parse success rate | Phase 2-3 |
| R02 | **Parser sai** — Parse ra sai số, sai giải, sai thứ tự | Trung bình | Rất cao | 🔴 | Unit test với real HTML, validate 27 count + digit lengths, cross-check với nguồn phụ | Phase 3 |
| R03 | **Mất leading zero** — Số "05" thành "5", "00" thành "0" | Cao | Rất cao | 🔴 | Strict `str` type, KHÔNG BAO GIỜ dùng `int()`, test coverage, DB CHECK constraints | All phases |
| R04 | **Future leakage** — Feature dùng data tương lai | Trung bình | Rất cao | 🔴 | `assert max(dates) < target_date` trong mỗi feature function, unit test chống leakage, code review | Phase 5, 8 |
| R05 | **Overfitting** — ML model overfit trên training data | Cao | Cao | 🔴 | Walk-forward backtest (không random split), compare vs baselines, calibration check, regularization | Phase 7-8 |
| R06 | **Xác suất không calibration** — Model output P=0.5 nhưng actual rate=0.2 | Trung bình | Trung bình | 🟡 | `CalibratedClassifierCV` cho tree models, reliability diagram, Brier Score monitoring | Phase 7 |
| R07 | **Hiểu sai target** — Nhầm lẫn `loto_2d_all_prizes` với `db_2cang` | Trung bình | Rất cao | 🔴 | Tài liệu rõ ràng (01_DOMAIN), test tách biệt, KHÔNG gộp datasets, code review | Phase 4 |
| R08 | **Performance db_3cang** — 1000 rows/ngày × 10 năm = 3.65M rows | Trung bình | Trung bình | 🟡 | Batch insert, index optimization, chunked processing, CSV storage thay vì full DB | Phase 4-5 |
| R09 | **Class imbalance db_3cang** — 1:999 positive:negative | Chắc chắn | Cao | 🔴 | `class_weight='balanced'`, ranking metrics (P@K, Recall@K thay vì accuracy), Brier Skill Score | Phase 7-8 |
| R10 | **Legal/Ethical risk** — Hệ thống bị hiểu nhầm là "bao trúng" | Thấp | Cao | 🟡 | Disclaimer ở mọi output, KHÔNG hứa hẹn, chỉ nói "nghiên cứu thống kê", AGENTS.md rule | All phases |
| R11 | **IP bị chặn khi scraping** — Crawl quá nhanh bị ban | Thấp | Trung bình | 🟡 | Rate limiting (1-3s sleep), retry mechanism, respectful User-Agent, không crawl hung hăng | Phase 2 |
| R12 | **Ngày không quay thưởng** — Lễ Tết, nghỉ bất thường | Chắc chắn | Thấp | 🟢 | Gap features tính theo kỳ quay thực tế, skip missing dates, document rõ | Phase 5 |
| R13 | **PostgreSQL vs SQLite mâu thuẫn** — docker-compose dùng PostgreSQL, AGENTS.md yêu cầu SQLite | Đã xảy ra | Thấp | 🟢 | Quyết định: SQLite cho MVP. Giữ docker-compose cho migration sau. Bỏ psycopg2 | Phase 1 |
| R14 | **Thiếu `__init__.py`** — Package import fails | Đã phát hiện | Thấp | 🟢 | Thêm `__init__.py` cho tất cả packages trong Phase 1 | Phase 1 |
| R15 | **Model không đánh bại baseline** — ML thua frequency baseline | Cao | Trung bình | 🟡 | Đây là kết quả khoa học hợp lệ. Ghi nhận trung thực. Dùng baseline tốt nhất. Không fake metrics | Phase 8 |
| R16 | **Data source không còn available** — Website đóng cửa hoặc thay đổi URL | Thấp | Cao | 🟡 | Adapter pattern cho multi-source, raw HTML cached, có thể chuyển nguồn nhanh | Phase 2 |

---

## Risk Response Actions

### Cho các risk 🔴 (Severe):

1. **R03 (Leading zero):** Thêm assertion `len(number) == 2` (hoặc 3) ở mọi insertion point. DB CHECK constraint. Test mọi edge case "00", "01", "09".

2. **R04 (Leakage):** Mỗi feature function phải nhận `target_date` param và filter `< target_date`. Thêm `_validate_no_leakage()` call. Unit test mandatory.

3. **R07 (Target confusion):** Enum cho target types. Mỗi target có dataset riêng, pipeline riêng, metric riêng. Code review khi cross-target.

4. **R09 (Imbalance db_3cang):** Accept rằng accuracy vô nghĩa cho 1:999. Chỉ dùng ranking metrics. Baseline comparison bắt buộc.

### Cho các risk 🟡 (Moderate):

5. **R15 (Model thua baseline):** Đây KHÔNG phải failure — đây là kết quả khoa học. Ghi nhận: "Lottery numbers are fundamentally random. ML model found no statistically significant advantage over frequency baseline for db_3cang." Đây là output trung thực.

---

## Ambiguity Defaults

Khi gặp yêu cầu mơ hồ, dùng defaults an toàn:

| Câu hỏi mơ hồ | Default an toàn |
|:---|:---|
| `loto_2d` lấy từ đâu? | Tất cả 27 giải (all prizes) |
| `db_2cang` lấy từ đâu? | 2 chữ số cuối giải Đặc biệt (special prize) |
| `db_3cang` lấy từ đâu? | 3 chữ số cuối giải Đặc biệt |
| Feature window đơn vị? | Số kỳ quay (draws), không phải ngày calendar |
| Database engine? | SQLite (per AGENTS.md) |
| Backtest split? | Walk-forward, KHÔNG random |
