# CRUD: SELECT, INSERT, UPDATE, DELETE

## 1. Mục tiêu

Sau bài này, bạn có thể:

- đọc dữ liệu bằng SELECT;
- insert một hoặc nhiều row;
- update có điều kiện;
- delete có điều kiện;
- dùng OUTPUT để quan sát row thay đổi;
- tránh UPDATE/DELETE toàn bảng ngoài ý muốn;
- hiểu CRUD SQL khác CRUD HTTP.

## 2. Bài toán mở đầu

Admin cần:

- thêm product;
- xem product;
- đổi price;
- ngừng bán product.

Đây là CRUD:

```text
Create
Read
Update
Delete
```

Nhưng trong hệ thống thương mại, “delete” đôi khi phải là soft delete hoặc state transition để giữ lịch sử.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_04') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_04
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_04;
END;
GO

CREATE DATABASE CommerceLab08_04;
GO
USE CommerceLab08_04;
GO

CREATE TABLE dbo.Products
(
    ProductId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Sku varchar(40) NOT NULL
        CONSTRAINT UQ_Products_Sku UNIQUE,
    Name nvarchar(160) NOT NULL,
    Price decimal(19,4) NOT NULL
        CONSTRAINT CK_Products_Price CHECK (Price >= 0),
    IsActive bit NOT NULL
        CONSTRAINT DF_Products_IsActive DEFAULT 1
);
GO

INSERT INTO dbo.Products (Sku, Name, Price)
OUTPUT inserted.ProductId, inserted.Sku
VALUES
    ('KB-01', N'Bàn phím', 750000),
    ('MS-01', N'Chuột', 450000),
    ('MN-01', N'Màn hình', 5200000);
GO

SELECT
    ProductId,
    Sku,
    Name,
    Price,
    IsActive
FROM dbo.Products
ORDER BY ProductId;
GO

UPDATE dbo.Products
SET Price = 790000
OUTPUT
    deleted.Price AS OldPrice,
    inserted.Price AS NewPrice
WHERE Sku = 'KB-01';
GO

UPDATE dbo.Products
SET IsActive = 0
WHERE Sku = 'MN-01';
GO

DELETE FROM dbo.Products
OUTPUT deleted.ProductId, deleted.Sku
WHERE Sku = 'MS-01';
GO

SELECT
    ProductId,
    Sku,
    Name,
    Price,
    IsActive
FROM dbo.Products
ORDER BY ProductId;
GO
```

## 4. Giải thích cơ chế

### INSERT

```sql
INSERT INTO dbo.Products (Sku, Name, Price)
VALUES (...);
```

Luôn liệt kê column.

Không dựa vào physical column order.

### SELECT

Chỉ chọn column cần:

```sql
SELECT ProductId, Name, Price
```

thay vì mặc định `SELECT *`.

### UPDATE

```sql
UPDATE ...
SET ...
WHERE ...
```

Không có `WHERE` thì mọi row có thể bị cập nhật.

### DELETE

```sql
DELETE FROM ...
WHERE ...
```

DELETE xóa row logic khỏi table và được transaction log ghi lại.

### OUTPUT

`inserted` và `deleted` pseudo table cho phép xem dữ liệu trước/sau.

Hữu ích khi:

- lấy identity;
- audit;
- debug;
- batch operation.

## 5. Kiến thức nền

### CRUD SQL và HTTP

SQL:

```text
INSERT SELECT UPDATE DELETE
```

HTTP:

```text
POST GET PUT/PATCH DELETE
```

Có tương đồng về intent nhưng không phải mapping bắt buộc một-một.

### Soft delete

Thay:

```sql
DELETE
```

bằng:

```sql
UPDATE ... SET IsDeleted = 1
```

chỉ khi business cần giữ row.

Soft delete mang thêm complexity:

- mọi query phải filter;
- unique constraint khó hơn;
- storage tăng.

### Idempotency

UPDATE cùng giá trị thường có semantics khác INSERT duplicate.

Module Web sẽ mở rộng khái niệm idempotency ở API.

## 6. Lỗi thường gặp

### UPDATE/DELETE không có WHERE

Trước khi chạy destructive query:

```sql
SELECT ...
WHERE ...
```

để xác nhận tập row.

### SELECT *

Dễ kéo column không cần và làm contract phụ thuộc schema.

### Hard delete dữ liệu lịch sử

Order/payment thường cần giữ để audit.

### Nhiều statement nhưng không transaction

Nếu nghiệp vụ cần all-or-nothing, CRUD riêng lẻ chưa đủ.

Transaction sẽ học ở bài 19.

## 7. Bài tập

### Bài 1

Insert 5 product bằng một statement.

### Bài 2

Tăng giá 5% cho category giả định.

### Bài 3

Dùng OUTPUT để ghi old/new price vào table variable.

### Bài 4

Thiết kế soft delete cho Product.

### Bài 5

Viết checklist an toàn trước khi chạy DELETE production.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi dùng được SELECT/INSERT/UPDATE/DELETE.
- [ ] Tôi liệt kê column khi INSERT.
- [ ] Tôi tránh SELECT *.
- [ ] Tôi kiểm tra WHERE trước destructive query.
- [ ] Tôi dùng được OUTPUT.
- [ ] Tôi hiểu hard delete và soft delete khác nhau.

Điều hướng:

- Bài trước: [Kiểu dữ liệu và NULL](./03-kieu-du-lieu-va-null.md)
- Bài tiếp theo: [Filter, sort và pagination](./05-filter-sort-va-pagination.md)
