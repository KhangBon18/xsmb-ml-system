# 01 — Định Nghĩa Miền Xổ Số Miền Bắc (XSMB Domain Definitions)

---

## 1. Kỳ quay XSMB

- XSMB quay thưởng **mỗi ngày**, 365 ngày/năm (trừ một số ngày lễ đặc biệt có thể không quay).
- Thời gian quay: 18:15 hàng ngày.
- Mỗi kỳ quay cho ra **27 con số** từ 8 hạng giải (prize tiers).
- Ngày quay được ghi nhận dạng `YYYY-MM-DD` (ISO 8601).
- Nếu một ngày không có quay thưởng, ngày đó không tồn tại trong hệ thống.

---

## 2. Danh sách 27 giải chính

| Prize Tier | Tên tiếng Việt | Mã giải | Số lượng giải | Độ dài số (chữ số) |
|:---|:---|:---|:---|:---|
| `special` | Giải Đặc biệt | `gdb` | 1 | 5 |
| `first` | Giải Nhất | `g1` | 1 | 5 |
| `second` | Giải Nhì | `g2` | 2 | 5 |
| `third` | Giải Ba | `g3` | 6 | 5 |
| `fourth` | Giải Tư | `g4` | 4 | 4 |
| `fifth` | Giải Năm | `g5` | 6 | 4 |
| `sixth` | Giải Sáu | `g6` | 3 | 3 |
| `seventh` | Giải Bảy | `g7` | 4 | 2 |

**Tổng:** 1 + 1 + 2 + 6 + 4 + 6 + 3 + 4 = **27 giải**

---

## 3. Độ dài số theo từng giải (VALIDATION RULE)

```python
PRIZE_STRUCTURE = {
    "special": {"count": 1, "digits": 5},
    "first":   {"count": 1, "digits": 5},
    "second":  {"count": 2, "digits": 5},
    "third":   {"count": 6, "digits": 5},
    "fourth":  {"count": 4, "digits": 4},
    "fifth":   {"count": 6, "digits": 4},
    "sixth":   {"count": 3, "digits": 3},
    "seventh": {"count": 4, "digits": 2},
}

TOTAL_PRIZES = sum(v["count"] for v in PRIZE_STRUCTURE.values())  # == 27
```

---

## 4. Định nghĩa 3 target types

### 4.1. `loto_2d_all_prizes` — Loto 2 chữ số (toàn bộ 27 giải)

- **Cách tính:** Lấy **2 chữ số cuối** của mỗi giải trong 27 giải.
- **Mỗi ngày:** 27 entries loto 2D, có thể có số trùng nhau (ví dụ số "15" nổ 3 nháy).
- **Phạm vi number:** `"00"` đến `"99"` (100 numbers).
- **Dataset:** Mỗi ngày tạo **100 rows** (1 row cho mỗi number `"00".."99"`).
- **Label:**
  - `label = 1` nếu number xuất hiện **ít nhất 1 lần** trong 27 entries.
  - `label = 0` nếu number không xuất hiện.
- **Trường bổ sung:** `actual_hits` = số lần number thực tế xuất hiện (0, 1, 2, 3...).
- **Tỷ lệ positive tham khảo:** Trung bình mỗi ngày có ~23-25 số unique xuất hiện trong 27 giải → ~23-25% rows label=1.

**Ví dụ:**
```
Ngày 2024-01-15, giải ĐB = "45678"
→ loto 2D từ giải ĐB = "78"
→ Nếu "78" xuất hiện thêm ở giải Ba → actual_hits = 2, label = 1
→ Số "00" không xuất hiện → actual_hits = 0, label = 0
```

### 4.2. `db_2cang` — Đề 2 càng (giải Đặc biệt)

- **Cách tính:** Lấy **2 chữ số cuối của giải Đặc biệt** (special prize only).
- **Mỗi ngày:** Chỉ có **1 target number** duy nhất.
- **Phạm vi number:** `"00"` đến `"99"` (100 numbers).
- **Dataset:** Mỗi ngày tạo **100 rows**.
- **Label:**
  - `label = 1` cho **đúng 1 row** (number trùng 2 chữ số cuối giải ĐB).
  - `label = 0` cho **99 rows** còn lại.
- **Class imbalance:** 1:99 mỗi ngày.
- **KHÔNG ĐƯỢC** dùng kết quả 27 giải để đánh giá target này.

**Ví dụ:**
```
Ngày 2024-01-15, giải ĐB = "45678"
→ db_2cang target = "78"
→ Row number="78": label=1
→ Row number="00".."77","79".."99": label=0
```

### 4.3. `db_3cang` — Đề 3 càng (giải Đặc biệt)

