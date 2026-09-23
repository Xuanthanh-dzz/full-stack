# View, stored procedure, function và trigger

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- View, procedure, function và trigger đóng gói các kiểu hành vi database khác nhau.
- Chọn theo cách gọi, shape kết quả và side effect cần thiết.
- Trigger chạy trong transaction của lệnh DML và phải xử lý nhiều row.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- tạo view cho query ổn định;
- tạo stored procedure có parameter;
- tạo inline table-valued function;
- hiểu trigger chạy tự động theo DML;
- phân biệt abstraction với business logic;
- nhận ra rủi ro khi nhét quá nhiều logic vào database;
- chọn object phù hợp theo use case.

## 2. Bài toán mở đầu

### Trực giác 60 giây

View là công thức xem sổ; procedure là một công việc được gọi tên; function trả dữ liệu để ghép vào câu hỏi khác. Trigger là việc tự xảy ra sau thao tác, nên người gọi phải biết nó có thể thêm công hoặc làm lệnh thất bại.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| view | query definition dùng như nguồn dữ liệu | vActiveProducts |
| stored procedure | lệnh được gọi bằng EXEC | GetOrdersByCustomer |
| inline TVF | hàm trả rowset ghép được vào query | OrdersForCustomer |
| DML trigger | code tự chạy theo statement ghi | audit giá đổi |

### Ví dụ nhỏ — tính tay trước

Giá Keyboard đổi từ 1.000.000 lên 1.100.000 tạo một row audit. Một lệnh `UPDATE` tăng giá cả Keyboard và Mouse tạo hai row audit; chỉ đổi `Name` hoặc gán `Price = Price` không tạo audit theo điều kiện của sample.

Hệ thống cần:

- view danh sách active product;
- procedure tìm order theo customer;
- function trả order của một customer;
- audit khi price thay đổi.

SQL Server có nhiều programmable object, nhưng dùng sai sẽ làm architecture khó debug.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_13') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_13
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_13;
END;
GO

CREATE DATABASE CommerceLab08_13;
GO
USE CommerceLab08_13;
GO

CREATE TABLE dbo.Products
(
    ProductId int NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Name nvarchar(100) NOT NULL,
    Price decimal(19,4) NOT NULL,
    IsActive bit NOT NULL
);

CREATE TABLE dbo.PriceAudit
(
    AuditId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_PriceAudit PRIMARY KEY,
    ProductId int NOT NULL,
    OldPrice decimal(19,4) NOT NULL,
    NewPrice decimal(19,4) NOT NULL,
    ChangedAt datetime2(0) NOT NULL
        CONSTRAINT DF_PriceAudit_ChangedAt DEFAULT SYSUTCDATETIME()
);

CREATE TABLE dbo.Orders
(
    OrderId int NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    TotalAmount decimal(19,4) NOT NULL
);
GO

INSERT INTO dbo.Products VALUES
(1,N'Keyboard',1000000,1),
(2,N'Mouse',500000,0);

INSERT INTO dbo.Orders VALUES
(101,1,3000000),
(102,1,1000000),
(201,2,9000000);
GO

CREATE VIEW dbo.vActiveProducts
AS
    SELECT ProductId, Name, Price
    FROM dbo.Products
    WHERE IsActive = 1;
GO

CREATE PROCEDURE dbo.GetOrdersByCustomer
    @CustomerId int
AS
BEGIN
    SET NOCOUNT ON;

    SELECT OrderId, CustomerId, TotalAmount
    FROM dbo.Orders
    WHERE CustomerId = @CustomerId
    ORDER BY OrderId;
END;
GO

CREATE FUNCTION dbo.OrdersForCustomer
(
    @CustomerId int
)
RETURNS TABLE
AS
RETURN
(
    SELECT OrderId, CustomerId, TotalAmount
    FROM dbo.Orders
    WHERE CustomerId = @CustomerId
);
GO

CREATE TRIGGER dbo.trg_Products_PriceAudit
ON dbo.Products
AFTER UPDATE
AS
BEGIN
    SET NOCOUNT ON;

    INSERT INTO dbo.PriceAudit
    (
        ProductId,
        OldPrice,
        NewPrice
    )
    SELECT
        i.ProductId,
        d.Price,
        i.Price
    FROM inserted AS i
    INNER JOIN deleted AS d
        ON d.ProductId = i.ProductId
    WHERE i.Price <> d.Price;
END;
GO

SELECT * FROM dbo.vActiveProducts;

EXEC dbo.GetOrdersByCustomer @CustomerId = 1;

SELECT *
FROM dbo.OrdersForCustomer(1);

