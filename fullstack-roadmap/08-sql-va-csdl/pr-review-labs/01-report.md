# PR Review — “Report linh hoạt và tránh blocking”

## Diff

Đọc [diff thật](./diffs/report.diff). Contract: trả chỉ OrderId/TotalAmount đã commit của đúng customer và status, theo OrderId. Caller truyền dữ liệu ngoài, không mở transaction trước. ReportRequests(Id,LastUsedAt) có row1; các request dùng chung row này. Runtime không cần quyền ghi report metadata. Không gửi input thử nghiệm tới DB thật.

## Nhiệm vụ review

Tìm ít nhất6nhóm lỗi: mất customer predicate, concatenate input, NOLOCK đổi consistency, SELECT* đổi shape, mất ORDER BY, ghi/giữ lock metadata trong transaction chờ10giây, và thiếu cleanup transaction khi dynamic SQL lỗi. Mỗi finding cần dòng, severity, input, state/failure mode và sửa tối thiểu. Đánh giá riêng nhu cầu ghi LastUsedAt; không đề xuất thêm index để che mất filter.

## Rubric

10 điểm: quyền và code/data3, semantics/grain/order3, transaction/failure2, test/evidence2. Đạt8 và không bỏ sót rò dữ liệu customer hoặc injection. Không chấm bằng số công cụ được thêm.

## Submission format

Nộp review.md với approve/request changes và findings; diff sửa riêng; SQL fixture và log expected/actual. Giữ bản lỗi để tái hiện trong container riêng.

[Bản đồ](../index.md).
