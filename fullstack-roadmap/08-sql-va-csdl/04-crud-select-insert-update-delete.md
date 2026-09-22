# CRUD: SELECT, INSERT, UPDATE, DELETE

## 1. Mục tiêu

Sau bài này, bạn có thể:

- thực hiện bốn thao tác dữ liệu cốt lõi: `SELECT`, `INSERT`, `UPDATE`, `DELETE`;
- chèn một hàng và nhiều hàng trong một câu lệnh;
- cập nhật và xóa **có điều kiện** bằng `WHERE`, hiểu hậu quả khi thiếu `WHERE`;
- dùng biểu thức trong `UPDATE` (ví dụ giảm giá 10%);
- xem trước hàng bị ảnh hưởng bằng `SELECT` trước khi `UPDATE`/`DELETE`;
- biết mệnh đề `OUTPUT` của SQL Server để lấy lại dữ liệu vừa thay đổi.

## 2. Bài toán mở đầu

Quản lý danh mục sản phẩm của cửa hàng là việc hằng ngày: **thêm** sản phẩm mới, **xem** danh sách, **đổi** giá khi khuyến mãi, **gỡ** sản phẩm ngừng bán. Bốn hành động này — Create, Read, Update, Delete — gọi tắt là **CRUD**, và chúng là xương sống của gần như mọi ứng dụng.

SQL diễn tả cả bốn bằng bốn câu lệnh gọn. Nhưng có một cái bẫy chết người: `UPDATE` và `DELETE` **không có `WHERE`** sẽ áp lên **toàn bộ bảng** — một lệnh lỡ tay có thể đổi giá mọi sản phẩm hoặc xóa sạch khách hàng. Bài này dạy CRUD an toàn: luôn biết mình đang chạm vào những hàng nào.

## 3. Lời giải bằng code

Chạy trên database `Shop` (đã có 6 sản phẩm từ bài 02).

### 3.1 INSERT — thêm hàng

```sql
-- Chèn nhiều hàng trong một câu lệnh
INSERT INTO SanPham (Ten, DanhMucId, Gia, TonKho) VALUES
    (N'Sạc dự phòng',  1, 450000, 50),
    (N'Giá đỡ laptop', 1, 210000, 35);

-- Xem lại các sản phẩm thuộc danh mục Điện tử (DanhMucId = 1)
SELECT SanPhamId, Ten, Gia FROM SanPham WHERE DanhMucId = 1 ORDER BY SanPhamId;
```
```text
SanPhamId | Ten             | Gia
----------+-----------------+-----------
1         | Bàn phím cơ     | 750000.00
2         | Chuột không dây | 320000.00
3         | Tai nghe        | 1200000.00
7         | Sạc dự phòng    | 450000.00
8         | Giá đỡ laptop   | 210000.00
```

`SanPhamId` mới là `7, 8` — `IDENTITY` tiếp tục từ số lớn nhất đã dùng, **không** lấp lại khoảng trống. Ta không cung cấp `SanPhamId` vì engine tự sinh.

### 3.2 UPDATE — sửa hàng (luôn có WHERE)

```sql
-- Giảm giá "Tai nghe" 10% -- biểu thức dùng chính giá trị cũ
UPDATE SanPham SET Gia = Gia * 0.9 WHERE Ten = N'Tai nghe';

SELECT Ten, Gia FROM SanPham WHERE Ten = N'Tai nghe';
```
```text
Ten      | Gia
---------+-----------
Tai nghe | 1080000.00
```

`WHERE Ten = N'Tai nghe'` giới hạn chỉ một hàng. Không có nó, **mọi** sản phẩm bị giảm 10%.

### 3.3 DELETE — xóa hàng (luôn có WHERE)

```sql
-- Gỡ hai sản phẩm vừa thêm
DELETE FROM SanPham WHERE Ten IN (N'Sạc dự phòng', N'Giá đỡ laptop');

SELECT COUNT(*) AS ConLai FROM SanPham;
```
```text
ConLai
------
6
```

### 3.4 SELECT — đọc có điều kiện

```sql
-- Sản phẩm giá trên 500k, sắp giảm dần theo giá
SELECT Ten, Gia, TonKho FROM SanPham WHERE Gia > 500000 ORDER BY Gia DESC;
```
```text
Ten          | Gia        | TonKho
-------------+------------+-------
Tai nghe     | 1080000.00 | 0
Nồi cơm điện | 890000.00  | 15
Bàn phím cơ  | 750000.00  | 25
```

## 4. Giải thích cơ chế

### 4.1 Bốn câu lệnh, một mẫu hình

| Thao tác | Câu lệnh | Nhắm vào |
|---|---|---|
| Create | `INSERT INTO ... VALUES ...` | thêm hàng mới |
| Read | `SELECT ... FROM ... WHERE ...` | đọc hàng hiện có |
| Update | `UPDATE ... SET ... WHERE ...` | sửa hàng khớp điều kiện |
| Delete | `DELETE FROM ... WHERE ...` | xóa hàng khớp điều kiện |

