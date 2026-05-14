# 00 — Repository Audit

**Ngày audit:** 2026-05-14
**Auditor:** AI Agent (Plan-First Mode)

---

## 1. Cây thư mục hiện tại

```text
xsmb-ml-system/
├── .env.example                 (213 bytes — có nội dung)
├── AGENTS.md                    (3202 bytes — có nội dung)
├── BACKTEST_SPEC.md             (4167 bytes — có nội dung)
├── DATA_CONTRACT.md             (4205 bytes — có nội dung)
├── MASTER_PROMPT_XSMB_PLAN_FIRST.md (14504 bytes — prompt chỉ đạo)
├── MODEL_SPEC.md                (4148 bytes — có nội dung)
├── PROJECT_SPEC.md              (5357 bytes — có nội dung)
├── README.md                    (890 bytes — có nội dung)
├── docker-compose.yml           (810 bytes — có nội dung, dùng PostgreSQL)
├── pyproject.toml               (635 bytes — có nội dung)
│
├── app/
│   └── main.py                  (0 bytes — RỖNG)
│
├── xsmb/
│   ├── config.py                (0 bytes — RỖNG)
│   │
│   ├── scraping/
│   │   ├── __init__.py          (0 bytes — RỖNG)
│   │   ├── sources.py           (0 bytes — RỖNG)
│   │   ├── crawler.py           (0 bytes — RỖNG)
│   │   └── parser.py            (0 bytes — RỖNG)
│   │
│   ├── database/
│   │   ├── __init__.py          (0 bytes — RỖNG)
│   │   ├── connection.py        (0 bytes — RỖNG)
│   │   ├── repository.py        (0 bytes — RỖNG)
│   │   └── schema.sql           (0 bytes — RỖNG)
│   │
│   ├── processing/
│   │   ├── normalize.py         (0 bytes — RỖNG)
│   │   ├── validate.py          (0 bytes — RỖNG)
│   │   └── transform.py         (0 bytes — RỖNG)
│   │
│   ├── features/
│   │   ├── build_dataset.py     (0 bytes — RỖNG)
│   │   ├── frequency_features.py(0 bytes — RỖNG)
│   │   ├── gap_features.py      (0 bytes — RỖNG)
│   │   └── rolling_features.py  (0 bytes — RỖNG)
│   │
│   ├── models/
│   │   ├── baseline.py          (0 bytes — RỖNG)
│   │   ├── train.py             (0 bytes — RỖNG)
│   │   ├── predict.py           (0 bytes — RỖNG)
│   │   ├── evaluate.py          (0 bytes — RỖNG)
│   │   └── backtest.py          (0 bytes — RỖNG)
│   │
│   ├── api/
│   │   ├── routes.py            (0 bytes — RỖNG)
│   │   └── schemas.py           (0 bytes — RỖNG)
│   │
│   └── dashboard/
│       └── streamlit_app.py     (0 bytes — RỖNG)
│
├── tests/
│   ├── test_parser.py           (0 bytes — RỖNG)
│   ├── test_normalize.py        (0 bytes — RỖNG)
│   ├── test_features.py         (0 bytes — RỖNG)
│   └── test_backtest.py         (0 bytes — RỖNG)
│
├── data/
│   ├── raw/                     (rỗng)
│   ├── processed/               (rỗng)
│   ├── models/                  (rỗng)
│   └── reports/                 (rỗng)
│
└── plans/
    └── 2026-05-14-xsmb-plan-first/ (rỗng — sẽ chứa plan này)
```

---

## 2. Trạng thái từng nhóm module

