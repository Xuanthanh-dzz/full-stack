# Subquery và correlated subquery

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Subquery dùng một truy vấn trong truy vấn khác theo shape cần thiết.
- EXISTS/NOT EXISTS diễn đạt có hay không có row liên quan.
- Correlated là phụ thuộc logic vào outer row, không khẳng định server chạy riêng một query mạng cho mỗi row.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- viết scalar, table và predicate subquery;
- dùng EXISTS/NOT EXISTS;
- hiểu correlated subquery tham chiếu outer row;
- phân biệt IN và EXISTS theo intent;
- viết anti-semi join bằng NOT EXISTS;
- tránh `NOT IN` + NULL trap;
- biết optimizer có thể rewrite subquery thành join/operator khác.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Với mỗi thẻ khách, câu hỏi chỉ là “có hóa đơn đã trả không”, không cần đem mọi hóa đơn vào kết quả. EXISTS diễn đạt đúng câu hỏi có/không ấy và giữ mỗi thẻ khách một lần.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| scalar subquery | trả một cột, tối đa một row | MAX ngày đơn |
| correlated | tham chiếu dữ liệu từ query ngoài | o.CustomerId=c.CustomerId |
| semi join | giữ row trái có match, không nhân theo số match | EXISTS |
| anti match | giữ row trái không có match | NOT EXISTS |

### Ví dụ nhỏ — tính tay trước

An có Paid và Pending, Bình có Paid, Chi không có order. EXISTS Paid trả An,Bình mỗi người một lần. NOT EXISTS order trả Chi; MAX ngày của Chi là NULL.

Cần tìm:

- customer có ít nhất một paid order;
- customer chưa từng order;
- product có giá cao hơn average;
- order mới nhất của mỗi customer.

Subquery cho phép một query dùng kết quả của query khác.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_09') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_09
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_09;
END;
GO

CREATE DATABASE CommerceLab08_09;
GO
USE CommerceLab08_09;
GO

CREATE TABLE dbo.Customers
(
    CustomerId int NOT NULL
        CONSTRAINT PK_Customers PRIMARY KEY,
    Name nvarchar(100) NOT NULL
);

CREATE TABLE dbo.Orders
(
    OrderId int NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    CustomerId int NOT NULL,
    Status varchar(20) NOT NULL,
    TotalAmount decimal(19,4) NOT NULL,
    OrderedAt date NOT NULL,
    CONSTRAINT FK_Orders_Customers
        FOREIGN KEY (CustomerId)
        REFERENCES dbo.Customers(CustomerId)
);
GO

INSERT INTO dbo.Customers VALUES
(1,N'An'),(2,N'Bình'),(3,N'Chi');

INSERT INTO dbo.Orders VALUES
(101,1,'Paid',1000000,'2026-01-01'),
(102,1,'Pending',2000000,'2026-02-01'),
(103,2,'Paid',9000000,'2026-02-10');
GO

SELECT
    c.CustomerId,
    c.Name
FROM dbo.Customers AS c
WHERE EXISTS
(
    SELECT 1
    FROM dbo.Orders AS o
    WHERE o.CustomerId = c.CustomerId
      AND o.Status = 'Paid'
)
ORDER BY c.CustomerId;
GO

SELECT
    c.CustomerId,
    c.Name
FROM dbo.Customers AS c
WHERE NOT EXISTS
(
    SELECT 1
    FROM dbo.Orders AS o
    WHERE o.CustomerId = c.CustomerId
)
ORDER BY c.CustomerId;
GO

SELECT
    o.OrderId,
    o.CustomerId,
    o.TotalAmount
FROM dbo.Orders AS o
WHERE o.TotalAmount >
(
    SELECT AVG(o2.TotalAmount)
    FROM dbo.Orders AS o2
)
ORDER BY o.OrderId;
GO

SELECT
    c.CustomerId,
    c.Name,
    (
        SELECT MAX(o.OrderedAt)
        FROM dbo.Orders AS o
        WHERE o.CustomerId = c.CustomerId
    ) AS LastOrderDate
