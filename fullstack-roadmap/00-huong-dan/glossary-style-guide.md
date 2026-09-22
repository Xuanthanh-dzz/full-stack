# Glossary & Style Guide dùng chung

> Canonical source cho Codex CLI, Claude Code và mọi công cụ sinh nội dung.
>
> Mục tiêu: toàn bộ roadmap phải đọc như do **một đội biên tập duy nhất** viết, dù nội dung được tạo trong nhiều tháng và bởi nhiều AI/tool khác nhau.

## 1. Quy tắc ngôn ngữ

- Viết tiếng Việt tự nhiên, ngắn gọn, kỹ thuật chính xác.
- Thuật ngữ phổ biến trong nghề được giữ tiếng Anh khi bản dịch Việt làm khó đọc hơn.
- Lần đầu xuất hiện: ưu tiên dạng `Thuật ngữ tiếng Việt (English term)` hoặc `English term (giải thích tiếng Việt)`.
- Sau lần đầu, dùng **một cách gọi duy nhất** trong toàn bộ khóa.
- Không đổi từ đồng nghĩa chỉ để “văn vẻ”.
- Không dịch tên API, keyword, command, class, interface, pattern hoặc product.
- Code, identifier, command, file path luôn giữ nguyên.
- Khi có khác biệt giữa “định nghĩa học thuật” và “cách nói trong công ty”, nói rõ cả hai.

## 2. Thuật ngữ canonical

| Khái niệm | Cách dùng chuẩn | Tránh dùng |
|---|---|---|
| lifecycle | **vòng đời** | chu kỳ sống |
| object | **đối tượng** | vật thể |
| instance | **instance / thể hiện**; ưu tiên `instance` trong code discussion | trường hợp |
| dependency | **dependency / phụ thuộc** | lệ thuộc |
| Dependency Injection | **Dependency Injection (DI)**; sau đó dùng `DI` | tiêm phụ thuộc nếu đứng một mình |
| garbage collection | **thu gom rác (GC)**; sau đó `GC` | dọn rác |
| memory stack | **stack** | ngăn xếp bộ nhớ nếu gây nhầm với cấu trúc Stack |
| memory heap | **heap** | vùng đống |
| collection | **collection** | tập hợp nếu có thể nhầm với Set |
| set | **set / tập hợp** theo ngữ cảnh toán hoặc cấu trúc dữ liệu | collection |
| query | **truy vấn / query**; ưu tiên `query` khi nói LINQ/API | câu hỏi |
| deferred execution | **deferred execution (thực thi trì hoãn)** | lazy execution nếu đang nói LINQ |
| materialization | **materialization (hiện thực hóa kết quả)** | kết tinh dữ liệu |
| tracking | **theo dõi thay đổi (change tracking)**; sau đó `tracking` | giám sát |
| eager loading | **eager loading** | tải háo hức |
| explicit loading | **explicit loading** | tải tường minh nếu không kèm English |
| lazy loading | **lazy loading** | tải lười |
| concurrency | **đồng thời / concurrency** | song song nếu không phải parallelism |
| parallelism | **song song / parallelism** | concurrency |
| transaction | **transaction / giao dịch**; ưu tiên `transaction` trong DB code | phiên giao dịch |
| idempotency | **idempotency / tính lũy đẳng** | tính bất biến |
| repository pattern | **Repository Pattern** | mẫu kho |
| unit of work | **Unit of Work** | đơn vị công việc |
| expression tree | **expression tree (cây biểu thức)** | cây biểu diễn |
| query provider | **query provider** | nhà cung cấp truy vấn |
| projection | **projection / phép chiếu** | ánh xạ nếu đang nói SELECT shape |
| DTO | **DTO** | object truyền dữ liệu sau lần giải thích đầu |
| migration | **migration** | di trú CSDL |
| schema | **schema** | lược đồ khi đang nói tên schema SQL cụ thể |
| index | **index / chỉ mục**; ưu tiên `index` trong DB discussion | mục lục |
| execution plan | **execution plan** | kế hoạch thực hiện |
| deadlock | **deadlock** | khóa chết |
| race condition | **race condition** | điều kiện đua |
| cache | **cache** | bộ nhớ đệm nếu lặp lại nhiều |
| throughput | **throughput / thông lượng** | năng suất |
| latency | **latency / độ trễ** | trì hoãn |
| resilience | **resilience / khả năng chống chịu lỗi** | khả năng phục hồi nếu dễ nhầm disaster recovery |
| observability | **observability / khả năng quan sát** | giám sát nếu nói rộng hơn monitoring |
| bounded context | **Bounded Context** | ngữ cảnh giới hạn |
| aggregate (DDD) | **Aggregate** | tổng hợp nếu đang nói DDD |
| aggregate (SQL) | **aggregate / phép tổng hợp** | Aggregate DDD |
| eventual consistency | **eventual consistency / nhất quán cuối cùng** | nhất quán chậm |

## 3. Quy tắc code chung

