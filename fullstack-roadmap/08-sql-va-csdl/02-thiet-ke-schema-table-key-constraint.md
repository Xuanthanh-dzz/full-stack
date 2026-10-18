# Thiết kế schema, table, key và constraint

> **Last verified:** 2026-10-18
>
> **Baseline:** SQL Server 2025 (17.0.x) · T-SQL · sqlcmd (mssql-tools18) · Docker image `mcr.microsoft.com/mssql/server:2025-latest`
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** SQL Server major/CU đổi hành vi constraint hoặc thông báo lỗi, đổi lab/schema, CI `verify-module-08` fail

## TL;DR

- Constraint là luật dữ liệu đặt trong database — `PRIMARY KEY`, `FOREIGN KEY`, `UNIQUE`, `CHECK`, `DEFAULT`, `NOT NULL` — được engine kiểm tra ở mọi lần ghi.
- Dùng cho invariant mà mọi writer phải tuân theo: định danh, quan hệ giữa các table và miền giá trị, thay vì chỉ tin code ứng dụng.
- Trade-off: mỗi lần ghi tốn thêm chi phí kiểm tra, đổi luật cần migration; luật nghiệp vụ phức tạp hoặc hay đổi không nên nhồi vào constraint.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- dùng schema để gom table theo domain;
- thiết kế primary key, foreign key và composite key cho bảng nối;
- dùng `UNIQUE`, `CHECK`, `DEFAULT`, `NOT NULL` và đặt tên constraint theo quy ước;
- phân biệt natural key (candidate key) với surrogate key;
- đọc lỗi `2627`, `547`, `515` và chỉ ra constraint nào đã chặn;
- giải thích vì sao invariant quan trọng phải nằm ở database, không chỉ ở application;
- nhận ra hai chi phí ẩn: cột foreign key không tự có index, constraint bật bằng `WITH NOCHECK` không được tin.

## 2. Bài toán mở đầu

Hệ thống bán hàng cần bảo đảm:

- email khách hàng không trùng;
- SKU sản phẩm không trùng;
- giá sản phẩm không âm;
- đơn hàng phải thuộc một khách hàng có thật;
- trạng thái đơn chỉ nhận một tập giá trị hợp lệ;
- một sản phẩm chỉ xuất hiện một dòng trong mỗi đơn.

Nếu chỉ kiểm tra trong C#, mọi luật trên phụ thuộc vào việc **mọi** writer đều gọi đúng đoạn code đó. Một script import, một service khác, hay một câu `INSERT` chạy tay vẫn ghi được dữ liệu sai. Ở Module 06 bạn đã đặt invariant vào constructor để object không bao giờ ở trạng thái sai; constraint làm điều tương tự cho dữ liệu trong table.

### Trực giác 60 giây

Constraint giống bảng nội quy dán ngay cửa kho: bất kể ai mang hàng tới — ứng dụng web, job chạy đêm hay người quản trị gõ lệnh — thủ kho đều kiểm tra cùng một bộ luật trước khi cất. Validation trong C# chỉ giống nhân viên ở một quầy: chặn được hàng đi qua quầy đó, không chặn được cửa sau. Dòng chảy là: câu `INSERT`/`UPDATE` → engine kiểm tra các constraint liên quan tới hàng → ghi, hoặc từ chối cả câu lệnh. Không có constraint, mỗi writer phải tự kiểm tra y hệt nhau, và chỉ một writer quên là dữ liệu bẩn.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| schema | không gian tên gom object theo domain, cũng là ranh giới phân quyền | `sales`, `catalog` |
| constraint | luật engine kiểm tra mỗi lần ghi | `CK_Products_Price` |
| natural key (candidate key) | giá trị có nghĩa nghiệp vụ và phải duy nhất | `Email`, `Sku` |
| surrogate key | khóa nhân tạo, không mang nghĩa nghiệp vụ | `CustomerId` tự tăng |
| foreign key | cột phải khớp primary key của table khác | `Orders.CustomerId` |
| referential integrity (toàn vẹn tham chiếu) | không có dòng con trỏ tới dòng cha không tồn tại | đơn hàng luôn có khách |
| composite key | khóa gồm nhiều cột | `(OrderId, ProductId)` |

### Ví dụ nhỏ — tính tay trước

`sales.Customers` đang có một khách `an@example.com` (`CustomerId = 1`). Chạy lần lượt ba câu:

