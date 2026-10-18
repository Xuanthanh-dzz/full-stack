# View, stored procedure, function và trigger

## 1. Mục tiêu

Sau bài này, bạn có thể:

- tạo view cho query ổn định;
- tạo stored procedure có parameter;
- tạo inline table-valued function;
- hiểu trigger chạy tự động theo DML;
- phân biệt abstraction với business logic;
- nhận ra rủi ro khi nhét quá nhiều logic vào database;
- chọn object phù hợp theo use case.

## 2. Bài toán mở đầu

Hệ thống cần:

- view danh sách active product;
- procedure tìm order theo customer;
- function trả order của một customer;
- audit khi price thay đổi.

SQL Server có nhiều programmable object, nhưng dùng sai sẽ làm architecture khó debug.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_13') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_13
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_13;
END;
GO

CREATE DATABASE CommerceLab08_13;
GO
USE CommerceLab08_13;
GO

CREATE TABLE dbo.Products
(
    ProductId int NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Name nvarchar(100) NOT NULL,
    Price decimal(19,4) NOT NULL,
    IsActive bit NOT NULL
);

CREATE TABLE dbo.PriceAudit
(
    AuditId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_PriceAudit PRIMARY KEY,
    ProductId int NOT NULL,
    OldPrice decimal(19,4) NOT NULL,
    NewPrice decimal(19,4) NOT NULL,
    ChangedAt datetime2(0) NOT NULL
        CONSTRAINT DF_PriceAudit_ChangedAt DEFAULT SYSUTCDATETIME()
);

CREATE TABLE dbo.Orders
(
    OrderId int NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    TotalAmount decimal(19,4) NOT NULL
);
GO

INSERT INTO dbo.Products VALUES
(1,N'Keyboard',1000000,1),
(2,N'Mouse',500000,0);

INSERT INTO dbo.Orders VALUES
(101,1,3000000),
(102,1,1000000),
(201,2,9000000);
GO

CREATE VIEW dbo.vActiveProducts
AS
    SELECT ProductId, Name, Price
    FROM dbo.Products
    WHERE IsActive = 1;
GO

CREATE PROCEDURE dbo.GetOrdersByCustomer
    @CustomerId int
AS
BEGIN
    SET NOCOUNT ON;

    SELECT OrderId, CustomerId, TotalAmount
    FROM dbo.Orders
    WHERE CustomerId = @CustomerId
    ORDER BY OrderId;
END;
GO

CREATE FUNCTION dbo.OrdersForCustomer
(
    @CustomerId int
)
RETURNS TABLE
AS
RETURN
(
    SELECT OrderId, CustomerId, TotalAmount
    FROM dbo.Orders
    WHERE CustomerId = @CustomerId
);
GO

CREATE TRIGGER dbo.trg_Products_PriceAudit
ON dbo.Products
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.PriceAudit
    (
        ProductId,
        OldPrice,
        NewPrice
    )
    SELECT
        i.ProductId,
        d.Price,
        i.Price
    FROM inserted AS i
    INNER JOIN deleted AS d
        ON d.ProductId = i.ProductId
    WHERE i.Price <> d.Price;
END;
GO

SELECT * FROM dbo.vActiveProducts;

EXEC dbo.GetOrdersByCustomer @CustomerId = 1;

SELECT *
FROM dbo.OrdersForCustomer(1);

UPDATE dbo.Products
SET Price = 1100000
WHERE ProductId = 1;

SELECT *
FROM dbo.PriceAudit;
GO
```

## 4. Giải thích cơ chế

### View

View lưu query definition.

Nó không mặc định lưu copy data.

### Stored procedure

Procedure là entry point database có parameter và nhiều statement.

### Inline table-valued function

Trả rowset và có thể compose trong query.

### Trigger

Trigger chạy tự động khi event xảy ra.

DML trigger phải xử lý **set nhiều row**, không giả định một row.

`inserted` và `deleted` có thể chứa nhiều row.

## 5. Kiến thức nền

### Logic nằm đâu?

Cân nhắc:

- ownership;
- testability;
- deployment;
- performance;
- nhiều application dùng chung DB;
- security.

### Trigger cho audit

Trigger bảo vệ audit ngay cả khi nhiều writer.

Nhưng trigger ẩn side effect khỏi application, nên phải document rõ.

### View và security

Có thể grant SELECT trên view thay vì table, giảm exposure column.

## 6. Lỗi thường gặp

### Trigger viết cho một row

Nếu UPDATE nhiều row, `inserted` chứa nhiều row.

### Procedure trả SELECT *

Contract dễ vỡ khi schema đổi.

### Scalar UDF trong hot query

Có thể gây overhead tùy version/plan; cần đo.

### Nhét toàn bộ domain logic vào stored procedure

Dễ làm application architecture khó test/maintain nếu team không chủ đích.

## 7. Bài tập

### Bài 1

Tạo view order summary.

### Bài 2

Tạo procedure search product theo min/max price.

### Bài 3

Tạo inline TVF trả paid order.

### Bài 4

UPDATE nhiều product cùng lúc và chứng minh trigger audit đúng nhiều row.

### Bài 5

Viết ADR ngắn: logic nào nên ở application, logic nào ở DB cho project của bạn.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi tạo được view.
- [ ] Tôi tạo được stored procedure.
- [ ] Tôi hiểu inline TVF.
- [ ] Tôi viết trigger set-based.
- [ ] Tôi hiểu trigger tạo side effect ẩn.
- [ ] Tôi chọn programmable object theo trade-off.

Điều hướng:

- Bài trước: [Window function](./12-window-function.md)
- Bài tiếp theo: [Mô hình ER và quan hệ](./14-mo-hinh-er-va-quan-he.md)
