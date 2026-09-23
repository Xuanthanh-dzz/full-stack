# Spaced Review 03 — Query có tên và mô hình

Sau cụm 11–15; quay lại sau 2 ngày và 1 tuần. Không mở bài ở lượt đầu.

## Retrieval

1. CTE có sống qua statement tiếp không?
2. ROW_NUMBER khác RANK theo tie gì?
3. Trigger nhận một row hay rowset?
4. FK có buộc cha có con không?
5. Ôn Module 06: snapshot lịch sử thuộc owner nào?

## Dự đoán output

1. Amounts 100, 90, 90: RANK<=2 trả bao nhiêu row?
2. Cây 1 → 2 → 3: depths và số row từ anchor 1?

## Debug

Trigger lấy biến scalar từ inserted khi UPDATE nhiều row; nêu test audit mất dữ liệu. Nộp input, actual/expected, root cause và test hồi quy.

## Judgment liên module

Schema có surrogate key nhưng CustomerName lặp theo CustomerId: đã 3NF chưa? Nêu contract, state ở client/server, chi phí và điều kiện phải đổi quyết định.

## Self-score

Retrieval 10 điểm, trace 4, debug 3, judgment 3. Đạt 16/20 và không bỏ sót sai grain/transaction contract. Ghi bài cần ôn rồi kiểm lại bằng ví dụ khác sau 2 ngày.

[Bản đồ](../index.md).
