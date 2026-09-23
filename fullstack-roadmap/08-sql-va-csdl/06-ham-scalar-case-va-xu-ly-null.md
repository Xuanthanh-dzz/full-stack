# Hàm scalar, CASE và xử lý NULL

> **Last verified:** pending — chưa chạy lại gate retrofit  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Hàm scalar và CASE tạo giá trị cho từng row trong truy vấn.
- Dùng để tính nhãn, fallback hoặc tỷ lệ có semantics rõ.
- Một expression nhìn an toàn chưa chắc bảo vệ lỗi đánh giá khác hoặc dùng index hiệu quả.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng các hàm string, numeric và date phổ biến;
- dùng `CASE` để tạo giá trị dẫn xuất;
- dùng `COALESCE`, `NULLIF` và `ISNULL`;
- phân biệt xử lý presentation với business invariant;
- tránh biến column thành expression không SARGable khi filter;
- hiểu hàm scalar có thể ảnh hưởng execution plan.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Mỗi phiếu giá đi qua một bàn tính: bỏ khoảng trắng, chọn nhãn theo giá rồi tính giảm bao nhiêu phần trăm. Kết quả trên màn hình có thể đổi mà phiếu gốc trong kho vẫn giữ nguyên.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| scalar | một giá trị đầu ra cho bộ input | TRIM(Name) |
| CASE expression | chọn giá trị theo điều kiện | PriceTier |
| COALESCE | lấy expression đầu không NULL | Description fallback |
| NULLIF | trả NULL khi hai giá trị bằng nhau | mẫu số bằng0 |

### Ví dụ nhỏ — tính tay trước

Price120,ListPrice150 →giảm20%. ListPrice NULL được thay bằng Price nên0%. Cả hai bằng0 →mẫu số NULL, kết quả NULL chứ không tự thành0%.

Dashboard cần hiển thị:

- tên product đã trim;
- mức giá `Budget / Standard / Premium`;
- mô tả fallback khi NULL;
- tuổi đơn hàng theo ngày;
- tỷ lệ discount không chia cho 0.

Đây là các phép biến đổi theo từng row.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. SQL Server đọc các cột cần cho từng row, tính TRIM/CASE và expression số.
2. CASE chọn Budget dưới 500000, Standard dưới 3000000, còn lại Premium.
3. NULLIF biến mẫu số 0 thành NULL; phép chia cho NULL trả NULL.
4. Projection không lưu nhãn trở lại table. CPU tăng theo số row/độ dài chuỗi; function trên cột trong WHERE có thể ảnh hưởng cách truy cập index.

### Mini-check

Từ23:59 tới00:01 ngày sau, DATEDIFF(day) bằng bao nhiêu và có đủ24 giờ chưa?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| COALESCE | nhiều lựa chọn fallback theo type precedence | không thay mọi trường hợp của ISNULL |
| ISNULL | hai argument, quy tắc type riêng | chuỗi thay có thể bị cắt theo type đầu |
| CASE | điều kiện tùy ý | không coi như if của C# bảo đảm mọi expression chỉ chạy sau guard |

### Misconception check

**Đúng hay sai?** DATEDIFF(day) đo số khoảng24 giờ trọn vẹn.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: đếm số ranh giới ngày đã đi qua.

</details>

**Đúng hay sai?** COALESCE ghi fallback vào row gốc.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: SELECT chỉ tạo giá trị kết quả.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** scalar và NULL.

- **Working Developer — dùng khi làm việc:** type inference và biên ngày.

- **Deep Dive — có thể quay lại sau:** computed/indexed expression khi đo được nhu cầu.

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

## 7. Khi nào KHÔNG dùng

Không format mọi số/ngày thành string trước khi application cần tính tiếp. Không rải cùng business rule CASE ở nhiều report mà không có owner.

## 8. Production notes & scale check

Gate kiểm tier, discount, NULLIF và khác type ISNULL/COALESCE. AgeInDays phụ thuộc ngày chạy nên không đóng băng một con số trong expected; phiên bản báo cáo cần thời điểm tham chiếu cố định có thể truyền @AsOf. Chuỗi Unicode và decimal vẫn cần policy precision.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

So formatter/policy Module 06: nhãn hiển thị có nên thành state lưu lâu dài? Với100 row và 10 triệu row, cost biến đổi chạy ở client hay server khác gì?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. CASE trả giá trị hay đổi control flow của batch?
2. Mẫu số 0 biến thành gì?
3. DATEDIFF đếm điều gì?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi dùng được scalar function phổ biến.
- [ ] Tôi viết được CASE.
- [ ] Tôi hiểu COALESCE/NULLIF.
- [ ] Tôi tránh chia 0.
- [ ] Tôi không format presentation quá sớm trong DB.
- [ ] Tôi nghĩ tới SARGability khi dùng function trong WHERE.

Điều hướng:

- Bài trước: [Filter, sort và pagination](./05-filter-sort-va-pagination.md)
- Bài tiếp theo: [GROUP BY, aggregate và HAVING](./07-group-by-aggregate-va-having.md)
