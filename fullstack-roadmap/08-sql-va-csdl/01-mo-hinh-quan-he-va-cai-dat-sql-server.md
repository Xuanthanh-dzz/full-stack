# Mô hình quan hệ và cài đặt SQL Server

> **Last verified:** 2026-10-18
>
> **Baseline:** SQL Server 2025 (17.0.x) · T-SQL · sqlcmd (mssql-tools18) · Docker image `mcr.microsoft.com/mssql/server:2025-latest`
>
> **Review cycle:** 180 days
>
> **Re-verify triggers:** SQL Server major/CU đổi hành vi, đổi image hoặc sqlcmd, đổi lab/schema, CI `verify-module-08` fail

## TL;DR

- Relational database lưu dữ liệu thành table gồm row và column, định danh bằng key, và để engine bảo vệ kiểu, ràng buộc và truy cập đồng thời.
- Dùng khi dữ liệu phải sống qua nhiều lần chạy, nhiều client cùng đọc/ghi và cần truy vấn hoặc tổng hợp linh hoạt.
- Trade-off: thêm một server phải cài, sao lưu, bảo mật; schema phải thiết kế trước và mỗi truy vấn đi qua mạng.

## 1. Mục tiêu

Học xong bài này, bạn có thể:

- chỉ ra database, table, row, column, primary key và relationship trên một ví dụ cụ thể;
- nêu bốn vấn đề của việc giữ dữ liệu trong `List<T>`/`Dictionary` hoặc file mà database giải quyết;
- chạy SQL Server 2025 bằng Docker và kết nối bằng `sqlcmd`;
- viết một script tạo database, table, insert và query chạy lại được nhiều lần;
- giải thích câu lệnh chạy ở đâu, state nằm ở đâu và cost nằm ở đâu;
- xếp một câu lệnh vào nhóm DDL, DML hoặc DCL.

## 2. Bài toán mở đầu

Suốt Module 04–07, dữ liệu sống trong `List<T>` và `Dictionary<TKey, TValue>`. Một cửa hàng thật cần lưu khách hàng, sản phẩm, đơn hàng và chi tiết đơn hàng. Giữ chúng trong bộ nhớ của chương trình gặp bốn vấn đề:

- **Mất khi tắt chương trình:** RAM của process bị giải phóng, đơn hàng biến mất.
- **Nhiều process không thấy nhau:** hai máy chủ web nhận hai đơn cùng lúc, mỗi máy chỉ thấy danh sách của mình.
- **Truy vấn linh hoạt tốn công:** “khách đăng ký tháng này, có đơn trên 1 triệu, sắp theo tên” phải viết vòng lặp riêng cho từng câu hỏi.
- **Không có gì chặn dữ liệu sai:** email trùng hoặc đơn hàng trỏ tới khách không tồn tại vẫn lọt vào.

Ghi ra một file text giải quyết được vấn đề đầu nhưng sinh vấn đề mới: khách bị lặp, đổi tên sản phẩm phải sửa nhiều chỗ, hai người ghi cùng lúc dễ đè nhau. Relational database tách dữ liệu thành các table, nối chúng bằng key và giao toàn bộ việc lưu, kiểm tra, đọc cho một engine dùng chung.

### Trực giác 60 giây

Hãy hình dung database như một kho hồ sơ có thủ kho. Bạn không tự lục kho; bạn đưa phiếu yêu cầu (câu SQL), thủ kho kiểm tra phiếu, lấy hồ sơ và trả lại bản sao (result set). Thủ kho từ chối hồ sơ sai mẫu trước khi cất, và nhiều người có thể cùng gửi phiếu. Dữ liệu đi theo đường: ứng dụng (client) → câu SQL qua mạng (cổng 1433) → engine đọc/ghi file trên đĩa của server → các hàng kết quả quay về client. Không có database, mỗi ứng dụng phải tự viết lại việc lưu file, khóa ghi, kiểm tra và tìm kiếm.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| database | ranh giới lưu trữ chứa table, index, constraint và log | `CommerceLab08_01` |
| table | tập các hàng cùng cấu trúc, mô tả một loại thực thể | `dbo.Customers` |
| row (hàng) | một bản ghi | khách `Nguyễn An` |
| column (cột) | một thuộc tính có kiểu dữ liệu cố định | `Email varchar(320)` |
| primary key | cột định danh duy nhất mỗi hàng, không được NULL | `CustomerId` |
| schema | không gian tên gom các object | `dbo` |
| T-SQL | phương ngữ SQL của SQL Server | mọi script trong bài |
| result set | các hàng engine trả về cho client | output của `SELECT` |

