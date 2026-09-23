# Spaced Review — sau bài 15

Không nhìn bài khi retrieval; đối chiếu sau và làm biến thể mới.

## Retrieval

1. Ôn RAII Module 03: cleanup khác rollback thế nào?
2. lock phải bảo vệ cả đọc và ghi ở đâu?
3. Dispose khác GC về lifecycle nào?
4. Span slice khác array range Module 04 thế nào?
5. Covariance/contravariance có tạo object mới không?

## Dự đoán output

1. Hai reader snapshot 0 trước release, cùng ghi+1: cuối là gì?
2. Animal[] chứa Cat[] rồi gán Dog: compile hay runtime lỗi?

## Debug

Parser nhận NaN dù TryParse thành công; viết cận domain và kiểm output trước khi tối ưu.

## Judgment liên module

Batch 100 file hay 1 triệu file: semaphore giới hạn số lượt xử lý cùng lúc ở đâu? Nó có giới hạn số task đang chờ và bộ nhớ dùng cho chúng không?

## Self-score

Retrieval 10, prediction 4, debug 3, judgment 3: tổng 20. Đạt 16 và không nhầm cancellation/ownership thì đi tiếp. Thiếu trace nhận tối đa nửa điểm; dưới 14 quay lại cụm và prerequisite được hỏi, rồi làm ví dụ mới. [Bản đồ](../index.md).
