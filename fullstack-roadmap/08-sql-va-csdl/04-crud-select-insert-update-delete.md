# CRUD: SELECT, INSERT, UPDATE, DELETE

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- CRUD là đọc, thêm, sửa và xóa row bằng các statement theo tập.
- Dùng predicate rõ và OUTPUT để quan sát thay đổi.
- SELECT xem trước không khóa tập row cho UPDATE sau; OUTPUT chưa phải bằng chứng transaction đã commit.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- đọc dữ liệu bằng SELECT;
- insert một hoặc nhiều row;
- update có điều kiện;
- delete có điều kiện;
- dùng OUTPUT để quan sát row thay đổi;
- tránh UPDATE/DELETE toàn bảng ngoài ý muốn;
- hiểu CRUD SQL khác CRUD HTTP.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một lệnh tăng giá có thể tác động cả nhóm sản phẩm. Trước khi bấm chạy, phải chỉ rõ nhóm nào và kiểm số row thực sự đổi; khác với vòng lặp sửa từng object trong RAM.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| predicate | điều kiện chọn row | WHERE Sku=... |
| DML | lệnh đọc/ghi dữ liệu theo ngữ cảnh bài | INSERT/UPDATE/DELETE |
| OUTPUT | rowset mô tả row bị tác động | inserted/deleted |
| soft delete | giữ row và đổi cờ/trạng thái | IsActive=0 |

### Ví dụ nhỏ — tính tay trước

Có KB750000,MS450000,MN5200000. UPDATE KB→790000; ngừng bán MN; DELETE MS. Cuối cùng còn KB active và MN inactive, không còn MS.

Admin cần:

- thêm product;
- xem product;
- đổi price;
- ngừng bán product.

Đây là CRUD:

```text
Create
Read
Update
Delete
```

Nhưng trong hệ thống thương mại, “delete” đôi khi phải là soft delete hoặc state transition để giữ lịch sử.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_04') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_04
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_04;
END;
GO

CREATE DATABASE CommerceLab08_04;
GO
USE CommerceLab08_04;
GO

CREATE TABLE dbo.Products
(
    ProductId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Sku varchar(40) NOT NULL
        CONSTRAINT UQ_Products_Sku UNIQUE,
    Name nvarchar(160) NOT NULL,
    Price decimal(19,4) NOT NULL
        CONSTRAINT CK_Products_Price CHECK (Price >= 0),
    IsActive bit NOT NULL
        CONSTRAINT DF_Products_IsActive DEFAULT 1
);
GO

INSERT INTO dbo.Products (Sku, Name, Price)
OUTPUT inserted.ProductId, inserted.Sku
VALUES
    ('KB-01', N'Bàn phím', 750000),
    ('MS-01', N'Chuột', 450000),
    ('MN-01', N'Màn hình', 5200000);
GO

SELECT
    ProductId,
    Sku,
    Name,
    Price,
    IsActive
FROM dbo.Products
ORDER BY ProductId;
GO

UPDATE dbo.Products
SET Price = 790000
OUTPUT
    deleted.Price AS OldPrice,
    inserted.Price AS NewPrice
WHERE Sku = 'KB-01';
GO

UPDATE dbo.Products
SET IsActive = 0
WHERE Sku = 'MN-01';
GO

DELETE FROM dbo.Products
OUTPUT deleted.ProductId, deleted.Sku
WHERE Sku = 'MS-01';
GO

SELECT
    ProductId,
    Sku,
    Name,
    Price,
    IsActive
