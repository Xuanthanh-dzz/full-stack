# PR Review — Cancellation và permit

Patch huấn luyện độc lập: gate là SemaphoreSlim, ReadAsync nhận token và trả FileResult; Failure tạo kết quả file lỗi. Contract: chỉ lỗi dữ liệu được chuyển thành result; cancellation đi lên caller; chỉ release permit đã acquire. Không áp trực tiếp patch vào capstone.

## Diff

Đọc [batch.diff](./diffs/batch.diff), trace cả token đã cancel trước acquire.

## Nhiệm vụ review

- Phân loại blocker/high/medium/low, dẫn vị trí và state cho mỗi finding.
- Kiểm tra cancellation propagation, acquire/release và exception bị che.
- Viết regression có lịch điều khiển, không dùng sleep để hy vọng race.
- Đánh giá raw exception message ở boundary và policy dữ liệu nhạy cảm.
- So sánh task-per-file với bounded queue cho20file và1triệufile; không thêm kiến trúc khi thiếu driver.

## Rubric

| Nhóm | Điểm |
|---|---:|
| Cancellation đúng trạng thái/token | 30 |
| Permit không release khi acquire lỗi | 30 |
| Error boundary và regression evidence | 20 |
| Scale/ownership judgment | 10 |
| Comment rõ location/severity/smallest fix | 10 |

Đạt80, không bỏ sót hai lỗi lifecycle chính.

## Submission format

Bảng location, severity, problem, impact, evidence, smallest fix, regression. Kết luận approve/request changes; sau review mới nộp diff sửa. [Bản đồ](../index.md).
