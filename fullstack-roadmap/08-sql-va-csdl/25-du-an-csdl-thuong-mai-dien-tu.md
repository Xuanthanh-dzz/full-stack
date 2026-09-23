# Dự án: CSDL thương mại điện tử

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Capstone ghép schema, query và checkout transaction thành một luồng dữ liệu có contract.
- Dùng để chứng minh từ requirement tới state và bằng chứng kiểm tra.
- Sample một sản phẩm chưa giải quyết payment idempotency, mọi concurrency hay vận hành production.

## 1. Mục tiêu

Đây là checkpoint cuối Module 08. Bạn phải có thể:

- đọc requirement và tạo ERD;
- thiết kế schema, PK, FK và constraint;
- chuẩn hóa rồi denormalize có lý do;
- viết query CRUD và report;
- thiết kế index từ workload;
- dùng transaction cho checkout;
- giải thích isolation và deadlock;
- áp dụng least privilege;
- có backup/migration plan;
- đọc execution plan và tối ưu query chậm.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Phiếu mua hàng phải nối được người mua, hàng, kho và lần thanh toán. Nếu thiếu kho thì không ghi nửa phiếu; nếu giá catalog đổi sau đó thì phiếu cũ vẫn phải giải thích đúng số tiền đã chốt.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| transaction boundary | nhóm thay đổi phải cùng thành công | stock/order/item/payment intent |
| payment attempt | một lần thử thanh toán | nhiều lần trên một order |
| snapshot price | giá được chốt cho dòng hàng | UnitPriceSnapshot |
| idempotency | lặp yêu cầu không tạo thêm effect ngoài contract | bài tập ProviderReference |

### Ví dụ nhỏ — tính tay trước

Kho product1=10,giá 1200000,quantity 2 →kho8,order Pending2400000,item2×1200000,payment Pending2400000. Đây là ý định thanh toán, chưa có bằng chứng thu tiền từ provider.

Thiết kế database cho mini e-commerce có:

- customer;
- product/category;
- inventory;
- order/order item;
- payment;
- shipping snapshot;
- audit/history.

Use case tối thiểu:

1. customer đăng ký;
2. browse/search product;
3. checkout;
4. trừ stock an toàn;
5. giữ snapshot giá/tên/address;
6. payment có thể retry;
7. admin xem doanh thu;
8. không xóa mất lịch sử order;
9. backup/restore được;
10. schema đủ rõ để Module 09 map bằng EF Core.

<a id="3-loi-giai-tham-chieu-bang-sql"></a>

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_25') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_25
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_25;
END;
GO

CREATE DATABASE CommerceLab08_25;
GO
USE CommerceLab08_25;
GO

CREATE SCHEMA catalog AUTHORIZATION dbo;
GO
CREATE SCHEMA sales AUTHORIZATION dbo;
GO
CREATE SCHEMA inventory AUTHORIZATION dbo;
GO
CREATE SCHEMA billing AUTHORIZATION dbo;
GO

CREATE TABLE sales.Customers
(
    CustomerId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Customers PRIMARY KEY,
    Email varchar(320) NOT NULL
        CONSTRAINT UQ_Customers_Email UNIQUE,
    FullName nvarchar(120) NOT NULL,
    CreatedAt datetime2(0) NOT NULL
        CONSTRAINT DF_Customers_CreatedAt DEFAULT SYSUTCDATETIME()
);

CREATE TABLE catalog.Categories
(
    CategoryId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Categories PRIMARY KEY,
    ParentCategoryId int NULL,
    Name nvarchar(100) NOT NULL,
    CONSTRAINT FK_Categories_Parent
        FOREIGN KEY (ParentCategoryId)
        REFERENCES catalog.Categories(CategoryId)
);

