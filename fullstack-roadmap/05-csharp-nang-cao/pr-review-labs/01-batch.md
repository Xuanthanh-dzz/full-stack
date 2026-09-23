# PR Review — Cancellation và permit

Patch huấn luyện độc lập: `gate` là `SemaphoreSlim`, `ReadAsync` nhận token và trả `FileResult`; `Failure` tạo kết quả file lỗi. Contract: chỉ lỗi dữ liệu được chuyển thành result với thông báo an toàn cho caller; cancellation đi lên caller; chỉ release permit đã acquire. Batch có thể từ 20 tới một triệu file. Không áp trực tiếp patch vào capstone.

## Diff

Đọc [batch.diff](./diffs/batch.diff), trace cả token đã cancel trước acquire.

## Nhiệm vụ review

- Review cả đường thành công, lỗi dữ liệu, lỗi I/O và yêu cầu hủy ở các thời điểm khác nhau.
- Vẽ trạng thái task, token và quyền sử dụng tài nguyên qua từng nhánh; tự chỉ ra contract nào bị vi phạm.
- Mỗi finding cần severity, location, impact, evidence và sửa nhỏ nhất.
- Đề xuất regression có lịch điều khiển, không dùng sleep ngẫu nhiên để hy vọng gặp lỗi.
- Xem xét dữ liệu được trả qua error boundary và chi phí của task-per-file ở 20 file so với một triệu file.

## Rubric

Chấm theo contract, bằng chứng, regression và lựa chọn phù hợp quy mô. Trong review, xét correctness, performance, security, maintainability và operability; nếu một nhóm không có finding, ghi lý do thay vì bịa lỗi. Viết review độc lập trước khi mở tiêu chí chi tiết.

<details markdown="1">
<summary>Sau khi nộp lượt review đầu: mở tiêu chí chấm chi tiết</summary>

| Nhóm | Điểm |
|---|---:|
| Cancellation đúng trạng thái/token | 25 |
| Permit và failure boundary | 25 |
| Thông báo lỗi và regression evidence | 20 |
| Scale/ownership judgment | 20 |
| Comment rõ location/severity/smallest fix | 10 |

Đạt 80, không bỏ sót hai lỗi lifecycle chính.

</details>

## Submission format

Bảng location, severity, problem, impact, evidence, smallest fix, regression. Kết luận approve/request changes; sau review mới nộp diff sửa. [Bản đồ](../index.md).
