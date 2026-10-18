# Spaced Review 02 — Execution boundaries (bài 06–10)

## Retrieval

1. Deferred execution khác materialization thế nào?
2. `AsEnumerable()` có execute query ngay không?
3. `IQueryable<T>` mang thêm gì so với `IEnumerable<T>`?
4. Expression tree khác delegate ở điểm nào?
5. Multiple enumeration gây loại cost nào?

## Dự đoán output / SQL

1. Một source log khi enumerate; query gọi `Count()` rồi `ToList()`. Source chạy mấy lần?
2. EF query gọi `AsEnumerable()` trước `Where(Helper)`. Predicate nào còn nằm trong generated SQL?

## Debug

Endpoint dev chạy nhanh nhưng production memory tăng vì helper không translate và filter chạy client-side. Liệt kê evidence bạn cần trước khi sửa.

## Judgment liên module

Normalization SKU nên chạy ở C#, computed/normalized column SQL, hay search engine? Đưa ra decision tree theo volume và query frequency.

## Ôn Module trước

- Module 07: HashSet vs nested scan.
- Module 08: SARGability và index.

## Self-score

- 9–10/10: tiếp tục.
- 7–8/10: làm lại bài 07–10.
- dưới 7/10: làm Failure Lab 01 và 02 trước khi sang EF Core.
