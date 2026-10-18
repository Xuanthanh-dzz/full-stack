# CRUD: SELECT, INSERT, UPDATE, DELETE

> **Last verified:** 2026-10-18
>
> **Baseline:** SQL Server 2025 (17.0.x) · T-SQL · sqlcmd (mssql-tools18) · Docker image `mcr.microsoft.com/mssql/server:2025-latest`
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** SQL Server major/CU đổi hành vi `OUTPUT`, identity hoặc `TRUNCATE`, đổi image hoặc sqlcmd, đổi lab/schema, CI `verify-module-08` fail

## TL;DR

- CRUD là bốn câu lệnh `INSERT`, `SELECT`, `UPDATE`, `DELETE`; mỗi câu làm việc trên một **tập hàng** chọn bởi `WHERE` và là all-or-nothing — một hàng sai thì cả câu bị hủy.
- Dùng `UPDATE`/`DELETE` luôn kèm `WHERE` đã được xem trước bằng `SELECT`, và `OUTPUT` để biết chính xác hàng nào đã đổi (identity mới, giá cũ/mới, bản sao trước khi xóa).
- Trade-off: hard delete gọn nhưng mất lịch sử và gãy tham chiếu; soft delete/trạng thái giữ lịch sử nhưng buộc mọi query phải lọc và làm `UNIQUE` phức tạp hơn.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- đọc dữ liệu bằng `SELECT` liệt kê column và có `ORDER BY`;
- thêm một hoặc nhiều hàng bằng một câu `INSERT` và lấy identity vừa sinh bằng `OUTPUT`;
- cập nhật và xóa có điều kiện, xem trước tập hàng trước khi chạy;
- dùng `OUTPUT ... INTO` để giữ giá trị cũ/mới cho audit;
- giải thích vì sao câu lệnh thất bại vẫn làm identity nhảy cóc, và `DELETE` khác `TRUNCATE` ở bộ đếm identity;
- chọn giữa hard delete, soft delete và chuyển trạng thái.

## 2. Bài toán mở đầu

Admin của cửa hàng cần bốn thao tác:

```text
thêm sản phẩm         → Create
xem danh sách         → Read
đổi giá               → Update
ngừng bán / xóa       → Delete
```

Ứng dụng đầu tiên viết `UPDATE dbo.Products SET Price = 790000` để đổi giá bàn phím — và quên `WHERE`. Mọi sản phẩm trong cửa hàng giờ có giá 790 000. Câu lệnh chạy thành công, không có lỗi nào. Bài này xây thói quen để lỗi đó không xảy ra, và cách biết chính xác dữ liệu đã đổi gì khi nó xảy ra.

### Trực giác 60 giây

Mỗi câu lệnh ghi giống một **lệnh kho gửi cho thủ kho**: “trong các kệ thỏa điều kiện X, làm Y”. Thủ kho không hỏi lại; điều kiện thiếu thì làm Y với toàn bộ kho. Vì vậy trước khi gửi lệnh, bạn đọc lại danh sách kệ sẽ bị đụng (`SELECT` với cùng `WHERE`), và yêu cầu thủ kho trả biên nhận ghi rõ trước/sau (`OUTPUT`). Lệnh kho cũng là trọn gói: nếu một món trong lô bị từ chối, cả lô không được nhập.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| CRUD | bốn thao tác cơ bản: tạo, đọc, sửa, xóa | `INSERT`/`SELECT`/`UPDATE`/`DELETE` |
| predicate | điều kiện trong `WHERE` chọn tập hàng | `WHERE Sku = 'KB-01'` |
| `OUTPUT` clause | trả về hàng đã bị câu lệnh đụng tới | `deleted.Price`, `inserted.Price` |
| `inserted` / `deleted` | hai bảng ảo: giá trị sau / trước khi đổi | giá cũ 750 000, giá mới 790 000 |
| identity | cột engine tự cấp số tăng dần | `ProductId` |
| hard delete / soft delete | xóa hẳn hàng / đánh dấu là không còn dùng | xóa `MS-01` / `IsActive = 0` cho `MN-01` |

### Ví dụ nhỏ — tính tay trước

