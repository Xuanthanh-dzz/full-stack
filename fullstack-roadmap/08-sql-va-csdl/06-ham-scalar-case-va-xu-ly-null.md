# Hàm scalar, CASE và xử lý NULL

> **Last verified:** 2026-10-18
>
> **Baseline:** SQL Server 2025 (17.0.x) · T-SQL · sqlcmd (mssql-tools18) · Docker image `mcr.microsoft.com/mssql/server:2025-latest`
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** SQL Server major/CU đổi hành vi hàm string/date, `CASE`, `ISNULL`/`COALESCE` hoặc kiểu kết quả phép chia, đổi image hoặc sqlcmd, đổi lab/schema, CI `verify-module-08` fail

## TL;DR

- Hàm scalar (`TRIM`, `LEFT`, `DATEDIFF`, `COALESCE`, `NULLIF`, …) và `CASE` biến đổi giá trị **trên từng hàng**, trả đúng một giá trị cho mỗi hàng; `CASE` dừng ở nhánh `WHEN` đúng đầu tiên và thiếu `ELSE` thì ra `NULL`.
- Dùng chúng cho giá trị dẫn xuất khi đọc: nhãn phân loại, giá trị thay thế cho `NULL`, chia an toàn bằng `NULLIF`, đếm có điều kiện bằng `SUM(CASE ...)`.
- Trade-off: logic rải trong nhiều query dễ lệch nhau; bọc column trong hàm ở `WHERE` làm mất khả năng tìm bằng index; định dạng hiển thị (tiền, ngày) nên để UI.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- dùng hàm string, số và ngày phổ biến, dự đoán đúng `LEN`, `DATALENGTH`, phép chia số nguyên và `DATEDIFF`;
- viết searched `CASE` và simple `CASE`, đặt thứ tự nhánh đúng, luôn có `ELSE` có chủ đích;
- kết hợp `COALESCE`, `NULLIF`, `TRIM` để xử lý cả `NULL` lẫn chuỗi rỗng;
- phân biệt `ISNULL` và `COALESCE` về kiểu kết quả;
- đếm theo nhiều điều kiện trong một lần quét bằng `SUM(CASE ...)`;
- giữ predicate SARGable: so sánh column với khoảng giá trị thay vì bọc column trong hàm.

## 2. Bài toán mở đầu

Dashboard sản phẩm cần, cho mỗi hàng:

```text
tên đã bỏ khoảng trắng thừa       "  Keyboard Pro  " → "Keyboard Pro"
mức giá                           Budget / Standard / Premium
mô tả thay thế                    NULL hoặc "" → "(chưa có mô tả)"
tuổi sản phẩm theo ngày           tính tới một mốc cố định
phần trăm giảm giá                không được chia cho 0, không được sai khi ListPrice NULL
```

Phiên bản đầu dùng `DATEDIFF(day, CreatedAt, SYSUTCDATETIME())`: mỗi lần chạy ra số khác, test không bao giờ ổn định. Một dev khác viết `CASE` mức giá theo thứ tự ngược và chuột 350 000 bị gắn nhãn `Standard` — không ai thấy lỗi vì query vẫn chạy.

### Trực giác 60 giây

Hãy nghĩ tới một dây chuyền: mỗi hàng đi qua một trạm biến đổi và ra đúng **một** giá trị mới — không thêm, không bớt hàng. Hàm scalar là trạm cố định (“cắt khoảng trắng”, “đếm ngày”). `CASE` là trạm phân loại có danh sách quy tắc đọc từ trên xuống: hàng khớp quy tắc nào **trước** thì dừng ở đó, không khớp quy tắc nào và không có `ELSE` thì ra `NULL`. `NULL` đi vào hầu hết các trạm sẽ đi ra vẫn là `NULL`, trừ trạm sinh ra để xử lý nó: `COALESCE`, `ISNULL`, `IS NULL`.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| scalar function | hàm nhận giá trị của một hàng, trả một giá trị | `TRIM(Name)`, `DATEDIFF(day, ...)` |
| searched `CASE` | các nhánh `WHEN <điều kiện>` đánh giá từ trên xuống | `CASE WHEN Price < 500000 THEN ...` |
| simple `CASE` | so một biểu thức với từng giá trị bằng `=` | `CASE Status WHEN 'Paid' THEN ...` |
| `COALESCE` | trả giá trị khác `NULL` đầu tiên trong danh sách | `COALESCE(ListPrice, Price)` |
| `NULLIF(a, b)` | trả `NULL` nếu `a = b`, ngược lại trả `a` | `NULLIF(TRIM(Description), N'')` |
| SARGable predicate | điều kiện engine dùng được index để tìm phạm vi | `CreatedAt >= @Start AND CreatedAt < @End` |