CREATE TABLE catalog.Products
(
    ProductId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Sku varchar(40) NOT NULL
        CONSTRAINT UQ_Products_Sku UNIQUE,
    Name nvarchar(160) NOT NULL,
    Price decimal(19,4) NOT NULL,
    IsActive bit NOT NULL
        CONSTRAINT DF_Products_IsActive DEFAULT 1,
    CreatedAt datetime2(0) NOT NULL
        CONSTRAINT DF_Products_CreatedAt DEFAULT SYSUTCDATETIME(),
    RowVersion rowversion NOT NULL,
    CONSTRAINT CK_Products_Price CHECK (Price >= 0)
);

CREATE TABLE catalog.ProductCategories
(
    ProductId bigint NOT NULL,
    CategoryId int NOT NULL,
    CONSTRAINT PK_ProductCategories
        PRIMARY KEY (ProductId, CategoryId),
    CONSTRAINT FK_ProductCategories_Product
        FOREIGN KEY (ProductId)
        REFERENCES catalog.Products(ProductId),
    CONSTRAINT FK_ProductCategories_Category
        FOREIGN KEY (CategoryId)
        REFERENCES catalog.Categories(CategoryId)
);

CREATE TABLE inventory.Stock
(
    ProductId bigint NOT NULL
        CONSTRAINT PK_Stock PRIMARY KEY,
    Quantity int NOT NULL,
    CONSTRAINT FK_Stock_Products
        FOREIGN KEY (ProductId)
        REFERENCES catalog.Products(ProductId),
    CONSTRAINT CK_Stock_Quantity CHECK (Quantity >= 0)
);

CREATE TABLE sales.Orders
(
    OrderId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId bigint NOT NULL,
    Status varchar(20) NOT NULL,
    ShippingName nvarchar(120) NOT NULL,
    ShippingAddress nvarchar(500) NOT NULL,
    TotalAmount decimal(19,4) NOT NULL,
    OrderedAt datetime2(0) NOT NULL
        CONSTRAINT DF_Orders_OrderedAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_Orders_Customers
        FOREIGN KEY (CustomerId)
        REFERENCES sales.Customers(CustomerId),
    CONSTRAINT CK_Orders_Status
        CHECK (Status IN ('Pending','Paid','Shipped','Cancelled')),
    CONSTRAINT CK_Orders_Total
        CHECK (TotalAmount >= 0)
);

CREATE TABLE sales.OrderItems
(
    OrderItemId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_OrderItems PRIMARY KEY,
    OrderId bigint NOT NULL,
    ProductId bigint NOT NULL,
    ProductNameSnapshot nvarchar(160) NOT NULL,
    UnitPriceSnapshot decimal(19,4) NOT NULL,
    Quantity int NOT NULL,
    CONSTRAINT FK_OrderItems_Orders
        FOREIGN KEY (OrderId)
        REFERENCES sales.Orders(OrderId),
    CONSTRAINT FK_OrderItems_Products
        FOREIGN KEY (ProductId)
        REFERENCES catalog.Products(ProductId),
    CONSTRAINT UQ_OrderItems_Order_Product
        UNIQUE (OrderId, ProductId),
    CONSTRAINT CK_OrderItems_Quantity
        CHECK (Quantity > 0),
    CONSTRAINT CK_OrderItems_UnitPrice
        CHECK (UnitPriceSnapshot >= 0)
);

CREATE TABLE billing.Payments
(
    PaymentId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Payments PRIMARY KEY,
    OrderId bigint NOT NULL,
    Provider varchar(30) NOT NULL,
    ProviderReference varchar(100) NULL,
    Status varchar(20) NOT NULL,
    Amount decimal(19,4) NOT NULL,
    CreatedAt datetime2(0) NOT NULL
        CONSTRAINT DF_Payments_CreatedAt DEFAULT SYSUTCDATETIME(),
    CONSTRAINT FK_Payments_Orders
        FOREIGN KEY (OrderId)
        REFERENCES sales.Orders(OrderId),
    CONSTRAINT CK_Payments_Amount
        CHECK (Amount >= 0)
);
GO

CREATE INDEX IX_Orders_Customer_OrderedAt
ON sales.Orders(CustomerId, OrderedAt DESC)
INCLUDE(Status, TotalAmount);

