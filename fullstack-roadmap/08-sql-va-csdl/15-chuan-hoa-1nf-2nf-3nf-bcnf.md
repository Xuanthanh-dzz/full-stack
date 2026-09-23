# Chuẩn hóa 1NF, 2NF, 3NF và BCNF

> **Last verified:** pending — chưa chạy lại gate retrofit  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Chuẩn hóa dùng phụ thuộc hàm để giảm dữ liệu lặp sai và anomaly.
- Tách fact theo key xác định nó, kiểm khả năng ghép lại đúng.
- Không suy normal form chỉ từ vài row mẫu hoặc đếm số table.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích functional dependency;
- nhận ra repeating group và update anomaly;
- hiểu trực giác 1NF, 2NF, 3NF và BCNF;
- tách schema theo dependency;
- biết chuẩn hóa không đồng nghĩa tách table tối đa;
- phân biệt duplication lỗi với historical snapshot có chủ đích.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Tên người quản lý nhóm sản phẩm xuất hiện trong mọi dòng bán hàng. Khi đổi người, sửa sót một dòng làm sổ tự mâu thuẫn. Tách thông tin nhóm thành một nơi giữ fact giúp tránh lỗi ấy.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| functional dependency | cùng X thì bắt buộc cùng Y trong mọi state hợp lệ | CategoryId→ManagerEmail |
| candidate key | tập cột tối thiểu định danh row | CustomerId hoặc Email |
| superkey | tập cột định danh row, có thể dư | CustomerId,FullName |
| anomaly | lỗi cập nhật/thêm/xóa do fact bị trộn | đổi manager nhiều nơi |

### Ví dụ nhỏ — tính tay trước

OrderItems key(OrderId,ProductId). ProductName chỉ phụ thuộc ProductId nên để trong Products nếu đó là tên hiện tại. UnitPrice tại lúc bán phụ thuộc cả giao dịch, không buộc giống giá catalog hôm nay.

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

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. Liệt kê dependencies từ quy tắc nghiệp vụ, không chỉ từ dữ liệu tình cờ hiện có.
2. Tách Customer/Category/Product/Order/Items theo key và nối bằng FK.
3. Join sample tái tạo hai dòng hàng, cùng thông tin khách và category, tổng tiền2200000.
4. Normalized writes giảm số nơi sửa fact nhưng reads có thể thêm join/index. Server không tự chứng minh3NF/BCNF khi CREATE TABLE thành công.

### Mini-check

ProductId→CategoryId và CategoryId→ManagerEmail: lưu ManagerEmail trong Products gây update anomaly nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

Với mỗi phụ thuộc hàm không tầm thường X → Y, X phải là **superkey** (tập thuộc tính xác định duy nhất row). Candidate key là superkey tối thiểu; BCNF không bắt determinant phải tối thiểu.

BCNF mạnh hơn 3NF ở một số dependency đặc biệt.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| 1NF/2NF | không nhóm lặp; non-prime phụ thuộc đầy đủ mọi candidate key | không chỉ nhìn primary key đã chọn |
| 3NF | với X→A không tầm thường: X là superkey hoặc A thuộc một candidate key | định nghĩa chặt hơn mẹo nhớ “không bắc cầu” |
| BCNF | mọi determinant của dependency không tầm thường là superkey | mạnh hơn3NF, decomposition có thể khó giữ mọi dependency |

### Misconception check

**Đúng hay sai?** Thêm surrogate primary key làm schema tự đạt3NF.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: các dependency nghiệp vụ cũ vẫn còn.

</details>

**Đúng hay sai?** BCNF bắt determinant phải là candidate key tối thiểu.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: yêu cầu superkey, có thể chứa thuộc tính dư.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** anomaly và dependency.

- **Working Developer — dùng khi làm việc:** candidate keys/lossless.

- **Deep Dive — có thể quay lại sau:** 3NF/BCNF formal khi cần.

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

## 7. Khi nào KHÔNG dùng

Không tách mọi field thành bảng riêng. Không bỏ historical price chỉ vì tên cột giống current price; trước hết xác định hai fact có cùng thời điểm/ngữ nghĩa không.

## 8. Production notes & scale check

Gate kiểm join fixture, keys và thay manager một nơi phản ánh các sản phẩm cùng nhóm. Normal forms cần reviewer xét dependency/lossless decomposition; dữ liệu seed nhỏ không chứng minh mọi state hợp lệ. Atomic value của1NF phụ thuộc domain được mô hình hóa, không cấm mọi kiểu JSON theo khẩu hiệu.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

So cohesion Module 06: fact nào đổi cùng nhau, fact nào có owner khác? Viết dependency trước khi đề xuất tách một table hiện tại.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Dependency đến từ đâu?
2. Candidate key khác superkey thế nào?
3. Join lại không sinh row giả nghĩa là gì?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi hiểu functional dependency.
- [ ] Tôi nhận ra update/insert/delete anomaly.
- [ ] Tôi giải thích được 1NF/2NF/3NF.
- [ ] Tôi biết BCNF mạnh hơn 3NF ở một số case.
- [ ] Tôi không chuẩn hóa máy móc.
- [ ] Tôi phân biệt duplication lỗi và snapshot lịch sử.

Điều hướng:

- Bài trước: [Mô hình ER và quan hệ](./14-mo-hinh-er-va-quan-he.md)
- Bài tiếp theo: [Denormalization và dữ liệu lịch sử](./16-denormalization-va-du-lieu-lich-su.md)

### Checkpoint sau cụm bài

- [Failure Lab](./failure-labs/03-rank.md)
- [Spaced Review](./reviews/review-03.md)
