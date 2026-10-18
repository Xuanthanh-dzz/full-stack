# Mô hình ER và quan hệ

## 1. Mục tiêu

Sau bài này, bạn có thể:

- chuyển requirement thành entity và relationship;
- xác định one-to-one, one-to-many, many-to-many;
- dùng associative entity cho many-to-many;
- phân biệt optional/required relationship;
- xác định cardinality và ownership;
- tạo ERD cho domain thương mại;
- tránh thiết kế table theo màn hình UI.

## 2. Bài toán mở đầu

Requirement:

> Customer đặt nhiều Order. Order có nhiều Product. Product thuộc nhiều Category. Mỗi Order có một địa chỉ giao hàng snapshot tại thời điểm đặt.

ER modeling bắt đầu từ **thực thể và quan hệ nghiệp vụ**.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_14') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_14
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_14;
END;
GO

CREATE DATABASE CommerceLab08_14;
GO
USE CommerceLab08_14;
GO

CREATE TABLE dbo.Customers
(
    CustomerId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Customers PRIMARY KEY,
    Email varchar(320) NOT NULL
        CONSTRAINT UQ_Customers_Email UNIQUE,
    FullName nvarchar(120) NOT NULL
);

CREATE TABLE dbo.Products
(
    ProductId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Sku varchar(40) NOT NULL
        CONSTRAINT UQ_Products_Sku UNIQUE,
    Name nvarchar(160) NOT NULL
);

CREATE TABLE dbo.Categories
(
    CategoryId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Categories PRIMARY KEY,
    Name nvarchar(100) NOT NULL
);

CREATE TABLE dbo.ProductCategories
(
    ProductId int NOT NULL,
    CategoryId int NOT NULL,
    CONSTRAINT PK_ProductCategories
        PRIMARY KEY (ProductId, CategoryId),
    CONSTRAINT FK_ProductCategories_Product
        FOREIGN KEY (ProductId)
        REFERENCES dbo.Products(ProductId),
    CONSTRAINT FK_ProductCategories_Category
        FOREIGN KEY (CategoryId)
        REFERENCES dbo.Categories(CategoryId)
);

CREATE TABLE dbo.Orders
(
    OrderId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    ShippingName nvarchar(120) NOT NULL,
    ShippingAddress nvarchar(500) NOT NULL,
    CONSTRAINT FK_Orders_Customers
        FOREIGN KEY (CustomerId)
        REFERENCES dbo.Customers(CustomerId)
);

CREATE TABLE dbo.OrderItems
(
    OrderItemId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_OrderItems PRIMARY KEY,
    OrderId bigint NOT NULL,
    ProductId int NOT NULL,
    ProductName nvarchar(160) NOT NULL,
    UnitPrice decimal(19,4) NOT NULL,
    Quantity int NOT NULL,
    CONSTRAINT FK_OrderItems_Orders
        FOREIGN KEY (OrderId)
        REFERENCES dbo.Orders(OrderId),
    CONSTRAINT FK_OrderItems_Products
        FOREIGN KEY (ProductId)
        REFERENCES dbo.Products(ProductId),
    CONSTRAINT CK_OrderItems_Quantity
        CHECK (Quantity > 0)
);
GO

SELECT
    fk.name AS ForeignKeyName,
    OBJECT_SCHEMA_NAME(fk.parent_object_id) AS ChildSchema,
    OBJECT_NAME(fk.parent_object_id) AS ChildTable,
    OBJECT_NAME(fk.referenced_object_id) AS ParentTable
FROM sys.foreign_keys AS fk
ORDER BY ChildTable, ForeignKeyName;
GO
```

## 4. Giải thích cơ chế

### One-to-many

```text
Customer 1 ---- * Order
```

Foreign key nằm phía many.

### Many-to-many

```text
Product * ---- * Category
```

Relational model cần associative table `ProductCategories`.

### Snapshot data

OrderItem lưu ProductName/UnitPrice dù Product cũng có giá hiện tại.

Đây là duplication có chủ đích để giữ lịch sử.

### Optional relationship

Nullable FK thường biểu diễn optional relation.

Nhưng optional phải đến từ business requirement.

## 5. Kiến thức nền

### Entity

Entity có identity riêng và lifecycle.

### Value object trong relational design

Shipping address snapshot có thể được flatten vào Order nếu lifecycle thuộc Order.

### Cardinality

Cần hỏi:

```text
0..1?
1?
0..*?
1..*?
```

### ERD trước code

ERD giúp review missing relation, ownership, optionality và history semantics.

## 6. Lỗi thường gặp

### Table theo màn hình

UI thay đổi thường xuyên; domain data tồn tại lâu hơn.

### Many-to-many lưu CSV IDs

Phá referential integrity và query.

### Không lưu historical snapshot

Product đổi giá làm order cũ đổi theo nếu chỉ join giá hiện tại.

### Mọi concept thành table

Over-normalization cũng có cost.

## 7. Bài tập

### Bài 1

Vẽ ERD cho School: Student, Course, Enrollment.

### Bài 2

Thiết kế Order -> Payment là 1-1 hay 1-n? Giải thích theo requirement refund/retry.

### Bài 3

Thêm Wishlist many-to-many Customer/Product.

### Bài 4

Thiết kế address book và order shipping snapshot.

### Bài 5

Review một schema cũ và chỉ ra table nào đang phản ánh UI thay vì domain.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi xác định được entity.
- [ ] Tôi phân biệt 1-1, 1-n, n-n.
- [ ] Tôi dùng associative entity.
- [ ] Tôi mô hình optionality có chủ đích.
- [ ] Tôi hiểu snapshot lịch sử.
- [ ] Tôi thiết kế từ domain không từ màn hình.

Điều hướng:

- Bài trước: [View, procedure, function và trigger](./13-view-stored-procedure-function-trigger.md)
- Bài tiếp theo: [Chuẩn hóa 1NF, 2NF, 3NF và BCNF](./15-chuan-hoa-1nf-2nf-3nf-bcnf.md)