CREATE INDEX IX_Orders_Status_OrderedAt
ON sales.Orders(Status, OrderedAt DESC)
INCLUDE(CustomerId, TotalAmount);

CREATE INDEX IX_Payments_Order
ON billing.Payments(OrderId, CreatedAt DESC)
INCLUDE(Status, Amount);
GO

INSERT INTO sales.Customers(Email, FullName)
VALUES ('an@example.com', N'Nguyễn An');

INSERT INTO catalog.Categories(ParentCategoryId, Name)
VALUES (NULL, N'Accessory');

INSERT INTO catalog.Products(Sku, Name, Price)
VALUES
('KB-01', N'Keyboard Pro', 1200000),
('MS-01', N'Mouse Pro', 700000);

INSERT INTO catalog.ProductCategories(ProductId, CategoryId)
SELECT ProductId, 1
FROM catalog.Products;

INSERT INTO inventory.Stock(ProductId, Quantity)
SELECT ProductId, 10
FROM catalog.Products;
GO

SET XACT_ABORT ON;

BEGIN TRY
    BEGIN TRANSACTION;

    DECLARE @CustomerId bigint = 1;
    DECLARE @ProductId bigint = 1;
    DECLARE @Quantity int = 2;
    IF @Quantity IS NULL OR @Quantity <= 0
        THROW 51003, 'Quantity must be positive.', 1;

    DECLARE @Price decimal(19,4);
    DECLARE @Name nvarchar(160);

    SELECT
        @Price = Price,
        @Name = Name
    FROM catalog.Products
    WHERE ProductId = @ProductId
      AND IsActive = 1;

    IF @Price IS NULL
        THROW 51001, 'Product not available.', 1;

    UPDATE inventory.Stock
    SET Quantity = Quantity - @Quantity
    WHERE ProductId = @ProductId
      AND Quantity >= @Quantity;

    IF @@ROWCOUNT <> 1
        THROW 51002, 'Not enough stock.', 1;

    DECLARE @Total decimal(19,4) = @Price * @Quantity;

    INSERT INTO sales.Orders
    (
        CustomerId,
        Status,
        ShippingName,
        ShippingAddress,
        TotalAmount
    )
    VALUES
    (
        @CustomerId,
        'Pending',
        N'Nguyễn An',
        N'1 Demo Street, Hà Nội',
        @Total
    );

    DECLARE @OrderId bigint = SCOPE_IDENTITY();

    INSERT INTO sales.OrderItems
    (
        OrderId,
        ProductId,
        ProductNameSnapshot,
        UnitPriceSnapshot,
        Quantity
    )
    VALUES
    (
        @OrderId,
        @ProductId,
        @Name,
        @Price,
        @Quantity
    );

    INSERT INTO billing.Payments
    (
        OrderId,
        Provider,
        Status,
        Amount
    )
    VALUES
    (
        @OrderId,
        'DemoPay',
        'Pending',
        @Total
    );

    COMMIT TRANSACTION;
END TRY
BEGIN CATCH
    IF XACT_STATE() <> 0
        ROLLBACK TRANSACTION;

    THROW;
END CATCH;
GO

SELECT
    o.OrderId,
    c.Email,
    o.Status,
    o.TotalAmount,
    oi.ProductNameSnapshot,
    oi.UnitPriceSnapshot,
    oi.Quantity,
    p.Status AS PaymentStatus
FROM sales.Orders AS o
JOIN sales.Customers AS c
    ON c.CustomerId = o.CustomerId
JOIN sales.OrderItems AS oi
    ON oi.OrderId = o.OrderId
LEFT JOIN billing.Payments AS p
    ON p.OrderId = o.OrderId
ORDER BY o.OrderId;
GO

SELECT
    YEAR(OrderedAt) AS SalesYear,
    MONTH(OrderedAt) AS SalesMonth,
    COUNT(*) AS OrderCount,
    SUM(TotalAmount) AS NonCancelledOrderValue
