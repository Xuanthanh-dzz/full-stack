# Subquery và correlated subquery

## 1. Mục tiêu

Sau bài này, bạn có thể:

- viết scalar, table và predicate subquery;
- dùng EXISTS/NOT EXISTS;
- hiểu correlated subquery tham chiếu outer row;
- phân biệt IN và EXISTS theo intent;
- viết anti-semi join bằng NOT EXISTS;
- tránh `NOT IN` + NULL trap;
- biết optimizer có thể rewrite subquery thành join/operator khác.

## 2. Bài toán mở đầu

Cần tìm:

- customer có ít nhất một paid order;
- customer chưa từng order;
- product có giá cao hơn average;
- order mới nhất của mỗi customer.

Subquery cho phép một query dùng kết quả của query khác.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_09') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_09
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_09;
END;
GO

CREATE DATABASE CommerceLab08_09;
GO
USE CommerceLab08_09;
GO

CREATE TABLE dbo.Customers
(
    CustomerId int NOT NULL
        CONSTRAINT PK_Customers PRIMARY KEY,
    Name nvarchar(100) NOT NULL
);

CREATE TABLE dbo.Orders
(
    OrderId int NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    Status varchar(20) NOT NULL,
    TotalAmount decimal(19,4) NOT NULL,
    OrderedAt date NOT NULL,
    CONSTRAINT FK_Orders_Customers
        FOREIGN KEY (CustomerId)
        REFERENCES dbo.Customers(CustomerId)
);
GO

INSERT INTO dbo.Customers VALUES
(1,N'An'),(2,N'Bình'),(3,N'Chi');

INSERT INTO dbo.Orders VALUES
(101,1,'Paid',1000000,'2026-01-01'),
(102,1,'Pending',2000000,'2026-02-01'),
(103,2,'Paid',9000000,'2026-02-10');
GO

SELECT
    c.CustomerId,
    c.Name
FROM dbo.Customers AS c
WHERE EXISTS
(
    SELECT 1
    FROM dbo.Orders AS o
    WHERE o.CustomerId = c.CustomerId
      AND o.Status = 'Paid'
)
ORDER BY c.CustomerId;
GO

SELECT
    c.CustomerId,
    c.Name
FROM dbo.Customers AS c
WHERE NOT EXISTS
(
    SELECT 1
    FROM dbo.Orders AS o
    WHERE o.CustomerId = c.CustomerId
)
ORDER BY c.CustomerId;
GO

SELECT
    o.OrderId,
    o.CustomerId,
    o.TotalAmount
FROM dbo.Orders AS o
WHERE o.TotalAmount >
(
    SELECT AVG(o2.TotalAmount)
    FROM dbo.Orders AS o2
)
ORDER BY o.OrderId;
GO

SELECT
    c.CustomerId,
    c.Name,
    (
        SELECT MAX(o.OrderedAt)
        FROM dbo.Orders AS o
        WHERE o.CustomerId = c.CustomerId
    ) AS LastOrderDate
FROM dbo.Customers AS c
ORDER BY c.CustomerId;
GO
```

## 4. Giải thích cơ chế

### Scalar subquery

Phải trả tối đa một value:

```sql
SELECT AVG(TotalAmount)
FROM Orders
```

### EXISTS

EXISTS hỏi:

```text
có ít nhất một row thỏa không?
```

Nó phù hợp membership theo relation.

### Correlated subquery

Query con tham chiếu outer alias:

```sql
WHERE o.CustomerId = c.CustomerId
```

Về mặt logic, nó phụ thuộc row bên ngoài.

Optimizer có thể biến thành semi join hoặc plan hiệu quả hơn.

### NOT EXISTS

Rất phù hợp tìm “không có child”.

```text
customers with no orders
```

## 5. Kiến thức nền

### NOT IN và NULL

Nếu subquery của `NOT IN` chứa NULL, three-valued logic có thể làm kết quả bất ngờ.

`NOT EXISTS` thường rõ intent hơn cho anti-match.

### Derived table

Subquery trong FROM:

```sql
FROM
(
    SELECT CustomerId, SUM(TotalAmount) AS Revenue
    FROM Orders
    GROUP BY CustomerId
) AS x
```

tạo rowset tạm về mặt logic.

### Subquery hay JOIN?

Không có rule “JOIN luôn nhanh hơn”.

Viết intent rõ, sau đó xem execution plan.

## 6. Lỗi thường gặp

### Scalar subquery trả nhiều row

SQL Server báo lỗi nếu expression cần một value nhưng subquery trả nhiều hơn một.

### NOT IN với nullable column

Có thể trả zero row ngoài dự đoán.

### Correlated subquery tính aggregate nặng

Có thể cần rewrite hoặc index; đo plan thay vì đoán.

### Dùng SELECT * trong EXISTS

Không cần column cụ thể.

`SELECT 1` thể hiện intent rõ.

## 7. Bài tập

### Bài 1

Tìm customer có order trên 5 triệu.

### Bài 2

Tìm product chưa từng được bán bằng NOT EXISTS.

### Bài 3

Tìm order lớn hơn average của chính customer đó.

### Bài 4

Rewrite một EXISTS thành JOIN và so execution plan.

### Bài 5

Tạo demo `NOT IN` chứa NULL và giải thích kết quả.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi viết được scalar subquery.
- [ ] Tôi dùng EXISTS/NOT EXISTS.
- [ ] Tôi hiểu correlated subquery.
- [ ] Tôi biết NOT IN + NULL trap.
- [ ] Tôi không khẳng định JOIN luôn nhanh hơn.
- [ ] Tôi kiểm tra plan khi performance quan trọng.

Điều hướng:

- Bài trước: [JOIN](./08-inner-left-right-full-cross-join.md)
- Bài tiếp theo: [Set operator: UNION, INTERSECT, EXCEPT](./10-set-operator-union-intersect-except.md)
