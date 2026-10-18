# Failure Lab — Bộ lọc sản phẩm trả sai tập hàng

Cụm 01–05. Chạy trên SQL Server lab của [bài 01](../01-mo-hinh-quan-he-va-cai-dat-sql-server.md); script tạo database riêng `FailureLab08_01` và cố ý chứa lỗi. Không chạy trên database thật.

## Bối cảnh

Endpoint `GET /products?search=...&maxPrice=...` tìm sản phẩm đang bán có từ khóa trong tên **hoặc** mô tả, giá không vượt `maxPrice`; không gửi `maxPrice` nghĩa là không giới hạn giá. Query đã qua code review vì “chạy được, không lỗi”, nhưng QA mở ba ticket trong cùng một tuần.

## Code lỗi

Lưu thành `failure01.sql` và chạy bằng `sqlcmd ... -C -b -i`:

```sql
USE master;
GO

IF DB_ID(N'FailureLab08_01') IS NOT NULL
BEGIN
    ALTER DATABASE FailureLab08_01
        SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
    DROP DATABASE FailureLab08_01;
END;
GO

CREATE DATABASE FailureLab08_01;
GO
USE FailureLab08_01;
GO

CREATE TABLE dbo.Products
(
    ProductId int IDENTITY(1,1) NOT NULL
        CONSTRAINT PK_Products PRIMARY KEY,
    Name nvarchar(160) NOT NULL,
    Description nvarchar(400) NULL,
    Price decimal(19,4) NOT NULL,
    IsActive bit NOT NULL
);

INSERT INTO dbo.Products (Name, Description, Price, IsActive)
VALUES
(N'Chuột không dây M1', N'Chuột văn phòng',              450000, 1),
(N'Chuột không dây M2', N'Pin 12 tháng',                 900000, 1),
(N'Bàn phím cơ K1',     N'Kết nối không dây và có dây', 1200000, 1),
(N'Tai nghe H1',        N'Tai nghe không dây đời cũ',    350000, 0),
(N'Lót chuột P1',       NULL,                            450000, 1);
GO

-- Query của endpoint GET /products?search=...&maxPrice=...
DECLARE @Search nvarchar(100) = N'không dây';
DECLARE @MaxPrice decimal(19,4) = 500000;   -- thử lại với NULL: "không giới hạn giá"

SELECT
    ProductId,
    Name,
    Price,
    IsActive
FROM dbo.Products
WHERE IsActive = 1
  AND Name LIKE N'%' + @Search + N'%'
   OR Description LIKE N'%' + @Search + N'%'
  AND Price <= @MaxPrice
ORDER BY Price DESC
OFFSET 0 ROWS FETCH NEXT 3 ROWS ONLY;
GO
```

## Triệu chứng

Với `@MaxPrice = 500000`, kết quả là:

```text
ProductId | Name               | Price       | IsActive
----------+--------------------+-------------+---------
2         | Chuột không dây M2 | 900000.0000 | 1
1         | Chuột không dây M1 | 450000.0000 | 1
4         | Tai nghe H1        | 350000.0000 | 0
```

- Ticket 1: chuột 900 000 vẫn hiện dù giá tối đa là 500 000.
- Ticket 2: tai nghe đã ngừng bán (`IsActive = 0`) xuất hiện.
- Ticket 3: khi không nhập giá tối đa (`@MaxPrice = NULL`), bàn phím có “không dây” trong mô tả biến mất, chỉ còn hai con chuột.

Không có exception nào; log ứng dụng sạch.

## Cách tái hiện

1. Chạy script nguyên văn, ghi lại output với `@MaxPrice = 500000`.
2. Đổi `@MaxPrice` thành `NULL`, chạy lại phần query, ghi output.
3. Trước khi sửa, viết **expected output** cho cả hai trường hợp bằng cách đọc dữ liệu năm hàng, không chạy query.
4. Giữ lại output lỗi để chứng minh bản sửa thay đổi đúng chỗ.

## Acceptance criteria

- Chỉ trả sản phẩm `IsActive = 1`, khớp từ khóa trong `Name` hoặc `Description`.
- `@MaxPrice = NULL` nghĩa là không giới hạn giá; `@MaxPrice = 500000` loại mọi sản phẩm trên 500 000.
- Thứ tự deterministic: hai sản phẩm cùng giá luôn ra theo cùng một thứ tự giữa các lần gọi.
- Có bằng chứng chạy được cho cả hai giá trị `@MaxPrice`, so với expected output đã viết trước.
- Giải thích bằng three-valued logic vì sao bản lỗi cho kết quả như trên, không chỉ nộp query đã sửa.

## Hints

1. Viết lại `WHERE` với ngoặc tường minh theo đúng precedence mà engine dùng (bài [05](../05-filter-sort-va-pagination.md)).
2. Khi `@MaxPrice` là `NULL`, `Price <= @MaxPrice` cho giá trị gì, và `WHERE` xử lý giá trị đó ra sao (bài [03](../03-kieu-du-lieu-va-null.md))?
3. Sửa ngoặc xong, chạy lại với `NULL`: danh sách rỗng hay đủ? Filter tùy chọn cần nói rõ nhánh “không có giá trị”.

## Checklist điều tra

- [ ] Viết expected output cho cả hai trường hợp trước khi sửa.
- [ ] Viết lại `WHERE` lỗi thành dạng có ngoặc và chỉ ra nhánh nào làm lọt từng hàng sai.
- [ ] Giải thích ticket 3 bằng `TRUE`/`FALSE`/`UNKNOWN`.
- [ ] Kiểm tra tiebreaker trong `ORDER BY`.
- [ ] Nộp diff nhỏ và output của cả hai lần chạy sau khi sửa.

Quay lại [bản đồ Module 08](../index.md).
