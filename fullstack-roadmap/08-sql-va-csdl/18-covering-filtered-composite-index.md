# Covering, filtered và composite index

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Composite, INCLUDE và filtered index phục vụ các phần khác nhau của access pattern.
- Chọn key cho predicate/order, INCLUDE cho dữ liệu cần đọc, filter cho tập con có ích.
- Covering phụ thuộc query; index rộng hoặc filter không khớp có thể không giúp.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- thiết kế composite index theo predicate và sort;
- dùng INCLUDE để cover query;
- tạo filtered index;
- phân biệt key column và included column;
- tránh index quá rộng;
- hiểu left-prefix behavior;
- kiểm chứng thiết kế bằng execution plan và logical reads.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Chia sổ trước theo khách, rồi trạng thái, rồi ngày giúp tìm đơn Paid mới nhất của một khách. Ghi tổng tiền ngay trên mục lục giúp khỏi mở hóa đơn, nhưng làm mục lục dày hơn.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| composite key | key gồm nhiều cột có thứ tự | CustomerId,Status,OrderedAt |
| INCLUDE | cột kèm ở lá, không là thứ tự search key | TotalAmount |
| covering | index đủ dữ liệu query cần | thuộc cặp query/index |
| filtered index | chỉ index row thỏa predicate | Status=Paid |

### Ví dụ nhỏ — tính tay trước

Index(CustomerId,Status,OrderedAt DESC) INCLUDE TotalAmount: với customer42/Paid có thể đọc theo ngày và lấy total ngay. Query chỉ Status=Paid không có cùng prefix tìm kiếm.

Dashboard chạy liên tục:

```sql
SELECT TOP 50
    OrderId,
    OrderedAt,
    TotalAmount
FROM Orders
WHERE CustomerId = @id
  AND Status = 'Paid'
ORDER BY OrderedAt DESC;
```

Một index chỉ có `CustomerId` có thể vẫn phải lookup thêm dữ liệu từ row gốc.

Ta cần thiết kế theo **toàn access pattern**, không chỉ một predicate.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_18') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_18
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_18;
END;
GO

CREATE DATABASE CommerceLab08_18;
GO
USE CommerceLab08_18;
GO

CREATE TABLE dbo.Orders
(
    OrderId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    Status varchar(20) NOT NULL,
    OrderedAt datetime2(0) NOT NULL,
    TotalAmount decimal(19,4) NOT NULL,
    ShippingCity nvarchar(100) NULL
);
GO

;WITH n AS
(
    SELECT TOP (10000)
        ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS rn
    FROM sys.all_objects AS a
    CROSS JOIN sys.all_objects AS b
)
INSERT INTO dbo.Orders
(
    CustomerId,
    Status,
    OrderedAt,
    TotalAmount,
    ShippingCity
)
SELECT
    ((rn - 1) % 200) + 1,
    CASE
        WHEN rn % 5 = 0 THEN 'Cancelled'
        WHEN rn % 2 = 0 THEN 'Paid'
        ELSE 'Pending'
    END,
    DATEADD(minute, rn, CAST('2026-01-01' AS datetime2)),
    CAST(100000 + rn AS decimal(19,4)),
    CASE WHEN rn % 2 = 0 THEN N'Hà Nội' ELSE N'TP.HCM' END
FROM n;
GO

CREATE NONCLUSTERED INDEX IX_Orders_Customer_Status_OrderedAt
ON dbo.Orders
(
    CustomerId,
    Status,
    OrderedAt DESC
)
INCLUDE
(
    TotalAmount
);
GO

SET ANSI_NULLS ON;
SET ANSI_PADDING ON;
SET ANSI_WARNINGS ON;
SET ARITHABORT ON;
SET CONCAT_NULL_YIELDS_NULL ON;
SET QUOTED_IDENTIFIER ON;
SET NUMERIC_ROUNDABORT OFF;
GO

CREATE NONCLUSTERED INDEX IX_Orders_Paid_OrderedAt
ON dbo.Orders
(
    OrderedAt DESC
)
INCLUDE
(
    CustomerId,
    TotalAmount
)
WHERE Status = 'Paid';
GO

SET STATISTICS IO ON;

SELECT TOP (50)
    OrderId,
    OrderedAt,
    TotalAmount
FROM dbo.Orders
WHERE CustomerId = 42
  AND Status = 'Paid'
ORDER BY OrderedAt DESC;

