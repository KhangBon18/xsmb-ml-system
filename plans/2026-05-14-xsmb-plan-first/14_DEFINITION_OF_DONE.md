# 14 — Definition of Done

---

## Global Definition of Done

Một task/phase được coi là **DONE** khi đáp ứng TẤT CẢ các tiêu chí sau:

### ✅ Code Quality

- [ ] Code chạy không lỗi (`python -c "import xsmb"` pass).
- [ ] Code có type hints cho public functions.
- [ ] Code có docstrings cho public functions.
- [ ] Không có `print()` trong library modules (chỉ dùng `logging`).
- [ ] Dùng `pathlib` thay vì string paths.

### ✅ Tests

- [ ] Tests pass: `pytest tests/ -v` — ALL GREEN.
- [ ] Existing tests KHÔNG bị break.
- [ ] Test mới cover 100% critical paths.
- [ ] Test leakage guard pass (nếu liên quan đến features/backtest).

### ✅ Data Integrity

- [ ] Leading zeros preserved: `len(loto_number) == 2`, `type(loto_number) == str`.
- [ ] Mỗi ngày XSMB hợp lệ có đúng **27 giải**.
- [ ] Số xổ số **LUÔN** lưu dạng `str`, KHÔNG BAO GIỜ `int`.
- [ ] Target datasets: loto_2d = 100 rows/date, db_2d = 100 rows/date (1 positive), db_3d = 1000 rows/date (1 positive).
- [ ] Target types KHÔNG bị gộp hoặc trộn lẫn.

### ✅ No Future Leakage

- [ ] Features cho `target_date` chỉ dùng dữ liệu `< target_date`.
- [ ] Backtest: train data dates `< test date`.
- [ ] Scaler fit chỉ trên train data (nếu áp dụng).
- [ ] Unit test chống leakage pass.

### ✅ Output Quality

- [ ] Predictions output dạng ranking xác suất: `0.0 ≤ P ≤ 1.0`.
- [ ] Output KHÔNG chứa khẳng định "chắc chắn", "bao trúng", "guaranteed".
- [ ] Backtest reports có baseline comparison.
- [ ] CSV/JSON output đúng format đã spec.

### ✅ Logging & Reports

- [ ] Logs ghi nhận: start time, end time, record counts, errors.
- [ ] Reports lưu đúng nơi: `data/reports/`.
- [ ] Model files lưu đúng nơi: `data/models/`.
- [ ] Raw data lưu trong DB (không mất khi re-parse).

---

## Per-Phase Done Criteria

### Phase 1 — Foundation ✅ when:
- DB initialized with 10 tables.
- `from xsmb.config import PRIZE_STRUCTURE` works.
- `from xsmb.database.connection import get_connection` works.

### Phase 2 — Scraping ✅ when:
- Crawl 1 date → raw HTML in DB.
- Crawl 7 dates → correct count.
- Rate limiting verified.

### Phase 3 — Parser ✅ when:
- Parse real HTML → 27 PrizeEntry.
- Leading zeros preserved.
- Invalid HTML → ParseError.
- All parser/normalize/transform tests pass.

### Phase 4 — Targets ✅ when:
- loto_2d: 100 rows, labels correct.
- db_2d: 100 rows, exactly 1 positive.
- db_3d: 1000 rows, exactly 1 positive.
- Targets are separate.

### Phase 5 — Features ✅ when:
- Feature dataset built for all 3 target types.
- No leakage test passes.
- CSV output in `data/processed/`.

### Phase 6 — Baselines ✅ when:
- 3 baselines produce valid output.
- Deterministic.
- Valid probabilities.

### Phase 7 — ML ✅ when:
- Logistic + HGB trained.
- Model files saved.
- Predictions valid.
- Calibration checked.

### Phase 8 — Backtest ✅ when:
- Walk-forward works.
- No random split.
- Metrics computed.
- CSV report generated.
- Baseline comparison included.

### Phase 9 — CLI ✅ when:
- All commands work end-to-end.
- `--help` works.
- Pipeline: scrape → process → features → train → backtest → predict.

### Phase 10 — API/Dashboard ✅ when:
- API serves predictions.
- Dashboard displays data.
- Disclaimer shown.

---

## Anti-Patterns (Things that make it NOT done)

- ❌ `int("05")` → mất leading zero → NOT DONE.
- ❌ Random train/test split → NOT DONE.
- ❌ Feature dùng data >= target_date → NOT DONE.
- ❌ Gộp loto_2d và db_2cang → NOT DONE.
- ❌ "Mô hình dự đoán chắc chắn" → NOT DONE (ethical violation).
- ❌ Tests fail → NOT DONE.
- ❌ Existing tests broken → NOT DONE.
- ❌ Print statements in library code → NOT DONE.