Table `Products` rỗng, `ProductId` là identity bắt đầu từ 1. Lần lượt:

```text
(a) INSERT 3 sản phẩm hợp lệ trong một câu
(b) INSERT 2 sản phẩm trong một câu, sản phẩm thứ hai giá -1 (vi phạm CHECK)
(c) INSERT 1 sản phẩm hợp lệ
```

Dự đoán: sau (b) table có mấy hàng? Sản phẩm ở (c) nhận `ProductId` bao nhiêu?

Đáp án để đối chiếu: sau (b) vẫn 3 hàng — sản phẩm hợp lệ trong câu (b) cũng không được ghi. Sản phẩm ở (c) **không** nhận 4 mà nhận 6 trong lab: câu (b) đã lấy số 4 và 5 rồi bị hủy, identity không trả lại số đã cấp.

## 3. Lời giải chạy được

Dùng SQL Server 2025 đã dựng ở [bài 01](./01-mo-hinh-quan-he-va-cai-dat-sql-server.md). Lưu script thành `lab04.sql` và chạy `sqlcmd ... -C -b -i /tmp/lab04.sql` như các bài trước:

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_04') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_04
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_04;
END;
GO

CREATE DATABASE CommerceLab08_04;
GO
USE CommerceLab08_04;
GO

CREATE TABLE dbo.Products
(
    ProductId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Sku varchar(40) NOT NULL
        CONSTRAINT UQ_Products_Sku UNIQUE,
    Name nvarchar(160) NOT NULL,
    Price decimal(19,4) NOT NULL
        CONSTRAINT CK_Products_Price CHECK (Price >= 0),
    IsActive bit NOT NULL
        CONSTRAINT DF_Products_IsActive DEFAULT 1
);

CREATE TABLE dbo.DeletedProducts
(
    ProductId int NOT NULL
        CONSTRAINT PK_DeletedProducts PRIMARY KEY,
    Sku varchar(40) NOT NULL,
    Name nvarchar(160) NOT NULL,
    Price decimal(19,4) NOT NULL
);
GO

-- 1) CREATE: một câu INSERT nhiều hàng; OUTPUT trả identity vừa sinh.
INSERT INTO dbo.Products (Sku, Name, Price)
OUTPUT inserted.ProductId, inserted.Sku
VALUES
    ('KB-01', N'Bàn phím', 750000),
    ('MS-01', N'Chuột', 450000),
    ('MN-01', N'Màn hình', 5200000);
GO

-- 2) READ: liệt kê column cần dùng, có ORDER BY.
SELECT
    ProductId,
    Sku,
    Name,
    Price,
    IsActive
FROM dbo.Products
ORDER BY ProductId;
GO

-- 3) UPDATE an toàn: xem trước tập hàng bằng đúng WHERE sẽ dùng.
SELECT COUNT(*) AS RowsMatched
FROM dbo.Products
WHERE Sku = 'KB-01';

UPDATE dbo.Products
SET Price = 790000
OUTPUT
    deleted.Price AS OldPrice,
    inserted.Price AS NewPrice
WHERE Sku = 'KB-01';
GO

-- 4) Ngừng bán bằng trạng thái thay vì xóa.
UPDATE dbo.Products
SET IsActive = 0
OUTPUT
    inserted.Sku,
    deleted.IsActive AS OldIsActive,
    inserted.IsActive AS NewIsActive
WHERE Sku = 'MN-01';
GO

-- 5) DELETE có điều kiện; OUTPUT INTO giữ bản sao để audit.
DELETE FROM dbo.Products
OUTPUT
    deleted.ProductId,
    deleted.Sku,
    deleted.Name,
    deleted.Price
INTO dbo.DeletedProducts (ProductId, Sku, Name, Price)
WHERE Sku = 'MS-01';
GO

-- 6) Một câu lệnh là all-or-nothing: một hàng sai, cả câu bị hủy.
BEGIN TRY
    INSERT INTO dbo.Products (Sku, Name, Price)
    VALUES
        ('HP-01', N'Tai nghe', 990000),
        ('CB-01', N'Cáp giá âm', -1);
