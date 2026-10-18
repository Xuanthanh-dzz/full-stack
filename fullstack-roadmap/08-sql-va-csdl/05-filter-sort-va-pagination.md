# Filter, sort và pagination

> **Last verified:** 2026-10-18
>
> **Baseline:** SQL Server 2025 (17.0.x) · T-SQL · sqlcmd (mssql-tools18) · Docker image `mcr.microsoft.com/mssql/server:2025-latest` · collation `SQL_Latin1_General_CP1_CI_AS`
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** SQL Server major/CU đổi hành vi `OFFSET/FETCH`, `LIKE` hoặc chuyển đổi date/time, đổi collation server/database, đổi image hoặc sqlcmd, đổi lab/schema, CI `verify-module-08` fail

## TL;DR

- `WHERE` lọc tập hàng, `ORDER BY` xếp thứ tự, `OFFSET/FETCH` hoặc keyset cắt ra một trang; trang chỉ có nghĩa khi thứ tự là **deterministic** — có tiebreaker duy nhất như `ProductId`.
- Dùng offset pagination cho UI cần nhảy tới trang N trên tập vừa phải; dùng keyset (“tiếp sau hàng cuối”) cho feed, infinite scroll và tập lớn hoặc thay đổi liên tục.
- Trade-off: offset dễ làm nhưng page sâu phải đọc rồi bỏ qua nhiều hàng và bị lặp/sót khi dữ liệu đổi giữa hai request; keyset ổn định và rẻ nhưng không nhảy trang tùy ý được.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- viết `WHERE` nhiều predicate với `AND`/`OR`/`NOT`, `IN`, `BETWEEN`, `LIKE` và đặt ngoặc đúng;
- lọc khoảng thời gian bằng khoảng nửa mở `>= start AND < end` thay vì `BETWEEN`;
- escape wildcard trong từ khóa người dùng trước khi ghép vào `LIKE`;
- sắp xếp nhiều column với tiebreaker duy nhất;
- phân trang bằng `OFFSET/FETCH` và bằng keyset, giải thích page drift;
- ánh xạ query string của API (`search`, `minPrice`, `page`, …) thành parameter SQL.

## 2. Bài toán mở đầu

API danh sách sản phẩm nhận:

```text
GET /products?search=keyboard&minPrice=400000&maxPrice=3000000&sort=price-desc&page=2&pageSize=3
```

QA báo ba lỗi: trang 2 lặp lại một sản phẩm đã có ở trang 1; tìm “Mouse hoặc Hub” lại ra cả sản phẩm đã ngừng bán; báo cáo đơn tháng 3 thiếu đơn ngày 31. Không lỗi nào gây exception — query vẫn chạy, chỉ trả **sai tập hàng**.

### Trực giác 60 giây

Hình dung hàng người xếp theo chiều cao. `WHERE` là người gác cửa chọn ai được vào hàng, `ORDER BY` là luật xếp, phân trang là “lấy 3 người tiếp theo”. Offset nói “bỏ qua 3 người đầu rồi lấy 3” — nếu có người mới chen lên đầu hàng, người thứ 3 cũ bị đẩy thành thứ 4 và bạn gặp lại họ. Keyset nói “lấy 3 người đứng ngay sau anh cao 1m70 mã số 1” — ai chen lên đầu cũng không ảnh hưởng. Còn nếu hai người cao bằng nhau mà luật xếp không nói ai trước, mỗi lần nhìn có thể thấy thứ tự khác: đó là lý do cần tiebreaker.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| predicate | điều kiện cho ra `TRUE`/`FALSE`/`UNKNOWN` trên từng hàng | `Price BETWEEN @MinPrice AND @MaxPrice` |
| operator precedence | thứ tự ưu tiên khi không có ngoặc: `NOT` > `AND` > `OR` | `A AND B OR C` là `(A AND B) OR C` |
| wildcard | ký tự đại diện trong `LIKE`: `%` nhiều ký tự, `_` một ký tự | `N'%keyboard%'` |
| tiebreaker | column duy nhất thêm cuối `ORDER BY` để không còn hàng “hòa” | `ProductId ASC` |
| offset pagination | bỏ qua N hàng rồi lấy M hàng | `OFFSET 3 ROWS FETCH NEXT 3 ROWS ONLY` |
| keyset pagination | lấy M hàng đứng sau hàng cuối của trang trước | `Price < 1200000 OR (Price = 1200000 AND ProductId > 1)` |
| half-open interval | khoảng gồm đầu, không gồm cuối | `OrderedAt >= '2026-03-01' AND OrderedAt < '2026-04-01'` |

