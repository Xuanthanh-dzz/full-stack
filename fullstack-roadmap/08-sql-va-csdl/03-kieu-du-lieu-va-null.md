# Kiểu dữ liệu và NULL

## 1. Mục tiêu

Sau bài này, bạn có thể:

- chọn integer, decimal, string, date/time và binary type phù hợp;
- phân biệt `varchar` và `nvarchar`;
- hiểu precision/scale của `decimal`;
- hiểu `NULL` là unknown/missing chứ không phải 0 hay chuỗi rỗng;
- dùng `IS NULL` và `IS NOT NULL`;
- tránh lỗi so sánh NULL bằng `=`;
- thiết kế nullable theo business semantics.

## 2. Bài toán mở đầu

Một table Product có:

```text
Price = 99.99
Weight = chưa biết
Description = ""
ReleasedAt = chưa có
```

Bốn trạng thái không giống nhau.

Nếu mọi thứ đều lưu string, bạn mất:

- validation kiểu;
- sort đúng;
- arithmetic;
- storage tối ưu;
- semantics NULL.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_03') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_03
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_03;
END;
GO

CREATE DATABASE CommerceLab08_03;
GO
USE CommerceLab08_03;
GO

CREATE TABLE dbo.Products
(
    ProductId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,

    Sku varchar(40) NOT NULL,
    Name nvarchar(160) NOT NULL,

    Price decimal(19,4) NOT NULL,
    WeightKg decimal(10,3) NULL,

    Stock int NOT NULL,
    IsActive bit NOT NULL,

    ReleasedAt date NULL,
    CreatedAt datetime2(3) NOT NULL,

    Description nvarchar(2000) NULL,
    RowVersion rowversion NOT NULL,

    CONSTRAINT CK_Products_Price CHECK (Price >= 0),
    CONSTRAINT CK_Products_Stock CHECK (Stock >= 0)
);
GO

INSERT INTO dbo.Products
(
    Sku,
    Name,
    Price,
    WeightKg,
    Stock,
    IsActive,
    ReleasedAt,
    CreatedAt,
    Description
)
VALUES
(
    'KB-01',
    N'Bàn phím cơ',
    1299000.0000,
    NULL,
    25,
    1,
    NULL,
    SYSUTCDATETIME(),
    N''
),
(
    'MS-01',
    N'Chuột không dây',
    599000.0000,
    0.095,
    40,
    1,
    '2026-01-15',
    SYSUTCDATETIME(),
    NULL
);
GO

SELECT
    ProductId,
    Name,
    Price,
    WeightKg,
    ReleasedAt,
    Description
FROM dbo.Products
WHERE WeightKg IS NULL
   OR ReleasedAt IS NULL;
GO

SELECT
    Name,
    COALESCE(Description, N'(chưa có mô tả)') AS DisplayDescription
FROM dbo.Products
ORDER BY ProductId;
GO
```

## 4. Giải thích cơ chế

### Integer

Dùng range phù hợp:

```text
tinyint
smallint
int
bigint
```

Đừng mặc định `bigint` cho mọi thứ.

### Decimal

Tiền nên dùng:

```sql
decimal(19,4)
```

Không dùng `float` cho tiền vì floating point là approximate.

### varchar và nvarchar

`nvarchar` phù hợp text Unicode như tên tiếng Việt.

Identifier kỹ thuật chỉ ASCII có thể dùng `varchar`.

### Date/time

Ưu tiên:

- `date` nếu chỉ ngày;
- `datetime2` cho timestamp;
- `datetimeoffset` nếu cần lưu offset cụ thể.

### NULL

`NULL` nghĩa là:

```text
unknown / missing / not applicable
```

Ba-valued logic:

```text
TRUE
FALSE
UNKNOWN
```

## 5. Kiến thức nền

### So sánh NULL

Sai:

```sql
WHERE WeightKg = NULL
```

Đúng:

```sql
WHERE WeightKg IS NULL
```

### COALESCE

```sql
COALESCE(Description, N'(chưa có)')
```

trả expression đầu tiên không NULL.

### NULL và aggregate

Nhiều aggregate bỏ qua NULL.

Ví dụ `AVG(WeightKg)` chỉ tính row có weight.

Cần hiểu semantics trước khi diễn giải số liệu.

### rowversion

`rowversion` là binary token tự tăng trong database, không phải timestamp ngày giờ.

Sau này EF Core có thể dùng nó cho optimistic concurrency.

## 6. Lỗi thường gặp

### Dùng float cho tiền

Có thể xuất hiện sai số biểu diễn.

### Dùng datetime cũ theo thói quen

`datetime2` có range/precision tốt hơn cho ứng dụng mới.

### Dùng NULL thay cho mọi trạng thái

Ví dụ Order.Status không nên nullable chỉ để “chưa xác định”.

Nếu business có trạng thái, hãy mô hình trạng thái rõ.

### Chuỗi rỗng và NULL lẫn lộn

```text
NULL = không có giá trị
''   = có chuỗi nhưng length 0
```

## 7. Bài tập

### Bài 1

Chọn type cho:

- quantity;
- money;
- email;
- birthday;
- uploaded file bytes.

### Bài 2

Tạo table Payment có:

- Amount;
- PaidAt nullable;
- ProviderReference nullable.

### Bài 3

Viết query tìm product chưa có ReleasedAt.

### Bài 4

Thử:

```sql
SELECT 1 WHERE NULL = NULL;
```

và giải thích vì sao không có row.

### Bài 5

So sánh storage/semantics giữa `nvarchar(100)` và `nvarchar(max)`.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi chọn type theo domain.
- [ ] Tôi không dùng float cho tiền.
- [ ] Tôi phân biệt varchar/nvarchar.
- [ ] Tôi hiểu NULL dùng three-valued logic.
- [ ] Tôi dùng IS NULL đúng.
- [ ] Tôi phân biệt NULL và empty string.

Điều hướng:

- Bài trước: [Thiết kế schema, table, key và constraint](./02-thiet-ke-schema-table-key-constraint.md)
- Bài tiếp theo: [CRUD: SELECT, INSERT, UPDATE, DELETE](./04-crud-select-insert-update-delete.md)