FROM sales.Orders
WHERE Status <> 'Cancelled'
GROUP BY
    YEAR(OrderedAt),
    MONTH(OrderedAt)
ORDER BY SalesYear, SalesMonth;
GO
```

### Walkthrough — execution / state / cost

1. Schemas/constraints/indexes được dựng trước, seed customer và hai products/kho.
2. Checkout validate quantity dương, đọc product active và giá snapshot trong transaction.
3. UPDATE kho có điều kiện; nếu không đổi đúng 1 row thì THROW và rollback mọi thay đổi trong transaction.
4. Tạo order/item/payment intent rồi commit; query report đọc từ server. Storage/index/log/locks tăng theo số dòng, join payment attempts có thể nhân item rows khi mở rộng.

### Mini-check

Nếu INSERT payment lỗi sau khi đã trừ kho và tạo order, catch phải để lại những row và số kho nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Schema boundary

```text
catalog
sales
inventory
billing
```

giúp tổ chức object theo domain và chuẩn bị permission boundary.

### Snapshot

OrderItems giữ ProductNameSnapshot và UnitPriceSnapshot.

Order giữ ShippingName và ShippingAddress snapshot.

Lịch sử không phụ thuộc catalog/profile hiện tại.

### Stock update

Pattern:

```sql
UPDATE inventory.Stock
SET Quantity = Quantity - @Quantity
WHERE ProductId = @ProductId
  AND Quantity >= @Quantity;
