# Spaced Review 05 — Performance, testing và architecture judgment (bài 21–24)

## Retrieval

1. `AsNoTracking` tối ưu cost nào?
2. `ExecuteUpdate` bypass những gì?
3. Vì sao SQLite test chưa chứng minh SQL Server behavior?
4. Generic Repository thường duplicate/leak EF semantics thế nào?
5. Khi query chậm, thứ tự điều tra thực dụng là gì?

## Dự đoán behavior

1. `ExecuteUpdate` sửa row mà context đang track. Entity tracked có tự sync không?
2. Một query compile nhanh nhưng SQL scan 20 triệu row. Compiled query có giải quyết bottleneck không?

## Debug

Test suite dùng mock `DbSet`, mọi test xanh nhưng production query fail translation. Thiết kế lại test pyramid.

## Judgment liên module

Team 3 người, 50 request/s, một SQL Server. Chọn `DbContext + application service` hay Generic Repository + CQRS + microservice? Ghi 5 dòng ADR với driver, alternative và trigger để revisit.

## Interleaving Module 07–09

Bạn cần top SKU bán chạy rồi kiểm tra chúng có thuộc blacklist 50.000 SKU. Chọn phần nào SQL aggregate/index, phần nào HashSet C#. Giải thích data locality và Big-O.

## Self-score

- 9–10/10: làm Career Checkpoint.
- 7–8/10: làm Failure Lab 04 + PR Review Lab.
- dưới 7/10: quay lại capstone 24 và viết lại reasoning document trước khi checkpoint.
