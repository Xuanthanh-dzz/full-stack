# Thiết kế schema, table, key và constraint

## 1. Mục tiêu

Sau bài này, bạn có thể:

- thiết kế một schema nhiều bảng cho bài toán thực tế (cửa hàng thương mại điện tử);
- dùng đúng **primary key**, **foreign key**, **unique**, **not null**, **check** và **default**;
- phân biệt **surrogate key** (khóa đại diện) với **natural key** (khóa tự nhiên);
- tạo **composite key** (khóa gồm nhiều cột);
- giải thích cách constraint để engine **bảo đảm toàn vẹn dữ liệu** thay vì phó mặc cho ứng dụng;
- đọc được lỗi khi một câu `INSERT` vi phạm ràng buộc.

## 2. Bài toán mở đầu

Bài [01](./01-mo-hinh-quan-he-va-cai-dat-sql-server.md) có một bảng `KhachHang` đơn lẻ. Cửa hàng thật cần nhiều bảng liên kết: khách hàng đặt **đơn hàng**, mỗi đơn gồm nhiều **sản phẩm**, mỗi sản phẩm thuộc một **danh mục**. Nếu không có ràng buộc, dữ liệu rác tràn vào mà không ai chặn:

- hai khách hàng cùng email;
- một sản phẩm giá **âm**;
- một đơn hàng trỏ tới khách hàng **không tồn tại**;
- một khách hàng **thiếu tên**.

Ta có thể kiểm tra mọi thứ trong code C#, nhưng nếu có nhiều ứng dụng cùng ghi vào database, hoặc ai đó chạy `INSERT` tay, thì tầng ứng dụng không đủ. **Constraint** đưa các quy tắc này vào chính engine: dữ liệu sai bị **từ chối tại nguồn**, bất kể ai ghi. Bài này thiết kế schema đầy đủ cho cửa hàng và để engine gác cửa toàn vẹn.

## 3. Lời giải bằng code

Thiết kế schema năm bảng (chạy trong database `Shop` đã tạo ở bài 01):

```sql
-- Danh mục sản phẩm
CREATE TABLE DanhMuc (
    DanhMucId INT IDENTITY(1,1) PRIMARY KEY,
    Ten       NVARCHAR(100) NOT NULL UNIQUE   -- tên danh mục không trùng
);

-- Khách hàng
CREATE TABLE KhachHang (
    KhachHangId INT IDENTITY(1,1) PRIMARY KEY,
    HoTen       NVARCHAR(100) NOT NULL,
    Email       NVARCHAR(255) NOT NULL UNIQUE, -- email là định danh tự nhiên, không trùng
    NgayDangKy  DATE NOT NULL,
    Thanh       NVARCHAR(50)                    -- cho phép NULL (chưa biết)
);

-- Sản phẩm: mỗi sản phẩm thuộc một danh mục
CREATE TABLE SanPham (
    SanPhamId INT IDENTITY(1,1) PRIMARY KEY,
    Ten       NVARCHAR(200) NOT NULL,
    DanhMucId INT NOT NULL
        REFERENCES DanhMuc(DanhMucId),           -- khóa ngoại
    Gia       DECIMAL(12,2) NOT NULL CHECK (Gia >= 0),   -- giá không âm
    TonKho    INT NOT NULL DEFAULT 0 CHECK (TonKho >= 0) -- mặc định 0, không âm
);

-- Đơn hàng: mỗi đơn thuộc một khách hàng
CREATE TABLE DonHang (
    DonHangId   INT IDENTITY(1,1) PRIMARY KEY,
    KhachHangId INT NOT NULL
        REFERENCES KhachHang(KhachHangId),
    NgayDat     DATE NOT NULL,
    TrangThai   NVARCHAR(20) NOT NULL DEFAULT N'Moi'
);

-- Chi tiết đơn: mỗi dòng là một sản phẩm trong một đơn
CREATE TABLE ChiTietDonHang (
    DonHangId INT NOT NULL REFERENCES DonHang(DonHangId),
    SanPhamId INT NOT NULL REFERENCES SanPham(SanPhamId),
    SoLuong   INT NOT NULL CHECK (SoLuong > 0),
    DonGia    DECIMAL(12,2) NOT NULL,
    PRIMARY KEY (DonHangId, SanPhamId)           -- khóa chính GỒM hai cột
);
```

