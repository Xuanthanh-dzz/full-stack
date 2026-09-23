# Filter, sort và pagination

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Pagination chia kết quả đã có thứ tự thành phần nhỏ để trả cho client.
- Offset tiện nhảy trang; keyset dùng khóa cuối để đi tiếp.
- Thứ tự duy nhất không tạo snapshot xuyên nhiều request khi dữ liệu đổi.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng WHERE với nhiều predicate;
- dùng IN, BETWEEN, LIKE;
- sort bằng ORDER BY nhiều column;
- phân trang bằng OFFSET/FETCH;
- hiểu pagination phải có deterministic order;
- mô tả nhược điểm offset pagination ở page sâu;
- chuẩn bị cho keyset pagination.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Đánh dấu cuốn sách cuối đã đọc giúp tìm trang tiếp theo theo vị trí cuốn ấy. Đếm bỏ qua 100 cuốn từ đầu là cách khác; nếu ai thêm sách ở đầu, số thứ tự cũ có thể lệch.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| tiebreaker | khóa phụ phân định row cùng giá trị sort | ProductId |
| offset | số row bỏ qua trước khi lấy | OFFSET |
| keyset/cursor | đi tiếp từ bộ giá trị khóa cuối | afterProductId |
| deterministic order | thứ tự xác định với cùng dữ liệu | Price DESC,ProductId ASC |

### Ví dụ nhỏ — tính tay trước

Lọc Keyboard giá từ 400.000 đến 3.000.000 giữ các ID 1, 2, 3, 8. Sắp theo giá giảm dần được 8, 2, 1, 3; trang đầu gồm 3 mục là 8, 2, 1. Một truy vấn keyset khác với điều kiện ID > 3 trả 4, 5, 6; truy vấn này không dùng bộ lọc Keyboard trước đó.

API product cần hỗ trợ:

```text
search = "keyboard"
minPrice = 500000
maxPrice = 3000000
isActive = true
sort = price-desc
page = 2
pageSize = 20
```

Nếu query không có order ổn định, page 1 và page 2 có thể trùng hoặc thiếu item khi dữ liệu thay đổi.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_05') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_05
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_05;
END;
GO

CREATE DATABASE CommerceLab08_05;
GO
USE CommerceLab08_05;
GO

CREATE TABLE dbo.Products
(
    ProductId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Name nvarchar(160) NOT NULL,
    Price decimal(19,4) NOT NULL,
    IsActive bit NOT NULL,
    CreatedAt datetime2(0) NOT NULL
);
GO

INSERT INTO dbo.Products (Name, Price, IsActive, CreatedAt)
VALUES
(N'Mechanical Keyboard A', 1200000, 1, '2026-01-01'),
(N'Mechanical Keyboard B', 1800000, 1, '2026-01-02'),
(N'Office Keyboard',       500000, 1, '2026-01-03'),
(N'Gaming Mouse',          900000, 1, '2026-01-04'),
(N'4K Monitor',           6500000, 1, '2026-01-05'),
(N'USB Hub',               400000, 0, '2026-01-06'),
(N'Keyboard Wrist Rest',   350000, 1, '2026-01-07'),
(N'Mechanical Keyboard C',2200000, 1, '2026-01-08');
GO

DECLARE @Search nvarchar(100) = N'Keyboard';
DECLARE @MinPrice decimal(19,4) = 400000;
DECLARE @MaxPrice decimal(19,4) = 3000000;
DECLARE @Page int = 1;
DECLARE @PageSize int = 3;

SELECT
    ProductId,
    Name,
    Price,
    CreatedAt
FROM dbo.Products
WHERE IsActive = 1
  AND Name LIKE N'%' + @Search + N'%'
  AND Price BETWEEN @MinPrice AND @MaxPrice
ORDER BY
    Price DESC,
    ProductId ASC
OFFSET (@Page - 1) * @PageSize ROWS
FETCH NEXT @PageSize ROWS ONLY;
GO

SELECT
    ProductId,
    Name,
    Price
