# 06 — Processing and Validation Plan

---

## 1. Processing Pipeline

```
[DB: draw_results]
    │
    ├── normalize_prize_tier()
    ├── validate_draw_date()
    ├── validate_prize_count()
    ├── validate_digit_lengths()
    ├── validate_digits_only()
    │
    ▼ (nếu TẤT CẢ pass)
[DB: loto_2digits]          ← extract 2 chữ số cuối
    │
    ├── build_targets_loto_2d()
    ├── build_targets_db_2d()
    └── build_targets_db_3d()
    │
    ▼
[DB: targets_loto_2d, targets_db_2d, targets_db_3d]
```

---

## 2. Module: `normalize.py`

### 2.1. Normalize prize tier names

Đảm bảo prize_tier luôn ở dạng chuẩn lowercase:

```python
VALID_PRIZE_TIERS = [
    "special", "first", "second", "third",
    "fourth", "fifth", "sixth", "seventh"
]

TIER_ALIASES = {
    "gdb": "special", "đặc biệt": "special", "đb": "special",
    "g1": "first", "nhất": "first",
    "g2": "second", "nhì": "second",
    "g3": "third", "ba": "third",
    "g4": "fourth", "tư": "fourth",
    "g5": "fifth", "năm": "fifth",
    "g6": "sixth", "sáu": "sixth",
    "g7": "seventh", "bảy": "seventh",
}

def normalize_prize_tier(raw_tier: str) -> str:
    """Normalize raw prize tier string to standard form."""
    ...
```

### 2.2. Normalize winning number

```python
def normalize_winning_number(raw_number: str) -> str:
    """Strip whitespace, remove dots/commas, validate digits-only.

    Returns cleaned number string.
    Raises ValueError if non-digit characters remain.
    """
    cleaned = raw_number.strip().replace(".", "").replace(",", "").replace(" ", "")
    if not cleaned.isdigit():
        raise ValueError(f"Non-digit characters in number: {raw_number!r}")
    return cleaned
```

---

## 3. Module: `validate.py`

### 3.1. Validation Functions

```python
from xsmb.processing.normalize import PRIZE_STRUCTURE

def validate_draw(prizes: list[PrizeEntry]) -> ValidationResult:
    """Validate a full day's draw results.

    Checks:
    1. Total count == 27
    2. Count per tier matches PRIZE_STRUCTURE
    3. Digit length per tier matches specification
    4. All numbers are digits-only
    5. Prize indices are sequential (0-indexed)

    Returns ValidationResult with status and errors list.
    """
    ...
```

### 3.2. Validation Result

```python
@dataclass
class ValidationResult:
    is_valid: bool
    draw_date: str
    total_prizes: int
    errors: list[str]       # list of error messages
    warnings: list[str]     # non-fatal issues
```

### 3.3. Validation Rules (Matrix)

| Rule | Check | Severity | Action on fail |
|:---|:---|:---|:---|
| V1: Total count | `len(prizes) == 27` | ERROR | REJECT entire draw |
| V2: Tier count | count per tier matches spec | ERROR | REJECT |
| V3: Digit length | `len(number) == expected` | ERROR | REJECT |
| V4: Digits only | `number.isdigit()` | ERROR | REJECT |
| V5: Prize index | sequential 0..(count-1) per tier | ERROR | REJECT |
| V6: Date format | `YYYY-MM-DD` regex match | ERROR | REJECT |
| V7: Duplicate check | no duplicate (tier, index) | WARNING | Deduplicate |

### 3.4. Reject / Quarantine

- Rejected draws are NOT inserted into `draw_results`.
- Log full error details.
- Optionally save to a `rejected_draws` table for investigation:

```sql
CREATE TABLE IF NOT EXISTS rejected_draws (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    draw_date   TEXT NOT NULL,
    source_name TEXT NOT NULL,
    error_type  TEXT NOT NULL,
    error_detail TEXT NOT NULL,
    created_at  TEXT NOT NULL
);
```