FROM dbo.Products
ORDER BY ProductId;
GO
```

### Walkthrough — execution / state / cost

1. INSERT ba row; OUTPUT trả ID/SKU được tạo, thứ tự OUTPUT không được hứa.
2. UPDATE theo SKU chỉ đổi KB; deleted.Price là giá cũ, inserted.Price là giá mới.
3. UPDATE IsActive giữ row MN; DELETE bỏ MS và ghi log.
4. SELECT cuối ORDER BY ProductId để đọc kết quả ổn định. Server chịu đọc/index/log/lock; client nhận rowset qua network.

### Mini-check

Chạy UPDATE SET Price=Price có thể làm trigger/rowversion hoạt động không dù giá không đổi?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### INSERT

```sql
INSERT INTO dbo.Products (Sku, Name, Price)
VALUES (...);
```

Luôn liệt kê column.

Không dựa vào physical column order.

### SELECT

Chỉ chọn column cần:

```sql
SELECT ProductId, Name, Price
```

thay vì mặc định `SELECT *`.

### UPDATE

```sql
UPDATE ...
SET ...
WHERE ...
```

Không có `WHERE` thì mọi row có thể bị cập nhật.

### DELETE

```sql
DELETE FROM ...
WHERE ...
```

DELETE xóa row logic khỏi table và được transaction log ghi lại.

### OUTPUT

`inserted` và `deleted` pseudo table cho phép xem dữ liệu trước/sau.

Hữu ích khi:

- lấy identity;
- audit;
- debug;
- batch operation.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| hard delete | xóa row khỏi table | FK/history có thể cấm |
| soft delete | đổi trạng thái, giữ row | mọi query liên quan phải tôn trọng trạng thái |
| transaction nhiều lệnh | nhóm cần cùng thành công | chỉ dùng khi invariant yêu cầu, học ở bài19 |

### Misconception check

**Đúng hay sai?** SELECT trước UPDATE bảo đảm không ai đổi dữ liệu xen giữa.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: hai statement có thể thấy state khác nếu thiếu contract transaction phù hợp.

</details>

**Đúng hay sai?** OUTPUT trả row nghĩa là đã commit.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: cần kiểm kết quả lệnh và transaction; không phát external side effect chỉ dựa vào row đã nhận.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace CRUD.

- **Working Developer — dùng khi làm việc:** affected rows và transaction result.

- **Deep Dive — có thể quay lại sau:** audit/retention theo nghiệp vụ.

### CRUD SQL và HTTP

SQL:

```text
INSERT SELECT UPDATE DELETE
```

HTTP:

```text
POST GET PUT/PATCH DELETE
```

Có tương đồng về intent nhưng không phải mapping bắt buộc một-một.

### Soft delete

Thay:

```sql
DELETE
```

bằng:

```sql
UPDATE ... SET IsDeleted = 1
```

chỉ khi business cần giữ row.

Soft delete mang thêm complexity:

- mọi query phải filter;
- unique constraint khó hơn;
- storage tăng.

### Idempotency

UPDATE cùng giá trị thường có semantics khác INSERT duplicate.

Module Web sẽ mở rộng khái niệm idempotency ở API.

## 6. Lỗi thường gặp

### UPDATE/DELETE không có WHERE

Trước khi chạy destructive query:

```sql
SELECT ...
WHERE ...
```

để xác nhận tập row.

### SELECT *

Dễ kéo column không cần và làm contract phụ thuộc schema.

### Hard delete dữ liệu lịch sử

Order/payment thường cần giữ để audit.

### Nhiều statement nhưng không transaction

Nếu nghiệp vụ cần all-or-nothing, CRUD riêng lẻ chưa đủ.

Transaction sẽ học ở bài 19.

## 7. Khi nào KHÔNG dùng

Không hard delete lịch sử hóa đơn để dọn màn hình. Không thêm soft delete cho dữ liệu tạm chỉ vì đó là pattern phổ biến.

## 8. Production notes & scale check

Gate kiểm state cuối và affected rows cho predicate không match. Statement đơn là đơn vị atomic trong điều kiện transaction thông thường; nhiều statement không tự thành một business transaction. Không suy ra idempotency của side effect từ việc cột có cùng giá trị.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Insert 5 product bằng một statement.

### Bài 2

Tăng giá 5% cho category giả định.

### Bài 3

Dùng OUTPUT để ghi old/new price vào table variable.

### Bài 4

Thiết kế soft delete cho Product.

### Bài 5

Viết checklist an toàn trước khi chạy DELETE production.

## 10. Bài tập tích hợp liên module — Judgment

Từ command/query Module 06, API “ngừng bán” nên đổi state hay xóa record? Nêu tác động tới lịch sử order và số row được phép đổi.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. inserted/deleted chứa gì khi UPDATE?
2. OUTPUT có thứ tự cố định không?
3. Soft delete thêm nghĩa vụ nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi dùng được SELECT/INSERT/UPDATE/DELETE.
- [ ] Tôi liệt kê column khi INSERT.
- [ ] Tôi tránh SELECT *.
- [ ] Tôi kiểm tra WHERE trước destructive query.
- [ ] Tôi dùng được OUTPUT.
- [ ] Tôi hiểu hard delete và soft delete khác nhau.

Điều hướng:

- Bài trước: [Kiểu dữ liệu và NULL](./03-kieu-du-lieu-va-null.md)
- Bài tiếp theo: [Filter, sort và pagination](./05-filter-sort-va-pagination.md)
