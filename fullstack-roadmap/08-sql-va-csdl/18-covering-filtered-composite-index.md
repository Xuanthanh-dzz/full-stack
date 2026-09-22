# Covering, filtered và composite index

## 1. Mục tiêu

Sau bài này, bạn có thể:

- thiết kế composite index theo predicate và sort;
- dùng INCLUDE để cover query;
- tạo filtered index;
- phân biệt key column và included column;
- tránh index quá rộng;
- hiểu left-prefix behavior;
- kiểm chứng thiết kế bằng execution plan và logical reads.

## 2. Bài toán mở đầu

Dashboard chạy liên tục:

```sql
SELECT TOP 50
    OrderId,
    OrderedAt,
    TotalAmount
FROM Orders
WHERE CustomerId = @id
  AND Status = 'Paid'
ORDER BY OrderedAt DESC;
```

Một index chỉ có `CustomerId` có thể vẫn phải lookup thêm dữ liệu từ row gốc.

Ta cần thiết kế theo **toàn access pattern**, không chỉ một predicate.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_18') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_18
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_18;
END;
GO

CREATE DATABASE CommerceLab08_18;
GO
USE CommerceLab08_18;
GO

CREATE TABLE dbo.Orders
(
    OrderId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    Status varchar(20) NOT NULL,
    OrderedAt datetime2(0) NOT NULL,
    TotalAmount decimal(19,4) NOT NULL,
    ShippingCity nvarchar(100) NULL
);
GO

;WITH n AS
(
    SELECT TOP (10000)
        ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS rn
    FROM sys.all_objects AS a
    CROSS JOIN sys.all_objects AS b
)
INSERT INTO dbo.Orders
(
    CustomerId,
    Status,
    OrderedAt,
    TotalAmount,
    ShippingCity
)
SELECT
    ((rn - 1) % 200) + 1,
    CASE
        WHEN rn % 5 = 0 THEN 'Cancelled'
        WHEN rn % 2 = 0 THEN 'Paid'
        ELSE 'Pending'
    END,
    DATEADD(minute, rn, CAST('2026-01-01' AS datetime2)),
    CAST(100000 + rn AS decimal(19,4)),
    CASE WHEN rn % 2 = 0 THEN N'Hà Nội' ELSE N'TP.HCM' END
FROM n;
GO

CREATE NONCLUSTERED INDEX IX_Orders_Customer_Status_OrderedAt
ON dbo.Orders
(
    CustomerId,
    Status,
    OrderedAt DESC
)
INCLUDE
(
    TotalAmount
);
GO

SET ANSI_NULLS ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET QUOTED_IDENTIFIER ON;
SET NUMERIC_ROUNDABORT OFF;
GO

CREATE NONCLUSTERED INDEX IX_Orders_Paid_OrderedAt
ON dbo.Orders
(
    OrderedAt DESC
)
INCLUDE
(
    CustomerId,
    TotalAmount
)
WHERE Status = 'Paid';
GO

SET STATISTICS IO ON;

SELECT TOP (50)
    OrderId,
    OrderedAt,
    TotalAmount
FROM dbo.Orders
WHERE CustomerId = 42
  AND Status = 'Paid'
ORDER BY OrderedAt DESC;

SET STATISTICS IO OFF;
GO
```

## 4. Giải thích cơ chế

### Composite key

Key:

```text
CustomerId, Status, OrderedAt
```

phù hợp với equality trên `CustomerId`, `Status` rồi sort/range theo `OrderedAt`.

### INCLUDE

Included column nằm ở leaf để query lấy dữ liệu mà không nhất thiết phải lookup row gốc.

Nó không tham gia thứ tự search key giống key column.

### Covering index

Một query được cover khi index chứa đủ dữ liệu cho predicate, ordering và output theo execution plan cụ thể.

Covering là thuộc tính của **query + index**, không phải nhãn cố định của index.

### Filtered index

```sql
WHERE Status = 'Paid'
```

index chỉ chứa subset cần thiết.

Hữu ích khi subset nhỏ và query thường xuyên dùng đúng predicate đó.

## 5. Kiến thức nền

### Left prefix

Composite index `(A,B,C)` thường hữu ích nhất khi predicate bắt đầu từ `A`.

Query chỉ filter `B` có thể không tận dụng seek như mong đợi.

### Equality trước range

Heuristic thường gặp:

```text
equality columns
-> range/order column
```

nhưng luôn phải kiểm chứng bằng workload.

### Index width

INCLUDE quá nhiều column làm tăng:

- disk;
- buffer cache pressure;
- write cost;
- maintenance.

## 6. Lỗi thường gặp

### INCLUDE mọi column để “cover tất cả”

Biến index thành gần như copy table.

### Filtered index không khớp predicate

Optimizer có thể không dùng nếu semantics query không tương thích.

### Thứ tự composite theo SELECT list

Index key nên theo access pattern, không theo thứ tự column trong SELECT.

### Chỉ làm theo missing-index hint

Hint là gợi ý, không phải thiết kế hoàn chỉnh.

## 7. Bài tập

### Bài 1

Thiết kế index cho `WHERE Email = @email`.

### Bài 2

Thiết kế index cho `WHERE CustomerId=@id AND OrderedAt>=@from ORDER BY OrderedAt`.

### Bài 3

Tạo filtered index cho active product.

### Bài 4

Bỏ INCLUDE rồi so logical reads và key lookup.

### Bài 5

Review 5 index trùng prefix và đề xuất consolidate.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi thiết kế composite key theo predicate.
- [ ] Tôi phân biệt key và INCLUDE.
- [ ] Tôi hiểu covering là theo query.
- [ ] Tôi dùng filtered index có mục tiêu.
- [ ] Tôi tránh index quá rộng.
- [ ] Tôi kiểm chứng bằng plan và IO.

Điều hướng:

- Bài trước: [Index B-tree, clustered và nonclustered](./17-index-btree-clustered-nonclustered.md)
- Bài tiếp theo: [Transaction và ACID](./19-transaction-va-acid.md)
