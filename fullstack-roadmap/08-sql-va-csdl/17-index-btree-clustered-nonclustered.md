# Index B-tree, clustered và nonclustered

> **Last verified:** pending — chưa chạy lại gate retrofit  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Index sắp key thành cấu trúc giúp tìm vùng dữ liệu phù hợp.
- Dùng theo query đọc thường xuyên và độ chọn lọc thực tế.
- Index tiêu tốn storage/write; seek không mặc định rẻ hơn scan.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích index giúp giảm lượng dữ liệu phải đọc;
- hiểu B-tree/B+tree ở mức thực hành;
- phân biệt heap, clustered index và nonclustered index;
- tạo index cho predicate phổ biến;
- đọc seek vs scan ở mức cơ bản;
- hiểu index tăng chi phí write/storage;
- tránh index mọi column.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Mục lục khách hàng dẫn tới đoạn sổ của khách42, thay vì lật mọi trang. Nhưng mỗi lần thêm hóa đơn, cả sổ lẫn mục lục phải được cập nhật; một mục lục quá rộng có thể gần bằng sổ.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| B+tree | cây cân bằng nhiều key mỗi page, dữ liệu/locator ở lá | rowstore index |
| clustered index | lá chứa row dữ liệu của table | PK OrderId |
| nonclustered index | cấu trúc key riêng kèm row locator | CustomerId,OrderedAt |
| logical read | một lần truy cập page trong buffer cache | STATISTICS IO |

### Ví dụ nhỏ — tính tay trước

Khách42 có 100 đơn trong seed10000 row. Index bắt đầu CustomerId dẫn tới vùng100 row; query lấy20 đơn mới nhất có thể dừng sớm. Cột Status/Total không nằm trong index phụ này nên plan có thể cần lookup.

Table Orders có 10 triệu row.

Query thường xuyên:

```sql
WHERE CustomerId = @CustomerId
ORDER BY OrderedAt DESC
```

Không có index phù hợp, SQL Server có thể phải scan lượng dữ liệu lớn.

Index tạo cấu trúc được sắp xếp để tìm vùng cần đọc nhanh hơn.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_17') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_17
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_17;
END;
GO

CREATE DATABASE CommerceLab08_17;
GO
USE CommerceLab08_17;
GO