### Ví dụ nhỏ — tính tay trước

Năm bàn phím đang bán, sắp `Price DESC, ProductId ASC`:

```text
ProductId  Price
8          2 200 000
2          1 800 000
1          1 200 000
9          1 200 000
3            500 000
```

Page size 3. (a) Trang 1 gồm id nào? (b) Trang 2 (offset 3) gồm id nào? (c) Giữa hai lần gọi, thêm bàn phím id 10 giá 2 500 000. Trang 2 bằng offset giờ gồm id nào? (d) Trang 2 bằng keyset “sau (1 200 000, id 1)” gồm id nào?

Đáp án để đối chiếu: (a) 8, 2, 1; (b) 9, 3; (c) 1, 9, 3 — id 1 bị lặp vì mọi hàng bị đẩy xuống một bậc; (d) 9, 3 — không lặp, không sót. Nếu bỏ `ProductId` khỏi `ORDER BY`, id 1 và 9 hòa nhau và (a) có thể là 8, 2, 9 ở lần chạy khác.

## 3. Lời giải chạy được

Dùng SQL Server 2025 đã dựng ở [bài 01](./01-mo-hinh-quan-he-va-cai-dat-sql-server.md). Lưu script thành `lab05.sql` và chạy `sqlcmd ... -C -b -i /tmp/lab05.sql` như các bài trước:

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_05') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_05
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_05;
END;
GO

CREATE DATABASE CommerceLab08_05;
GO
USE CommerceLab08_05;
GO

CREATE TABLE dbo.Products
(
    ProductId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Name nvarchar(160) NOT NULL,
    Price decimal(19,4) NOT NULL,
    IsActive bit NOT NULL,
    CreatedAt datetime2(0) NOT NULL
);

CREATE TABLE dbo.Orders
(
    OrderId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Orders PRIMARY KEY,
    OrderedAt datetime2(0) NOT NULL,
    Total decimal(19,4) NOT NULL
);
GO

INSERT INTO dbo.Products (Name, Price, IsActive, CreatedAt)
VALUES
(N'Mechanical Keyboard A', 1200000, 1, '2026-01-01'),
(N'Mechanical Keyboard B', 1800000, 1, '2026-01-02'),
(N'Office Keyboard',        500000, 1, '2026-01-03'),
(N'Gaming Mouse',           900000, 1, '2026-01-04'),
(N'4K Monitor',            6500000, 1, '2026-01-05'),
(N'USB Hub',                400000, 0, '2026-01-06'),
(N'Keyboard Wrist Rest',    350000, 1, '2026-01-07'),
(N'Mechanical Keyboard C', 2200000, 1, '2026-01-08'),
(N'Mechanical Keyboard D', 1200000, 1, '2026-01-09');

INSERT INTO dbo.Orders (OrderedAt, Total)
VALUES
('2026-03-01T09:00:00', 1200000),
('2026-03-15T14:00:00',  900000),
('2026-03-31T10:30:00',  500000),
('2026-04-01T00:00:00', 1800000);
GO

-- 1) Search + filter + sort ổn định + OFFSET/FETCH (page 1).
--    Collation CI_AS: 'keyboard' khớp 'Keyboard'.
DECLARE @Search nvarchar(100) = N'keyboard';
DECLARE @MinPrice decimal(19,4) = 400000;
DECLARE @MaxPrice decimal(19,4) = 3000000;
DECLARE @Page int = 1;
DECLARE @PageSize int = 3;

SELECT
    ProductId,
    Name,
    Price
FROM dbo.Products
WHERE IsActive = 1
  AND Name LIKE N'%' + @Search + N'%'
  AND Price BETWEEN @MinPrice AND @MaxPrice
ORDER BY
    Price DESC,
    ProductId ASC
OFFSET (@Page - 1) * @PageSize ROWS
FETCH NEXT @PageSize ROWS ONLY;
GO

-- 2) Page drift: có sản phẩm mới chen lên đầu giữa hai lần gọi.
INSERT INTO dbo.Products (Name, Price, IsActive, CreatedAt)
VALUES (N'Mechanical Keyboard X', 2500000, 1, '2026-01-10');

