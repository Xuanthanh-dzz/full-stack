# Hàm scalar, CASE và xử lý NULL

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng các **hàm scalar** phổ biến: chuỗi (`UPPER`, `CONCAT`, `LEN`, `SUBSTRING`), số (`ROUND`, `ABS`), ngày (`YEAR`, `MONTH`, `DATEDIFF`);
- viết biểu thức **`CASE`** để phân loại/ánh xạ giá trị ngay trong truy vấn;
- kết hợp `COALESCE`, `NULLIF`, `ISNULL` để xử lý NULL sạch sẽ;
- hiểu hàm scalar chạy **trên từng hàng**, khác hàm tổng hợp (bài sau) chạy trên nhóm;
- biết các khác biệt phương ngữ hàm giữa SQL Server và PostgreSQL;
- tạo các cột dẫn xuất (derived column) để hiển thị mà không đổi dữ liệu gốc.

## 2. Bài toán mở đầu

Dữ liệu lưu ở dạng "thô" nhưng khi hiển thị ta cần **biến đổi**: viết hoa tên, ghép "tên &lt;email&gt;" thành dòng liên hệ, gắn nhãn "Cao cấp / Trung cấp / Phổ thông" theo giá, tính "đã đăng ký bao nhiêu ngày", thay thành phố trống bằng "Chưa rõ".

Ta có thể làm hết trong C#, nhưng nhiều khi làm ngay trong SQL gọn hơn và giảm dữ liệu trả về. **Hàm scalar** biến đổi từng giá trị, **`CASE`** ánh xạ điều kiện thành nhãn, và các hàm NULL biến giá trị thiếu thành thứ hiển thị được. Bài này biến truy vấn từ "lấy dữ liệu thô" thành "lấy dữ liệu đã sẵn sàng hiển thị".

## 3. Lời giải bằng code

### 3.1 `CASE` — phân loại theo điều kiện

```sql
SELECT Ten, Gia,
    CASE
        WHEN Gia >= 1000000 THEN N'Cao cấp'
        WHEN Gia >= 400000  THEN N'Trung cấp'
        ELSE N'Phổ thông'
    END AS BacGia
FROM SanPham
ORDER BY Gia DESC;
```
```text
Ten                   | Gia        | BacGia
----------------------+------------+---------
Tai nghe              | 1200000.00 | Cao cấp
Nồi cơm điện          | 890000.00  | Trung cấp
Bàn phím cơ           | 750000.00  | Trung cấp
Ấm siêu tốc           | 350000.00  | Phổ thông
Chuột không dây       | 320000.00  | Phổ thông
Lập trình C# nâng cao | 180000.00  | Phổ thông
```

### 3.2 Hàm chuỗi

```sql
SELECT UPPER(HoTen) AS HoTenHoa,
       CONCAT(HoTen, ' <', Email, '>') AS HienThi,
       LEN(HoTen) AS SoKyTu
FROM KhachHang
WHERE KhachHangId <= 2;
```
```text
HoTenHoa  | HienThi                      | SoKyTu
----------+------------------------------+-------
AN NGUYỄN | An Nguyễn <an@example.com>    | 9
BÌNH TRẦN | Bình Trần <binh@example.com>  | 9
```

### 3.3 Hàm ngày

```sql
-- Dùng một ngày cố định '2026-08-22' cho kết quả tái lập; thực tế dùng GETDATE()
SELECT HoTen,
       YEAR(NgayDangKy)  AS Nam,
       MONTH(NgayDangKy) AS Thang,
       DATEDIFF(DAY, NgayDangKy, '2026-08-22') AS SoNgay
FROM KhachHang
ORDER BY KhachHangId;
```
```text
HoTen     | Nam  | Thang | SoNgay
----------+------+-------+-------
An Nguyễn | 2026 | 1     | 219
Bình Trần | 2026 | 2     | 183
Cường Lê  | 2026 | 3     | 170
Dung Phạm | 2026 | 3     | 157
```

### 3.4 Xử lý NULL với `NULLIF` + `COALESCE`

