# Set operator: UNION, INTERSECT, EXCEPT

## 1. Mục tiêu

Sau bài này, bạn có thể:

- kết hợp rowset bằng UNION/UNION ALL;
- tìm phần giao bằng INTERSECT;
- tìm chênh lệch bằng EXCEPT;
- hiểu column count/type compatibility;
- phân biệt UNION với JOIN;
- biết UNION loại duplicate còn UNION ALL không;
- dùng set operator cho reconciliation.

## 2. Bài toán mở đầu

Ta có hai nguồn SKU:

```text
CatalogA
CatalogB
```

Cần biết:

- toàn bộ SKU của cả hai;
- SKU xuất hiện ở cả hai;
- SKU chỉ có ở A;
- SKU chỉ có ở B.

Đây là bài toán set, không phải join enrichment.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_10') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_10
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_10;
END;
GO

CREATE DATABASE CommerceLab08_10;
GO
USE CommerceLab08_10;
GO

CREATE TABLE dbo.CatalogA
(
    Sku varchar(20) NOT NULL
        CONSTRAINT PK_CatalogA PRIMARY KEY
);

CREATE TABLE dbo.CatalogB
(
    Sku varchar(20) NOT NULL
        CONSTRAINT PK_CatalogB PRIMARY KEY
);
GO

INSERT INTO dbo.CatalogA VALUES
('A-01'),('A-02'),('COMMON-01');

INSERT INTO dbo.CatalogB VALUES
('B-01'),('B-02'),('COMMON-01');
GO

SELECT Sku FROM dbo.CatalogA
UNION
SELECT Sku FROM dbo.CatalogB
ORDER BY Sku;
GO

SELECT Sku FROM dbo.CatalogA
UNION ALL
SELECT Sku FROM dbo.CatalogB
ORDER BY Sku;
GO

SELECT Sku FROM dbo.CatalogA
INTERSECT
SELECT Sku FROM dbo.CatalogB;
GO

SELECT Sku FROM dbo.CatalogA
EXCEPT
SELECT Sku FROM dbo.CatalogB;
GO

SELECT Sku FROM dbo.CatalogB
EXCEPT
SELECT Sku FROM dbo.CatalogA;
GO
```

## 4. Giải thích cơ chế

### UNION

Kết hợp row từ hai query và loại duplicate.

```text
A ∪ B
```

### UNION ALL

Giữ mọi row, kể cả duplicate.

Nếu không cần deduplicate, `UNION ALL` thường ít việc hơn.

### INTERSECT

Chỉ giữ row có ở cả hai set.

### EXCEPT

```text
A EXCEPT B
```

giữ row có ở A nhưng không ở B.

Thứ tự operand quan trọng.

## 5. Kiến thức nền

### Shape compatibility

Hai phía cần:

- cùng số column;
- type tương thích theo vị trí.

Column name của result thường lấy từ query đầu.

### UNION khác JOIN

UNION xếp row **dọc**:

```text
rows A
+
rows B
```

JOIN ghép column **ngang** dựa trên relation.

### Reconciliation

Set operator rất hữu ích khi:

- migrate dữ liệu;
- đối chiếu source/target;
- kiểm tra đồng bộ;
- validation ETL.

## 6. Lỗi thường gặp

### Dùng UNION khi UNION ALL đủ

Dedup có thể cần sort/hash thêm.

### ORDER BY trong từng nhánh

ORDER BY áp dụng cho result cuối, trừ các cấu trúc đặc biệt.

### Nhầm EXCEPT là symmetric difference

`A EXCEPT B` khác `B EXCEPT A`.

### Dùng UNION để thay JOIN

Nếu cần CustomerName cạnh OrderId, đó là join.

## 7. Bài tập

### Bài 1

Gộp active và archived SKU bằng UNION ALL.

### Bài 2

Tìm email tồn tại ở cả CRM và Shop.

### Bài 3

Tìm row thiếu sau migration bằng EXCEPT hai chiều.

### Bài 4

So sánh execution plan UNION và UNION ALL.

### Bài 5

Giải thích khi nào JOIN và UNION cho số column khác nhau.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt UNION và UNION ALL.
- [ ] Tôi dùng được INTERSECT/EXCEPT.
- [ ] Tôi hiểu operand của EXCEPT có thứ tự.
- [ ] Tôi phân biệt set operator với JOIN.
- [ ] Tôi kiểm tra type/column compatibility.
- [ ] Tôi dùng UNION ALL khi không cần dedup.

Điều hướng:

- Bài trước: [Subquery và correlated subquery](./09-subquery-va-correlated-subquery.md)
- Bài tiếp theo: [CTE và recursive CTE](./11-cte-va-recursive-cte.md)