### Ví dụ nhỏ — tính tay trước

Ba sản phẩm, quy tắc `Price < 500000 → Budget`, `Price < 3000000 → Standard`, còn lại `Premium`:

```text
Office Mouse   350 000
USB Hub        500 000
4K Monitor   7 200 000
```

(a) Nhãn đúng của từng sản phẩm? (b) Nếu đảo hai nhánh đầu (`< 3000000` đứng trước `< 500000`), chuột mang nhãn gì? (c) Nếu bỏ `ELSE`, màn hình mang nhãn gì? (d) `7 / 2` trong SQL Server bằng bao nhiêu?

Đáp án để đối chiếu: (a) Budget, Standard (500 000 không `< 500000`), Premium; (b) Standard — nhánh đầu đã đúng nên nhánh `Budget` không bao giờ được xét; (c) `NULL`; (d) `3` — hai số nguyên chia nhau cho số nguyên.

## 3. Lời giải chạy được

Dùng SQL Server 2025 đã dựng ở [bài 01](./01-mo-hinh-quan-he-va-cai-dat-sql-server.md). Lưu script thành `lab06.sql` và chạy `sqlcmd ... -C -b -i /tmp/lab06.sql` như các bài trước. Mốc thời gian `@AsOf` được cố định để output lặp lại được:

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
(N'  Keyboard Pro  ', 1200000, 1500000, NULL,               '2026-01-01'),
(N'Office Mouse',      350000,  350000, N'Basic mouse',     '2026-02-01'),
(N'4K Monitor',       7200000,    NULL, N'27-inch monitor', '2026-03-01'),
(N'USB Hub',           500000,  600000, N'',                '2026-03-15');
GO

-- Mốc thời gian cố định để kết quả lặp lại được; ứng dụng thật truyền vào.
DECLARE @AsOf datetime2(0) = '2026-04-01T00:00:00';

-- 1) Dashboard: biến đổi theo từng hàng.
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
    COALESCE(NULLIF(TRIM(Description), N''), N'(chưa có mô tả)') AS DisplayDescription,
    DATEDIFF(day, CreatedAt, @AsOf) AS AgeInDays,
    CAST(
        (COALESCE(ListPrice, Price) - Price)
        / NULLIF(COALESCE(ListPrice, Price), 0)
        * 100
        AS decimal(6,2)
    ) AS DiscountPercent
FROM dbo.Products
ORDER BY ProductId;

-- 2) CASE dừng ở WHEN đúng đầu tiên; thiếu ELSE thì ra NULL.
SELECT
    TRIM(Name) AS CleanName,
    Price,
    CASE
        WHEN Price < 3000000 THEN 'Standard'
        WHEN Price < 500000 THEN 'Budget'
        ELSE 'Premium'
    END AS WrongOrderTier,
    CASE
        WHEN Price < 500000 THEN 'Budget'
        WHEN Price < 3000000 THEN 'Standard'
    END AS MissingElseTier
FROM dbo.Products
ORDER BY ProductId;

-- 3) CASE bên trong aggregate: đếm theo điều kiện trong một lần quét.
SELECT
    SUM(CASE WHEN Price < 500000 THEN 1 ELSE 0 END) AS BudgetCount,
    SUM(CASE WHEN Price >= 500000 AND Price < 3000000 THEN 1 ELSE 0 END) AS StandardCount,
    SUM(CASE WHEN Price >= 3000000 THEN 1 ELSE 0 END) AS PremiumCount,
    SUM(CASE WHEN Description IS NULL OR TRIM(Description) = N'' THEN 1 ELSE 0 END) AS MissingDescriptionCount
FROM dbo.Products;

