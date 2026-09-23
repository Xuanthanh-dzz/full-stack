# INNER, LEFT, RIGHT, FULL và CROSS JOIN

> **Last verified:** pending — chưa chạy lại gate retrofit  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- JOIN ghép các cặp row thỏa điều kiện; outer join còn giữ row không khớp.
- Dùng khóa và cardinality để dự đoán số row trước khi chạy.
- Một row cha có nhiều con sẽ lặp; DISTINCT không sửa được điều kiện nối sai.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- join table theo PK/FK;
- phân biệt INNER và OUTER JOIN;
- hiểu row preservation của LEFT/RIGHT/FULL;
- dùng CROSS JOIN có chủ đích;
- tránh accidental Cartesian product;
- biết predicate đặt ở ON hay WHERE có thể đổi semantics;
- đọc cardinality của join.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Đặt thẻ khách cạnh từng hóa đơn của họ. An có hai hóa đơn thì thẻ An xuất hiện hai lần; Chi chưa mua có thể vẫn được giữ bằng một dòng trống phía hóa đơn nếu chọn LEFT JOIN.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| INNER JOIN | chỉ các cặp thỏa ON | 3 đơn có khách |
| LEFT JOIN | giữ mọi row trái, thêm NULL nếu không match | Chi vẫn xuất hiện |
| cardinality | số row và số match dự kiến | 1 khách tới nhiều đơn |
| CROSS JOIN | mọi cặp giữa hai phía | 3 khách×2 sản phẩm |

### Ví dụ nhỏ — tính tay trước

Customers An,Bình,Chi; Orders101/102 của An,103 của Bình. INNER có 3 row; LEFT có 4 row; CROSS với2products có 6 row. LEFT với Paid trong ON giữ Chi, chuyển sang WHERE thì mất Chi.

Ta có:

```text
Customers
Orders
Products
OrderItems
```

Để hiển thị:

```text
OrderId
CustomerName
ProductName
Quantity
UnitPrice
```

cần nối nhiều table.

Join là kỹ năng SQL cốt lõi nhất cho backend.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_08') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_08
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_08;
END;
GO

CREATE DATABASE CommerceLab08_08;
GO
USE CommerceLab08_08;
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
    CustomerId int NOT NULL
        CONSTRAINT FK_Orders_Customers
        REFERENCES dbo.Customers(CustomerId),
    Status varchar(20) NOT NULL
);

CREATE TABLE dbo.Products
(
    ProductId int NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Name nvarchar(100) NOT NULL
);
GO

INSERT INTO dbo.Customers VALUES
(1,N'An'),(2,N'Bình'),(3,N'Chi');

INSERT INTO dbo.Orders VALUES
(101,1,'Paid'),
(102,1,'Pending'),
(103,2,'Paid');

INSERT INTO dbo.Products VALUES
(10,N'Keyboard'),(20,N'Mouse');
GO

SELECT
    o.OrderId,
    c.Name AS CustomerName,
    o.Status
FROM dbo.Orders AS o
INNER JOIN dbo.Customers AS c
    ON c.CustomerId = o.CustomerId
ORDER BY o.OrderId;
GO

SELECT
    c.CustomerId,
    c.Name,
    o.OrderId,
    o.Status
FROM dbo.Customers AS c
LEFT JOIN dbo.Orders AS o
    ON o.CustomerId = c.CustomerId
ORDER BY c.CustomerId, o.OrderId;
GO

SELECT
    c.Name,
    p.Name AS ProductName
