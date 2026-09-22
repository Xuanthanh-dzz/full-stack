# Career Checkpoint — C# Foundation

Sau Module05. Mục tiêu: tự xây/debug/test một ứng dụng C# vừa, giải thích state, async, cancellation và resource mà không copy tutorial. Đây là đánh giá người học; CI samples không tự chứng nhận năng lực nghề nghiệp.

## 1. Knowledge test — không nhìn tài liệu

1. Copy struct khác copy reference class thế nào?
2. Nullable annotation khác runtime guard ở đâu?
3. Delegate giữ target và closure sống theo đường nào?
4. Event handler ném sau commit có rollback không?
5. Record with copy container và element ra sao?
6. Vì sao Task không phải thread?
7. Phần nào của async method chạy trước incomplete await?
8. Timeout chờ khác cancellation operation thế nào?
9. Khi nào semaphore được release?
10. Dispose khác GC về trách nhiệm nào?
11. Span slice khác array range ở copy/lifetime nào?
12. Variance producer/consumer có hướng gì?
13. Expression tree Compile khác translation thế nào?
14. JSON required khác domain validation ở đâu?
15. B/op thread-local không đo được những gì?

## 2. Build task

Trong120–180phút, được tra docs nhưng không chép capstone: xây CLI import phiếu chi từ danh sách JSON. Mỗi phiếu có ID, amount không âm và currency; chỉ tổng hợp cùng currency. Batch20–200file trên một máy, một writer, tối đa3file mở đồng thời. In kết quả theo filename, trả exit1 khi có input lỗi, cancellation đi lên boundary. Ghi report qua file tạm và giữ report cũ khi lỗi trước commit. Không yêu cầu database/web/container DI.

Acceptance: build warnings-as-errors, fixture có valid/invalid/null/overflow, kiểm thứ tự/tổng/exit, token truyền tới I/O, dispose sau work hoàn tất. Nộp README, source, tests, report mẫu, SDK và trace task/resource/state. Nêu giới hạn filename trùng, file lớn và crash durability.

## 3. Debugging task

Chọn hai lab từ hai cụm khác nhau: [capture](../failure-labs/01-capture.md), [timeout](../failure-labs/02-timeout.md), [dispose](../failure-labs/03-dispose.md), [cancel](../failure-labs/04-cancel.md).

Nộp hypothesis, evidence, root cause, smallest fix, regression và metric/log cần theo dõi. Test phải fail ở bản lỗi; không dùng delay ngẫu nhiên làm bằng chứng correctness.

## 4. PR review

Review [batch patch](../pr-review-labs/01-batch.md). Phải phát hiện cancellation bị che và release khi chưa acquire; mỗi finding có severity/location/impact/evidence/fix/test. Không bù lỗi correctness bằng nhiều comment style.

## 5. Judgment task

Viết quyết định một trang cho hai scale:200file mỗi tối và1triệufile liên tục. Nêu giới hạn active I/O, pending tasks, payload memory, failure policy và durability. Chọn giải pháp nhỏ nhất đủ scale; nếu thêm bounded queue/database phải có driver. Phân biệt cải thiện cần làm ngay với trigger đo được để xem xét lại.

## 6. Interview explanation

Giải thích miệng3–5phút mỗi câu: vì sao await không giữ thread ngồi chờ; vì sao timeout chưa dừng work; vì sao record chưa deep immutable; vì sao GC không thay Dispose. Dùng sơ đồ và một phản ví dụ, không chỉ đọc định nghĩa.

## 7. Competency matrix

| Năng lực | Điểm | Bằng chứng đạt |
|---|---:|---|
| Kiểu/reference/nullable | 15 | knowledge và graph đúng |
| Delegate/closure/event | 10 | debug capture/lifecycle |
| Async/cancellation | 20 | task status, token và boundary |
| Ownership/resource | 15 | acquire/release, cleanup đường lỗi |
| JSON/correctness | 15 | fixture và report đúng |
| Debug/PR review | 15 | root cause và test bắt lỗi gốc |
| Judgment/explanation | 10 | scale/cost/driver rõ |

Đạt từ80/100 và không còn lỗi nghiêm trọng về cancellation, permit, resource ownership hoặc mất report cũ. Reviewer ghi ngày, commit, môi trường và rubric; điểm build đơn thuần không đủ đạt checkpoint.

## 8. Remediation map

| Thiếu năng lực | Ôn lại | Làm lại |
|---|---|---|
| Nhầm copy/alias/null | Module04 bài05–08; Module05 bài06–07 | graph và input null |
| Callback giữ state sai | bài02–04 | capture lab biến thể |
| Timeout/cancel/thread | bài09–11 | controlled completion và pre-cancel |
| Cleanup/permit | bài11–12,19 | lỗi trước/sau acquire |
| JSON/domain | bài17,19 | missing/unknown/negative fixture |
| Đo lường/judgment | bài14,18 | correctness trước benchmark |

Sau ôn, làm biến thể mới sau ít nhất một buổi học khác rồi chấm lại cùng rubric. [Bản đồ Module05](../index.md).
