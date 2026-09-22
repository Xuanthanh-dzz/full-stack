# Index B-tree, clustered và nonclustered

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích index giúp giảm lượng dữ liệu phải đọc;
- hiểu B-tree/B+tree ở mức thực hành;
- phân biệt heap, clustered index và nonclustered index;
- tạo index cho predicate phổ biến;
- đọc seek vs scan ở mức cơ bản;
- hiểu index tăng chi phí write/storage;
- tránh index mọi column.

## 2. Bài toán mở đầu

Table Orders có 10 triệu row.

Query thường xuyên:

```sql
WHERE CustomerId = @CustomerId
ORDER BY OrderedAt DESC
```

Không có index phù hợp, SQL Server có thể phải scan lượng dữ liệu lớn.

Index tạo cấu trúc được sắp xếp để tìm vùng cần đọc nhanh hơn.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_17') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_17
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_17;
END;
GO

CREATE DATABASE CommerceLab08_17;
GO
USE CommerceLab08_17;
GO

CREATE TABLE dbo.Orders
(
    OrderId bigint IDENTITY(1,1) NOT NULL,
    CustomerId int NOT NULL,
    OrderedAt datetime2(0) NOT NULL,
    Status varchar(20) NOT NULL,
    TotalAmount decimal(19,4) NOT NULL,
    CONSTRAINT PK_Orders
        PRIMARY KEY CLUSTERED (OrderId)
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
(CustomerId, OrderedAt, Status, TotalAmount)
SELECT
    ((rn - 1) % 100) + 1,
    DATEADD(minute, rn, CAST('2026-01-01' AS datetime2)),
    CASE WHEN rn % 3 = 0 THEN 'Paid' ELSE 'Pending' END,
    CAST(100000 + (rn % 5000000) AS decimal(19,4))
FROM n;
GO

CREATE NONCLUSTERED INDEX IX_Orders_CustomerId_OrderedAt
ON dbo.Orders
(
    CustomerId,
    OrderedAt DESC
);
GO

SET STATISTICS IO ON;

SELECT TOP (20)
    OrderId,
    CustomerId,
    OrderedAt,
    Status,
    TotalAmount
FROM dbo.Orders
WHERE CustomerId = 42
ORDER BY OrderedAt DESC;

SET STATISTICS IO OFF;
GO
```

## 4. Giải thích cơ chế

### B-tree trực giác

Index có root, intermediate pages và leaf pages.

Thay vì scan toàn bộ row, engine đi theo key range.

### Clustered index

Leaf level chứa data row của table theo clustered key structure.

Một table chỉ có một clustered index.

### Nonclustered index

Có key riêng và locator về row gốc.

Một table có thể có nhiều nonclustered index.

### Seek và scan

Seek dùng key để tới range cần.

Scan đọc toàn bộ hoặc phần lớn structure.

Scan không luôn xấu.

## 5. Kiến thức nền

### Index key order

Index `(CustomerId, OrderedAt)` khác `(OrderedAt, CustomerId)`.

### Write amplification

INSERT/UPDATE/DELETE phải duy trì mọi index liên quan.

### Clustered key

Key nhỏ, ổn định và tăng dần thường dễ quản lý, nhưng workload mới quyết định.

## 6. Lỗi thường gặp

### Index mọi column

Write cost và maintenance tăng mạnh.

### Nghĩ seek luôn nhanh hơn scan

Nếu trả phần lớn table, scan có thể đúng.

### Clustered key quá rộng

Làm nonclustered index lớn hơn.

### Không đo logical reads

Elapsed time một lần chạy dễ nhiễu.

## 7. Bài tập

### Bài 1

Tạo query theo Status và xem plan trước/sau index.

### Bài 2

Đổi order key trong composite index và so query.

### Bài 3

Tạo heap table và clustered table để so concept.

### Bài 4

Dùng STATISTICS IO ghi logical reads.

### Bài 5

Liệt kê index ứng viên rồi chọn theo workload.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi hiểu index giảm search space.
- [ ] Tôi phân biệt clustered/nonclustered.
- [ ] Tôi biết key order quan trọng.
- [ ] Tôi hiểu seek/scan không phải tốt/xấu tuyệt đối.
- [ ] Tôi biết index làm write đắt hơn.
- [ ] Tôi đo logical reads thay vì đoán.

Điều hướng:

- Bài trước: [Denormalization và dữ liệu lịch sử](./16-denormalization-va-du-lieu-lich-su.md)
- Bài tiếp theo: [Covering, filtered và composite index](./18-covering-filtered-composite-index.md)
