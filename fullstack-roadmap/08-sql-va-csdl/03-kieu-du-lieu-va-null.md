# Kiểu dữ liệu và NULL

> **Last verified:** 2026-10-18
>
> **Baseline:** SQL Server 2025 (17.0.x) · T-SQL · sqlcmd (mssql-tools18) · Docker image `mcr.microsoft.com/mssql/server:2025-latest`
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** SQL Server major/CU đổi hành vi NULL, kiểu dữ liệu hoặc filtered index, đổi image hoặc mặc định SET option của sqlcmd, đổi lab/schema, CI `verify-module-08` fail

## TL;DR

- Mỗi column có một kiểu dữ liệu quyết định giá trị hợp lệ, cách so sánh và dung lượng; `NULL` nghĩa là “chưa biết / không có”, không phải 0 hay chuỗi rỗng, và làm phép so sánh thành `UNKNOWN`.
- Dùng `decimal` cho tiền, `nvarchar` cho text tiếng Việt, `date`/`datetime2` cho thời gian; chỉ cho `NULL` khi nghiệp vụ thật sự có trạng thái “chưa biết”, và tìm nó bằng `IS NULL`.
- Trade-off: `NULL` tiết kiệm một trạng thái nhưng khiến `=`, `NOT IN`, phép cộng, aggregate và `UNIQUE` cư xử khác trực giác; kiểu quá rộng tốn dung lượng và index, kiểu quá hẹp gây overflow.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- chọn integer, `decimal`, string, date/time và binary type theo domain;
- phân biệt `varchar` với `nvarchar`, `decimal` với `float`, `datetime2` với `datetime`;
- giải thích three-valued logic (`TRUE`/`FALSE`/`UNKNOWN`) và vì sao `= NULL` không bao giờ khớp;
- dự đoán kết quả của `NULL` trong phép toán, phép nối chuỗi, aggregate và `NOT IN`;
- thiết kế column nullable theo nghĩa nghiệp vụ, phân biệt `NULL` với chuỗi rỗng;
- xử lý “duy nhất nếu có giá trị” bằng filtered unique index thay vì `UNIQUE` thường.

## 2. Bài toán mở đầu

Một product trong catalog có bốn thông tin trông giống nhau nhưng mang nghĩa khác hẳn:

```text
Price       = 1 299 000      → có giá trị, là tiền
WeightKg    = chưa cân        → chưa biết
Description = ""              → đã biết: mô tả rỗng
ReleasedAt  = chưa phát hành  → chưa có
```

Nếu mọi column đều là chuỗi, bạn mất validation kiểu, sort đúng thứ tự, phép tính và cả sự khác biệt giữa “chưa biết” với “rỗng”. Báo cáo “trọng lượng trung bình” sẽ sai mà không ai biết, còn query `WHERE WeightKg = NULL` trả về 0 hàng dù rõ ràng có sản phẩm chưa cân.

### Trực giác 60 giây

Hãy coi `NULL` là một ô có dán nhãn **“chưa biết”**. Hỏi “ô chưa biết có bằng 5 không?” thì câu trả lời trung thực là “không biết”, không phải “có” hay “không”. SQL gọi câu trả lời đó là `UNKNOWN`. `WHERE` chỉ giữ hàng mà điều kiện là `TRUE`, nên mọi hàng có điều kiện `UNKNOWN` lặng lẽ biến mất. Từ một ý đó suy ra gần hết các bẫy của bài: `= NULL` không khớp gì, `NULL + 1` vẫn là “chưa biết”, `NOT IN (..., NULL)` loại sạch, aggregate bỏ qua ô chưa biết.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| data type | luật về loại giá trị một column nhận | `decimal(19,4)` cho `Price` |
| precision / scale | tổng số chữ số / số chữ số sau dấu phẩy | `decimal(10,3)`: tối đa 7 chữ số phần nguyên |
| `NULL` | đánh dấu giá trị chưa biết hoặc không áp dụng | `WeightKg` của bàn phím |
| three-valued logic | điều kiện có thể là `TRUE`, `FALSE` hoặc `UNKNOWN` | `WeightKg = NULL` → `UNKNOWN` |
| nullable column | column cho phép `NULL` | `ReleasedAt date NULL` |
| filtered index | index chỉ chứa các hàng thỏa một điều kiện | `UX_Suppliers_TaxCode ... WHERE TaxCode IS NOT NULL` |

