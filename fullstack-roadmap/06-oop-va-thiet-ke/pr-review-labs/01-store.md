# PR Review — “Đơn giản hóa đặt hàng”

## Diff

Đọc [diff thật](./diffs/store.diff). Giả định Save có thể ném trước khi lưu, notifier chỉ được gọi khi Save thành công; MutableOrders là List nội bộ, Snapshot trả bản sao. Store hiện chỉ được gọi tuần tự; không suy ra guarantee đồng thời.

## Nhiệm vụ review

Review mất duplicate check, nuốt lỗi Save, notification sau thất bại và read-only alias. Ghi severity kèm dòng, failure mode, input tái hiện và sửa tối thiểu. Đánh giá riêng việc Exists/Save vốn chưa atomic khi mở concurrency. Không yêu cầu framework/pattern không có driver.

## Rubric

10điểm: contract4, state/failure trace2, regression evidence2, lựa chọn vừa scale2. Đạt8 và không bỏ sót thông báo đơn chưa lưu. Không chấm số thuật ngữ SOLID sử dụng.

## Submission format

Nộp review.md gồm quyết định approve/request changes, bảng phát hiện và test đề xuất; kèm diff sửa riêng cùng log kiểm tra. Không chỉ dán bản code cuối.

[Bản đồ](../index.md).
