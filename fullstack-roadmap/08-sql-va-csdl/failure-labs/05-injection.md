# Failure Lab — Dữ liệu bị ghép thành syntax SQL

Sau bài 25; SQL Server 2025/T-SQL. Dùng session lab riêng, các table variable/temp table không ghi dữ liệu ứng dụng.

## Bối cảnh

Tìm tên chính xác trong table tạm lab; chuỗi giống SQL vẫn chỉ là tên.

## Code lỗi

Chạy nguyên block độc lập trong sqlcmd; output dưới đây là dấu hiệu lỗi cần điều tra.

```sql
CREATE TABLE #Products (Id int PRIMARY KEY, Name nvarchar(100));
INSERT INTO #Products VALUES (1,N'Keyboard'),(2,N'Mouse');
DECLARE @Search nvarchar(100)=N'none'' OR 1=1 --';
DECLARE @Sql nvarchar(max)=N'SELECT COUNT(*) FROM #Products WHERE Name=N''' + @Search + N''';';
EXEC sys.sp_executesql @Sql;
```

## Triệu chứng

Output dữ liệu hiện tại: `2` (dấu | ngăn cột, bỏ header). Viết expected từ contract trước khi sửa.

## Cách tái hiện

Kết nối container lab ở bài 01, chạy block bằng sqlcmd với `-b -C -W -h -1 -s "|"`. Ghi engine build, output, lỗi và exit code. Không chạy trên database ứng dụng. Verifier tái hiện bản lỗi; learner phải nộp test bản sửa riêng.

## Acceptance criteria

- Input trên trả 0,Keyboard trả 1, tên chứa dấu nháy được xử lý đúng. SQL text cố định và value truyền bằng parameter; không sửa bằng replace dấu nháy.
- Có test đỏ với bản lỗi, xanh với bản sửa và ít nhất một biên.
- Giải thích nơi code chạy, state trước/sau và cost.
- Giữ diff lỗi và bằng chứng, không chỉ thay expected cho qua.

## Hints

1. sp_executesql có tự biến chuỗi đã concatenate thành parameter không?
2. Trace từng bước theo semantics SQL; không nhầm logical order với physical plan.
3. Chọn sửa nhỏ nhất bảo vệ contract, nêu điều kiện phải xem lại khi scale.

## Checklist điều tra

- [ ] Contract và input tối thiểu.
- [ ] State/output khác expected ở bước nào.
- [ ] Root cause và regression test.
- [ ] Diff, trade-off và giới hạn kiểm chứng.

[Bản đồ](../index.md).