- Code trong bài phải **chạy được**, không dùng pseudo-code trong block được giới thiệu là runnable.
- Pseudo-code phải gắn nhãn `text` hoặc `pseudo`.
- Ví dụ ưu tiên nhỏ nhất nhưng vẫn thể hiện đúng vấn đề.
- Không dùng syntax “mới cho đẹp” nếu làm tăng cognitive load mà không phục vụ mục tiêu bài.
- Mọi command cần có working directory hoặc ngữ cảnh rõ ràng khi dễ gây nhầm.
- Không giấu dependency quan trọng.
- Không hard-code secret thật.

## 4. C

- Baseline: C11 trừ bài nói rõ chuẩn khác.
- Function/variable: `snake_case`.
- Macro/compile-time constant: `UPPER_SNAKE_CASE`.
- Type tự định nghĩa: `PascalCase` khi dùng typedef.
- Luôn kiểm tra return code của API có thể fail.
- Không cast kết quả `malloc` trong C.
- Giải phóng resource theo một ownership rõ ràng.

## 5. C++20

- Type/class: `PascalCase`.
- Function/local variable: `camelCase`.
- Hằng compile-time: `kPascalCase` hoặc `UPPER_SNAKE_CASE`; trong roadmap ưu tiên `kPascalCase`.
- Ưu tiên RAII, smart pointer và value semantics.
- Không dùng raw `new/delete` trừ bài đang dạy chính chúng.
- `auto` khi type hiển nhiên hoặc type rất dài; không dùng nếu làm mất ý nghĩa domain.

## 6. C# / .NET

- Baseline bài mới: **.NET 10 LTS + C# 14** trừ khi metadata ghi khác.
- File-scoped namespace.
- Nullable reference types bật.
- Type/member public: `PascalCase`.
- Local/parameter/private field: `camelCase`; private field nếu cần field prefix dùng `_camelCase`.
- Async method có suffix `Async`.
- Truyền `CancellationToken` cho I/O async có thể hủy.
- `var` khi type rõ từ RHS, anonymous type, LINQ projection hoặc generic type quá dài.
- Dùng explicit type khi nó mang thông tin domain quan trọng hoặc RHS không làm type rõ.
- Không dùng `.Result` / `.Wait()` cho async flow thông thường.
- Collection expression / primary constructor / syntax mới chỉ dùng khi không làm bài beginner khó đọc hơn hoặc bài đang dạy tính năng đó.
- Exception chỉ dùng cho exceptional failure, không thay control flow bình thường.

## 7. SQL Server

- Keyword SQL viết HOA.
- Object luôn schema-qualified trong ví dụ production-oriented: `dbo.Products`, `sales.Orders`.
- Table/column/constraint: `PascalCase`.
- Alias ngắn nhưng có nghĩa.
- Tiền dùng `decimal`, không dùng `float`.
- Timestamp ứng dụng mới ưu tiên `datetime2`.
- Không dùng `SELECT *` trong ví dụ production.
- Mọi destructive statement phải có predicate rõ hoặc được giải thích vì sao toàn bảng.
- SQL động phải parameterize value; identifier động phải whitelist.
- Index luôn gắn với access pattern, không thêm theo cảm tính.

## 8. JavaScript / TypeScript / React

- `const` mặc định; `let` khi cần reassign; không dùng `var`.
- TypeScript strict mode.
- Type/interface `PascalCase`; variable/function `camelCase`.
- Không dùng `any` nếu không có lý do được giải thích.
- React dùng function component và hooks.
- Server state không mặc định nhét vào global client-state store.
- Side effect phải có ownership rõ.

## 9. Angular

- Dùng standalone component cho bài mới.
- Service/DI/RxJS/Signals được chọn theo semantics, không trộn chỉ để trình diễn.
- Observable stream đặt tên có `$` khi codebase đang theo convention đó; trong roadmap dùng nhất quán `orders$`.
- Reactive Forms ưu tiên cho form nghiệp vụ phức tạp.

## 10. DevOps / YAML / shell

- YAML 2-space indentation.
- Shell script bật fail-fast khi phù hợp: `set -euo pipefail`.
- Image/package version phải pin ở nơi reproducibility quan trọng.
- Không đưa secret vào YAML.
- Command destructive phải có guard hoặc môi trường lab rõ.

## 11. Style giải thích

Mỗi đoạn giải thích phải trả lời ít nhất một trong các câu:

1. Nó giải quyết vấn đề gì?
2. Nó hoạt động vì sao?
3. Trade-off là gì?
4. Khi nào không nên dùng?
5. Làm sao biết nó đang gây vấn đề trong production?

Tránh:

- định nghĩa vòng tròn;
- “best practice” không có lý do;
- khẳng định performance nếu chưa đo;
- pattern worship;
- abstraction chỉ để tăng số layer.

## 12. Quy tắc cho AI authoring

Trước khi tạo/sửa bài, tool **phải đọc**:

1. `AGENTS.md` hoặc `CLAUDE.md`;
2. file này;
3. `lesson-authoring-standard.md`;
4. `PROGRESS.md`;
5. bài trước và bài sau nếu đã tồn tại.

Nếu nội dung mới mâu thuẫn file này, **file này thắng** trừ khi maintainer sửa canonical guide.
