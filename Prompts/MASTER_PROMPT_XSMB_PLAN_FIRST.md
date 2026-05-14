# MASTER PROMPT — XSMB ML SYSTEM / PLAN-FIRST VIBE CODING

Bạn là **Principal ML Engineer + Software Architect + Data Engineer**. Nhiệm vụ của bạn là tiếp quản repository hiện có `xsmb-ml-system` và chuẩn bị kế hoạch phát triển thật kỹ trước khi code. Đây là hệ thống nghiên cứu/thống kê Machine Learning cho Xổ Số Miền Bắc (XSMB), không phải hệ thống cam kết dự đoán chắc chắn.

## RUN MODE

**PLAN_FIRST_ONLY**.

Ở lượt chạy đầu tiên, bạn **KHÔNG ĐƯỢC CODE TÍNH NĂNG**. Bạn chỉ được:
1. Đọc/audit toàn bộ repository.
2. Hiểu domain XSMB.
3. Tạo thư mục chứa tài liệu kế hoạch.
4. Viết plan chi tiết, checklist, kiến trúc, data contract, test plan, implementation roadmap.
5. Kết thúc bằng báo cáo ngắn gọn: đã tạo file nào, rủi ro nào, bước code tiếp theo là gì.

Chỉ khi tôi trả lời rõ ràng: **APPROVE PLAN, START CODING**, bạn mới được triển khai code theo plan.

---

## BỐI CẢNH DỰ ÁN

Repository hiện có tên: `xsmb-ml-system`.

Mục tiêu: xây dựng hệ thống Python end-to-end để:
- thu thập dữ liệu kết quả XSMB hợp pháp;
- lưu raw HTML/source response;
- parse kết quả đầy đủ;
- chuẩn hóa dữ liệu;
- sinh dataset cho bài toán 2 càng / 3 càng / loto 2 số theo đúng định nghĩa XSMB;
- tạo feature không rò rỉ tương lai;
- huấn luyện baseline và ML models;
- backtest nghiêm ngặt theo thời gian;
- xuất ranking xác suất, không xuất khẳng định chắc chắn;
- cung cấp CLI trước, API/dashboard sau.

Hệ thống này chỉ phục vụ **nghiên cứu thống kê, phân tích xác suất và kiểm thử thuật toán**. Tuyệt đối không viết nội dung hứa hẹn thắng, chắc ăn, bao trúng, hoặc tối ưu hành vi cá cược/lô đề trái phép.

---

## PHẠM VI XSMB — KHÔNG ĐƯỢC LẪN MIỀN NAM / MIỀN TRUNG

Hệ thống hiện tại phải tập trung **Xổ Số Miền Bắc**.

Một kỳ kết quả XSMB chuẩn cần parse các giải chính sau:

```text
special / gdb : 1 số, thường 5 chữ số
first   / g1  : 1 số, 5 chữ số
second  / g2  : 2 số, 5 chữ số
third   / g3  : 6 số, 5 chữ số
fourth  / g4  : 4 số, 4 chữ số
fifth   / g5  : 6 số, 4 chữ số
sixth   / g6  : 3 số, 3 chữ số
seventh / g7  : 4 số, 2 chữ số
```

Tổng số kết quả giải chính: `1 + 1 + 2 + 6 + 4 + 6 + 3 + 4 = 27`.

Tất cả số phải lưu dạng `str`, không lưu dạng `int`, để giữ số 0 đầu như `00`, `01`, `05`, `009`, `00012`.

---

## ĐỊNH NGHĨA TARGET BẮT BUỘC PHẢI CHỐT TRONG PLAN

Trước khi code, bạn phải viết rõ trong plan các target sau và đề xuất schema/module hỗ trợ từng loại:

### 1. `loto_2d_all_prizes`
- Không phải “đề”.
- Lấy **2 chữ số cuối** của cả 27 kết quả giải chính trong ngày.
- Một ngày có 27 entry, có thể trùng số.
- Dataset binary classification: mỗi ngày tạo 100 rows cho `00..99`.
- `label=1` nếu số đó xuất hiện ít nhất một lần trong 27 entry.
- `actual_hits` = số nháy thực tế của số đó trong 27 entry.

### 2. `db_2cang`
- Lấy **2 chữ số cuối của giải đặc biệt**.
- Một ngày chỉ có 1 target trong `00..99`.
- Bài toán có thể biểu diễn theo 2 cách:
  - multiclass classification 100 classes; hoặc
  - ranking/binary one-vs-rest: mỗi ngày 100 rows, chỉ 1 row label=1.