```sql
-- NULLIF(a, '') biến chuỗi rỗng thành NULL; COALESCE thay NULL bằng nhãn
SELECT HoTen, COALESCE(NULLIF(Thanh, ''), N'Chưa rõ') AS ThanhPho
FROM KhachHang
ORDER BY KhachHangId;
```
```text
HoTen     | ThanhPho
----------+---------
An Nguyễn | Hà Nội
Bình Trần | Đà Nẵng
Cường Lê  | Hà Nội
Dung Phạm | Chưa rõ
```

## 4. Giải thích cơ chế

### 4.1 Hàm scalar chạy trên từng hàng

Hàm **scalar** nhận đầu vào và trả **một giá trị**, áp **độc lập cho mỗi hàng**. `UPPER(HoTen)` biến tên của từng khách thành chữ hoa; `DATEDIFF(...)` tính số ngày riêng cho từng hàng. Kết quả có đúng số hàng như đầu vào — hàm scalar không gộp hàng lại. Đây là khác biệt cốt lõi với **hàm tổng hợp** (`COUNT`, `SUM`, `AVG` — bài [07](./07-group-by-aggregate-va-having.md)) vốn gộp nhiều hàng thành một giá trị.

### 4.2 `CASE` — rẽ nhánh trong biểu thức

`CASE` là "if/else" của SQL, nhưng là **biểu thức** (trả về giá trị) chứ không phải câu lệnh. Dạng **searched** (dùng trong bài) xét lần lượt các `WHEN điều_kiện THEN giá_trị`, lấy nhánh **đầu tiên** đúng; `ELSE` cho phần còn lại. Thứ tự quan trọng: vì xét từ trên xuống và dừng ở nhánh đúng đầu tiên, phải đặt điều kiện **hẹp/cao** trước. Nếu đảo hai `WHEN` (đặt `>= 400000` trước `>= 1000000`), mọi giá trên 1 triệu cũng rơi vào "Trung cấp" — sai.

Còn dạng **simple**: `CASE TrangThai WHEN N'Moi' THEN ... WHEN N'Huy' THEN ... END` — so `TrangThai` với từng giá trị. Dùng dạng simple khi so **bằng** một cột với các hằng; dạng searched khi cần điều kiện phức tạp (khoảng, `AND`/`OR`).

### 4.3 `NULLIF` và `COALESCE` phối hợp

- `NULLIF(a, b)` trả `NULL` nếu `a = b`, ngược lại trả `a`. `NULLIF(Thanh, '')` biến **chuỗi rỗng** thành NULL.
- `COALESCE(x, y)` trả `x` nếu khác NULL, ngược lại `y`.

Ghép lại `COALESCE(NULLIF(Thanh, ''), N'Chưa rõ')` xử lý **cả hai** loại "trống": NULL thật (Dung Phạm) **và** chuỗi rỗng (nếu có) đều thành "Chưa rõ". Đây là mẫu làm sạch dữ liệu hiển thị rất thường dùng (nối tiếp bài [03](./03-kieu-du-lieu-va-null.md) về NULL).

### 4.4 Cột dẫn xuất không đổi dữ liệu gốc

Mọi biểu thức trong `SELECT` tạo ra **cột dẫn xuất** chỉ tồn tại trong kết quả truy vấn — dữ liệu trong bảng **không đổi**. `UPPER(HoTen)` không viết hoa tên trong bảng, chỉ hiển thị hoa. Đây là điểm mạnh: một dữ liệu gốc, nhiều cách trình bày, tùy truy vấn. Đặt alias (`AS BacGia`) để đặt tên cột kết quả.

### Đào sâu (có thể quay lại sau)