### Ví dụ nhỏ — tính tay trước

Hai danh sách C#:

```text
customers: (1, An), (2, Bình)
orders:    (10 → customer 1), (11 → customer 1), (12 → customer 3)
```

Tự trả lời trước khi đọc tiếp:

1. An có mấy đơn? — 2 (đơn 10 và 11). Trong C# bạn phải viết vòng lặp đếm.
2. Đơn 12 thuộc khách nào? — Không ai: customer 3 không tồn tại. `List<T>` vẫn nhận đơn mồ côi này.

Trong database, đơn 12 bị từ chối ngay khi ghi nhờ khóa ngoại (bài [02](./02-thiet-ke-schema-table-key-constraint.md)), và câu “An có mấy đơn” chỉ là một câu `SELECT COUNT(*)`.

## 3. Lời giải chạy được

Chạy SQL Server 2025 trên máy bằng Docker. Mật khẩu dưới đây **chỉ dành cho lab**:

```bash
docker pull mcr.microsoft.com/mssql/server:2025-latest

docker run -e "ACCEPT_EULA=Y" -e "MSSQL_SA_PASSWORD=SqlLab!2026Strong" \
  -p 1433:1433 --name sql2025 --hostname sql2025 \
  -d mcr.microsoft.com/mssql/server:2025-latest

docker logs sql2025
```

Kết nối bằng `sqlcmd` có sẵn trong container. Cờ `-C` tin chứng chỉ tự ký của container lab:

```bash
docker exec -it sql2025 /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "SqlLab!2026Strong" -C
```

Lưu script sau thành `lab01.sql`, chép vào container rồi chạy bằng `docker cp lab01.sql sql2025:/tmp/lab01.sql` và `docker exec sql2025 /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "SqlLab!2026Strong" -C -b -i /tmp/lab01.sql`:

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_01') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_01
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_01;
END;
GO

CREATE DATABASE CommerceLab08_01;
GO

USE CommerceLab08_01;
GO

CREATE TABLE dbo.Customers
(
    CustomerId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Customers PRIMARY KEY,
    FullName nvarchar(120) NOT NULL,
    Email varchar(320) NOT NULL
);
GO

INSERT INTO dbo.Customers (FullName, Email)
VALUES
    (N'Nguyễn An', 'an@example.com'),
    (N'Trần Bình', 'binh@example.com');
GO

-- 1) Dữ liệu: engine trả result set theo thứ tự ORDER BY yêu cầu.
SELECT
    CustomerId,
    FullName,
    Email
FROM dbo.Customers
ORDER BY CustomerId;
GO

-- 2) Schema cũng là dữ liệu: engine lưu định nghĩa table trong system catalog.
SELECT
    c.name AS ColumnName,
    t.name AS DataType,
    c.max_length AS MaxBytes,
    c.is_nullable AS IsNullable
FROM sys.columns AS c
JOIN sys.types AS t
    ON t.user_type_id = c.user_type_id
WHERE c.object_id = OBJECT_ID(N'dbo.Customers')
ORDER BY c.column_id;
GO
```

Output (SQL Server 2025, đã lược dòng `Changed database context` và `rows affected`):

```text
CustomerId | FullName  | Email
-----------+-----------+-----------------
1          | Nguyễn An | an@example.com
2          | Trần Bình | binh@example.com

