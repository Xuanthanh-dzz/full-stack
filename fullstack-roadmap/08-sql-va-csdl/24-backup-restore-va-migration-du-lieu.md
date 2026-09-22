# Backup, restore và migration dữ liệu

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt backup với high availability;
- tạo full backup và restore;
- hiểu RPO/RTO ở mức cơ bản;
- kiểm tra backup;
- thiết kế migration dữ liệu theo bước;
- tránh migration phá dữ liệu;
- hiểu schema migration khác data migration.

## 2. Bài toán mở đầu

Một migration đổi:

```text
Customer.FullName
```

thành:

```text
FirstName
LastName
```

Nếu deploy code trước khi data migration xong, app có thể lỗi.

Nếu migration sai mà không có backup/rollback plan, downtime kéo dài.

Production data cần kế hoạch thay đổi có kiểm chứng.

## 3. Lời giải bằng SQL

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_24') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_24
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_24;
END;
GO

CREATE DATABASE CommerceLab08_24;
GO
USE CommerceLab08_24;
GO

CREATE TABLE dbo.Customers
(
    CustomerId int NOT NULL
        CONSTRAINT PK_Customers PRIMARY KEY,
    FullName nvarchar(200) NOT NULL
);

INSERT INTO dbo.Customers VALUES
(1,N'Nguyễn Văn An'),
(2,N'Trần Bình');
GO

ALTER TABLE dbo.Customers
ADD
    FirstName nvarchar(100) NULL,
    LastName nvarchar(100) NULL;
GO

UPDATE dbo.Customers
SET
    LastName = LEFT(FullName, CHARINDEX(N' ', FullName + N' ') - 1),
    FirstName = LTRIM(
        SUBSTRING(
            FullName,
            CHARINDEX(N' ', FullName + N' ') + 1,
            200
        )
    );
GO

SELECT
    CustomerId,
    FullName,
    FirstName,
    LastName
FROM dbo.Customers
ORDER BY CustomerId;
GO

SELECT
    name,
    recovery_model_desc
FROM sys.databases
WHERE name = N'CommerceLab08_24';
GO
```

Backup command chạy trong môi trường có folder backup mà SQL Server process truy cập được:

```sql
BACKUP DATABASE CommerceLab08_24
TO DISK = N'/var/opt/mssql/backup/CommerceLab08_24.bak'
WITH INIT, CHECKSUM, STATS = 10;

RESTORE VERIFYONLY
FROM DISK = N'/var/opt/mssql/backup/CommerceLab08_24.bak'
WITH CHECKSUM;
```

Restore nên thực hành vào database tên khác để không phá lab đang chạy.

## 4. Giải thích cơ chế

### Backup không phải HA

Backup bảo vệ khả năng phục hồi dữ liệu.

Replica/failover bảo vệ availability.

Hai mục tiêu khác nhau.

### RPO

Recovery Point Objective:

> chấp nhận mất tối đa bao nhiêu dữ liệu?

### RTO

Recovery Time Objective:

> cần phục hồi dịch vụ trong bao lâu?

### Expand-contract migration

Pattern an toàn:

1. add column mới;
2. deploy code tương thích hai schema nếu cần;
3. backfill;
4. verify;
5. chuyển read/write sang schema mới;
6. remove cũ ở release sau.

## 5. Kiến thức nền

### Full, differential, log backup

Recovery model và requirement quyết định chiến lược.

Module này tập trung concept, không thay thế DBA chuyên sâu.

### Restore test

Backup chưa từng restore thử chưa thể coi là đáng tin.

### Data migration

Migration lớn cần:

- idempotency hoặc checkpoint;
- batch;
- validation count/hash/sample;
- observability;
- rollback hoặc forward-fix plan.

### Schema migration khác data migration

Schema migration thay structure.

Data migration biến đổi nội dung row.

Nhiều release thực tế cần cả hai.

## 6. Lỗi thường gặp

### Chỉ backup trước release nhưng không test restore

Có file backup chưa có nghĩa restore được.

### DROP column cùng release với code mới

Rollback application trở nên khó.

### Update hàng trăm triệu row trong một transaction

Log, lock và downtime có thể bùng nổ.

### Rename semantics mà không verify backfill

Dữ liệu có thể sai âm thầm.

## 7. Bài tập

### Bài 1

Viết RPO/RTO cho shop nhỏ và hệ thống payment.

### Bài 2

Tạo full backup lab và chạy RESTORE VERIFYONLY.

### Bài 3

Restore thành database `CommerceLab08_24_Restore`.

### Bài 4

Thiết kế expand-contract cho Email bắt buộc unique.

### Bài 5

Viết validation checklist cho data migration 10 triệu row.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt backup và HA.
- [ ] Tôi hiểu RPO/RTO.
- [ ] Tôi tạo/verify được backup.
- [ ] Tôi hiểu restore test là bắt buộc.
- [ ] Tôi thiết kế expand-contract migration.
- [ ] Tôi có validation và rollback plan.

Điều hướng:

- Bài trước: [Bảo mật, phân quyền và SQL injection](./23-bao-mat-phan-quyen-va-sql-injection.md)
- Bài tiếp theo: [Dự án CSDL thương mại điện tử](./25-du-an-csdl-thuong-mai-dien-tu.md)
