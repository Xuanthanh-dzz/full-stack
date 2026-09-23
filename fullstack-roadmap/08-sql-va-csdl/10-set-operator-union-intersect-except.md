# Set operator: UNION, INTERSECT, EXCEPT

> **Last verified:** pending — chưa chạy lại gate retrofit  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Set operators ghép hoặc so các rowset có cùng shape.
- Dùng UNION ALL để nối row, UNION/INTERSECT/EXCEPT khi cần loại trùng hoặc đối chiếu.
- Dedup so toàn bộ cột được chọn; EXCEPT không kiểm được số lần xuất hiện.

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

### Trực giác 60 giây

Đặt hai danh sách SKU nối tiếp để giữ mọi lượt xuất hiện, hoặc gạch các dòng giống nhau để lấy danh sách duy nhất. Đối chiếu A thiếu gì ở B cần làm cả hai chiều nếu muốn thấy mọi khác biệt.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| UNION ALL | nối và giữ mọi row | COMMON xuất hiện2 lần |
| UNION | nối rồi loại row trùng | COMMON một lần |
| INTERSECT | row có ở cả hai phía, không lặp | COMMON |
| EXCEPT | row ở trái mà không ở phải | A-only |

### Ví dụ nhỏ — tính tay trước

A=[A1,A2,C],B=[B1,B2,C]: UNION5 row,ALL6 row,INTERSECT[C],A EXCEPT B=[A1,A2]. Đảo EXCEPT nhận[B1,B2].

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

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. Server kiểm số cột và chuyển type tương thích theo vị trí.
2. UNION ALL giữ multiplicity; các operator còn lại so cả row để dedup.
3. ORDER BY cuối sắp kết quả chung; không giữ thứ tự từng nguồn chỉ vì viết trước.
4. Dedup có thể cần sort/hash và memory; đọc input và truyền output vẫn có cost. NULL được coi bằng nhau cho mục đích loại trùng của các set operators này.

### Mini-check

A có[C,C],B có[C]: EXCEPT hai chiều trả gì, COUNT khác nhau không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| UNION ALL | giữ các lượt xuất hiện | ít việc dedup nhưng có thể nhiều output |
| UNION/INTERSECT/EXCEPT | semantics tập không lặp | không kiểm duplicate count |
| JOIN | ghép cột theo quan hệ | khác shape và cardinality |

### Misconception check

**Đúng hay sai?** EXCEPT hai chiều rỗng chứng minh số bản ghi trùng giống nhau.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: EXCEPT loại trùng trước so.

</details>

**Đúng hay sai?** UNION chỉ so cột đầu tiên.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: so toàn row trong projection.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** shape và set operators.

- **Working Developer — dùng khi làm việc:** multiplicity/NULL.

- **Deep Dive — có thể quay lại sau:** collation và cost dedup.

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

## 7. Khi nào KHÔNG dùng

Không dùng UNION khi cần giữ mọi event trùng giá trị. Không dùng EXCEPT một mình để chứng nhận migration giữ multiplicity.

## 8. Production notes & scale check

Gate kiểm kết quả và số row của5query chính, thêm NULL/duplicate case. Collation/type conversion ảnh hưởng equality; đối chiếu dữ liệu quan trọng cần cả key, count và giá trị, không chỉ checksum dễ collision.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

So HashSet và List Module 07: chọn collection nào làm oracle cho UNION và UNION ALL? Khi kiểm migration cần thêm phép so nào để bắt row trùng mất đi?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. EXCEPT có đối xứng không?
2. Dedup so những cột nào?
3. NULL có bị loại như WHERE UNKNOWN không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt UNION và UNION ALL.
- [ ] Tôi dùng được INTERSECT/EXCEPT.
- [ ] Tôi hiểu operand của EXCEPT có thứ tự.
- [ ] Tôi phân biệt set operator với JOIN.
- [ ] Tôi kiểm tra type/column compatibility.
- [ ] Tôi dùng UNION ALL khi không cần dedup.

Điều hướng:

- Bài trước: [Subquery và correlated subquery](./09-subquery-va-correlated-subquery.md)
- Bài tiếp theo: [CTE và recursive CTE](./11-cte-va-recursive-cte.md)

### Checkpoint sau cụm bài

- [Failure Lab](./failure-labs/02-left-join.md)
- [Spaced Review](./reviews/review-02.md)