FROM dbo.Products
WHERE ProductId > 3
ORDER BY ProductId
OFFSET 0 ROWS
FETCH NEXT 3 ROWS ONLY;
GO
```

### Walkthrough — execution / state / cost

1. WHERE kiểm active, LIKE và giá theo logic query.
2. ORDER BY Price DESC rồi ProductId ASC phân định tie.
3. OFFSET/FETCH chọn đoạn; phép nhân offset cần validate page/size và tránh overflow khi nhận input ngoài.
4. Server đọc/filter/sort hoặc dùng index; page sâu có thể đọc nhiều row bị bỏ. Network chỉ nhận page không có nghĩa server chỉ làm việc trên page.

### Mini-check

Chèn sản phẩm đắt nhất sau khi đọc trang 1: nội dung trang 2 dùng offset sẽ dịch thế nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### WHERE

Predicate kết hợp bằng:

```text
AND
OR
NOT
```

Dùng ngoặc khi logic phức tạp.

### LIKE

```sql
LIKE N'%Keyboard%'
```

leading wildcard thường khó tận dụng B-tree index hiệu quả.

Đây là preview cho SARGability ở bài 22.

### ORDER BY

Pagination không nên chỉ:

```sql
ORDER BY Price DESC
```

nếu nhiều row cùng Price.

Thêm tiebreaker unique:

```sql
ORDER BY Price DESC, ProductId ASC
```

để order deterministic.

### OFFSET/FETCH

```sql
OFFSET 20 ROWS
FETCH NEXT 20 ROWS ONLY
```

dễ hiểu và phù hợp nhiều UI.

Nhưng page sâu có thể buộc engine đọc/bỏ qua nhiều row.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| offset | nhảy tới trang sốN | page sâu và drift khi insert/delete |
| keyset | đi tiếp theo khóa sort | không nhảy tùy ý, cần cursor đầy đủ |
| tải hết rồi page ở client | dataset nhỏ cố định | RAM/network lớn khi scale |

### Misconception check

**Đúng hay sai?** ORDER BY unique ngăn mọi row trùng qua hai request.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: dữ liệu đổi giữa requests vẫn có thể drift.

</details>

**Đúng hay sai?** Cursor chỉ cần ID dù sort theo Price rồi ID.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: phải lưu đủ bộ khóa và chiều so sánh tương ứng.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** WHERE/sort/page.

- **Working Developer — dùng khi làm việc:** cursor và concurrent drift.

- **Deep Dive — có thể quay lại sau:** index/query plan cho trang sâu.

### Offset pagination

Ưu điểm:

- page number dễ hiển thị;
- random jump tới page N.

Nhược:

- page sâu đắt;
- concurrent insert/delete làm page drift.

### Keyset pagination

Thay vì:

```text
page=10000
```

gửi cursor:

```text
afterProductId=812345
```

Query:

```sql
WHERE ProductId > @After
ORDER BY ProductId
```

rất phù hợp infinite scroll/feed.

### TOP

```sql
SELECT TOP (10) ...
ORDER BY ...
```

luôn đi cùng ORDER BY nếu cần “top” có nghĩa xác định.

## 6. Lỗi thường gặp

### Pagination không ORDER BY

Relational table không có natural presentation order được bảo đảm.

### ORDER BY không unique

Các row tie có thể đổi vị trí giữa request.

### Search `%term%` trên table lớn

Có thể cần full-text search hoặc search engine riêng.

### Client tự tải tất cả rồi phân trang

Backend phải filter/sort/page gần dữ liệu khi dataset lớn.

## 7. Khi nào KHÔNG dùng

Không dùng offset rất sâu cho feed lớn theo thói quen. Không thêm search engine cho 8 row chỉ vì LIKE có wildcard; đo workload trước.

## 8. Production notes & scale check

Gate kiểm hai query chính và tie pagination trên dữ liệu cố định. LIKE parameter vẫn hiểu % và _ là wildcard; muốn literal substring phải có policy escape riêng. Keyset giảm drift do vị trí nhưng không đóng băng row đang được sửa.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Filter active product giá dưới 1 triệu.

### Bài 2

Sort theo IsActive desc, Price asc, ProductId asc.

### Bài 3

Viết page 2 size 2 bằng OFFSET/FETCH.

### Bài 4

Viết keyset pagination theo `(CreatedAt, ProductId)`.

### Bài 5

Giải thích vì sao `ORDER BY Price` chưa đủ stable.

## 10. Bài tập tích hợp liên module — Judgment

Từ binary search/index Module 07, chi phí chuẩn bị thứ tự và bỏ qua prefix nằm ở đâu? Với 20 sản phẩm so với 10 triệu sản phẩm, chọn pagination và nêu evidence cần đo.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Tiebreaker bảo vệ điều gì?
2. Keyset cần giữ state gì ở client?
3. Nhận 3 row có nghĩa database chỉ đọc 3 row không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi viết được WHERE nhiều predicate.
- [ ] Tôi dùng IN/BETWEEN/LIKE đúng.
- [ ] Tôi sort nhiều column.
- [ ] Tôi phân trang bằng OFFSET/FETCH.
- [ ] Tôi dùng unique tiebreaker.
- [ ] Tôi hiểu offset và keyset pagination khác nhau.

Điều hướng:

- Bài trước: [CRUD](./04-crud-select-insert-update-delete.md)
- Bài tiếp theo: [Hàm scalar, CASE và xử lý NULL](./06-ham-scalar-case-va-xu-ly-null.md)

### Checkpoint sau cụm bài

- [Failure Lab](./failure-labs/01-null-check.md)
- [Spaced Review](./reviews/review-01.md)
