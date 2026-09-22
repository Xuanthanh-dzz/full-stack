# Lesson Authoring Standard v2

> Áp dụng bắt buộc cho Module 09 trở đi. Module 01–08 sẽ được retrofit sau.
>
> Canonical style/terminology: [Glossary & Style Guide](./glossary-style-guide.md).

## 1. Definition of Done mới

Một bài chỉ được đánh dấu hoàn thành khi:

- file tồn tại đúng manifest;
- đủ cấu trúc bắt buộc;
- code chính chạy/compile;
- command tái tạo được;
- cross-link hợp lệ;
- có TL;DR;
- có mục **Khi nào KHÔNG dùng**;
- có production/scale note khi kỹ thuật có trade-off vận hành;
- có bài tập retrieval và ít nhất một bài judgment/tích hợp khi phù hợp;
- có metadata `Last verified`, version baseline và review cycle;
- verifier CI của module pass;
- MkDocs build pass.

## 2. Cấu trúc bắt buộc của mỗi bài

### Metadata — trước nội dung chính

Mẫu:

```markdown
> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.x · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** major SDK/provider update, breaking change, sample CI failure
```

Foundation ít biến động có thể dùng 180 ngày. Web/framework/cloud nên 90–120 ngày.

### TL;DR — đúng 3 dòng

Đặt trước “Bài toán mở đầu”.

Ba dòng phải trả lời:

1. Đây là gì?
2. Khi nào dùng?
3. Trade-off/rủi ro chính là gì?

Không biến TL;DR thành mục lục.

### 1. Mục tiêu

4–8 outcome có thể kiểm tra.

Tránh “hiểu X” nếu không nói người học phải làm được gì.

### 2. Bài toán mở đầu

Bắt đầu bằng vấn đề thật, không bắt đầu bằng định nghĩa API.

### 3. Lời giải chạy được

- Code hoàn chỉnh tối thiểu.
- Có command setup/build/run/test.
- Comment giải thích phần khó, không comment từng dòng hiển nhiên.
- Expected output hoặc assertion khi hợp lý.

### 4. Cơ chế hoạt động

Giải thích runtime/database/network mechanism.

Có sơ đồ text/memory/data-flow nếu giúp reasoning.

### 5. Kiến thức nền và prerequisites

Nêu dependency kiến thức, liên hệ bài/module trước.

### 6. Lỗi thường gặp

Đây là trường hợp **dùng đúng kỹ thuật nhưng triển khai sai**.

Ví dụ:

- query đúng intent nhưng materialize quá sớm;
- transaction đúng chỗ nhưng giữ quá lâu;
- async đúng use case nhưng sync-over-async.

### 7. Khi nào KHÔNG dùng

Đây là trường hợp **code có thể đúng nhưng chọn kỹ thuật sai ngữ cảnh**.

Bắt buộc tách khỏi “Lỗi thường gặp”.

Phải nêu:

- tín hiệu cho thấy kỹ thuật không đáng dùng;
- phương án đơn giản hơn;
- chi phí abstraction/ops/debug;
- ngưỡng hoặc câu hỏi quyết định nếu có.

### 8. Production notes & scale check

Tối thiểu trả lời:

- demo khác production ở đâu?
- performance/security/observability/concurrency có rủi ro nào?
- team 2–3 người / hệ thống vừa có cần kỹ thuật này chưa?
- khi nào nên nâng cấp sang giải pháp phức tạp hơn?

Với kỹ thuật enterprise như K8s, Saga, distributed lock, microservices:
phải có subsection **“Ở quy mô nhỏ có thật sự cần không?”**.

### 9. Bài tập kỹ thuật

3–5 bài, có hint nhưng không full solution.

Ít nhất một bài yêu cầu debug/fix code sai nếu chủ đề phù hợp.

### 10. Bài tập tích hợp liên module — Judgment

Không chỉ “hãy dùng kỹ thuật vừa học”.

Phải bắt người học quyết định **giải ở tầng nào** và bảo vệ lựa chọn.

Ví dụ:

- SQL hay LINQ in-memory?
- index hay cache?
- constraint DB hay validation application?
- DSA hay query SQL?
- transaction DB hay message/outbox?
- monolith hay microservice?

Chấm cả reasoning, không chỉ output.

### 11. Retrieval practice

3–5 câu không nhìn tài liệu:

- giải thích bằng lời;
- dự đoán output;
- sketch mechanism;
- nêu trade-off;
- chọn giữa hai giải pháp.

### 12. Checklist tự đánh giá & điều hướng

Checklist phải kiểm tra khả năng:

- build;
- debug;
- giải thích;
- đo;
- chọn đúng kỹ thuật.

