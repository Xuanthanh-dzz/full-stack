# Checkpoint review chất lượng Module 01–08

Ngày bắt đầu: 2026-09-23. Reviewer: Codex, lượt rà soát hỗ trợ maintainer. Baseline trước review: commit `7ca0a09`. Kết luận hiện tại: **REQUEST CHANGES — chưa phê duyệt toàn bộ nội dung**.

Đây là evidence review nội dung, không phải kết quả học thử của người mới và không thay chữ ký phê duyệt của maintainer. Completion giữ 164/421; chưa mở Module 10.

## Phạm vi đã đọc và kết luận

| Phạm vi | Evidence đã xem | Kết luận |
|---|---|---|
| PR Review Module 01–08 | Toàn bộ 8 đề, rubric và 8 patch | Đã sửa độ rộng, cách hỏi và rubric; 8 patch đọc được bằng `git apply --numstat`. Chưa có bài nộp thật của người học. |
| Spaced Review Module 01–08 | Đã rà prompt/format của 28 checkpoint; sửa câu dính chữ/số ở Module 04–08 | Có retrieval, trace, debug và judgment; chưa thử với người mới để kiểm tra mức khó. |
| Failure Labs Module 01–08 | Đã rà context/triệu chứng/acceptance của 28 lab và chỉnh lỗi trình bày thấy được | Mô tả đủ đường tái hiện và tiêu chí đầu ra; chưa kiểm thử độc lập bản sửa do người học nộp. |
| Career Checkpoint Module 05 | Toàn bộ đề và competency matrix | Đủ nhóm task, thiếu mô tả ba mức năng lực; đã bổ sung. |
| 137 bài chính | Đã đối chiếu tóm tắt ví dụ nhỏ và walkthrough theo tuyến module; đã xem sâu Module 01, câu hỏi Module 07 và ví dụ mở đầu Module 08. Verifier có kiểm cấu trúc toàn bộ 137 bài. | Chưa tự trace và đánh giá prerequisite/retrieval/judgment của từng bài; không suy PASS nội dung từ verifier hoặc lần authoring trước. |

## Findings đã xử lý trong lượt đầu

| ID | Mức | Evidence trước sửa | Tác động | Thay đổi |
|---|---|---|---|---|
| R01 | High | Mục nhiệm vụ PR Module 02–08 gọi tên trực tiếp phần lớn lỗi; Module 06–08 gần như liệt kê đáp án. | Người học có thể lặp lại danh sách mà không tự phát hiện failure mode; bài đánh giá yếu hơn mục tiêu review độc lập. | Đổi sang contract, scenario và yêu cầu evidence; đưa rubric chi tiết vào phần mở sau lượt review đầu. Không sửa lỗi cố ý trong patch. |
| R03 | Medium | Career Checkpoint Module 05 có điểm và cột evidence đạt, chưa mô tả Chưa đạt/Đạt/Vững. | Reviewer khó phân biệt hoàn thành task đã thấy với chuyển giao kỹ năng sang biến thể mới. | Thêm ba mức có hành vi quan sát được, yêu cầu evidence từng năng lực và điều kiện chặn khi còn lỗi nghiêm trọng. |
| R04 | High | PR patch Module 02–06 trước đó chỉ có 2–4 vấn đề độc lập ở mỗi patch. | Người học khó luyện phân loại issue và review theo nhiều nhóm. | Mở rộng từng patch thành ít nhất 6 root cause độc lập, bổ sung contract; cả 8 rubric nay yêu cầu xét correctness/performance/security/maintainability/operability. Không buộc bịa finding ở nhóm không có lỗi. |
| R05 | Medium | Nhiều câu trong Failure Lab/Spaced Review/PR Lab và career checkpoint dính số và từ, ví dụ `20file`, `Retrieval10điểm`, `Top2`. | Khó đọc và tăng tải nhận thức không cần thiết. | Biên tập các câu đã phát hiện; giữ identifier và baseline. Kiểm lại bằng tìm kiếm ngoài code fence/inline code. |
| R07 | Medium | Nhiều ví dụ/câu hỏi bài chính Module 07–08 nén số và thuật ngữ, ví dụ `Coins[1,3,4],amount 6`, `Customers An,Bình,Chi; Orders101/102`, `Stock 1=99,Stock 2=100`. | Người mới khó tính tay và đối chiếu state với walkthrough; dấu nối chữ/số che contract. | Viết lại các câu phát hiện trong 19 bài Module 07 và 25 bài Module 08, tách input, bước và output. Sửa riêng ví dụ capstone Module 08 để phân biệt trạng thái đơn, dòng hàng và payment intent. Không đổi code/SQL sample. |

