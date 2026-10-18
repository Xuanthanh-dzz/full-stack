# Execution plan và statistics

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt estimated và actual execution plan;
- đọc operator cơ bản như Scan, Seek, Sort, Hash Match, Nested Loops;
- hiểu cardinality estimate;
- hiểu statistics hỗ trợ optimizer;
- dùng SET STATISTICS IO/TIME;
- phát hiện estimate sai;
- tránh tối ưu chỉ dựa trên cost percentage.

## 2. Bài toán mở đầu

Một query chạy chậm:

```sql
SELECT OrderId, CustomerId, OrderedAt, TotalAmount
FROM Orders
WHERE CustomerId = 42
  AND Status = 'Paid';
```

Cần trả lời:

- optimizer chọn plan gì?
- đọc bao nhiêu page?
- estimate bao nhiêu row?
- actual bao nhiêu row?
- operator nào xử lý volume lớn?

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_21') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_21
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_21;
END;
GO

CREATE DATABASE CommerceLab08_21;
GO
USE CommerceLab08_21;
GO

CREATE TABLE dbo.Orders
(
    OrderId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    Status varchar(20) NOT NULL,
    OrderedAt datetime2(0) NOT NULL,
    TotalAmount decimal(19,4) NOT NULL
);
GO

;WITH n AS
(
    SELECT TOP (20000)
        ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS rn
    FROM sys.all_objects AS a
    CROSS JOIN sys.all_objects AS b
)
INSERT INTO dbo.Orders
(CustomerId, Status, OrderedAt, TotalAmount)
SELECT
    CASE
        WHEN rn <= 12000 THEN 1
        ELSE ((rn - 1) % 200) + 2
    END,
    CASE WHEN rn % 4 = 0 THEN 'Paid' ELSE 'Pending' END,
    DATEADD(minute, rn, CAST('2026-01-01' AS datetime2)),
    CAST(100000 + rn AS decimal(19,4))
FROM n;
GO

CREATE NONCLUSTERED INDEX IX_Orders_Customer_Status
ON dbo.Orders(CustomerId, Status)
INCLUDE(OrderedAt, TotalAmount);
GO

UPDATE STATISTICS dbo.Orders WITH FULLSCAN;
GO

SET STATISTICS IO ON;
SET STATISTICS TIME ON;

SELECT
    OrderId,
    CustomerId,
    OrderedAt,
    TotalAmount
FROM dbo.Orders
WHERE CustomerId = 42
  AND Status = 'Paid';

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;
GO

SELECT
    s.name AS StatisticName,
    STATS_DATE(s.object_id, s.stats_id) AS LastUpdated
FROM sys.stats AS s
WHERE s.object_id = OBJECT_ID(N'dbo.Orders')
ORDER BY s.name;
GO
```

Để xem plan, bật **Actual Execution Plan** trong công cụ SQL rồi chạy query.

## 4. Giải thích cơ chế

### Query optimizer

Optimizer cân nhắc nhiều phương án như scan, seek, nested loops, hash join, sort và parallelism.

### Statistics

Statistics tóm tắt phân bố dữ liệu để optimizer ước lượng số row.

### Estimated vs actual

Estimated plan chỉ có ước lượng.

Actual plan bổ sung số row runtime và metrics thực tế.

### STATISTICS IO

Logical reads cho biết số page đọc từ buffer cache.

## 5. Kiến thức nền

### Cardinality estimate

Estimate sai lớn có thể làm chọn join, memory grant hoặc access path kém.

### Nested Loops

Phù hợp khi outer input nhỏ và inner lookup rẻ.

### Hash Match

Thường phù hợp volume lớn nhưng có memory cost.

### Sort

Có thể spill ra tempdb nếu memory grant thiếu.

## 6. Lỗi thường gặp

### Chỉ nhìn phần trăm cost

Đó là estimate tương đối trong plan, không phải profiler toàn hệ thống.

### Thấy scan là đổi thành seek bằng mọi giá

Scan có thể đúng nếu query lấy phần lớn table.

### Update statistics vô tội vạ

Không sửa được schema/query sai.

### Không so actual và estimated rows

Bỏ lỡ tín hiệu quan trọng.

## 7. Bài tập

### Bài 1

Bỏ index và ghi logical reads trước/sau.

### Bài 2

So CustomerId=1 với CustomerId=42.

### Bài 3

Xem estimated/actual row.

### Bài 4

Tạo join và xác định physical join operator.

### Bài 5

Viết checklist khi nhận ticket “query chậm”.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt estimated và actual plan.
- [ ] Tôi nhận ra Scan/Seek/Sort/Join operator cơ bản.
- [ ] Tôi hiểu statistics và cardinality estimate.
- [ ] Tôi dùng STATISTICS IO/TIME.
- [ ] Tôi so estimated với actual rows.
- [ ] Tôi không tối ưu chỉ theo cost percentage.

Điều hướng:

- Bài trước: [Isolation level, MVCC, lock và deadlock](./20-isolation-level-mvcc-lock-deadlock.md)
- Bài tiếp theo: [Tối ưu truy vấn và SARGability](./22-toi-uu-truy-van-va-sargability.md)
