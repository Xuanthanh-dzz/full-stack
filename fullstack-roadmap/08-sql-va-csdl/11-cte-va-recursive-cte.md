# CTE và recursive CTE

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng common table expression để chia query thành bước dễ đọc;
- hiểu CTE không mặc định materialize;
- dùng recursive CTE cho hierarchy;
- thiết kế anchor member và recursive member;
- giới hạn recursion;
- phân biệt CTE với temp table.

## 2. Bài toán mở đầu

Category có cấu trúc:

```text
Electronics
├── Computer
│   ├── Laptop
│   └── Desktop
└── Accessory
    ├── Keyboard
    └── Mouse
```

Ta cần lấy toàn bộ descendant của Electronics và hiển thị depth/path.

Recursive CTE mô tả bài toán hierarchy tự nhiên.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_11') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_11
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_11;
END;
GO

CREATE DATABASE CommerceLab08_11;
GO
USE CommerceLab08_11;
GO

CREATE TABLE dbo.Categories
(
    CategoryId int NOT NULL
        CONSTRAINT PK_Categories PRIMARY KEY,
    ParentCategoryId int NULL,
    Name nvarchar(100) NOT NULL,
    CONSTRAINT FK_Categories_Parent
        FOREIGN KEY (ParentCategoryId)
        REFERENCES dbo.Categories(CategoryId)
);
GO

INSERT INTO dbo.Categories
(CategoryId, ParentCategoryId, Name)
VALUES
(1,NULL,N'Electronics'),
(2,1,N'Computer'),
(3,2,N'Laptop'),
(4,2,N'Desktop'),
(5,1,N'Accessory'),
(6,5,N'Keyboard'),
(7,5,N'Mouse');
GO

WITH CategoryTree AS
(
    SELECT
        CategoryId,
        ParentCategoryId,
        Name,
        0 AS Depth,
        CAST(Name AS nvarchar(1000)) AS [Path]
    FROM dbo.Categories
    WHERE CategoryId = 1

    UNION ALL

    SELECT
        c.CategoryId,
        c.ParentCategoryId,
        c.Name,
        t.Depth + 1,
        CAST(t.[Path] + N' > ' + c.Name AS nvarchar(1000))
    FROM dbo.Categories AS c
    INNER JOIN CategoryTree AS t
        ON c.ParentCategoryId = t.CategoryId
)
SELECT
    CategoryId,
    ParentCategoryId,
    Name,
    Depth,
    [Path]
FROM CategoryTree
ORDER BY [Path]
OPTION (MAXRECURSION 100);
GO

WITH PaidOrders AS
(
    SELECT 1 AS CustomerId, CAST(1000000 AS decimal(19,4)) AS Amount
    UNION ALL
    SELECT 1, 2000000
    UNION ALL
    SELECT 2, 5000000
)
SELECT
    CustomerId,
    SUM(Amount) AS Revenue
FROM PaidOrders
GROUP BY CustomerId
ORDER BY CustomerId;
GO
```

## 4. Giải thích cơ chế

### Non-recursive CTE

CTE giúp đặt tên cho query trung gian:

```sql
WITH PaidOrders AS (...)
SELECT ...
FROM PaidOrders;
```

Nó chủ yếu là công cụ tổ chức query.

Không nên mặc định CTE tạo một table vật lý tạm.

### Recursive CTE

Gồm:

```text
anchor member
UNION ALL
recursive member
```

Anchor tạo level 0.

Recursive member nối level hiện tại sang level tiếp theo.

### MAXRECURSION

Nếu hierarchy có cycle do dữ liệu sai, recursion có thể không dừng theo ý định.

```sql
OPTION (MAXRECURSION 100)
```

đặt guard.

## 5. Kiến thức nền

### CTE hay derived table

CTE thường dễ đọc hơn khi query có nhiều bước hoặc cùng một concept cần đặt tên.

### CTE hay temp table

Temp table phù hợp khi:

- cần reuse nhiều statement;
- cần index riêng;
- muốn materialize/intermediate statistics;
- query cực phức tạp cần break optimization boundary.

### Hierarchy model

Adjacency list:

```text
CategoryId
ParentCategoryId
```

đơn giản nhưng query descendant cần recursion.

Có các model khác như materialized path, hierarchyid, nested sets tùy workload.

## 6. Lỗi thường gặp

### Nghĩ CTE luôn nhanh hơn subquery

CTE không phải performance magic.

### Recursive member không tiến gần điểm dừng

Có thể sinh recursion vô hạn về logic.

### Dùng UNION thay UNION ALL

Recursive CTE thông thường dùng UNION ALL; dedup không cần thiết có thể thêm chi phí và đổi semantics.

### Hierarchy có cycle

Foreign key self-reference không tự ngăn mọi cycle logic.

## 7. Bài tập

### Bài 1

Tìm toàn bộ ancestor của một category.

### Bài 2

Tính depth toàn cây từ mọi root.

### Bài 3

Tạo organization chart Employee -> Manager.

### Bài 4

Tạo cycle thử nghiệm và quan sát MAXRECURSION.

### Bài 5

Rewrite một derived table dài thành CTE có tên rõ nghĩa.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi viết được CTE thường.
- [ ] Tôi hiểu CTE không mặc định materialize.
- [ ] Tôi thiết kế được anchor/recursive member.
- [ ] Tôi dùng MAXRECURSION có chủ đích.
- [ ] Tôi phân biệt CTE và temp table.
- [ ] Tôi mô hình hierarchy bằng self-reference.

Điều hướng:

- Bài trước: [Set operator](./10-set-operator-union-intersect-except.md)
- Bài tiếp theo: [Window function](./12-window-function.md)
