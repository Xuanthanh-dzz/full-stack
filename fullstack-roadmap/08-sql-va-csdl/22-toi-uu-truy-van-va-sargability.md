# Tối ưu truy vấn và SARGability

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích SARGable predicate;
- rewrite function-on-column predicate;
- tránh implicit conversion;
- tránh kéo dữ liệu thừa;
- nhận ra leading wildcard;
- tối ưu pagination/query shape;
- đo trước và sau thay đổi;
- phân biệt tuning query với tuning schema.

## 2. Bài toán mở đầu

Query:

```sql
WHERE YEAR(OrderedAt) = 2026
```

rõ nghĩa nhưng function áp lên indexed column có thể làm engine khó seek theo range.

Rewrite:

```sql
WHERE OrderedAt >= '2026-01-01'
  AND OrderedAt <  '2027-01-01'
```

giữ column searchable.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_22') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_22
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_22;
END;
GO

CREATE DATABASE CommerceLab08_22;
GO
USE CommerceLab08_22;
GO

CREATE TABLE dbo.Orders
(
    OrderId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    OrderedAt datetime2(0) NOT NULL,
    ExternalCode varchar(30) NOT NULL,
    TotalAmount decimal(19,4) NOT NULL
);
GO

;WITH n AS
(
    SELECT TOP (30000)
        ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS rn
    FROM sys.all_objects AS a
    CROSS JOIN sys.all_objects AS b
)
INSERT INTO dbo.Orders
(CustomerId, OrderedAt, ExternalCode, TotalAmount)
SELECT
    ((rn - 1) % 500) + 1,
    DATEADD(hour, rn, CAST('2024-01-01' AS datetime2)),
    CONCAT('ORD-', RIGHT(CONCAT('000000', rn), 6)),
    CAST(100000 + rn AS decimal(19,4))
FROM n;
GO

CREATE INDEX IX_Orders_OrderedAt
ON dbo.Orders(OrderedAt)
INCLUDE(CustomerId, TotalAmount);

CREATE UNIQUE INDEX UX_Orders_ExternalCode
ON dbo.Orders(ExternalCode);
GO

SET STATISTICS IO ON;

SELECT COUNT_BIG(*)
FROM dbo.Orders
WHERE YEAR(OrderedAt) = 2026;

SELECT COUNT_BIG(*)
FROM dbo.Orders
WHERE OrderedAt >= '2026-01-01'
  AND OrderedAt < '2027-01-01';

SELECT OrderId, ExternalCode
FROM dbo.Orders
WHERE ExternalCode = 'ORD-000500';

SET STATISTICS IO OFF;
GO
```

## 4. Giải thích cơ chế

### SARGable

Search ARGument able: predicate có thể tận dụng cấu trúc index để xác định key/range hiệu quả.

### Function on column

Nếu filter expression thường xuyên, có thể cân nhắc computed column/index nhưng phải dựa trên workload.

### Implicit conversion

Parameter type lệch schema có thể tạo conversion và plan xấu.

### Query shape

Tối ưu thường bắt đầu bằng lấy ít row/column hơn, filter sớm và index đúng.

## 5. Kiến thức nền

### Leading wildcard

```sql
LIKE '%abc%'
```

khó dùng B-tree prefix seek.

Có thể cần full-text index hoặc search engine.

### Parameterization

Không concatenate SQL string từ input.

Parameterization vừa bảo mật vừa hỗ trợ plan reuse trong nhiều trường hợp.

### Pagination

Page sâu bằng OFFSET có thể đắt; keyset pagination phù hợp nhiều feed/infinite-scroll.

## 6. Lỗi thường gặp

### Tối ưu bằng hint trước khi hiểu plan

Hint có thể khóa plan kém khi data đổi.

### SELECT *

Kéo network/storage/cache nhiều hơn cần.

### CAST/CONVERT column trong WHERE

Có thể làm predicate không SARGable.

### Chỉ đo milliseconds

Cần xem IO, CPU, row count và concurrency.

## 7. Bài tập

### Bài 1

Rewrite `CAST(OrderedAt AS date) = @date`.

### Bài 2

Tạo implicit conversion giữa varchar và nvarchar rồi xem plan.

### Bài 3

So offset page 1000 với keyset pagination.

### Bài 4

Thu hẹp projection của ba query SELECT *.

### Bài 5

Lập bảng before/after: reads, CPU, elapsed, rows.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi giải thích được SARGability.
- [ ] Tôi rewrite function-on-column predicate.
- [ ] Tôi tránh implicit conversion.
- [ ] Tôi thu hẹp row/column.
- [ ] Tôi hiểu leading wildcard.
- [ ] Tôi đo before/after.

Điều hướng:

- Bài trước: [Execution plan và statistics](./21-execution-plan-va-statistics.md)
- Bài tiếp theo: [Bảo mật, phân quyền và SQL injection](./23-bao-mat-phan-quyen-va-sql-injection.md)