| Nhóm | Files | Trạng thái | Ghi chú |
|:---|:---|:---|:---|
| **Config** | `xsmb/config.py` | ❌ RỖNG | Chưa có logging, paths, constants |
| **Scraping** | `sources.py`, `crawler.py`, `parser.py`, `__init__.py` | ❌ TẤT CẢ RỖNG | Chỉ có skeleton files |
| **Database** | `connection.py`, `repository.py`, `schema.sql`, `__init__.py` | ❌ TẤT CẢ RỖNG | Schema chưa viết |
| **Processing** | `normalize.py`, `validate.py`, `transform.py` | ❌ TẤT CẢ RỖNG | |
| **Features** | `build_dataset.py`, `frequency_features.py`, `gap_features.py`, `rolling_features.py` | ❌ TẤT CẢ RỖNG | |
| **Models** | `baseline.py`, `train.py`, `predict.py`, `evaluate.py`, `backtest.py` | ❌ TẤT CẢ RỖNG | |
| **API** | `routes.py`, `schemas.py` | ❌ TẤT CẢ RỖNG | |
| **Dashboard** | `streamlit_app.py` | ❌ RỖNG | |
| **App Entry** | `app/main.py` | ❌ RỖNG | Chưa có CLI |
| **Tests** | 4 test files | ❌ TẤT CẢ RỖNG | |
| **Data dirs** | `raw/`, `processed/`, `models/`, `reports/` | ✅ Có thư mục | Rỗng, sẵn sàng |

**Kết luận:** Repository 100% là skeleton. Tất cả 26 file Python và 1 file SQL đều rỗng (0 bytes). Chỉ có documentation specs là có nội dung.

---

## 3. Nhận xét về specs hiện có

### 3.1. Các file spec có nội dung tốt

| File | Chất lượng | Nhận xét |
|:---|:---|:---|
| `PROJECT_SPEC.md` | ✅ Tốt | Rõ ràng scope MVP, kiến trúc modular, pipeline, rủi ro |
| `DATA_CONTRACT.md` | ✅ Tốt | Đúng 27 giải, schema `raw_results` + `draw_results` + `loto_2digits`, leading zero rule |
| `MODEL_SPEC.md` | ✅ Tốt | Binary classification đúng, 100 rows/ngày, feature groups, baselines, calibration |
| `BACKTEST_SPEC.md` | ✅ Tốt | Rolling origin, no random split, metrics rõ (Brier, Log Loss, P@K, Hit@K, Avg@K), report format |
| `AGENTS.md` | ✅ Tốt | Coding rules rõ ràng, preferred stack, testing policy |
| `README.md` | ⚠️ Sơ sài | Chỉ giới thiệu cấu trúc thư mục, thiếu hướng dẫn chi tiết |

### 3.2. Điểm mạnh của specs

1. **Leading zero rule** được nhấn mạnh nhiều lần — đúng ưu tiên.
2. **27 giải validation** đã được xác lập rõ.
3. **No future leakage** được quy định nghiêm ngặt ở cả MODEL_SPEC và BACKTEST_SPEC.
4. **Binary classification framing** cho loto 2D là hợp lý (100 rows/ngày).
5. **Calibration requirement** (CalibratedClassifierCV) là thiết kế đúng.
6. **Output format** dạng JSON ranking xác suất — không hứa hẹn.

### 3.3. Điểm thiếu và khoảng trống

1. **Không có khái niệm `db_2cang` và `db_3cang`**: Tất cả specs hiện tại chỉ nói đến `loto_2d_all_prizes` (27 giải → 2 chữ số cuối). Chưa có bất kỳ đề cập nào đến:
   - Đề 2 càng (2 chữ số cuối giải ĐB) — 1 target/ngày trong 100 classes
   - Đề 3 càng (3 chữ số cuối giải ĐB) — 1 target/ngày trong 1000 classes

2. **Database dùng PostgreSQL trong docker-compose** nhưng `AGENTS.md` yêu cầu SQLite cho MVP. Mâu thuẫn.

3. **pyproject.toml dùng `sqlalchemy` + `psycopg2-binary`** — phù hợp PostgreSQL nhưng không phù hợp SQLite MVP.

4. **Thiếu `__init__.py`** ở nhiều package: `xsmb/`, `xsmb/processing/`, `xsmb/features/`, `xsmb/models/`, `xsmb/api/`, `xsmb/dashboard/`.

5. **Thiếu bảng target** trong DATA_CONTRACT: không có `targets_loto_2d`, `targets_db_2d`, `targets_db_3d`.

6. **Không có CLI plan** cụ thể — `PROJECT_SPEC.md` chỉ liệt kê commands mẫu.