Sau khi tạo và nạp dữ liệu mẫu (4 khách, 6 sản phẩm, 4 đơn), thử ghi dữ liệu sai — engine từ chối cả bốn:

```sql
-- 1. Trùng email -> vi phạm UNIQUE
INSERT INTO KhachHang (HoTen, Email, NgayDangKy)
VALUES (N'An Giả', N'an@example.com', '2026-04-01');
```
```text
Msg 2627: Violation of UNIQUE KEY constraint 'UQ_KhachHang_Email'.
Cannot insert duplicate key ... The duplicate key value is (an@example.com).
```

```sql
-- 2. Giá âm -> vi phạm CHECK
INSERT INTO SanPham (Ten, DanhMucId, Gia) VALUES (N'Hàng lỗi', 1, -5000);
```
```text
Msg 547: The INSERT statement conflicted with the CHECK constraint 'CK_SanPham_Gia'.
```

```sql
-- 3. Đơn cho khách không tồn tại -> vi phạm FOREIGN KEY
INSERT INTO DonHang (KhachHangId, NgayDat) VALUES (999, '2026-04-01');
```
```text
Msg 547: The INSERT statement conflicted with the FOREIGN KEY constraint
'FK_DonHang_KhachHang'. The conflict occurred in table 'KhachHang', column 'KhachHangId'.
```

```sql
-- 4. Thiếu tên -> vi phạm NOT NULL
INSERT INTO KhachHang (Email, NgayDangKy) VALUES (N'x@example.com', '2026-04-01');
```
```text
Msg 515: Cannot insert the value NULL into column 'HoTen'... column does not allow nulls.
```

Cả bốn câu bị chặn; số khách hàng vẫn là **4** — không một dòng rác nào lọt vào.

## 4. Giải thích cơ chế

### 4.1 Sơ đồ quan hệ

Năm bảng nối với nhau qua khóa ngoại:

```text
   DanhMuc                    KhachHang
   ┌──────────┐              ┌────────────┐
   │DanhMucId*│              │KhachHangId*│
   │Ten       │              │HoTen ...   │
   └────┬─────┘              └─────┬──────┘
        │ 1                        │ 1
        │ n                        │ n
   ┌────┴─────┐              ┌─────┴──────┐
   │SanPham   │              │DonHang     │
   │SanPhamId*│              │DonHangId*  │
   │DanhMucId→│              │KhachHangId→│
   └────┬─────┘              └─────┬──────┘
        │ n                        │ n
        │       ┌──────────────────┘
        │  n    │  (ChiTietDonHang nối DonHang với SanPham)
   ┌────┴───────┴────┐
   │ChiTietDonHang   │
   │DonHangId→  (PK) │
   │SanPhamId→  (PK) │
   │SoLuong, DonGia  │
   └─────────────────┘
   (* = khóa chính, → = khóa ngoại)
```

Đây là các quan hệ **một–nhiều**: một danh mục có nhiều sản phẩm; một khách hàng có nhiều đơn. `ChiTietDonHang` là **bảng nối** hiện thực quan hệ **nhiều–nhiều** giữa `DonHang` và `SanPham` (một đơn có nhiều sản phẩm, một sản phẩm nằm trong nhiều đơn). Bài [14](./14-mo-hinh-er-va-quan-he.md) sẽ hình thức hóa việc mô hình hóa quan hệ.

### 4.2 Sáu loại constraint

| Constraint | Bảo đảm | Ví dụ trong schema |
|---|---|---|
| `PRIMARY KEY` | định danh duy nhất, không NULL | `KhachHangId` |
| `FOREIGN KEY` | giá trị phải tồn tại ở bảng cha | `DonHang.KhachHangId → KhachHang` |
| `UNIQUE` | không trùng (nhưng cho phép NULL) | `KhachHang.Email` |
| `NOT NULL` | bắt buộc có giá trị | `HoTen` |
| `CHECK` | thỏa một điều kiện logic | `Gia >= 0` |
| `DEFAULT` | giá trị mặc định khi không cung cấp | `TonKho DEFAULT 0` |

Điểm mấu chốt: các quy tắc này sống **trong database**. Dù dữ liệu đến từ ứng dụng .NET, từ một script, hay từ một hệ thống khác, engine đều áp cùng bộ luật. Đây là "một nguồn sự thật" cho toàn vẹn dữ liệu — an toàn hơn nhiều so với rải kiểm tra khắp các ứng dụng.

### 4.3 Foreign key và toàn vẹn tham chiếu

