# Career Checkpoint — C# Foundation

Sau Module 05. Mục tiêu: tự xây, debug và test một ứng dụng C# vừa; giải thích state, async, cancellation và resource mà không copy tutorial. Đây là đánh giá người học; CI samples không tự chứng nhận năng lực nghề nghiệp.

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

Trong 120–180 phút, được tra tài liệu nhưng không chép capstone: xây CLI import phiếu chi từ danh sách JSON. Mỗi phiếu có ID, amount không âm và currency; chỉ tổng hợp cùng currency. Batch 20–200 file trên một máy, một writer, tối đa 3 file mở đồng thời. In kết quả theo filename, trả exit code 1 khi có input lỗi, cancellation đi lên boundary. Ghi report qua file tạm và giữ report cũ khi lỗi trước commit. Không yêu cầu database, web hoặc container DI.

Acceptance: build warnings-as-errors, fixture có valid/invalid/null/overflow, kiểm thứ tự/tổng/exit, token truyền tới I/O, dispose sau work hoàn tất. Nộp README, source, tests, report mẫu, SDK và trace task/resource/state. Nêu giới hạn filename trùng, file lớn và crash durability.

## 3. Debugging task

Chọn hai lab từ hai cụm khác nhau: [capture](../failure-labs/01-capture.md), [timeout](../failure-labs/02-timeout.md), [dispose](../failure-labs/03-dispose.md), [cancel](../failure-labs/04-cancel.md).

Nộp hypothesis, evidence, root cause, smallest fix, regression và metric/log cần theo dõi. Test phải fail ở bản lỗi; không dùng delay ngẫu nhiên làm bằng chứng correctness.

## 4. PR review

Review [batch patch](../pr-review-labs/01-batch.md). Mỗi finding có severity/location/impact/evidence/fix/test; tự suy ra lỗi từ contract và trace trước khi xem hướng dẫn chấm. Không bù lỗi correctness bằng nhiều comment style.

## 5. Judgment task

Viết quyết định một trang cho hai quy mô: 200 file mỗi tối và 1 triệu file liên tục. Nêu giới hạn I/O đang chạy, task đang chờ, bộ nhớ payload, chính sách lỗi và độ bền dữ liệu. Chọn giải pháp nhỏ nhất đủ quy mô; nếu thêm bounded queue hoặc database phải có driver. Phân biệt cải thiện cần làm ngay với trigger đo được để xem xét lại.

## 6. Interview explanation

Giải thích miệng 3–5 phút mỗi câu: vì sao await không giữ thread ngồi chờ; vì sao timeout chưa dừng work; vì sao record chưa bất biến sâu; vì sao GC không thay Dispose. Dùng sơ đồ và một phản ví dụ, không chỉ đọc định nghĩa.

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

Đạt từ 80/100 và không còn lỗi nghiêm trọng về cancellation, permit, resource ownership hoặc mất report cũ. Reviewer ghi ngày, commit, môi trường và rubric; điểm build đơn thuần không đủ đạt checkpoint.

### Ba mức năng lực — ghi riêng cho từng hàng

Điểm tổng không thay thế đánh giá từng năng lực. Reviewer ghi mức và link evidence cho từng hàng trong matrix ở trên:

| Mức | Biểu hiện quan sát được |
|---|---|
| Chưa đạt | Chưa giải thích đúng state/contract hoặc chưa hoàn thành task đúng; test không bắt được lỗi gốc, cần người khác chỉ ra bước sửa. |
| Đạt | Tự hoàn thành task trong quy mô đã cho; giải thích execution/state/cost, có test biên và đường lỗi; biết giới hạn của giải pháp. |
| Vững | Đạt các yêu cầu trên và giải được biến thể chưa thấy; tự tạo phản ví dụ, chọn giải pháp đơn giản theo scale, giải thích trade-off và chuyển kiến thức sang tình huống khác. |

Không suy mức Vững chỉ từ tốc độ làm bài hoặc điểm knowledge test. Với cancellation, ownership và tính toàn vẹn report, mức Chưa đạt vẫn chặn checkpoint dù điểm tổng vượt ngưỡng. Lưu bảng `năng lực | mức | evidence | bài cần ôn | ngày kiểm lại` cùng submission.

## 8. Remediation map

| Thiếu năng lực | Ôn lại | Làm lại |
|---|---|---|
| Nhầm copy/alias/null | Module 04 bài 05–08; Module 05 bài 06–07 | graph và input null |
| Callback giữ state sai | bài 02–04 | capture lab biến thể |
| Timeout/cancel/thread | bài 09–11 | controlled completion và pre-cancel |
| Cleanup/permit | bài 11–12, 19 | lỗi trước/sau acquire |
| JSON/domain | bài 17, 19 | missing/unknown/negative fixture |
| Đo lường/judgment | bài 14, 18 | correctness trước benchmark |

Sau ôn, làm biến thể mới sau ít nhất một buổi học khác rồi chấm lại cùng rubric. [Bản đồ Module 05](../index.md).