Cả `SELECT`, `UPDATE`, `DELETE` đều dùng `WHERE` để **chọn tập hàng** bị tác động. Nắm `WHERE` là nắm chìa khóa của cả ba (bài [05](./05-filter-sort-va-pagination.md) đào sâu lọc).

### 4.2 `WHERE` là ranh giới an toàn

`UPDATE`/`DELETE` tác động lên **mọi hàng thỏa `WHERE`**. Đây vừa là sức mạnh (sửa 1000 hàng bằng một câu) vừa là hiểm họa (sửa nhầm 1000 hàng). Thói quen an toàn: **chạy `SELECT` với cùng `WHERE` trước**, xem đúng những hàng định sửa, rồi mới đổi thành `UPDATE`/`DELETE`:

```sql
-- Bước 1: xem sẽ đụng vào hàng nào
SELECT * FROM SanPham WHERE Ten = N'Tai nghe';
-- Bước 2: yên tâm rồi mới sửa
UPDATE SanPham SET Gia = Gia * 0.9 WHERE Ten = N'Tai nghe';
```

### 4.3 Biểu thức trong `UPDATE`

`SET Gia = Gia * 0.9` cho thấy vế phải có thể là **biểu thức tính từ giá trị hiện tại** của chính hàng đó. SQL tính riêng cho từng hàng: mỗi sản phẩm lấy giá cũ của nó nhân `0.9`. Có thể cập nhật nhiều cột cùng lúc: `SET Gia = ..., TonKho = TonKho - 1`.

### 4.4 `INSERT` và cột tự sinh

Khi chèn, ta **bỏ qua** cột `IDENTITY` (`SanPhamId`) và cột có `DEFAULT` nếu muốn dùng mặc định. Danh sách cột sau tên bảng cho biết ta cung cấp cột nào; các cột còn lại nhận giá trị tự sinh hoặc mặc định. Nên **luôn liệt kê cột rõ ràng** thay vì `INSERT INTO SanPham VALUES (...)` — nếu cấu trúc bảng đổi, câu liệt kê cột vẫn đúng còn câu không liệt kê sẽ vỡ.

### Đào sâu (có thể quay lại sau)

- **`OUTPUT` (SQL Server).** Có thể lấy lại dữ liệu vừa thay đổi ngay trong câu lệnh: `INSERT ... OUTPUT inserted.SanPhamId, inserted.Ten VALUES (...)` trả về id vừa sinh; `DELETE ... OUTPUT deleted.*` trả các hàng vừa xóa. PostgreSQL dùng `RETURNING` cho cùng mục đích. Hữu ích để biết khóa vừa tạo mà không cần truy vấn lại.
- **`TRUNCATE` khác `DELETE`.** `TRUNCATE TABLE` xóa **mọi** hàng cực nhanh (không ghi log từng hàng, reset `IDENTITY`) nhưng không có `WHERE` và không kích hoạt trigger như `DELETE`. Dùng cẩn thận, chỉ khi thực sự muốn dọn sạch bảng.
- **Nguyên tử theo câu lệnh.** Mỗi câu `INSERT`/`UPDATE`/`DELETE` là **nguyên tử**: hoặc mọi hàng bị ảnh hưởng thành công, hoặc không hàng nào đổi (nếu có lỗi). Nhiều câu lệnh cần đi cùng nhau thì gói trong **transaction** (bài [19](./19-transaction-va-acid.md)).
- **`INSERT ... SELECT`.** Có thể chèn kết quả một truy vấn: `INSERT INTO BangSaoLuu SELECT * FROM SanPham WHERE ...` — chép hàng loạt giữa các bảng.

## 5. Kiến thức nền

### CRUD là nền của mọi ứng dụng

Gần như mọi màn hình phần mềm là một biến thể CRUD: danh sách (Read), nút "Thêm" (Create), form "Sửa" (Update), nút "Xóa" (Delete). Web API ở [module 11](../11-aspnet-core-backend/08-controller-api.md) ánh xạ CRUD sang HTTP: `POST` (create), `GET` (read), `PUT`/`PATCH` (update), `DELETE`. Hiểu CRUD trên SQL là hiểu tầng dữ liệu của toàn bộ chuỗi đó.

### Thứ tự logic của `SELECT`

Dù viết `SELECT` trước, engine xử lý theo thứ tự: `FROM` (lấy bảng) → `WHERE` (lọc hàng) → `SELECT` (chọn cột) → `ORDER BY` (sắp xếp). Hiểu thứ tự này giải thích vì sao không thể dùng alias cột (đặt ở `SELECT`) trong `WHERE` — lúc `WHERE` chạy, alias chưa tồn tại. Bài [05](./05-filter-sort-va-pagination.md) và [07](./07-group-by-aggregate-va-having.md) khai thác kỹ.

