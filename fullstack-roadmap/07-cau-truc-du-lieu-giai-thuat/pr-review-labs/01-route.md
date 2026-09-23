# PR Review — “Tối ưu route bằng BFS”

## Diff

Đọc [diff thật](./diffs/route.diff). Contract: trim tên, từ chối đỉnh không tồn tại, trả route tổng cost thấp nhất với cạnh dương kiểu int. Dijkstra cũ validate endpoints; Route.TotalCost kiểu long. Graph cố định, caller tuần tự. Hàm BFS mới chọn ít cạnh nhất; không giả định nó giữ kiểm tra của hàm bị thay.

## Nhiệm vụ review

Đánh giá mất normalization, thu hẹp distance, early return cho đỉnh chưa tồn tại đổi đại lượng tối ưu, cache thiếu target và nuốt exception thành route “thành công”. Có sáu nhóm lỗi cần phân biệt. Dựng graph3 đỉnh có đường trực tiếp đắt hơn đường2cạnh. Mỗi finding ghi severity, dòng, input, actual/expected và sửa nhỏ nhất. Nêu điều kiện riêng khiến BFS hợp lệ.

## Rubric

10 điểm: correctness4, boundary2, regression evidence2, scale judgment2. Đạt8 và không bỏ sót shortest-cost khác fewest-hops. Không chấm thêm framework hoặc cache nếu chưa có driver.

## Submission format

Nộp review.md gồm approve/request changes, bảng phát hiện và test; kèm diff sửa riêng cùng log. Giữ diff lỗi để người khác tái hiện.

[Bản đồ](../index.md).
