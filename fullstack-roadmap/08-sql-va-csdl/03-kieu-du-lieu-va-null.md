# Kiểu dữ liệu và NULL

## 1. Mục tiêu

Sau bài này, bạn có thể:

- chọn đúng **kiểu dữ liệu** SQL Server cho từng loại thông tin (số, tiền, chuỗi, ngày, luận lý);
- giải thích vì sao dùng `DECIMAL` cho tiền chứ không `FLOAT`, và `NVARCHAR` cho tiếng Việt;
- hiểu **NULL** nghĩa là "không biết/thiếu", khác `0` và chuỗi rỗng;
- áp dụng **logic ba giá trị** (true / false / unknown) khi so sánh với NULL;
- dùng `IS NULL`, `IS NOT NULL`, `COALESCE`, `ISNULL` để xử lý NULL đúng cách;
- lường trước cách NULL lan truyền trong số học và bị bỏ qua trong hàm tổng hợp.

## 2. Bài toán mở đầu

Bảng `KhachHang` có cột `Thanh` (thành phố) mà khách "Dung Phạm" **chưa cung cấp**. Ta lưu gì vào đó? Chuỗi rỗng `''`? Số `0`? Chữ `"không có"`? Mỗi cách đều gây rắc rối: chuỗi rỗng trông như một thành phố tên rỗng; `"không có"` lẫn vào dữ liệu thật.

SQL có một giá trị đặc biệt cho đúng tình huống này: **NULL** — nghĩa là **"không biết"** hoặc **"thiếu"**. Nhưng NULL cư xử khác mọi giá trị thường tới mức gây bất ngờ: `WHERE Thanh = NULL` **không** tìm ra Dung Phạm, dù cột đó đúng là NULL. Hiểu sai NULL là một trong những nguồn bug SQL phổ biến nhất. Bài này làm rõ NULL, và song song đó chọn đúng kiểu dữ liệu — nền tảng cho mọi bảng sau này.

## 3. Lời giải bằng code

### 3.1 Chọn kiểu dữ liệu

Các kiểu thường dùng của SQL Server:

```sql
CREATE TABLE ViDuKieu (
    SoNguyen     INT,            -- số nguyên 32-bit (-2 tỉ .. 2 tỉ)
    SoLon        BIGINT,         -- số nguyên 64-bit
    Tien         DECIMAL(12,2),  -- số thập phân CHÍNH XÁC: 12 chữ số, 2 sau dấu phẩy
    TiLe         FLOAT,          -- dấu phẩy động (gần đúng) — KHÔNG dùng cho tiền
    TenNgan      NVARCHAR(100),  -- chuỗi Unicode độ dài thay đổi
    MaCoDinh     CHAR(3),        -- chuỗi độ dài cố định (ví dụ mã tiền 'VND')
    Ngay         DATE,           -- chỉ ngày
    ThoiDiem     DATETIME2,      -- ngày + giờ, độ chính xác cao
    DungSai      BIT             -- luận lý: 1 / 0 / NULL
);
```

### 3.2 NULL và logic ba giá trị

Dữ liệu mẫu: "Dung Phạm" có `Thanh` là NULL, ba người kia có thành phố.

```sql
-- SAI: so sánh = với NULL không bao giờ đúng -> không ra hàng nào
SELECT HoTen, Thanh FROM KhachHang WHERE Thanh = NULL;
```
```text
HoTen | Thanh
------+------
(không có hàng)
```

```sql
-- ĐÚNG: dùng IS NULL để tìm giá trị thiếu
SELECT HoTen, Thanh FROM KhachHang WHERE Thanh IS NULL;
```
```text
HoTen     | Thanh
----------+------
Dung Phạm | NULL
```

NULL lan truyền qua số học, và bị bỏ qua trong hàm đếm:

```sql
SELECT 100 + NULL AS PhepCong,            -- bất kỳ phép tính với NULL -> NULL
       COALESCE(NULL, 0) + 5 AS XuLyNull; -- thay NULL bằng 0 trước khi cộng
```
```text
PhepCong | XuLyNull
---------+---------
NULL     | 5
```