### Ví dụ nhỏ — tính tay trước

Table có hai hàng: bàn phím (`WeightKg = NULL`, `Description = N''`) và chuột (`WeightKg = 0.095`, `Description = NULL`). Trước khi chạy lab, tự điền:

```text
(a) số hàng có WeightKg = NULL                 → ?
(b) số hàng có WeightKg IS NULL                → ?
(c) COUNT(*) và COUNT(WeightKg)                → ?, ?
(d) AVG(WeightKg)                              → ?
(e) số hàng có ProductId NOT IN (2, NULL)      → ?
```

Đáp án để đối chiếu: (a) 0; (b) 1; (c) 2 và 1; (d) 0.095 — chỉ chia cho 1 hàng có giá trị; (e) 0. Nếu (a) hoặc (e) bạn đoán khác, phần cơ chế bên dưới là chỗ cần đọc kỹ.

## 3. Lời giải chạy được

Dùng SQL Server 2025 đã dựng ở [bài 01](./01-mo-hinh-quan-he-va-cai-dat-sql-server.md). Lưu script thành `lab03.sql`, chép vào container rồi chạy `sqlcmd ... -C -b -i /tmp/lab03.sql` như bài trước. Script tự xóa và tạo lại database nên chạy lại bao nhiêu lần cũng được:

