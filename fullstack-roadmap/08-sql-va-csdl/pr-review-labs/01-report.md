# PR Review — “Report linh hoạt và tránh blocking”

## Diff

Đọc [diff thật](./diffs/report.diff). Contract: trả chỉ OrderId/TotalAmount đã commit của đúng customer và status, theo OrderId. Caller truyền dữ liệu ngoài, không mở transaction trước. ReportRequests(Id,LastUsedAt) có row 1; các request dùng chung row này. Runtime không cần quyền ghi report metadata. Không gửi input thử nghiệm tới DB thật.

## Nhiệm vụ review

Review quyền truy cập, phạm vi dữ liệu, shape/thứ tự kết quả và vòng đời transaction theo contract đã nêu. Tự chọn input thường, input biên và lỗi runtime; trace state của session trước/sau mỗi đường đi. Mỗi finding cần dòng, severity, expected/actual, hậu quả và regression test. Đánh giá riêng thay đổi nghiệp vụ ghi LastUsedAt. Nộp review trước diff sửa; không dùng thêm index như câu trả lời mặc định cho mọi vấn đề.

## Rubric

Chấm theo contract, bằng chứng, regression và lựa chọn phù hợp quy mô. Viết review độc lập trước khi mở tiêu chí chi tiết.

<details markdown="1">
<summary>Sau khi nộp lượt review đầu: mở tiêu chí chấm chi tiết</summary>

10 điểm: quyền và code/data 3, semantics/grain/order 3, transaction/failure 2, test/evidence 2. Đạt 8 và không bỏ sót rò dữ liệu customer hoặc injection. Không chấm bằng số công cụ được thêm.

</details>

## Submission format

Nộp review.md với approve/request changes và findings; diff sửa riêng; SQL fixture và log expected/actual. Giữ bản lỗi để tái hiện trong container riêng.

[Bản đồ](../index.md).