- **Cách tính:** Lấy **3 chữ số cuối của giải Đặc biệt**.
- **Mỗi ngày:** Chỉ có **1 target number** duy nhất.
- **Phạm vi number:** `"000"` đến `"999"` (1000 numbers).
- **Dataset:** Mỗi ngày tạo **1000 rows**.
- **Label:**
  - `label = 1` cho **đúng 1 row**.
  - `label = 0` cho **999 rows** còn lại.
- **Class imbalance:** 1:999 mỗi ngày — **CỰC LỚN**.
- **Ghi chú hiệu năng:** 1000 rows/ngày × 3650 ngày (10 năm) = ~3.65 triệu rows. Cần batch processing.

**Ví dụ:**
```
Ngày 2024-01-15, giải ĐB = "45678"
→ db_3cang target = "678"
→ Row number="678": label=1
→ Còn lại 999 rows: label=0
```

### 4.4. QUY TẮC KHÔNG ĐƯỢC GỘP

> **CRITICAL:** Mỗi target type phải có dataset riêng, feature set riêng (có thể dùng chung feature functions nhưng build riêng), baseline riêng, metric riêng, backtest riêng. KHÔNG ĐƯỢC dùng kết quả backtest của `loto_2d_all_prizes` để kết luận cho `db_2cang`.

---

## 5. Quy tắc giữ leading zero

### 5.1. Quy tắc chung

- **Tất cả** số xổ số phải lưu dạng `str` / `TEXT`.
- **Không bao giờ** ép kiểu sang `int`, `float`, hoặc dùng hàm `int()` trên số xổ số.
- Khi parse: dùng string slicing, không dùng arithmetic.

### 5.2. Ví dụ đúng / sai

| Phép toán | Đúng | Sai |
|:---|:---|:---|
| Trích 2 chữ số cuối từ "00512" | `"00512"[-2:]` → `"12"` | `int("00512") % 100` → `12` (mất leading zero nếu kết quả < 10) |
| Trích 2 chữ số cuối từ "10005" | `"10005"[-2:]` → `"05"` | `10005 % 100` → `5` (mất "0") |
| Trích 3 chữ số cuối từ "45008" | `"45008"[-3:]` → `"008"` | `45008 % 1000` → `8` (mất "00") |
| Lưu giải Bảy "02" | `"02"` (str) | `2` (int) ❌ |
| So sánh | `loto_number == "05"` | `loto_number == 5` ❌ |

### 5.3. Cách tạo number list

```python
# Loto 2D numbers
LOTO_2D_NUMBERS = [f"{i:02d}" for i in range(100)]
# ["00", "01", "02", ..., "99"]

# DB 3 càng numbers
DB_3D_NUMBERS = [f"{i:03d}" for i in range(1000)]
# ["000", "001", "002", ..., "999"]
```

---

## 6. Ví dụ parse một ngày hoàn chỉnh

### Input: Kết quả XSMB ngày 2024-01-15

```text
Giải Đặc biệt: 45678
Giải Nhất:      12345
Giải Nhì:       67890  11223
Giải Ba:        33445  55667  78901  23456  78012  90123
Giải Tư:        1234   5678   9012   3456
Giải Năm:       7890   1234   5678   9012   3456   7890
Giải Sáu:       123    456    789
Giải Bảy:       01     23     45     67
```

### Step 1: Parse `draw_results`

| draw_date | prize_tier | prize_index | winning_number |
|:---|:---|:---|:---|
| 2024-01-15 | special | 0 | "45678" |
| 2024-01-15 | first | 0 | "12345" |
| 2024-01-15 | second | 0 | "67890" |
| 2024-01-15 | second | 1 | "11223" |
| 2024-01-15 | third | 0 | "33445" |
| 2024-01-15 | third | 1 | "55667" |
| 2024-01-15 | third | 2 | "78901" |
| 2024-01-15 | third | 3 | "23456" |
| 2024-01-15 | third | 4 | "78012" |
| 2024-01-15 | third | 5 | "90123" |
| 2024-01-15 | fourth | 0 | "1234" |
| 2024-01-15 | fourth | 1 | "5678" |
| 2024-01-15 | fourth | 2 | "9012" |
| 2024-01-15 | fourth | 3 | "3456" |
| 2024-01-15 | fifth | 0 | "7890" |
| 2024-01-15 | fifth | 1 | "1234" |
| 2024-01-15 | fifth | 2 | "5678" |
| 2024-01-15 | fifth | 3 | "9012" |
| 2024-01-15 | fifth | 4 | "3456" |
| 2024-01-15 | fifth | 5 | "7890" |
| 2024-01-15 | sixth | 0 | "123" |
| 2024-01-15 | sixth | 1 | "456" |
| 2024-01-15 | sixth | 2 | "789" |
| 2024-01-15 | seventh | 0 | "01" |
| 2024-01-15 | seventh | 1 | "23" |
| 2024-01-15 | seventh | 2 | "45" |
| 2024-01-15 | seventh | 3 | "67" |

