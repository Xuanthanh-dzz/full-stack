# Failure Lab — Top 2 trả 3 row khi có tie

Sau bài 15; SQL Server 2025/T-SQL. Dùng session lab riêng, các table variable/temp table không ghi dữ liệu ứng dụng.

## Bối cảnh

API cần đúng tối đa 2 đơn mỗi khách, hòa tiền thì ID nhỏ trước.

## Code lỗi

Chạy nguyên block độc lập trong sqlcmd; output dưới đây là dấu hiệu lỗi cần điều tra.

```sql
DECLARE @Orders TABLE (Id int PRIMARY KEY, CustomerId int, Amount int);
INSERT INTO @Orders VALUES (1,1,100),(2,1,90),(3,1,90);
WITH Ranked AS
(
    SELECT Id, RANK() OVER(PARTITION BY CustomerId ORDER BY Amount DESC) AS rn
    FROM @Orders
)
SELECT COUNT(*) AS SelectedRows FROM Ranked WHERE rn<=2;
```

## Triệu chứng

Output dữ liệu hiện tại: `3` (dấu | ngăn cột, bỏ header). Viết expected từ contract trước khi sửa.

## Cách tái hiện

Kết nối container lab ở bài 01, chạy block bằng sqlcmd với `-b -C -W -h -1 -s "|"`. Ghi engine build, output, lỗi và exit code. Không chạy trên database ứng dụng. Verifier tái hiện bản lỗi; learner phải nộp test bản sửa riêng.

## Acceptance criteria

- Trả đúng ID 1, 2; thêm ca ít hơn 2 đơn và không tie. Giữ rõ contract 2 row khác 2 mức hạng.
- Có test đỏ với bản lỗi, xanh với bản sửa và ít nhất một biên.
- Giải thích nơi code chạy, state trước/sau và cost.
- Giữ diff lỗi và bằng chứng, không chỉ thay expected cho qua.

## Hints

1. RANK có bỏ qua hoặc giữ tie không? Tiebreaker thuộc window nào?
2. Trace từng bước theo semantics SQL; không nhầm logical order với physical plan.
3. Chọn sửa nhỏ nhất bảo vệ contract, nêu điều kiện phải xem lại khi scale.

## Checklist điều tra

- [ ] Contract và input tối thiểu.
- [ ] State/output khác expected ở bước nào.
- [ ] Root cause và regression test.
- [ ] Diff, trade-off và giới hạn kiểm chứng.

[Bản đồ](../index.md).
