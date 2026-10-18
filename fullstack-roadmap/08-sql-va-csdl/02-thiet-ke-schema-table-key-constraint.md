# Thiết kế schema, table, key và constraint

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng schema để tổ chức object;
- thiết kế primary key và foreign key;
- dùng UNIQUE, CHECK, DEFAULT và NOT NULL;
- hiểu candidate key và surrogate key;
- tạo relationship one-to-many;
- để database bảo vệ invariant thay vì chỉ tin application.

## 2. Bài toán mở đầu

Hệ thống bán hàng cần bảo đảm:

- email customer không trùng;
- SKU không trùng;
- giá sản phẩm không âm;
- order phải thuộc customer tồn tại;
- status chỉ nhận một tập giá trị hợp lệ.

Nếu chỉ kiểm tra trong C#, một script SQL hoặc service khác vẫn có thể ghi dữ liệu sai.

Constraint đặt invariant ngay tại database.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_02') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_02
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_02;
END;
GO

CREATE DATABASE CommerceLab08_02;
GO
USE CommerceLab08_02;
GO

CREATE SCHEMA sales AUTHORIZATION dbo;
GO
CREATE SCHEMA catalog AUTHORIZATION dbo;
GO

CREATE TABLE sales.Customers
(
    CustomerId int IDENTITY(1,1) NOT NULL,
    FullName nvarchar(120) NOT NULL,
    Email varchar(320) NOT NULL,
    CreatedAt datetime2(0) NOT NULL
        CONSTRAINT DF_Customers_CreatedAt DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_Customers
        PRIMARY KEY (CustomerId),

    CONSTRAINT UQ_Customers_Email
        UNIQUE (Email)
);
GO

CREATE TABLE catalog.Products
(
    ProductId int IDENTITY(1,1) NOT NULL,
    Sku varchar(40) NOT NULL,
    Name nvarchar(160) NOT NULL,
    Price decimal(19,4) NOT NULL,
    IsActive bit NOT NULL
        CONSTRAINT DF_Products_IsActive DEFAULT 1,

    CONSTRAINT PK_Products
        PRIMARY KEY (ProductId),

    CONSTRAINT UQ_Products_Sku
        UNIQUE (Sku),

    CONSTRAINT CK_Products_Price
        CHECK (Price >= 0)
);
GO

CREATE TABLE sales.Orders
(
    OrderId bigint IDENTITY(1,1) NOT NULL,
    CustomerId int NOT NULL,
    Status varchar(20) NOT NULL,
    OrderedAt datetime2(0) NOT NULL
        CONSTRAINT DF_Orders_OrderedAt DEFAULT SYSUTCDATETIME(),

    CONSTRAINT PK_Orders
        PRIMARY KEY (OrderId),

    CONSTRAINT FK_Orders_Customers
        FOREIGN KEY (CustomerId)
        REFERENCES sales.Customers(CustomerId),

    CONSTRAINT CK_Orders_Status
        CHECK (Status IN ('Pending', 'Paid', 'Shipped', 'Cancelled'))
);
GO

INSERT INTO sales.Customers (FullName, Email)
VALUES (N'Nguyễn An', 'an@example.com');

INSERT INTO catalog.Products (Sku, Name, Price)
VALUES ('KB-01', N'Bàn phím', 750000);

INSERT INTO sales.Orders (CustomerId, Status)
VALUES (1, 'Pending');

SELECT
    o.OrderId,
    c.FullName,
    o.Status,
    o.OrderedAt
FROM sales.Orders AS o
JOIN sales.Customers AS c
    ON c.CustomerId = o.CustomerId;
GO
```

## 4. Giải thích cơ chế

### Schema

```text
sales.Customers
sales.Orders
catalog.Products
```

Schema tạo namespace.

Nó giúp:

- tổ chức domain;
- phân quyền;
- tránh tên object lẫn lộn.

### Primary key

```sql
PRIMARY KEY (CustomerId)
```

SQL Server tạo uniqueness guarantee và index phù hợp theo thiết kế mặc định.

### Foreign key

```sql
FOREIGN KEY (CustomerId)
REFERENCES sales.Customers(CustomerId)
```

Database từ chối order có CustomerId không tồn tại.

### UNIQUE

Email và SKU là candidate key nghiệp vụ.

Ta vẫn dùng surrogate primary key nhưng bảo vệ uniqueness business key.

### CHECK

```sql
CHECK (Price >= 0)
```

Constraint đơn giản nhưng cực giá trị: dữ liệu sai bị chặn bất kể nguồn ghi.

## 5. Kiến thức nền

### Natural key và surrogate key

Natural key:

```text
Email
NationalId
SKU
```

Surrogate key:

```text
CustomerId
ProductId
```

Surrogate key thường:

- nhỏ;
- ổn định;
- ít phụ thuộc business change.

Nhưng natural key vẫn có thể cần UNIQUE.

### Constraint naming

Tên rõ:

```text
PK_
FK_
UQ_
CK_
DF_
```

giúp đọc error và migration dễ hơn.

### Referential action

Có thể cấu hình:

```text
ON DELETE CASCADE
ON DELETE SET NULL
```

Không bật cascade theo thói quen.

Xóa customer kéo theo toàn bộ order thường là business bug.

## 6. Lỗi thường gặp

### Không có foreign key vì “application đã validate”

Application có thể có bug hoặc nhiều writer.

Database constraint là lớp bảo vệ cuối.

### Dùng varchar cho text Unicode tiếng Việt

Tên người/sản phẩm nên dùng `nvarchar`.

### Mọi column đều nullable

Nullable phải phản ánh business semantics, không phải để insert dễ hơn.

### Cascade delete tùy tiện

Cần phân biệt:

- dữ liệu child thật sự owned;
- dữ liệu lịch sử cần giữ.

## 7. Bài tập

### Bài 1

Thêm table `catalog.Categories`.

### Bài 2

Cho Product có CategoryId foreign key.

### Bài 3

Thêm CHECK để SKU không là chuỗi rỗng sau khi trim.

### Bài 4

Tạo table `sales.OrderItems` với composite unique:

```text
(OrderId, ProductId)
```

### Bài 5

Cố insert:

- email trùng;
- price âm;
- CustomerId không tồn tại.

Ghi lại constraint nào chặn từng lỗi.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi dùng được schema.
- [ ] Tôi phân biệt PK/FK/UQ.
- [ ] Tôi dùng CHECK/DEFAULT/NOT NULL.
- [ ] Tôi hiểu natural và surrogate key.
- [ ] Tôi không bật cascade delete tùy tiện.
- [ ] Tôi đặt invariant quan trọng trong database.

Điều hướng:

- Bài trước: [Mô hình quan hệ và cài đặt SQL Server](./01-mo-hinh-quan-he-va-cai-dat-sql-server.md)
- Bài tiếp theo: [Kiểu dữ liệu và NULL](./03-kieu-du-lieu-va-null.md)
