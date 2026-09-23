# Failure Lab — Khách chưa mua biến mất khỏi LEFT JOIN

Sau bài 10; SQL Server 2025/T-SQL. Dùng session lab riêng, các table variable/temp table không ghi dữ liệu ứng dụng.

## Bối cảnh

Report giữ mọi khách và chỉ ghép đơn Paid nếu có.

## Code lỗi

Chạy nguyên block độc lập trong sqlcmd; output dưới đây là dấu hiệu lỗi cần điều tra.

```sql
DECLARE @Customers TABLE (Id int PRIMARY KEY);
DECLARE @Orders TABLE (Id int PRIMARY KEY, CustomerId int, Status varchar(20));
INSERT INTO @Customers VALUES (1),(2),(3);
INSERT INTO @Orders VALUES (101,1,'Paid'),(102,2,'Pending');
SELECT c.Id, o.Id AS OrderId
FROM @Customers c LEFT JOIN @Orders o ON o.CustomerId=c.Id
WHERE o.Status='Paid'
ORDER BY c.Id;
```

## Triệu chứng

Output dữ liệu hiện tại: `1|101` (dấu | ngăn cột, bỏ header). Viết expected từ contract trước khi sửa.

## Cách tái hiện

Kết nối container lab ở bài 01, chạy block bằng sqlcmd với `-b -C -W -h -1 -s "|"`. Ghi engine build, output, lỗi và exit code. Không chạy trên database ứng dụng. Verifier tái hiện bản lỗi; learner phải nộp test bản sửa riêng.

## Acceptance criteria

- Giữ cả 3 khách; khách 2 và 3 có NULL phía đơn. Không thêm DISTINCT hoặc UNION để che nguyên nhân.
- Có test đỏ với bản lỗi, xanh với bản sửa và ít nhất một biên.
- Giải thích nơi code chạy, state trước/sau và cost.
- Giữ diff lỗi và bằng chứng, không chỉ thay expected cho qua.

## Hints

1. Predicate đặt ở ON khác WHERE tại bước bổ sung NULL thế nào?
2. Trace từng bước theo semantics SQL; không nhầm logical order với physical plan.
3. Chọn sửa nhỏ nhất bảo vệ contract, nêu điều kiện phải xem lại khi scale.

## Checklist điều tra

- [ ] Contract và input tối thiểu.
- [ ] State/output khác expected ở bước nào.
- [ ] Root cause và regression test.
- [ ] Diff, trade-off và giới hạn kiểm chứng.

[Bản đồ](../index.md).
