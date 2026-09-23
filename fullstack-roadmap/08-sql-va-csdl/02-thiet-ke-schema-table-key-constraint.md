# Thiết kế schema, table, key và constraint

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Constraint đặt quy tắc dữ liệu ngay tại nơi mọi writer phải đi qua.
- Dùng PK/FK/UNIQUE/CHECK cho invariant biểu diễn được trong schema.
- Constraint không tự suy ra quy tắc nghiệp vụ chưa được khai báo.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng schema để tổ chức object;
- thiết kế primary key và foreign key;
- dùng UNIQUE, CHECK, DEFAULT và NOT NULL;
- hiểu candidate key và surrogate key;
- tạo relationship one-to-many;
- để database bảo vệ invariant thay vì chỉ tin application.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Số đơn phải duy nhất, khách được ghi trên đơn phải có trong sổ khách, giá không được âm. Dù người nhập dùng form hay script, cửa kiểm của database vẫn áp dụng cùng quy tắc.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| schema | namespace chứa object trong database | sales, catalog |
| foreign key | khóa tham chiếu row hợp lệ ở bảng khác | Orders.CustomerId |
| UNIQUE | không cho các key trùng theo quy tắc so sánh | Email/Sku |
| CHECK | từ chối row khi biểu thức là FALSE | Price>=0 |
| DEFAULT | giá trị dùng khi INSERT bỏ qua cột | CreatedAt |

### Ví dụ nhỏ — tính tay trước

Có customer ID 1. Đơn hàng tham chiếu ID 1 được nhận; đơn tham chiếu ID 99 bị foreign key chặn vì khách này chưa tồn tại. Giá -1 bị `CHECK` chặn. `DEFAULT` không thay giá trị `NULL` được truyền tường minh vào cột `NOT NULL`.

Hệ thống bán hàng cần bảo đảm:

- email customer không trùng;
- SKU không trùng;
- giá sản phẩm không âm;
- order phải thuộc customer tồn tại;
- status chỉ nhận một tập giá trị hợp lệ.

Nếu chỉ kiểm tra trong C#, một script SQL hoặc service khác vẫn có thể ghi dữ liệu sai.

Constraint đặt invariant ngay tại database.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. DDL tạo schemas, bảng và constraints ở server.
2. INSERT customer/product chạy trước order để FK có row đích.
3. Mỗi write kiểm NOT NULL, key và CHECK; vi phạm làm statement lỗi.
4. Constraints giữ state trong metadata/index, FK cần tìm key cha. UNIQUE thường có index hỗ trợ; foreign key không tự tạo index phía child trong SQL Server.

### Mini-check

Nếu muốn mỗi customer có ít nhất một order, FK từ Orders sang Customers đã đủ chưa?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| validation application | phản hồi sớm, thông báo theo UI | writer khác có thể bỏ qua |
| database constraint | áp dụng cho mọi writer chịu constraint | có cost write và lỗi cần ánh xạ |
| trigger | xử lý quy tắc phức tạp hơn | side effect khó thấy, không thay constraint đơn giản |

### Misconception check

**Đúng hay sai?** CHECK Price>=0 tự cấm NULL.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: CHECK không từ chối UNKNOWN; cần NOT NULL nếu giá bắt buộc.

</details>

**Đúng hay sai?** Có FK nghĩa là luôn có index trên cột child.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: cần thiết kế index child theo workload riêng.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** PK/FK/UQ.

- **Working Developer — dùng khi làm việc:** NULL/default và negative tests.

- **Deep Dive — có thể quay lại sau:** index child và migration constraints.

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

## 7. Khi nào KHÔNG dùng

Không bật cascade delete chỉ vì tiện. Không thay tất cả validation bằng trigger; PK/FK/CHECK diễn đạt được thì dùng chúng trước.

## 8. Production notes & scale check

Kiểm lỗi duplicate, giá âm, FK không tồn tại và DEFAULT trong lab. Collation — quy tắc so sánh chuỗi — ảnh hưởng uniqueness hoa/thường; policy email/SKU cần rõ. Constraint trusted không bảo vệ rule chưa viết, ví dụ trim chuỗi trắng là bài tập riêng.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

So invariant constructor Module 06: nhiều service hoặc script ghi cùng DB thì guard C# còn thiếu lớp nào? Chọn hai rule nên đặt ở DB và một rule cần application.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. CHECK xử lý UNKNOWN ra sao?
2. DEFAULT chạy khi nào?
3. FK bảo vệ phía nào của quan hệ?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi dùng được schema.
- [ ] Tôi phân biệt PK/FK/UQ.
- [ ] Tôi dùng CHECK/DEFAULT/NOT NULL.
- [ ] Tôi hiểu natural và surrogate key.
- [ ] Tôi không bật cascade delete tùy tiện.
- [ ] Tôi đặt invariant quan trọng trong database.

Điều hướng:

- Bài trước: [Mô hình quan hệ và cài đặt SQL Server](./01-mo-hinh-quan-he-va-cai-dat-sql-server.md)
- Bài tiếp theo: [Kiểu dữ liệu và NULL](./03-kieu-du-lieu-va-null.md)
