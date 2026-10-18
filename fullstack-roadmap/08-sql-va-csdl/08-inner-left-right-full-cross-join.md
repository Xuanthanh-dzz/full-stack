# INNER, LEFT, RIGHT, FULL và CROSS JOIN

## 1. Mục tiêu

Sau bài này, bạn có thể:

- join table theo PK/FK;
- phân biệt INNER và OUTER JOIN;
- hiểu row preservation của LEFT/RIGHT/FULL;
- dùng CROSS JOIN có chủ đích;
- tránh accidental Cartesian product;
- biết predicate đặt ở ON hay WHERE có thể đổi semantics;
- đọc cardinality của join.

## 2. Bài toán mở đầu

Ta có:

```text
Customers
Orders
Products
OrderItems
```

Để hiển thị:

```text
OrderId
CustomerName
ProductName
Quantity
UnitPrice
```

cần nối nhiều table.

Join là kỹ năng SQL cốt lõi nhất cho backend.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_08') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_08
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_08;
END;
GO

CREATE DATABASE CommerceLab08_08;
GO
USE CommerceLab08_08;
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
    CustomerId int NOT NULL
        CONSTRAINT FK_Orders_Customers
        REFERENCES dbo.Customers(CustomerId),
    Status varchar(20) NOT NULL
);

CREATE TABLE dbo.Products
(
    ProductId int NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Name nvarchar(100) NOT NULL
);
GO

INSERT INTO dbo.Customers VALUES
(1,N'An'),(2,N'Bình'),(3,N'Chi');

INSERT INTO dbo.Orders VALUES
(101,1,'Paid'),
(102,1,'Pending'),
(103,2,'Paid');

INSERT INTO dbo.Products VALUES
(10,N'Keyboard'),(20,N'Mouse');
GO

SELECT
    o.OrderId,
    c.Name AS CustomerName,
    o.Status
FROM dbo.Orders AS o
INNER JOIN dbo.Customers AS c
    ON c.CustomerId = o.CustomerId
ORDER BY o.OrderId;
GO

SELECT
    c.CustomerId,
    c.Name,
    o.OrderId,
    o.Status
FROM dbo.Customers AS c
LEFT JOIN dbo.Orders AS o
    ON o.CustomerId = c.CustomerId
ORDER BY c.CustomerId, o.OrderId;
GO

SELECT
    c.Name,
    p.Name AS ProductName
FROM dbo.Customers AS c
CROSS JOIN dbo.Products AS p
ORDER BY c.CustomerId, p.ProductId;
GO
```

## 4. Giải thích cơ chế

### INNER JOIN

Chỉ giữ row có match hai bên.

```text
Customers ∩ Orders
```

### LEFT JOIN

Giữ toàn bộ row bên trái.

Nếu không match, column bên phải thành NULL.

Customer Chi vẫn xuất hiện dù chưa có order.

### RIGHT JOIN

Tương đương đổi vị trí table của LEFT JOIN trong nhiều trường hợp.

Team thường ưu tiên LEFT JOIN để query dễ đọc nhất quán.

### FULL OUTER JOIN

Giữ unmatched từ cả hai phía.

Hữu ích reconciliation nhưng ít dùng hơn trong CRUD thường ngày.

### CROSS JOIN

Tạo mọi combination:

```text
m customers × n products = m*n rows
```

Dùng cho:

- calendar grid;
- matrix;
- sinh combination có kiểm soát.

## 5. Kiến thức nền

### ON và WHERE

Với LEFT JOIN:

```sql
LEFT JOIN Orders o
  ON o.CustomerId = c.CustomerId
 AND o.Status = 'Paid'
```

khác:

```sql
LEFT JOIN Orders o
  ON o.CustomerId = c.CustomerId
WHERE o.Status = 'Paid'
```

Version WHERE loại row có `o.Status = NULL`, vô tình làm semantics giống INNER JOIN.

### Cardinality

One-to-many join làm row phía one lặp lại.

Một customer có 3 order -> 3 result rows.

Đây không phải duplicate lỗi.

### Join nhiều table

Thứ tự viết join không đồng nghĩa optimizer luôn thực thi đúng thứ tự đó.

Execution plan mới cho biết physical join order/operator.

## 6. Lỗi thường gặp

### Quên ON

Accidental Cartesian product có thể làm row count nổ.

### JOIN theo text thay vì key

Tên có thể trùng/thay đổi.

Join bằng key được thiết kế.

### LEFT JOIN rồi filter right table ở WHERE

Có thể mất unmatched row.

### DISTINCT để che join sai

Nếu duplicate đến từ join condition thiếu, `DISTINCT` chỉ che bug.

## 7. Bài tập

### Bài 1

Tìm customer chưa có order.

**Gợi ý:** LEFT JOIN + `WHERE o.OrderId IS NULL`.

### Bài 2

Tạo OrderItems và join Order -> Customer -> Item -> Product.

### Bài 3

Viết cùng logic bằng RIGHT JOIN rồi refactor thành LEFT JOIN.

### Bài 4

Tạo FULL OUTER JOIN giữa hai bảng SKU để reconciliation.

### Bài 5

Tạo CROSS JOIN 7 ngày × 3 ca làm việc.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt INNER/LEFT/RIGHT/FULL.
- [ ] Tôi hiểu CROSS JOIN.
- [ ] Tôi biết ON và WHERE có thể đổi outer-join semantics.
- [ ] Tôi reasoning được cardinality.
- [ ] Tôi không dùng DISTINCT để che join bug.
- [ ] Tôi join bằng key ổn định.

Điều hướng:

- Bài trước: [GROUP BY, aggregate và HAVING](./07-group-by-aggregate-va-having.md)
- Bài tiếp theo: [Subquery và correlated subquery](./09-subquery-va-correlated-subquery.md)