FROM dbo.Customers AS c
ORDER BY c.CustomerId;
GO
```

### Walkthrough — execution / state / cost

1. Query ngoài cung cấp CustomerId cho điều kiện liên quan trong query con theo nghĩa logic.
2. EXISTS kiểm có row; các cột SELECT trong query con không được đưa ra kết quả.
3. Scalar query0 row cho NULL, nhiều hơn1 row gây lỗi nếu không aggregate thu về1 row.
4. Optimizer có thể decorrelate hoặc chọn semi join; đo plan để biết đọc/index/memory thực tế. Một SQL request không tự là N+1 network requests.

### Mini-check

3 NOT IN (1,NULL) là TRUE hay UNKNOWN? WHERE sẽ giữ row không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Scalar subquery

Phải trả tối đa một value:

```sql
SELECT AVG(TotalAmount)
FROM Orders
```

### EXISTS

EXISTS hỏi:

```text
có ít nhất một row thỏa không?
```

Nó phù hợp membership theo relation.

### Correlated subquery

Query con tham chiếu outer alias:

```sql
WHERE o.CustomerId = c.CustomerId
```

Về mặt logic, nó phụ thuộc row bên ngoài.

Optimizer có thể biến thành semi join hoặc plan hiệu quả hơn.

### NOT EXISTS

Rất phù hợp tìm “không có child”.

```text
customers with no orders
```

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| EXISTS | kiểm tồn tại, giữ multiplicity trái | không cần JOIN+DISTINCT |
| JOIN | cần cột phía phải hoặc mọi cặp | có thể nhân row |
| NOT IN | so với danh sách giá trị | NULL trong danh sách làm UNKNOWN |

### Misconception check

**Đúng hay sai?** JOIN luôn nhanh hơn subquery.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: optimizer/workload quyết định.

</details>

**Đúng hay sai?** NOT IN và NOT EXISTS luôn tương đương.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai khi NULL và predicate có semantics khác.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** shape subquery.

- **Working Developer — dùng khi làm việc:** NULL và cardinality.

- **Deep Dive — có thể quay lại sau:** decorrelation/plan nếu query chậm.

### NOT IN và NULL

Nếu subquery của `NOT IN` chứa NULL, three-valued logic có thể làm kết quả bất ngờ.

`NOT EXISTS` thường rõ intent hơn cho anti-match.

### Derived table

Subquery trong FROM:

```sql
FROM
(
    SELECT CustomerId, SUM(TotalAmount) AS Revenue
    FROM Orders
    GROUP BY CustomerId
) AS x
```

tạo rowset tạm về mặt logic.

### Subquery hay JOIN?

Không có rule “JOIN luôn nhanh hơn”.

Viết intent rõ, sau đó xem execution plan.

## 6. Lỗi thường gặp

### Scalar subquery trả nhiều row

SQL Server báo lỗi nếu expression cần một value nhưng subquery trả nhiều hơn một.

### NOT IN với nullable column

Có thể trả zero row ngoài dự đoán.

### Correlated subquery tính aggregate nặng

Có thể cần rewrite hoặc index; đo plan thay vì đoán.

### Dùng SELECT * trong EXISTS

Không cần column cụ thể.

`SELECT 1` thể hiện intent rõ.

## 7. Khi nào KHÔNG dùng

Không dùng scalar subquery nếu nghiệp vụ thật sự có nhiều kết quả mà chưa chọn rule. Không rewrite EXISTS thành JOIN rồi thêm DISTINCT chỉ vì nghĩ JOIN nhanh hơn.

## 8. Production notes & scale check

Gate kiểm membership, anti-match, average threshold và scalar NULL; negative case nhiều row phải báo lỗi. SELECT1 trong EXISTS diễn đạt intent, không mặc định nhanh hơn SELECT*. Ca NULL minh họa lý do chọn NOT EXISTS.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Tìm customer có order trên 5 triệu.

### Bài 2

Tìm product chưa từng được bán bằng NOT EXISTS.

### Bài 3

Tìm order lớn hơn average của chính customer đó.

### Bài 4

Rewrite một EXISTS thành JOIN và so execution plan.

### Bài 5

Tạo demo `NOT IN` chứa NULL và giải thích kết quả.

## 10. Bài tập tích hợp liên module — Judgment

Từ LINQ IEnumerable Module 05, Any và Join trả shape khác nhau thế nào? Đến Module 09 cần phân biệt query SQL một lần với loop client gọi DB nhiều lần.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Scalar0 row trả gì?
2. EXISTS có nhân khách theo số đơn không?
3. Correlation mô tả logic hay số network calls?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi viết được scalar subquery.
- [ ] Tôi dùng EXISTS/NOT EXISTS.
- [ ] Tôi hiểu correlated subquery.
- [ ] Tôi biết NOT IN + NULL trap.
- [ ] Tôi không khẳng định JOIN luôn nhanh hơn.
- [ ] Tôi kiểm tra plan khi performance quan trọng.

Điều hướng:

- Bài trước: [JOIN](./08-inner-left-right-full-cross-join.md)
- Bài tiếp theo: [Set operator: UNION, INTERSECT, EXCEPT](./10-set-operator-union-intersect-except.md)