ColumnName | DataType | MaxBytes | IsNullable
-----------+----------+----------+-----------
CustomerId | int      | 4        | 0
FullName   | nvarchar | 240      | 0
Email      | varchar  | 320      | 0
```

### Walkthrough — execution / state / cost

1. **`USE master` + `IF DB_ID(...)`:** script kiểm tra database đã tồn tại chưa và xóa nếu có. Nhờ vậy script chạy lại bao nhiêu lần cũng ra cùng trạng thái ban đầu — tính chất này gọi là **idempotent**. `SINGLE_USER WITH ROLLBACK IMMEDIATE` ngắt kết nối khác trước khi xóa.
2. **`CREATE DATABASE`:** engine tạo file dữ liệu và file log bên trong container (thư mục `/var/opt/mssql/data`). State sống ở **server**, không ở `sqlcmd`.
3. **`CREATE TABLE`:** câu lệnh DDL. Định nghĩa table được ghi vào **system catalog** — chính truy vấn thứ hai đọc lại các dòng định nghĩa đó.
4. **`INSERT`:** câu lệnh DML. Engine kiểm tra từng giá trị theo kiểu và `NOT NULL`, `IDENTITY` sinh `1` rồi `2`, thay đổi được ghi vào log trước khi ghi vào trang dữ liệu.
5. **`SELECT ... ORDER BY`:** engine đọc trang dữ liệu, sắp xếp và gửi các hàng qua mạng về client. Cost nằm ở I/O đọc trang trên server và băng thông trả kết quả; với hai hàng thì gần như bằng không.
6. **`MaxBytes = 240` cho `nvarchar(120)`:** `nvarchar` lưu Unicode 2 byte mỗi ký tự, nên 120 ký tự chiếm tối đa 240 byte; `varchar(320)` chiếm tối đa 320 byte.
7. **`GO`:** không phải lệnh T-SQL; nó báo `sqlcmd` gửi khối lệnh phía trên lên server thành một batch.

### Mini-check

Nếu chạy `docker stop sql2025` rồi `docker start sql2025`, hai khách hàng còn không? Nếu chạy `docker rm -f sql2025` rồi `docker run` lại cùng lệnh thì sao? Dòng nào trong walkthrough cho bạn câu trả lời?

## 4. Cơ chế hoạt động

### Table, row, column

```text
dbo.Customers
+------------+-----------+------------------+
| CustomerId | FullName  | Email            |
+------------+-----------+------------------+
| 1          | Nguyễn An | an@example.com   |
| 2          | Trần Bình | binh@example.com |
+------------+-----------+------------------+
```

Mỗi column có kiểu dữ liệu cố định; mỗi row là một khách hàng; table là tập các row cùng cấu trúc. Thứ tự hàng **không** phải một phần của table: muốn thứ tự xác định, phải yêu cầu bằng `ORDER BY`.

### Key và relationship

`CustomerId` là **primary key**: duy nhất, không NULL và ổn định, nên phân biệt được hai khách trùng tên. Khi có bảng `Orders` chứa cột `CustomerId`, cột đó là **foreign key** trỏ về `Customers`, biểu diễn quan hệ một–nhiều:

```text
Customers (1) ───< (*) Orders
một khách hàng     nhiều đơn hàng
```

Engine sẽ từ chối đơn trỏ tới khách không tồn tại — chính đơn số 12 trong ví dụ nhỏ.

### SQL là ngôn ngữ khai báo

```sql
SELECT FullName
FROM dbo.Customers
WHERE Email = 'an@example.com';
```

Câu này mô tả **kết quả muốn có**, không mô tả cách đọc từng trang trên đĩa. **Query optimizer** của engine tự chọn cách thực hiện (execution plan, bài [21](./21-execution-plan-va-statistics.md)). Đây là khác biệt lớn nhất so với vòng lặp C#.

Câu lệnh SQL chia ba nhóm:

- **DDL** (Data Definition): `CREATE`, `ALTER`, `DROP` — định nghĩa cấu trúc.
- **DML** (Data Manipulation): `SELECT`, `INSERT`, `UPDATE`, `DELETE` — đọc và đổi dữ liệu.
- **DCL** (Data Control): `GRANT`, `REVOKE` — phân quyền (bài [23](./23-bao-mat-phan-quyen-va-sql-injection.md)).

### Client–server

```text
Client (sqlcmd / SSMS / app .NET)          Server (SQL Server engine)
┌──────────────────────────────┐  câu SQL   ┌──────────────────────────┐
│ SELECT ... FROM dbo.Customers│ ─────────▶ │ đọc trang, kiểm tra,     │
│                              │ ◀───────── │ trả result set           │
└──────────────────────────────┘  các hàng  └────────────┬─────────────┘
                                                         │
                                              file dữ liệu + log trên đĩa
