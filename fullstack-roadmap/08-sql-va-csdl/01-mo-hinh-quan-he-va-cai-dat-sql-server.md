# Mô hình quan hệ và cài đặt SQL Server

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích vì sao cần cơ sở dữ liệu quan hệ thay vì lưu dữ liệu trong bộ nhớ hay file;
- mô tả **mô hình quan hệ**: bảng, hàng, cột, khóa và quan hệ giữa các bảng;
- phân biệt vai trò của **SQL** (ngôn ngữ khai báo) với code thủ tục đã học ở C#;
- cài đặt SQL Server (Developer edition miễn phí) và một công cụ client để chạy truy vấn;
- tạo database, tạo bảng đầu tiên và chạy câu `SELECT` đầu tiên;
- hiểu mô hình client–server: engine giữ dữ liệu, client gửi câu lệnh.

## 2. Bài toán mở đầu

Suốt module 04–07 bạn lưu dữ liệu trong `List<T>`, `Dictionary<K,V>` và các cấu trúc trong bộ nhớ. Chúng nhanh, nhưng có bốn giới hạn chí mạng khi làm ứng dụng thật:

- **Mất khi tắt chương trình.** RAM bay hết khi process dừng; đơn hàng, khách hàng biến mất.
- **Không nhiều tiến trình cùng dùng được.** Hai người đặt hàng cùng lúc trên hai máy chủ không thấy dữ liệu của nhau.
- **Truy vấn linh hoạt rất khó.** "Tìm khách hàng đăng ký tháng này, sắp theo tên, có đơn trên 1 triệu" — viết tay bằng vòng lặp thì dài và chậm.
- **Không có bảo đảm toàn vẹn.** Không gì ngăn hai đơn hàng trùng mã, hay đơn trỏ tới khách hàng không tồn tại.

**Cơ sở dữ liệu quan hệ** sinh ra để giải cả bốn: dữ liệu lưu bền trên đĩa, nhiều client cùng truy cập an toàn, truy vấn bằng một ngôn ngữ khai báo mạnh (SQL), và ràng buộc toàn vẹn được engine bảo đảm. Bài này dựng nền tảng đó với **SQL Server** — hệ quản trị chính của cả lộ trình — và chạy câu lệnh đầu tiên.

## 3. Lời giải bằng code

### 3.1 Cài đặt SQL Server và công cụ client

SQL Server **Developer edition** miễn phí cho học tập và phát triển, đầy đủ tính năng như bản Enterprise. Chọn một trong hai cách:

**Cách A — Docker (chạy được trên Windows/macOS/Linux):**

```bash
docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=Your_strong_Passw0rd" \
  -p 1433:1433 --name sqlserver -d \
  mcr.microsoft.com/mssql/server:2022-latest
```

**Cách B — cài trực tiếp trên Windows:** tải "SQL Server 2022 Developer" từ trang Microsoft, chạy trình cài, chọn *Basic*.

Sau đó cài một **client** để gõ truy vấn — khuyến nghị **Azure Data Studio** (đa nền tảng) hoặc **SQL Server Management Studio / SSMS** (Windows). Dòng lệnh thì dùng `sqlcmd`:

```bash
sqlcmd -S localhost -U sa -P "Your_strong_Passw0rd" -C
```

> Phần cài đặt này đặc thù SQL Server nên không thể minh họa bằng output chạy sẵn trong tài liệu. Các phiên bản, cổng `1433` và tài khoản `sa` theo tài liệu chính thức của Microsoft; hãy đặt mật khẩu mạnh và không dùng `sa` cho ứng dụng thật (bài [23](./23-bao-mat-phan-quyen-va-sql-injection.md) sẽ bàn phân quyền).

### 3.2 Tạo database, bảng và chạy truy vấn đầu tiên

Trong client, chạy các câu lệnh sau (đây là **T-SQL** — phương ngữ SQL của SQL Server):