Ghi chú kiểm chứng: nghi vấn escape trong patch C Module 01 đã được loại bỏ sau kiểm tra ký tự nguồn; newline/NUL vốn đúng và file không thay đổi. Không tính nghi vấn này là finding.

## Findings còn mở — cần review trước phê duyệt

1. **R06 — High, độ sâu của bài chính chưa được chứng nhận.** Cần đọc đủ 137 bài cùng bài liền trước/liền sau, tự tính worked example và trace sample, rồi đối chiếu retrieval/judgment với prerequisite. Lượt này đã so tuyến Module 01 theo bài 01–15 và đọc tóm tắt ví dụ/trace của các module khác; chưa có review sâu tương ứng cho Module 02–08. Không biến checklist tự sinh thành chứng nhận chất lượng.
2. **G01 — CI phải khớp commit đang xét.** Chín workflow của commit review `576a567` đã PASS trên GitHub: [Module 01](https://github.com/Xuanthanh-dzz/full-stack/actions/runs/35831857887), [02](https://github.com/Xuanthanh-dzz/full-stack/actions/runs/35831857919), [03](https://github.com/Xuanthanh-dzz/full-stack/actions/runs/35831857856), [04](https://github.com/Xuanthanh-dzz/full-stack/actions/runs/35831857833), [05](https://github.com/Xuanthanh-dzz/full-stack/actions/runs/35831857869), [06](https://github.com/Xuanthanh-dzz/full-stack/actions/runs/35831857930), [07](https://github.com/Xuanthanh-dzz/full-stack/actions/runs/35831857884), [08](https://github.com/Xuanthanh-dzz/full-stack/actions/runs/35831857901), [09](https://github.com/Xuanthanh-dzz/full-stack/actions/runs/35831857818). Bản prose Module 07–08 tiếp theo đã qua verifier 07/08, MkDocs strict và diff check local; cần xem [CI của HEAD trên nhánh](https://github.com/Xuanthanh-dzz/full-stack/actions?query=branch%3Aretrofit%2Fmodules-01-08-v4) sau khi đẩy. Maintainer chưa ký duyệt.

### Evidence riêng cho R04

| Module | Vấn đề độc lập có thể tái hiện trong patch sau sửa |
|---|---|
| 02 | mất owner khi `realloc` lỗi; `count` bị gán bằng capacity; free phần tử trong mảng; xóa kho cũ trước khi load thành công; so mã bằng prefix; bỏ qua lỗi `fclose`. |
| 03 | nhận ID trùng; dereference owner sau move; xóa danh mục trước parse; tra ID bằng prefix; comparator `<=` sai contract sắp xếp; gọi `remove_if` nhưng không erase. |
| 04 | sửa object bị alias trong bản copy list; publish state trước Save; parse sai input bằng exception; trả reference tới list mutable; nhận ID trùng; báo xóa thành công khi ID không có. |
| 05 | release permit chưa acquire; bỏ token khi đọc; `catch` quá rộng (gồm cancellation và lỗi I/O); lộ exception message; tạo task cho toàn bộ input trước khi giới hạn số lượng; đảo thứ tự result. |
| 06 | bỏ kiểm ID rỗng; bỏ kiểm tổng tiền dương; nhận ID trùng; nuốt lỗi Save khiến gửi thông báo dù chưa lưu; trả list nội bộ mutable; báo Cancel thành công với ID không có. |

Mỗi hàng đếm root cause riêng, không tách một lỗi thành nhiều cách diễn đạt. Patch là fixture cố ý sai nên không được áp lên sample đang chạy.

### Evidence review bài chính đã làm trong checkpoint này

Module 01: đọc ví dụ nhỏ, walkthrough, prerequisites, judgment và retrieval của cả 15 bài theo thứ tự. Kiểm tay các ví dụ có số/biên nổi bật: bài 01 `2 × 5 = 10` và khi đổi số lượng thành 3 là 15 (sample cố ý chỉ in chuỗi, bài nói rõ); bài 03 `2 / 3` chia nguyên bằng 0; bài 11 tổng `[5, 2, 8]` là 15 và index 3 ngoài mảng; bài 13 `"An"` cần 3 slot kể cả NUL. Các bài judgment hỏi chọn ranh giới hoặc giải pháp nhỏ theo quy mô, không buộc dùng cú pháp module sau. Đây là lượt soát ví dụ/tuyến học, chưa phải learner trial; code chính có evidence verifier/CI baseline trong `PROGRESS.md`.

Module 02–08: đã đối chiếu tiêu đề, ví dụ nhỏ và các bước walkthrough để tìm mâu thuẫn rõ, cùng judgment/retrieval của nhiều bài. Ca kiểm tay tiêu biểu: Module 02 `[2, 5, 1]` cộng thành 8 và kho cũ `[A:2]` phải còn khi load hỏng; Module 03 VAT của 200 ở 8% là 16, tổng 216; Module 04 `749701.50 - 74970.15 = 674731.35`; Module 05 hai giá 3 và 2 hoàn tất ngược thứ tự vẫn cộng 5, thuế 0.5; Module 06 `2 × 750000 + 350000 = 1850000`; Module 07 coin `[1,3,4]` với amount 6 cần hai đồng 3, greedy 4+1+1 dùng ba; Module 08 `COUNT(*)=2`, `COUNT(WeightKg)=1` và `AVG=0.095` khi có NULL và 0.095. Các phép thử này không đại diện cho mọi nhánh của 137 bài; chưa đọc sâu toàn bộ phần cơ chế, bài tập và prerequisite từng bài. Cần tiếp tục từ Module 02, ghi evidence cùng finding theo bài khi có lỗi thực tế.

Lượt biên tập tiếp theo: rà bài liền trước/liền sau và ví dụ/câu hỏi Module 07–08; sửa R07 trong 44 bài. Phép đối chiếu riêng: Dijkstra ở Module 07 bài 12 cho A→C→D bằng 2, B có đường tốt hơn qua C bằng 3 nên entry B(4) cũ; Module 08 bài 07 có `(3 + 4,5) / 2 = 3,75` triệu, bài 08 có 3 row inner/4 row left/6 row cross, bài 12 có tổng lũy kế 1/4/7 và rank hòa 1/1/3, bài 19 rollback đơn khi kho 5 nhưng đặt 10, bài 25 ghi đơn và payment intent `Pending` chứ không chứng nhận thu tiền. Đây là soát câu và phép tính cục bộ, chưa đóng R06.

## Quy trình review từng module

1. Đọc theo thứ tự bài; ghi prerequisite, thuật ngữ lần đầu và kiến thức chưa được giới thiệu.
2. Tự giải ví dụ nhỏ trước khi đọc code; trace một ca thường và một ca biên qua state trung gian.
3. Đối chiếu lời giải thích với code: nơi chạy, ownership/lifetime, dữ liệu vào/ra và cost. Tách mô hình đơn giản hóa khỏi guarantee thực tế.
4. Thử làm retrieval/judgment mà không dùng kiến thức module sau; đánh giá hints và rubric bằng một câu trả lời đúng nhưng khác sample.
5. Review labs, spaced reviews và capstone theo cùng contract. Sửa finding, chạy gate thích hợp; không cập nhật Last verified cho sample không chạy lại.
6. Nộp evidence từng module: finding đóng/mở, diff sửa, test/CI, giới hạn và đề xuất approve/request changes. Maintainer quyết định sign-off sau review.

## Điều kiện đóng checkpoint

Cần đủ evidence cho cả 137 bài và artifact bổ trợ; không còn finding High chưa giải quyết; CI phù hợp thay đổi qua; maintainer ghi quyết định và commit được duyệt. Một lượt AI tự kiểm hay bảng điểm tự sinh không được coi là thử nghiệm người mới.

[Tiến độ và trạng thái phê duyệt](../PROGRESS.md).

## Kiểm tra sau sửa lượt đầu

Gate cấu trúc/liên kết/cadence của cả 8 module qua; 10 regression tests qua; MkDocs strict qua bằng `/tmp/fullstack-docs-v4-venv`; `git apply --numstat` đọc được cả 8 patch, `git diff --check` sạch. Lệnh `python -m mkdocs` với Python hệ thống không chạy vì chưa cài MkDocs; đã chạy lại bằng venv có sẵn và qua. Chín workflow của `576a567` đều PASS. Sau sửa prose Module 07–08, verifier của hai module, MkDocs strict và diff check local đều qua; sample runtime không đổi, `Last verified` giữ nguyên. Kết quả CI của commit chứa prose được theo dõi riêng theo đúng SHA.