SET STATISTICS IO OFF;
GO
```

### Walkthrough — execution / state / cost

1. DDL dựng index composite và index filtered riêng; không có nghĩa cả hai được chọn cùng lúc.
2. Filter quyết định row được giữ; SET options cần tương thích cho filtered index.
3. Optimizer kiểm predicate có bảo đảm nằm trong filter hay không, rồi so chi phí.
4. INCLUDE giảm lookup nhưng tăng page và write cost. Khi status đổi Pending→Paid, row phải được thêm vào filtered index.

### Mini-check

Vì sao OrderId có thể được lấy từ nonclustered index dù không viết trong INCLUDE khi table có clustered PK OrderId?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Composite key

Key:

```text
CustomerId, Status, OrderedAt
```

phù hợp với equality trên `CustomerId`, `Status` rồi sort/range theo `OrderedAt`.

### INCLUDE

Included column nằm ở leaf để query lấy dữ liệu mà không nhất thiết phải lookup row gốc.

Nó không tham gia thứ tự search key giống key column.

### Covering index

Một query được cover khi index chứa đủ dữ liệu cho predicate, ordering và output theo execution plan cụ thể.

Covering là thuộc tính của **query + index**, không phải nhãn cố định của index.

### Filtered index

```sql
WHERE Status = 'Paid'
```

index chỉ chứa subset cần thiết.

Hữu ích khi subset nhỏ và query thường xuyên dùng đúng predicate đó.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| key column | tham gia thứ tự/range | key rộng tăng cost nhiều tầng |
| included column | có giá trị tại leaf | không thay vị trí cột trong key |
| filtered index | ít row theo predicate | parameter không đủ chứng minh filter có thể không dùng được |

### Misconception check

**Đúng hay sai?** INCLUDE(OrderedAt) tương đương key OrderedAt để tránh sort.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: INCLUDE không tạo thứ tự search key đó.

</details>

**Đúng hay sai?** Có index cover thì optimizer bắt buộc chọn.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: vẫn so chi phí theo stats và query shape.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** ba vai trò index.

- **Working Developer — dùng khi làm việc:** prefix/filter implication.

- **Deep Dive — có thể quay lại sau:** consolidation theo telemetry.

### Left prefix

Composite index `(A,B,C)` thường hữu ích nhất khi predicate bắt đầu từ `A`.

Query chỉ filter `B` có thể không tận dụng seek như mong đợi.

### Equality trước range

Heuristic thường gặp:

```text
equality columns
-> range/order column
```

nhưng luôn phải kiểm chứng bằng workload.

### Index width

INCLUDE quá nhiều column làm tăng:

- disk;
- buffer cache pressure;
- write cost;
- maintenance.

## 6. Lỗi thường gặp

### INCLUDE mọi column để “cover tất cả”

Biến index thành gần như copy table.

### Filtered index không khớp predicate

Optimizer có thể không dùng nếu semantics query không tương thích.

### Thứ tự composite theo SELECT list

Index key nên theo access pattern, không theo thứ tự column trong SELECT.

### Chỉ làm theo missing-index hint

Hint là gợi ý, không phải thiết kế hoàn chỉnh.

## 7. Khi nào KHÔNG dùng

Không INCLUDE toàn table để cover mọi query. Không áp “cột selective nhất trước” như luật tuyệt đối khi equality/range/order của workload khác nhau.

## 8. Production notes & scale check

Gate kiểm metadata key/include/filter và rowset khách42. Không chấm theo tên operator cố định; index đề xuất còn cần so reads/write cost. Hai index trong demo minh họa hai thiết kế, chưa phải đề nghị giữ cả hai trên mọi hệ thống.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Thiết kế index cho `WHERE Email = @email`.

### Bài 2

Thiết kế index cho `WHERE CustomerId=@id AND OrderedAt>=@from ORDER BY OrderedAt`.

### Bài 3

Tạo filtered index cho active product.

### Bài 4

Bỏ INCLUDE rồi so logical reads và key lookup.

### Bài 5

Review 5 index trùng prefix và đề xuất consolidate.

## 10. Bài tập tích hợp liên module — Judgment

Từ topK Module 07: ORDER BY +TOP có thể dừng sớm khi dữ liệu đã theo thứ tự nào? Nêu index nhỏ nhất cho query cụ thể và query nó không phục vụ tốt.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Covering là thuộc tính của gì?
2. INCLUDE có sắp row không?
3. Filter ảnh hưởng UPDATE ra sao?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi thiết kế composite key theo predicate.
- [ ] Tôi phân biệt key và INCLUDE.
- [ ] Tôi hiểu covering là theo query.
- [ ] Tôi dùng filtered index có mục tiêu.
- [ ] Tôi tránh index quá rộng.
- [ ] Tôi kiểm chứng bằng plan và IO.

Điều hướng:

- Bài trước: [Index B-tree, clustered và nonclustered](./17-index-btree-clustered-nonclustered.md)
- Bài tiếp theo: [Transaction và ACID](./19-transaction-va-acid.md)