```sql
-- Tạo một database mới cho cửa hàng
CREATE DATABASE Shop;
GO

USE Shop;
GO

-- Tạo bảng khách hàng: mỗi cột có kiểu dữ liệu và ràng buộc
CREATE TABLE KhachHang (
    KhachHangId INT IDENTITY(1,1) PRIMARY KEY, -- khóa chính, tự tăng
    HoTen       NVARCHAR(100) NOT NULL,          -- chuỗi Unicode, bắt buộc
    Email       NVARCHAR(255) NOT NULL,
    NgayDangKy  DATE NOT NULL
);
GO

-- Thêm dữ liệu (N'...' cho chuỗi Unicode tiếng Việt)
INSERT INTO KhachHang (HoTen, Email, NgayDangKy) VALUES
    (N'An Nguyễn',  N'an@example.com',   '2026-01-15'),
    (N'Bình Trần',  N'binh@example.com', '2026-02-20'),
    (N'Cường Lê',   N'cuong@example.com','2026-03-05');
GO

-- Truy vấn: lấy ba cột của mọi khách hàng
SELECT KhachHangId, HoTen, NgayDangKy
FROM KhachHang;
GO
```

Kết quả câu `SELECT`:

```text
KhachHangId | HoTen     | NgayDangKy
------------+-----------+-----------
1           | An Nguyễn | 2026-01-15
2           | Bình Trần | 2026-02-20
3           | Cường Lê  | 2026-03-05
```

Ba hàng vừa thêm hiện ra, `KhachHangId` được engine tự sinh `1, 2, 3` nhờ `IDENTITY`.

## 4. Giải thích cơ chế

### 4.1 Mô hình quan hệ: mọi thứ là bảng

Mô hình quan hệ (Edgar Codd, 1970) tổ chức dữ liệu thành **bảng (table)** — còn gọi là **quan hệ (relation)**:

```text
                 cột (column / attribute)
                 ┌──────────┬───────────┬───────────────────┬────────────┐
                 │KhachHangId│  HoTen   │      Email        │ NgayDangKy │
                 ├──────────┼───────────┼───────────────────┼────────────┤
   hàng (row) →  │    1     │An Nguyễn │ an@example.com    │ 2026-01-15 │
                 │    2     │Bình Trần │ binh@example.com  │ 2026-02-20 │
                 │    3     │Cường Lê  │ cuong@example.com │ 2026-03-05 │
                 └──────────┴───────────┴───────────────────┴────────────┘
```

- **Cột (column):** một thuộc tính, có **kiểu dữ liệu** cố định (`INT`, `NVARCHAR`, `DATE`...).
- **Hàng (row):** một bản ghi — một khách hàng cụ thể.
- **Bảng (table):** tập các hàng cùng cấu trúc.

So với `List<KhachHang>` trong C#: bảng giống danh sách các object, cột giống property, hàng giống một object. Khác biệt cốt lõi: bảng nằm **trên đĩa**, được **nhiều client** dùng chung, và engine **ép kiểu + ràng buộc** trên mọi hàng.

### 4.2 Khóa và quan hệ

**Khóa chính (primary key)** là cột (hay nhóm cột) định danh **duy nhất** mỗi hàng — ở đây là `KhachHangId`. Không hai khách hàng nào cùng `KhachHangId`, và nó không được `NULL`. Đó là cách phân biệt hai khách hàng dù trùng tên.

Sức mạnh thật của mô hình quan hệ là **nối các bảng qua khóa**. Khi có thêm bảng `DonHang` với cột `KhachHangId`, cột đó là **khóa ngoại (foreign key)** trỏ về `KhachHang` — diễn tả quan hệ "đơn hàng này thuộc về khách hàng kia". Ta sẽ dựng đầy đủ quan hệ ở bài [02](./02-thiet-ke-schema-table-key-constraint.md) và [08](./08-inner-left-right-full-cross-join.md).

### 4.3 SQL là ngôn ngữ khai báo

Điểm chuyển tư duy lớn nhất từ C#: SQL là **declarative** — bạn mô tả **kết quả muốn có**, không mô tả **cách lấy**. Câu:

```sql
SELECT KhachHangId, HoTen, NgayDangKy FROM KhachHang;
```

nói "cho tôi ba cột này của mọi hàng trong `KhachHang`". Bạn **không** viết vòng lặp, không mở file, không quản lý con trỏ. Engine tự quyết định đọc dữ liệu thế nào cho nhanh (bài [21](./21-execution-plan-va-statistics.md) — execution plan). SQL gồm mấy nhóm lệnh:

- **DDL** (Data Definition): `CREATE`, `ALTER`, `DROP` — định nghĩa cấu trúc.
- **DML** (Data Manipulation): `SELECT`, `INSERT`, `UPDATE`, `DELETE` — thao tác dữ liệu.
- **DCL** (Data Control): `GRANT`, `REVOKE` — phân quyền (bài [23](./23-bao-mat-phan-quyen-va-sql-injection.md)).