```

tránh read-then-write race đơn giản.

### Giá trị đơn chưa phải tiền đã thu

Report cuối cộng giá trị các đơn chưa hủy, nên tên cột là NonCancelledOrderValue. Đơn Pending của sample đóng góp 2400000; không được gọi đó là tiền đã thu. Báo cáo thanh toán cần status và quy tắc refund/settlement riêng.

### Payment retry

Payments là one-to-many với Order vì payment có thể fail, retry hoặc refund về sau.

Không ép one-to-one nếu workflow không bảo đảm.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| reference sample | một sản phẩm, một process gọi SQL | đủ trace atomic state, chưa là shop hoàn chỉnh |
| multi-item checkout | nhiều dòng, lock order và tổng tiền | cần contract/test thêm trước mở rộng |
| provider payment | effect ngoài DB | không rollback bằng SQL transaction |

### Misconception check

**Đúng hay sai?** Payments Pending nghĩa là đã trừ tiền khách.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chỉ ghi intent trong DB, chưa gọi provider.

</details>

**Đúng hay sai?** FK và CHECK tự giữ TotalAmount bằng tổng items.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: rule tổng nhiều row cần protocol cập nhật/validation riêng.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace checkout và schema.

- **Working Developer — dùng khi làm việc:** failure/constraints/history.

- **Deep Dive — có thể quay lại sau:** concurrency/payment/ops khi có yêu cầu.

### Workload phải được định nghĩa

Trước khi thêm index, liệt kê query quan trọng:

- product by SKU;
- orders by customer;
- pending orders by time;
- payment by order;
- revenue report.

Index đi theo workload.

### Security

Runtime account không cần quyền DROP/ALTER.

Migration account và runtime account nên tách.

### Backup

Capstone phải có backup command, restore test, RPO/RTO giả định và migration plan.

### README database

Project tối thiểu cần:

```text
requirements
ERD
setup
seed
queries
indexes
transactions
security
backup/restore
known trade-offs
```

<a id="6-loi-thuong-gap-va-review-checklist"></a>

## 6. Lỗi thường gặp

### Checkout đọc stock rồi update sau

Race condition dễ oversell.

### Product price không snapshot

Order lịch sử thay đổi khi catalog đổi.

### Payment unique one-to-one khi provider có retry

Schema không phản ánh workflow thật.

### Index theo cảm tính

Không map index với query.

### Runtime dùng owner/sysadmin

Phá least privilege.

### Không có restore drill

Backup chỉ trên giấy.

<a id="7-bai-tap-mo-rong"></a>

## 7. Khi nào KHÔNG dùng

Không thêm broker/microservice hoặc nhiều tầng repository cho lab schema nhỏ. Không gọi provider trong transaction giữ lock dài; trước hết xác định failure/idempotency contract.

## 8. Production notes & scale check

Gate kiểm schema, seed, checkout state, snapshot và rollback khi biến thể quantity vượt kho/không hợp lệ. Report NonCancelledOrderValue không gọi là tiền đã thu. Permission và backup drill có evidence ở bài23/24; bài tập capstone mở rộng cần submission riêng, không được coi tự động hoàn thành.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Cart

Thêm Cart/CartItems với unique constraint hợp lý.

### Bài 2 — Coupon

Thiết kế coupon có thời gian hiệu lực, usage limit và order discount snapshot.

### Bài 3 — Inventory ledger

Thêm StockMovements để audit nhập/xuất.

### Bài 4 — Payment idempotency

Thêm ProviderReference unique theo policy phù hợp và thiết kế retry.

### Bài 5 — Query tuning

Sinh 100.000 order, đo 5 query trước/sau index.

### Bài 6 — Security

Tạo runtime role chỉ có quyền application cần.

### Bài 7 — Backup

Backup, verify và restore vào database khác.

### Bài 8 — Migration

Thêm OrderNumber theo expand-contract.

<a id="8-checklist-hoan-thanh-module-08"></a>

## 10. Bài tập tích hợp liên module — Judgment

Từ Module 06 và 07: vẽ ownership/state từ input tới DB commit; chọn khóa/index theo query đã nêu. Với100order/ngày, giải pháp nhỏ nhất nào đủ và driver nào buộc xem lại?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Điểm nào công bố checkout thành công?
2. Rule nào chưa được CHECK bảo vệ?
3. Payment attempt khác payment success thế nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

### Kiến thức

- [ ] Tôi thiết kế PK/FK/constraint từ domain.
- [ ] Tôi chọn type và NULL semantics đúng.
- [ ] Tôi viết CRUD/filter/group/join/subquery/window.
- [ ] Tôi chuẩn hóa và denormalize có lý do.
- [ ] Tôi thiết kế index từ workload.
- [ ] Tôi dùng transaction và giải thích ACID/isolation.
- [ ] Tôi đọc execution plan cơ bản.
- [ ] Tôi tối ưu SARGability dựa trên đo lường.
- [ ] Tôi áp dụng least privilege/parameterization.
- [ ] Tôi có backup/restore/migration plan.

### Project

- [ ] ERD đầy đủ.
- [ ] Schema dựng từ script sạch.
- [ ] Seed data tái tạo được.
- [ ] Checkout transaction chống stock âm.
- [ ] Order giữ snapshot lịch sử.
- [ ] Có query report thực tế.
- [ ] Index có lý do và đo IO.
- [ ] Runtime permission tối thiểu.
- [ ] Backup được restore thử.
- [ ] README giải thích trade-off.

Điều hướng:

- Bài trước: [Backup, restore và migration dữ liệu](./24-backup-restore-va-migration-du-lieu.md)
- Module tiếp theo: [LINQ và Entity Framework Core](../PROGRESS.md#09-linq-va-ef-core)

---

## Definition of Done

Module chỉ hoàn thành khi:

```text
25/25 bài
+
SQL sample chạy trên SQL Server 2025
+
constraint/query/transaction pass
+
cross-link hợp lệ
+
MkDocs build pass
+
project capstone tái tạo được từ database sạch
```

Mục tiêu cuối cùng không phải nhớ cú pháp SQL, mà là có thể đi từ:

```text
requirement
-> ERD
-> schema
-> constraint
-> query
-> index
-> transaction
-> security
-> backup
-> performance verification
```

### Checkpoint sau cụm bài

- [Failure Lab](./failure-labs/05-injection.md)
- [Spaced Review](./reviews/review-05.md)
- [PR Review](./pr-review-labs/01-report.md)