**Tổng: 27 rows** ✅

### Step 2: Extract loto 2D (2 chữ số cuối)

| loto_number | Nguồn |
|:---|:---|
| "78" | special "45678" |
| "45" | first "12345" |
| "90" | second "67890" |
| "23" | second "11223" |
| "45" | third "33445" |
| "67" | third "55667" |
| "01" | third "78901" |
| "56" | third "23456" |
| "12" | third "78012" |
| "23" | third "90123" |
| "34" | fourth "1234" |
| "78" | fourth "5678" |
| "12" | fourth "9012" |
| "56" | fourth "3456" |
| "90" | fifth "7890" |
| "34" | fifth "1234" |
| "78" | fifth "5678" |
| "12" | fifth "9012" |
| "56" | fifth "3456" |
| "90" | fifth "7890" |
| "23" | sixth "123" |
| "56" | sixth "456" |
| "89" | sixth "789" |
| "01" | seventh "01" |
| "23" | seventh "23" |
| "45" | seventh "45" |
| "67" | seventh "67" |

**Tổng loto entries: 27** ✅

### Step 3: Extract targets

- **`loto_2d_all_prizes`:** Tất cả 27 entries trên → unique numbers có label=1.
- **`db_2cang`:** `"45678"[-2:]` → `"78"`.
- **`db_3cang`:** `"45678"[-3:]` → `"678"`.

---

## 7. Các case lỗi phải xử lý

### 7.1. Thiếu giải

- **Hiện tượng:** HTML page thiếu 1 hoặc nhiều giải (do lỗi crawl hoặc trang web).
- **Xử lý:** Đếm tổng results. Nếu ≠ 27 → `REJECT` ngày đó, log warning, không lưu vào `draw_results`.
- **Không bao giờ** tự điền missing prizes.

### 7.2. Thừa giải

- **Hiện tượng:** Parse ra > 27 prizes (có thể do HTML trùng lặp, div lồng nhau).
- **Xử lý:** `REJECT` ngày đó, log error.

### 7.3. Sai độ dài số

- **Hiện tượng:** Giải Đặc biệt có 4 chữ số thay vì 5, hoặc Giải Bảy có 3 chữ số thay vì 2.
- **Xử lý:** Validate `len(winning_number) == expected_digits` cho từng prize tier. Nếu sai → `REJECT` ngày đó.

### 7.4. Ký tự không phải số

- **Hiện tượng:** Số chứa khoảng trắng, dấu chấm, dấu phẩy, chữ cái (do parse lỗi).
- **Xử lý:** Strip whitespace trước, sau đó `winning_number.isdigit()` → nếu `False` → `REJECT`.

### 7.5. Ngày trùng lặp (duplicate)

- **Hiện tượng:** Crawl cùng ngày nhiều lần.
- **Xử lý:** Sử dụng `UNIQUE(draw_date, prize_tier, prize_index)` trong DB. Crawl lại = UPSERT hoặc SKIP nếu đã tồn tại.

### 7.6. Ngày không quay thưởng

- **Hiện tượng:** Ngày nghỉ lễ, Tết — không có kết quả.
- **Xử lý:** Không tạo record. Gap features phải tính theo **số kỳ quay thực tế**, không phải số ngày lịch.

### 7.7. Giải ĐB có leading zero

- **Hiện tượng:** Giải ĐB = "00512" → nếu dùng `int()` sẽ thành `512`.
- **Xử lý:** Luôn dùng string slicing. `"00512"[-2:]` = `"12"`, `"00512"[-3:]` = `"512"`.

---

## 8. Glossary

| Thuật ngữ | Định nghĩa |
|:---|:---|
| **Loto** | Hệ thống trích xuất 2 chữ số cuối từ tất cả 27 giải XSMB |
| **Nháy (hit)** | Một lần một con số xuất hiện trong 27 entries của 1 ngày |
| **Gan** | Số kỳ quay liên tiếp mà một con số không xuất hiện |
| **Đề 2 càng** | Đoán đúng 2 chữ số cuối của giải Đặc biệt |
| **Đề 3 càng** | Đoán đúng 3 chữ số cuối của giải Đặc biệt |
| **Prize tier** | Hạng giải (special, first, second, ..., seventh) |
| **Prize index** | Thứ tự giải trong cùng một hạng (0-indexed) |
| **Draw date** | Ngày quay thưởng (ISO YYYY-MM-DD) |
