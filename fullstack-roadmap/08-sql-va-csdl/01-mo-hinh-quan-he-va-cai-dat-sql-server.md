# Mô hình quan hệ và cài đặt SQL Server

> **Last verified:** pending — chưa chạy lại gate retrofit  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Database quan hệ lưu các bảng có khóa và quy tắc liên kết.
- Dùng khi nhiều thao tác cần dữ liệu bền vững, truy vấn và ràng buộc chung.
- Một container chạy được chưa có nghĩa dữ liệu đã được backup hoặc tồn tại sau khi xóa container.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích database, table, row, column, key và relationship;
- phân biệt dữ liệu quan hệ với object trong chương trình;
- cài hoặc chạy SQL Server 2025 bằng Docker;
- kết nối bằng `sqlcmd` hoặc công cụ GUI;
- tạo database đầu tiên và chạy truy vấn kiểm tra;
- hiểu vì sao schema phải được thiết kế trước khi EF Core xuất hiện.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Sổ khách hàng đánh số từng người; sổ đơn hàng chỉ ghi số khách để tham chiếu. Đổi tên khách không cần sửa từng đơn đang dùng thông tin hiện tại. Máy chủ database giữ sổ, còn công cụ SQL gửi yêu cầu đọc/ghi.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| database | vùng dữ liệu và metadata do server quản lý | CommerceLab08_01 |
| table/row/column | bảng/bản ghi/thuộc tính có kiểu | Customers, An, Email |
| primary key | khóa duy nhất và không NULL | CustomerId |
| session | một kết nối có trạng thái riêng | database hiện tại sau USE |
| batch | nhóm lệnh client gửi một lần | GO phân cách trong sqlcmd |

### Ví dụ nhỏ — tính tay trước

Customers có (1,An),(2,Bình). Query ORDER BY CustomerId trả An rồi Bình. Bỏ ORDER BY thì hai row vẫn tồn tại nhưng thứ tự hiển thị không được cam kết.

Một cửa hàng cần lưu:

```text
Khách hàng
Sản phẩm
Đơn hàng
Chi tiết đơn hàng
```

Nếu lưu tất cả vào một file text duy nhất, dữ liệu nhanh chóng gặp vấn đề:

- khách hàng bị lặp;
- tên sản phẩm thay đổi ở nhiều chỗ;
- khó đảm bảo order item luôn thuộc một order thật;
- nhiều người ghi file cùng lúc dễ xung đột;
- tìm kiếm và tổng hợp chậm.

Relational database tách dữ liệu thành các table và nối chúng bằng key.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

SQL Server 2025 có thể chạy local bằng Docker:

```bash
docker pull mcr.microsoft.com/mssql/server:2025-latest

docker run   -e "ACCEPT_EULA=Y"   -e "MSSQL_SA_PASSWORD=SqlLab!2026Strong"   -p 1433:1433   --name sql2025   --hostname sql2025   -d mcr.microsoft.com/mssql/server:2025-latest
```

Kiểm tra log:

```bash
docker logs sql2025
```

Kết nối bằng `sqlcmd` bên trong container:

```bash
docker exec -it sql2025 /opt/mssql-tools18/bin/sqlcmd   -S localhost   -U sa   -P "SqlLab!2026Strong"   -C
```

Chạy script:

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

SELECT
    CustomerId,
    FullName,
    Email
FROM dbo.Customers
ORDER BY CustomerId;
GO
```

Output logic:

```text
1 | Nguyễn An | an@example.com
2 | Trần Bình | binh@example.com
```

### Walkthrough — execution / state / cost

1. sqlcmd chạy phía client; GO được client tách batch, không gửi như câu T-SQL.
2. USE chọn database trong session; CREATE TABLE lưu cấu trúc ở server.
3. INSERT ghi hai row và index; SELECT gửi kết quả về client để hiển thị.
4. Dữ liệu/log nằm trong file của SQL Server, buffer pages ở RAM server. Network, đọc page và duy trì index đều có cost; tắt client không xóa table.

### Mini-check

Đóng terminal sqlcmd rồi mở kết nối mới: bảng còn không, biến @x của session cũ còn không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Database

Database là boundary lưu trữ logic chứa:

- table;
- index;
- constraint;
- view;
- procedure;
- metadata;
- transaction log.

### Table

Table mô hình một tập thực thể cùng cấu trúc:

```text
Customers
+------------+-------------+------------------+
| CustomerId | FullName    | Email            |
+------------+-------------+------------------+
| 1          | Nguyễn An   | an@example.com   |
| 2          | Trần Bình   | binh@example.com |
+------------+-------------+------------------+
```

### Row và column

- row: một record;
- column: một thuộc tính;
- data type: miền giá trị được phép.

### Primary key

`CustomerId` định danh duy nhất một customer.

Primary key phải:

- unique;
- không null;
- ổn định.

### Quan hệ

Sau này:

```text
Customers
    |
    | 1
    |
    | *
