# Chuẩn hóa 1NF, 2NF, 3NF và BCNF

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích functional dependency;
- nhận ra repeating group và update anomaly;
- hiểu trực giác 1NF, 2NF, 3NF và BCNF;
- tách schema theo dependency;
- biết chuẩn hóa không đồng nghĩa tách table tối đa;
- phân biệt duplication lỗi với historical snapshot có chủ đích.

## 2. Bài toán mở đầu

Một table xấu:

```text
OrderId
CustomerEmail
CustomerName
Product1
Product2
Product3
CategoryName
CategoryManager
```

Vấn đề:

- giới hạn số product;
- customer name lặp;
- đổi category manager phải update nhiều row;
- xóa order cuối có thể làm mất thông tin customer;
- insert customer chưa có order khó.

Đây là anomaly do dependency bị trộn trong cùng relation.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_15') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_15
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_15;
END;
GO

CREATE DATABASE CommerceLab08_15;
GO
USE CommerceLab08_15;
GO

CREATE TABLE dbo.Customers
(
    CustomerId int NOT NULL
        CONSTRAINT PK_Customers PRIMARY KEY,
    Email varchar(320) NOT NULL
        CONSTRAINT UQ_Customers_Email UNIQUE,
    FullName nvarchar(120) NOT NULL
);

CREATE TABLE dbo.Categories
(
    CategoryId int NOT NULL
        CONSTRAINT PK_Categories PRIMARY KEY,
    CategoryName nvarchar(100) NOT NULL,
    ManagerEmail varchar(320) NOT NULL
);

CREATE TABLE dbo.Products
(
    ProductId int NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    CategoryId int NOT NULL,
    ProductName nvarchar(160) NOT NULL,
    CONSTRAINT FK_Products_Categories
        FOREIGN KEY (CategoryId)
        REFERENCES dbo.Categories(CategoryId)
);

CREATE TABLE dbo.Orders
(
    OrderId int NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    OrderedAt date NOT NULL,
    CONSTRAINT FK_Orders_Customers
        FOREIGN KEY (CustomerId)
        REFERENCES dbo.Customers(CustomerId)
);

CREATE TABLE dbo.OrderItems
(
    OrderId int NOT NULL,
    ProductId int NOT NULL,
    Quantity int NOT NULL,
    UnitPrice decimal(19,4) NOT NULL,
    CONSTRAINT PK_OrderItems
        PRIMARY KEY (OrderId, ProductId),
    CONSTRAINT FK_OrderItems_Orders
        FOREIGN KEY (OrderId)
        REFERENCES dbo.Orders(OrderId),
    CONSTRAINT FK_OrderItems_Products
        FOREIGN KEY (ProductId)
        REFERENCES dbo.Products(ProductId)
);
GO

INSERT INTO dbo.Customers VALUES
(1,'an@example.com',N'Nguyễn An');

INSERT INTO dbo.Categories VALUES
(10,N'Accessory','manager@example.com');

INSERT INTO dbo.Products VALUES
(100,10,N'Keyboard'),
(101,10,N'Mouse');

INSERT INTO dbo.Orders VALUES
(1000,1,'2026-09-01');

INSERT INTO dbo.OrderItems VALUES
(1000,100,1,1200000),
(1000,101,2,500000);
GO

SELECT
    o.OrderId,
    c.Email,
    c.FullName,
    p.ProductName,
    cat.CategoryName,
    oi.Quantity,
    oi.UnitPrice
FROM dbo.Orders AS o
JOIN dbo.Customers AS c
    ON c.CustomerId = o.CustomerId
JOIN dbo.OrderItems AS oi
    ON oi.OrderId = o.OrderId
JOIN dbo.Products AS p
    ON p.ProductId = oi.ProductId
JOIN dbo.Categories AS cat
    ON cat.CategoryId = p.CategoryId
ORDER BY o.OrderId, p.ProductId;
GO
```

## 4. Giải thích cơ chế

### Functional dependency

Ví dụ:

```text
CustomerId -> Email, FullName
CategoryId -> CategoryName, ManagerEmail
ProductId -> ProductName, CategoryId
```

Nếu một fact phụ thuộc key khác, nó thường nên ở relation tương ứng.

### 1NF

Không dùng repeating group hoặc danh sách IDs trong một column:

```text
ProductIds = "10,20,30"
```

Thay bằng nhiều row OrderItems.

### 2NF

Với composite key:

```text
(OrderId, ProductId)
```

attribute non-key phải phụ thuộc toàn bộ key, không chỉ một phần.

### 3NF

Non-key attribute không nên phụ thuộc transitively qua non-key khác.

```text
ProductId -> CategoryId -> CategoryName
```

CategoryName thuộc Categories.

### BCNF

Mọi determinant không tầm thường nên là candidate key.

BCNF mạnh hơn 3NF ở một số dependency đặc biệt.

## 5. Kiến thức nền

### Anomaly

- update anomaly;
- insert anomaly;
- delete anomaly.

Chuẩn hóa giúp giảm các anomaly này.

### Lossless decomposition

Sau khi tách table, join lại phải tái tạo fact đúng mà không sinh row giả.

### Snapshot có chủ đích

OrderItems trong production có thể giữ ProductName/UnitPrice snapshot để bảo toàn lịch sử.

Đây là denormalization có lý do.

### Normal form là công cụ reasoning

Mục tiêu thực tế:

- dependency rõ;
- invariant đúng;
- anomaly được kiểm soát;
- query/maintenance hợp lý.

## 6. Lỗi thường gặp

### Tách mọi field thành table

Chuẩn hóa không phải càng nhiều table càng tốt.

### Xóa historical snapshot vì thấy duplicate

Historical fact khác current catalog fact.

### Dùng JSON/CSV để né relation

Có thể mất constraint và queryability.

### Học thuộc định nghĩa nhưng không tìm dependency

Dependency mới là gốc của reasoning.

## 7. Bài tập

### Bài 1

Chuẩn hóa StudentCourse có StudentName, CourseName, TeacherName.

### Bài 2

Tìm partial dependency trong composite key.

### Bài 3

Tìm transitive dependency.

### Bài 4

Giải thích vì sao OrderItem.UnitPrice có thể giữ dù Product.Price tồn tại.

### Bài 5

Viết before/after schema cho table có Phone1/Phone2/Phone3.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi hiểu functional dependency.
- [ ] Tôi nhận ra update/insert/delete anomaly.
- [ ] Tôi giải thích được 1NF/2NF/3NF.
- [ ] Tôi biết BCNF mạnh hơn 3NF ở một số case.
- [ ] Tôi không chuẩn hóa máy móc.
- [ ] Tôi phân biệt duplication lỗi và snapshot lịch sử.

Điều hướng:

- Bài trước: [Mô hình ER và quan hệ](./14-mo-hinh-er-va-quan-he.md)
- Bài tiếp theo: [Denormalization và dữ liệu lịch sử](./16-denormalization-va-du-lieu-lich-su.md)