- **Khác biệt phương ngữ hàm.** Đây là nơi SQL Server và PostgreSQL lệch nhau nhiều nhất:

  | Mục đích | SQL Server | PostgreSQL |
  |---|---|---|
  | Độ dài chuỗi | `LEN(s)` | `LENGTH(s)` / `CHAR_LENGTH(s)` |
  | Trích năm | `YEAR(d)` | `EXTRACT(YEAR FROM d)` |
  | Chênh lệch ngày | `DATEDIFF(DAY, a, b)` | `b - a` (kiểu date) |
  | Thời điểm hiện tại | `GETDATE()` / `SYSUTCDATETIME()` | `NOW()` / `CURRENT_TIMESTAMP` |
  | Nối chuỗi | `a + b` hoặc `CONCAT(a,b)` | `a || b` hoặc `CONCAT(a,b)` |
  | Thay NULL (2 tham số) | `ISNULL(a,b)` | (không có; dùng `COALESCE`) |

  `CONCAT`, `COALESCE`, `NULLIF`, `CASE`, `UPPER`, `LOWER`, `ROUND`, `ABS`, `SUBSTRING` là **chuẩn**, chạy giống nhau. Ưu tiên chúng khi muốn code di động.
- **`LEN` bỏ khoảng trắng cuối.** `LEN` của SQL Server bỏ khoảng trắng ở cuối (`LEN('abc  ') = 3`), còn `DATALENGTH`/`LENGTH` thì không — một khác biệt tinh vi.
- **`CONCAT` xử lý NULL êm.** Khác `+`/`||`, hàm `CONCAT` coi NULL như chuỗi rỗng thay vì lan truyền NULL — nên `CONCAT(HoTen, NULL)` vẫn ra tên, không ra NULL.
- **`FORMAT` và định dạng.** SQL Server có `FORMAT(Gia, 'N0')` cho định dạng số/tiền/ngày kiểu văn hóa, nhưng chậm; thường nên định dạng ở tầng ứng dụng (C#/frontend) thay vì trong SQL.

## 5. Kiến thức nền

### Scalar so với aggregate

| | Hàm scalar | Hàm tổng hợp |
|---|---|---|
| Đầu vào | một hàng | nhiều hàng (nhóm) |
| Đầu ra | một giá trị mỗi hàng | một giá trị mỗi nhóm |
| Ví dụ | `UPPER`, `ROUND`, `YEAR` | `COUNT`, `SUM`, `AVG` |
| Số hàng kết quả | như đầu vào | ít hơn (theo nhóm) |

Bài [07](./07-group-by-aggregate-va-having.md) chuyển sang aggregate. Hai loại hàm này thường phối hợp: `AVG(...)` (aggregate) rồi bọc `ROUND(...)` (scalar) để làm tròn kết quả trung bình.

### `CASE` ở nhiều vị trí

`CASE` là biểu thức nên dùng được ở bất cứ đâu chấp nhận giá trị: trong `SELECT` (cột dẫn xuất), `WHERE` (điều kiện có nhánh), `ORDER BY` (thứ tự tùy biến — ví dụ sắp `TrangThai` theo ưu tiên nghiệp vụ chứ không theo bảng chữ cái), và cả trong hàm tổng hợp (`SUM(CASE WHEN ... THEN 1 ELSE 0 END)` để đếm có điều kiện).

### Nên biến đổi ở đâu?

Nguyên tắc: biến đổi **để lọc/nhóm/sắp** nên làm trong SQL (gần dữ liệu, tận dụng index nếu được); còn **định dạng thuần hiển thị** (dấu phẩy nghìn, ký hiệu tiền tệ, ngày theo locale) thường nên làm ở tầng ứng dụng để tách quan tâm và tái dùng.

## 6. Lỗi thường gặp

### Sai thứ tự nhánh `CASE`

Đặt điều kiện rộng trước điều kiện hẹp khiến nhánh hẹp không bao giờ chạm tới. Xếp `WHEN` từ **cụ thể/cao nhất** xuống, hoặc dùng khoảng không chồng lấn.

### Quên `ELSE` trong `CASE`

Không có `ELSE`, các hàng không khớp `WHEN` nào nhận **NULL** — dễ gây bất ngờ. Thêm `ELSE` cho trường hợp còn lại (kể cả `ELSE NULL` tường minh nếu cố ý).

### Dùng hàm phương ngữ rồi đổi hệ quản trị

`LEN`, `YEAR`, `GETDATE`, `ISNULL` là riêng SQL Server; port sang PostgreSQL sẽ lỗi. Khi cần di động, ưu tiên hàm chuẩn (`CHAR_LENGTH`, `EXTRACT`, `COALESCE`).

### `+` nối chuỗi gặp NULL

Trong SQL Server, `HoTen + ' - ' + Thanh` cho NULL nếu `Thanh` NULL (bài [03](./03-kieu-du-lieu-va-null.md)). Dùng `CONCAT` (bỏ qua NULL) hoặc `COALESCE` từng phần.

### Lồng hàm quá nhiều trong `WHERE`

`WHERE YEAR(NgayDat) = 2026` bọc cột trong hàm nên **không dùng được index** (không sargable). Viết `NgayDat >= '2026-01-01' AND NgayDat < '2027-01-01'` thay thế (bài [22](./22-toi-uu-truy-van-va-sargability.md)).

## 7. Bài tập

### Bài 1 — Nhãn tồn kho

Thêm cột dẫn xuất `TinhTrang` bằng `CASE`: `TonKho = 0` → "Hết hàng", `<= 20` → "Sắp hết", còn lại → "Còn hàng". Áp cho bảng `SanPham`.

**Gợi ý:** xếp `WHEN TonKho = 0` trước `WHEN TonKho <= 20`.

### Bài 2 — Địa chỉ email che

Viết câu hiển thị email dạng che một phần, ví dụ `a***@example.com`, dùng `SUBSTRING` và nối chuỗi.

**Gợi ý:** lấy ký tự đầu bằng `SUBSTRING(Email, 1, 1)`, phần sau `@` bằng `SUBSTRING` từ vị trí `CHARINDEX('@', Email)`.

### Bài 3 — Đếm có điều kiện bằng CASE

Đếm số sản phẩm "Còn hàng" và "Hết hàng" trong một câu, dùng `SUM(CASE WHEN ... THEN 1 ELSE 0 END)`.

**Gợi ý:** hai biểu thức `SUM(CASE ...)` trong cùng `SELECT`, mỗi cái đếm một nhóm.

### Bài 4 — Tuổi tài khoản theo tháng

Tính số **tháng** kể từ ngày đăng ký tới một ngày cố định, cho mỗi khách hàng.

**Gợi ý:** `DATEDIFF(MONTH, NgayDangKy, '2026-08-22')`; suy nghĩ `DATEDIFF` đếm ranh giới tháng, không phải số ngày chia 30.

### Bài 5 — Làm sạch hiển thị

Cho một bảng có cột `GhiChu` vừa có NULL vừa có chuỗi rỗng và cả `'  '` (khoảng trắng), viết câu chuẩn hóa mọi trường hợp trống thành `'(không có)'`.

**Gợi ý:** `COALESCE(NULLIF(TRIM(GhiChu), ''), '(không có)')` — `TRIM` bỏ khoảng trắng trước khi so rỗng.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi dùng được hàm chuỗi, số, ngày cơ bản để biến đổi giá trị.
- [ ] Tôi viết `CASE` searched đúng thứ tự nhánh và có `ELSE`.
- [ ] Tôi kết hợp `NULLIF` + `COALESCE` để làm sạch giá trị trống.
- [ ] Tôi phân biệt hàm scalar (mỗi hàng) với hàm tổng hợp (mỗi nhóm).
- [ ] Tôi biết các khác biệt hàm giữa SQL Server và PostgreSQL và ưu tiên hàm chuẩn khi cần di động.
- [ ] Tôi hiểu cột dẫn xuất không làm đổi dữ liệu gốc.

Điều hướng:

- Bài prerequisite: [Filter, sort và pagination](./05-filter-sort-va-pagination.md)
- Ôn lại nền tảng: [Kiểu dữ liệu và NULL](./03-kieu-du-lieu-va-null.md)
- Bài tiếp theo: [GROUP BY, aggregate và HAVING](./07-group-by-aggregate-va-having.md)
