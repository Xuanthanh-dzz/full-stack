# Window function

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

Dashboard cần:

- xếp hạng order theo giá trị trong từng customer;
- lấy 2 order lớn nhất của mỗi customer;
- tính running revenue;
- so order hiện tại với order trước.

Nếu GROUP BY, detail row bị collapse.

Window function giữ detail row nhưng vẫn tính trên “cửa sổ” các row liên quan.

## 3. Lời giải bằng SQL

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

## 4. Giải thích cơ chế

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

## 5. Kiến thức nền

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

## 7. Bài tập

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

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi dùng được OVER/PARTITION BY.
- [ ] Tôi phân biệt ROW_NUMBER/RANK/DENSE_RANK.
- [ ] Tôi tính được running total.
- [ ] Tôi dùng LAG/LEAD.
- [ ] Tôi lấy được top-N per group.
- [ ] Tôi phân biệt GROUP BY và window.

Điều hướng:

- Bài trước: [CTE và recursive CTE](./11-cte-va-recursive-cte.md)
- Bài tiếp theo: [View, stored procedure, function và trigger](./13-view-stored-procedure-function-trigger.md)