UPDATE dbo.Products
SET Price = 1100000
WHERE ProductId = 1;

SELECT *
FROM dbo.PriceAudit;
GO
```

### Walkthrough — execution / state / cost

1. DDL tạo object ở server; GO tách batch vì các CREATE object có yêu cầu vị trí trong batch.
2. View/TVF đọc dữ liệu hiện tại khi query; procedure nhận parameter CustomerId.
3. UPDATE tạo inserted/deleted rowsets, trigger join theo ProductId rồi ghi các giá thực sự khác.
4. Audit write cùng transaction: rollback UPDATE cũng rollback audit. Storage/log tăng theo số thay đổi; trigger làm tăng latency statement dù client không gọi riêng.

### Mini-check

UPDATE không match row nào: trigger có thể vẫn được gọi không, code set-based có cần giả định một row không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### View

View lưu query definition.

Nó không mặc định lưu copy data.

### Stored procedure

Procedure là entry point database có parameter và nhiều statement.

### Inline table-valued function

Trả rowset và có thể compose trong query.

### Trigger

Trigger chạy tự động khi event xảy ra.

DML trigger phải xử lý **set nhiều row**, không giả định một row.

`inserted` và `deleted` có thể chứa nhiều row.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| view/inline TVF | rowset composable | không tự là bản sao dữ liệu |
| procedure | entry point nhiều statement | contract result và quyền EXEC cần rõ |
| trigger | side effect tự động cùng DML | khó thấy, tránh khi constraint đơn giản đủ |

### Misconception check

**Đúng hay sai?** Trigger chạy một lần cho mỗi row như vòng lặp C#.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: DML trigger xử lý statement, inserted/deleted có thể nhiều row.

</details>

**Đúng hay sai?** Audit trong trigger vẫn còn sau rollback.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai với audit table trong cùng transaction của sample.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** bốn loại object.

- **Working Developer — dùng khi làm việc:** set-based trigger và rollback.

- **Deep Dive — có thể quay lại sau:** permissions/deployment theo boundary.

### Logic nằm đâu?

Cân nhắc:

- ownership;
- testability;
- deployment;
- performance;
- nhiều application dùng chung DB;
- security.

### Trigger cho audit

Trigger bảo vệ audit ngay cả khi nhiều writer.

Nhưng trigger ẩn side effect khỏi application, nên phải document rõ.

### View và security

Có thể grant SELECT trên view thay vì table, giảm exposure column.

## 6. Lỗi thường gặp

### Trigger viết cho một row

Nếu UPDATE nhiều row, `inserted` chứa nhiều row.

### Procedure trả SELECT *

Contract dễ vỡ khi schema đổi.

### Scalar UDF trong hot query

Có thể gây overhead tùy version/plan; cần đo.

### Nhét toàn bộ domain logic vào stored procedure

Dễ làm application architecture khó test/maintain nếu team không chủ đích.

## 7. Khi nào KHÔNG dùng

Không dùng trigger để gửi HTTP/email hoặc giấu workflow dài. Không tạo procedure cho mọi SELECT nếu quyền và ownership không cần.

## 8. Production notes & scale check

Gate gọi procedure/TVF, kiểm view, multi-row audit, no-op và rollback audit. Price NOT NULL nên so <> đủ trong sample; nullable giá cần predicate phát hiện NULL transition riêng. Caller cần biết transaction ownership khi procedure có BEGIN/COMMIT.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Tạo view order summary.

### Bài 2

Tạo procedure search product theo min/max price.

### Bài 3

Tạo inline TVF trả paid order.

### Bài 4

UPDATE nhiều product cùng lúc và chứng minh trigger audit đúng nhiều row.

### Bài 5

Viết ADR ngắn: logic nào nên ở application, logic nào ở DB cho project của bạn.

## 10. Bài tập tích hợp liên module — Judgment

So adapter/policy Module 06: đặt rule audit ở DB giúp nhiều writer thế nào và làm test/deploy khó hơn ở đâu? Chọn theo người sở hữu dữ liệu, không theo sở thích syntax.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. View lưu gì?
2. Trigger audit thuộc transaction nào?
3. TVF khác procedure về composition thế nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi tạo được view.
- [ ] Tôi tạo được stored procedure.
- [ ] Tôi hiểu inline TVF.
- [ ] Tôi viết trigger set-based.
- [ ] Tôi hiểu trigger tạo side effect ẩn.
- [ ] Tôi chọn programmable object theo trade-off.

Điều hướng:

- Bài trước: [Window function](./12-window-function.md)
- Bài tiếp theo: [Mô hình ER và quan hệ](./14-mo-hinh-er-va-quan-he.md)
