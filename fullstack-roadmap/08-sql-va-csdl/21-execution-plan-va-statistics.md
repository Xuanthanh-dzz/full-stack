# Execution plan và statistics

> **Last verified:** pending — chưa chạy lại gate retrofit  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Execution plan mô tả cách engine thực hiện query; statistics giúp ước lượng dữ liệu.
- Dùng actual rows, reads, CPU và waits để tìm bottleneck có bằng chứng.
- Phần trăm cost là ước lượng tương đối, không phải số thời gian đo được.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt estimated và actual execution plan;
- đọc operator cơ bản như Scan, Seek, Sort, Hash Match, Nested Loops;
- hiểu cardinality estimate;
- hiểu statistics hỗ trợ optimizer;
- dùng SET STATISTICS IO/TIME;
- phát hiện estimate sai;
- tránh tối ưu chỉ dựa trên cost percentage.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Hai lộ trình giao hàng cùng tới đích nhưng một đường đi vòng qua nhiều phố. Plan cho biết lộ trình engine chọn; số row thực tế và lượng page đọc cho biết nó đã phải mang bao nhiêu hàng qua từng đoạn.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| optimizer | thành phần chọn phương án thực thi | seek/scan/join |
| cardinality estimate | số row dự đoán | ước lượng cho customer42/Paid |
| statistics | tóm tắt phân bố dữ liệu | histogram/density |
| actual plan | plan kèm metrics của lần chạy | actual rows |
| spill | ghi dữ liệu xử lý trung gian ra tempdb | sort/hash thiếu memory grant |

### Ví dụ nhỏ — tính tay trước

Seed có 20000 đơn,12000thuộc customer1. Cùng query cho customer1 và 42 có volume rất khác. Actual rows là số đo; estimated rows là dự đoán trước hoặc trong lựa chọn plan, không phải hai tên cho cùng số.

Một query chạy chậm:

```sql
SELECT OrderId, CustomerId, OrderedAt, TotalAmount
FROM Orders
WHERE CustomerId = 42
  AND Status = 'Paid';
```

Cần trả lời:

- optimizer chọn plan gì?
- đọc bao nhiêu page?
- estimate bao nhiêu row?
- actual bao nhiêu row?
- operator nào xử lý volume lớn?

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_21') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_21
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_21;
END;
GO

CREATE DATABASE CommerceLab08_21;
GO
USE CommerceLab08_21;
GO

CREATE TABLE dbo.Orders
(
    OrderId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    Status varchar(20) NOT NULL,
    OrderedAt datetime2(0) NOT NULL,
    TotalAmount decimal(19,4) NOT NULL
);
GO

;WITH n AS
(
    SELECT TOP (20000)
        ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS rn
    FROM sys.all_objects AS a
    CROSS JOIN sys.all_objects AS b
)
INSERT INTO dbo.Orders
(CustomerId, Status, OrderedAt, TotalAmount)
SELECT
    CASE
        WHEN rn <= 12000 THEN 1
        ELSE ((rn - 1) % 200) + 2
    END,
    CASE WHEN rn % 3 = 0 THEN 'Paid' ELSE 'Pending' END,
    DATEADD(minute, rn, CAST('2026-01-01' AS datetime2)),
    CAST(100000 + rn AS decimal(19,4))
FROM n;
GO

CREATE NONCLUSTERED INDEX IX_Orders_Customer_Status
ON dbo.Orders(CustomerId, Status)
INCLUDE(OrderedAt, TotalAmount);
GO

UPDATE STATISTICS dbo.Orders WITH FULLSCAN;
GO

SET STATISTICS IO ON;
SET STATISTICS TIME ON;

SELECT
    OrderId,
    CustomerId,
    OrderedAt,
    TotalAmount
FROM dbo.Orders
WHERE CustomerId = 42
  AND Status = 'Paid';

SET STATISTICS TIME OFF;
SET STATISTICS IO OFF;
GO

SELECT
    s.name AS StatisticName,
    STATS_DATE(s.object_id, s.stats_id) AS LastUpdated