### 4.4 Mô hình client–server

SQL Server là một **engine** chạy như một dịch vụ, giữ dữ liệu trên đĩa và lắng nghe ở cổng `1433`. Client (Azure Data Studio, `sqlcmd`, hay ứng dụng .NET của bạn) **kết nối** tới engine, gửi câu SQL, nhận về **result set**:

```text
   Client (SSMS / sqlcmd / app .NET)          Server (SQL Server engine)
   ┌───────────────────────────┐   câu SQL    ┌──────────────────────────┐
   │  SELECT ... FROM KhachHang │ ───────────▶ │  đọc từ đĩa, xử lý        │
   │                            │ ◀─────────── │  trả result set          │
   └───────────────────────────┘  các hàng    └──────────────────────────┘
                                                       │
                                                  dữ liệu bền trên đĩa
```

Nhờ tách client và server, **nhiều client** cùng nối tới một database, dữ liệu **sống độc lập** với ứng dụng, và engine lo chuyện đồng thời, giao dịch, bảo mật.

### Đào sâu (có thể quay lại sau)

- **`GO` không phải lệnh SQL.** `GO` là dấu ngăn "batch" của công cụ client SQL Server (sqlcmd/SSMS), không phải T-SQL chuẩn. Nó bảo client gửi khối lệnh phía trên đi. Client khác (hay code .NET) không dùng `GO`.
- **`IDENTITY(1,1)`** bảo SQL Server tự sinh số cho khóa chính, bắt đầu từ 1, mỗi hàng tăng 1. PostgreSQL dùng `GENERATED ALWAYS AS IDENTITY` hoặc `SERIAL` cho cùng mục đích — một khác biệt phương ngữ điển hình.
- **`NVARCHAR` vs `VARCHAR`.** `NVARCHAR` lưu Unicode (tiếng Việt có dấu an toàn); `VARCHAR` lưu bảng mã một byte. Tiền tố `N'...'` báo chuỗi là Unicode. Với dữ liệu tiếng Việt, dùng `NVARCHAR`.
- **Có nhiều hệ quản trị quan hệ.** SQL Server, PostgreSQL, MySQL, Oracle... đều theo mô hình quan hệ và nói SQL, nhưng mỗi hệ có phương ngữ riêng. Lộ trình này dùng SQL Server làm chính; khi một khác biệt giúp hiểu bản chất provider/dialect, tài liệu sẽ ghi chú PostgreSQL.

## 5. Kiến thức nền

### Vì sao "quan hệ" chứ không phải "quan hệ giữa các bảng"

Tên "relational" **không** nói về quan hệ giữa các bảng, mà về khái niệm toán học **relation** = một tập các bộ (tuple) — chính là một bảng các hàng. Đây là hiểu lầm phổ biến. Quan hệ giữa các bảng (qua khóa ngoại) là hệ quả, không phải nguồn gốc của cái tên.

### Bảng so với collection trong C#

| Khái niệm C# | Tương ứng trong CSDL quan hệ |
|---|---|
| `List<KhachHang>` | bảng `KhachHang` |
| một object `KhachHang` | một hàng |
| property `HoTen` | cột `HoTen` |
| kiểu `string`, `int` | kiểu SQL `NVARCHAR`, `INT` |
| lưu trong RAM | lưu bền trên đĩa |
| một process dùng | nhiều client dùng chung |

### SQL Server so với các lựa chọn

SQL Server mạnh về hệ sinh thái .NET (tích hợp EF Core ở [module 09](../09-linq-va-ef-core/11-ef-core-9-dbcontext-va-entity.md)), công cụ (SSMS, Azure Data Studio), và bản Developer miễn phí đầy đủ tính năng. Kiến thức SQL cốt lõi (bảng, khóa, join, transaction) chuyển được sang mọi hệ quản trị quan hệ khác.

## 6. Lỗi thường gặp

### Nghĩ database chỉ là "chỗ chứa file"

Database quan hệ không phải folder chứa file — nó là một engine chủ động: ép kiểu, bảo đảm toàn vẹn, xử lý đồng thời, tối ưu truy vấn. Coi nó như "kho file" bỏ lỡ toàn bộ giá trị.

