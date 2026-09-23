# Failure Lab — Thiếu kho nhưng vẫn commit đơn

Sau bài 20; SQL Server 2025/T-SQL. Dùng session lab riêng, các table variable/temp table không ghi dữ liệu ứng dụng.

## Bối cảnh

Checkout phải hoặc tạo đơn và trừ kho, hoặc giữ nguyên cả hai.

## Code lỗi

Chạy nguyên block độc lập trong sqlcmd; output dưới đây là dấu hiệu lỗi cần điều tra.

```sql
CREATE TABLE #Stock (Id int PRIMARY KEY, Quantity int NOT NULL CHECK(Quantity>=0));
CREATE TABLE #Orders (Id int PRIMARY KEY);
INSERT INTO #Stock VALUES (1,5);
BEGIN TRAN;
INSERT INTO #Orders VALUES (1);
UPDATE #Stock SET Quantity=Quantity-10 WHERE Id=1 AND Quantity>=10;
COMMIT;
SELECT (SELECT COUNT(*) FROM #Orders) AS OrdersCreated, Quantity FROM #Stock;
```

## Triệu chứng

Output dữ liệu hiện tại: `1|5` (dấu | ngăn cột, bỏ header). Viết expected từ contract trước khi sửa.

## Cách tái hiện

Kết nối container lab ở bài01, chạy block bằng sqlcmd với `-b -C -W -h -1 -s "|"`. Ghi engine build, output, lỗi và exit code. Không chạy trên database ứng dụng. Verifier tái hiện bản lỗi; learner phải nộp test bản sửa riêng.

## Acceptance criteria

- Thiếu kho phải báo lỗi và không tạo order; đủ kho thành công. Kiểm @@ROWCOUNT ngay và không để transaction mở.
- Có test đỏ với bản lỗi, xanh với bản sửa và ít nhất một biên.
- Giải thích nơi code chạy, state trước/sau và cost.
- Giữ diff lỗi và bằng chứng, không chỉ thay expected cho qua.

## Hints

1. UPDATE0 row có tự là exception không?
2. Trace từng bước theo semantics SQL; không nhầm logical order với physical plan.
3. Chọn sửa nhỏ nhất bảo vệ contract, nêu điều kiện phải xem lại khi scale.

## Checklist điều tra

- [ ] Contract và input tối thiểu.
- [ ] State/output khác expected ở bước nào.
- [ ] Root cause và regression test.
- [ ] Diff, trade-off và giới hạn kiểm chứng.

[Bản đồ](../index.md).