-- 4) Những kết quả dễ đoán sai.
SELECT
    LEN(N'  Keyboard Pro  ') AS LenIgnoresTrailing,
    DATALENGTH(N'  Keyboard Pro  ') AS DataLengthBytes,
    7 / 2 AS IntegerDivision,
    7 / 2.0 AS DecimalDivision,
    DATEDIFF(month, '2026-01-31', '2026-02-01') AS MonthBoundariesCrossed,
    ISNULL(CAST(NULL AS varchar(3)), 'abcdef') AS IsNullResult,
    COALESCE(CAST(NULL AS varchar(3)), 'abcdef') AS CoalesceResult;
GO
```

Output (SQL Server 2025, đã lược dòng thông báo):

```text
ProductId | CleanName    | ShortCode | Price        | PriceTier | DisplayDescription | AgeInDays | DiscountPercent
----------+--------------+-----------+--------------+-----------+--------------------+-----------+----------------
1         | Keyboard Pro | KEY       | 1200000.0000 | Standard  | (chưa có mô tả)    | 90        | 20.00
2         | Office Mouse | OFF       | 350000.0000  | Budget    | Basic mouse        | 59        | .00
3         | 4K Monitor   | 4K        | 7200000.0000 | Premium   | 27-inch monitor    | 31        | .00
4         | USB Hub      | USB       | 500000.0000  | Standard  | (chưa có mô tả)    | 17        | 16.67

CleanName    | Price        | WrongOrderTier | MissingElseTier
-------------+--------------+----------------+----------------
Keyboard Pro | 1200000.0000 | Standard       | Standard
Office Mouse | 350000.0000  | Standard       | Budget
4K Monitor   | 7200000.0000 | Premium        | NULL
USB Hub      | 500000.0000  | Standard       | Standard

BudgetCount | StandardCount | PremiumCount | MissingDescriptionCount
------------+---------------+--------------+------------------------
1           | 2             | 1            | 2

LenIgnoresTrailing | DataLengthBytes | IntegerDivision | DecimalDivision | MonthBoundariesCrossed | IsNullResult | CoalesceResult
-------------------+-----------------+-----------------+-----------------+------------------------+--------------+---------------
14                 | 32              | 3               | 3.500000        | 1                      | abc          | abcdef
```

`ShortCode` của màn hình thực ra là `'4K '` (có khoảng trắng cuối) vì `LEFT(..., 3)` lấy cả dấu cách trong `4K Monitor`.

### Walkthrough — execution / state / cost

1. **`TRIM`, `LEFT`, `UPPER`:** chạy trên từng hàng, từ trong ra ngoài: `TRIM(N'  Keyboard Pro  ')` → `Keyboard Pro` → `LEFT(..., 3)` → `Key` → `KEY`. Dữ liệu trong table không đổi; chỉ giá trị trả về bị biến đổi.
2. **`PriceTier`:** với USB Hub 500 000, `Price < 500000` sai, `Price < 3000000` đúng → `Standard`. Biên `<` hay `<=` là quyết định nghiệp vụ, phải ghi rõ.
3. **Mô tả:** bàn phím có `NULL`, hub có `N''`. `NULLIF(TRIM(Description), N'')` đổi chuỗi rỗng thành `NULL`, sau đó `COALESCE` thay cả hai bằng `(chưa có mô tả)`. Nếu chỉ dùng `COALESCE`, hub sẽ hiện ô trống.
4. **`AgeInDays`:** `DATEDIFF(day, '2026-01-01', '2026-04-01')` = 31 + 28 + 31 = 90. Mốc `@AsOf` cố định nên chạy lại vẫn ra 90.
5. **`DiscountPercent`:** màn hình có `ListPrice = NULL` → `COALESCE` dùng `Price` → giảm 0%. `NULLIF(..., 0)` biến mẫu số 0 thành `NULL`, nên phép chia trả `NULL` thay vì lỗi chia cho 0. Hub: (600 000 − 500 000) / 600 000 × 100 = 16.666… → làm tròn thành `16.67` khi `CAST` về `decimal(6,2)`.
6. **`WrongOrderTier`:** nhánh `< 3000000` đứng đầu bắt luôn chuột 350 000; nhánh `Budget` không bao giờ được xét. **`MissingElseTier`:** màn hình không khớp nhánh nào → `NULL`.
7. **`SUM(CASE ...)`:** mỗi hàng góp 1 hoặc 0 vào từng cột đếm; một lần quét cho bốn con số. Bài [07](./07-group-by-aggregate-va-having.md) dùng mẫu này cho báo cáo.
8. **Những kết quả dễ đoán sai:** `LEN` bỏ khoảng trắng **cuối** (14 ký tự), `DATALENGTH` đếm byte gồm cả khoảng trắng (16 × 2 = 32); `7 / 2 = 3`; `DATEDIFF(month, ...)` đếm số lần **vượt ranh giới tháng**, nên 31/01 → 01/02 là 1 tháng dù chỉ cách 1 ngày; `ISNULL` lấy kiểu của tham số đầu (`varchar(3)`) nên cắt thành `abc`, `COALESCE` lấy kiểu ưu tiên cao nhất trong danh sách nên giữ `abcdef`.
9. **Cost:** hàm scalar built-in trong `SELECT` rẻ — chạy một lần mỗi hàng đã được chọn. Chi phí thật xuất hiện khi hàm bọc column trong `WHERE` (mục 6) hoặc khi dùng scalar UDF tự viết chạy cho hàng triệu hàng (bài [13](./13-view-stored-procedure-function-trigger.md)).

### Mini-check

Nếu đổi `ELSE 'Premium'` thành `ELSE NULL` trong `PriceTier`, `SUM(CASE WHEN PriceTier = 'Premium' ...)` ở một query bọc ngoài đếm được mấy sản phẩm, và lỗi đó có hiện ra ở đâu không?

## 4. Cơ chế hoạt động

### Hàm scalar: một hàng vào, một giá trị ra

```text
string:  TRIM, LTRIM/RTRIM, LEFT/RIGHT, SUBSTRING, UPPER/LOWER, REPLACE, LEN, DATALENGTH, CONCAT
số:      ROUND, CEILING, FLOOR, ABS, CAST/CONVERT
ngày:    DATEADD, DATEDIFF, DATEFROMPARTS, EOMONTH, YEAR/MONTH/DAY
NULL:    COALESCE, ISNULL, NULLIF
```

Kiểu kết quả theo **data type precedence**: `int / int` → `int`; `int / decimal` → `decimal`. Muốn chia lấy phần thập phân, ít nhất một vế phải là `decimal` (`7 / 2.0`, hoặc `CAST(x AS decimal(19,4))`).

### `CASE`: first match wins

```sql
-- searched CASE: mỗi WHEN là một điều kiện
CASE
    WHEN Price < 500000 THEN 'Budget'
    WHEN Price < 3000000 THEN 'Standard'
    ELSE 'Premium'
