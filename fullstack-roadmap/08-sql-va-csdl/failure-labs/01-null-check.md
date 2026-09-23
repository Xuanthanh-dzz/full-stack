# Failure Lab — CHECK không cấm NULL

Sau bài 05; SQL Server 2025/T-SQL. Dùng session lab riêng, các table variable/temp table không ghi dữ liệu ứng dụng.

## Bối cảnh

Giá bắt buộc có và không âm; mọi writer phải tuân rule.

## Code lỗi

Chạy nguyên block độc lập trong sqlcmd; output dưới đây là dấu hiệu lỗi cần điều tra.

```sql
DECLARE @Products TABLE (Id int PRIMARY KEY, Price decimal(10,2) NULL CHECK (Price >= 0));
INSERT INTO @Products VALUES (1, NULL);
SELECT COUNT(*) AS AcceptedRows FROM @Products;
```

## Triệu chứng

Output dữ liệu hiện tại: `1` (dấu | ngăn cột, bỏ header). Viết expected từ contract trước khi sửa.

## Cách tái hiện

Kết nối container lab ở bài01, chạy block bằng sqlcmd với `-b -C -W -h -1 -s "|"`. Ghi engine build, output, lỗi và exit code. Không chạy trên database ứng dụng. Verifier tái hiện bản lỗi; learner phải nộp test bản sửa riêng.

## Acceptance criteria

- NULL phải bị từ chối,0vẫn hợp lệ và số âm bị chặn. Chỉ sửa constraint/type cần thiết.
- Có test đỏ với bản lỗi, xanh với bản sửa và ít nhất một biên.
- Giải thích nơi code chạy, state trước/sau và cost.
- Giữ diff lỗi và bằng chứng, không chỉ thay expected cho qua.

## Hints

1. CHECK từ chối FALSE hay cả UNKNOWN?
2. Trace từng bước theo semantics SQL; không nhầm logical order với physical plan.
3. Chọn sửa nhỏ nhất bảo vệ contract, nêu điều kiện phải xem lại khi scale.

## Checklist điều tra

- [ ] Contract và input tối thiểu.
- [ ] State/output khác expected ở bước nào.
- [ ] Root cause và regression test.
- [ ] Diff, trade-off và giới hạn kiểm chứng.

[Bản đồ](../index.md).