FROM dbo.Customers AS c
CROSS JOIN dbo.Products AS p
ORDER BY c.CustomerId, p.ProductId;
GO
```

### Walkthrough — execution / state / cost

1. ON xét cặp theo CustomerId; INNER xuất các cặp match.
2. LEFT bổ sung một row với cột phải NULL cho khách không match.
3. WHERE áp lên rowset sau bước nối theo mô hình logic; predicate phải TRUE mới giữ.
4. Server chọn nested loops/hash/merge join; index, cardinality và memory ảnh hưởng cost. Không có vòng lặp client cho từng customer trong sample.

### Mini-check

COUNT(*) sau LEFT JOIN cho Chi bằng1 hay0? COUNT(o.OrderId) thì sao?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### INNER JOIN

Chỉ giữ row có match hai bên.

Đây là ghép các **cặp row thỏa ON**, không phải phép giao hai tập customer và order. Một customer có hai order sẽ xuất hiện trong hai cặp.

### LEFT JOIN

Giữ toàn bộ row bên trái.

Nếu không match, column bên phải thành NULL.

Customer Chi vẫn xuất hiện dù chưa có order.

### RIGHT JOIN

Tương đương đổi vị trí table của LEFT JOIN trong nhiều trường hợp.

Team thường ưu tiên LEFT JOIN để query dễ đọc nhất quán.

### FULL OUTER JOIN

Giữ unmatched từ cả hai phía.

Hữu ích reconciliation nhưng ít dùng hơn trong CRUD thường ngày.

### CROSS JOIN

Tạo mọi combination:

```text
m customers × n products = m*n rows
```

Dùng cho:

- calendar grid;
- matrix;
- sinh combination có kiểm soát.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| INNER | chỉ match | hợp khi không cần unmatched |
| LEFT/RIGHT | giữ một phía | vị trí predicate đổi nghĩa |
| FULL/CROSS | giữ unmatched hai phía / mọi cặp | FULL cho đối chiếu, CROSS cần kiểm giới hạn m×n |

### Misconception check

**Đúng hay sai?** INNER JOIN chính là giao hai tập thực thể.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: tạo cặp row, có thể nhân số row theo số match.

</details>

**Đúng hay sai?** LEFT JOIN luôn giữ khách dù WHERE yêu cầu o.Status=Paid.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: NULL phía phải làm predicate UNKNOWN và bị loại.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace cặp row.

- **Working Developer — dùng khi làm việc:** outer join và aggregate.

- **Deep Dive — có thể quay lại sau:** physical join khi đọc plan.

### ON và WHERE

Với LEFT JOIN:

```sql
LEFT JOIN Orders o
  ON o.CustomerId = c.CustomerId
 AND o.Status = 'Paid'
```

khác:

```sql
LEFT JOIN Orders o
  ON o.CustomerId = c.CustomerId
WHERE o.Status = 'Paid'
```

Version WHERE loại row có `o.Status = NULL`, vô tình làm semantics giống INNER JOIN.

### Cardinality

One-to-many join làm row phía one lặp lại.

Một customer có 3 order -> 3 result rows.

Đây không phải duplicate lỗi.

### Join nhiều table

Thứ tự viết join không đồng nghĩa optimizer luôn thực thi đúng thứ tự đó.

Execution plan mới cho biết physical join order/operator.

## 6. Lỗi thường gặp

### Quên ON

Accidental Cartesian product có thể làm row count nổ.

### JOIN theo text thay vì key

Tên có thể trùng/thay đổi.

Join bằng key được thiết kế.

### LEFT JOIN rồi filter right table ở WHERE

Có thể mất unmatched row.

### DISTINCT để che join sai

Nếu duplicate đến từ join condition thiếu, `DISTINCT` chỉ che bug.

## 7. Khi nào KHÔNG dùng

Không dùng DISTINCT che lỗi join thiếu key. Không CROSS JOIN nguồn lớn nếu chưa biết số cặp và ngân sách kết quả.

## 8. Production notes & scale check

Gate kiểm3/4/6 row, unmatched customer và ON/WHERE khác nhau. RIGHT/FULL có ca riêng trên tập nhỏ; semantics tập kết quả không bảo đảm thứ tự nếu thiếu ORDER BY. JOIN nhiều children có thể nhân số tiền trước SUM.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Tìm customer chưa có order.

**Gợi ý:** LEFT JOIN + `WHERE o.OrderId IS NULL`.

### Bài 2

Tạo OrderItems và join Order -> Customer -> Item -> Product.

### Bài 3

Viết cùng logic bằng RIGHT JOIN rồi refactor thành LEFT JOIN.

### Bài 4

Tạo FULL OUTER JOIN giữa hai bảng SKU để reconciliation.

### Bài 5

Tạo CROSS JOIN 7 ngày × 3 ca làm việc.

## 10. Bài tập tích hợp liên module — Judgment

So graph adjacency Module 07: một khóa cha có nhiều cạnh/child thì lookup trả một row hay nhiều? Thiết kế report tổng tiền không bị nhân bởi join payment attempts.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. LEFT thêm NULL ở đâu?
2. ON và WHERE khác chỗ nào?
3. Cardinality dự đoán cost gì?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt INNER/LEFT/RIGHT/FULL.
- [ ] Tôi hiểu CROSS JOIN.
- [ ] Tôi biết ON và WHERE có thể đổi outer-join semantics.
- [ ] Tôi reasoning được cardinality.
- [ ] Tôi không dùng DISTINCT để che join bug.
- [ ] Tôi join bằng key ổn định.

Điều hướng:

- Bài trước: [GROUP BY, aggregate và HAVING](./07-group-by-aggregate-va-having.md)
- Bài tiếp theo: [Subquery và correlated subquery](./09-subquery-va-correlated-subquery.md)
