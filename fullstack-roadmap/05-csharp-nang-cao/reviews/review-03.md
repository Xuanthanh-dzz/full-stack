# Spaced Review — sau bài 15

Không nhìn bài khi retrieval; đối chiếu sau và làm biến thể mới.

## Retrieval

1. Ôn RAII Module03: cleanup khác rollback thế nào?
2. lock phải bảo vệ cả đọc và ghi ở đâu?
3. Dispose khác GC về lifecycle nào?
4. Span slice khác array range Module04 thế nào?
5. Covariance/contravariance có tạo object mới không?

## Dự đoán output

1. Hai reader snapshot0 trước release, cùng ghi+1: cuối là gì?
2. Animal[] chứa Cat[] rồi gán Dog: compile hay runtime lỗi?

## Debug

Parser nhận NaN dù TryParse thành công; viết cận domain và kiểm output trước khi tối ưu.

## Judgment liên module

Batch100file hay1triệufile: semaphore giải quyết capacity nào, không giải quyết memory nào?

## Self-score

Retrieval10, prediction4, debug3, judgment3: tổng20. Đạt16 và không nhầm cancellation/ownership thì đi tiếp. Thiếu trace nhận tối đa nửa điểm; dưới14 quay lại cụm và prerequisite được hỏi, rồi làm ví dụ mới. [Bản đồ](../index.md).