---

## 4. Module: `transform.py`

### 4.1. Extract loto 2 digits

```python
def extract_loto_2d(winning_number: str) -> str:
    """Extract last 2 digits from a winning number.

    MUST use string slicing, never int conversion.

    Examples:
        "45678" -> "78"
        "00512" -> "12"
        "105"   -> "05"
        "02"    -> "02"
    """
    return winning_number[-2:]
```

### 4.2. Extract special prize targets

```python
def extract_db_2cang(special_number: str) -> str:
    """Extract last 2 digits of special prize for đề 2 càng.

    Example: "45678" -> "78"
    """
    assert len(special_number) == 5, f"Special prize must be 5 digits, got {special_number!r}"
    return special_number[-2:]

def extract_db_3cang(special_number: str) -> str:
    """Extract last 3 digits of special prize for đề 3 càng.

    Example: "45678" -> "678"
    """
    assert len(special_number) == 5, f"Special prize must be 5 digits, got {special_number!r}"
    return special_number[-3:]
```

### 4.3. Build target datasets

```python
def build_targets_loto_2d(
    draw_date: str,
    loto_entries: list[str],    # 27 loto 2-digit strings
) -> list[dict]:
    """Build 100 target rows for loto 2D.

    For each number "00".."99":
      - label = 1 if number in loto_entries, else 0
      - actual_hits = count of number in loto_entries
    """
    ...

def build_targets_db_2d(
    draw_date: str,
    special_number: str,
) -> list[dict]:
    """Build 100 target rows for đề 2 càng.

    Only the last-2-digit match gets label=1.
    """
    target = extract_db_2cang(special_number)
    rows = []
    for i in range(100):
        number = f"{i:02d}"
        rows.append({
            "draw_date": draw_date,
            "number": number,
            "label": 1 if number == target else 0,
        })
    return rows

def build_targets_db_3d(
    draw_date: str,
    special_number: str,
) -> list[dict]:
    """Build 1000 target rows for đề 3 càng.

    Only the last-3-digit match gets label=1.
    """
    target = extract_db_3cang(special_number)
    rows = []
    for i in range(1000):
        number = f"{i:03d}"
        rows.append({
            "draw_date": draw_date,
            "number": number,
            "label": 1 if number == target else 0,
        })
    return rows
```

---

## 5. Xử lý Duplicate Dates

- **Trong DB:** `UNIQUE(draw_date, prize_tier, prize_index)` → INSERT fails nếu duplicate.
- **Application level:** Trước khi process, check xem date đã có trong `draw_results` chưa.
  - Nếu đã có → **SKIP** (default) hoặc **DELETE + RE-INSERT** (với `--force` flag).

---

## 6. Xử lý Missing Dates

- Không tự điền missing dates.
- Khi tính features (gap, frequency), dùng **số kỳ quay thực tế** (không dùng số ngày calendar).
- Query: `SELECT DISTINCT draw_date FROM draw_results ORDER BY draw_date` → đây là danh sách kỳ quay thực tế.

---

## 7. Process Pipeline Command

```bash
# Process raw → draw_results → loto_2digits → targets
python -m app.main process --start-date 2014-01-01 --end-date 2024-12-31

# Chỉ build targets (nếu draw_results đã có)
python -m app.main build-targets --start-date 2014-01-01 --end-date 2024-12-31 --target all
```

---

## 8. Logging Requirements

```
[INFO] Processing 2024-01-15...
[INFO]   Parsed 27 prizes: ✓ valid
[INFO]   Extracted 27 loto 2D entries
[INFO]   Built targets: loto_2d=100 rows, db_2d=100 rows, db_3d=1000 rows
[WARNING] Processing 2024-01-16...
[WARNING]   Parsed 25 prizes: ✗ INVALID (missing 2 prizes in 'third' tier)
[WARNING]   REJECTED: draw_date=2024-01-16, reason=prize_count_mismatch
```