```sql
-- sqlcmd mặc định QUOTED_IDENTIFIER OFF; filtered index cần ON.
SET QUOTED_IDENTIFIER ON;
GO

USE master;
GO

IF DB_ID(N'CommerceLab08_03') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_03
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_03;
END;
GO

CREATE DATABASE CommerceLab08_03;
GO
USE CommerceLab08_03;
GO

CREATE TABLE dbo.Products
(
    ProductId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,

    Sku varchar(40) NOT NULL,
    Name nvarchar(160) NOT NULL,

    Price decimal(19,4) NOT NULL,
    WeightKg decimal(10,3) NULL,

    Stock int NOT NULL,
    IsActive bit NOT NULL,

    ReleasedAt date NULL,
    CreatedAt datetime2(3) NOT NULL,

    Description nvarchar(2000) NULL,
    RowVersion rowversion NOT NULL,

    CONSTRAINT CK_Products_Price CHECK (Price >= 0),
    CONSTRAINT CK_Products_Stock CHECK (Stock >= 0)
);
GO

INSERT INTO dbo.Products
(
    Sku,
    Name,
    Price,
    WeightKg,
    Stock,
    IsActive,
    ReleasedAt,
    CreatedAt,
    Description
)
VALUES
(
    'KB-01',
    N'Bàn phím cơ',
    1299000.0000,
    NULL,
    25,
    1,
    NULL,
    SYSUTCDATETIME(),
    N''
),
(
    'MS-01',
    N'Chuột không dây',
    599000.0000,
    0.095,
    40,
    1,
    '2026-01-15',
    SYSUTCDATETIME(),
    NULL
);
GO

-- 1) Tìm giá trị thiếu: phải dùng IS NULL.
SELECT
    ProductId,
    Name,
    WeightKg,
    ReleasedAt
FROM dbo.Products
WHERE WeightKg IS NULL
   OR ReleasedAt IS NULL;

-- 2) Logic ba giá trị: '= NULL' không bao giờ TRUE; NULL khác chuỗi rỗng.
SELECT
    (SELECT COUNT(*) FROM dbo.Products WHERE WeightKg = NULL) AS EqualsNullRows,
    (SELECT COUNT(*) FROM dbo.Products WHERE WeightKg IS NULL) AS IsNullRows,
    (SELECT COUNT(*) FROM dbo.Products WHERE Description = N'') AS EmptyDescriptionRows,
    (SELECT COUNT(*) FROM dbo.Products WHERE Description IS NULL) AS NullDescriptionRows;

-- 3) Aggregate bỏ qua NULL.
SELECT
    COUNT(*) AS AllRows,
    COUNT(WeightKg) AS RowsWithWeight,
    AVG(WeightKg) AS AvgWeightKg
FROM dbo.Products;

-- 4) NULL lan truyền qua phép toán và phép nối bằng '+'; CONCAT coi NULL là rỗng.
SELECT
    Name,
    Price + WeightKg AS PricePlusWeight,
    Name + N' - ' + Description AS PlusConcat,
    CONCAT(Name, N' - ', Description) AS ConcatFunction,
    COALESCE(Description, N'(chưa có mô tả)') AS DisplayDescription
FROM dbo.Products
ORDER BY ProductId;

-- 5) NOT IN gặp NULL trong danh sách: điều kiện thành UNKNOWN cho mọi hàng.
SELECT
    (SELECT COUNT(*) FROM dbo.Products WHERE ProductId NOT IN (2)) AS NotInWithoutNull,
    (SELECT COUNT(*) FROM dbo.Products WHERE ProductId NOT IN (2, NULL)) AS NotInWithNull;
GO

-- 6) UNIQUE trên cột nullable: SQL Server chỉ cho MỘT NULL.
CREATE TABLE dbo.Suppliers
(
    SupplierId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Suppliers PRIMARY KEY,
    Name nvarchar(120) NOT NULL,
    TaxCode varchar(20) NULL
        CONSTRAINT UQ_Suppliers_TaxCode UNIQUE
);

INSERT INTO dbo.Suppliers (Name, TaxCode) VALUES (N'Công ty A', NULL);

BEGIN TRY
    INSERT INTO dbo.Suppliers (Name, TaxCode) VALUES (N'Công ty B', NULL);
END TRY
BEGIN CATCH
    SELECT N'NULL thứ hai với UNIQUE constraint' AS Attempt, ERROR_NUMBER() AS ErrorNumber;
END CATCH;

-- Cách sửa: unique chỉ áp cho giá trị khác NULL (filtered unique index).
ALTER TABLE dbo.Suppliers DROP CONSTRAINT UQ_Suppliers_TaxCode;

CREATE UNIQUE INDEX UX_Suppliers_TaxCode
    ON dbo.Suppliers (TaxCode)
    WHERE TaxCode IS NOT NULL;

INSERT INTO dbo.Suppliers (Name, TaxCode) VALUES (N'Công ty B', NULL);
INSERT INTO dbo.Suppliers (Name, TaxCode) VALUES (N'Công ty C', '0101234567');

BEGIN TRY
    INSERT INTO dbo.Suppliers (Name, TaxCode) VALUES (N'Công ty D', '0101234567');
END TRY
BEGIN CATCH
    SELECT N'Mã số thuế trùng với filtered index' AS Attempt, ERROR_NUMBER() AS ErrorNumber;
END CATCH;

SELECT
    COUNT(*) AS Suppliers,
    COUNT(TaxCode) AS WithTaxCode
FROM dbo.Suppliers;
GO

-- 7) float là xấp xỉ: cộng 0.1 mười lần.
DECLARE @FloatSum float = 0;
DECLARE @DecimalSum decimal(19,4) = 0;
DECLARE @Step int = 0;

WHILE @Step < 10
BEGIN
    SET @FloatSum += 0.1;
    SET @DecimalSum += 0.1;
    SET @Step += 1;
END;

SELECT
    CASE WHEN @FloatSum = 1 THEN N'bằng 1' ELSE N'khác 1' END AS FloatSumEqualsOne,
    CASE WHEN @DecimalSum = 1 THEN N'bằng 1' ELSE N'khác 1' END AS DecimalSumEqualsOne,
    CAST(@FloatSum AS decimal(38,17)) AS FloatSumExact;
GO
```

Output (SQL Server 2025, đã lược dòng thông báo; `CreatedAt` không được in vì phụ thuộc thời điểm chạy):