### An toàn khi thao tác dữ liệu thật

- Luôn `SELECT` kiểm tra `WHERE` trước `UPDATE`/`DELETE`.
- Trên dữ liệu quan trọng, gói trong transaction để có thể `ROLLBACK`.
- Sao lưu trước các thao tác hàng loạt (bài [24](./24-backup-restore-va-migration-du-lieu.md)).
- Không chạy lệnh sửa/xóa trực tiếp trên production khi chưa thử ở môi trường an toàn.

## 6. Lỗi thường gặp

### `UPDATE`/`DELETE` không có `WHERE`

Bẫy nguy hiểm nhất: `DELETE FROM KhachHang;` xóa **mọi** khách hàng; `UPDATE SanPham SET Gia = 0;` đặt giá mọi sản phẩm về 0. Luôn có `WHERE` (trừ khi thực sự muốn tác động toàn bảng, và đã chắc chắn).

### `INSERT` không liệt kê cột

`INSERT INTO SanPham VALUES (...)` phụ thuộc thứ tự cột; thêm/đổi cột là câu lệnh vỡ âm thầm hoặc gán nhầm cột. Luôn liệt kê cột.

### Cung cấp giá trị cho cột `IDENTITY`

Gán tay `SanPhamId` khi cột là `IDENTITY` gây lỗi (trừ khi bật `IDENTITY_INSERT`). Để engine tự sinh khóa.

### Quên rằng `UPDATE` chạy trên từng hàng

`SET Gia = Gia * 0.9` áp riêng cho từng hàng thỏa `WHERE`. Nếu `WHERE` khớp nhiều hàng, mọi hàng đó đều đổi — kiểm tra phạm vi `WHERE` trước.

### Dùng `TRUNCATE` khi cần `DELETE` có điều kiện

`TRUNCATE` xóa sạch bảng, không có `WHERE`. Cần xóa chọn lọc thì dùng `DELETE ... WHERE`.

## 7. Bài tập

### Bài 1 — Thêm và xem

Thêm hai khách hàng mới vào `KhachHang` bằng một câu `INSERT`, rồi `SELECT` lại toàn bộ khách hàng sắp theo `NgayDangKy`.

**Gợi ý:** liệt kê cột; bỏ qua `KhachHangId` để engine tự sinh.

### Bài 2 — Cập nhật an toàn

Tăng tồn kho của "Tai nghe" (đang 0) lên 20. Viết `SELECT` kiểm tra `WHERE` trước, rồi `UPDATE`, rồi `SELECT` xác nhận.

**Gợi ý:** ba bước SELECT–UPDATE–SELECT là thói quen an toàn.

### Bài 3 — Xóa có điều kiện

Xóa mọi sản phẩm có `TonKho = 0` **và** thuộc danh mục Điện tử. Dự đoán số hàng bị xóa trước khi chạy.

**Gợi ý:** `WHERE TonKho = 0 AND DanhMucId = 1`; chạy `SELECT` cùng điều kiện để đếm trước.

### Bài 4 — Cập nhật nhiều cột

Đặt "Nồi cơm điện" thành giá `990000` **và** tồn kho `20` trong một câu `UPDATE`.

**Gợi ý:** `SET Gia = 990000, TonKho = 20 WHERE ...`.

### Bài 5 — Mô phỏng thảm họa (an toàn)

Trên một bảng nháp (copy vài hàng), chạy `UPDATE` **không** `WHERE`, quan sát mọi hàng đổi, rồi viết lại đúng có `WHERE`. Rút ra bài học.

**Gợi ý:** làm trên bảng tạm, không trên dữ liệu thật; bọc trong transaction để `ROLLBACK` được (bài 19).

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi viết được `INSERT` một hàng và nhiều hàng, có liệt kê cột.
- [ ] Tôi `UPDATE`/`DELETE` luôn kèm `WHERE` và biết hậu quả khi thiếu.
- [ ] Tôi dùng được biểu thức trong `SET` (tính từ giá trị cũ).
- [ ] Tôi kiểm tra `WHERE` bằng `SELECT` trước khi sửa/xóa.
- [ ] Tôi hiểu `IDENTITY` tự sinh khóa và không cung cấp nó khi `INSERT`.
- [ ] Tôi biết `OUTPUT`/`RETURNING` để lấy lại dữ liệu vừa thay đổi.

Điều hướng:

- Bài prerequisite: [Kiểu dữ liệu và NULL](./03-kieu-du-lieu-va-null.md)
- Ôn lại nền tảng: [Thiết kế schema, table, key và constraint](./02-thiet-ke-schema-table-key-constraint.md)
- Bài tiếp theo: [Filter, sort và pagination](./05-filter-sort-va-pagination.md)
