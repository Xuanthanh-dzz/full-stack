# Spaced Review 04 — Index và đồng thời

Sau cụm 16–20; quay lại sau 2 ngày và 1 tuần. Không mở bài ở lượt đầu.

## Retrieval

1. Covering thuộc query hay chỉ index?
2. INCLUDE có tạo key order không?
3. RCSI khác SNAPSHOT về thời điểm nào?
4. Deadlock victim rollback bao nhiêu statement?
5. Ôn graph Module 07: cycle chờ khác đường chờ một chiều thế nào?

## Dự đoán output

1. Stock 5, mua 3 rồi commit; mua 4 thì thiếu: kho/order phải còn gì?
2. A giữ 1 chờ 2, B giữ 2 chờ 1: một victim thì survivor giữ bao nhiêu lần trừ?

## Debug

SELECT OUTPUT đã nhận nhưng COMMIT lỗi: client có nên gửi email thành công không? Nộp input, actual/expected, root cause và test hồi quy.

## Judgment liên module

Query trả 90%table: scan hay ép seek, cần đo gì? Nêu contract, state ở client/server, chi phí và điều kiện phải đổi quyết định.

## Self-score

Retrieval 10 điểm, trace 4, debug 3, judgment 3. Đạt 16/20 và không bỏ sót sai grain/transaction contract. Ghi bài cần ôn rồi kiểm lại bằng ví dụ khác sau 2 ngày.

[Bản đồ](../index.md).
