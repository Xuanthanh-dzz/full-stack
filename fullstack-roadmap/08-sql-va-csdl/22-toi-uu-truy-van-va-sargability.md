# Tối ưu truy vấn và SARGability

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- SARGability là khả năng predicate giúp index giới hạn vùng key cần tìm.
- Giữ column có thể so theo range và dùng parameter type phù hợp.
- SARGable không bảo đảm optimizer chọn seek hoặc query nhanh.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích SARGable predicate;
- rewrite function-on-column predicate;
- tránh implicit conversion;
- tránh kéo dữ liệu thừa;
- nhận ra leading wildcard;
- tối ưu pagination/query shape;
- đo trước và sau thay đổi;
- phân biệt tuning query với tuning schema.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Mục lục đã theo ngày, hỏi từ đầu năm 2026 tới trước năm 2027 giúp mở đúng đoạn. Nếu bắt tính YEAR trên từng ngày rồi mới so, engine có thể phải xét nhiều entry hơn trước khi biết entry nào thuộc năm cần tìm.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| SARGable | predicate có thể làm điều kiện tìm key/range | OrderedAt>=from AND <to |
| implicit conversion | engine tự đổi type để so sánh | parameter lệch column type |
| half-open range | gồm đầu, loại cuối | [2026-01-01,2027-01-01) |
| residual predicate | điều kiện kiểm thêm sau bước truy cập | không phải mọi filter đều là seek key |

### Ví dụ nhỏ — tính tay trước

Mốc 2026-12-31 23:59:59 nằm trong khoảng từ 2026-01-01 (gồm) tới 2027-01-01 (không gồm). Nếu lọc tới 2026-12-31 00:00, các thời điểm còn lại của ngày cuối sẽ bị bỏ.

Query:

```sql
WHERE YEAR(OrderedAt) = 2026
```

rõ nghĩa nhưng function áp lên indexed column có thể làm engine khó seek theo range.

Rewrite:

```sql
WHERE OrderedAt >= '2026-01-01'
  AND OrderedAt <  '2027-01-01'
```

giữ column searchable.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_22') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_22
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_22;
END;
GO

CREATE DATABASE CommerceLab08_22;
GO
USE CommerceLab08_22;
GO

CREATE TABLE dbo.Orders
(
    OrderId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    OrderedAt datetime2(0) NOT NULL,
    ExternalCode varchar(30) NOT NULL,
    TotalAmount decimal(19,4) NOT NULL
);
GO

;WITH n AS
(
    SELECT TOP (30000)
        ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS rn
    FROM sys.all_objects AS a
    CROSS JOIN sys.all_objects AS b
)
INSERT INTO dbo.Orders
(CustomerId, OrderedAt, ExternalCode, TotalAmount)
SELECT
    ((rn - 1) % 500) + 1,
    DATEADD(hour, rn, CAST('2024-01-01' AS datetime2)),
    CONCAT('ORD-', RIGHT(CONCAT('000000', rn), 6)),
    CAST(100000 + rn AS decimal(19,4))
FROM n;
GO

CREATE INDEX IX_Orders_OrderedAt
ON dbo.Orders(OrderedAt)
INCLUDE(CustomerId, TotalAmount);

CREATE UNIQUE INDEX UX_Orders_ExternalCode
ON dbo.Orders(ExternalCode);
GO

SET STATISTICS IO ON;

SELECT COUNT_BIG(*)
FROM dbo.Orders
WHERE YEAR(OrderedAt) = 2026;

SELECT COUNT_BIG(*)
FROM dbo.Orders
WHERE OrderedAt >= '2026-01-01'
  AND OrderedAt < '2027-01-01';

SELECT OrderId, ExternalCode
FROM dbo.Orders
WHERE ExternalCode = 'ORD-000500';