### 3. `db_3cang`
- Lấy **3 chữ số cuối của giải đặc biệt**.
- Một ngày chỉ có 1 target trong `000..999`.
- Bài toán có thể biểu diễn theo 2 cách:
  - multiclass classification 1000 classes; hoặc
  - ranking/binary one-vs-rest: mỗi ngày 1000 rows, chỉ 1 row label=1.

### 4. Không tự ý gộp các target
Không được dùng target của `loto_2d_all_prizes` để đánh giá `db_2cang`. Không được lấy 27 giải để kết luận cho 2 càng đặc biệt. Mỗi target phải có metric riêng, dataset riêng, baseline riêng.

---

## NHỮNG VIỆC PHẢI LÀM TRƯỚC KHI CODE

### Bước 0 — Repository audit
Đọc toàn bộ repo hiện có, tối thiểu các file:
- `README.md`
- `PROJECT_SPEC.md`
- `DATA_CONTRACT.md`
- `MODEL_SPEC.md`
- `BACKTEST_SPEC.md`
- `AGENTS.md`
- `pyproject.toml`
- toàn bộ cây thư mục `xsmb/`, `app/`, `tests/`, `data/`

Ghi nhận:
- file nào đã có nội dung;
- file nào đang rỗng;
- spec nào còn thiếu;
- spec nào đang mâu thuẫn với yêu cầu mới 2 càng / 3 càng;
- rủi ro thiết kế;
- thứ tự triển khai hợp lý.

### Bước 1 — Tạo thư mục plan
Tạo thư mục mới:

```text
plans/YYYY-MM-DD-xsmb-plan-first/
```

Ví dụ:

```text
plans/2026-05-14-xsmb-plan-first/
```

Không ghi đè plan cũ. Nếu folder đã tồn tại, thêm suffix `-v2`, `-v3`.

### Bước 2 — Viết bộ tài liệu plan
Trong thư mục plan, tạo các file sau:

```text
00_REPO_AUDIT.md
01_DOMAIN_XSMB_DEFINITIONS.md
02_PRODUCT_REQUIREMENTS.md
03_DATA_CONTRACT_V2.md
04_DATABASE_SCHEMA_PLAN.md
05_SCRAPING_AND_INGESTION_PLAN.md
06_PROCESSING_AND_VALIDATION_PLAN.md
07_TARGET_AND_FEATURE_PLAN.md
08_MODELING_PLAN.md
09_BACKTEST_AND_METRICS_PLAN.md
10_CLI_API_DASHBOARD_PLAN.md
11_TESTING_QA_PLAN.md
12_IMPLEMENTATION_ROADMAP.md
13_RISK_REGISTER.md
14_DEFINITION_OF_DONE.md
15_AGENT_CODING_PROMPTS.md
```

### Bước 3 — Không code tính năng
Trong mode này, không sửa các file Python tính năng như:
- `xsmb/scraping/*.py`
- `xsmb/database/*.py`
- `xsmb/processing/*.py`
- `xsmb/features/*.py`
- `xsmb/models/*.py`
- `xsmb/api/*.py`
- `xsmb/dashboard/*.py`
- `app/main.py`

Ngoại lệ: được phép thêm file `.gitkeep` nếu cần giữ thư mục, nhưng không cần thiết.

---

## NỘI DUNG CHI TIẾT TỪNG FILE PLAN

### `00_REPO_AUDIT.md`
Phải có:
- cây thư mục hiện tại;
- trạng thái từng nhóm module;
- file có nội dung / file rỗng;
- nhận xét về specs hiện có;
- điểm mạnh của codebase;
- điểm thiếu;
- mâu thuẫn giữa spec cũ và yêu cầu mới;
- đề xuất cập nhật.

### `01_DOMAIN_XSMB_DEFINITIONS.md`
Phải có:
- định nghĩa kỳ quay XSMB;
- danh sách 27 giải chính;
- độ dài số theo từng giải;
- định nghĩa `loto_2d_all_prizes`, `db_2cang`, `db_3cang`;
- quy tắc giữ leading zero;
- ví dụ parse một ngày;
- các case lỗi: thiếu giải, thừa giải, sai độ dài, ký tự không phải số.

### `02_PRODUCT_REQUIREMENTS.md`
Phải có:
- mục tiêu MVP;
- ngoài phạm vi MVP;
- personas: researcher, developer, analyst;
- user stories;
- acceptance criteria;
- non-functional requirements: reproducibility, logging, deterministic pipeline, no leakage.

