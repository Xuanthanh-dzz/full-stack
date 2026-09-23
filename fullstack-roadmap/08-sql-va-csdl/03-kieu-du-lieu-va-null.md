# Kiểu dữ liệu và NULL

> **Last verified:** pending — chưa chạy lại gate retrofit  
> **Baseline:** SQL Server 2025 (17.x) · T-SQL · compatibility level 170 · sqlcmd 18  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi SQL sample/schema, engine build, compatibility/isolation/plan; CI failure

## TL;DR

- Kiểu dữ liệu giữ miền giá trị; NULL biểu diễn giá trị chưa có theo contract.
- Chọn type theo range, độ chính xác và ý nghĩa nghiệp vụ.
- NULL, số 0 và chuỗi rỗng khác nhau; xử lý chúng tùy tiện làm sai báo cáo.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- chọn integer, decimal, string, date/time và binary type phù hợp;
- phân biệt `varchar` và `nvarchar`;
- hiểu precision/scale của `decimal`;
- hiểu `NULL` là unknown/missing chứ không phải 0 hay chuỗi rỗng;
- dùng `IS NULL` và `IS NOT NULL`;
- tránh lỗi so sánh NULL bằng `=`;
- thiết kế nullable theo business semantics.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Ô cân nặng chưa đo không thể ghi0 vì0 là một kết quả đo. Một nhãn trống cũng khác chưa từng nhập nhãn. Database cần lưu được các khác biệt ấy để phép tính sau có nghĩa.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| precision/scale | tổng chữ số/số chữ số sau dấu thập phân | decimal(10,3) |
| NULL | không có giá trị theo ý nghĩa đã chọn | WeightKg chưa biết |
| UNKNOWN | kết quả logic chưa xác định | NULL=0 |
| rowversion | token nhị phân đổi khi row được cập nhật | không phải ngày giờ |

### Ví dụ nhỏ — tính tay trước

Weights gồm NULL và 0.095: COUNT(*)=2,COUNT(WeightKg)=1,AVG=0.095. WHERE WeightKg=0 không nhận row NULL; IS NULL nhận đúng row chưa đo.

Một table Product có:

```text
Price = 99.99
Weight = chưa biết
Description = ""
ReleasedAt = chưa có
```

Bốn trạng thái không giống nhau.

Nếu mọi thứ đều lưu string, bạn mất:

- validation kiểu;
- sort đúng;
- arithmetic;
- storage tối ưu;
- semantics NULL.

<a id="3-loi-giai-bang-sql"></a>

## 3. Lời giải chạy được

```sql
USE master;
GO

IF DB_ID(N'CommerceLab08_03') IS NOT NULL
BEGIN
    ALTER DATABASE CommerceLab08_03
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE CommerceLab08_03;
END;
GO

CREATE DATABASE CommerceLab08_03;
GO
USE CommerceLab08_03;
GO

CREATE TABLE dbo.Products
(
    ProductId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,

    Sku varchar(40) NOT NULL,
    Name nvarchar(160) NOT NULL,

    Price decimal(19,4) NOT NULL,
    WeightKg decimal(10,3) NULL,

    Stock int NOT NULL,
    IsActive bit NOT NULL,

    ReleasedAt date NULL,
    CreatedAt datetime2(3) NOT NULL,

    Description nvarchar(2000) NULL,
    RowVersion rowversion NOT NULL,

    CONSTRAINT CK_Products_Price CHECK (Price >= 0),
    CONSTRAINT CK_Products_Stock CHECK (Stock >= 0)
);
GO

INSERT INTO dbo.Products
(
    Sku,
    Name,
    Price,
    WeightKg,
    Stock,
    IsActive,
    ReleasedAt,
    CreatedAt,
    Description
)
VALUES
(
    'KB-01',
    N'Bàn phím cơ',
    1299000.0000,
    NULL,
    25,
    1,
    NULL,
    SYSUTCDATETIME(),
    N''
),
(
    'MS-01',
    N'Chuột không dây',
    599000.0000,
    0.095,
    40,
    1,
    '2026-01-15',
    SYSUTCDATETIME(),
    NULL
);
GO

SELECT
    ProductId,
    Name,
    Price,
    WeightKg,
    ReleasedAt,
    Description
FROM dbo.Products
WHERE WeightKg IS NULL
   OR ReleasedAt IS NULL;
GO

SELECT
    Name,
    COALESCE(Description, N'(chưa có mô tả)') AS DisplayDescription
FROM dbo.Products
ORDER BY ProductId;
GO
```

### Walkthrough — execution / state / cost

1. INSERT chuyển literal sang type của cột và kiểm constraints.
2. WHERE giữ row chỉ khi predicate là TRUE; UNKNOWN bị loại cùng FALSE.
3. COALESCE thay NULL trong projection, không tự UPDATE dữ liệu gốc.
4. Type quyết định kích thước lưu/index và cách arithmetic chạy trên server. NVARCHAR(n) dùng n đơn vị mã UTF-16 tối đa; emoji có thể cần hai đơn vị.

### Mini-check

