# Spaced Review 04 — Loading, concurrency và raw SQL (bài 16–20)

## Retrieval

1. Eager, explicit và lazy loading khác nhau ở thời điểm I/O nào?
2. N+1 và cartesian explosion là hai failure mode khác nhau thế nào?
3. Optimistic concurrency token hoạt động qua `WHERE` update ra sao?
4. Global query filter có phải authorization boundary không?
5. Khi nào raw SQL là escape hatch hợp lý?

## Dự đoán behavior

1. 100 Orders × 20 Items × 5 Payments có thể tạo bao nhiêu joined rows trước deduplication?
2. Hai context load cùng token; context A save trước, context B save sau. Điều gì xảy ra nếu token được cấu hình đúng?

## Debug

Fix N+1 bằng hai collection `Include` làm endpoint chậm hơn. Bạn sẽ đo gì trước khi chọn projection hoặc split query?

## Judgment liên module

Inventory contention cao: atomic conditional UPDATE, optimistic token, serializable transaction hay distributed lock? Nêu driver và giải pháp nhỏ nhất đủ tốt.

## Ôn Module trước

- Module 08: transaction/isolation/deadlock.
- Module 07: cardinality/complexity reasoning.

## Self-score

- 9–10/10: tiếp tục.
- 7–8/10: làm Failure Lab 03.
- dưới 7/10: ôn bài 16–20 và chạy lại SQL logging lab.
