# Window function

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Window function tính trên các row liên quan mà vẫn giữ detail row.
- Dùng cho ranking, running total và so row trước/sau.
- ORDER BY trong OVER khác ORDER BY kết quả; frame và tie quyết định nghĩa phép tính.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng ROW_NUMBER, RANK và DENSE_RANK;
- dùng aggregate với OVER;
- partition dữ liệu mà không làm mất detail row;
- dùng LAG/LEAD;
- lấy top-N per group;
- tính running total;
- phân biệt GROUP BY với window function.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Mỗi hóa đơn vẫn có một dòng, nhưng bên cạnh ghi thêm thứ hạng trong khách đó và tổng tiền tới lúc này. Không gom mất hóa đơn như một báo cáo GROUP BY.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| partition | nhóm row để tính độc lập | mỗi CustomerId |
| window order | thứ tự dùng khi tính | OrderedAt,OrderId |
| frame | phần partition tham gia phép tổng tại row hiện tại | ROWS từ đầu tới hiện tại |
| LAG | giá trị ở row trước trong window order | PreviousAmount |

### Ví dụ nhỏ — tính tay trước

Khách1 có amounts1,3,3 triệu theo ngày: running totals1,4,7 triệu. Theo amount giảm: ROW_NUMBER của IDs102,103,101 là1,2,3; RANK là1,1,3; DENSE_RANK là1,1,2.

Dashboard cần:

- xếp hạng order theo giá trị trong từng customer;
- lấy 2 order lớn nhất của mỗi customer;
- tính running revenue;
- so order hiện tại với order trước.

Nếu GROUP BY, detail row bị collapse.

Window function giữ detail row nhưng vẫn tính trên “cửa sổ” các row liên quan.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_12') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_12
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_12;
END;
GO

CREATE DATABASE CommerceLab08_12;
GO
USE CommerceLab08_12;
GO

CREATE TABLE dbo.Orders
(
    OrderId int NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    OrderedAt date NOT NULL,
    TotalAmount decimal(19,4) NOT NULL
);
GO

INSERT INTO dbo.Orders VALUES
(101,1,'2026-01-01',1000000),
(102,1,'2026-01-10',3000000),
(103,1,'2026-02-01',3000000),
(201,2,'2026-01-03',5000000),
(202,2,'2026-02-03',7000000);
GO

