Tiếp tục viết bộ tài liệu trong `fullstack-roadmap/`. Đây là prompt đầy đủ để viết MỘT module nội dung.

## Chuẩn bị (làm TRƯỚC khi viết)
1. Đọc `00-huong-dan/roadmap.md` và `PROGRESS.md` để biết đã viết tới đâu.
2. Đọc kỹ 2–3 file đã hoàn thành trong `04-csharp-co-ban/` và `05-csharp-nang-cao/` (ví dụ bài 04, 05, và async 09) để nắm CHÍNH XÁC style: thứ tự và tên các mục, cách đặt tiêu đề, cách dẫn vào code block, phong cách comment, cách trình bày bài tập + gợi ý, format link prerequisite/bài sau, giọng văn. Bài mới phải khớp đúng khuôn đó.
3. Tự xác định module TIẾP THEO theo đúng thứ tự và phụ thuộc trong roadmap.

## Nhiệm vụ
Viết đầy đủ toàn bộ file của 1 module (2 nếu cả hai đều ngắn) rồi DỪNG. Xong mỗi file tick checkbox trong `PROGRESS.md`. Cross-link trỏ đúng tên file thật.

## Format mỗi bài (giữ y hệt module 04/05)
1. Mục tiêu — học xong nắm được gì.
2. Bài toán mở đầu — tình huống thực tế cần giải (PROBLEM-FIRST, không mở bằng định nghĩa khô).
3. Lời giải bằng code — hoàn chỉnh, có comment, chạy được.
4. Giải thích cơ chế — hoạt động thế nào, tại sao (gồm mô hình bộ nhớ khi liên quan: stack/heap, value/reference, mỗi `new` một vùng nhớ riêng).
5. Kiến thức nền — khái niệm cốt lõi phía sau.
6. Lỗi thường gặp — bẫy hay dính và cách tránh.
7. Bài tập — 3–5 bài từ dễ đến khó, có GỢI Ý nhưng KHÔNG lộ lời giải đầy đủ.
8. Checklist tự đánh giá + link bài prerequisite và bài tiếp theo.

## A. KHÔNG để người học bỡ ngỡ
- Trước khi dùng bất kỳ khái niệm / keyword / API nào, nó phải đã được dạy ở một bài TRƯỚC trong lộ trình, hoặc giới thiệu tại chỗ đủ để hiểu. Không giả định kiến thức chưa dạy.
- Nếu buộc phải nhắc tới thứ dạy ở bài sau, chỉ nói một câu ngắn và link tới bài đó, KHÔNG dựa vào nó để giải thích.
- Mỗi bài nối liền mạch với bài trước; có thể tham chiếu lại ví dụ/khái niệm đã học để người đi tuyến tính không bị hẫng.

## B. Nội dung phải CHUẨN
- Mọi đoạn code phải compile và chạy được trên .NET 9; output ghi trong bài phải đúng với khi chạy thật (build/run kiểm chứng).
- Dùng đúng pattern / khuyến nghị hiện hành. Nếu cố tình dùng cách viết KHÔNG nên dùng trong production để minh hoạ, phải nói rõ đó là demo và chỉ ra cách viết đúng.

## C. Điều chỉnh ĐỘ KHÓ
- Mỗi bài phải hiểu được bởi người chỉ mới học tới các bài trước, đọc tuyến tính. Mỗi phần chỉ giới thiệu 1–2 khái niệm mới, không dồn nhiều khái niệm khó cùng lúc.
- Sau mỗi khái niệm khó, chèn một ví dụ tối giản chạy được TRƯỚC, rồi mới ghép vào ví dụ lớn.
- Phần nâng cao/internals/edge case/hiệu năng tách thành mục riêng "### Đào sâu (có thể quay lại sau)", đặt sau "Giải thích cơ chế". Người mới bỏ qua mục này lần đọc đầu mà vẫn nắm đủ cốt lõi để đi tiếp. Bài của module nền tách mạnh tay; bài của module nâng cao chỉ đẩy phần sâu nhất xuống.

Thứ tự các bài trong module và cách chia nhỏ do bạn quyết, miễn đúng chuẩn sư phạm và không phá vỡ phụ thuộc.