DECLARE @Search nvarchar(100) = N'keyboard';
DECLARE @MinPrice decimal(19,4) = 400000;
DECLARE @MaxPrice decimal(19,4) = 3000000;
DECLARE @Page int = 2;
DECLARE @PageSize int = 3;

SELECT
    N'offset page 2' AS Strategy,
    ProductId,
    Name,
    Price
FROM dbo.Products
WHERE IsActive = 1
  AND Name LIKE N'%' + @Search + N'%'
  AND Price BETWEEN @MinPrice AND @MaxPrice
ORDER BY
    Price DESC,
    ProductId ASC
OFFSET (@Page - 1) * @PageSize ROWS
FETCH NEXT @PageSize ROWS ONLY;

-- 3) Keyset: tiếp tục sau hàng cuối của page 1 (Price 1200000, ProductId 1).
DECLARE @AfterPrice decimal(19,4) = 1200000;
DECLARE @AfterProductId int = 1;

SELECT TOP (@PageSize)
    N'keyset after (1200000, 1)' AS Strategy,
    ProductId,
    Name,
    Price
FROM dbo.Products
WHERE IsActive = 1
  AND Name LIKE N'%' + @Search + N'%'
  AND Price BETWEEN @MinPrice AND @MaxPrice
  AND (
        Price < @AfterPrice
     OR (Price = @AfterPrice AND ProductId > @AfterProductId)
      )
ORDER BY
    Price DESC,
    ProductId ASC;
GO

-- 4) AND ưu tiên hơn OR: thiếu ngoặc làm lọt sản phẩm ngừng bán.
SELECT
    (SELECT COUNT(*)
     FROM dbo.Products
     WHERE IsActive = 1 AND Name LIKE N'%Mouse%' OR Name LIKE N'%Hub%') AS WithoutParentheses,
    (SELECT COUNT(*)
     FROM dbo.Products
     WHERE IsActive = 1 AND (Name LIKE N'%Mouse%' OR Name LIKE N'%Hub%')) AS WithParentheses;

-- 5) Từ khóa người dùng chứa wildcard: phải escape trước khi ghép vào LIKE.
DECLARE @RawTerm nvarchar(100) = N'%';

SELECT
    (SELECT COUNT(*)
     FROM dbo.Products
     WHERE Name LIKE N'%' + @RawTerm + N'%') AS RawMatches,
    (SELECT COUNT(*)
     FROM dbo.Products
     WHERE Name LIKE N'%'
         + REPLACE(REPLACE(REPLACE(@RawTerm, N'[', N'[[]'), N'%', N'[%]'), N'_', N'[_]')
         + N'%') AS EscapedMatches;

-- 6) BETWEEN với datetime2: ngày cuối chỉ tính tới 00:00:00.
SELECT
    (SELECT COUNT(*)
     FROM dbo.Orders
     WHERE OrderedAt BETWEEN '2026-03-01' AND '2026-03-31') AS BetweenMarch,
    (SELECT COUNT(*)
     FROM dbo.Orders
     WHERE OrderedAt >= '2026-03-01'
       AND OrderedAt < '2026-04-01') AS HalfOpenMarch;
GO
```

Output (SQL Server 2025, đã lược dòng thông báo):

```text
ProductId | Name                  | Price
----------+-----------------------+-------------
8         | Mechanical Keyboard C | 2200000.0000
2         | Mechanical Keyboard B | 1800000.0000
1         | Mechanical Keyboard A | 1200000.0000

Strategy      | ProductId | Name                  | Price
--------------+-----------+-----------------------+-------------
offset page 2 | 1         | Mechanical Keyboard A | 1200000.0000
offset page 2 | 9         | Mechanical Keyboard D | 1200000.0000
offset page 2 | 3         | Office Keyboard       | 500000.0000

Strategy                  | ProductId | Name                  | Price
--------------------------+-----------+-----------------------+-------------
keyset after (1200000, 1) | 9         | Mechanical Keyboard D | 1200000.0000
keyset after (1200000, 1) | 3         | Office Keyboard       | 500000.0000

WithoutParentheses | WithParentheses
-------------------+----------------
2                  | 1

RawMatches | EscapedMatches
-----------+---------------
10         | 0

