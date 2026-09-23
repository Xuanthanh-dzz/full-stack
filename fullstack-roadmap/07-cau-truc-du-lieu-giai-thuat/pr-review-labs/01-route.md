# PR Review — “Tối ưu route bằng BFS”

## Diff

Đọc [diff thật](./diffs/route.diff). Contract: trim tên, từ chối đỉnh không tồn tại, trả route tổng cost thấp nhất với cạnh dương kiểu int. Dijkstra cũ validate endpoints; Route.TotalCost kiểu long. Graph cố định, caller tuần tự. Hàm BFS mới chọn ít cạnh nhất; không giả định nó giữ kiểm tra của hàm bị thay.

## Nhiệm vụ review

Review theo contract về input, kết quả đường đi, trạng thái giữ giữa các lần gọi và cách báo lỗi. Tự dựng graph nhỏ, tính tay route mong muốn rồi trace patch; có ít nhất một chuỗi nhiều lần gọi cùng finder. Mỗi finding cần severity, dòng, expected/actual, state và regression test. Phân biệt lỗi chắc chắn với câu hỏi về yêu cầu. Chỉ đề xuất thuật toán hoặc cache khi giải thích được điều kiện đúng và chi phí.

## Rubric

Chấm theo contract, bằng chứng, regression và lựa chọn phù hợp quy mô. Viết review độc lập trước khi mở tiêu chí chi tiết.

<details markdown="1">
<summary>Sau khi nộp lượt review đầu: mở tiêu chí chấm chi tiết</summary>

10 điểm: correctness 4, boundary 2, regression evidence 2, scale judgment 2. Đạt 8 và không bỏ sót shortest-cost khác fewest-hops. Không chấm thêm framework hoặc cache nếu chưa có driver.

</details>

## Submission format

Nộp review.md gồm approve/request changes, bảng phát hiện và test; kèm diff sửa riêng cùng log. Giữ diff lỗi để người khác tái hiện.

[Bản đồ](../index.md).