Có link bài trước / bài sau / prerequisite liên module.

## 3. Failure-driven learning

Mỗi 3–5 bài phải có ít nhất một lab bắt người học sửa lỗi thật:

- N+1;
- stale tracking;
- race condition;
- deadlock;
- missing index;
- wrong lifetime;
- invalid cache;
- retry duplicate;
- memory leak/resource leak;
- auth/config mistake.

Không đưa đáp án ngay trước bài tập.

## 4. Must know / Should know / Deep dive

Khi bài dài, chia rõ:

- **Must know:** cần để đi tiếp/đi làm;
- **Should know:** tăng chất lượng implementation;
- **Deep dive:** dành cho Mid/Senior/Architect.

Không bắt beginner học thuộc Deep dive để qua module.

## 5. Project xuyên suốt

Từ Module 08 trở đi, ưu tiên cùng domain **CommerceLab**:

```text
SQL schema
→ EF Core data access
→ ASP.NET Core API
→ React/Angular
→ tests
→ Docker/CI
→ observability
→ architecture
```

Capstone module phải để lại artifact có thể dùng làm input cho module sau.

## 6. Rubric project

Mỗi capstone chấm tối thiểu:

| Nhóm | Trọng số gợi ý |
|---|---:|
| Correctness | 25% |
| Data/model/API design | 15% |
| Error handling & edge cases | 10% |
| Testability & tests | 15% |
| Performance | 10% |
| Security | 10% |
| Maintainability/readability | 10% |
| Documentation & reproducibility | 5% |

Không dùng điểm để “xếp hạng con người”; rubric dùng để chỉ ra gap kỹ năng.

## 7. Entry test / Exit test

Mỗi module mới nên có:

- Entry test: 10–15 câu/task ngắn từ prerequisites.
- Exit test: 1–3 task thực hành không copy sample.
- Capstone: tích hợp nhiều kỹ năng.

Fail entry test không cấm học; nó chỉ chỉ ra bài cần ôn.

## 8. Last verified & freshness

Mỗi bài mới phải có metadata.

Reverify khi:

- quá `Review cycle`;
- major .NET/EF/React/Angular/SQL/SDK thay đổi;
- breaking-change note ảnh hưởng API;
- sample CI fail;
- security advisory ảnh hưởng code mẫu.

CI freshness chạy định kỳ và báo bài stale.

## 9. Quy mô nhỏ trước, enterprise sau

Mọi nội dung Architect phải trả lời:

> Nếu team 2–3 người, traffic vừa, deployment đơn giản — giải pháp nhỏ nhất đủ tốt là gì?

Chỉ nâng cấp khi có driver cụ thể:

- scale;
- team ownership;
- isolation;
- compliance;
- availability;
- deploy independence;
- data boundary;
- measured bottleneck.

## 10. Không pattern worship

Mỗi pattern/technology phải có:

```text
Problem
→ simplest solution
→ failure mode
→ threshold/driver
→ stronger solution
→ operational cost
```

Nếu không chỉ ra driver, không được khuyến nghị abstraction phức tạp.

## 11. Quality gate cho AI tool

Trước khi commit bài mới, AI phải tự check:

- thuật ngữ canonical;
- style code;
- version baseline;
- links;
- runnable sample;
- TL;DR 3 dòng;
- section 7 “Khi nào KHÔNG dùng”;
- scale note;
- judgment exercise;
- retrieval practice;
- metadata freshness.

## 12. Quy tắc sửa bài cũ

Khi retrofit Module 01–08:

1. không đổi concept đúng chỉ để đồng nhất văn phong;
2. thêm metadata/TL;DR/sections thiếu;
3. chạy lại sample;
4. sửa terminology/style;
5. thêm judgment/production note;
6. chỉ tick verified sau CI.


## 13. Failure Lab bắt buộc

Từ Module 09 trở đi, ngoài bài tập debug nhỏ trong từng bài, mỗi module phải có **lab lỗi chuyên dụng**.

### Cadence

- tối thiểu 1 Failure Lab sau mỗi 4–6 bài;
- một module 20+ bài nên có ít nhất 4 lab;
- lab không tính vào số bài chính trong manifest.

### Cấu trúc Failure Lab

Mỗi lab phải có:

1. bối cảnh production-like;
2. code/query/config cố ý sai;
3. triệu chứng quan sát được;
4. cách tái hiện;
5. acceptance criteria;
6. 2–4 hint tăng dần;
7. checklist điều tra;
8. **không có full solution trong cùng trang**.

Lab phải buộc người học dùng ít nhất hai kỹ năng, ví dụ:

- LINQ + Big-O;
- EF loading + SQL cardinality;
- concurrency + transaction;
- cache + HTTP semantics.

