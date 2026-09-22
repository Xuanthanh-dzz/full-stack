# Filter, sort và pagination

## 1. Mục tiêu

Sau bài này, bạn có thể:

- lọc hàng bằng `WHERE` với đủ toán tử: so sánh, `BETWEEN`, `IN`, `LIKE`, `AND`/`OR`/`NOT`;
- tìm theo mẫu chuỗi với `LIKE` và ký tự đại diện `%`, `_`;
- sắp xếp kết quả bằng `ORDER BY` theo một hoặc nhiều cột, tăng/giảm dần;
- phân trang kết quả bằng `OFFSET ... FETCH` (chuẩn SQL, có trong SQL Server);
- hiểu vì sao pagination **bắt buộc** đi kèm `ORDER BY` xác định;
- kết hợp lọc, sắp, phân trang thành một truy vấn danh sách hoàn chỉnh.

## 2. Bài toán mở đầu

Trang danh sách sản phẩm của cửa hàng cần đúng ba việc: **lọc** (chỉ hiện danh mục Điện tử, giá trong khoảng nào đó), **sắp xếp** (giá giảm dần, hoặc mới nhất trước), và **phân trang** (hiển thị 20 sản phẩm mỗi trang, bấm sang trang 2). Nếu lấy hết hàng nghìn sản phẩm rồi lọc/sắp/cắt trong code C#, ta kéo về quá nhiều dữ liệu và chậm.

SQL làm cả ba việc này ngay tại database, chỉ trả về đúng phần cần. Đây là bộ ba xuất hiện trên gần như mọi màn hình danh sách. Bài này ghép chúng lại, và chỉ ra một cái bẫy tinh vi: phân trang mà không sắp xếp xác định thì thứ tự các trang **không đảm bảo** — trang 2 có thể lặp hàng của trang 1.

## 3. Lời giải bằng code

### 3.1 Lọc với `WHERE`

```sql
-- Giá trong khoảng 300k–900k, thuộc danh mục Điện tử (1) hoặc Gia dụng (3)
SELECT Ten, Gia FROM SanPham
WHERE Gia BETWEEN 300000 AND 900000
  AND DanhMucId IN (1, 3)
ORDER BY Gia;
```
```text
Ten             | Gia
----------------+----------
Chuột không dây | 320000.00
Ấm siêu tốc     | 350000.00
Bàn phím cơ     | 750000.00
Nồi cơm điện    | 890000.00
```

### 3.2 Tìm theo mẫu với `LIKE`

```sql
-- Tên chứa "điện" hoặc "dây"
SELECT Ten FROM SanPham
WHERE Ten LIKE N'%điện%' OR Ten LIKE N'%dây%'
ORDER BY Ten;
```
```text
Ten
----------------
Chuột không dây
Nồi cơm điện
```

### 3.3 Sắp xếp nhiều cột với `ORDER BY`

```sql
-- Nhóm theo danh mục tăng dần, trong mỗi danh mục sắp giá giảm dần
SELECT Ten, DanhMucId, Gia FROM SanPham
ORDER BY DanhMucId ASC, Gia DESC;
```
```text
Ten                   | DanhMucId | Gia
----------------------+-----------+-----------
Tai nghe              | 1         | 1200000.00
Bàn phím cơ           | 1         | 750000.00
Chuột không dây       | 1         | 320000.00
Lập trình C# nâng cao | 2         | 180000.00
Nồi cơm điện          | 3         | 890000.00
Ấm siêu tốc           | 3         | 350000.00
```

### 3.4 Phân trang với `OFFSET ... FETCH`

```sql
-- Trang 2, mỗi trang 2 sản phẩm, sắp theo giá giảm dần
-- (bỏ qua 2 hàng đầu, lấy 2 hàng tiếp theo)
SELECT SanPhamId, Ten, Gia FROM SanPham
ORDER BY Gia DESC
OFFSET 2 ROWS FETCH NEXT 2 ROWS ONLY;
```
```text
SanPhamId | Ten         | Gia
----------+-------------+----------
1         | Bàn phím cơ | 750000.00
6         | Ấm siêu tốc | 350000.00
```

Toàn bộ sắp theo giá giảm dần là: Tai nghe, Nồi cơm điện, **Bàn phím cơ, Ấm siêu tốc**, Chuột, Lập trình C#. `OFFSET 2` bỏ hai đầu (Tai nghe, Nồi cơm điện), `FETCH NEXT 2` lấy đúng hai hàng của trang 2.

## 4. Giải thích cơ chế

### 4.1 Các toán tử của `WHERE`

| Toán tử | Ý nghĩa | Ví dụ |
|---|---|---|
| `=` `<>` `<` `>` `<=` `>=` | so sánh | `Gia > 500000` |
| `BETWEEN a AND b` | trong khoảng (bao gồm hai đầu) | `Gia BETWEEN 300000 AND 900000` |
| `IN (...)` | thuộc một tập | `DanhMucId IN (1, 3)` |
| `LIKE 'mẫu'` | khớp mẫu chuỗi | `Ten LIKE N'%điện%'` |
| `IS NULL` / `IS NOT NULL` | kiểm tra NULL | `Thanh IS NULL` |
| `AND` `OR` `NOT` | kết hợp điều kiện | `A AND (B OR C)` |