### Dùng `VARCHAR` cho dữ liệu tiếng Việt

`VARCHAR` không lưu Unicode đầy đủ; tên có dấu có thể thành ký tự lỗi. Với tiếng Việt dùng `NVARCHAR` và tiền tố `N'...'` khi nhập literal.

### Nhầm SQL khai báo với code thủ tục

Cố "viết vòng lặp" trong SQL cho việc mà một câu `SELECT` làm được là chống lại bản chất khai báo của nó — vừa dài vừa chậm. Hãy mô tả kết quả muốn có và để engine lo cách thực hiện.

### Dùng tài khoản `sa` cho mọi thứ

`sa` là tài khoản quản trị toàn quyền. Dùng nó cho ứng dụng thật là rủi ro bảo mật lớn. Tạo tài khoản riêng với quyền tối thiểu (bài [23](./23-bao-mat-phan-quyen-va-sql-injection.md)).

### Quên `IDENTITY` khi cần khóa tự tăng

Nếu tự gán `KhachHangId` bằng tay, bạn phải tự lo không trùng. `IDENTITY` để engine sinh số duy nhất tăng dần — dùng nó cho khóa chính đại diện (surrogate key).

## 7. Bài tập

### Bài 1 — Bảng sản phẩm

Tạo bảng `SanPham` với `SanPhamId` (khóa chính tự tăng), `Ten` (`NVARCHAR`, bắt buộc), `Gia` (`DECIMAL(12,2)`), `ConHang` (`BIT`). Thêm ba sản phẩm rồi `SELECT` ra.

**Gợi ý:** `BIT` là kiểu true/false của SQL Server; giá trị `1`/`0`.

### Bài 2 — Vẽ mô hình quan hệ

Với bảng `KhachHang` trong bài, vẽ ra giấy các thành phần: tên bảng, tên cột kèm kiểu, khóa chính. Đối chiếu với một `class KhachHang` trong C#.

**Gợi ý:** mỗi property C# ↔ một cột; mỗi object ↔ một hàng.

### Bài 3 — Kiểu dữ liệu phù hợp

Cho các dữ liệu: số điện thoại, ngày sinh, số dư tài khoản, trạng thái đã kích hoạt, ghi chú dài. Chọn kiểu SQL Server phù hợp cho mỗi cái và giải thích.

**Gợi ý:** số điện thoại nên là chuỗi (giữ số 0 đầu), không phải số; số dư dùng `DECIMAL` chứ không `FLOAT`.

### Bài 4 — Truy vấn chọn cột

Từ bảng `KhachHang`, viết câu chỉ lấy `HoTen` và `Email` (không lấy `KhachHangId`, `NgayDangKy`). Chạy và so kết quả với `SELECT *`.

**Gợi ý:** liệt kê đúng các cột cần sau `SELECT`; tránh `SELECT *` trong code thật.

### Bài 5 — Client và server

Giải thích bằng lời: khi ứng dụng .NET của bạn gọi database, đâu là client, đâu là server, dữ liệu nằm ở đâu, và điều gì xảy ra nếu tắt ứng dụng .NET (dữ liệu còn không?).

**Gợi ý:** dữ liệu sống trong engine SQL Server, độc lập với vòng đời ứng dụng client.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi nêu được bốn giới hạn của lưu trữ trong bộ nhớ mà CSDL quan hệ giải quyết.
- [ ] Tôi mô tả được bảng, hàng, cột, khóa chính bằng ví dụ cụ thể.
- [ ] Tôi phân biệt SQL khai báo với code thủ tục.
- [ ] Tôi cài được SQL Server (Docker hoặc Windows) và kết nối bằng một client.
- [ ] Tôi tạo được database, bảng và chạy `SELECT` đầu tiên.
- [ ] Tôi giải thích được mô hình client–server và vì sao dữ liệu sống độc lập với ứng dụng.

Điều hướng:

- Bài prerequisite: [Module 07, bài 19 — Dự án engine tìm đường](../07-cau-truc-du-lieu-giai-thuat/19-du-an-engine-tim-duong.md)
- Ôn lại nền tảng: [Collection: List, Dictionary, HashSet, Queue và Stack](../04-csharp-co-ban/13-collection-list-dictionary-hashset-queue-stack.md)
- Bài tiếp theo: [Thiết kế schema, table, key và constraint](./02-thiet-ke-schema-table-key-constraint.md)
