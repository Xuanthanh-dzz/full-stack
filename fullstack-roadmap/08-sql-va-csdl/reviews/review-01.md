# Spaced Review 01 — Dữ liệu, NULL và predicate

Sau cụm 01–05; quay lại sau 2 ngày và 1 tuần. Không mở bài ở lượt đầu.

## Retrieval

1. GO chạy ở đâu?
2. CHECK nhận UNKNOWN không?
3. DEFAULT có thay NULL tường minh không?
4. Tiebreaker có tạo snapshot xuyên request không?
5. Ôn Module 06: guard C# bảo vệ được mọi writer DB không?

## Dự đoán output

1. Values NULL,0,2: WHERE value<>0 giữ row nào?
2. Page size 2 trên giá 100,100,90: thiếu ID tiebreaker làm mơ hồ gì?

## Debug

UPDATE không WHERE sửa cả table; nêu cách kiểm affected rows và boundary. Nộp input, actual/expected, root cause và test hồi quy.

## Judgment liên module

20 mục cho một tool cá nhân cần SQL Server hay file đã đủ? Nêu contract, state ở client/server, chi phí và điều kiện phải đổi quyết định.

## Self-score

Retrieval10 điểm, trace4, debug3, judgment3. Đạt16/20 và không bỏ sót sai grain/transaction contract. Ghi bài cần ôn rồi kiểm lại bằng ví dụ khác sau 2 ngày.

[Bản đồ](../index.md).