END

-- simple CASE: so sánh một biểu thức bằng '='
CASE Status
    WHEN 'Paid' THEN N'Đã thanh toán'
    WHEN 'Pending' THEN N'Chờ thanh toán'
    ELSE N'Khác'
END
```

Hai luật cần nhớ: nhánh được xét từ trên xuống và dừng ở nhánh đúng đầu tiên; thiếu `ELSE` nghĩa là `ELSE NULL`. Simple `CASE` dùng `=`, nên `CASE x WHEN NULL THEN ...` **không bao giờ** khớp (đã kiểm chứng: ra nhánh `ELSE`); muốn bắt `NULL` thì dùng searched `CASE WHEN x IS NULL`. `CASE` là **biểu thức**, dùng được trong `SELECT`, `ORDER BY`, `UPDATE ... SET` và bên trong aggregate.

### `COALESCE`, `ISNULL`, `NULLIF`

- `COALESCE(a, b, c)`: chuẩn SQL, nhiều tham số, kiểu kết quả là kiểu ưu tiên cao nhất.
- `ISNULL(a, b)`: riêng T-SQL, đúng hai tham số, kiểu kết quả là kiểu của `a` — có thể cắt chuỗi như lab.
- `NULLIF(a, b)`: “nếu bằng thì coi như không có”. Hai cách dùng phổ biến: chống chia cho 0 (`x / NULLIF(y, 0)`) và đổi giá trị “ma” thành `NULL` (`NULLIF(TRIM(s), N'')`).

### Hàm trong `WHERE` và SARGability

```sql
-- Bọc column trong hàm: engine phải tính YEAR() cho mọi hàng.
WHERE YEAR(CreatedAt) = 2026

-- So sánh column trần với khoảng: index trên CreatedAt tìm thẳng phạm vi.
WHERE CreatedAt >= '2026-01-01'
  AND CreatedAt <  '2027-01-01'
