# Full-stack Roadmap: từ số 0 đến Software Architect

Đây là bộ tài liệu tự học bằng tiếng Việt, lấy C làm nền tảng tư duy và mô hình bộ nhớ, C#/.NET làm công nghệ đi làm chính, C++ ở mức đủ sâu để hiểu OOP, STL, RAII và ownership. Tuyến học đi tiếp qua SQL, LINQ, Entity Framework Core, web, React, kiểm thử, DevOps, kiến trúc phần mềm và thiết kế hệ thống.

> Trạng thái hiện tại: **đã hoàn thành khung chương trình và toàn bộ module `01`–`05`: 15 bài C nền tảng, 15 bài C chuyên sâu, 14 bài C++20, 16 bài C# cơ bản và 19 bài C# nâng cao. Module `00` hiện mới có roadmap; các bài hướng dẫn môi trường vẫn chờ biên soạn**.

## Bắt đầu ở đâu?

1. Đọc [roadmap 5 cấp](./00-huong-dan/roadmap.md) để hiểu thứ tự, prerequisite và checkpoint.
2. Mở [PROGRESS.md](./PROGRESS.md) để xem toàn bộ mục lục dự kiến và trạng thái từng file.
3. Học tuyến tính theo số module và số bài. Module `01–05` đã hoàn thành; trước khi bắt đầu module `01`, hãy tự bảo đảm đã có C compiler theo lệnh build ghi trong bài vì các bài cài môi trường chi tiết của module `00` chưa được viết.

## Phạm vi kỹ thuật

- Nền tảng: C11, mô hình bộ nhớ, pointer, quản lý tài nguyên.
- C++: C++20, OOP, STL, RAII, smart pointer và move semantics.
- .NET: project target `net9.0`; bài học sẽ pin rõ SDK, compiler và package để code có thể tái tạo được.
- C#: từ cú pháp cơ bản đến generics, async/await, reflection, nullable, `Span<T>` và các tính năng ngôn ngữ mới phù hợp với target.
- Dữ liệu: SQL chuyên sâu, thiết kế cơ sở dữ liệu, LINQ và Entity Framework Core.
- Full-stack: ASP.NET Core, HTTP/API/security, HTML/CSS, JavaScript, TypeScript và React.
- Production: testing, Docker, CI/CD, Redis, gRPC, SignalR, message broker, cloud, Kubernetes và observability.
- Senior/Architect: design pattern, DDD, CQRS, event-driven architecture, microservices, system design, ADR, C4/UML và phân tích trade-off.

Phiên bản patch/minor và dependency cụ thể sẽ được khóa trong bài cài đặt môi trường và từng project. Mục tiêu là code chạy lại được, không phụ thuộc vào trạng thái riêng của IDE.

## Cây thư mục

| Thư mục | Mảng kiến thức |
|---|---|
| `00-huong-dan` | Roadmap, môi trường, công cụ và phương pháp học |
| `01-nen-tang-lap-trinh` | Tư duy lập trình với C |
| `02-c-chuyen-sau` | Pointer, bộ nhớ, C nhiều file và file I/O |
| `03-cpp` | OOP, STL, RAII và C++20 |
| `04-csharp-co-ban` | Nền tảng C# và mô hình value/reference |
| `05-csharp-nang-cao` | C# nâng cao, bất đồng bộ và hiệu năng |
| `06-oop-va-thiet-ke` | OOP, SOLID, coupling/cohesion và clean code |
| `07-cau-truc-du-lieu-giai-thuat` | Cấu trúc dữ liệu, giải thuật và Big-O |
| `08-sql-va-csdl` | SQL và cơ sở dữ liệu chuyên sâu |
| `09-linq-va-ef-core` | LINQ và Entity Framework Core chuyên sâu |
| `10-web-nen-tang` | HTTP, REST, identity và web security |
| `11-aspnet-core-backend` | Backend với ASP.NET Core |
| `12-frontend` | HTML/CSS, JavaScript, TypeScript và React |
| `13-fullstack-tich-hop` | Tích hợp frontend–backend end-to-end |
| `14-testing-chat-luong` | Testing, TDD và quality engineering |
| `15-devops-trien-khai` | Git nâng cao, Docker, CI/CD và vận hành |
| `16-design-pattern` | Creational, structural và behavioral patterns |
| `17-kien-truc-phan-mem` | DDD, CQRS, Clean Architecture và microservices |
| `18-thiet-ke-he-thong` | Scalability, caching, consistency và case study |
| `19-cong-nghe-hien-dai` | Cloud, Kubernetes, messaging và observability |
| `20-ky-nang-architect` | Trade-off, ADR, C4/UML, governance và mentoring |
| `21-du-an-thuc-hanh` | Dự án checkpoint từ console đến distributed system |

## Hợp đồng nội dung của mỗi bài

Trừ tài liệu điều hướng và đặc tả dự án, mỗi bài học phải có đủ:

1. Mục tiêu.
2. Bài toán mở đầu.
3. Lời giải bằng code hoàn chỉnh, có comment và lệnh chạy.
4. Giải thích cơ chế; có sơ đồ bộ nhớ khi liên quan.
5. Kiến thức nền.
6. Lỗi thường gặp và cách tránh.
7. Ba đến năm bài tập có gợi ý, không có lời giải đầy đủ.
8. Checklist tự đánh giá, link prerequisite và bài tiếp theo.

Mọi bài tuân theo hướng **problem-first**. Thuật ngữ, keyword, tên hàm và code giữ nguyên tiếng Anh; phần giải thích dùng tiếng Việt và đi thẳng vào cơ chế.

## Quy ước biên soạn

- Thư mục module có tiền tố `00` đến `21`; file bài có tiền tố thứ tự hai chữ số.
- Tên file dùng `kebab-case`, tiếng Việt không dấu.
- Chỉ đánh dấu `[x]` trong `PROGRESS.md` sau khi file đã viết đủ, code đã được chạy/kiểm tra và cross-link hợp lệ.
- Hoàn thành trọn một module rồi mới biên soạn module tiếp theo.
- Không dùng chức danh nghề nghiệp như chứng chỉ hoàn thành; Senior/Architect còn đòi hỏi kinh nghiệm production và trách nhiệm thực tế.

## Trạng thái và review

`PROGRESS.md` là nguồn sự thật duy nhất về phạm vi và tiến độ. Module `01-nen-tang-lap-trinh` đến `05-csharp-nang-cao` hiện đã hoàn thành, kiểm tra code/output/failure path và cross-link; module `00` còn các bài hướng dẫn môi trường, còn checkbox của module `06` trở đi vẫn biểu thị kế hoạch chưa viết.