COALESCE(Description,N'chưa có') có thay chuỗi rỗng thành fallback không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Integer

Dùng range phù hợp:

```text
tinyint
smallint
int
bigint
```

Đừng mặc định `bigint` cho mọi thứ.

### Decimal

Tiền nên dùng:

```sql
decimal(19,4)
```

Không dùng `float` cho tiền vì floating point là approximate.

### varchar và nvarchar

`nvarchar` phù hợp text Unicode như tên tiếng Việt.

Identifier kỹ thuật chỉ ASCII có thể dùng `varchar`.

### Date/time

Ưu tiên:

- `date` nếu chỉ ngày;
- `datetime2` cho timestamp;
- `datetimeoffset` nếu cần lưu offset cụ thể.

### NULL

`NULL` nghĩa là:

```text
unknown / missing / not applicable
```

Ba-valued logic:

```text
TRUE
FALSE
UNKNOWN
```

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| NULL | thiếu/không áp dụng, phải quy định | cần three-valued logic |
| 0 hoặc chuỗi rỗng | giá trị đã biết | tham gia so sánh và aggregate như giá trị thật |
| float | số gần đúng | hợp đo lường, không dùng khi cần tiền chính xác thập phân |

### Misconception check

**Đúng hay sai?** NULL=NULL là TRUE.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: kết quả UNKNOWN, dùng IS NULL.

</details>

**Đúng hay sai?** rowversion cho biết thời điểm sửa.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: đó là token thay đổi trong database, không mã hóa ngày giờ.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** NULL và type.

- **Working Developer — dùng khi làm việc:** precision/scale và mapping.

- **Deep Dive — có thể quay lại sau:** collation/encoding theo workload.

### So sánh NULL

Sai:

```sql
WHERE WeightKg = NULL
```

Đúng:

```sql
WHERE WeightKg IS NULL
```

### COALESCE

```sql
COALESCE(Description, N'(chưa có)')
```

trả expression đầu tiên không NULL.

### NULL và aggregate

Nhiều aggregate bỏ qua NULL.

Ví dụ `AVG(WeightKg)` chỉ tính row có weight.

Cần hiểu semantics trước khi diễn giải số liệu.

### rowversion

`rowversion` là binary token tự tăng trong database, không phải timestamp ngày giờ.

Sau này EF Core có thể dùng nó cho optimistic concurrency.

## 6. Lỗi thường gặp

### Dùng float cho tiền

Có thể xuất hiện sai số biểu diễn.

### Dùng datetime cũ theo thói quen

`datetime2` có range/precision tốt hơn cho ứng dụng mới.

### Dùng NULL thay cho mọi trạng thái

Ví dụ Order.Status không nên nullable chỉ để “chưa xác định”.

Nếu business có trạng thái, hãy mô hình trạng thái rõ.

### Chuỗi rỗng và NULL lẫn lộn

```text
NULL = không có giá trị
''   = có chuỗi nhưng length 0
```

## 7. Khi nào KHÔNG dùng

Không chọn nvarchar(max) cho mọi key. Không dùng NULL làm toàn bộ state machine khi nghiệp vụ có các trạng thái cần phân biệt.

## 8. Production notes & scale check

Gate kiểm giá trị thập phân, NULL/empty và token rowversion thay sau UPDATE. datetime2 không lưu timezone: dùng UTC là quy ước cần duy trì; datetimeoffset lưu offset chứ không lưu đầy đủ timezone rules. Varchar với collation UTF-8 cũng lưu Unicode được; lab chọn nvarchar để baseline rõ.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1

Chọn type cho:

- quantity;
- money;
- email;
- birthday;
- uploaded file bytes.

### Bài 2

Tạo table Payment có:

- Amount;
- PaidAt nullable;
- ProviderReference nullable.

### Bài 3

Viết query tìm product chưa có ReleasedAt.

### Bài 4

Thử:

```sql
SELECT 1 WHERE NULL = NULL;
```

và giải thích vì sao không có row.

### Bài 5

So sánh storage/semantics giữa `nvarchar(100)` và `nvarchar(max)`.

## 10. Bài tập tích hợp liên module — Judgment

Từ nullable C# Module 04 và equality Module 05, so null check trong C# với predicate SQL UNKNOWN. DTO nào phải nullable để không bịa giá trị khi đọc WeightKg?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. WHERE có giữ UNKNOWN không?
2. COALESCE có sửa table không?
3. Token rowversion có ý nghĩa gì?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chọn type theo domain.
- [ ] Tôi không dùng float cho tiền.
- [ ] Tôi phân biệt varchar/nvarchar.
- [ ] Tôi hiểu NULL dùng three-valued logic.
- [ ] Tôi dùng IS NULL đúng.
- [ ] Tôi phân biệt NULL và empty string.

Điều hướng:

- Bài trước: [Thiết kế schema, table, key và constraint](./02-thiet-ke-schema-table-key-constraint.md)
- Bài tiếp theo: [CRUD: SELECT, INSERT, UPDATE, DELETE](./04-crud-select-insert-update-delete.md)