```text
ProductId | Name        | WeightKg | ReleasedAt
----------+-------------+----------+-----------
1         | Bàn phím cơ | NULL     | NULL

EqualsNullRows | IsNullRows | EmptyDescriptionRows | NullDescriptionRows
---------------+------------+----------------------+--------------------
0              | 1          | 1                    | 1

AllRows | RowsWithWeight | AvgWeightKg
--------+----------------+------------
2       | 1              | .095000

Name            | PricePlusWeight | PlusConcat    | ConcatFunction    | DisplayDescription
----------------+-----------------+---------------+-------------------+-------------------
Bàn phím cơ     | NULL            | Bàn phím cơ - | Bàn phím cơ -     |
Chuột không dây | 599000.0950     | NULL          | Chuột không dây - | (chưa có mô tả)

NotInWithoutNull | NotInWithNull
-----------------+--------------
1                | 0

Attempt                            | ErrorNumber
-----------------------------------+------------
NULL thứ hai với UNIQUE constraint | 2627

Attempt                             | ErrorNumber
------------------------------------+------------
Mã số thuế trùng với filtered index | 2601

Suppliers | WithTaxCode
----------+------------
3         | 1

FloatSumEqualsOne | DecimalSumEqualsOne | FloatSumExact
------------------+---------------------+-------------------
khác 1            | bằng 1              | .99999999999999989
```

### Walkthrough — execution / state / cost

1. **`CREATE TABLE`:** mỗi column được khai báo kiểu và `NULL`/`NOT NULL`. `rowversion` không nhận giá trị từ `INSERT`; engine tự gán một số nhị phân tăng dần mỗi khi hàng thay đổi.
2. **`INSERT` hai hàng:** bàn phím có `WeightKg = NULL`, `ReleasedAt = NULL` và `Description = N''`; chuột có `Description = NULL`. Hai hàng cố ý trộn “chưa biết” và “rỗng”.
3. **Truy vấn 1–2:** với bàn phím, `WeightKg = NULL` cho `UNKNOWN`, `WeightKg IS NULL` cho `TRUE`. `WHERE` chỉ giữ `TRUE`, nên `EqualsNullRows = 0`, `IsNullRows = 1`. `Description = N''` và `Description IS NULL` mỗi cái khớp đúng một hàng khác nhau: rỗng và `NULL` là hai trạng thái.
4. **Truy vấn 3:** `COUNT(*)` đếm hàng; `COUNT(WeightKg)` và `AVG(WeightKg)` chỉ xét giá trị khác `NULL`, nên trung bình là `0.095 / 1`, không phải `0.095 / 2`.
5. **Truy vấn 4:** `Price + NULL` → `NULL`; `Name + N' - ' + NULL` → `NULL` cho chuột; `CONCAT` thay `NULL` bằng chuỗi rỗng. `COALESCE` chỉ thay `NULL`, không đụng chuỗi rỗng — bàn phím vẫn hiện ô trống.
6. **Truy vấn 5:** `ProductId NOT IN (2, NULL)` nghĩa là `ProductId <> 2 AND ProductId <> NULL`. Vế sau luôn `UNKNOWN`, nên cả biểu thức không bao giờ `TRUE` → 0 hàng.
7. **`Suppliers`:** `UNIQUE` của SQL Server coi hai `NULL` là trùng → lỗi `2627`. Filtered unique index chỉ chứa hàng có `TaxCode` nên nhiều `NULL` vẫn hợp lệ, còn mã số thuế trùng vẫn bị chặn (lỗi `2601` — lỗi của unique **index**, không phải constraint).
8. **`float` vs `decimal`:** `0.1` không biểu diễn chính xác trong nhị phân; cộng mười lần cho `0.99999999999999989`, so với `1` ra “khác 1”. `decimal` lưu chữ số thập phân nên ra đúng `1`.
9. **Cost:** kiểu hẹp hơn nghĩa là hàng nhỏ hơn, nhiều hàng hơn trên mỗi page 8 KB, index nhỏ hơn. `NULL` gần như không tốn thêm chỗ, nhưng tốn ở chỗ khác: mọi query phải nhớ xử lý `UNKNOWN`.

### Mini-check

Không chạy lab: `SELECT COUNT(*) FROM dbo.Products WHERE WeightKg <> 0.095;` trả về mấy? Bàn phím có được đếm không, vì sao?

## 4. Cơ chế hoạt động

### Chọn kiểu theo domain

