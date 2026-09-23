# Mô hình ER và quan hệ

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- ER modeling xác định entity, identity và cardinality trước khi tạo table.
- Dùng quan hệ để đặt FK, unique key và snapshot đúng chỗ.
- FK không tự buộc mọi cha có con hoặc bảo vệ lịch sử khỏi mọi UPDATE.

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

### Trực giác 60 giây

Đơn có người mua và nhiều dòng hàng. Sản phẩm có thể nằm trong nhiều nhóm, nên cần phiếu liên kết sản phẩm–nhóm; nhét danh sách mã vào một ô làm mất chỗ kiểm từng quan hệ.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| entity | thực thể có identity và vòng đời | Order |
| cardinality | số lượng quan hệ được phép | 0..n orders/customer |
| associative table | bảng nối quan hệ nhiều–nhiều | ProductCategories |
| snapshot | giá trị chụp tại thời điểm nghiệp vụ | ShippingAddress |

### Ví dụ nhỏ — tính tay trước

Sản phẩm ID 1 thuộc hai nhóm ID 10 và 20, nên bảng nối có (1, 10) và (1, 20). Thêm lại (1, 10) bị khóa chính ghép chặn; thêm (1, 99) bị foreign key chặn nếu nhóm 99 chưa tồn tại.

Requirement:

> Customer đặt nhiều Order. Order có nhiều Product. Product thuộc nhiều Category. Mỗi Order có một địa chỉ giao hàng snapshot tại thời điểm đặt.

ER modeling bắt đầu từ **thực thể và quan hệ nghiệp vụ**.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. Requirement xác định identity và optionality trước DDL.
2. FK Orders.CustomerId biểu diễn mỗi order có một customer hợp lệ; không buộc customer phải có order.
3. PK ghép bảng nối bảo vệ cặp liên kết duy nhất.
4. Snapshot nằm trên order/item và tồn tại theo lịch sử; table/index/FK có storage và write cost ở server. Schema mẫu không tự cấm sửa snapshot sau checkout.

### Mini-check

Orders.CustomerId có NOT NULL nhưng không UNIQUE: một khách có tối đa bao nhiêu order theo schema?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| one-to-many | FK ở child | NOT NULL quyết định child bắt buộc có cha |
| one-to-one | FK kèm UNIQUE ở phía phù hợp | chỉ FK chưa giới hạn tối đa 1 |
| many-to-many | bảng nối với key cặp | thêm row và join nhưng giữ integrity |

### Misconception check

**Đúng hay sai?** FK bắt buộc cha có ít nhất một child.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: kiểm tham chiếu từ child, không kiểm số child tối thiểu.

</details>

**Đúng hay sai?** Snapshot là dữ liệu sai chuẩn hóa phải xóa.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: giá trị lịch sử và hiện tại là hai fact khác nhau.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** entity và cardinality.

- **Working Developer — dùng khi làm việc:** DDL enforcement gaps.

- **Deep Dive — có thể quay lại sau:** lifecycle/history theo requirement.

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

## 7. Khi nào KHÔNG dùng

Không thiết kế table theo mỗi màn hình UI. Không tách địa chỉ snapshot thành entity dùng chung nếu việc sửa địa chỉ làm đổi đơn cũ ngoài ý muốn.

## 8. Production notes & scale check

Gate kiểm quan hệ/cặp trùng/FK và dữ liệu snapshot với fixture nhỏ; sample DDL gốc chưa seed nên verifier thêm fixture riêng. Quy tắc 1..n và immutable history cần application/transaction/permissions bổ sung nếu nghiệp vụ yêu cầu.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

So entity/value Module 06: ShippingAddress dùng chung và ShippingAddress snapshot có ownership khác nhau thế nào? Chọn schema khi khách đổi địa chỉ sau khi mua.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. FK nằm ở phía nào?
2. 1-1 cần thêm ràng buộc nào?
3. Snapshot có tự bất biến không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi xác định được entity.
- [ ] Tôi phân biệt 1-1, 1-n, n-n.
- [ ] Tôi dùng associative entity.
- [ ] Tôi mô hình optionality có chủ đích.
- [ ] Tôi hiểu snapshot lịch sử.
- [ ] Tôi thiết kế từ domain không từ màn hình.

Điều hướng:

- Bài trước: [View, procedure, function và trigger](./13-view-stored-procedure-function-trigger.md)
- Bài tiếp theo: [Chuẩn hóa 1NF, 2NF, 3NF và BCNF](./15-chuan-hoa-1nf-2nf-3nf-bcnf.md)