### `03_DATA_CONTRACT_V2.md`
Phải có schema logic cho:
- raw source responses;
- draw results full;
- loto 2D all prizes;
- special 2D target;
- special 3D target;
- features dataset;
- predictions;
- backtest reports.

Bắt buộc nêu kiểu dữ liệu:
- số xổ số: `TEXT`/`str`;
- ngày: ISO `YYYY-MM-DD`;
- xác suất: float trong `[0, 1]`;
- model version/run id.

### `04_DATABASE_SCHEMA_PLAN.md`
Phải đề xuất SQLite schema cho MVP:
- `raw_results`
- `draw_results`
- `targets_loto_2d`
- `targets_db_2d`
- `targets_db_3d`
- `feature_rows`
- `model_runs`
- `predictions`
- `backtest_runs`
- `backtest_predictions`

Phải có index/unique constraints để tránh duplicate.

### `05_SCRAPING_AND_INGESTION_PLAN.md`
Phải có:
- nguồn dữ liệu hợp pháp/đáng tin;
- thiết kế `sources.py`, `crawler.py`, `parser.py`;
- rate limit;
- retry;
- timeout;
- raw cache;
- idempotency;
- cách re-parse raw HTML khi parser thay đổi;
- không crawl hung hăng.

Nếu chưa biết selector HTML cụ thể, không bịa. Ghi rõ cần tạo adapter theo từng nguồn.

### `06_PROCESSING_AND_VALIDATION_PLAN.md`
Phải có:
- normalize prize tier;
- validate số lượng 27 giải;
- validate độ dài theo tier;
- extract 2D/3D;
- xử lý duplicate;
- xử lý missing dates;
- reject/quarantine invalid draw;
- logging lỗi.

### `07_TARGET_AND_FEATURE_PLAN.md`
Phải có:
- thiết kế target builder cho 3 target types;
- feature groups:
  - frequency windows: 7, 14, 30, 60, 90, 180, 365 kỳ;
  - current gap;
  - max historical gap;
  - average gap;
  - days/draws since last seen;
  - rolling hits count;
  - special-only features cho `db_2cang` và `db_3cang`;
  - calendar features nếu có nhưng không được lạm dụng.
- quy tắc tuyệt đối: feature cho `target_date` chỉ dùng dữ liệu `< target_date`.
- cơ chế unit test chống leakage.

### `08_MODELING_PLAN.md`
Phải có:
- Random baseline;
- Frequency baseline;
- Gap/Gan baseline;
- Logistic Regression;
- RandomForest hoặc HistGradientBoosting;
- optional LightGBM/XGBoost nếu dependency cho phép, nhưng không bắt buộc MVP;
- calibration plan;
- model registry local;
- save/load model;
- prediction output đủ 100 số hoặc 1000 số tùy target.

Không được hứa mô hình chính xác cao. Chỉ được nói model tạo ranking xác suất và phải chứng minh bằng backtest.

### `09_BACKTEST_AND_METRICS_PLAN.md`
Phải có:
- walk-forward validation;
- rolling origin;
- expanding window vs sliding window;
- no random split;
- metrics riêng cho từng target:
  - Brier Score;
  - Log Loss;
  - Precision@K;
  - Recall@K;
  - HitRate@K;
  - AvgHits@K cho loto 2D;
  - calibration curve / reliability table;
  - comparison with random baseline.
- báo cáo CSV/JSON.

Với `db_3cang`, phải nêu rõ class imbalance rất lớn: 1 positive / 999 negative mỗi ngày nếu dùng one-vs-rest.

### `10_CLI_API_DASHBOARD_PLAN.md`
Phải có CLI trước:

```bash
python -m app.main scrape --start-date YYYY-MM-DD --end-date YYYY-MM-DD
python -m app.main process --start-date YYYY-MM-DD --end-date YYYY-MM-DD
python -m app.main build-features --target loto_2d_all_prizes
python -m app.main train --target db_2cang --model logistic
python -m app.main backtest --target db_3cang --start-date YYYY-MM-DD
python -m app.main predict --target loto_2d_all_prizes --date YYYY-MM-DD --top-k 20
```

Sau CLI mới đến API và Streamlit.

### `11_TESTING_QA_PLAN.md`
Phải có test checklist:
- parser test;
- normalize test;
- leading zero test;
- 27 entries test;
- target extraction test;
- feature no-leakage test;
- baseline deterministic test;
- backtest split test;
- metrics test;
- CLI smoke test.