Orders
```

Một customer có nhiều order.

Foreign key sẽ làm database tự kiểm tra quan hệ này.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| object C# trong RAM | thuộc process và references | mất khi process kết thúc nếu chưa lưu |
| file tự quản | ứng dụng tự định dạng và phối hợp ghi | đủ cho dữ liệu nhỏ, ít writer |
| relational database | constraints/query/concurrency chung | cần vận hành, storage và quyền truy cập |

### Misconception check

**Đúng hay sai?** GO là một câu lệnh SQL Server.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: sqlcmd/GUI xử lý GO như dấu kết thúc batch.

</details>

**Đúng hay sai?** Table luôn trả theo primary key.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chỉ ORDER BY cam kết thứ tự kết quả.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** table/key và kết nối.

- **Working Developer — dùng khi làm việc:** script tái tạo và nơi dữ liệu sống.

- **Deep Dive — có thể quay lại sau:** vận hành/backup khi có dữ liệu thật.

### SQL là declarative

Bạn thường nói:

```sql
SELECT *
FROM dbo.Customers
WHERE Email = 'an@example.com';
```

Bạn mô tả **muốn dữ liệu nào**, không viết vòng lặp để đọc từng page trên disk.

Query optimizer quyết định execution plan.

### SQL Server 2025

Trong khóa này, Module 08 dùng SQL Server 2025 cho lab.

Có ba cách học phổ biến:

- Developer Edition local;
- Express/LocalDB cho môi trường nhẹ;
- Docker container để tái tạo giống nhau giữa các máy.

Docker được ưu tiên cho course lab vì dễ reset và CI dùng cùng image.

### Tool GUI

Có thể dùng:

- SQL Server Management Studio;
- Visual Studio Code với SQL extension;
- Azure Data Studio chỉ còn là ghi chú lịch sử: đã ngừng hỗ trợ từ 28/02/2026, không chọn cho setup mới ([thông báo Microsoft](https://learn.microsoft.com/en-us/azure-data-studio/whats-happening-azure-data-studio));
- `sqlcmd`.

Không phụ thuộc GUI: mọi bài đều phải chạy được bằng script.

## 6. Lỗi thường gặp

### Dùng tài khoản sa trong ứng dụng

`sa` chỉ phù hợp lab/admin.

Production cần login/user với quyền tối thiểu.

### Dùng database như file dump

Nếu mọi dữ liệu nhét vào JSON text, database không thể bảo vệ relation/type/index tốt.

### Đặt business identity làm primary key quá sớm

Email có thể thay đổi.

Surrogate key như `CustomerId` thường ổn định hơn.

### Không script hóa setup

Click GUI thủ công khó tái tạo.

Project tốt phải có script/migration để dựng schema từ đầu.

## 7. Khi nào KHÔNG dùng

Không dùng database server chỉ để thay một hằng số cấu hình nhỏ. Không dùng các script reset bài học trên instance có dữ liệu thật; chúng xóa database lab được ghi tên rõ.

## 8. Production notes & scale check

Lab chỉ có hai row để đọc được toàn bộ luồng. Verifier dùng container SQL Server 2025 riêng, ghi build/image và output; không kết nối DB ứng dụng. Dữ liệu container không có volume sẽ mất khi xóa container. Tài khoản sa và trust certificate chỉ dành cho môi trường lab này.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Tạo database `SchoolLab` và table `Students` gồm:

- StudentId;
- FullName;
- Email.

### Bài 2

Insert 5 student rồi query theo StudentId.

### Bài 3

Vẽ mô hình:

```text
Customer
Order
OrderItem
Product
```

và ghi cardinality.

### Bài 4

Giải thích vì sao order item không nên lưu tên customer trực tiếp.

### Bài 5

Xóa container SQL Server rồi dựng lại bằng cùng command để kiểm tra tính tái tạo.

## 10. Bài tập tích hợp liên module — Judgment

So Dictionary Module 07 và file writer Module 06: phần nào của ownership/durability được chuyển sang database, phần nào ứng dụng vẫn phải quyết định? Với một công cụ cá nhân lưu20 mục, chọn cách đơn giản nhất.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Code SQL chạy ở client hay server?
2. GO do ai xử lý?
3. State nào mất khi đóng session?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt database/table/row/column.
- [ ] Tôi giải thích được primary key.
- [ ] Tôi chạy được SQL Server 2025.
- [ ] Tôi kết nối được bằng sqlcmd.
- [ ] Tôi tạo database/table bằng script.
- [ ] Tôi hiểu vì sao relation cần key.

Điều hướng:

- Prerequisite: [Big-O và cấu trúc dữ liệu](../07-cau-truc-du-lieu-giai-thuat/01-big-o-thoi-gian-va-bo-nho.md)
- Bài tiếp theo: [Thiết kế schema, table, key và constraint](./02-thiet-ke-schema-table-key-constraint.md)
