# Filter, sort và pagination

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng WHERE với nhiều predicate;
- dùng IN, BETWEEN, LIKE;
- sort bằng ORDER BY nhiều column;
- phân trang bằng OFFSET/FETCH;
- hiểu pagination phải có deterministic order;
- mô tả nhược điểm offset pagination ở page sâu;
- chuẩn bị cho keyset pagination.

## 2. Bài toán mở đầu

API product cần hỗ trợ:

```text
search = "keyboard"
minPrice = 500000
maxPrice = 3000000
isActive = true
sort = price-desc
page = 2
pageSize = 20
```

Nếu query không có order ổn định, page 1 và page 2 có thể trùng hoặc thiếu item khi dữ liệu thay đổi.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_05') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_05
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_05;
END;
GO

CREATE DATABASE CommerceLab08_05;
GO
USE CommerceLab08_05;
GO

CREATE TABLE dbo.Products
(
    ProductId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Name nvarchar(160) NOT NULL,
    Price decimal(19,4) NOT NULL,
    IsActive bit NOT NULL,
    CreatedAt datetime2(0) NOT NULL
);
GO

INSERT INTO dbo.Products (Name, Price, IsActive, CreatedAt)
VALUES
(N'Mechanical Keyboard A', 1200000, 1, '2026-01-01'),
(N'Mechanical Keyboard B', 1800000, 1, '2026-01-02'),
(N'Office Keyboard',       500000, 1, '2026-01-03'),
(N'Gaming Mouse',          900000, 1, '2026-01-04'),
(N'4K Monitor',           6500000, 1, '2026-01-05'),
(N'USB Hub',               400000, 0, '2026-01-06'),
(N'Keyboard Wrist Rest',   350000, 1, '2026-01-07'),
(N'Mechanical Keyboard C',2200000, 1, '2026-01-08');
GO

DECLARE @Search nvarchar(100) = N'Keyboard';
DECLARE @MinPrice decimal(19,4) = 400000;
DECLARE @MaxPrice decimal(19,4) = 3000000;
DECLARE @Page int = 1;
DECLARE @PageSize int = 3;

SELECT
    ProductId,
    Name,
    Price,
    CreatedAt
FROM dbo.Products
WHERE IsActive = 1
  AND Name LIKE N'%' + @Search + N'%'
  AND Price BETWEEN @MinPrice AND @MaxPrice
ORDER BY
    Price DESC,
    ProductId ASC
OFFSET (@Page - 1) * @PageSize ROWS
FETCH NEXT @PageSize ROWS ONLY;
GO

SELECT
    ProductId,
    Name,
    Price
FROM dbo.Products
WHERE ProductId > 3
ORDER BY ProductId
OFFSET 0 ROWS
FETCH NEXT 3 ROWS ONLY;
GO
```

## 4. Giải thích cơ chế

### WHERE

Predicate kết hợp bằng:

```text
AND
OR
NOT
```

Dùng ngoặc khi logic phức tạp.

### LIKE

```sql
LIKE N'%Keyboard%'
```

leading wildcard thường khó tận dụng B-tree index hiệu quả.

Đây là preview cho SARGability ở bài 22.

### ORDER BY

Pagination không nên chỉ:

```sql
ORDER BY Price DESC
```

nếu nhiều row cùng Price.

Thêm tiebreaker unique:

```sql
ORDER BY Price DESC, ProductId ASC
```

để order deterministic.

### OFFSET/FETCH

```sql
OFFSET 20 ROWS
FETCH NEXT 20 ROWS ONLY
```

dễ hiểu và phù hợp nhiều UI.

Nhưng page sâu có thể buộc engine đọc/bỏ qua nhiều row.

## 5. Kiến thức nền

### Offset pagination

Ưu điểm:

- page number dễ hiển thị;
- random jump tới page N.

Nhược:

- page sâu đắt;
- concurrent insert/delete làm page drift.

### Keyset pagination

Thay vì:

```text
page=10000
```

gửi cursor:

```text
afterProductId=812345
```

Query:

```sql
WHERE ProductId > @After
ORDER BY ProductId
```

rất phù hợp infinite scroll/feed.

### TOP

```sql
SELECT TOP (10) ...
ORDER BY ...
```

luôn đi cùng ORDER BY nếu cần “top” có nghĩa xác định.

## 6. Lỗi thường gặp

### Pagination không ORDER BY

Relational table không có natural presentation order được bảo đảm.

### ORDER BY không unique

Các row tie có thể đổi vị trí giữa request.

### Search `%term%` trên table lớn

Có thể cần full-text search hoặc search engine riêng.

### Client tự tải tất cả rồi phân trang

Backend phải filter/sort/page gần dữ liệu khi dataset lớn.

## 7. Bài tập

### Bài 1

Filter active product giá dưới 1 triệu.

### Bài 2

Sort theo IsActive desc, Price asc, ProductId asc.

### Bài 3

Viết page 2 size 2 bằng OFFSET/FETCH.

### Bài 4

Viết keyset pagination theo `(CreatedAt, ProductId)`.

### Bài 5

Giải thích vì sao `ORDER BY Price` chưa đủ stable.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi viết được WHERE nhiều predicate.
- [ ] Tôi dùng IN/BETWEEN/LIKE đúng.
- [ ] Tôi sort nhiều column.
- [ ] Tôi phân trang bằng OFFSET/FETCH.
- [ ] Tôi dùng unique tiebreaker.
- [ ] Tôi hiểu offset và keyset pagination khác nhau.

Điều hướng:

- Bài trước: [CRUD](./04-crud-select-insert-update-delete.md)
- Bài tiếp theo: [Hàm scalar, CASE và xử lý NULL](./06-ham-scalar-case-va-xu-ly-null.md)