| Domain | Kiểu gợi ý | Lý do |
|---|---|---|
| số lượng, tồn kho | `int` (hoặc `smallint` nếu chắc chắn nhỏ) | `tinyint` chỉ 0–255; gán `256` → lỗi `220` arithmetic overflow |
| tiền | `decimal(19,4)` | chính xác theo chữ số thập phân; `decimal(5,2)` nhận `1234.5` → lỗi `8115` |
| tên, mô tả tiếng Việt | `nvarchar(n)` | Unicode; `varchar` với collation mặc định biến `ễ` thành `?` (bài [01](./01-mo-hinh-quan-he-va-cai-dat-sql-server.md)) |
| SKU, email, mã kỹ thuật ASCII | `varchar(n)` | một byte mỗi ký tự |
| chỉ ngày | `date` | không kèm giờ, không lẫn múi giờ |
| thời điểm | `datetime2(3)` lưu UTC, hoặc `datetimeoffset` khi cần giữ offset | `datetime` cũ làm tròn tới 1/300 giây: `.001` thành `.000` |
| file nhỏ, hash | `varbinary(n)` | dữ liệu nhị phân; file lớn nên để object storage |
| version cho optimistic concurrency | `rowversion` | engine tự tăng mỗi lần update; không phải ngày giờ |

Đừng mặc định `bigint` hay `nvarchar(max)` cho mọi thứ: `nvarchar(max)` không làm được key column của index và khiến người đọc schema mất thông tin “giá trị dài tối đa bao nhiêu”.

### Three-valued logic

So sánh có `NULL` cho `UNKNOWN`. `AND`, `OR`, `NOT` kết hợp `UNKNOWN` theo bảng:

```text
AND      | TRUE     FALSE   UNKNOWN        OR       | TRUE   FALSE    UNKNOWN
---------+--------------------------        ---------+------------------------
TRUE     | TRUE     FALSE   UNKNOWN        TRUE     | TRUE   TRUE     TRUE
FALSE    | FALSE    FALSE   FALSE          FALSE    | TRUE   FALSE    UNKNOWN
UNKNOWN  | UNKNOWN  FALSE   UNKNOWN        UNKNOWN  | TRUE   UNKNOWN  UNKNOWN

NOT UNKNOWN = UNKNOWN
```

`WHERE`, `ON` của join và `HAVING` chỉ giữ hàng có kết quả `TRUE`. Riêng `CHECK` constraint thì ngược lại: chỉ **từ chối** khi kết quả là `FALSE`, nên `CHECK (WeightKg > 0)` vẫn cho `WeightKg = NULL` đi qua.

### NULL trong biểu thức và aggregate

- Phép toán và phép nối `+` với `NULL` → `NULL` (“chưa biết cộng 1 vẫn là chưa biết”).
- `CONCAT` coi `NULL` là chuỗi rỗng; `COALESCE(a, b, ...)` trả giá trị khác `NULL` đầu tiên. Bài [06](./06-ham-scalar-case-va-xu-ly-null.md) so sánh `COALESCE` với `ISNULL` chi tiết.
- `COUNT(*)` đếm hàng; `COUNT(col)`, `SUM`, `AVG`, `MIN`, `MAX` bỏ qua `NULL`. Bài [07](./07-group-by-aggregate-va-having.md) dùng điều này cho báo cáo.

### UNIQUE và NULL

Chuẩn SQL coi các `NULL` là “không trùng nhau”, nhưng `UNIQUE` constraint của SQL Server coi chúng là trùng và chỉ cho **một** `NULL`. Khi nghiệp vụ là “nếu có thì không trùng” (mã số thuế, số điện thoại phụ), dùng filtered unique index `WHERE col IS NOT NULL`. PostgreSQL mặc định cho nhiều `NULL` trong `UNIQUE` — đây là điểm khác phương ngữ cần nhớ khi đổi engine.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| `NULL` | giá trị chưa biết hoặc không áp dụng | không cần giá trị giả; mọi query phải xử lý `UNKNOWN`; không dùng thay cho một trạng thái nghiệp vụ có tên |
| Chuỗi rỗng `N''` | đã biết, và giá trị là rỗng | so sánh bằng `=` bình thường; không dùng để giả lập “chưa biết” |
| Giá trị “ma” (`0`, `'1900-01-01'`, `-1`) | giả vờ có giá trị | query đơn giản nhưng phá aggregate (`AVG` kéo về 0) và dễ bị hiểu nhầm là dữ liệu thật; tránh |
| Column/trạng thái riêng (`Status = 'Draft'`) | trạng thái có tên rõ ràng | rõ nghĩa, ràng buộc được bằng `CHECK`; phù hợp khi “chưa có” là một bước trong quy trình |

