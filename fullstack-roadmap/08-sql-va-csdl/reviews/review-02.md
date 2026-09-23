# Spaced Review 02 — Grain và cardinality

Sau cụm 06–10; quay lại sau 2 ngày và 1 tuần. Không mở bài ở lượt đầu.

## Retrieval

1. COUNT(*) khác COUNT(column) khi nào?
2. ON khác WHERE với LEFT JOIN ra sao?
3. EXISTS có nhân row theo child không?
4. EXCEPT có kiểm multiplicity không?
5. Ôn HashSet Module 07: equality do ai quyết định?

## Dự đoán output

1. An có 2 orders,Bình0: LEFT JOIN có mấy row?
2. A=[1,1],B=[1]: UNION ALL và EXCEPT hai chiều ra sao?

## Debug

SUM(order.Total) sau join2payment attempts bị gấp đôi; vẽ grain trước sửa. Nộp input, actual/expected, root cause và test hồi quy.

## Judgment liên module

Report chỉ hỏi có Paid order: EXISTS hay JOIN+DISTINCT, giải thích shape. Nêu contract, state ở client/server, chi phí và điều kiện phải đổi quyết định.

## Self-score

Retrieval10 điểm, trace4, debug3, judgment3. Đạt16/20 và không bỏ sót sai grain/transaction contract. Ghi bài cần ôn rồi kiểm lại bằng ví dụ khác sau 2 ngày.

[Bản đồ](../index.md).
