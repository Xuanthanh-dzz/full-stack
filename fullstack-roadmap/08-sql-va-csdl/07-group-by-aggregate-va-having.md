# GROUP BY, aggregate và HAVING

> **Last verified:** pending — chưa chạy lại gate retrofit  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Aggregate gom nhiều row thành kết quả ở một grain mới.
- Dùng GROUP BY cho tổng theo khách, tháng hoặc trạng thái.
- WHERE lọc row còn HAVING lọc nhóm; chọn nhầm có thể đổi metric.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng COUNT, SUM, AVG, MIN, MAX;
- nhóm dữ liệu bằng GROUP BY;
- phân biệt WHERE và HAVING;
- xử lý NULL trong aggregate;
- tính doanh thu theo customer/status;
- tránh select column không thuộc group;
- hiểu grain của kết quả aggregate.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Xếp hóa đơn thành chồng theo khách rồi cộng từng chồng. Trước khi xếp, có thể bỏ hóa đơn chưa thanh toán; sau khi cộng mới biết chồng nào đạt ngưỡng doanh thu.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| grain | một row kết quả đại diện cho cái gì | một customer summary |
| aggregate | phép tính trên nhiều row | SUM/COUNT/AVG |
| HAVING | điều kiện trên nhóm đã tính | SUM>=5000000 |
| logical order | mô hình nghĩa của query | không phải thứ tự operator vật lý |

### Ví dụ nhỏ — tính tay trước

Khách1 có 3 đơn với amounts3 triệu,4.5 triệu,NULL: COUNT(*)=3,COUNT(amount)=2,SUM=7.5 triệu,AVG=3.75 triệu. NULL không tự tính là0 trong AVG.

Business hỏi:

- có bao nhiêu order mỗi customer?
- tổng doanh thu theo tháng?
- customer nào chi trên 10 triệu?
- average order value là bao nhiêu?

Đây không còn là query từng row riêng lẻ; cần biến nhiều row thành summary.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_07') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_07
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_07;
END;
GO

CREATE DATABASE CommerceLab08_07;
GO
USE CommerceLab08_07;
GO

CREATE TABLE dbo.Orders
(
    OrderId bigint IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    Status varchar(20) NOT NULL,
    TotalAmount decimal(19,4) NULL,
    OrderedAt date NOT NULL
);
GO

INSERT INTO dbo.Orders
(CustomerId, Status, TotalAmount, OrderedAt)
VALUES
(1, 'Paid',      3000000, '2026-01-05'),
(1, 'Paid',      4500000, '2026-01-20'),
(1, 'Cancelled', NULL,    '2026-02-01'),
(2, 'Paid',      12000000,'2026-01-10'),
(2, 'Pending',   2000000, '2026-02-03'),
(3, 'Paid',      900000,  '2026-02-15');
GO

SELECT
    CustomerId,
    COUNT(*) AS OrderCount,
    COUNT(TotalAmount) AS OrdersWithAmount,
    SUM(COALESCE(TotalAmount, 0)) AS TotalAmount,
    AVG(TotalAmount) AS AverageAmount,
    MIN(TotalAmount) AS MinAmount,
    MAX(TotalAmount) AS MaxAmount
FROM dbo.Orders
GROUP BY CustomerId
ORDER BY CustomerId;
GO

SELECT
    CustomerId,
    SUM(TotalAmount) AS PaidRevenue
FROM dbo.Orders
WHERE Status = 'Paid'
GROUP BY CustomerId
HAVING SUM(TotalAmount) >= 5000000
ORDER BY PaidRevenue DESC;
GO

SELECT
    YEAR(OrderedAt) AS OrderYear,
    MONTH(OrderedAt) AS OrderMonth,
    COUNT(*) AS OrderCount,
    SUM(COALESCE(TotalAmount, 0)) AS Revenue
FROM dbo.Orders
GROUP BY
    YEAR(OrderedAt),
    MONTH(OrderedAt)