CREATE TABLE dbo.Orders
(
    OrderId bigint IDENTITY(1,1) NOT NULL,
    CustomerId int NOT NULL,
    OrderedAt datetime2(0) NOT NULL,
    Status varchar(20) NOT NULL,
    TotalAmount decimal(19,4) NOT NULL,
    CONSTRAINT PK_Orders
        PRIMARY KEY CLUSTERED (OrderId)
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
(CustomerId, OrderedAt, Status, TotalAmount)
SELECT
    ((rn - 1) % 100) + 1,
    DATEADD(minute, rn, CAST('2026-01-01' AS datetime2)),
    CASE WHEN rn % 3 = 0 THEN 'Paid' ELSE 'Pending' END,
    CAST(100000 + (rn % 5000000) AS decimal(19,4))
FROM n;
GO

CREATE NONCLUSTERED INDEX IX_Orders_CustomerId_OrderedAt
ON dbo.Orders
(
    CustomerId,
    OrderedAt DESC
);
GO

SET STATISTICS IO ON;

SELECT TOP (20)
    OrderId,
    CustomerId,
    OrderedAt,
    Status,
    TotalAmount
FROM dbo.Orders
WHERE CustomerId = 42
ORDER BY OrderedAt DESC;

SET STATISTICS IO OFF;
GO
```

### Walkthrough — execution / state / cost

1. Seed tạo10000 row, clustered PK giữ row tại leaf theo key logic.
2. CREATE INDEX đọc dữ liệu và dựng cây phụ theo CustomerId rồi OrderedAt giảm.
3. Optimizer ước lượng phạm vi cần đọc, chọn index/lookup hoặc scan.
4. Query chạy trên server; buffer pages và memory plan ở RAM, files/log trên storage. Kết quả cần ORDER BY dù có clustered index.

### Mini-check

Query cần90%table: vì sao đọc tuần tự nhiều page có thể hợp hơn hàng nghìn lookup?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### B-tree trực giác

Index có root, intermediate pages và leaf pages.

Thay vì scan toàn bộ row, engine đi theo key range.

### Clustered index

Leaf level chứa data row của table theo clustered key structure.

Một table chỉ có một clustered index.

### Nonclustered index

Có key riêng và locator về row gốc.

Một table có thể có nhiều nonclustered index.

### Seek và scan

Seek dùng key để tới range cần.

Scan đọc toàn bộ hoặc phần lớn structure.

Scan không luôn xấu.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| heap table | không clustered index | locator khác, không là heap priority queue |
| clustered | một thứ tự key logic cho data leaf | không cam kết vị trí page vật lý liên tục hay output order |
| nonclustered | nhiều đường truy cập theo workload | thêm storage/write và có thể lookup |

### Misconception check

**Đúng hay sai?** Clustered index bảo đảm SELECT không ORDER BY vẫn theo key.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: presentation order cần ORDER BY.

</details>

**Đúng hay sai?** Index seek luôn đọc ít hơn scan.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: range rộng/lookup nhiều có thể rất tốn.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** seek/scan trực giác.

- **Working Developer — dùng khi làm việc:** key/locator và logical reads.

- **Deep Dive — có thể quay lại sau:** page splits/concurrency khi có workload.

### Index key order

Index `(CustomerId, OrderedAt)` khác `(OrderedAt, CustomerId)`.

### Write amplification

INSERT/UPDATE/DELETE phải duy trì mọi index liên quan.

### Clustered key

Key nhỏ, ổn định và tăng dần thường dễ quản lý, nhưng workload mới quyết định.

## 6. Lỗi thường gặp

### Index mọi column

Write cost và maintenance tăng mạnh.

### Nghĩ seek luôn nhanh hơn scan

Nếu trả phần lớn table, scan có thể đúng.

### Clustered key quá rộng

Làm nonclustered index lớn hơn.

### Không đo logical reads

Elapsed time một lần chạy dễ nhiễu.

## 7. Khi nào KHÔNG dùng

Không index mọi cột hoặc chọn key rộng chỉ vì dễ đọc. Không coi heap table SQL là cùng cấu trúc binary heap bài08 Module 07.

## 8. Production notes & scale check

Gate kiểm seed/index key và kết quả query; IO được ghi làm evidence, không ép một plan shape cố định. Sample10000 row không đại diện10 triệu row production. Đo cardinality, reads và write workload trước giữ thêm index.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Tạo query theo Status và xem plan trước/sau index.

### Bài 2

Đổi order key trong composite index và so query.

### Bài 3

Tạo heap table và clustered table để so concept.

### Bài 4

Dùng STATISTICS IO ghi logical reads.

### Bài 5

Liệt kê index ứng viên rồi chọn theo workload.

## 10. Bài tập tích hợp liên module — Judgment

Từ BST Module 07: cây index page-based giảm số lần đọc page thế nào so mỗi node một giá trị? Với table nhỏ, chi phí duy trì index có đáng cho một query/ngày không?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Leaf clustered chứa gì?
2. Nonclustered locator dùng làm gì?
3. Cost ghi tăng ở đâu?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi hiểu index giảm search space.
- [ ] Tôi phân biệt clustered/nonclustered.
- [ ] Tôi biết key order quan trọng.
- [ ] Tôi hiểu seek/scan không phải tốt/xấu tuyệt đối.
- [ ] Tôi biết index làm write đắt hơn.
- [ ] Tôi đo logical reads thay vì đoán.

Điều hướng:

- Bài trước: [Denormalization và dữ liệu lịch sử](./16-denormalization-va-du-lieu-lich-su.md)
- Bài tiếp theo: [Covering, filtered và composite index](./18-covering-filtered-composite-index.md)