### Misconception check

**Đúng hay sai?** `WHERE WeightKg = NULL` và `WHERE WeightKg IS NULL` cho cùng kết quả, chỉ khác cách viết.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. Lab cho `EqualsNullRows = 0` và `IsNullRows = 1`. So sánh `= NULL` luôn ra `UNKNOWN`, nên không hàng nào qua được `WHERE`.

</details>

**Đúng hay sai?** `AVG(WeightKg)` chia tổng cho số hàng của table.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. `AVG` bỏ qua `NULL`: lab có 2 hàng nhưng `AvgWeightKg = 0.095`, tức chia cho 1. Nếu muốn coi “chưa cân” là 0 thì phải nói rõ bằng `AVG(COALESCE(WeightKg, 0))` — và thường đó là sai nghiệp vụ.

</details>

**Đúng hay sai?** `NULL` trong SQL giống `null` trong C#.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. Trong C#, `null == null` là `true` và gọi member trên `null` gây `NullReferenceException`. Trong SQL, `NULL = NULL` là `UNKNOWN`, và `NULL` lan truyền lặng lẽ qua biểu thức thay vì gây lỗi. Map sang C# thì column nullable tương ứng `decimal?`, `DateOnly?`, `string?` ([nullable reference type](../05-csharp-nang-cao/06-nullable-reference-type.md)).

</details>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** chọn `int`/`decimal`/`nvarchar`/`date`/`datetime2`; `NULL` là “chưa biết”; dùng `IS NULL`/`IS NOT NULL`; `COUNT(*)` khác `COUNT(col)`.
- **Working Developer — dùng khi làm việc:** bẫy `NOT IN` với `NULL`, `NULL` trong phép nối chuỗi, `UNIQUE` một-`NULL` và filtered unique index, map kiểu SQL ↔ C#.
- **Deep Dive — có thể quay lại sau:** `CHECK` chấp nhận `UNKNOWN`, độ chính xác của `datetime` cũ, SET option `QUOTED_IDENTIFIER` và filtered index.