SELECT
    OrderId,
    CustomerId,
    OrderedAt,
    TotalAmount,
    ROW_NUMBER() OVER
    (
        PARTITION BY CustomerId
        ORDER BY TotalAmount DESC, OrderId
    ) AS RowNumber,
    RANK() OVER
    (
        PARTITION BY CustomerId
        ORDER BY TotalAmount DESC
    ) AS AmountRank,
    DENSE_RANK() OVER
    (
        PARTITION BY CustomerId
        ORDER BY TotalAmount DESC
    ) AS DenseAmountRank,
    SUM(TotalAmount) OVER
    (
        PARTITION BY CustomerId
        ORDER BY OrderedAt, OrderId
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS RunningTotal,
    LAG(TotalAmount) OVER
    (
        PARTITION BY CustomerId
        ORDER BY OrderedAt, OrderId
    ) AS PreviousAmount
FROM dbo.Orders
ORDER BY CustomerId, OrderedAt, OrderId;
GO

WITH Ranked AS
(
    SELECT
        OrderId,
        CustomerId,
        TotalAmount,
        ROW_NUMBER() OVER
        (
            PARTITION BY CustomerId
            ORDER BY TotalAmount DESC, OrderId
        ) AS rn
    FROM dbo.Orders
)
SELECT
    OrderId,
    CustomerId,
    TotalAmount
FROM Ranked
WHERE rn <= 2
ORDER BY CustomerId, rn;
GO
```

### Walkthrough — execution / state / cost

1. Server chia logic theo CustomerId và xác định thứ tự riêng cho từng window.
2. ROW_NUMBER dùng OrderId phân định tie; RANK chỉ theo amount để hai giá bằng nhau cùng hạng.
3. SUM dùng ROWS frame tường minh; LAG đầu partition trả NULL khi không chỉ định default.
4. CTE Ranked giữ rn để WHERE ngoài lọc top 2. Sort/memory có thể đáng kể; index phù hợp có thể giảm sort, không hứa mọi window dùng cùng một thứ tự vật lý.

### Mini-check

Hai order cùng ngày: bỏ OrderId khỏi running order và dùng frame mặc định có thể đổi tổng ở row đầu thế nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### OVER

Window function có dạng:

```sql
function() OVER (...)
```

Window có thể định nghĩa PARTITION BY, ORDER BY và frame.

### PARTITION BY

Tạo nhóm logic nhưng không collapse row.

Mỗi customer có window riêng.

### ROW_NUMBER, RANK, DENSE_RANK

- ROW_NUMBER luôn tạo 1,2,3...
- RANK giữ tie và tạo gap: 1,2,2,4.
- DENSE_RANK giữ tie nhưng không gap: 1,2,2,3.

### Running total

Frame:

```sql
ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
```

nghĩa là từ đầu partition tới row hiện tại.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| GROUP BY | một row mỗi group | mất detail nếu không nối lại |
| window | giữ row và thêm metric | cần order/frame rõ |
| RANK/DENSE_RANK | giữ tie | topN hạng có thể trả hơnNrow |

### Misconception check

**Đúng hay sai?** ORDER BY trong OVER tự sắp output cuối.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: cần ORDER BY ngoài nếu presentation cần thứ tự.

</details>

**Đúng hay sai?** ROW_NUMBER và RANK đều trả đúng 2 row khi lọc<=2.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: RANK có tie nên có thể trả hơn2 row.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace ranking.

- **Working Developer — dùng khi làm việc:** frame/tie và topN.

- **Deep Dive — có thể quay lại sau:** sort/index/memory theo plan.

### GROUP BY vs window

GROUP BY:

```text
n detail rows -> ít summary rows
```

Window:

```text
n detail rows -> vẫn n rows + metric
```

### Top-N per group

Pattern:

```text
ROW_NUMBER PARTITION
-> CTE
-> WHERE rn <= N
```

rất phổ biến.

### LAG/LEAD

Cho phép nhìn row trước/sau mà không self-join phức tạp.

## 6. Lỗi thường gặp

### ROW_NUMBER không có tiebreaker

Nếu ORDER BY không deterministic, numbering giữa các lần chạy có thể khác.

### Running total dùng frame mặc định mà không hiểu

Nên ghi frame rõ khi semantics quan trọng.

### Dùng GROUP BY rồi join ngược lại

Nhiều trường hợp window function đơn giản hơn.

### Filter window function trực tiếp ở WHERE cùng level

Dùng CTE/subquery rồi filter.

## 7. Khi nào KHÔNG dùng

Không dùng ROW_NUMBER không tiebreaker cho pagination cần ổn định. Không join summary ngược detail theo thói quen khi window diễn đạt đúng và đơn giản hơn.

## 8. Production notes & scale check

Gate kiểm ranking có tie, running totals, NULL đầu partition và top 2. Không gắn ngưỡng milliseconds; plan có nhiều window order có thể cần nhiều sort hoặc spool. Khi chỉ cần tổng mỗi khách, GROUP BY vẫn hợp hơn.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Lấy order mới nhất mỗi customer.

### Bài 2

Tính revenue running theo toàn hệ thống.

### Bài 3

Dùng LEAD để tính ngày tới order tiếp theo.

### Bài 4

So sánh ROW_NUMBER/RANK/DENSE_RANK với dữ liệu tie.

### Bài 5

Tính phần trăm order trên tổng revenue customer bằng SUM OVER.

## 10. Bài tập tích hợp liên module — Judgment

Từ stable sort Module 07: giữ tie trong rank khác phân định tie cho vị trí thế nào? Thiết kế báo cáo “2 đơn” và “2mức giá” thành hai contract riêng.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Frame chọn những row nào?
2. RANK tạo gap khi nào?
3. Window có collapse detail không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi dùng được OVER/PARTITION BY.
- [ ] Tôi phân biệt ROW_NUMBER/RANK/DENSE_RANK.
- [ ] Tôi tính được running total.
- [ ] Tôi dùng LAG/LEAD.
- [ ] Tôi lấy được top-N per group.
- [ ] Tôi phân biệt GROUP BY và window.

Điều hướng:

- Bài trước: [CTE và recursive CTE](./11-cte-va-recursive-cte.md)
- Bài tiếp theo: [View, stored procedure, function và trigger](./13-view-stored-procedure-function-trigger.md)