`BETWEEN 300000 AND 900000` tương đương `Gia >= 300000 AND Gia <= 900000` — **bao gồm** cả hai biên. `IN (1, 3)` gọn hơn `DanhMucId = 1 OR DanhMucId = 3`. Khi trộn `AND` và `OR`, dùng ngoặc để tránh nhầm thứ tự ưu tiên (`AND` được tính trước `OR`).

### 4.2 `LIKE` và ký tự đại diện

- `%` khớp **không hoặc nhiều** ký tự bất kỳ: `N'%điện%'` khớp mọi chuỗi **chứa** "điện".
- `_` khớp **đúng một** ký tự: `'A_C'` khớp "ABC", "AXC".

`'%điện'` khớp chuỗi **kết thúc** bằng "điện"; `'điện%'` khớp chuỗi **bắt đầu** bằng "điện". Lưu ý: `LIKE` với `%` ở **đầu** mẫu (`'%điện%'`) không dùng được index thông thường nên chậm trên bảng lớn — bài [22](./22-toi-uu-truy-van-va-sargability.md) bàn về "sargability".

### 4.3 `ORDER BY` và thứ tự nhiều cột

`ORDER BY DanhMucId ASC, Gia DESC` sắp **theo tầng**: trước hết gom theo `DanhMucId` tăng dần; trong các hàng cùng danh mục, sắp `Gia` giảm dần. Cột thứ hai chỉ quyết định thứ tự khi cột thứ nhất **bằng nhau**. `ASC` (tăng, mặc định) hay `DESC` (giảm) áp riêng cho từng cột.

### 4.4 Pagination cần `ORDER BY` xác định

`OFFSET n ROWS FETCH NEXT m ROWS ONLY` bỏ qua `n` hàng đầu rồi lấy `m` hàng — chính là "trang thứ `k`" với `n = (k-1) * m`. Nhưng có một điều kiện sống còn: **thứ tự phải xác định**. Nếu không có `ORDER BY` (hoặc sắp theo cột có giá trị trùng), database **không đảm bảo** thứ tự hàng giữa các lần chạy — trang 2 có thể chứa hàng đã hiện ở trang 1, hoặc bỏ sót hàng. Luôn `ORDER BY` theo một tổ hợp cột **duy nhất** (thường thêm khóa chính vào cuối để phá thế hòa): `ORDER BY Gia DESC, SanPhamId`.

### Đào sâu (có thể quay lại sau)

- **`TOP` của SQL Server.** SQL Server còn có `SELECT TOP 5 ... ORDER BY ...` để lấy `n` hàng đầu — tiện cho "5 sản phẩm đắt nhất". `OFFSET/FETCH` tổng quát hơn (phân trang bất kỳ) và là chuẩn SQL. PostgreSQL/MySQL dùng `LIMIT`/`OFFSET` cho cùng mục đích.
- **Collation và `LIKE`.** Kết quả `LIKE` và `ORDER BY` trên chuỗi phụ thuộc **collation** (quy tắc so sánh/sắp chữ). SQL Server mặc định thường **không phân biệt hoa/thường** (case-insensitive); một số hệ khác phân biệt. Với tiếng Việt, collation còn quyết định thứ tự dấu. Khi cần chắc chắn, chỉ định collation rõ ràng.
- **Keyset pagination.** Với dữ liệu rất lớn, `OFFSET` lớn vẫn phải quét bỏ `n` hàng đầu nên chậm dần ở các trang sau. Kỹ thuật "keyset/seek pagination" (`WHERE Gia < giá_hàng_cuối_trang_trước`) nhanh hơn nhiều — sẽ gặp lại khi tối ưu (bài [22](./22-toi-uu-truy-van-va-sargability.md)).
- **`ESCAPE` trong `LIKE`.** Muốn tìm ký tự `%` hay `_` theo nghĩa đen, dùng `LIKE '%30\%%' ESCAPE '\'`.

## 5. Kiến thức nền

### Lọc/sắp ở database, không ở ứng dụng

Nguyên tắc quan trọng: đẩy lọc, sắp, phân trang **xuống database**, đừng kéo hết về rồi xử lý trong C#. Database có index và bộ tối ưu để làm việc này hiệu quả (module sau), và trả ít dữ liệu qua mạng hơn. `list.Where(...).OrderBy(...).Skip(...).Take(...)` trong LINQ ([module 09](../09-linq-va-ef-core/02-where-select-va-selectmany.md)) sẽ **dịch** thành đúng `WHERE`/`ORDER BY`/`OFFSET FETCH` này khi chạy trên `IQueryable`.

### Ánh xạ sang trang web

