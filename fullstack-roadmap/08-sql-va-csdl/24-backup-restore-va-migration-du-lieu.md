# Backup, restore và migration dữ liệu

> **Last verified:** 2026-09-23  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Backup chỉ có giá trị khi có thể restore và dữ liệu phục hồi đáp ứng yêu cầu.
- Dùng restore drill và migration theo bước có thể kiểm chứng.
- VERIFYONLY, replica và rollback application đều không tự thay thế backup/restore.

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

### Trực giác 60 giây

Chụp một bản sổ rồi cất đi chưa biết có đọc được khi cần. Phải thử mở bản đó ở nơi khác, kiểm nội dung và đo thời gian; đồng thời tránh sửa mẫu sổ mới khiến phần mềm cũ không đọc được.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| RPO | mức mất dữ liệu tối đa chấp nhận theo thời gian | mất tối đa 1 giờ |
| RTO | thời gian mục tiêu khôi phục dịch vụ | trở lại trong 30 phút |
| backfill | điền dữ liệu cũ vào cột mới | FirstName/LastName |
| expand-contract | thêm tương thích rồi mới bỏ cũ | hai release |
| restore drill | thử phục hồi có kiểm dữ liệu | database tên khác |

### Ví dụ nhỏ — tính tay trước

Nguyễn Văn An được demo tách LastName=Nguyễn,FirstName=Văn An. Đây là quy tắc đơn giản cho fixture, không hiểu tên mọi nền văn hóa. FullName được giữ để đối chiếu và sửa ca mơ hồ.

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

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

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
WITH COPY_ONLY, INIT, CHECKSUM, STATS = 10;

RESTORE VERIFYONLY
FROM DISK = N'/var/opt/mssql/backup/CommerceLab08_24.bak'
WITH CHECKSUM;
```

VERIFYONLY kiểm khả năng đọc/kiểm tra backup nhưng không thay thế restore và kiểm dữ liệu ([Microsoft Learn](https://learn.microsoft.com/en-us/sql/t-sql/statements/restore-statements-verifyonly-transact-sql?view=sql-server-ver17)). Trong container lab riêng, folder `/var/opt/mssql/backup` phải tồn tại và SQL Server có quyền ghi. File .bak này là artifact lab có thể ghi đè bằng INIT.

Restore thực tế vào tên khác, giữ nguyên database nguồn:

```sql
USE master;
GO
IF DB_ID(N'CommerceLab08_24_Restore') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_24_Restore SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_24_Restore;
END;
GO
RESTORE DATABASE CommerceLab08_24_Restore
FROM DISK = N'/var/opt/mssql/backup/CommerceLab08_24.bak'
WITH
    MOVE N'CommerceLab08_24' TO N'/var/opt/mssql/data/CommerceLab08_24_Restore.mdf',
    MOVE N'CommerceLab08_24_log' TO N'/var/opt/mssql/data/CommerceLab08_24_Restore_log.ldf',
    CHECKSUM;
GO
DBCC CHECKDB(N'CommerceLab08_24_Restore') WITH NO_INFOMSGS;
GO
SELECT CustomerId, FullName, FirstName, LastName
FROM CommerceLab08_24_Restore.dbo.Customers
ORDER BY CustomerId;
GO
```

Tên logical file trong MOVE là tên do CREATE DATABASE của lab tạo. Với backup khác, đọc RESTORE FILELISTONLY trước; không đoán tên hoặc ghi đè file của database khác.

### Walkthrough — execution / state / cost

1. ALTER thêm cột nullable, UPDATE backfill và SELECT kiểm mapping.
2. BACKUP COPY_ONLY CHECKSUM ghi file ở filesystem server, không phải máy client.
3. VERIFYONLY đọc kiểm backup; RESTORE với MOVE tạo database và files khác nguồn.
4. CHECKDB và query đối chiếu dữ liệu kiểm restore. Log/storage/locks và thời gian phục hồi là cost thật; chưa đo RTO production chỉ từ 2 row.

### Mini-check

BACKUP path nằm ở container: copy file ra host rồi xóa container có còn đủ dữ liệu/khóa cần để restore không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| backup | bản để phục hồi ở thời điểm trước | cần bảo vệ file và thử restore |
| replica/failover | giảm gián đoạn khi node lỗi | có thể sao chép cả xóa nhầm |
| VERIFYONLY / restore | kiểm backup có thể đọc / tạo DB rồi kiểm thực tế | VERIFYONLY không chứng minh toàn bộ cấu trúc và nội dung đúng |

### Misconception check

**Đúng hay sai?** Backup file tồn tại nghĩa là mục tiêu RTO đã đạt.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: phải thử phục hồi cả dịch vụ trong thời gian yêu cầu.

</details>

**Đúng hay sai?** Tách tên theo dấu cách đầu luôn ra FirstName/LastName đúng.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: cần policy, dữ liệu quốc tế và review ca mơ hồ.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** restore end-to-end.

- **Working Developer — dùng khi làm việc:** backfill validation và compatibility.

- **Deep Dive — có thể quay lại sau:** log chain/PITR khi requirement cần.

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

### Tách tên theo một dấu cách rồi coi là quy tắc quốc tế

Code chỉ minh họa backfill cho hai tên mẫu: từ đầu đưa vào LastName, phần còn lại vào FirstName. Tên một từ, tên ghép, khoảng trắng thừa hoặc quy ước văn hóa khác không được giải đúng tự động. Giữ FullName gốc, xác định policy với nghiệp vụ và đưa ca mơ hồ vào hàng đợi review.

### Rename semantics mà không verify backfill

Dữ liệu có thể sai âm thầm.

## 7. Khi nào KHÔNG dùng

Không DROP cột cũ cùng lúc đổi application khi cần rollback phiên bản. Không dùng INIT vào file backup quan trọng ngoài lab; không đoán logical file name của backup khác.

## 8. Production notes & scale check

Gate chạy cả 3 block: migration, backup/VERIFYONLY, restore/CHECKDB và so dữ liệu nguồn–đích. Đây là full backup nhỏ, chưa kiểm log chain/PITR, encryption key recovery hay RPO/RTO thực tế. Restore target dùng tên riêng trong container tạm.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Từ snapshot Module 07 và commit point Module 06: bản sao RAM khác backup bền vững ở đâu? Viết kế hoạch thêm Email bắt buộc gồm backfill, validation và rollback app trước bỏ cột cũ.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Backup path thuộc máy nào?
2. VERIFYONLY thiếu bằng chứng gì?
3. Expand-contract giữ tương thích lúc nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt backup và HA.
- [ ] Tôi hiểu RPO/RTO.
- [ ] Tôi tạo/verify được backup.
- [ ] Tôi hiểu restore test là bắt buộc.
- [ ] Tôi thiết kế expand-contract migration.
- [ ] Tôi có validation và rollback plan.

Điều hướng:

- Bài trước: [Bảo mật, phân quyền và SQL injection](./23-bao-mat-phan-quyen-va-sql-injection.md)
- Bài tiếp theo: [Dự án CSDL thương mại điện tử](./25-du-an-csdl-thuong-mai-dien-tu.md)
