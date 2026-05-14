# 05 — Scraping and Ingestion Plan

---

## 1. Nguồn dữ liệu

### 1.1. Nguồn chính (MVP): `xoso.com.vn`

- URL pattern: `https://xoso.com.vn/xsmb-{dd}-{mm}-{yyyy}.html`
- Trang công khai, không cần authentication.
- Dữ liệu lịch sử khả dụng từ ~2010 trở lại đây.
- HTML structure tương đối ổn định.

### 1.2. Nguồn phụ (backup — post-MVP):

- `https://ketqua.net` — JSON API hoặc HTML.
- `https://minhngoc.net.vn` — HTML tables.

### 1.3. Adapter Pattern

Thiết kế `sources.py` theo adapter pattern để dễ thêm nguồn mới:

```python
# xsmb/scraping/sources.py

from dataclasses import dataclass

@dataclass
class Source:
    name: str
    base_url: str
    url_template: str      # pattern với {date} hoặc {dd}, {mm}, {yyyy}
    response_type: str     # 'html' hoặc 'json'

SOURCES = {
    "xoso_com_vn": Source(
        name="xoso_com_vn",
        base_url="https://xoso.com.vn",
        url_template="https://xoso.com.vn/xsmb-{dd}-{mm}-{yyyy}.html",
        response_type="html",
    ),
}

DEFAULT_SOURCE = "xoso_com_vn"
```

---

## 2. Thiết kế `crawler.py`

### 2.1. Responsibilities

- Nhận date range → sinh danh sách URLs.
- Gửi HTTP GET requests với safety controls.
- Lưu raw response vào `raw_results` table.
- **KHÔNG parse HTML** — chỉ lưu thô.

### 2.2. Safety Controls

| Control | Giá trị | Configurable? |
|:---|:---|:---|
| Timeout | 10 giây | Có (env var) |
| Retry | 3 lần | Có |
| Backoff | Exponential (1s, 2s, 4s) | Có |
| Sleep between requests | Random 1-3 giây | Có |
| User-Agent | `xsmb-ml-system/0.1 (research)` | Có |
| Max concurrent | 1 (sequential) | Cố định cho MVP |

### 2.3. Idempotency

- Trước khi crawl ngày D, check `raw_results` xem đã có chưa.
- Nếu đã có → **SKIP** (default) hoặc **OVERWRITE** (nếu `--force` flag).
- Log: `INFO: Skipping 2024-01-15 (already crawled)`.

### 2.4. Interface

```python
# xsmb/scraping/crawler.py

def crawl_date(
    date: str,
    source: Source,
    repo: XSMBRepository,
    force: bool = False,
    timeout: int = 10,
    max_retries: int = 3,
) -> CrawlResult:
    """Crawl a single date, save raw HTML to DB.

    Returns CrawlResult with status: 'success', 'skipped', 'failed'.
    """
    ...

def crawl_date_range(
    start_date: str,
    end_date: str,
    source: Source,
    repo: XSMBRepository,
    force: bool = False,
) -> list[CrawlResult]:
    """Crawl a range of dates sequentially with sleep between requests."""
    ...
```

### 2.5. Error Handling

| Error | Action |
|:---|:---|
| HTTP 404 | Log WARNING, mark date as "no_data" (có thể ngày không quay), skip |
| HTTP 5xx | Retry up to max_retries, then FAIL |
| Timeout | Retry, then FAIL |
| Connection error | Retry, then FAIL |
| Rate limited (429) | Wait 60s, retry |

---

## 3. Thiết kế `parser.py`

### 3.1. Responsibilities

- Nhận raw HTML → parse thành structured data.
- Output: list of `PrizeEntry(prize_tier, prize_index, winning_number)`.
- Validate count = 27.
- Validate digit lengths.
- **KHÔNG** viết vào DB — chỉ trả về parsed data.

### 3.2. Interface

```python
# xsmb/scraping/parser.py

from dataclasses import dataclass

@dataclass
class PrizeEntry:
    prize_tier: str       # 'special', 'first', ..., 'seventh'
    prize_index: int      # 0-indexed
    winning_number: str   # giữ leading zeros

class ParseError(Exception):
    """Raised when HTML cannot be parsed correctly."""
    pass

def parse_xsmb_html(html: str, source_name: str) -> list[PrizeEntry]:
    """Parse XSMB result page HTML into list of PrizeEntry.

    Args:
        html: raw HTML content
        source_name: adapter name (determines parsing strategy)

    Returns:
        List of exactly 27 PrizeEntry objects.

    Raises:
        ParseError: if HTML structure unexpected or validation fails.
    """
    ...
```

### 3.3. Parser Strategy per Source

- MVP: chỉ implement parser cho `xoso_com_vn`.
- Mỗi source có parser function riêng: `_parse_xoso_com_vn(html)`.
- Dispatch bằng `source_name`.

### 3.4. Chưa biết selector cụ thể — Action Items

> **IMPORTANT:** Cần khảo sát thực tế HTML structure của `xoso.com.vn` trước khi viết parser. Plan này chỉ thiết kế interface. Khi code Phase 3, phải:
> 1. Crawl 1 trang mẫu.
> 2. Inspect HTML structure.
> 3. Xác định CSS selectors/table structure.
> 4. Viết parser dựa trên structure thực tế.
> 5. Không bịa selectors.

---

## 4. Re-parse Flow

Khi parser thay đổi (fix bug, cải tiến):

```
1. KHÔNG cần crawl lại.
2. Đọc raw_content từ raw_results.
3. Xóa draw_results + loto_2digits cho date range bị ảnh hưởng.
4. Re-parse raw_content → insert draw_results + loto_2digits mới.
5. Re-compute targets (nếu bị ảnh hưởng).
```

CLI command: `python -m app.main reparse --start-date X --end-date Y`

---

## 5. Data Flow

```
[Web Source]
    │
    ▼ HTTP GET (with safety controls)
[raw_content]
    │
    ▼ Save to raw_results table
[DB: raw_results]
    │
    ▼ parse_xsmb_html()
[list[PrizeEntry]] (27 items)
    │
    ├──▼ validate_prize_count() == 27
    ├──▼ validate_digit_lengths()
    ├──▼ validate_digits_only()
    │
    ▼ Save to draw_results table
[DB: draw_results]
    │
    ▼ extract_loto_2digits()
[DB: loto_2digits] (27 entries per date)
```

---

## 6. Ingestion Pipeline Command

```bash
# Crawl + parse + store
python -m app.main scrape --start-date 2014-01-01 --end-date 2024-12-31

# Force re-crawl specific dates
python -m app.main scrape --start-date 2024-01-15 --end-date 2024-01-15 --force

# Re-parse without re-crawling
python -m app.main reparse --start-date 2014-01-01 --end-date 2024-12-31
```

---

## 7. Monitoring & Logging

```
[INFO] Starting crawl: 2024-01-01 to 2024-01-31 (source: xoso_com_vn)
[INFO] Crawling 2024-01-01... OK (1.2s)
[INFO] Crawling 2024-01-02... SKIPPED (already exists)
[WARNING] Crawling 2024-01-03... 404 Not Found (holiday?)
[ERROR] Crawling 2024-01-04... FAILED after 3 retries (timeout)
[INFO] Crawl complete: 28/31 success, 1 skipped, 1 not found, 1 failed
[INFO] Parsing 28 raw results...
[INFO] Parse complete: 28/28 valid (27 prizes each)
```
