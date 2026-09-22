# GROUP BY, aggregate và HAVING

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng COUNT, SUM, AVG, MIN, MAX;
- nhóm dữ liệu bằng GROUP BY;
- phân biệt WHERE và HAVING;
- xử lý NULL trong aggregate;
- tính doanh thu theo customer/status;
- tránh select column không thuộc group;
- hiểu grain của kết quả aggregate.

## 2. Bài toán mở đầu

Business hỏi:

- có bao nhiêu order mỗi customer?
- tổng doanh thu theo tháng?
- customer nào chi trên 10 triệu?
- average order value là bao nhiêu?

Đây không còn là query từng row riêng lẻ; cần biến nhiều row thành summary.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_07') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_07
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_07;
END;
GO

CREATE DATABASE CommerceLab08_07;
GO
USE CommerceLab08_07;
GO

CREATE TABLE dbo.Orders
(
    OrderId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    Status varchar(20) NOT NULL,
    TotalAmount decimal(19,4) NULL,
    OrderedAt date NOT NULL
);
GO

INSERT INTO dbo.Orders
(CustomerId, Status, TotalAmount, OrderedAt)
VALUES
(1, 'Paid',      3000000, '2026-01-05'),
(1, 'Paid',      4500000, '2026-01-20'),
(1, 'Cancelled', NULL,    '2026-02-01'),
(2, 'Paid',      12000000,'2026-01-10'),
(2, 'Pending',   2000000, '2026-02-03'),
(3, 'Paid',      900000,  '2026-02-15');
GO

SELECT
    CustomerId,
    COUNT(*) AS OrderCount,
    COUNT(TotalAmount) AS OrdersWithAmount,
    SUM(COALESCE(TotalAmount, 0)) AS TotalAmount,
    AVG(TotalAmount) AS AverageAmount,
    MIN(TotalAmount) AS MinAmount,
    MAX(TotalAmount) AS MaxAmount
FROM dbo.Orders
GROUP BY CustomerId
ORDER BY CustomerId;
GO

SELECT
    CustomerId,
    SUM(TotalAmount) AS PaidRevenue
FROM dbo.Orders
WHERE Status = 'Paid'
GROUP BY CustomerId
HAVING SUM(TotalAmount) >= 5000000
ORDER BY PaidRevenue DESC;
GO

SELECT
    YEAR(OrderedAt) AS OrderYear,
    MONTH(OrderedAt) AS OrderMonth,
    COUNT(*) AS OrderCount,
    SUM(COALESCE(TotalAmount, 0)) AS Revenue
FROM dbo.Orders
GROUP BY
    YEAR(OrderedAt),
    MONTH(OrderedAt)
ORDER BY OrderYear, OrderMonth;
GO
```

## 4. Giải thích cơ chế

### Grain

Query:

```sql
GROUP BY CustomerId
```

trả một row trên mỗi customer.

Grain thay từ:

```text
1 row = 1 order
```

thành:

```text
1 row = 1 customer summary
```

### COUNT(*) và COUNT(column)

`COUNT(*)` đếm row.

`COUNT(TotalAmount)` bỏ row có TotalAmount NULL.

### WHERE và HAVING

`WHERE` lọc row **trước group**.

`HAVING` lọc group **sau aggregate**.

Ví dụ:

```sql
WHERE Status = 'Paid'
...
HAVING SUM(TotalAmount) >= 5000000
```

## 5. Kiến thức nền

### Logical query processing

Mô hình đơn giản:

```text
FROM
WHERE
GROUP BY
HAVING
SELECT
ORDER BY
```

Không phải implementation vật lý chính xác, nhưng rất hữu ích để reasoning.

### Aggregate và NULL

`SUM`, `AVG`, `MIN`, `MAX` thường bỏ NULL.

Do đó NULL semantics phải được quyết định rõ.

### Conditional aggregate

Có thể dùng:

```sql
SUM(CASE WHEN Status = 'Paid' THEN TotalAmount ELSE 0 END)
```

để tính nhiều metric trong cùng group.

## 6. Lỗi thường gặp

### SELECT column không group/aggregate

Nếu grain là customer, không thể tùy tiện select OrderId.

### Dùng HAVING thay WHERE

Nếu predicate có thể lọc row trước group, dùng WHERE thường tốt hơn.

### AVG trên integer

Cần hiểu data type của expression để tránh mất phần thập phân.

### COUNT(column) nhưng tưởng là COUNT(*)

NULL làm kết quả khác.

## 7. Bài tập

### Bài 1

Tính order count theo Status.

### Bài 2

Tính paid revenue theo tháng.

### Bài 3

Tìm customer có ít nhất 2 paid order.

### Bài 4

Tính tỷ lệ cancelled bằng conditional aggregate.

### Bài 5

Giải thích grain của ba query bạn vừa viết.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi dùng được COUNT/SUM/AVG/MIN/MAX.
- [ ] Tôi xác định được grain.
- [ ] Tôi phân biệt WHERE và HAVING.
- [ ] Tôi hiểu aggregate bỏ NULL ra sao.
- [ ] Tôi viết conditional aggregate.
- [ ] Tôi không select column phá grain.

Điều hướng:

- Bài trước: [Hàm scalar, CASE và xử lý NULL](./06-ham-scalar-case-va-xu-ly-null.md)
- Bài tiếp theo: [INNER, LEFT, RIGHT, FULL và CROSS JOIN](./08-inner-left-right-full-cross-join.md)