```text
(a) thêm khách email binh@example.com
(b) thêm khách email an@example.com
(c) thêm đơn cho CustomerId = 999
```

Dự đoán: câu nào thành công, câu nào bị chặn bởi constraint nào? Sau ba câu, `Customers` có mấy dòng và `Orders` có mấy dòng?

Đáp án để đối chiếu: (a) thành công; (b) bị `UNIQUE` chặn; (c) bị `FOREIGN KEY` chặn. Kết quả: `Customers` 2 dòng, `Orders` 0 dòng — câu bị từ chối không ghi gì cả.

## 3. Lời giải chạy được

Dùng SQL Server 2025 đã dựng ở [bài 01](./01-mo-hinh-quan-he-va-cai-dat-sql-server.md). Lưu script thành `lab02.sql`, chép vào container rồi chạy với `sqlcmd ... -C -b -i /tmp/lab02.sql` như bài trước:

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

-- Bảng nối: một dòng = một sản phẩm trong một đơn; khóa chính gồm hai cột.
CREATE TABLE sales.OrderItems
(
    OrderId bigint NOT NULL,
    ProductId int NOT NULL,
    Quantity int NOT NULL,
    UnitPrice decimal(19,4) NOT NULL,

    CONSTRAINT PK_OrderItems
        PRIMARY KEY (OrderId, ProductId),

    CONSTRAINT FK_OrderItems_Orders
        FOREIGN KEY (OrderId)
        REFERENCES sales.Orders(OrderId),

    CONSTRAINT FK_OrderItems_Products
        FOREIGN KEY (ProductId)
        REFERENCES catalog.Products(ProductId),

    CONSTRAINT CK_OrderItems_Quantity
        CHECK (Quantity > 0)
);
GO

INSERT INTO sales.Customers (FullName, Email)
VALUES (N'Nguyễn An', 'an@example.com');

INSERT INTO catalog.Products (Sku, Name, Price)
VALUES ('KB-01', N'Bàn phím', 750000);

INSERT INTO sales.Orders (CustomerId, Status)
VALUES (1, 'Pending');

INSERT INTO sales.OrderItems (OrderId, ProductId, Quantity, UnitPrice)
VALUES (1, 1, 2, 750000);
GO

-- Thử ghi dữ liệu sai; mỗi lỗi được bắt lại và ghi nhận thay vì dừng script.
DECLARE @Attempts TABLE
(
    Attempt nvarchar(40) NOT NULL,
    ErrorNumber int NOT NULL,
    ErrorMessage nvarchar(400) NOT NULL
);

BEGIN TRY
    INSERT INTO sales.Customers (FullName, Email) VALUES (N'Giả mạo', 'an@example.com');
END TRY
BEGIN CATCH
    INSERT INTO @Attempts VALUES (N'Email trùng', ERROR_NUMBER(), ERROR_MESSAGE());
END CATCH;

BEGIN TRY
    INSERT INTO catalog.Products (Sku, Name, Price) VALUES ('BAD-01', N'Giá âm', -5000);
END TRY
BEGIN CATCH
    INSERT INTO @Attempts VALUES (N'Giá âm', ERROR_NUMBER(), ERROR_MESSAGE());
END CATCH;

BEGIN TRY
    INSERT INTO sales.Orders (CustomerId, Status) VALUES (999, 'Pending');
END TRY
BEGIN CATCH
    INSERT INTO @Attempts VALUES (N'Khách không tồn tại', ERROR_NUMBER(), ERROR_MESSAGE());
END CATCH;

BEGIN TRY
    INSERT INTO sales.Orders (CustomerId, Status) VALUES (1, 'Lost');
END TRY
BEGIN CATCH
    INSERT INTO @Attempts VALUES (N'Status lạ', ERROR_NUMBER(), ERROR_MESSAGE());
END CATCH;

BEGIN TRY
    INSERT INTO sales.Customers (Email) VALUES ('noname@example.com');
END TRY
BEGIN CATCH
    INSERT INTO @Attempts VALUES (N'Thiếu tên', ERROR_NUMBER(), ERROR_MESSAGE());
END CATCH;

BEGIN TRY
    INSERT INTO sales.OrderItems (OrderId, ProductId, Quantity, UnitPrice) VALUES (1, 1, 1, 750000);
END TRY
BEGIN CATCH
    INSERT INTO @Attempts VALUES (N'Trùng dòng trong đơn', ERROR_NUMBER(), ERROR_MESSAGE());
END CATCH;