`DonHang.KhachHangId REFERENCES KhachHang(KhachHangId)` bảo đảm **toàn vẹn tham chiếu**: mọi đơn hàng phải trỏ tới một khách hàng **có thật**. Câu `INSERT` với `KhachHangId = 999` bị chặn vì không có khách hàng nào mang id đó. Khóa ngoại cũng chi phối việc **xóa**: mặc định, không xóa được một khách hàng khi vẫn còn đơn trỏ tới họ (tránh "đơn mồ côi") — trừ khi cấu hình `ON DELETE CASCADE`.

### 4.4 Composite key

`ChiTietDonHang` có khóa chính **gồm hai cột** `(DonHangId, SanPhamId)`. Nghĩa là: trong một đơn, mỗi sản phẩm xuất hiện **đúng một dòng** (muốn mua thêm thì tăng `SoLuong`, không tạo dòng thứ hai). Composite key phù hợp cho bảng nối, nơi tính duy nhất đến từ **tổ hợp** các khóa ngoại chứ không từ một cột đơn.

### Đào sâu (có thể quay lại sau)

- **Surrogate vs natural key.** `KhachHangId` (số tự tăng, vô nghĩa nghiệp vụ) là **surrogate key**. `Email` (có ý nghĩa, định danh khách hàng) là **natural key**. Thực tế thường dùng surrogate làm khóa chính (ổn định, nhỏ, không đổi) và đặt `UNIQUE` trên natural key để vẫn chống trùng. Email có thể đổi; id thì không.
- **`UNIQUE` cho phép NULL.** Khác `PRIMARY KEY`, cột `UNIQUE` được phép một (SQL Server) giá trị `NULL`. `Thanh` để `NULL` nghĩa là "chưa biết", hợp lệ. Bài [03](./03-kieu-du-lieu-va-null.md) mổ xẻ NULL.
- **Đặt tên constraint.** Nên đặt tên rõ (`CK_SanPham_Gia`, `FK_DonHang_KhachHang`) thay để engine tự sinh tên ngẫu nhiên — thông báo lỗi dễ đọc và migration dễ quản lý hơn.
- **`ON DELETE`/`ON UPDATE`.** Khóa ngoại có thể cấu hình hành vi khi bản ghi cha bị xóa/sửa: `NO ACTION` (mặc định, chặn), `CASCADE` (xóa/sửa lây), `SET NULL`. Chọn tùy nghiệp vụ — cascade tiện nhưng dễ xóa nhầm hàng loạt.

## 5. Kiến thức nền

### Constraint là hợp đồng dữ liệu

Constraint chính là "invariant" của [module 06](../06-oop-va-thiet-ke/13-design-by-contract-va-invariant.md) nhưng ở tầng dữ liệu: chúng bảo đảm database **không bao giờ** ở trạng thái sai. Một object C# có invariant nhờ constructor; một bảng có invariant nhờ constraint. Cả hai cùng triết lý: làm cho trạng thái sai **không thể tồn tại**.

### Vì sao không chỉ kiểm tra trong ứng dụng

- Nhiều ứng dụng/nhiều ngôn ngữ có thể dùng chung một database — mỗi cái tự kiểm tra sẽ lệch nhau.
- Import dữ liệu, sửa tay, job nền... đi vòng qua tầng ứng dụng.
- Engine kiểm tra ở tốc độ cao và **nguyên tử** cùng với thao tác ghi.

Kiểm tra ở ứng dụng vẫn cần (phản hồi sớm, thông báo thân thiện), nhưng constraint database là **lưới an toàn cuối cùng** không được bỏ.

### Thiết kế bảng: vài nguyên tắc

- Mỗi bảng mô tả **một loại thực thể** (khách hàng, sản phẩm, đơn).
- Mỗi bảng có **khóa chính**.
- Quan hệ diễn tả bằng **khóa ngoại**, không nhồi mọi thứ vào một bảng.
- Chọn **kiểu dữ liệu** hẹp nhất đủ dùng (bài [03](./03-kieu-du-lieu-va-null.md)).
- Bài [15](./15-chuan-hoa-1nf-2nf-3nf-bcnf.md) sẽ chuẩn hóa việc chia bảng này thành lý thuyết (chuẩn hóa).

## 6. Lỗi thường gặp

### Không đặt khóa ngoại