```

Hai điều kiện cho cùng kết quả, nhưng chỉ dạng thứ hai cho phép index seek. Quy tắc: biến đổi **tham số**, không biến đổi **column**. Bài [22](./22-toi-uu-truy-van-va-sargability.md) đo khác biệt bằng execution plan.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| `CASE` trong query | tính giá trị dẫn xuất mỗi lần đọc | đơn giản, luôn khớp dữ liệu hiện tại; không hợp khi cùng luật bị chép vào nhiều query |
| Computed column / view (bài [13](./13-view-stored-procedure-function-trigger.md)) | định nghĩa luật dẫn xuất một lần trong database | mọi query dùng chung một luật; đổi luật cần migration |
| Lưu giá trị dẫn xuất vào column thường | chụp lại kết quả tại thời điểm ghi | đọc nhanh, giữ được lịch sử (giá lúc bán); phải tự đồng bộ khi nguồn đổi |
| Tính ở application/UI | biến đổi sau khi đọc | hợp cho định dạng tiền/ngày theo ngôn ngữ; không dùng khi cần lọc, sắp xếp hoặc đếm theo giá trị đó trong SQL |

### Misconception check

**Đúng hay sai?** Thứ tự các nhánh `WHEN` không quan trọng vì `CASE` chọn nhánh khớp nhất.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. `CASE` chọn nhánh đúng **đầu tiên**, không phải nhánh “chặt” nhất. Lab: đặt `< 3000000` trước khiến chuột 350 000 thành `Standard`.

</details>

**Đúng hay sai?** `ISNULL(a, b)` và `COALESCE(a, b)` luôn cho cùng kết quả.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. Giá trị thay thế giống nhau nhưng kiểu kết quả khác: `ISNULL` theo kiểu của `a` nên `varchar(3)` cắt `abcdef` thành `abc`; `COALESCE` theo kiểu ưu tiên cao nhất nên giữ `abcdef`.

</details>

**Đúng hay sai?** `DATEDIFF(month, '2026-01-31', '2026-02-01')` bằng 0 vì chưa đủ một tháng.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. `DATEDIFF` đếm số ranh giới (đầu tháng) bị vượt qua, không đo độ dài khoảng thời gian; lab cho `1`. Tuổi chính xác theo tháng/năm phải tự tính với điều kiện so ngày.

</details>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** `TRIM`/`LEFT`/`UPPER`, searched `CASE` có `ELSE`, `COALESCE`, `NULLIF` chống chia 0, `DATEDIFF` theo ngày.
- **Working Developer — dùng khi làm việc:** thứ tự nhánh `CASE`, `NULLIF(TRIM(s), N'')`, `SUM(CASE ...)`, `ISNULL` vs `COALESCE`, mốc thời gian truyền vào thay vì gọi hàm giờ hệ thống, predicate SARGable.
- **Deep Dive — có thể quay lại sau:** data type precedence, `DATEDIFF` đếm ranh giới, khác biệt phương ngữ SQL Server ↔ PostgreSQL.

Bài trước: [Filter, sort và pagination](./05-filter-sort-va-pagination.md). Liên hệ: `CASE` giống `switch` expression của C# — cũng là “nhánh khớp đầu tiên thắng”, nhưng C# bắt buộc xử lý đủ trường hợp còn SQL lặng lẽ trả `NULL` ([pattern matching](../05-csharp-nang-cao/08-pattern-matching.md)).

### Thời gian “hiện tại” là một tham số

`SYSUTCDATETIME()` trong query làm kết quả đổi theo thời điểm chạy: test không lặp lại được, và hai query trong cùng một báo cáo có thể dùng hai mốc khác nhau. Ứng dụng nên truyền mốc thời gian vào (`@AsOf`), giống cách inject clock trong C# để test được.

### Đào sâu (có thể quay lại sau)

Khác biệt phương ngữ hay gặp khi chuyển giữa SQL Server và PostgreSQL (tham khảo, lab chỉ chạy trên SQL Server):

```text
Ý định                SQL Server                         PostgreSQL
độ dài chuỗi          LEN(s) (bỏ khoảng trắng cuối)      length(s) (đếm đủ)
nối chuỗi             s1 + s2, CONCAT(s1, s2)            s1 || s2, concat(s1, s2)
thay NULL             ISNULL(a, b), COALESCE(a, b)       COALESCE(a, b)
số ngày giữa hai date DATEDIFF(day, d1, d2)              d2 - d1
n hàng đầu            TOP (n) / OFFSET … FETCH           LIMIT n / OFFSET … FETCH
```

`COALESCE`, `NULLIF`, `CASE` và `TRIM` là phần chuẩn, chạy được ở cả hai; ưu tiên chúng khi viết SQL cần dùng lại giữa các engine.

## 6. Lỗi thường gặp

### Sắp nhánh `CASE` sai thứ tự

Nhánh rộng đứng trước nuốt nhánh hẹp. Sắp theo một chiều (tăng dần cận trên) và viết test với giá trị ở đúng biên.

### Quên `ELSE`

Giá trị ngoài dự kiến thành `NULL`, rồi biến mất khỏi mọi `WHERE PriceTier = ...` và báo cáo. Luôn có `ELSE`, kể cả `ELSE 'Unknown'` để lộ ra dữ liệu lạ.

### Chia số nguyên

`SUM(Quantity) / COUNT(*)` với hai vế `int` cắt mất phần thập phân. `CAST` một vế sang `decimal` trước khi chia.

### Chia cho 0

Lỗi `8134` làm hỏng cả query. Dùng `NULLIF(denominator, 0)` khi `NULL` là kết quả chấp nhận được, và quyết định UI hiển thị gì cho `NULL`.

### Bọc column trong hàm ở `WHERE`

`WHERE YEAR(CreatedAt) = 2026`, `WHERE TRIM(Email) = @Email`, `WHERE CONVERT(date, OrderedAt) = @Day` đều chặn index seek. Chuẩn hóa dữ liệu khi ghi, hoặc viết lại thành khoảng.

### Gọi hàm giờ hệ thống trong query cần test

Kết quả đổi theo thời điểm chạy. Truyền mốc thời gian làm tham số.

### Định dạng tiền/ngày trong SQL

`FORMAT(Price, 'N0')` trả chuỗi: mất khả năng sắp xếp/tính toán ở tầng sau, và chậm. Trả kiểu gốc, định dạng ở UI theo ngôn ngữ người dùng.

## 7. Khi nào KHÔNG dùng

- **Không chép cùng một `CASE` nghiệp vụ vào nhiều query:** đưa vào view/computed column, hoặc lưu thành trạng thái có tên nếu nó là state thật (đơn hàng `Shipped` không nên là “`CASE WHEN ShippedAt IS NOT NULL`” ở 20 chỗ).
- **Không dùng `CASE` thay table tra cứu** khi danh sách giá trị dài hoặc hay đổi: join với table cấu hình.
- **Không dùng hàm bọc column trong `WHERE`/`JOIN`** trên table lớn.
- **Không dùng `ISNULL`** khi hai tham số khác kiểu hoặc khi code cần chạy trên engine khác: dùng `COALESCE`.
- **Không định dạng hiển thị trong SQL** trừ khi đầu ra là file xuất cho người đọc trực tiếp.

Tín hiệu đang dùng sai: sửa một ngưỡng giá phải tìm-thay trong nhiều file SQL, hoặc báo cáo “mất” hàng vì nhãn `NULL`. Phương án đơn giản hơn: một nguồn định nghĩa luật (view, computed column hoặc table cấu hình). Câu hỏi quyết định: giá trị này là cách **hiển thị**, là **luật dẫn xuất** dùng chung, hay là **trạng thái** cần lưu?

## 8. Production notes & scale check

- **Logic dẫn xuất dùng chung:** đặt ở một chỗ — view hoặc computed column (bài [13](./13-view-stored-procedure-function-trigger.md)); persisted computed column còn index được.
- **Scalar UDF tự viết:** từ SQL Server 2019 có thể được inline, nhưng không phải mọi hàm đủ điều kiện; đo plan trước khi đặt UDF vào query nóng.
- **Chuẩn hóa khi ghi:** `TRIM`/lowercase email một lần ở tầng ghi rẻ hơn `TRIM` ở mọi lần đọc và giữ predicate SARGable.
- **Biên thời gian:** dùng một `@AsOf` cho cả báo cáo để mọi con số cùng một mốc; ghi mốc đó lên báo cáo.
- **Ngưỡng nghiệp vụ:** ngưỡng `500000`/`3000000` nằm trong code SQL nghĩa là đổi ngưỡng cần deploy; nếu business đổi thường xuyên, chuyển sang table cấu hình.
- **Team 2–3 người:** `CASE` trong query là đủ khi luật chỉ dùng ở một hai chỗ; tách ra view khi luật xuất hiện lần thứ ba.

## 9. Bài tập kỹ thuật

### Bài 1 — Nhãn tồn kho

Thêm `Stock int NOT NULL` và tạo nhãn `0 → OutOfStock`, `1–10 → Low`, `> 10 → Available`; viết test dữ liệu cho các giá trị biên 0, 1, 10, 11.

**Gợi ý:** sắp nhánh theo cận trên tăng dần và vẫn có `ELSE`.

### Bài 2 — Kênh liên lạc

Với `Phone` và `Email` đều nullable và có thể là chuỗi rỗng, trả kênh liên lạc ưu tiên phone, rồi email, rồi `N'(không có)'`.

**Gợi ý:** `COALESCE` của hai `NULLIF(TRIM(...), N'')`.

### Bài 3 — Thời gian giao hàng

Tính số ngày từ `OrderedAt` tới `ShippedAt`; nếu chưa giao thì tính tới `@AsOf`. Thêm nhãn `Late` khi quá 3 ngày.

**Gợi ý:** `DATEDIFF(day, OrderedAt, COALESCE(ShippedAt, @AsOf))`; nhớ `DATEDIFF` đếm ranh giới.

### Bài 4 — Lọc theo năm

Viết hai phiên bản lọc sản phẩm tạo trong năm 2026 và giải thích phiên bản nào SARGable.

**Gợi ý:** biến đổi tham số thành khoảng nửa mở `[2026-01-01, 2027-01-01)`.

### Bài 5 — `ISNULL` hay `COALESCE`

Tìm thêm một trường hợp `ISNULL` và `COALESCE` cho kết quả khác nhau (gợi ý: thử `int` với chuỗi, hoặc `NULL` không kiểu).

**Gợi ý:** so sánh kiểu kết quả bằng `SQL_VARIANT_PROPERTY(expr, 'BaseType')`.

## 10. Bài tập tích hợp liên module — Judgment

Nhãn “khách VIP” (tổng chi tiêu 12 tháng trên 20 triệu) đang được tính bằng `CASE` trong 4 query báo cáo và một lần nữa bằng `if` trong C# (Module 06) cho màn hình khách hàng. Đề xuất nơi duy nhất định nghĩa luật: view SQL, computed column, cột lưu được cập nhật định kỳ, hay service C#. Phân tích theo: ai đọc nhãn (báo cáo SQL, API, job), luật có đổi không, dữ liệu cần để tính nằm ở đâu, và cost mỗi lần đọc.

**Tiêu chí:** chỉ ra một nguồn sự thật cho luật, cách các nơi khác dùng lại nó, và điều gì xảy ra khi ngưỡng đổi; không chấm theo số công nghệ được dùng.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Viết `CASE` xếp điểm A/B/C/D với ngưỡng 85/70/50 và chỉ ra giá trị biên cần test.
2. Vì sao `CASE x WHEN NULL THEN ...` không bao giờ khớp?
3. Dự đoán `LEN` và `DATALENGTH` của `N'SQL  '`.
4. Viết phép tính tỉ lệ hoàn đơn không lỗi chia 0 và không cắt phần thập phân.
5. Viết lại `WHERE MONTH(OrderedAt) = 3 AND YEAR(OrderedAt) = 2026` thành dạng SARGable.

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi dự đoán đúng kết quả `LEN`/`DATALENGTH`, chia số nguyên và `DATEDIFF`.
- [ ] Tôi viết `CASE` đúng thứ tự nhánh và luôn có `ELSE` có chủ đích.
- [ ] Tôi xử lý cả `NULL` lẫn chuỗi rỗng bằng `NULLIF` + `COALESCE`.
- [ ] Tôi chọn đúng giữa `ISNULL` và `COALESCE`.
- [ ] Tôi giữ predicate SARGable và truyền mốc thời gian làm tham số.

**Bài prerequisite:** [Filter, sort và pagination](./05-filter-sort-va-pagination.md)

**Bài tiếp theo:** [GROUP BY, aggregate và HAVING](./07-group-by-aggregate-va-having.md)