FROM sys.stats AS s
WHERE s.object_id = OBJECT_ID(N'dbo.Orders')
ORDER BY s.name;
GO
```

Seed dùng chu kỳ status 3 khác chu kỳ customer 200 để CustomerId=42 có cả Paid và Pending; tránh một query rỗng che mất bài toán estimate.

Để xem plan, bật **Actual Execution Plan** trong công cụ SQL rồi chạy query.

### Walkthrough — execution / state / cost

1. Seed tạo dữ liệu lệch, index cover query và FULLSCAN cập nhật statistics.
2. Optimizer dùng metadata/stats và parameters để chọn plan.
3. STATISTICS IO/TIME ghi lượng công việc; actual plan cần bật công cụ hoặc STATISTICS XML.
4. Plan cache giữ phương án có thể được reuse; buffer cache giữ pages, hai cache khác nhau. CPU, reads, memory grant và waits đều có thể góp latency.

### Mini-check

Operator estimate1 row nhưng actual100000 row: điều gì có thể xảy ra với join choice hoặc memory grant?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Query optimizer

Optimizer cân nhắc nhiều phương án như scan, seek, nested loops, hash join, sort và parallelism.

### Statistics

Statistics tóm tắt phân bố dữ liệu để optimizer ước lượng số row.

### Estimated vs actual

Estimated plan chỉ có ước lượng.

Actual plan bổ sung số row runtime và metrics thực tế.

### STATISTICS IO

Logical reads cho biết số page đọc từ buffer cache.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| estimated plan | không chạy query để có runtime rows | hữu ích dự đoán nhưng chưa có evidence thực thi |
| actual plan | chạy query và thu runtime metrics | có overhead và DML vẫn gây thay đổi |
| cost percentage | tỷ trọng estimate trong plan | không là profiler thời gian tuyệt đối |

### Misconception check

**Đúng hay sai?** FULLSCAN statistics bảo đảm mọi estimate chính xác.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: correlation, histogram và query model vẫn có giới hạn.

</details>

**Đúng hay sai?** Query trả ít row chắc chắn rẻ.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: có thể đọc rất nhiều rồi mới lọc còn ít.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** đọc rows/reads.

- **Working Developer — dùng khi làm việc:** estimate mismatch.

- **Deep Dive — có thể quay lại sau:** parameter sensitivity theo workload.

### Cardinality estimate

Estimate sai lớn có thể làm chọn join, memory grant hoặc access path kém.

### Nested Loops

Phù hợp khi outer input nhỏ và inner lookup rẻ.

### Hash Match

Thường phù hợp volume lớn nhưng có memory cost.

### Sort

Có thể spill ra tempdb nếu memory grant thiếu.

## 6. Lỗi thường gặp

### Chỉ nhìn phần trăm cost

Đó là estimate tương đối trong plan, không phải profiler toàn hệ thống.

### Thấy scan là đổi thành seek bằng mọi giá

Scan có thể đúng nếu query lấy phần lớn table.

### Update statistics vô tội vạ

Không sửa được schema/query sai.

### Không so actual và estimated rows

Bỏ lỡ tín hiệu quan trọng.

## 7. Khi nào KHÔNG dùng

Không ép seek hoặc dùng hint chỉ để biểu tượng plan đẹp hơn. Không chạy actual plan của DML trên dữ liệu thật như thể đó chỉ là thao tác xem.

## 8. Production notes & scale check

Gate kiểm seed lệch, query có kết quả và stats đã cập nhật; lưu IO và plan XML để review. Không ép estimate/physical operator cố định qua mọi SQL build. Mốc baseline ghi engine build và compatibility level; thay cấu hình/phiên bản có thể đổi plan hợp lệ.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Bỏ index và ghi logical reads trước/sau.

### Bài 2

So CustomerId=1 với CustomerId=42.

### Bài 3

Xem estimated/actual row.

### Bài 4

Tạo join và xác định physical join operator.

### Bài 5

Viết checklist khi nhận ticket “query chậm”.

## 10. Bài tập tích hợp liên module — Judgment

Từ benchmark Module 07: vì sao một elapsed time chưa đủ kết luận? Đặt câu hỏi về input distribution, cache, concurrency trước khi đề xuất index mới.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Actual plan có chạy DML không?
2. Stats khác index ra sao?
3. Plan cache khác buffer cache thế nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt estimated và actual plan.
- [ ] Tôi nhận ra Scan/Seek/Sort/Join operator cơ bản.
- [ ] Tôi hiểu statistics và cardinality estimate.
- [ ] Tôi dùng STATISTICS IO/TIME.
- [ ] Tôi so estimated với actual rows.
- [ ] Tôi không tối ưu chỉ theo cost percentage.

Điều hướng:

- Bài trước: [Isolation level, MVCC, lock và deadlock](./20-isolation-level-mvcc-lock-deadlock.md)
- Bài tiếp theo: [Tối ưu truy vấn và SARGability](./22-toi-uu-truy-van-va-sargability.md)