SELECT Attempt, ErrorNumber, ErrorMessage
FROM @Attempts;

-- Không dòng sai nào lọt vào: số hàng vẫn như trước khi thử.
SELECT
    (SELECT COUNT(*) FROM sales.Customers) AS Customers,
    (SELECT COUNT(*) FROM catalog.Products) AS Products,
    (SELECT COUNT(*) FROM sales.Orders) AS Orders,
    (SELECT COUNT(*) FROM sales.OrderItems) AS OrderItems;

SELECT
    o.OrderId,
    c.FullName,
    o.Status,
    p.Name AS ProductName,
    oi.Quantity,
    p.IsActive
FROM sales.Orders AS o
JOIN sales.Customers AS c
    ON c.CustomerId = o.CustomerId
JOIN sales.OrderItems AS oi
    ON oi.OrderId = o.OrderId
JOIN catalog.Products AS p
    ON p.ProductId = oi.ProductId;
GO
```

Output (SQL Server 2025, đã lược dòng thông báo):

```text
Attempt              | ErrorNumber | ErrorMessage
---------------------+-------------+-------------------------------------------------------------
Email trùng          | 2627        | Violation of UNIQUE KEY constraint 'UQ_Customers_Email'. Cannot insert duplicate key in object 'sales.Customers'. The duplicate key value is (an@example.com).
Giá âm               | 547         | The INSERT statement conflicted with the CHECK constraint "CK_Products_Price". The conflict occurred in database "CommerceLab08_02", table "catalog.Products", column 'Price'.
Khách không tồn tại  | 547         | The INSERT statement conflicted with the FOREIGN KEY constraint "FK_Orders_Customers". The conflict occurred in database "CommerceLab08_02", table "sales.Customers", column 'CustomerId'.
Status lạ            | 547         | The INSERT statement conflicted with the CHECK constraint "CK_Orders_Status". The conflict occurred in database "CommerceLab08_02", table "sales.Orders", column 'Status'.
Thiếu tên            | 515         | Cannot insert the value NULL into column 'FullName', table 'CommerceLab08_02.sales.Customers'; column does not allow nulls. INSERT fails.
Trùng dòng trong đơn | 2627        | Violation of PRIMARY KEY constraint 'PK_OrderItems'. Cannot insert duplicate key in object 'sales.OrderItems'. The duplicate key value is (1, 1).

Customers | Products | Orders | OrderItems
----------+----------+--------+-----------
1         | 1        | 1      | 1

OrderId | FullName  | Status  | ProductName | Quantity | IsActive
--------+-----------+---------+-------------+----------+---------
1       | Nguyễn An | Pending | Bàn phím    | 2        | 1
```

### Walkthrough — execution / state / cost

1. **`CREATE SCHEMA sales`, `catalog`:** tạo hai không gian tên. Table được gọi bằng tên đầy đủ `sales.Orders`, nên hai domain có thể có table trùng tên mà không lẫn.
2. **`CREATE TABLE` với constraint đặt tên:** định nghĩa và tên constraint được lưu vào system catalog. `PRIMARY KEY` mặc định tạo một clustered index trên cột khóa; `FOREIGN KEY` **không** tạo index nào.
3. **Bốn `INSERT` hợp lệ:** các `DEFAULT` tự điền `CreatedAt`, `OrderedAt` và `IsActive = 1` — output cuối cho thấy `IsActive` là 1 dù ta không truyền.
4. **Sáu `INSERT` sai:** với mỗi hàng, engine kiểm tra các constraint liên quan; vi phạm bất kỳ cái nào thì **cả câu lệnh** bị hủy và không ghi gì. Khối `BEGIN CATCH` chỉ ghi lại `ERROR_NUMBER()` và `ERROR_MESSAGE()`; tên trong thông báo chính là tên ta đã đặt.
5. **Đếm lại:** vẫn 1/1/1/1 — không dòng rác nào lọt vào.
6. **Cost:** kiểm tra `UNIQUE`/`PRIMARY KEY` là một lần tìm trong index của chính table; kiểm tra `FOREIGN KEY` là một lần tìm trong primary key của table cha. Với một dòng thì rất rẻ; với nạp hàng triệu dòng thì cộng dồn thành chi phí đáng kể.

### Mini-check

Bây giờ chạy `DELETE FROM sales.Customers WHERE CustomerId = 1;`. Điều gì xảy ra, constraint nào quyết định, và vì sao?

## 4. Cơ chế hoạt động

### Sơ đồ quan hệ của lab

```text
sales.Customers (PK CustomerId, UQ Email)
       │ 1
       │
       │ n
