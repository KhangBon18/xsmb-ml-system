# Hợp Đồng Dữ Liệu (Data Contract)

## 1. Định nghĩa một ngày kết quả XSMB
Một ngày kết quả XSMB hợp lệ là ngày có thực hiện quay thưởng và cho ra kết quả của toàn bộ các giải. Bất kỳ ngày nào không quay thưởng (Lễ, Tết, sự cố) sẽ không tồn tại dữ liệu trong hệ thống, và chuỗi thời gian (time-series) sẽ bỏ qua ngày đó (tính khoảng cách số ngày dựa trên số kỳ quay thực tế).

## 2. Danh sách các giải cần parse
Một kỳ quay XSMB tiêu chuẩn bao gồm đúng 27 giải, phân bổ theo các hạng giải (Prize Tier) như sau:
- Giải Đặc biệt (Special): 1 giải (mỗi giải 5 chữ số)
- Giải Nhất (1st): 1 giải (5 chữ số)
- Giải Nhì (2nd): 2 giải (5 chữ số)
- Giải Ba (3rd): 6 giải (5 chữ số)
- Giải Tư (4th): 4 giải (4 chữ số)
- Giải Năm (5th): 6 giải (4 chữ số)
- Giải Sáu (6th): 3 giải (3 chữ số)
- Giải Bảy (7th): 4 giải (2 chữ số)
Tổng cộng: 1 + 1 + 2 + 6 + 4 + 6 + 3 + 4 = 27 giải.

## 3. Cách sinh 27 loto 2 chữ số
- Thuật toán: Trích xuất **2 chữ số cuối cùng** của từng giải trong 27 giải.
- Ví dụ: 
  - Giải đặc biệt "45678" -> Loto "78"
  - Giải sáu "105" -> Loto "05"
  - Giải bảy "02" -> Loto "02"

## 4. Schema các bảng dữ liệu

### Bảng `raw_results` (Lưu trữ thô)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PK | Auto-increment ID |
| `draw_date` | DATE | Ngày quay thưởng (YYYY-MM-DD) |
| `source_url` | TEXT | URL nguồn đã cào |
| `raw_html` | TEXT | Nội dung HTML thô, dùng để re-parse nếu cần |
| `crawled_at` | TIMESTAMP | Thời gian thực hiện cào dữ liệu |

### Bảng `draw_results` (Kết quả đầy đủ)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PK | Auto-increment ID |
| `draw_date` | DATE | Ngày quay thưởng |
| `prize_tier` | TEXT | Hạng giải (VD: 'special', 'first', 'second', ..., 'seventh') |
| `prize_index` | INTEGER | Thứ tự giải trong hạng (VD: Giải 3 thứ 1 là 0, thứ 2 là 1) |
| `winning_number`| TEXT | Con số trúng thưởng toàn phần (Phải là String để giữ số 0 đầu) |

### Bảng `loto_2digits` (Kết quả Loto 2 số)
| Column | Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PK | Auto-increment ID |
| `draw_date` | DATE | Ngày quay thưởng |
| `prize_tier` | TEXT | Hạng giải tương ứng |
| `prize_index` | INTEGER | Thứ tự giải trong hạng |
| `loto_number` | TEXT | 2 chữ số cuối (Ví dụ: "01", "89", "00") |

## 5. Quy tắc giữ "leading zero" (Sống còn)
TẤT CẢ các con số (cả `winning_number` và `loto_number`) phải luôn được định nghĩa, xử lý và lưu trữ ở định dạng chuỗi (`TEXT`/`VARCHAR` trong DB, `str` trong Python).
Tuyệt đối không ép kiểu (cast) về Integer, vì điều đó sẽ làm mất số `0` ở đầu. (VD: "05" biến thành `5` là sai quy chuẩn loto 2 chữ số). Các số loto luôn có độ dài chuẩn là 2 ký tự.

## 6. Quy tắc Validate dữ liệu
Ở bước Transform/Validation, hệ thống bắt buộc kiểm tra:
1. `count(loto_number) == 27` cho mỗi `draw_date`. Nếu thiếu hoặc thừa, đánh dấu Error và từ chối lưu.
2. `len(loto_number) == 2` cho mọi bản ghi loto.
3. Độ dài `winning_number` phải khớp với quy định của `prize_tier` (VD: Special phải có 5 ký tự).
4. `loto_number` chỉ bao gồm các ký tự số (`.isdigit() == True`).

## 7. Ví dụ dữ liệu chuẩn hóa
Bảng `loto_2digits` cho ngày `2023-10-25`:

| draw_date  | prize_tier | prize_index | loto_number |
| :---       | :---       | :---        | :---        |
| 2023-10-25 | special    | 0           | "45"        |
| 2023-10-25 | first      | 0           | "12"        |
| 2023-10-25 | second     | 0           | "09"        |
| ...        | ...        | ...         | ...         |
| 2023-10-25 | seventh    | 3           | "00"        |
*(Tổng đúng 27 dòng cho draw_date 2023-10-25)*
