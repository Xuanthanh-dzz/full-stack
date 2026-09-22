# Hàm scalar, CASE và xử lý NULL

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng các hàm string, numeric và date phổ biến;
- dùng `CASE` để tạo giá trị dẫn xuất;
- dùng `COALESCE`, `NULLIF` và `ISNULL`;
- phân biệt xử lý presentation với business invariant;
- tránh biến column thành expression không SARGable khi filter;
- hiểu hàm scalar có thể ảnh hưởng execution plan.

## 2. Bài toán mở đầu

Dashboard cần hiển thị:

- tên product đã trim;
- mức giá `Budget / Standard / Premium`;
- mô tả fallback khi NULL;
- tuổi đơn hàng theo ngày;
- tỷ lệ discount không chia cho 0.

Đây là các phép biến đổi theo từng row.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_06') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_06
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_06;
END;
GO

CREATE DATABASE CommerceLab08_06;
GO
USE CommerceLab08_06;
GO

CREATE TABLE dbo.Products
(
    ProductId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Name nvarchar(160) NOT NULL,
    Price decimal(19,4) NOT NULL,
    ListPrice decimal(19,4) NULL,
    Description nvarchar(500) NULL,
    CreatedAt datetime2(0) NOT NULL
);
GO

INSERT INTO dbo.Products
(
    Name, Price, ListPrice, Description, CreatedAt
)
VALUES
(N'  Keyboard Pro  ', 1200000, 1500000, NULL, '2026-01-01'),
(N'Office Mouse', 350000, 350000, N'Basic mouse', '2026-02-01'),
(N'4K Monitor', 7200000, NULL, N'27-inch monitor', '2026-03-01');
GO

SELECT
    ProductId,
    TRIM(Name) AS CleanName,
    UPPER(LEFT(TRIM(Name), 3)) AS ShortCode,
    Price,
    CASE
        WHEN Price < 500000 THEN 'Budget'
        WHEN Price < 3000000 THEN 'Standard'
        ELSE 'Premium'
    END AS PriceTier,
    COALESCE(Description, N'(chưa có mô tả)') AS DisplayDescription,
    DATEDIFF(day, CreatedAt, SYSUTCDATETIME()) AS AgeInDays,
    CAST(
        (COALESCE(ListPrice, Price) - Price)
        / NULLIF(COALESCE(ListPrice, Price), 0)
        * 100
        AS decimal(6,2)
    ) AS DiscountPercent
FROM dbo.Products
ORDER BY ProductId;
GO
```

## 4. Giải thích cơ chế

### Scalar function

Scalar function nhận một hoặc nhiều giá trị và trả một giá trị.

Ví dụ:

```sql
TRIM(Name)
UPPER(Name)
ROUND(Price, 0)
DATEDIFF(day, CreatedAt, SYSUTCDATETIME())
```

### CASE

`CASE` là expression:

```sql
CASE
    WHEN condition THEN value
    ELSE value
END
```

Nó có thể nằm trong:

- SELECT;
- ORDER BY;
- aggregate;
- UPDATE.

### COALESCE

```sql
COALESCE(A, B, C)
```

trả expression đầu tiên không NULL.

### NULLIF

```sql
NULLIF(x, 0)
```

trả NULL nếu `x = 0`.

Rất hữu ích để tránh chia 0.

## 5. Kiến thức nền

### ISNULL và COALESCE

`ISNULL` là T-SQL specific và nhận hai argument.

`COALESCE` theo chuẩn SQL và nhận nhiều argument.

Chúng có khác biệt về type/nullability inference; không coi là hoàn toàn interchangeable trong mọi expression.

### Computed value không nhất thiết lưu

`PriceTier` có thể derive từ Price.

Nếu lưu cả hai, bạn phải giữ chúng đồng bộ.

Chỉ persist khi có lý do business/performance rõ.

### Function trên indexed column

Predicate:

```sql
WHERE YEAR(CreatedAt) = 2026
```

thường khó dùng index seek hơn:

```sql
WHERE CreatedAt >= '2026-01-01'
  AND CreatedAt <  '2027-01-01'
```

Bài SARGability sẽ đi sâu hơn.

## 6. Lỗi thường gặp

### Nhét business state vào CASE rải rác

Nếu trạng thái quan trọng được tính ở 20 query khác nhau, logic dễ lệch.

### Chia cho 0

Dùng `NULLIF(denominator, 0)` khi NULL result là semantics chấp nhận được.

### Format tiền/ngày trong database quá sớm

Presentation formatting thường thuộc UI/application.

Database nên trả type gốc khi có thể.

### Dùng function trong WHERE theo thói quen

Có thể phá khả năng tận dụng index.

## 7. Bài tập

### Bài 1

Tạo label stock:

```text
0 -> OutOfStock
1-10 -> Low
>10 -> Available
```

### Bài 2

Dùng `COALESCE` chọn phone rồi email làm contact.

### Bài 3

Tính số ngày từ OrderedAt tới ShippedAt; nếu chưa ship thì tới hiện tại.

### Bài 4

Viết hai version filter năm 2026 và giải thích version nào SARGable hơn.

### Bài 5

Tìm trường hợp `ISNULL` và `COALESCE` suy luận type khác nhau.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi dùng được scalar function phổ biến.
- [ ] Tôi viết được CASE.
- [ ] Tôi hiểu COALESCE/NULLIF.
- [ ] Tôi tránh chia 0.
- [ ] Tôi không format presentation quá sớm trong DB.
- [ ] Tôi nghĩ tới SARGability khi dùng function trong WHERE.

Điều hướng:

- Bài trước: [Filter, sort và pagination](./05-filter-sort-va-pagination.md)
- Bài tiếp theo: [GROUP BY, aggregate và HAVING](./07-group-by-aggregate-va-having.md)
