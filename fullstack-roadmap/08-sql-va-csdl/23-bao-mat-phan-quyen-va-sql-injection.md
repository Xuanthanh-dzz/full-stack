# Bảo mật, phân quyền và SQL injection

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Phân quyền giới hạn thao tác; parameterization giữ dữ liệu tách khỏi syntax SQL.
- Dùng role nhỏ theo nhiệm vụ và typed parameters ở boundary.
- Parameter không đại diện tên bảng/cột; stored procedure vẫn có thể injection nếu nối chuỗi bên trong.

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

### Trực giác 60 giây

Mẫu phiếu có ô nhập tên. Nếu nội dung ô được dán thành chỉ thị mới trong câu lệnh, người nhập có thể đổi việc hệ thống làm. Parameter giữ nội dung trong ô dữ liệu, còn quyền nhỏ giới hạn hậu quả của lỗi khác.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| login | identity để kết nối instance | khác user trong DB |
| database user | identity nhận quyền trong database | demo_reader |
| role | nhóm quyền được cấp cho thành viên | app_reader |
| parameter | giá trị có type truyền tách SQL text | @Pattern |
| allowlist | tập tên được phép chọn | sort column hợp lệ |

### Ví dụ nhỏ — tính tay trước

demo_reader SELECT Products được nhưng DELETE phải bị từ chối. Chuỗi nhập có dấu nháy hoặc giống `OR 1=1` vẫn chỉ là dữ liệu khi truyền qua `@Pattern`; ký tự `%` vẫn là wildcard của `LIKE` theo contract.

Code nguy hiểm:

```csharp
string sql =
    "SELECT * FROM Users WHERE Email = '" +
    email +
    "'";
```

Nếu input trở thành một phần syntax SQL, attacker có thể thay đổi câu lệnh.

Vấn đề cốt lõi là **code và data không được tách rời**.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. DDL tạo roles và user WITHOUT LOGIN để mô phỏng quyền trong một database.
2. EXECUTE AS đổi execution context của session; REVERT trả context trước.
3. sp_executesql nhận SQL text cố định, khai báo type parameter và giá trị riêng.
4. Engine kiểm quyền và thực thi query; app giữ secret kết nối ngoài source/log. Dynamic SQL có ownership/permission khác static SQL, cần test bằng user thật.

### Mini-check

Ứng dụng muốn sort theo cột do user chọn: tại sao ORDER BY @Column không thay tên column được?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| typed parameter | cho value | không thay identifier hoặc cả mệnh đề ORDER BY |
| allowlist + QUOTENAME | cho identifier đã được phép | quote không tự cấp quyền hoặc xác nhận nghiệp vụ |
| least privilege | giảm thao tác được phép | không thay parameterization |

### Misconception check

**Đúng hay sai?** Dùng stored procedure thì không thể SQL injection.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: procedure có thể nối input vào dynamic SQL.

</details>

**Đúng hay sai?** Parameter LIKE % nghĩa là tìm ký tự% theo nghĩa literal.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: parameter vẫn được LIKE diễn giải wildcard, chỉ không trở thành SQL syntax.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** code/data và roles.

- **Working Developer — dùng khi làm việc:** negative permission tests.

- **Deep Dive — có thể quay lại sau:** ownership chain/TLS khi triển khai.

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

## 7. Khi nào KHÔNG dùng

Không grant db_owner/sa cho runtime để làm hết lỗi quyền. Không tự escape dấu nháy thay parameter API; không xem QUOTENAME là allowlist.

## 8. Production notes & scale check

Gate chạy SELECT thành công và DELETE bị từ chối dưới demo_reader, kiểm input dạng injection không mở rộng kết quả. User WITHOUT LOGIN không test network authentication/TLS của deployment. Script chạy admin để dựng lab, không phải mẫu quyền cho application.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

So role interface Module 06 với database role: cái nào giới hạn API lúc compile, cái nào engine thực thi bằng identity? Thiết kế quyền migration riêng quyền runtime.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Login và user khác scope nào?
2. Parameter không thay được gì?
3. REVERT phục hồi state nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt login/user/role.
- [ ] Tôi áp dụng least privilege.
- [ ] Tôi dùng parameterized query.
- [ ] Tôi không dùng sa cho runtime app.
- [ ] Tôi whitelist dynamic identifier.
- [ ] Tôi không commit/log secret.

Điều hướng:

- Bài trước: [Tối ưu truy vấn và SARGability](./22-toi-uu-truy-van-va-sargability.md)
- Bài tiếp theo: [Backup, restore và migration dữ liệu](./24-backup-restore-va-migration-du-lieu.md)