sales.Orders (PK OrderId, FK CustomerId, CK Status)
       │ 1
       │
       │ n
sales.OrderItems (PK OrderId + ProductId)
       │ n
       │
       │ 1
catalog.Products (PK ProductId, UQ Sku, CK Price)
```

`Customers–Orders` là quan hệ một–nhiều. `Orders–Products` là nhiều–nhiều: một đơn có nhiều sản phẩm, một sản phẩm nằm trong nhiều đơn. Bảng nối `OrderItems` hiện thực quan hệ đó (bài [14](./14-mo-hinh-er-va-quan-he.md) mô hình hóa đầy đủ).

### Primary key và composite key

Primary key định danh duy nhất, không NULL và nên ổn định. Ở `OrderItems`, tính duy nhất đến từ **tổ hợp** `(OrderId, ProductId)`: trong một đơn, mỗi sản phẩm chỉ có một dòng; mua thêm thì tăng `Quantity`. Dòng `(1, 1)` thứ hai bị `PK_OrderItems` chặn với lỗi `2627`.

### Foreign key và toàn vẹn tham chiếu

`FK_Orders_Customers` chặn hai chiều:

- thêm đơn trỏ tới khách không tồn tại (`CustomerId = 999`) → lỗi `547`;
- xóa khách đang có đơn → cũng lỗi `547`, vì mặc định là `NO ACTION`.

Có thể đổi bằng referential action như `ON DELETE CASCADE` hoặc `ON DELETE SET NULL`, nhưng không bật theo thói quen: xóa khách kéo theo toàn bộ đơn lịch sử thường là bug nghiệp vụ.

### UNIQUE, CHECK, DEFAULT, NOT NULL

- `UNIQUE (Email)`: bảo vệ natural key dù primary key là surrogate.
- `CHECK (Price >= 0)`: luật miền giá trị, bị kiểm tra bất kể nguồn ghi.
- `DEFAULT SYSUTCDATETIME()`: giá trị khi câu `INSERT` không truyền cột đó.
- `NOT NULL`: cột bắt buộc; thiếu `FullName` → lỗi `515`.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Validation trong application (C#) | chỉ chặn dữ liệu đi qua đúng code path đó | phản hồi sớm, thông báo thân thiện; không bảo vệ khi có writer khác |
| Constraint trong database | engine kiểm tra mọi lần ghi, bất kể nguồn | lớp bảo vệ cuối cho invariant đơn giản, ổn định; không hợp với luật nhiều bước hoặc hay đổi |
| Trigger (bài 13) | code chạy kèm mỗi lần ghi, có thể đọc nhiều table | linh hoạt nhưng ẩn logic, khó test và debug; chỉ dùng khi constraint không diễn tả được |

Thực tế dùng **cả hai** lớp đầu: validation ở application để báo lỗi sớm và thân thiện, constraint ở database để không gì vượt qua được.

### Misconception check

**Đúng hay sai?** `UNIQUE` và `PRIMARY KEY` là một, chỉ khác tên.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. Mỗi table chỉ có một primary key và nó không cho NULL; có thể có nhiều `UNIQUE`, và `UNIQUE` cho phép NULL (SQL Server chỉ cho một NULL — bài [03](./03-kieu-du-lieu-va-null.md)).

</details>

**Đúng hay sai?** Khai báo `FOREIGN KEY` thì SQL Server tự tạo index cho cột đó.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. Sau lab, `sys.indexes` của `sales.Orders` chỉ có `PK_Orders` (clustered, trên `OrderId`). Cột `CustomerId` không có index; join theo khách hoặc xóa khách sẽ phải quét `Orders`.

</details>

**Đúng hay sai?** Đã validate trong C# thì constraint trong database là thừa.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. Validation C# chỉ bảo vệ code path của nó; script, service khác, import hoặc bug trong code đều ghi thẳng vào database.

</details>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** primary key, foreign key, `UNIQUE`, `CHECK`, `NOT NULL`; đọc được lỗi `2627/547/515`.
- **Working Developer — dùng khi làm việc:** đặt tên constraint, surrogate key + `UNIQUE` trên natural key, composite key cho bảng nối, index cho cột foreign key.
- **Deep Dive — có thể quay lại sau:** constraint trusted/untrusted, referential action, thêm constraint vào table đã có dữ liệu.

Bài trước: [Mô hình quan hệ và cài đặt SQL Server](./01-mo-hinh-quan-he-va-cai-dat-sql-server.md). Liên hệ: [Design by contract và invariant](../06-oop-va-thiet-ke/13-design-by-contract-va-invariant.md) — constraint là invariant ở tầng dữ liệu.

### Natural key và surrogate key

- Natural key: `Email`, `Sku`, mã số thuế — có nghĩa nghiệp vụ, có thể **đổi**.
- Surrogate key: `CustomerId`, `ProductId` — nhỏ, ổn định, không phụ thuộc thay đổi nghiệp vụ.

Cách phổ biến: surrogate key làm primary key, đặt `UNIQUE` trên natural key. Khách đổi email thì chỉ sửa một cột; mọi foreign key trỏ tới `CustomerId` không đổi.

### Quy ước đặt tên constraint

```text
PK_  primary key       FK_  foreign key       UQ_  unique
CK_  check             DF_  default
```

Nếu không đặt tên, SQL Server tự sinh tên dạng `UQ__Customer__A9D10534...`. Thông báo lỗi và script migration khi đó rất khó đọc.

### Đào sâu (có thể quay lại sau)

- **Constraint untrusted:** bật lại một foreign key bằng `ALTER TABLE ... WITH NOCHECK CHECK CONSTRAINT ...` không kiểm tra dữ liệu cũ, và `sys.foreign_keys.is_not_trusted` thành `1`. Optimizer không dựa vào constraint chưa được tin. `WITH CHECK CHECK CONSTRAINT` kiểm tra toàn bộ dữ liệu và đưa về `0`.
- **Primary key và index:** primary key mặc định là clustered index — dữ liệu table được sắp theo khóa (bài [17](./17-index-btree-clustered-nonclustered.md)).
- **Phương ngữ:** cú pháp constraint gần như chuẩn SQL; khác biệt nằm ở tên tự sinh, thông báo lỗi và việc `UNIQUE` xử lý NULL.

## 6. Lỗi thường gặp

### Khai báo foreign key nhưng quên index cho nó

Constraint đúng, nhưng join `Orders` theo `CustomerId` hoặc xóa một khách phải quét toàn bộ `Orders`. Tạo index cho cột foreign key khi access pattern cần (bài [17](./17-index-btree-clustered-nonclustered.md)).

### Để engine tự đặt tên constraint

Lỗi `Violation of UNIQUE KEY constraint 'UQ__Customer__A9D10534...'` không nói lên nghiệp vụ, và migration phải dò tên ngẫu nhiên khác nhau giữa các môi trường.

### Bật lại constraint bằng `WITH NOCHECK`

Nhanh, nhưng dữ liệu cũ có thể vi phạm và constraint thành untrusted. Làm sạch dữ liệu rồi dùng `WITH CHECK`.

### Dùng `varchar` cho tên tiếng Việt

Tên người/sản phẩm cần `nvarchar`; `varchar` với collation mặc định làm mất dấu.

### Để mọi column nullable

Nullable phải phản ánh nghĩa nghiệp vụ “có thể chưa biết”, không phải để `INSERT` dễ hơn.

## 7. Khi nào KHÔNG dùng

- **Luật nghiệp vụ hay đổi hoặc nhiều bước** (“khách VIP được giảm 15% nếu mua trên 3 món trong tháng”): đặt ở application/domain; constraint chỉ dành cho invariant ổn định.
- **`CHECK (Status IN (...))` cho danh sách lớn hoặc hay thêm giá trị:** dùng table tra cứu `OrderStatuses` + foreign key, thêm giá trị không cần sửa schema.
- **`ON DELETE CASCADE` cho dữ liệu lịch sử:** đơn hàng, hóa đơn phải giữ lại; chặn xóa hoặc dùng trạng thái thay vì xóa lây.
- **Natural key dễ đổi làm primary key:** email, số điện thoại — dùng surrogate key.

Tín hiệu đang dùng sai: phải `ALTER` constraint mỗi lần nghiệp vụ đổi, hoặc constraint cần đọc nhiều table để quyết định. Phương án đơn giản hơn: validation ở application cộng một constraint tối thiểu ở database. Câu hỏi quyết định: luật này có đúng với **mọi** writer, ở **mọi** thời điểm, và diễn tả được trên một dòng không?

## 8. Production notes & scale check

- **Thêm constraint vào table đã có dữ liệu:** làm sạch dữ liệu vi phạm trước; tạo bằng `WITH CHECK` để constraint trusted; việc kiểm tra quét toàn table nên chạy trong cửa sổ bảo trì với table lớn.
- **Index cho foreign key:** thêm theo access pattern thật (join, xóa cha), không thêm đồng loạt theo cảm tính.
- **Bulk load:** kiểm tra constraint tốn chi phí khi nạp hàng triệu dòng; vẫn giữ constraint, chỉ tối ưu khi đã đo.
- **API:** bắt lỗi `2627`/`547` ở tầng data access và trả thông báo nghiệp vụ; không lộ nguyên message SQL cho người dùng.
- **Team 2–3 người:** primary key, foreign key, `UNIQUE`, `CHECK` cơ bản là đủ; trigger hoặc ràng buộc phức tạp chỉ khi có driver cụ thể.

## 9. Bài tập kỹ thuật

### Bài 1 — Danh mục sản phẩm

Thêm `catalog.Categories` và cột `CategoryId` cho `catalog.Products` với foreign key có tên theo quy ước.

**Gợi ý:** quyết định `CategoryId` là `NOT NULL` hay cho NULL dựa trên câu hỏi “sản phẩm có thể chưa có danh mục không?”.

### Bài 2 — SKU không rỗng

Thêm `CHECK` để `Sku` không là chuỗi rỗng sau khi bỏ khoảng trắng.

**Gợi ý:** `LEN(TRIM(Sku)) > 0`.

### Bài 3 — Debug xóa khách hàng

Chạy `DELETE FROM sales.Customers WHERE CustomerId = 1;`. Đọc lỗi, chỉ ra constraint đã chặn và đề xuất cách xử lý đúng nghiệp vụ.

**Gợi ý:** đơn hàng là dữ liệu lịch sử; cân nhắc trạng thái “ngừng hoạt động” thay vì xóa.

### Bài 4 — Index cho foreign key

Truy vấn `sys.indexes` để liệt kê index của `sales.Orders`, rồi tạo `IX_Orders_CustomerId` và chạy lại truy vấn.

**Gợi ý:** join `sys.indexes` với `sys.index_columns`; lọc bằng `OBJECT_ID(N'sales.Orders')`.

### Bài 5 — Surrogate hay natural?

Với tỉnh/thành (có mã bưu chính), sách (có ISBN) và người dùng (có username), chọn primary key và giải thích.

**Gợi ý:** hỏi “giá trị này có bao giờ đổi, có nhỏ gọn, có luôn tồn tại không?”.

## 10. Bài tập tích hợp liên module — Judgment

Cho hai luật: “giá bán không âm” và “mỗi khách chỉ mua tối đa 5 sản phẩm khuyến mãi mỗi tháng”. Với mỗi luật, chọn đặt ở constraint database, validation C# (Module 05–06), hay cả hai. Bảo vệ lựa chọn bằng: ai là writer, luật có đổi không, cần đọc bao nhiêu dữ liệu để quyết định, và trải nghiệm lỗi của người dùng.

**Tiêu chí:** nêu nơi luật được kiểm tra, điều gì xảy ra khi có writer thứ hai, cost mỗi lần ghi; không chấm theo số cơ chế được dùng.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vì sao dùng surrogate key làm primary key nhưng vẫn đặt `UNIQUE` trên email?
2. Dự đoán lỗi khi xóa một sản phẩm đang nằm trong `OrderItems`.
3. Vẽ sơ đồ bảng nối cho quan hệ “sinh viên — môn học — điểm”.
4. Nêu hai lý do một constraint đúng vẫn có thể làm hệ thống chậm.
5. Khi nào chọn table tra cứu thay vì `CHECK (... IN ...)`?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi tạo được schema, primary key, foreign key và composite key có tên rõ ràng.
- [ ] Tôi debug được lỗi `2627`, `547`, `515` và chỉ ra constraint đã chặn.
- [ ] Tôi giải thích được vì sao câu lệnh bị từ chối không ghi dữ liệu nào.
- [ ] Tôi kiểm tra được index trên cột foreign key bằng system catalog.
- [ ] Tôi chọn được nơi đặt luật: constraint, validation hay cả hai.

**Bài prerequisite:** [Mô hình quan hệ và cài đặt SQL Server](./01-mo-hinh-quan-he-va-cai-dat-sql-server.md)

**Bài tiếp theo:** [Kiểu dữ liệu và NULL](./03-kieu-du-lieu-va-null.md)
