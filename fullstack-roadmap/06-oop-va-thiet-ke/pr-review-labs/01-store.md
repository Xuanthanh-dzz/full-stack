# PR Review — “Đơn giản hóa đặt hàng”

## Diff

Đọc [patch huấn luyện](./diffs/store.diff). Giả định `Save` có thể ném trước khi lưu, notifier chỉ được gọi khi Save thành công; `MutableOrders` là List nội bộ, `Snapshot` trả bản sao. ID đơn phải có nội dung, tổng tiền phải dương, gọi lại cùng ID không tạo đơn thứ hai; `Cancel` ID không tồn tại trả false. Store hiện chỉ được gọi tuần tự; không suy ra guarantee đồng thời.

## Nhiệm vụ review

Review tính đúng của Place và List theo contract trong bối cảnh. Tự chọn ca gọi lặp, ca collaborator thất bại và ca caller giữ kết quả đọc để kiểm tra. Mỗi finding cần severity, dòng, expected/actual, trace state và regression test. Phân biệt guarantee cho caller tuần tự với yêu cầu mới nếu mở concurrency. Nộp nhận xét trước khi viết diff sửa; không thêm framework/pattern nếu chưa có driver.

## Rubric

Chấm theo contract, bằng chứng, regression và lựa chọn phù hợp quy mô. Trong review, xét correctness, performance, security, maintainability và operability; nếu một nhóm không có finding, ghi lý do thay vì bịa lỗi. Viết review độc lập trước khi mở tiêu chí chi tiết.

<details markdown="1">
<summary>Sau khi nộp lượt review đầu: mở tiêu chí chấm chi tiết</summary>

10 điểm: contract 4, state/failure trace 2, regression evidence 2, lựa chọn vừa quy mô 2. Đạt 8 và không bỏ sót thông báo đơn chưa lưu. Không chấm số thuật ngữ SOLID sử dụng.

</details>

## Submission format

Nộp review.md gồm quyết định approve/request changes, bảng phát hiện và test đề xuất; kèm diff sửa riêng cùng log kiểm tra. Không chỉ dán bản code cuối.

[Bản đồ](../index.md).