Một request `GET /products?category=1&minPrice=300000&sort=price_desc&page=2` ánh xạ trực tiếp: `category` → `WHERE DanhMucId`, `minPrice` → `WHERE Gia >=`, `sort` → `ORDER BY`, `page` → `OFFSET`. Bài [10](../10-web-nen-tang/07-pagination-filtering-versioning-va-idempotency.md) sẽ thiết kế API phân trang chuẩn.

### Thứ tự logic nhắc lại

Nhớ từ bài [04](./04-crud-select-insert-update-delete.md): `FROM → WHERE → SELECT → ORDER BY → OFFSET/FETCH`. Vì `ORDER BY` chạy **sau** `SELECT`, nó **được** dùng alias cột đặt ở `SELECT` (khác `WHERE`).

## 6. Lỗi thường gặp

### Pagination không có `ORDER BY`

`OFFSET/FETCH` mà không `ORDER BY` (hoặc sắp theo cột trùng nhiều) cho thứ tự không xác định — trang lặp/sót hàng. Luôn sắp theo tổ hợp cột duy nhất.

### Nhầm thứ tự ưu tiên `AND`/`OR`

`WHERE A OR B AND C` được hiểu là `A OR (B AND C)`, không phải `(A OR B) AND C`. Dùng ngoặc khi trộn để nói rõ ý.

### `LIKE '%...%'` trên bảng lớn

Mẫu bắt đầu bằng `%` không dùng được index nên quét toàn bảng. Trên bảng lớn cần tìm text, cân nhắc full-text search (bài [18 module 18](../18-thiet-ke-he-thong/16-search-full-text-va-indexing.md)) thay vì `LIKE '%...%'`.

### `BETWEEN` với ngày và giờ

`NgayDat BETWEEN '2026-03-01' AND '2026-03-31'` có thể **bỏ sót** các bản ghi ngày 31 có phần giờ (vì `'2026-03-31'` = `00:00`). Với cột có giờ, dùng `>= '2026-03-01' AND < '2026-04-01'`.

### Kéo hết dữ liệu rồi lọc trong code

`SELECT * FROM SanPham` rồi `.Where()` trong C# lãng phí băng thông và bỏ qua index. Đẩy điều kiện vào `WHERE` của SQL.

## 7. Bài tập

### Bài 1 — Lọc kết hợp

Viết câu lấy sản phẩm thuộc danh mục Gia dụng (3) **có** tồn kho > 0, sắp theo giá tăng dần.

**Gợi ý:** `WHERE DanhMucId = 3 AND TonKho > 0 ORDER BY Gia`.

### Bài 2 — Tìm theo tiền tố

Tìm mọi khách hàng có email kết thúc bằng `@example.com`. Viết mẫu `LIKE` phù hợp.

**Gợi ý:** `Email LIKE '%@example.com'`.

### Bài 3 — Phân trang đầy đủ

Viết truy vấn lấy "trang 1, mỗi trang 3 sản phẩm, sắp giá giảm dần", rồi trang 2, và giải thích `OFFSET` của mỗi trang.

**Gợi ý:** trang `k` có `OFFSET (k-1)*3 ROWS FETCH NEXT 3 ROWS ONLY`; thêm `SanPhamId` vào `ORDER BY` để chắc chắn.

### Bài 4 — Top N

Viết câu lấy 3 sản phẩm đắt nhất bằng hai cách: `OFFSET/FETCH` và (nếu dùng SQL Server) `TOP`.

**Gợi ý:** `ORDER BY Gia DESC OFFSET 0 ROWS FETCH NEXT 3 ROWS ONLY`, hoặc `SELECT TOP 3 ... ORDER BY Gia DESC`.

### Bài 5 — Bẫy ngày tháng

Cho bảng `DonHang` với cột ngày–giờ, viết câu lấy đơn "trong tháng 3/2026" đúng cách (không bỏ sót ngày cuối tháng có giờ).

**Gợi ý:** `NgayDat >= '2026-03-01' AND NgayDat < '2026-04-01'` thay vì `BETWEEN`.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi lọc được bằng `WHERE` với `BETWEEN`, `IN`, `LIKE`, `AND`/`OR`/`NOT`.
- [ ] Tôi dùng `%` và `_` trong `LIKE` đúng ý.
- [ ] Tôi sắp xếp nhiều cột với `ORDER BY` tăng/giảm dần.
- [ ] Tôi phân trang bằng `OFFSET ... FETCH` và luôn kèm `ORDER BY` xác định.
- [ ] Tôi giải thích được vì sao pagination cần thứ tự duy nhất.
- [ ] Tôi biết đẩy lọc/sắp/phân trang xuống database thay vì xử lý trong code.

Điều hướng:

- Bài prerequisite: [CRUD: SELECT, INSERT, UPDATE, DELETE](./04-crud-select-insert-update-delete.md)
- Ôn lại nền tảng: [Kiểu dữ liệu và NULL](./03-kieu-du-lieu-va-null.md)
- Bài tiếp theo: [Hàm scalar, CASE và xử lý NULL](./06-ham-scalar-case-va-xu-ly-null.md)
