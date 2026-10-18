# Bảo mật, phân quyền và SQL injection

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt login, user, role và permission;
- áp dụng least privilege;
- cấp quyền qua role;
- hiểu SQL injection xảy ra thế nào;
- dùng parameterized query;
- tránh dùng sa/application owner;
- bảo vệ secret kết nối;
- hiểu dynamic SQL cần whitelist identifier.

## 2. Bài toán mở đầu

Code nguy hiểm:

```csharp
string sql =
    "SELECT * FROM Users WHERE Email = '" +
    email +
    "'";
```

Nếu input trở thành một phần syntax SQL, attacker có thể thay đổi câu lệnh.

Vấn đề cốt lõi là **code và data không được tách rời**.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_23') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_23
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_23;
END;
GO

CREATE DATABASE CommerceLab08_23;
GO
USE CommerceLab08_23;
GO

CREATE TABLE dbo.Products
(
    ProductId int NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Name nvarchar(100) NOT NULL,
    Price decimal(19,4) NOT NULL
);

INSERT INTO dbo.Products VALUES
(1,N'Keyboard',1000000),
(2,N'Mouse',500000);
GO

CREATE ROLE app_reader;
CREATE ROLE app_writer;
GO

GRANT SELECT ON dbo.Products TO app_reader;
GRANT SELECT, INSERT, UPDATE ON dbo.Products TO app_writer;
GO

CREATE USER demo_reader WITHOUT LOGIN;
ALTER ROLE app_reader ADD MEMBER demo_reader;
GO

EXECUTE AS USER = 'demo_reader';

SELECT ProductId, Name, Price
FROM dbo.Products;

REVERT;
GO

DECLARE @Search nvarchar(100) = N'Key%';

EXEC sys.sp_executesql
    N'
      SELECT ProductId, Name, Price
      FROM dbo.Products
      WHERE Name LIKE @Pattern;
    ',
    N'@Pattern nvarchar(100)',
    @Pattern = @Search;
GO
```

## 4. Giải thích cơ chế

### Login và user

Khái niệm đơn giản:

```text
Login -> kết nối instance
User  -> identity trong database
Role  -> nhóm permission
```

### Least privilege

Ứng dụng chỉ cần quyền đúng use case, không cần sysadmin.

### SQL injection

Nguy cơ xuất hiện khi input được concatenate vào SQL syntax.

Parameter giữ SQL text và typed value tách biệt.

### Role

Grant cho role rồi add user vào role giúp quản trị dễ hơn.

## 5. Kiến thức nền

### Parameterization ở .NET

ADO.NET/EF Core phải dùng parameter API, không tự escape chuỗi.

### Dynamic SQL

Parameter không thay thế identifier như column/table name.

Nếu thật sự cần dynamic identifier:

- whitelist;
- dùng QUOTENAME khi phù hợp;
- không nhận raw syntax từ user.

### Secret

Connection string/password:

- không commit Git;
- dùng secret store/environment;
- rotate;
- audit access.

## 6. Lỗi thường gặp

### Application dùng sa

Một injection/bug có thể thành toàn quyền server.

### Escape dấu nháy bằng replace

Không thay thế parameterization.

### Grant db_owner cho tiện

Phá least privilege.

### Log connection string có password

Secret rò qua log/telemetry.

## 7. Bài tập

### Bài 1

Tạo role chỉ đọc catalog.

### Bài 2

Tạo role order_writer không được DROP table.

### Bài 3

Viết ví dụ injection trong lab rồi sửa bằng parameter.

### Bài 4

Tách migration account và runtime account.

### Bài 5

Viết checklist secret management cho ASP.NET Core.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt login/user/role.
- [ ] Tôi áp dụng least privilege.
- [ ] Tôi dùng parameterized query.
- [ ] Tôi không dùng sa cho runtime app.
- [ ] Tôi whitelist dynamic identifier.
- [ ] Tôi không commit/log secret.

Điều hướng:

- Bài trước: [Tối ưu truy vấn và SARGability](./22-toi-uu-truy-van-va-sargability.md)
- Bài tiếp theo: [Backup, restore và migration dữ liệu](./24-backup-restore-va-migration-du-lieu.md)