ORDER BY OrderYear, OrderMonth;
GO
```

### Walkthrough — execution / state / cost

1. Theo nghĩa logic: FROM →WHERE →GROUP BY →HAVING →SELECT →ORDER BY.
2. Query1 gom mọi status; query2 chỉ giữ Paid trước khi tính ngưỡng.
3. Query tháng đầu tiên đang cộng giá trị mọi đơn, không tự chứng minh đó là tiền đã thu.
4. Optimizer chọn hash/sort/stream aggregate ở server; có thể giữ state nhóm và spill ra tempdb. Kết quả ít row không đồng nghĩa đọc ít row.

### Mini-check

AVG(COALESCE(amount,0)) trên ví dụ khách1 bằng bao nhiêu, và đang trả lời câu hỏi khác gì?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Grain

Query:

```sql
GROUP BY CustomerId
```

trả một row trên mỗi customer.

Grain thay từ:

```text
1 row = 1 order
```

thành:

```text
1 row = 1 customer summary
```

### COUNT(*) và COUNT(column)

`COUNT(*)` đếm row.

`COUNT(TotalAmount)` bỏ row có TotalAmount NULL.

### WHERE và HAVING

`WHERE` lọc row **trước group**.

`HAVING` lọc group **sau aggregate**.

Ví dụ:

```sql
WHERE Status = 'Paid'
...
HAVING SUM(TotalAmount) >= 5000000
```

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| WHERE | lọc từng row trước group | không dùng aggregate cùng level |
| HAVING | lọc nhóm theo metric | không thay WHERE nếu cần loại row trước cộng |
| window | giữ detail và thêm metric | học bài12, không collapse như GROUP BY |

### Misconception check

**Đúng hay sai?** COUNT(column) luôn bằng COUNT(*).

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai khi column có NULL.

</details>

**Đúng hay sai?** Thứ tự logic là trace chính xác execution plan.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: optimizer có thể biến đổi cách thực thi mà giữ semantics.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** group/metric.

- **Working Developer — dùng khi làm việc:** NULL và grain.

- **Deep Dive — có thể quay lại sau:** physical aggregate/memory khi xem plan.

### Logical query processing

Mô hình đơn giản:

```text
FROM
WHERE
GROUP BY
HAVING
SELECT
ORDER BY
```

Không phải implementation vật lý chính xác, nhưng rất hữu ích để reasoning.

### Aggregate và NULL

`SUM`, `AVG`, `MIN`, `MAX` thường bỏ NULL.

Do đó NULL semantics phải được quyết định rõ.

### Conditional aggregate

Có thể dùng:

```sql
SUM(CASE WHEN Status = 'Paid' THEN TotalAmount ELSE 0 END)
```

để tính nhiều metric trong cùng group.

## 6. Lỗi thường gặp

### SELECT column không group/aggregate

Nếu grain là customer, không thể tùy tiện select OrderId.

### Dùng HAVING thay WHERE

Nếu predicate có thể lọc row trước group, dùng WHERE thường tốt hơn.

### AVG trên integer

Cần hiểu data type của expression để tránh mất phần thập phân.

### COUNT(column) nhưng tưởng là COUNT(*)

NULL làm kết quả khác.

## 7. Khi nào KHÔNG dùng

Không GROUP BY mọi cột chỉ để làm hết lỗi compiler khi chưa biết grain. Không gọi tổng Pending là paid revenue.

## 8. Production notes & scale check

Gate đối chiếu count/sum/average, Paid threshold và nhóm tháng với dữ liệu xác định. SUM trên tập rỗng có thể NULL còn COUNT trả 0; COUNT lớn có giới hạn int, chọn COUNT_BIG nếu miền dữ liệu cần. Không dùng thời gian chạy nhỏ để kết luận plan tốt.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Tính order count theo Status.

### Bài 2

Tính paid revenue theo tháng.

### Bài 3

Tìm customer có ít nhất 2 paid order.

### Bài 4

Tính tỷ lệ cancelled bằng conditional aggregate.

### Bài 5

Giải thích grain của ba query bạn vừa viết.

## 10. Bài tập tích hợp liên module — Judgment

Từ dictionary counting Module 07: hash group giữ state gì theo số nhóm? So10 khách nhiều đơn với1 triệu khách ít đơn, đề xuất metric bộ nhớ cần xem.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Grain trước/sau là gì?
2. AVG bỏ NULL khác thêm 0 thế nào?
3. HAVING chạy logic sau bước nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi dùng được COUNT/SUM/AVG/MIN/MAX.
- [ ] Tôi xác định được grain.
- [ ] Tôi phân biệt WHERE và HAVING.
- [ ] Tôi hiểu aggregate bỏ NULL ra sao.
- [ ] Tôi viết conditional aggregate.
- [ ] Tôi không select column phá grain.

Điều hướng:

- Bài trước: [Hàm scalar, CASE và xử lý NULL](./06-ham-scalar-case-va-xu-ly-null.md)
- Bài tiếp theo: [INNER, LEFT, RIGHT, FULL và CROSS JOIN](./08-inner-left-right-full-cross-join.md)