```

Nhiều client nối tới cùng một engine; dữ liệu sống độc lập với vòng đời ứng dụng; engine lo đồng thời, transaction và quyền truy cập.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| `List<T>` / `Dictionary` trong RAM | dữ liệu thuộc một process, mất khi process dừng | nhanh nhất, không cài gì; hợp với dữ liệu tạm trong một lần chạy |
| File JSON/CSV | dữ liệu bền nhưng chương trình tự đọc, tự khóa, tự kiểm tra | đơn giản cho một người ghi; không hợp khi nhiều writer hoặc cần truy vấn |
| Relational database (SQL Server) | engine dùng chung lưu bền, kiểm tra constraint, xử lý đồng thời | thêm server và vận hành; đáng dùng khi dữ liệu nhiều người dùng, cần toàn vẹn và truy vấn |

### Misconception check

**Đúng hay sai?** “Relational” nghĩa là các table có quan hệ với nhau.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. *Relation* là khái niệm toán học: một tập các bộ giá trị cùng cấu trúc — tức là chính một table. Quan hệ giữa các table qua foreign key là hệ quả, không phải nguồn gốc của tên gọi.

</details>

**Đúng hay sai?** `GO` là một lệnh T-SQL nên code .NET cũng phải gửi `GO`.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. `GO` là dấu ngăn batch của `sqlcmd`/SSMS. Engine không hiểu `GO`; ứng dụng gửi từng batch riêng.

</details>

**Đúng hay sai?** `SELECT` không có `ORDER BY` luôn trả hàng theo thứ tự insert.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai. Không có `ORDER BY` thì thứ tự không được bảo đảm; nó có thể đổi khi dữ liệu, index hoặc execution plan đổi.

</details>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** table/row/column/primary key, chạy lab, đọc output.
- **Working Developer — dùng khi làm việc:** script idempotent, `sqlcmd -b`, không dùng `sa` cho ứng dụng, reset môi trường bằng Docker.
- **Deep Dive — có thể quay lại sau:** file dữ liệu và log, system catalog, collation, các edition của SQL Server.

### Từ collection sang table

| Khái niệm C# (Module 04–07) | Tương ứng trong relational database |
|---|---|
| `List<Customer>` | table `dbo.Customers` |
| một object `Customer` | một row |
| property `FullName` | column `FullName` |
| kiểu `string`, `int` | kiểu `nvarchar`, `int` |
| key của `Dictionary` | primary key (tra cứu qua index, bài [17](./17-index-btree-clustered-nonclustered.md)) |
| sống trong RAM của một process | sống bền trên đĩa, nhiều client dùng chung |

Bài trước: [Module 07 — Dự án engine tìm đường](../07-cau-truc-du-lieu-giai-thuat/19-du-an-engine-tim-duong.md). Nền collection: [List, Dictionary, HashSet, Queue và Stack](../04-csharp-co-ban/13-collection-list-dictionary-hashset-queue-stack.md).

### Chọn môi trường SQL Server

- **Developer Edition** — miễn phí cho học tập/phát triển, đủ tính năng.
- **Express/LocalDB** — nhẹ, phù hợp máy cấu hình thấp.
- **Docker** — được ưu tiên cho khóa học: dễ reset và CI dùng cùng image.

Công cụ GUI (SQL Server Management Studio, VS Code với SQL extension) tiện, nhưng mọi bài phải chạy được bằng script.

### Đào sâu (có thể quay lại sau)

- **`N'...'` và `nvarchar`:** tiền tố `N` báo literal là Unicode. Với collation mặc định `SQL_Latin1_General_CP1_CI_AS`, `'Nguyễn An'` không có `N` bị đổi thành `Nguy?n An` trước khi tới column — mất dữ liệu ngay khi ghi.
- **Phương ngữ:** `IDENTITY(1,1)` là của SQL Server; PostgreSQL dùng `GENERATED ALWAYS AS IDENTITY`. Khái niệm table/key/SQL khai báo thì giống nhau giữa các hệ quản trị.
- **Write-ahead log:** engine ghi thay đổi vào log trước dữ liệu để phục hồi được sau sự cố; bài [19](./19-transaction-va-acid.md) giải thích qua transaction.

## 6. Lỗi thường gặp

### Script không chạy lại được

Bỏ khối `IF DB_ID(...)` thì lần chạy thứ hai báo `Msg 1801: Database 'CommerceLab08_01' already exists`. Script setup nên idempotent: kiểm tra tồn tại rồi tạo, hoặc xóa có kiểm soát rồi tạo lại.

### Quên tiền tố `N` cho chuỗi tiếng Việt

`INSERT ... VALUES ('Nguyễn An', ...)` ghi `Nguy?n An` dù column là `nvarchar`. Dữ liệu hỏng không báo lỗi. Luôn viết `N'...'` cho literal Unicode.

### Kết nối `sqlcmd` thiếu `-C`

`sqlcmd` của mssql-tools18 mã hóa kết nối mặc định và từ chối chứng chỉ tự ký của container: `certificate verify failed: self-signed certificate`. `-C` chỉ dùng cho lab; production cần chứng chỉ hợp lệ.

### Dùng tài khoản `sa` trong ứng dụng

`sa` có toàn quyền trên server. Ứng dụng cần login/user riêng với quyền tối thiểu (bài [23](./23-bao-mat-phan-quyen-va-sql-injection.md)).

### Click GUI thay vì viết script

Thao tác tay trong GUI khó tái tạo trên máy khác hoặc trong CI. Project tốt dựng schema từ script hoặc migration.

## 7. Khi nào KHÔNG dùng

- **Dữ liệu chỉ sống trong một lần chạy** (kết quả tính tạm, cache cục bộ): `List<T>`/`Dictionary` đủ và nhanh hơn.
- **Cấu hình nhỏ một người đọc** (file cài đặt): file JSON/`appsettings.json` đơn giản hơn nhiều.
- **Ứng dụng cá nhân một người ghi** cần lưu bền và vài truy vấn: SQLite (database nhúng trong một file) tránh được việc vận hành server.

Tín hiệu chưa cần SQL Server: không có nhiều process ghi, không cần truy vấn ad-hoc, mất dữ liệu khi restart vẫn chấp nhận được. Cost bỏ ra gồm cài đặt, backup, bảo mật, migration và một thành phần mạng có thể hỏng. Câu hỏi quyết định: dữ liệu có phải sống qua restart, có hơn một writer, có cần truy vấn/tổng hợp linh hoạt không? Ba câu đều “không” thì chưa cần database server.

## 8. Production notes & scale check

- **Demo khác production:** lab dùng `sa`, mật khẩu ghi thẳng trong lệnh và container không gắn volume. Production dùng login quyền tối thiểu, secret nằm ngoài source code, dữ liệu trên volume/đĩa bền và có backup đã thử restore (bài [24](./24-backup-restore-va-migration-du-lieu.md)).
- **Bảo mật:** chỉ mở cổng 1433 cho mạng cần thiết; bật mã hóa kết nối bằng chứng chỉ thật thay vì `-C`.
- **Observability:** theo dõi `docker logs`/error log, dung lượng đĩa của file dữ liệu và log.
- **Team 2–3 người:** một instance SQL Server (tự host hoặc dịch vụ managed) là đủ cho hệ thống vừa; replication, sharding chỉ cần khi đo được giới hạn thật (Module 18).

## 9. Bài tập kỹ thuật

### Bài 1 — SchoolLab

Tạo database `SchoolLab` với table `dbo.Students` gồm `StudentId`, `FullName`, `Email`, insert 5 sinh viên rồi query theo `StudentId`.

**Gợi ý:** sao chép cấu trúc lab, đổi tên; giữ khối `IF DB_ID(...)` để chạy lại được.

### Bài 2 — Debug script chạy lần hai

Xóa khối `IF DB_ID(...)` khỏi lab rồi chạy hai lần. Ghi lại mã lỗi và giải thích vì sao lần đầu chạy được.

**Gợi ý:** so sánh state của server trước lần chạy thứ nhất và thứ hai.

### Bài 3 — Debug tên bị mất dấu

Một bạn viết `INSERT INTO dbo.Customers (FullName, Email) VALUES ('Lê Cường', 'cuong@example.com');` và thấy tên hiển thị sai. Tìm nguyên nhân và sửa.

**Gợi ý:** kiểu column đã đúng; hãy xem literal được gửi đi dưới dạng gì.

### Bài 4 — Vẽ mô hình

Vẽ `Customer`, `Order`, `OrderItem`, `Product` và ghi cardinality của từng quan hệ.

**Gợi ý:** hỏi “một A có bao nhiêu B, một B thuộc bao nhiêu A?” cho từng cặp.

### Bài 5 — Dữ liệu có sống sót không?

Chạy lab, `docker rm -f` container rồi dựng lại; sau đó dựng lại với `-v sql2025data:/var/opt/mssql` và lặp lại thí nghiệm.

**Gợi ý:** dữ liệu nằm trong filesystem của container trừ khi gắn volume.

## 10. Bài tập tích hợp liên module — Judgment

Dự án quản lý điểm ở Module 01 đang lưu file văn bản, chỉ một giáo viên dùng. Nhà trường muốn ba giáo viên cùng nhập điểm và hiệu trưởng xem thống kê theo lớp. Chọn giữa: giữ file, chuyển SQLite, hoặc dùng SQL Server. Bảo vệ lựa chọn bằng số writer, nhu cầu truy vấn, chi phí vận hành và điều gì sẽ khiến bạn đổi lựa chọn.

**Tiêu chí:** nêu rõ state sống ở đâu, ai ghi đồng thời, truy vấn nào cần chạy và cost vận hành; không chấm theo số công nghệ được nhắc tới.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Giải thích primary key bằng lời của bạn và vì sao nó phải ổn định.
2. Trace đường đi của một câu `SELECT` từ client tới đĩa rồi quay về.
3. Dự đoán `MaxBytes` của một column `nvarchar(50)` và giải thích.
4. Vì sao kết quả `SELECT` không có `ORDER BY` không được tin thứ tự?
5. Khi nào `Dictionary` trong RAM là lựa chọn tốt hơn một table?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy được SQL Server 2025 bằng Docker và kết nối bằng `sqlcmd`.
- [ ] Tôi viết được script tạo database/table chạy lại nhiều lần không lỗi.
- [ ] Tôi debug được lỗi `Msg 1801`, lỗi thiếu `-C` và lỗi mất dấu do thiếu `N`.
- [ ] Tôi giải thích được state nằm ở server, cost nằm ở I/O và mạng.
- [ ] Tôi đọc được định nghĩa table từ system catalog.
- [ ] Tôi chọn được giữa collection, file và database theo số writer và nhu cầu truy vấn.

**Bài prerequisite:** [Module 07 — Dự án engine tìm đường](../07-cau-truc-du-lieu-giai-thuat/19-du-an-engine-tim-duong.md)

**Bài tiếp theo:** [Thiết kế schema, table, key và constraint](./02-thiet-ke-schema-table-key-constraint.md)