Bài trước: [Thiết kế schema, table, key và constraint](./02-thiet-ke-schema-table-key-constraint.md). Liên hệ: [Cú pháp, biến và kiểu dữ liệu C#](../04-csharp-co-ban/02-cu-phap-bien-va-kieu-du-lieu.md) — `decimal` trong C# và SQL đều là số thập phân chính xác.

### Map kiểu SQL ↔ C#

```text
int            ↔ int              decimal(19,4)  ↔ decimal
nvarchar(n)    ↔ string           bit            ↔ bool
date           ↔ DateOnly         datetime2      ↔ DateTime
datetimeoffset ↔ DateTimeOffset   rowversion     ↔ byte[]
column NULL    ↔ kiểu nullable: int?, decimal?, string?
```

Nếu column `NOT NULL` nhưng property C# là nullable (hoặc ngược lại), lỗi chỉ lộ ra khi đọc/ghi dữ liệu thật. Module 09 dùng bảng này khi cấu hình EF Core.

### Đào sâu (có thể quay lại sau)

- **`CHECK` và `UNKNOWN`:** `CHECK (WeightKg > 0)` chỉ từ chối khi biểu thức là `FALSE`; `NULL > 0` là `UNKNOWN` nên được chấp nhận. Muốn bắt buộc có giá trị thì thêm `NOT NULL`.
- **`datetime` cũ:** `CAST('2026-01-01T10:00:00.001' AS datetime)` cho `10:00:00.000`, còn `datetime2(3)` giữ `.001`. Code mới dùng `datetime2`.
- **`QUOTED_IDENTIFIER`:** `sqlcmd` mặc định tắt option này (trừ khi chạy với `-I`). Khi tắt, mọi `INSERT`/`UPDATE`/`DELETE` vào table có filtered index đều lỗi `1934` — vì vậy dòng đầu lab bật nó lên. Driver ứng dụng (ADO.NET, ODBC) mặc định bật.

## 6. Lỗi thường gặp

### So sánh với `NULL` bằng `=` hoặc `<>`

`WHERE WeightKg = NULL` trả 0 hàng; `WHERE WeightKg <> 0.095` cũng bỏ sót hàng `NULL`. Dùng `IS NULL`, hoặc viết rõ `WHERE WeightKg <> 0.095 OR WeightKg IS NULL`.

### `NOT IN` với subquery có thể trả `NULL`

`WHERE ProductId NOT IN (SELECT ProductId FROM ...)` trả 0 hàng nếu subquery chứa dù chỉ một `NULL`. Dùng `NOT EXISTS` (bài [09](./09-subquery-va-correlated-subquery.md)) hoặc lọc `IS NOT NULL` trong subquery.

### Nối chuỗi bằng `+` với cột nullable

Một cột `NULL` làm cả chuỗi hiển thị thành `NULL`. Dùng `CONCAT` hoặc `COALESCE` từng phần.

### Dùng `float` cho tiền

Tổng `0.1` mười lần khác `1`; sai lệch cộng dồn qua hàng triệu giao dịch và làm đối soát lệch. Dùng `decimal`.

### Dùng `NULL` thay cho trạng thái nghiệp vụ

`Order.Status NULL` để nói “chưa xử lý” khiến mọi query phải đoán nghĩa. Mô hình trạng thái có tên và ràng buộc bằng `CHECK` hoặc table tra cứu.

### Lẫn `NULL` với chuỗi rỗng

Form web gửi `""` cho ô bỏ trống; lưu thẳng vào database thì cùng một ý “không có mô tả” tồn tại dưới hai dạng. Chuẩn hóa ở một chỗ (ví dụ đổi `""` thành `NULL` ở tầng ứng dụng) và áp dụng nhất quán.

## 7. Khi nào KHÔNG dùng

- **Không cho cột nullable chỉ để `INSERT` dễ hơn:** cột bắt buộc theo nghiệp vụ phải `NOT NULL`, thiếu thì để `DEFAULT` hoặc lỗi `515` báo sớm.
- **Không dùng `NULL` khi “chưa có” là một bước quy trình:** dùng column trạng thái có tên.
- **Không dùng `UNIQUE` thường cho cột “duy nhất nếu có”:** dùng filtered unique index.
- **Không dùng `float`/`real` cho tiền, số lượng hay mã định danh:** chỉ dùng cho đo đạc khoa học, nơi sai số tương đối chấp nhận được.
- **Không dùng `nvarchar(max)` cho cột ngắn:** chọn độ dài theo domain để index được và tự mô tả.

Tín hiệu đang dùng sai: query đầy `COALESCE(x, 0)` để “sửa” số liệu, hoặc team tranh luận `NULL` ở cột này nghĩa là gì. Phương án đơn giản hơn: `NOT NULL` + `DEFAULT`, hoặc column trạng thái. Câu hỏi quyết định: “chưa biết” có phải là một trạng thái hợp lệ, có nghĩa duy nhất, của dữ liệu này không?

## 8. Production notes & scale check

- **Đổi kiểu column trên table lớn:** `ALTER COLUMN` có thể phải ghi lại mọi hàng và giữ lock lâu; mở rộng `varchar(20)` → `varchar(40)` thường rẻ, thu hẹp hoặc đổi kiểu thì phải kiểm tra dữ liệu và chạy trong cửa sổ bảo trì (bài [24](./24-backup-restore-va-migration-du-lieu.md)).
- **Thêm `NOT NULL` vào cột đã có dữ liệu:** backfill giá trị trước, rồi mới đổi ràng buộc; làm theo đợt với table lớn.
- **Kiểu nhỏ hơn = index nhỏ hơn:** key `int` 4 byte so với `uniqueidentifier` 16 byte ảnh hưởng mọi nonclustered index vì chúng mang theo clustered key (bài [17](./17-index-btree-clustered-nonclustered.md)).
- **Báo cáo:** khi in số liệu có cột nullable, ghi rõ trong định nghĩa metric là `NULL` bị bỏ qua hay được coi là 0.
- **Script triển khai:** chạy migration bằng `sqlcmd` thì thêm `-I` hoặc `SET QUOTED_IDENTIFIER ON` nếu schema có filtered index.
- **Team 2–3 người:** quy ước `decimal(19,4)` cho tiền, `nvarchar` cho text người dùng, `datetime2` UTC cho thời điểm, `NOT NULL` mặc định là đủ dùng lâu.

## 9. Bài tập kỹ thuật

### Bài 1 — Chọn kiểu

Chọn kiểu và `NULL`/`NOT NULL` cho: số lượng trong giỏ, giá trị đơn hàng, email, ngày sinh, ảnh đại diện nhỏ, thời điểm đăng nhập cuối.

**Gợi ý:** hỏi “giá trị lớn nhất hợp lý là bao nhiêu?” và “có lúc nào thật sự chưa biết không?”.

### Bài 2 — Table Payments

Tạo `dbo.Payments` có `Amount`, `PaidAt` (nullable — chưa thanh toán) và `ProviderReference` (nullable, nhưng nếu có thì không trùng).

**Gợi ý:** `ProviderReference` cần filtered unique index; thêm `CHECK (Amount > 0)` và nghĩ xem nó xử lý `NULL` ra sao.

### Bài 3 — Sản phẩm chưa phát hành

Viết query liệt kê sản phẩm chưa có `ReleasedAt`, hiển thị `N'Sắp ra mắt'` thay cho `NULL`.

**Gợi ý:** `IS NULL` trong `WHERE`, `COALESCE` cần cùng kiểu dữ liệu nên phải `CONVERT` ngày sang chuỗi.

### Bài 4 — Debug `NOT IN`

Chạy `SELECT 1 WHERE NULL = NULL;`, rồi viết query “sản phẩm không có trong danh sách khuyến mãi” với danh sách chứa một `NULL`. Giải thích vì sao không ra hàng nào và sửa bằng hai cách.

**Gợi ý:** viết `NOT IN` thành chuỗi `<> ... AND <> ...` trên giấy.

### Bài 5 — `nvarchar(100)` hay `nvarchar(max)`

So sánh hai lựa chọn cho `Description` theo: index được không, dung lượng tối đa, thông tin schema truyền đạt.

**Gợi ý:** thử `CREATE INDEX` trên cột `nvarchar(max)` và đọc lỗi.

## 10. Bài tập tích hợp liên module — Judgment

Một API (Module 11 sẽ xây) nhận JSON cập nhật hồ sơ khách: `{"phone": null}` và trường hợp không gửi `phone`. Với C# nullable (Module 05) và column `Phone varchar(20) NULL`, thiết kế cách phân biệt “xóa số điện thoại”, “không thay đổi” và “số điện thoại là chuỗi rỗng”. Quyết định trạng thái nào được lưu thành `NULL`, trạng thái nào không bao giờ chạm database.

**Tiêu chí:** nêu rõ nghĩa của `NULL` trong column, cách DTO C# biểu diễn ba trường hợp, và một query báo cáo không bị sai vì lựa chọn đó; không chấm theo độ phức tạp.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vì sao `WHERE x = NULL` không bao giờ trả hàng, còn `CHECK (x > 0)` lại cho `NULL` đi qua?
2. Dự đoán `COUNT(*)`, `COUNT(Phone)` và `AVG(Score)` trên một table 4 hàng có 1 `Phone` và 1 `Score` là `NULL`.
3. Viết lại `NOT IN (1, NULL)` thành biểu thức `AND` và chỉ ra vế làm hỏng kết quả.
4. Khi nào chọn filtered unique index thay vì `UNIQUE` constraint?
5. Nêu hai lý do không lưu tiền bằng `float`.

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chọn được kiểu dữ liệu theo domain và giải thích lựa chọn.
- [ ] Tôi dự đoán đúng kết quả của `NULL` trong `WHERE`, phép toán, phép nối và aggregate.
- [ ] Tôi tránh được bẫy `NOT IN` với `NULL`.
- [ ] Tôi phân biệt `NULL`, chuỗi rỗng và giá trị “ma”.
- [ ] Tôi tạo được filtered unique index cho cột “duy nhất nếu có”.

**Bài prerequisite:** [Thiết kế schema, table, key và constraint](./02-thiet-ke-schema-table-key-constraint.md)

**Bài tiếp theo:** [CRUD: SELECT, INSERT, UPDATE, DELETE](./04-crud-select-insert-update-delete.md)