Bỏ khóa ngoại vì "ứng dụng sẽ lo" dẫn tới đơn mồ côi, dữ liệu trỏ tới bản ghi đã xóa. Luôn khai báo khóa ngoại cho quan hệ giữa các bảng.

### Dùng natural key làm khóa chính rồi nó thay đổi

Lấy email làm khóa chính, đến khi khách đổi email thì mọi khóa ngoại trỏ tới đều phải sửa. Dùng surrogate key ổn định làm khóa chính, đặt `UNIQUE` trên natural key.

### Nhầm `UNIQUE` với `PRIMARY KEY`

Một bảng chỉ có **một** primary key nhưng nhiều `UNIQUE`. Primary key không cho NULL; `UNIQUE` cho phép. Dùng primary key cho định danh chính, `UNIQUE` cho các ràng buộc không trùng khác.

### Quên `CHECK` cho quy tắc miền giá trị

Không có `CHECK (Gia >= 0)`, một giá âm lọt vào âm thầm. Mọi quy tắc "giá trị phải nằm trong khoảng/thỏa điều kiện" nên thành một `CHECK`.

### Lạm dụng `ON DELETE CASCADE`

Cascade tiện nhưng nguy hiểm: xóa một khách hàng có thể xóa lây toàn bộ đơn hàng lịch sử. Chỉ dùng cascade khi bản ghi con **thực sự** vô nghĩa nếu thiếu bản ghi cha (như chi tiết đơn khi xóa đơn).

## 7. Bài tập

### Bài 1 — Bảng nhà cung cấp

Thêm bảng `NhaCungCap` (id, tên bắt buộc, email unique, số điện thoại) và thêm cột khóa ngoại `NhaCungCapId` vào `SanPham`. Viết đủ constraint.

**Gợi ý:** `SanPham.NhaCungCapId` là khóa ngoại `REFERENCES NhaCungCap`; quyết định nó `NOT NULL` hay cho `NULL`.

### Bài 2 — Chặn số lượng và giá bất hợp lý

Thêm `CHECK` để `ChiTietDonHang.DonGia >= 0` và `DonHang.TrangThai` chỉ nhận các giá trị `'Moi'`, `'DangGiao'`, `'HoanThanh'`, `'Huy'`.

**Gợi ý:** `CHECK (TrangThai IN (N'Moi', N'DangGiao', ...))` giới hạn miền giá trị.

### Bài 3 — Thử vi phạm từng constraint

Viết bốn câu `INSERT`, mỗi câu cố tình vi phạm một loại constraint khác nhau, và dự đoán thông báo lỗi trước khi chạy.

**Gợi ý:** so kết quả với bốn ví dụ trong bài; mỗi loại có mã lỗi riêng.

### Bài 4 — Surrogate hay natural?

Cho ba thực thể: tỉnh/thành (có mã bưu chính), sách (có ISBN), người dùng (có username). Với mỗi cái, quyết định dùng surrogate key hay natural key làm khóa chính và giải thích.

**Gợi ý:** hỏi "giá trị này có bao giờ đổi không, có ổn định và nhỏ gọn không?".

### Bài 5 — Quan hệ nhiều–nhiều

Thiết kế bảng cho quan hệ "một sinh viên học nhiều môn, một môn có nhiều sinh viên", có lưu điểm. Chỉ ra bảng nối và khóa chính của nó.

**Gợi ý:** bảng nối `DangKy(SinhVienId, MonHocId, Diem)` với composite primary key `(SinhVienId, MonHocId)`.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi thiết kế được schema nhiều bảng với quan hệ qua khóa ngoại.
- [ ] Tôi dùng đúng sáu loại constraint và giải thích mỗi cái bảo đảm gì.
- [ ] Tôi phân biệt surrogate key và natural key, biết khi nào dùng cái nào.
- [ ] Tôi tạo được composite key cho bảng nối.
- [ ] Tôi giải thích được vì sao constraint database an toàn hơn chỉ kiểm tra ở ứng dụng.
- [ ] Tôi đọc được lỗi khi `INSERT` vi phạm từng loại constraint.

Điều hướng:

- Bài prerequisite: [Mô hình quan hệ và cài đặt SQL Server](./01-mo-hinh-quan-he-va-cai-dat-sql-server.md)
- Ôn lại nền tảng: [Design by contract và invariant](../06-oop-va-thiet-ke/13-design-by-contract-va-invariant.md)
- Bài tiếp theo: [Kiểu dữ liệu và NULL](./03-kieu-du-lieu-va-null.md)