### `12_IMPLEMENTATION_ROADMAP.md`
Chia phase:

Phase 1 — Foundation
- config, logging, database connection, schema, repository.

Phase 2 — Data ingestion
- sources, crawler, raw storage.

Phase 3 — Parser + validation
- parse full draw, validate 27 giải, normalize.

Phase 4 — Target builders
- loto 2D, DB 2 càng, DB 3 càng.

Phase 5 — Features
- frequency, gap, rolling, dataset builder.

Phase 6 — Baselines
- random, frequency, gap.

Phase 7 — ML training
- logistic, tree model, calibration, save/load.

Phase 8 — Backtest
- walk-forward, metrics, reports.

Phase 9 — CLI
- command orchestration.

Phase 10 — API/dashboard
- only after core pipeline passes tests.

Mỗi phase phải có deliverables, files touched, tests, done criteria.

### `13_RISK_REGISTER.md`
Phải có:
- dữ liệu nguồn thay đổi;
- parser sai;
- mất leading zero;
- future leakage;
- overfitting;
- xác suất không calibration;
- hiểu sai target 2 càng/3 càng;
- performance khi `db_3cang` tạo 1000 rows/ngày;
- legal/ethical risk.

### `14_DEFINITION_OF_DONE.md`
Phải có checklist:
- code chạy;
- tests pass;
- không leakage;
- số lưu string;
- một ngày XSMB đủ 27 giải;
- backtest có baseline comparison;
- output xác suất, không khẳng định;
- logs/reports được tạo đúng nơi.

### `15_AGENT_CODING_PROMPTS.md`
Viết các prompt nhỏ cho những lượt code sau, ví dụ:
- Prompt Phase 1 Foundation;
- Prompt Phase 2 Scraping;
- Prompt Phase 3 Parser;
- Prompt Phase 4 Targets;
- Prompt Phase 5 Features;
- Prompt Phase 6 Baselines;
- Prompt Phase 7 ML;
- Prompt Phase 8 Backtest;
- Prompt Phase 9 CLI.

Mỗi prompt nhỏ phải yêu cầu:
- đọc plan liên quan trước;
- chỉ code đúng phase;
- không mở rộng scope;
- chạy test;
- báo cáo file đã sửa.

---

## QUY TẮC THIẾT KẾ KHÔNG ĐƯỢC VI PHẠM

1. Không dùng random split cho time-series.
2. Không tạo feature từ ngày `target_date` hoặc sau đó.
3. Không convert số sang int.
4. Không làm mất leading zero.
5. Không gộp target `loto_2d_all_prizes`, `db_2cang`, `db_3cang`.
6. Không hứa dự đoán chính xác cao.
7. Không thêm frontend trước khi data/backtest ổn.
8. Không thêm dependency nặng nếu MVP chưa cần.
9. Không crawl dữ liệu hung hăng.
10. Không sửa cấu trúc top-level nếu không cần.
11. Không xóa spec cũ; nếu cần thay đổi, tạo bản V2 hoặc ghi migration note.
12. Không code tính năng trong lượt PLAN_FIRST_ONLY.

---

## FORMAT BÁO CÁO CUỐI LƯỢT PLAN

Sau khi tạo plan, trả lời theo format:

```markdown
## Plan created
Folder: `plans/YYYY-MM-DD-xsmb-plan-first/`

## Files created
- `00_REPO_AUDIT.md` — ...
- `01_DOMAIN_XSMB_DEFINITIONS.md` — ...
...

## Key decisions proposed
1. ...
2. ...
3. ...

## Risks to approve
1. ...
2. ...
3. ...

## Ready for next step
Để bắt đầu code, hãy trả lời chính xác:
`APPROVE PLAN, START CODING PHASE 1`
```

---

## CHẤT LƯỢNG KỲ VỌNG

Plan phải đủ chi tiết để một agent khác có thể code theo từng phase mà không phải tự suy diễn domain. Ưu tiên đúng dữ liệu, đúng target, chống leakage và backtest nghiêm túc hơn là làm model phức tạp.

Nếu phát hiện yêu cầu mơ hồ, không dừng lại hỏi ngay. Hãy ghi vào `13_RISK_REGISTER.md` và đề xuất default an toàn trong plan. Với yêu cầu này, default an toàn là:
- `loto_2d_all_prizes`: all 27 prizes;
- `db_2cang`: special prize last 2 digits;
- `db_3cang`: special prize last 3 digits.

Bắt đầu bằng việc audit repository, sau đó tạo thư mục plan và các file plan. Không code tính năng.
