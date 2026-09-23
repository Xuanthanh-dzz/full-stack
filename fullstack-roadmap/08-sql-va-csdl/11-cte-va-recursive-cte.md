# CTE và recursive CTE

> **Last verified:** pending — chưa chạy lại gate retrofit  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- CTE đặt tên một query trong một statement; recursive CTE lặp theo quan hệ cha–con.
- Dùng để chia bước logic hoặc duyệt hierarchy có cận.
- CTE không mặc định là bảng tạm lưu kết quả, và FK tự tham chiếu không ngăn cycle.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng common table expression để chia query thành bước dễ đọc;
- hiểu CTE không mặc định materialize;
- dùng recursive CTE cho hierarchy;
- thiết kế anchor member và recursive member;
- giới hạn recursion;
- phân biệt CTE với temp table.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Bắt đầu từ phòng ban gốc, ghi những phòng trực thuộc rồi tiếp tục hỏi con của các phòng vừa tìm. Khi một lượt không có phòng mới, phép duyệt dừng; dữ liệu đi vòng sẽ phá điều kiện dừng ấy.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| CTE | tên tạm cho biểu thức query trong một statement | CategoryTree |
| anchor | rowset khởi đầu | category1 |
| recursive member | bước suy rowset tiếp theo từ lượt trước | join ParentCategoryId |
| materialize | lưu kết quả trung gian để dùng lại | temp table, không mặc định CTE |

### Ví dụ nhỏ — tính tay trước

Gốc1 có con2,5;2 có 3,4;5 có 6,7. Các depth là0:[1],1:[2,5],2:[3,4,6,7]. Output ORDER BY Path là thứ tự chữ của path, không phải cam kết thứ tự chạy từng node.

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

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. Anchor chọn gốc1 với Depth0 và cast Path sang nvarchar(1000).
2. Recursive member nối mỗi row vừa có với children, tăng depth và nối path.
3. UNION ALL gom các lượt; dừng khi không sinh thêm row hoặc MAXRECURSION báo lỗi.
4. Server giữ state thực thi theo plan; path dài thêm và sort cuối có cost. CTE không còn dùng được ở statement tiếp theo.

### Mini-check

Nếu parent của gốc1 đổi thành7, FK có cấm vòng1→5→7→1 không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| CTE | tổ chức một statement | không hứa cache/reuse vật lý |
| derived table | query con trong FROM | cùng hướng tổ chức logic, cú pháp khác |
| temp table | dữ liệu trung gian qua nhiều statement | ghi tempdb, có thể thêm index/statistics |

### Misconception check

**Đúng hay sai?** CTE được tham chiếu hai lần chắc chắn chỉ tính một lần.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: xem plan, không có guarantee materialization.

</details>

**Đúng hay sai?** MAXRECURSION sửa được cycle trong dữ liệu.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chỉ dừng bằng lỗi, cần sửa invariant/path detection.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** anchor và từng lượt.

- **Working Developer — dùng khi làm việc:** scope/cycle và cận path.

- **Deep Dive — có thể quay lại sau:** plan/temp table khi có evidence.

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

Trong T-SQL, phải dùng UNION ALL giữa anchor cuối và recursive member đầu, cũng như giữa các recursive member. Không thể tùy ý thay bằng UNION để xử lý cycle ([Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/queries/recursive-common-table-expression-transact-sql?view=sql-server-ver17)).

### Hierarchy có cycle

Foreign key self-reference không tự ngăn mọi cycle logic.

## 7. Khi nào KHÔNG dùng

Không dùng recursion vô hạn bằng MAXRECURSION0 cho dữ liệu chưa kiểm. Không chọn temp table chỉ vì query dài nếu CTE đủ rõ và plan ổn.

## 8. Production notes & scale check

Gate kiểm7 node/depth/path và case cycle có lỗi recursion. Path cast1000 là cận demo, không bảo đảm hierarchy tùy ý không bị cắt chuỗi. Cần chọn cận và policy vượt cận trước dùng cho cây dữ liệu thật.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

So BFS/DFS Module 07: state chờ duyệt nằm ở đâu khi chuyển sang SQL? Với cây20 node, cần materialized path hay adjacency list hiện tại đã đủ?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Anchor tạo gì?
2. CTE sống qua mấy statement?
3. MAXRECURSION là kết quả hay lỗi?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi viết được CTE thường.
- [ ] Tôi hiểu CTE không mặc định materialize.
- [ ] Tôi thiết kế được anchor/recursive member.
- [ ] Tôi dùng MAXRECURSION có chủ đích.
- [ ] Tôi phân biệt CTE và temp table.
- [ ] Tôi mô hình hierarchy bằng self-reference.

Điều hướng:

- Bài trước: [Set operator](./10-set-operator-union-intersect-except.md)
- Bài tiếp theo: [Window function](./12-window-function.md)
