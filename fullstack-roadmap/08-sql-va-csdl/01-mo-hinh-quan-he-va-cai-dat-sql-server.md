# Mô hình quan hệ và cài đặt SQL Server

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích database, table, row, column, key và relationship;
- phân biệt dữ liệu quan hệ với object trong chương trình;
- cài hoặc chạy SQL Server 2025 bằng Docker;
- kết nối bằng `sqlcmd` hoặc công cụ GUI;
- tạo database đầu tiên và chạy truy vấn kiểm tra;
- hiểu vì sao schema phải được thiết kế trước khi EF Core xuất hiện.

## 2. Bài toán mở đầu

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

## 3. Lời giải bằng SQL

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

## 4. Giải thích cơ chế

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

## 5. Kiến thức nền

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
- Azure Data Studio ở môi trường cũ;
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

## 7. Bài tập

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

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt database/table/row/column.
- [ ] Tôi giải thích được primary key.
- [ ] Tôi chạy được SQL Server 2025.
- [ ] Tôi kết nối được bằng sqlcmd.
- [ ] Tôi tạo database/table bằng script.
- [ ] Tôi hiểu vì sao relation cần key.

Điều hướng:

- Prerequisite: [Big-O và cấu trúc dữ liệu](../07-cau-truc-du-lieu-giai-thuat/01-big-o-thoi-gian-va-bo-nho.md)
- Bài tiếp theo: [Thiết kế schema, table, key và constraint](./02-thiet-ke-schema-table-key-constraint.md)