```sql
-- COUNT(*) đếm mọi hàng; COUNT(cot) bỏ qua hàng NULL ở cột đó
SELECT COUNT(*) AS TongHang,
       COUNT(Thanh) AS CoThanh,
       COUNT(*) - COUNT(Thanh) AS ThieuThanh
FROM KhachHang;
```
```text
TongHang | CoThanh | ThieuThanh
---------+---------+-----------
4        | 3       | 1
```

```sql
-- COALESCE: trả giá trị đầu tiên khác NULL -> thay chỗ thiếu bằng nhãn
SELECT HoTen, COALESCE(Thanh, N'Chưa rõ') AS ThanhPho
FROM KhachHang ORDER BY KhachHangId;
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

### 4.1 Vì sao `= NULL` không bao giờ đúng

SQL dùng **logic ba giá trị**: một biểu thức có thể là **TRUE**, **FALSE**, hoặc **UNKNOWN**. Vì NULL nghĩa là "không biết", mọi so sánh với nó cho kết quả **UNKNOWN**:

```text
Thanh = NULL       -> UNKNOWN   (không biết Thanh bằng cái không biết không)
Thanh <> NULL      -> UNKNOWN
NULL = NULL        -> UNKNOWN
```

Mệnh đề `WHERE` chỉ giữ hàng khi điều kiện là **TRUE**. UNKNOWN bị loại y như FALSE. Nên `WHERE Thanh = NULL` loại **mọi** hàng, kể cả hàng NULL. Muốn kiểm tra NULL phải dùng toán tử riêng `IS NULL` / `IS NOT NULL` — chúng trả TRUE/FALSE thật sự, không phải UNKNOWN.

### 4.2 NULL lan truyền trong biểu thức

Bất kỳ phép toán số học hay nối chuỗi nào **có một toán hạng NULL** đều cho NULL: `100 + NULL = NULL`, `N'A' + NULL = NULL`. Logic: nếu một phần chưa biết thì kết quả chưa biết. Đây là lý do phải `COALESCE` (hoặc `ISNULL`) **trước** khi tính, để thay NULL bằng một giá trị trung tính (thường `0` cho số, `''` cho chuỗi).

### 4.3 NULL trong hàm tổng hợp

`COUNT(*)` đếm **hàng**, nên tính cả hàng có NULL. `COUNT(Thanh)` đếm **giá trị khác NULL** của cột `Thanh`, nên bỏ qua Dung Phạm — ra 3. Tương tự, `AVG`, `SUM`, `MIN`, `MAX` đều **bỏ qua** NULL. Điều này quan trọng: `AVG(Gia)` là trung bình của các giá trị có thật, không coi NULL là 0 (nếu coi NULL là 0 sẽ kéo trung bình xuống sai). Bài [07](./07-group-by-aggregate-va-having.md) đào sâu tổng hợp.

### 4.4 `COALESCE` và `ISNULL`

- `COALESCE(a, b, c, ...)` — trả giá trị **đầu tiên khác NULL** trong danh sách. Là chuẩn SQL, chạy trên mọi hệ.
- `ISNULL(a, b)` — riêng SQL Server, trả `b` nếu `a` là NULL. Chỉ nhận **hai** tham số.

Dùng `COALESCE` cho tính di động và khi cần nhiều mức dự phòng. Ví dụ `COALESCE(SoDiDong, SoBan, N'Không có số')` lấy số di động, thiếu thì số bàn, thiếu nữa thì nhãn.

### Đào sâu (có thể quay lại sau)

- **`NULL` khác `0` và `''`.** `0` là một số đã biết (bằng 0); `''` là chuỗi rỗng đã biết (dài 0). `NULL` là **chưa biết**. Đừng trộn lẫn: tồn kho `0` (biết là hết hàng) khác tồn kho NULL (chưa nhập số liệu).
- **`DECIMAL` vs `FLOAT` cho tiền.** `FLOAT` lưu gần đúng theo nhị phân, nên `0.1 + 0.2` có thể ra `0.30000000000000004`. Với tiền, sai số tích lũy là không chấp nhận được — dùng `DECIMAL(p,s)` lưu **chính xác**. `FLOAT` chỉ hợp cho đại lượng khoa học/đo lường chấp nhận xấp xỉ.
- **`UNIQUE` và NULL.** Vì `NULL = NULL` là UNKNOWN, ràng buộc `UNIQUE` coi các NULL là "khác nhau" ở hầu hết hệ — nhưng SQL Server chỉ cho **một** NULL trong cột UNIQUE. Đây là một khác biệt phương ngữ đáng nhớ.
- **`ANSI_NULLS`.** SQL Server có thiết lập cũ `ANSI_NULLS OFF` khiến `= NULL` hoạt động như `IS NULL` — nhưng nó đã lỗi thời và sẽ bị bỏ. Luôn viết `IS NULL`, đừng dựa vào thiết lập này.
- **`NOT IN` với NULL.** `WHERE x NOT IN (1, 2, NULL)` cho kết quả bất ngờ (không ra hàng nào) vì NULL biến điều kiện thành UNKNOWN. Cẩn thận NULL trong danh sách `IN`/`NOT IN`.

## 5. Kiến thức nền

### Bảng chọn kiểu dữ liệu

| Dữ liệu | Kiểu nên dùng | Vì sao |
|---|---|---|
| Khóa tự tăng, số đếm | `INT` / `BIGINT` | số nguyên gọn |
| Tiền, giá | `DECIMAL(p, s)` | chính xác, không sai số nhị phân |
| Đại lượng đo/khoa học | `FLOAT` | chấp nhận gần đúng |
| Tên, mô tả tiếng Việt | `NVARCHAR(n)` | Unicode, độ dài thay đổi |
| Mã cố định (VND, VN) | `CHAR(n)` | độ dài cố định |
| Số điện thoại | `NVARCHAR`/`VARCHAR` | giữ số 0 đầu, không tính toán |
| Ngày | `DATE` | chỉ ngày |
| Ngày + giờ | `DATETIME2` | chính xác cao hơn `DATETIME` cũ |
| Đúng/sai | `BIT` | 1 / 0 / NULL |

### NULL trong tư duy thiết kế

Quyết định một cột **có cho phép NULL hay không** là quyết định thiết kế quan trọng:

- `NOT NULL` khi thông tin **bắt buộc** (tên khách, giá sản phẩm).
- Cho NULL khi thông tin **có thể chưa biết/không áp dụng** (thành phố chưa nhập, ngày giao khi đơn chưa giao).

Đừng dùng "giá trị đặc biệt" như `-1` hay `'N/A'` để né NULL — điều đó trộn dữ liệu thật với cờ trạng thái. NULL là cách chuẩn để nói "không có giá trị".

### So với `Nullable<T>` trong C#

NULL của SQL tương tự nullable reference/value type của C# ([module 05](../05-csharp-nang-cao/06-nullable-reference-type.md)): cùng diễn tả "có thể vắng mặt". Khác biệt: SQL dùng **logic ba giá trị** trong so sánh, còn C# dùng logic hai giá trị (một `null == null` trong C# là `true`). Khi ánh xạ database sang C# (EF Core, module 09), cột cho NULL thường thành kiểu nullable.

## 6. Lỗi thường gặp

### Dùng `=`/`<>` với NULL

`WHERE cot = NULL` hay `cot <> NULL` không bao giờ đúng. Luôn dùng `IS NULL` / `IS NOT NULL`. Đây là lỗi SQL kinh điển nhất về NULL.

### Quên NULL lan truyền

`SELECT Gia * SoLuong` khi một trong hai NULL cho ra NULL — dòng tổng tiền trống. `COALESCE` các cột có thể NULL trước khi tính.

### Coi NULL là 0 trong trung bình

`AVG` bỏ qua NULL (không coi là 0). Nếu bạn muốn NULL tính như 0, phải `AVG(COALESCE(cot, 0))` — nhưng cân nhắc kỹ vì điều đó đổi ý nghĩa thống kê.

### Dùng `FLOAT` cho tiền

Sai số nhị phân của `FLOAT` tích lũy qua nhiều phép cộng, gây lệch tiền. Luôn dùng `DECIMAL` cho giá, số dư, tổng tiền.

### `NOT IN` với danh sách chứa NULL

Nếu một giá trị trong danh sách `IN` là NULL, `NOT IN` có thể loại hết hàng bất ngờ. Lọc NULL khỏi danh sách, hoặc dùng `NOT EXISTS` (bài [09](./09-subquery-va-correlated-subquery.md)).

### Lưu `''` hoặc `'N/A'` thay cho NULL

Chuỗi rỗng hay `'N/A'` là **giá trị đã biết**, làm hỏng thống kê và `COUNT`. Khi dữ liệu thật sự thiếu, dùng NULL.

## 7. Bài tập

### Bài 1 — Chọn kiểu cho bảng nhân viên

Thiết kế bảng `NhanVien` với: mã nhân viên, họ tên, lương, ngày vào làm, đang làm việc hay không, ghi chú (có thể rất dài, có thể thiếu). Chọn kiểu và tính NULL cho mỗi cột.

**Gợi ý:** lương dùng `DECIMAL`; ghi chú dùng `NVARCHAR(MAX)` và cho NULL.

### Bài 2 — Tìm dữ liệu thiếu

Viết câu đếm số khách hàng **thiếu** thành phố, rồi câu liệt kê họ. Dùng đúng toán tử NULL.

**Gợi ý:** `WHERE Thanh IS NULL`; đối chiếu với `COUNT(*) - COUNT(Thanh)`.

### Bài 3 — Số điện thoại dự phòng

Cho bảng có `SoDiDong` và `SoBan` (đều có thể NULL), viết câu trả về một cột `LienHe` lấy số di động, thiếu thì số bàn, thiếu cả hai thì `N'Không có'`.

**Gợi ý:** `COALESCE(SoDiDong, SoBan, N'Không có')`.

### Bài 4 — Bẫy trung bình

Cho một bảng điểm có vài ô NULL (chưa chấm). So `AVG(Diem)` với `AVG(COALESCE(Diem, 0))` và giải thích vì sao hai số khác nhau, cái nào đúng với câu hỏi "điểm trung bình các bài đã chấm".

**Gợi ý:** `AVG(Diem)` bỏ NULL (đúng cho "bài đã chấm"); bản COALESCE coi bài chưa chấm là 0 điểm.

### Bài 5 — `FLOAT` gây lệch tiền

Tạo một cột `FLOAT`, cộng dồn `0.1` mười lần, so với `1.0`. Rồi làm lại bằng `DECIMAL`. Quan sát khác biệt.

**Gợi ý:** tổng `FLOAT` có thể không đúng `1.0`; `DECIMAL` chính xác — bằng chứng vì sao tiền dùng `DECIMAL`.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi chọn được kiểu dữ liệu phù hợp cho số, tiền, chuỗi, ngày, luận lý.
- [ ] Tôi giải thích được vì sao tiền dùng `DECIMAL` và tiếng Việt dùng `NVARCHAR`.
- [ ] Tôi hiểu NULL là "không biết", khác `0` và `''`.
- [ ] Tôi dùng `IS NULL`/`IS NOT NULL` thay vì `=`/`<>` với NULL.
- [ ] Tôi lường được NULL lan truyền trong số học và bị bỏ qua trong tổng hợp.
- [ ] Tôi dùng được `COALESCE`/`ISNULL` để xử lý giá trị thiếu.

Điều hướng:

- Bài prerequisite: [Thiết kế schema, table, key và constraint](./02-thiet-ke-schema-table-key-constraint.md)
- Ôn lại nền tảng: [Nullable reference type](../05-csharp-nang-cao/06-nullable-reference-type.md)
- Bài tiếp theo: [CRUD: SELECT, INSERT, UPDATE, DELETE](./04-crud-select-insert-update-delete.md)