BetweenMarch | HalfOpenMarch
-------------+--------------
2            | 3
```

### Walkthrough — execution / state / cost

1. **Trang 1:** `WHERE` giữ 5 bàn phím đang bán trong khoảng giá (`Keyboard Wrist Rest` 350 000 bị loại vì dưới `@MinPrice`). `LIKE N'%keyboard%'` khớp `Keyboard` vì collation `CI_AS` không phân biệt hoa thường. `ORDER BY Price DESC, ProductId ASC` xếp id 1 trước id 9 dù cùng giá; `OFFSET 0 ... FETCH NEXT 3` lấy 8, 2, 1.
2. **Chèn id 10 giá 2 500 000:** tập sau lọc giờ là 10, 8, 2, 1, 9, 3.
3. **Trang 2 bằng offset:** bỏ qua 3 hàng đầu (10, 8, 2) → lấy 1, 9, 3. Người dùng đã thấy id 1 ở trang 1 — **page drift**. Nếu một hàng bị xóa thay vì chèn, sẽ có hàng bị **sót**.
4. **Trang 2 bằng keyset:** client gửi khóa của hàng cuối trang 1 `(1200000, 1)`. Điều kiện “đứng sau” theo đúng thứ tự sort: giá nhỏ hơn, hoặc cùng giá và id lớn hơn → 9, 3. Hàng mới chen ở đầu không ảnh hưởng.
5. **`AND`/`OR`:** không ngoặc, engine hiểu là `(IsActive = 1 AND Name LIKE '%Mouse%') OR Name LIKE '%Hub%'` — `USB Hub` đã ngừng bán lọt vào (2 hàng). Có ngoặc → 1 hàng.
6. **Escape wildcard:** người dùng gõ `%` thì `LIKE N'%%%'` khớp **mọi** hàng (10, kể cả hàng ngừng bán vì query này không lọc `IsActive`). Sau khi bọc `%` thành `[%]`, nó được hiểu là ký tự `%` thật → 0 hàng.
7. **`BETWEEN` với thời gian:** `'2026-03-31'` được chuyển thành `2026-03-31 00:00:00`, nên đơn lúc 10:30 ngày 31 nằm ngoài khoảng → 2 thay vì 3. Khoảng nửa mở `< '2026-04-01'` bao trọn ngày cuối và không lấy đơn của 01/04.
8. **Cost:** không có index phù hợp, mỗi query quét toàn bộ table rồi sort. `OFFSET k` phải đọc và bỏ qua k hàng đã sort, nên trang càng sâu càng đắt; keyset với index trên `(Price, ProductId)` có thể nhảy thẳng tới vị trí bắt đầu (bài [18](./18-covering-filtered-composite-index.md) và [22](./22-toi-uu-truy-van-va-sargability.md)). `LIKE N'%...'` có wildcard ở đầu không dùng được index để tìm vị trí.

### Mini-check

Nếu `ORDER BY` chỉ là `Price DESC` (bỏ `ProductId`), hai lần gọi trang 1 có chắc cùng kết quả không? Hàng nào có thể đổi chỗ, và keyset `(Price, ProductId)` còn viết được không?

## 4. Cơ chế hoạt động

### Thứ tự xử lý logic

```text
FROM → WHERE → SELECT → ORDER BY → OFFSET/FETCH (hoặc TOP)
```

Phân trang áp **sau** sắp xếp, sắp xếp áp **sau** lọc. Vì vậy `WHERE` sai thì cả tập sai; `ORDER BY` không deterministic thì cùng một `OFFSET` có thể cắt ra hàng khác nhau giữa các lần chạy. Thứ tự logic này không phải thứ tự engine thực thi vật lý — optimizer có thể đổi cách làm miễn kết quả tương đương (bài [21](./21-execution-plan-va-statistics.md)).

### Predicate và ngoặc

- Ưu tiên: `NOT` > `AND` > `OR`. Khi trộn `AND` và `OR`, luôn đặt ngoặc dù bạn nhớ quy tắc — người đọc sau không phải đoán.
- `IN (a, b, c)` là `= a OR = b OR = c`; `NOT IN` gặp `NULL` thì không khớp gì (bài [03](./03-kieu-du-lieu-va-null.md)).
- `BETWEEN a AND b` bao gồm **cả hai đầu**: `>= a AND <= b`. Hợp với số nguyên và `date`; dễ sai với `datetime2`.

### `LIKE`, wildcard và collation

```text
%      0 hoặc nhiều ký tự        N'%board%'
_      đúng 1 ký tự              'KB-0_'
[...]  1 ký tự trong tập         '[%]' = ký tự % thật
```

Collation quyết định so sánh có phân biệt hoa thường/dấu hay không. Server lab dùng `SQL_Latin1_General_CP1_CI_AS`: `CI` = case-insensitive, `AS` = accent-sensitive. Database tạo bằng collation khác (ví dụ `_CS_`) sẽ cho `'keyboard'` không khớp `'Keyboard'`.

### Offset và keyset

```text
Offset:  sort toàn tập → bỏ qua (page - 1) * size hàng → lấy size hàng
Keyset:  tìm vị trí ngay sau khóa cuối (Price, ProductId) → lấy size hàng
```

Keyset cần khóa sort **duy nhất** để biết chính xác “sau” là đâu, và điều kiện phải theo đúng chiều sort của từng column. Client không gửi số trang mà gửi cursor — thường là khóa của hàng cuối đã mã hóa.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| `OFFSET/FETCH` | trang thứ N theo thứ tự đã sort | dễ làm, nhảy trang tùy ý, hợp admin/bảng nhỏ; page sâu đắt, lặp/sót khi dữ liệu đổi |
| Keyset (cursor) | các hàng đứng sau một khóa đã biết | ổn định khi dữ liệu đổi, rẻ ở mọi độ sâu nếu có index; không nhảy tới trang N, cần sort key duy nhất |
| `TOP (n)` không phân trang | n hàng đầu theo thứ tự | “top 10 bán chạy”; không dùng thay phân trang |
| Tải hết về client rồi chia trang | client tự cắt | chỉ hợp với vài chục hàng cố định; tập lớn tốn network, bộ nhớ và lộ dữ liệu thừa |

### Misconception check

**Đúng hay sai?** Không có `ORDER BY` thì SQL Server trả hàng theo primary key.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. Table là tập hợp, không có thứ tự trình bày được bảo đảm. Kết quả thường *trông như* theo khóa vì cách đọc clustered index, nhưng song song hóa, index khác hoặc plan khác có thể đổi thứ tự bất kỳ lúc nào.

</details>

**Đúng hay sai?** `WHERE OrderedAt BETWEEN '2026-03-01' AND '2026-03-31'` lấy mọi đơn của tháng 3.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. Với `datetime2`, cận trên là `2026-03-31 00:00:00`; lab cho 2 thay vì 3. Dùng `>= '2026-03-01' AND < '2026-04-01'`.

</details>

**Đúng hay sai?** Có `ORDER BY Price DESC` là đủ để phân trang ổn định.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. Hai bàn phím cùng 1 200 000 là “hòa”; thứ tự giữa chúng không được bảo đảm, và nếu chúng nằm ở ranh giới trang thì một cái có thể xuất hiện hai lần hoặc không lần nào. Thêm tiebreaker duy nhất: `Price DESC, ProductId ASC`.

</details>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** `WHERE` nhiều điều kiện có ngoặc, `IN`, `LIKE`, `ORDER BY` nhiều column có tiebreaker, `OFFSET/FETCH`.
- **Working Developer — dùng khi làm việc:** khoảng thời gian nửa mở, escape wildcard, keyset pagination, ánh xạ query string API thành parameter, giới hạn page size.
- **Deep Dive — có thể quay lại sau:** thứ tự xử lý logic, collation, chi phí `OFFSET` sâu và index cho keyset.

Bài trước: [CRUD: SELECT, INSERT, UPDATE, DELETE](./04-crud-select-insert-update-delete.md). Liên hệ: [Big-O thời gian và bộ nhớ](../07-cau-truc-du-lieu-giai-thuat/01-big-o-thoi-gian-va-bo-nho.md) — offset sâu tốn tỉ lệ với số hàng bỏ qua; `Skip/Take` của LINQ được EF Core dịch thành chính `OFFSET/FETCH` ([ordering và partitioning](../09-linq-va-ef-core/03-ordering-partitioning-va-distinct.md)).

### Từ query string tới `WHERE`

```text
search=keyboard     → @Search      → Name LIKE N'%' + escaped(@Search) + N'%'
minPrice / maxPrice → @MinPrice…   → Price >= @MinPrice AND Price <= @MaxPrice
sort=price-desc     → whitelist    → ORDER BY Price DESC, ProductId ASC
page / pageSize     → @Page…       → OFFSET … FETCH …, pageSize bị chặn trên (ví dụ ≤ 100)
```

Giá trị người dùng luôn đi qua **parameter**, không bao giờ ghép thẳng vào chuỗi SQL (bài [23](./23-bao-mat-phan-quyen-va-sql-injection.md)). Riêng `sort` không parameter hóa được tên column, nên map từ một danh sách cho phép cố định.

### Đào sâu (có thể quay lại sau)

- **Tổng số trang:** UI “trang 2/17” cần thêm một `COUNT(*)` với cùng `WHERE` — một query nữa, có thể đắt hơn chính trang dữ liệu. Feed keyset thường chỉ trả “còn nữa hay không” bằng cách lấy `pageSize + 1` hàng.
- **Literal thời gian:** SQL Server không nhận `'2026-03-01T09:00'` (thiếu giây) — lỗi `241` khi chuyển sang `datetime2` hoặc `datetime`. Dùng đủ `'2026-03-01T09:00:00'` hoặc truyền parameter kiểu thời gian từ ứng dụng.
- **Keyset nhiều column:** `(A DESC, B ASC)` → `A < @A OR (A = @A AND B > @B)`. Index `(A DESC, B ASC)` khớp chiều sort giúp engine đọc liên tục.

## 6. Lỗi thường gặp

### Phân trang không có `ORDER BY` hoặc `ORDER BY` không duy nhất

`OFFSET/FETCH` bắt buộc có `ORDER BY`, nhưng `ORDER BY` không duy nhất vẫn chạy và cho trang không ổn định. Luôn kết thúc bằng khóa duy nhất.

### Trộn `AND`/`OR` không ngoặc

Lọc “đang bán và (Mouse hoặc Hub)” mà viết thiếu ngoặc làm lọt hàng ngừng bán — đúng như lab.

### `BETWEEN` cho khoảng thời gian

Bỏ sót mọi thứ sau `00:00:00` của ngày cuối. Dùng khoảng nửa mở.

### Ghép từ khóa người dùng vào `LIKE` không escape

Từ khóa `%` hoặc `_` biến thành wildcard và trả kết quả sai. Escape `[`, `%`, `_` (hoặc dùng `ESCAPE`) trước khi ghép.

### Ghép giá trị người dùng thành chuỗi SQL

Không chỉ sai kết quả mà còn mở đường SQL injection. Dùng parameter (bài [23](./23-bao-mat-phan-quyen-va-sql-injection.md)).

### Không giới hạn `pageSize`

`pageSize=1000000` biến API phân trang thành API “tải hết”. Chặn trên ở tầng ứng dụng.

## 7. Khi nào KHÔNG dùng

- **Không dùng `OFFSET` sâu** cho feed, infinite scroll, export toàn bộ hoặc tập hàng triệu hàng: dùng keyset.
- **Không dùng keyset** khi UI thật sự cần “nhảy tới trang 37” hoặc sort theo column người dùng chọn tự do không có khóa ổn định.
- **Không dùng `LIKE N'%từ khóa%'`** làm tìm kiếm chính trên table lớn hoặc cần tìm theo từ, dấu, độ liên quan: cân nhắc full-text search hoặc search engine riêng.
- **Không dùng `BETWEEN`** cho `datetime2`/`datetimeoffset`.
- **Không phân trang ở client** khi dữ liệu không cố định và nhỏ.

Tín hiệu đang dùng sai: người dùng báo “thấy lại sản phẩm vừa xem” khi cuộn, hoặc thời gian phản hồi tăng theo số trang. Phương án đơn giản hơn: keyset với tiebreaker, hoặc giới hạn số trang tối đa. Câu hỏi quyết định: người dùng cần nhảy trang tùy ý, hay chỉ cần “xem tiếp”?

## 8. Production notes & scale check

- **Index cho query phân trang:** index khớp `WHERE` + `ORDER BY` (ví dụ `(IsActive, Price DESC, ProductId)`) cho phép đọc đúng phần cần thay vì sort toàn bộ; thiết kế ở bài [18](./18-covering-filtered-composite-index.md), đo bằng execution plan ở bài [21](./21-execution-plan-va-statistics.md).
- **Page sâu:** đặt trần số trang offset (ví dụ 100) hoặc chuyển sang keyset; crawler và bot hay đi rất sâu.
- **Tổng số hàng:** cache hoặc ước lượng khi `COUNT(*)` trên tập lớn quá đắt; nhiều UI không cần số chính xác.
- **Múi giờ:** lọc “tháng 3” theo giờ Việt Nam khác theo UTC; quy đổi biên khoảng trước khi so sánh nếu lưu UTC.
- **Plan reuse:** query có parameter được tái sử dụng plan; ghép chuỗi tạo plan mới mỗi lần và làm phình plan cache.
- **Team 2–3 người:** offset có tiebreaker + `pageSize` tối đa là đủ cho hầu hết màn hình admin; chỉ thêm keyset cho feed hoặc khi đo được page sâu chậm.

## 9. Bài tập kỹ thuật

### Bài 1 — Lọc cơ bản

Lấy sản phẩm đang bán có giá dưới 1 000 000, sắp theo giá tăng dần.

**Gợi ý:** nhớ tiebreaker dù hiện tại chưa có giá trùng.

### Bài 2 — Sort nhiều column

Sắp theo `IsActive DESC, Price ASC, ProductId ASC` và giải thích vai trò từng column.

**Gợi ý:** hàng nào đổi chỗ nếu bỏ column cuối?

### Bài 3 — Trang 2 size 2

Viết trang 2, page size 2 bằng `OFFSET/FETCH` cho danh sách bàn phím, rồi viết lại bằng keyset.

**Gợi ý:** keyset cần giá và id của hàng cuối trang 1.

### Bài 4 — Keyset theo thời gian

Viết keyset pagination cho “sản phẩm mới nhất trước” theo `(CreatedAt DESC, ProductId DESC)`.

**Gợi ý:** cả hai column cùng chiều `DESC`, nên điều kiện “đứng sau” dùng `<` cho cả hai.

### Bài 5 — Báo cáo theo tuần

Đếm đơn trong tuần từ thứ Hai 2026-03-30 đến hết Chủ nhật, có đơn lúc 23:59:59 ngày Chủ nhật.

**Gợi ý:** cận dưới là thứ Hai 00:00:00, cận trên là thứ Hai **tuần sau**, dùng `<`.

## 10. Bài tập tích hợp liên module — Judgment

Cùng một catalog 2 triệu sản phẩm phục vụ ba màn hình: trang admin có ô “đi tới trang”, app mobile cuộn vô hạn, và chức năng xuất CSV toàn bộ. Với mỗi màn hình, chọn offset, keyset hay cách khác; ước lượng cost theo Big-O (Module 07) cho trang đầu và trang thứ 10 000, và nêu index cần có. Nếu backend dùng EF Core (Module 09), chỉ ra chỗ `Skip/Take` cần được thay.

**Tiêu chí:** gắn lựa chọn với nhu cầu người dùng, cost ở page sâu, độ ổn định khi dữ liệu đổi và index cần thiết; được chọn khác nhau cho ba màn hình.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Viết lại `A AND B OR C AND D` với ngoặc tường minh theo đúng precedence.
2. Vì sao trang 2 có thể lặp hàng của trang 1 dù `ORDER BY` có tiebreaker?
3. Viết điều kiện keyset cho sort `(Score DESC, UserId ASC)`.
4. Đếm đơn của ngày 2026-02-28 bằng khoảng nửa mở.
5. Nêu hai rủi ro khi ghép từ khóa người dùng thẳng vào `LIKE`.

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi viết `WHERE` nhiều điều kiện có ngoặc đúng ý nghĩa.
- [ ] Tôi lọc khoảng thời gian bằng khoảng nửa mở.
- [ ] Tôi escape được wildcard trong từ khóa người dùng.
- [ ] Tôi phân trang có tiebreaker và giải thích được page drift.
- [ ] Tôi chọn được offset hay keyset theo nhu cầu màn hình.

**Bài prerequisite:** [CRUD: SELECT, INSERT, UPDATE, DELETE](./04-crud-select-insert-update-delete.md)

**Bài tiếp theo:** [Hàm scalar, CASE và xử lý NULL](./06-ham-scalar-case-va-xu-ly-null.md)

**Checkpoint cụm:** [Failure Lab](./failure-labs/01-bo-loc-san-pham-tra-sai-tap-hang.md) · [Spaced Review](./reviews/review-01-nen-tang-truy-van.md)