END TRY
BEGIN CATCH
    SELECT
        ERROR_NUMBER() AS ErrorNumber,
        (SELECT COUNT(*) FROM dbo.Products WHERE Sku = 'HP-01') AS HeadphoneRows;
END CATCH;

-- Identity đã bị câu lệnh thất bại tiêu thụ: ProductId nhảy cóc.
INSERT INTO dbo.Products (Sku, Name, Price)
OUTPUT inserted.ProductId, inserted.Sku
VALUES ('HP-01', N'Tai nghe', 990000);
GO

-- 7) DELETE giữ bộ đếm identity; TRUNCATE (cho table staging) đặt lại.
CREATE TABLE dbo.ImportStaging
(
    RowId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_ImportStaging PRIMARY KEY,
    Sku varchar(40) NOT NULL
);

INSERT INTO dbo.ImportStaging (Sku) VALUES ('A'), ('B');

DELETE FROM dbo.ImportStaging
WHERE RowId >= 1;

INSERT INTO dbo.ImportStaging (Sku)
OUTPUT N'sau DELETE' AS AfterStatement, inserted.RowId
VALUES ('C');

TRUNCATE TABLE dbo.ImportStaging;

INSERT INTO dbo.ImportStaging (Sku)
OUTPUT N'sau TRUNCATE' AS AfterStatement, inserted.RowId
VALUES ('D');
GO

-- 8) Trạng thái cuối.
SELECT
    ProductId,
    Sku,
    Name,
    Price,
    IsActive
FROM dbo.Products
ORDER BY ProductId;

SELECT
    ProductId,
    Sku,
    Name,
    Price
FROM dbo.DeletedProducts;
GO
```

Output (SQL Server 2025, đã lược dòng thông báo):

```text
ProductId | Sku
----------+------
1         | KB-01
2         | MS-01
3         | MN-01

ProductId | Sku   | Name     | Price        | IsActive
----------+-------+----------+--------------+---------
1         | KB-01 | Bàn phím | 750000.0000  | 1
2         | MS-01 | Chuột    | 450000.0000  | 1
3         | MN-01 | Màn hình | 5200000.0000 | 1

RowsMatched
-----------
1

OldPrice    | NewPrice
------------+------------
750000.0000 | 790000.0000

Sku   | OldIsActive | NewIsActive
------+-------------+------------
MN-01 | 1           | 0

ErrorNumber | HeadphoneRows
------------+--------------
547         | 0

ProductId | Sku
----------+------
6         | HP-01

AfterStatement | RowId
---------------+------
sau DELETE     | 3

AfterStatement | RowId
---------------+------
sau TRUNCATE   | 1

ProductId | Sku   | Name     | Price        | IsActive
----------+-------+----------+--------------+---------
1         | KB-01 | Bàn phím | 790000.0000  | 1
3         | MN-01 | Màn hình | 5200000.0000 | 0
6         | HP-01 | Tai nghe | 990000.0000  | 1