7. **Thiếu `__init__.py` cho `tests/`** — pytest có thể hoạt động, nhưng không chuẩn.

8. **Thiếu model registry/save-load spec** — MODEL_SPEC chỉ nói output format.

9. **Thiếu idempotency spec** cho scraping — crawl lại cùng ngày nên skip hay overwrite?

---

## 4. Mâu thuẫn giữa spec cũ và yêu cầu mới

| # | Spec cũ | Yêu cầu mới (MASTER_PROMPT) | Hành động đề xuất |
|:---|:---|:---|:---|
| 1 | DB: PostgreSQL (docker-compose.yml, .env.example, pyproject.toml dùng psycopg2) | AGENTS.md yêu cầu SQLite cho MVP | **Chuyển sang SQLite** cho MVP. Giữ docker-compose cho phase sau. Bỏ psycopg2, thêm sqlite3 (stdlib). |
| 2 | DATA_CONTRACT chỉ có `loto_2digits` | Cần thêm `targets_db_2d` (đề 2 càng) và `targets_db_3d` (đề 3 càng) | **Tạo DATA_CONTRACT_V2** bổ sung 3 target types riêng biệt. |
| 3 | MODEL_SPEC chỉ nói binary classification 100 rows/ngày cho loto 2D | `db_2cang` cần 100 rows/ngày (only 1 positive), `db_3cang` cần 1000 rows/ngày (only 1 positive) | **Cập nhật MODELING_PLAN** hỗ trợ cả 3 target types với metric riêng. |
| 4 | BACKTEST_SPEC chỉ nói backtest cho loto 2D | Cần backtest riêng cho mỗi target type | **Tạo BACKTEST plan** cho 3 target types. |
| 5 | pyproject.toml dùng `requests` | AGENTS.md cho phép `requests` hoặc `httpx` | Giữ `requests` cho MVP (đơn giản hơn). |
| 6 | Feature groups không phân biệt loto vs special | Feature cho `db_2cang`/`db_3cang` cần feature từ giải ĐB riêng | **Thiết kế feature builder theo target type.** |

---

## 5. Rủi ro thiết kế

| # | Rủi ro | Mức độ | Giải pháp đề xuất |
|:---|:---|:---|:---|
| R1 | `db_3cang` tạo 1000 rows/ngày × nhiều năm = dataset rất lớn | Cao | Tối ưu query, batch processing, lazy loading |
| R2 | Class imbalance `db_3cang`: 1 positive / 999 negative | Cao | Stratified metrics, class weights, ranking-based evaluation |
| R3 | Nguồn scraping thay đổi HTML → parser gãy | Trung bình | Raw cache + adapter pattern per source |
| R4 | Mất leading zero khi xử lý số | Cao | Strict type enforcement, test coverage |
| R5 | Future leakage trong feature computation | Cao | Unit test `assert max(feature_dates) < target_date` |

---

## 6. Thứ tự triển khai hợp lý

```
Phase 1: Foundation (config, logging, DB connection, schema)
Phase 2: Data Ingestion (sources, crawler, raw storage)
Phase 3: Parser + Validation (parse 27 giải, validate, normalize)
Phase 4: Target Builders (loto_2d, db_2cang, db_3cang)
Phase 5: Features (frequency, gap, rolling, dataset builder)
Phase 6: Baselines (random, frequency, gap)
Phase 7: ML Training (logistic, tree, calibration)
Phase 8: Backtest (walk-forward, metrics, reports)
Phase 9: CLI (command orchestration)
Phase 10: API + Dashboard (only after pipeline works)
```

---

## 7. Tổng kết

- **Tình trạng**: Greenfield project — 100% skeleton, 0% implementation.
- **Specs**: 5/6 specs có nội dung tốt, nhưng thiếu coverage cho `db_2cang`/`db_3cang`.
- **Mâu thuẫn chính**: PostgreSQL vs SQLite MVP.
- **Ưu tiên**: Xây foundation đúng từ đầu, tránh phải refactor lại data layer sau.
- **Hành động tiếp theo**: Viết plan chi tiết cho 16 files trong thư mục `plans/`.