SET STATISTICS IO OFF;
GO
```

### Walkthrough — execution / state / cost

1. Dữ liệu mẫu có 30.000 row trải qua nhiều năm, tạo index OrderedAt và ExternalCode.
2. Query YEAR và query range phải trả cùng số row trước khi so performance.
3. Range để engine có lựa chọn truy cập vùng key, nhưng optimizer vẫn cân nhắc scan.
4. Đọc page, tính expression, lookup và network đều là cost; chạy STATISTICS IO trên cùng dữ liệu và ghi plan/cấu hình.

### Mini-check

Tại sao kiểm hai query trả cùng tập row cần làm trước so logical reads?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### SARGable

Search ARGument able: predicate có thể tận dụng cấu trúc index để xác định key/range hiệu quả.

### Function on column

Nếu filter expression thường xuyên, có thể cân nhắc computed column/index nhưng phải dựa trên workload.

### Implicit conversion

Parameter type lệch schema có thể tạo conversion và plan xấu.

### Query shape

Tối ưu thường bắt đầu bằng lấy ít row/column hơn, filter sớm và index đúng.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| function trên column | có thể hạn chế range seek | một số conversion có tối ưu đặc biệt, không kết luận bằng cú pháp đơn lẻ |
| range trên column | diễn đạt biên trực tiếp | vẫn phụ thuộc selectivity/index |
| computed indexed expression | phục vụ expression cần lặp nhiều | thêm storage/write và điều kiện DDL |

### Misconception check

**Đúng hay sai?** SARGable luôn có seek trong plan.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: scan có thể rẻ hơn.

</details>

**Đúng hay sai?** Full-text search thay thế chính xác mọi LIKE %term%.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: tìm theo token/ngôn ngữ khác semantics substring tùy ý.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** equivalence trước tuning.

- **Working Developer — dùng khi làm việc:** range/type và reads.

- **Deep Dive — có thể quay lại sau:** computed index/search khi có driver.

### Leading wildcard

```sql
LIKE '%abc%'
```

khó dùng B-tree prefix seek.

Có thể cần full-text index hoặc search engine.

### Parameterization

Không concatenate SQL string từ input.

Parameterization vừa bảo mật vừa hỗ trợ plan reuse trong nhiều trường hợp.

### Pagination

Page sâu bằng OFFSET có thể đắt; keyset pagination phù hợp nhiều feed/infinite-scroll.

## 6. Lỗi thường gặp

### Tối ưu bằng hint trước khi hiểu plan

Hint có thể khóa plan kém khi data đổi.

### SELECT *

Kéo network/storage/cache nhiều hơn cần.

### CAST/CONVERT column trong WHERE

Có thể làm predicate không SARGable.

### Chỉ đo milliseconds

Cần xem IO, CPU, row count và concurrency.

## 7. Khi nào KHÔNG dùng

Không dùng query hint để che schema/query sai. Không thay substring bằng full-text mà không xác nhận semantics tìm kiếm với người dùng.

## 8. Production notes & scale check

Gate kiểm hai count bằng nhau và bằng 8.760 giờ của năm 2026 trong seed, lookup ExternalCode đúng, thêm biên timestamp. Lưu IO để review, không đặt tỷ lệ tốc độ cố định. Parameterization chống trộn syntax không tự sửa type mismatch hoặc wildcard semantics.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Rewrite `CAST(OrderedAt AS date) = @date`.

### Bài 2

Tạo implicit conversion giữa varchar và nvarchar rồi xem plan.

### Bài 3

So offset page 1000 với keyset pagination.

### Bài 4

Thu hẹp projection của ba query SELECT *.

### Bài 5

Lập bảng before/after: reads, CPU, elapsed, rows.

## 10. Bài tập tích hợp liên module — Judgment

Từ lower bound Module 07: range index giống giới hạn khoảng tìm kiếm ở đâu? Với report trả 80%table, vì sao scan có thể là lựa chọn đơn giản đúng?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Range nửa mở bảo vệ biên nào?
2. SARGable bảo đảm điều gì và không bảo đảm gì?
3. Type conversion nằm phía column có thể gây gì?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi giải thích được SARGability.
- [ ] Tôi rewrite function-on-column predicate.
- [ ] Tôi tránh implicit conversion.
- [ ] Tôi thu hẹp row/column.
- [ ] Tôi hiểu leading wildcard.
- [ ] Tôi đo before/after.

Điều hướng:

- Bài trước: [Execution plan và statistics](./21-execution-plan-va-statistics.md)
- Bài tiếp theo: [Bảo mật, phân quyền và SQL injection](./23-bao-mat-phan-quyen-va-sql-injection.md)