Verifier module phải kiểm tra số lượng lab tối thiểu.

## 14. Spaced Review / Retrieval Cycle

Retrieval practice cuối bài là mức vi mô; mỗi module còn phải có **review checkpoint giãn cách**.

### Cadence

- sau khoảng bài 1–5;
- sau bài 6–10;
- sau bài 11–15;
- sau bài 16–20;
- cuối module/capstone.

Mỗi review phải trộn:

- 40–60% kiến thức cụm vừa học;
- 20–30% kiến thức module trước;
- 10–20% judgment/debugging.

Không copy nguyên câu hỏi từ bài cũ.

### Format

Mỗi review nên có:

- 5 câu retrieval không nhìn tài liệu;
- 2 bài dự đoán output/SQL/query count;
- 1 bài debug;
- 1 bài judgment chọn tầng giải quyết;
- self-score để biết nên ôn lại bài nào.

## 15. PR / Code Review Lab

Từ Module 09 trở đi, mỗi module kỹ thuật phải có ít nhất **1 PR review lab**; module backend/data/architecture nên có 2.

Lab phải cung cấp:

- diff hoặc patch gần giống PR thật;
- 6–12 vấn đề thuộc nhiều nhóm;
- rubric review: correctness, performance, security, maintainability, operability;
- yêu cầu viết review comment có severity và reasoning;
- không yêu cầu người học sửa hết code trước khi review.

Mục tiêu là luyện khả năng:

```text
đọc code người khác
→ phát hiện vấn đề
→ đánh giá mức độ
→ giải thích tác động
→ đề xuất thay đổi nhỏ nhất hợp lý
```

## 16. Career Checkpoint

Các mốc nghề nghiệp chính:

| Sau module | Checkpoint | Mục tiêu |
|---|---|---|
| 05 | C# Foundation | viết/debug/test ứng dụng C# vừa |
| 09 | Junior Data/Backend | LINQ + SQL + EF Core + data access production basics |
| 13 | Full-stack Junior | API + React/Angular + auth + integration |
| 15 | Production-ready Developer | testing + CI/CD + Docker + observability |
| 18 | Senior/System Design | architecture drivers + distributed/system design |
| 20 | Architect | trade-off, ADR, migration strategy, technical leadership |

Mỗi checkpoint phải có ít nhất:

1. knowledge test;
2. build task;
3. debugging task;
4. PR review task;
5. judgment task;
6. interview-style explanation;
7. competency matrix theo mức **Chưa đạt / Đạt / Vững**.

Checkpoint **không xếp hạng con người**; nó chỉ chỉ ra gap kỹ năng và bài cần ôn.

## 17. Quality gate module v3

Từ Module 09 trở đi, module chỉ hoàn thành khi:

- lesson gate v2 pass;
- Failure Labs đạt cadence;
- Spaced Reviews đạt cadence;
- PR Review Lab tồn tại;
- Career Checkpoint tương ứng tồn tại nếu module là mốc checkpoint;
- sample/test/provider-real gate pass;
- freshness gate pass;
- MkDocs build pass.



## 18. Pedagogy Depth Standard — beginner-first, expert-depth

Một bài **không đạt** chỉ vì code đúng hoặc production note sâu. Bài phải giúp người học tự xây mental model trước khi dùng API.

### 18.1. Không dùng thuật ngữ trước khi giải thích

Khi một thuật ngữ mới xuất hiện lần đầu, phải có:

1. tên;
2. giải thích bằng ngôn ngữ đơn giản;
3. ví dụ nhỏ;
4. liên hệ với kiến thức người học đã biết.

Ví dụ không đạt:

> `IQueryable<T>` dùng expression tree cho query provider.

Ví dụ đạt:

> `IQueryable<T>` không chỉ giữ “các phần tử”. Nó giữ **một mô tả truy vấn chưa chạy**. Mô tả này giống một bản kế hoạch: “lọc Price > 100, sắp xếp theo Name”. EF Core đọc bản kế hoạch đó và chuyển nó thành SQL. Cấu trúc object biểu diễn “bản kế hoạch” này được gọi là **expression tree**.

### 18.2. Mỗi bài phải có lớp giải thích theo thứ tự

~~~text
Trực giác
→ Từ vựng
→ Ví dụ tối thiểu
→ Trace từng bước
→ Cơ chế
→ Biến thể / so sánh
→ Production
→ Judgment
~~~

Không được nhảy thẳng từ định nghĩa sang production trade-off.

### 18.3. Khối “Trực giác trước khi code”

Mỗi bài phải có một subsection trước hoặc trong bài toán mở đầu trả lời:

- nếu giải thích cho người mới trong 60 giây thì nói gì?
- dữ liệu đi từ đâu tới đâu?
- kỹ thuật này tồn tại vì vấn đề gì?
- nếu không có nó, ta phải làm thủ công thế nào?

### 18.4. Từ vựng tối thiểu

Bài có từ mới phải có bảng:

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|

Không giả định người học nhớ mọi thuật ngữ từ module trước.

### 18.5. Worked example nhỏ trước sample production-like

Trước CommerceLab hoặc ví dụ lớn, luôn có ví dụ 3–6 phần tử / 1–2 entity / 1 transaction nhỏ.

Ví dụ nhỏ phải cho phép người học **tính tay kết quả**.

### 18.6. Execution trace bắt buộc

Với code có pipeline/runtime/database behavior, phải trace từng bước.

Ví dụ:

~~~text
orders
  ↓ Where
[1, 3]
  ↓ OrderByDescending
[3, 1]
  ↓ Select
[{Id=3}, {Id=1}]
~~~

Với EF/database:

~~~text
C# LINQ
→ expression tree
→ EF query translator
→ SQL
→ SQL Server executes
→ rows
→ EF materializes DTO/entity
~~~

Với async/concurrency:

~~~text
Request A reads token=T1
Request B reads token=T1
A updates WHERE token=T1 → 1 row
B updates WHERE token=T1 → 0 row
→ concurrency conflict
~~~

### 18.7. “Vì sao?” sau mỗi API quan trọng

Không chỉ ghi API làm gì. Phải giải thích:

- vì sao framework thiết kế như vậy;
- state nào được giữ;
- lúc nào code thực sự chạy;
- cost nằm ở CPU, memory, network hay database;
- điều gì thay đổi nếu đổi data source/provider.

### 18.8. Bảng so sánh khi có khái niệm dễ nhầm

Ví dụ bắt buộc khi phù hợp:

- `IEnumerable` vs `IQueryable`;
- tracking vs no-tracking;
- eager vs explicit vs lazy loading;
- single vs split query;
- transaction vs concurrency token;
- SQLite test vs SQL Server test;
- EF LINQ vs raw SQL;
- DbContext trực tiếp vs Repository.

Bảng phải so theo **semantics/cost/use case**, không chỉ syntax.

### 18.9. Misconception check

Mỗi bài phải có 2–4 câu kiểu:

> “Đúng hay sai? `AsEnumerable()` chạy query ngay.”

Sau câu hỏi phải có đáp án giải thích ngắn **sau một khoảng cách thị giác**, để người học tự đoán trước.

### 18.10. Mini-check trong thân bài

Không đợi cuối bài mới kiểm tra.

Sau một khái niệm khó, thêm 1 câu:

> Nếu source là 1 triệu row, dòng code nào quyết định filter chạy ở SQL hay RAM?

Mini-check phải kiểm tra mental model vừa xây.

### 18.11. Beginner / Working Developer / Deep Dive

Bài dài chia ba tầng:

- **Beginner core:** bắt buộc hiểu để đi tiếp;
- **Working developer:** thứ cần dùng trong công việc;
- **Deep dive:** internals, provider nuance, performance edge case.

Người học phải biết phần nào có thể bỏ qua trong lượt học đầu.

### 18.12. Giải thích code theo khối, không chỉ đưa code

Sau sample lớn phải có walkthrough:

1. input là gì;
2. dòng/khối đầu thay đổi state gì;
3. execution xảy ra lúc nào;
4. output/intermediate shape;
5. failure mode nếu sửa sai một dòng quan trọng.

### 18.13. Minimum depth heuristic

Bài kỹ thuật cốt lõi chỉ được coi là đủ sâu khi người học có thể trả lời **không nhìn tài liệu**:

1. Nó là gì bằng lời của mình?
2. Vì sao cần nó?
3. Nó chạy ở đâu?
4. Nó giữ state gì?
5. Cost chính nằm ở đâu?
6. Nó khác lựa chọn gần nhất thế nào?
7. Khi nào code vẫn chạy nhưng lựa chọn sai?
8. Làm sao debug khi nó hỏng?

Nếu bài chưa cung cấp đủ thông tin để trả lời tám câu này, bài chưa đủ chi tiết.

### 18.14. Quality gate v4 — clarity gate

Module 09+ phải kiểm tra thêm:

- có khối trực giác;
- có bảng từ vựng khi xuất hiện thuật ngữ mới;
- có execution trace cho bài có pipeline/runtime/database flow;
- có bảng so sánh cho concept dễ nhầm;
- có misconception check;
- có walkthrough sau code lớn;
- có phân tầng Beginner / Working developer / Deep dive ở bài dài.

Gate không dùng word count đơn thuần; ưu tiên evidence về khả năng giải thích.