ProductId | Sku   | Name  | Price
----------+-------+-------+------------
2         | MS-01 | Chuột | 450000.0000
```

### Walkthrough — execution / state / cost

1. **`INSERT` ba hàng:** engine cấp identity 1, 2, 3, kiểm tra `UNIQUE`/`CHECK`, áp `DEFAULT IsActive = 1`; `OUTPUT inserted.ProductId` trả đúng số vừa cấp — không cần truy vấn lại.
2. **`SELECT`:** đọc ba hàng theo `ORDER BY ProductId`. Không có `ORDER BY`, thứ tự hàng không được bảo đảm.
3. **Xem trước rồi `UPDATE`:** `RowsMatched = 1` xác nhận `WHERE` chỉ chọn bàn phím. `UPDATE` đọc giá cũ vào `deleted`, ghi giá mới vào `inserted`; `OUTPUT` cho thấy 750 000 → 790 000.
4. **Ngừng bán:** màn hình vẫn nằm trong table với `IsActive = 0`; đơn hàng cũ trỏ tới `ProductId = 3` vẫn hợp lệ.
5. **`DELETE ... OUTPUT INTO`:** hàng chuột bị xóa khỏi `Products`, và cùng câu lệnh đó chép nó vào `DeletedProducts` — không có khoảnh khắc nào dữ liệu bị mất mà không có bản sao.
6. **`INSERT` hai hàng, một hàng sai:** `CK_Products_Price` từ chối giá `-1` → lỗi `547`, cả câu bị hủy nên `HeadphoneRows = 0`. Nhưng identity 4 và 5 đã được cấp và không được trả lại; tai nghe nhận `ProductId = 6`.
7. **`DELETE` vs `TRUNCATE`:** sau `DELETE` toàn bộ staging, hàng mới nhận `RowId = 3` (bộ đếm giữ nguyên). `TRUNCATE` giải phóng toàn bộ page và đặt lại bộ đếm → `RowId = 1`.
8. **Cost:** `INSERT` một câu nhiều hàng là một lần đi qua network và một lần kiểm tra; `UPDATE`/`DELETE` theo `WHERE Sku = ...` dùng index của `UQ_Products_Sku` để tìm hàng thay vì quét cả table. `DELETE` ghi log từng hàng; `TRUNCATE` chỉ ghi log việc giải phóng page nên nhanh hơn nhiều với table lớn.

### Mini-check

Nếu bước 3 quên `WHERE` thì `RowsMatched` bằng bao nhiêu, `OUTPUT` trả mấy hàng, và bạn dùng output đó để khôi phục giá như thế nào?

## 4. Cơ chế hoạt động

### Mỗi câu lệnh làm việc trên một tập hàng

SQL không “lặp từng hàng” như vòng `for` trong C#; bạn mô tả **tập hàng** bằng predicate và thao tác áp cho cả tập. Cùng một predicate dùng được cho `SELECT`, `UPDATE`, `DELETE` — đó là lý do thói quen “`SELECT` trước với đúng `WHERE` sẽ dùng” có giá trị: tập hàng bạn nhìn thấy chính là tập hàng sẽ bị đổi (nếu không ai ghi xen giữa — bài [19](./19-transaction-va-acid.md)).

### `OUTPUT`, `inserted` và `deleted`

```text
INSERT  → inserted  = hàng mới
UPDATE  → deleted   = giá trị trước, inserted = giá trị sau
DELETE  → deleted   = hàng vừa xóa
```

`OUTPUT` trả về client như một result set; `OUTPUT ... INTO` ghi vào table khác trong **cùng** câu lệnh, nên audit và dữ liệu chính không thể lệch nhau. Dùng cho: lấy identity vừa sinh, ghi lịch sử giá, giữ bản sao trước khi xóa, debug batch.

### Câu lệnh là all-or-nothing

Mỗi câu `INSERT`/`UPDATE`/`DELETE` là atomic: hoặc mọi hàng trong tập được ghi, hoặc không hàng nào. Nhưng **nhiều** câu lệnh liên tiếp thì không: câu 1 thành công, câu 2 lỗi → câu 1 vẫn ở lại. Muốn “trừ kho + tạo đơn” cùng thành công hoặc cùng hủy, cần transaction (bài [19](./19-transaction-va-acid.md)).

### Identity không phải bộ đếm liên tục

Identity cấp số trước khi kiểm tra constraint và không bao giờ trả lại số đã cấp, kể cả khi câu lệnh hoặc transaction bị hủy. Khoảng trống trong `ProductId` là bình thường; đừng dùng identity làm số hóa đơn liên tục theo luật kế toán, và đừng dựa vào `MAX(ProductId) + 1`.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Hard delete (`DELETE`) | hàng biến mất khỏi table | gọn, query đơn giản; không dùng cho đơn hàng, thanh toán, dữ liệu cần audit hoặc đang được foreign key trỏ tới |
| Soft delete (`IsDeleted = 1`) | hàng vẫn còn, coi như đã xóa | giữ lịch sử, khôi phục được; mọi query phải lọc, `UNIQUE` phải thành filtered index, table phình dần |
| Chuyển trạng thái (`IsActive = 0`, `Status = 'Discontinued'`) | hàng là dữ liệu sống với vòng đời có tên | rõ nghĩa nghiệp vụ nhất; dùng khi “ngừng bán” là một bước thật của quy trình |
| `TRUNCATE TABLE` | xóa toàn bộ hàng, đặt lại identity | nhanh cho table staging/tạm; không dùng khi table bị foreign key trỏ tới hoặc cần `WHERE` |

### Misconception check

**Đúng hay sai?** Một câu `INSERT` 100 hàng mà hàng thứ 100 vi phạm `CHECK` thì 99 hàng đầu vẫn được ghi.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. Câu lệnh là atomic: lab cho `HeadphoneRows = 0` dù tai nghe là hàng hợp lệ đứng trước hàng giá âm. Điều ngược lại mới đúng với **nhiều câu lệnh** riêng lẻ không có transaction.

</details>

**Đúng hay sai?** `ProductId` lớn nhất cộng 1 chính là id của sản phẩm tiếp theo.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. Câu `INSERT` thất bại đã tiêu thụ số 4 và 5, nên sản phẩm tiếp theo nhận 6. Ngoài ra, hai session cùng tính `MAX + 1` sẽ ra cùng một số. Lấy id bằng `OUTPUT inserted.ProductId` hoặc `SCOPE_IDENTITY()`.

</details>

**Đúng hay sai?** `DELETE` không có `WHERE` và `TRUNCATE` cho cùng kết quả.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. Cả hai làm table rỗng, nhưng sau `DELETE` hàng mới nhận `RowId = 3`, sau `TRUNCATE` nhận `RowId = 1`. `TRUNCATE` còn bị chặn nếu table được foreign key trỏ tới và cần quyền cao hơn.

</details>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** viết `SELECT` liệt kê column, `INSERT` có danh sách column, `UPDATE`/`DELETE` có `WHERE`; xem trước tập hàng bằng `SELECT`.
- **Working Developer — dùng khi làm việc:** `OUTPUT`/`OUTPUT INTO`, lấy identity đúng cách, soft delete vs trạng thái, câu lệnh atomic vs nhiều câu lệnh.
- **Deep Dive — có thể quay lại sau:** identity gap, `DELETE` vs `TRUNCATE` (log, lock, quyền), `INSERT ... SELECT` và `MERGE`.

Bài trước: [Kiểu dữ liệu và NULL](./03-kieu-du-lieu-va-null.md). Liên hệ: EF Core sinh chính các câu lệnh này từ change tracking — xem [CRUD, change tracking và unit of work](../09-linq-va-ef-core/14-crud-change-tracking-va-unit-of-work.md) sau khi xong Module 08.

### Luôn liệt kê column

```sql
INSERT INTO dbo.Products (Sku, Name, Price)
VALUES ('KB-02', N'Bàn phím không dây', 890000);
```

Không dựa vào thứ tự column vật lý: ai đó thêm column vào giữa table là `INSERT INTO dbo.Products VALUES (...)` ghi nhầm cột hoặc lỗi. Tương tự, `SELECT` chỉ lấy column cần dùng thay vì `SELECT *`, để thêm column mới không âm thầm đổi contract của query.

### CRUD SQL và HTTP

```text
INSERT ↔ POST      SELECT ↔ GET      UPDATE ↔ PUT/PATCH      DELETE ↔ DELETE
```

Đây là tương đồng về ý định, không phải mapping một-một: `DELETE /products/3` trong API thường nên thành `UPDATE ... SET IsActive = 0`, còn một `POST /orders` có thể chạy nhiều câu `INSERT` trong một transaction.

### Đào sâu (có thể quay lại sau)

- **`INSERT ... SELECT`:** chép một tập hàng từ query vào table — ví dụ khôi phục từ `DeletedProducts`. Hàng khôi phục nhận identity **mới**, nên foreign key cũ trỏ tới id cũ không tự nối lại; muốn giữ id phải bật `SET IDENTITY_INSERT`, việc chỉ nên làm trong script migration có kiểm soát.
- **`TRUNCATE`:** ghi log ở mức page thay vì từng hàng, cần quyền `ALTER` trên table, không chạy được khi có foreign key trỏ tới.
- **`MERGE`:** gộp insert/update/delete theo điều kiện khớp; cú pháp mạnh nhưng có nhiều bẫy concurrency — trong module này ưu tiên các câu lệnh tách bạch.

## 6. Lỗi thường gặp

### `UPDATE`/`DELETE` không có `WHERE`

Câu lệnh chạy thành công và đổi toàn bộ table. Phòng tránh: viết `SELECT` với đúng `WHERE` trước, kiểm tra số hàng, rồi mới đổi `SELECT` thành `UPDATE`/`DELETE`; với thao tác production, bọc trong transaction và chỉ commit khi số hàng khớp kỳ vọng (bài [19](./19-transaction-va-acid.md)).

### `WHERE` đúng cú pháp nhưng sai tập hàng

`WHERE Name LIKE N'%phím%'` có thể bắt cả “Bàn phím” lẫn “Kê phím”. Lọc theo khóa (`Sku`, `ProductId`) khi đổi một hàng cụ thể.

### `INSERT` không liệt kê column và `SELECT *`

Phụ thuộc thứ tự column vật lý và kéo column không cần; schema đổi là code gãy hoặc chậm đi mà không ai biết.

### Hard delete dữ liệu lịch sử

Xóa sản phẩm đã có trong đơn hàng bị foreign key chặn (bài [02](./02-thiet-ke-schema-table-key-constraint.md)); nếu không có foreign key, báo cáo doanh thu cũ mất tên sản phẩm. Dùng trạng thái hoặc soft delete.

### Lấy identity bằng `MAX(Id)` sau khi insert

Sai khi có session khác insert cùng lúc. Dùng `OUTPUT inserted.Id` hoặc `SCOPE_IDENTITY()`.

### Nhiều câu lệnh phụ thuộc nhau nhưng không có transaction

Câu thứ hai lỗi để lại dữ liệu nửa vời. Transaction học ở bài [19](./19-transaction-va-acid.md).

## 7. Khi nào KHÔNG dùng

- **Không hard delete** đơn hàng, thanh toán, hóa đơn và mọi hàng đang được tham chiếu: dùng trạng thái.
- **Không soft delete theo phản xạ** cho dữ liệu tạm, log đã hết hạn, hoặc dữ liệu cá nhân mà luật yêu cầu xóa thật.
- **Không `TRUNCATE`** table nghiệp vụ hoặc table có foreign key trỏ tới; chỉ dùng cho staging/tạm.
- **Không `UPDATE` từng hàng trong vòng lặp ứng dụng** khi một câu lệnh set-based làm được: N câu là N lần đi qua network và N lần ghi log riêng.
- **Không dùng `OUTPUT` để trả dữ liệu cho UI** khi chỉ cần biết “thành công”: trả đúng thứ cần, không kéo cả hàng.

Tín hiệu đang dùng sai: thấy `IsDeleted = 0` lặp lại ở mọi query nhưng chưa ai từng khôi phục một hàng nào. Phương án đơn giản hơn: trạng thái có tên cho dữ liệu sống, hard delete cho dữ liệu tạm. Câu hỏi quyết định: sau khi “xóa”, có ai còn cần đọc hàng này — báo cáo, audit, foreign key — không?

## 8. Production notes & scale check

- **Thao tác tay trên production:** `BEGIN TRANSACTION` → câu lệnh → kiểm tra số hàng và `OUTPUT` → `COMMIT` hoặc `ROLLBACK`; có người thứ hai đọc script trước khi chạy.
- **Xóa/cập nhật hàng triệu dòng:** làm theo lô (ví dụ `DELETE TOP (5000) ... WHERE ...` lặp lại) để transaction log và lock không phình; một câu khổng lồ có thể khóa table và làm đầy log.
- **Audit:** `OUTPUT INTO` một history table (bài [16](./16-denormalization-va-du-lieu-lich-su.md)) thay vì trigger tự viết khi chỉ cần lưu trước/sau; audit thật còn cần ai đổi và lúc nào.
- **Soft delete và `UNIQUE`:** `Sku` đã xóa mềm vẫn chiếm chỗ trong `UNIQUE`; dùng filtered unique index `WHERE IsDeleted = 0` (bài [18](./18-covering-filtered-composite-index.md)).
- **Team 2–3 người:** quy ước “mọi `UPDATE`/`DELETE` tay phải có `SELECT` xem trước và transaction” rẻ hơn nhiều so với một lần khôi phục từ backup.

## 9. Bài tập kỹ thuật

### Bài 1 — Nhập lô sản phẩm

Thêm 5 sản phẩm bằng một câu `INSERT` và lấy về `ProductId` của cả 5.

**Gợi ý:** `OUTPUT inserted.ProductId, inserted.Sku` trả về một hàng cho mỗi sản phẩm.

### Bài 2 — Tăng giá có kiểm soát

Tăng 5% giá cho mọi sản phẩm đang bán (`IsActive = 1`), xem trước số hàng bị ảnh hưởng và in giá cũ/mới.

**Gợi ý:** `SET Price = Price * 1.05` dùng giá trị cũ của chính hàng đó; chạy `SELECT COUNT(*)` với cùng `WHERE` trước.

### Bài 3 — Lịch sử giá

Tạo `dbo.PriceHistory (ProductId, OldPrice, NewPrice)` và ghi lịch sử cho mọi lần đổi giá ngay trong câu `UPDATE`.

**Gợi ý:** `OUTPUT deleted.ProductId, deleted.Price, inserted.Price INTO dbo.PriceHistory (...)`.

### Bài 4 — Khôi phục sản phẩm đã xóa

Khôi phục `MS-01` từ `DeletedProducts` bằng `INSERT ... SELECT`. `ProductId` mới là bao nhiêu và điều đó ảnh hưởng gì nếu có đơn hàng cũ trỏ tới id 2?

**Gợi ý:** so sánh `ProductId` trước và sau khôi phục; đọc về `IDENTITY_INSERT` nhưng đừng bật nó trong bài tập.

### Bài 5 — Checklist trước `DELETE` production

Viết checklist 5–7 bước trước khi chạy một câu `DELETE` trên production.

**Gợi ý:** bao gồm xem trước tập hàng, backup/bản sao, transaction, số hàng kỳ vọng, người review và kế hoạch rollback.

## 10. Bài tập tích hợp liên module — Judgment

Một màn hình admin có nút “Xóa sản phẩm”. Đội đề xuất ba cách: `DELETE` thật, `IsDeleted = 1` kèm global query filter của EF Core (Module 09), hoặc `Status = 'Discontinued'`. Với sản phẩm đã có trong đơn hàng và sản phẩm nhập nhầm chưa bán lần nào, chọn cách xử lý cho từng trường hợp và giải thích tác động lên foreign key, báo cáo doanh thu, `UNIQUE (Sku)` và độ phức tạp của mọi query khác.

**Tiêu chí:** nêu rõ ai còn đọc hàng sau khi “xóa”, chi phí lên mọi query và cách khôi phục; được phép chọn khác nhau cho hai trường hợp, không chấm theo số cơ chế được dùng.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Viết chuỗi thao tác an toàn để đổi email của một khách hàng trên production.
2. Trong `UPDATE`, `deleted` và `inserted` chứa gì? Cho ví dụ dùng cả hai.
3. Giải thích vì sao id của hàng mới có thể nhảy từ 3 lên 6.
4. Khi nào `TRUNCATE` hợp lý và khi nào nó bị chặn?
5. So sánh soft delete và chuyển trạng thái cho một tài khoản người dùng.

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi viết được bốn câu CRUD có danh sách column và `WHERE` rõ ràng.
- [ ] Tôi xem trước tập hàng trước mọi `UPDATE`/`DELETE`.
- [ ] Tôi dùng được `OUTPUT` và `OUTPUT INTO` để lấy identity và giữ giá trị cũ/mới.
- [ ] Tôi giải thích được câu lệnh atomic, identity gap và `DELETE` vs `TRUNCATE`.
- [ ] Tôi chọn được giữa hard delete, soft delete và chuyển trạng thái.

**Bài prerequisite:** [Kiểu dữ liệu và NULL](./03-kieu-du-lieu-va-null.md)

**Bài tiếp theo:** [Filter, sort và pagination](./05-filter-sort-va-pagination.md)
