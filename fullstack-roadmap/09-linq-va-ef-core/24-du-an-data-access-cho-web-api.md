# Dự án: Data Access cho Web API

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/provider major update, API/security/testing behavior change, sample CI failure

## TL;DR

- Capstone biến CommerceLab SQL schema thành EF Core 10 data-access layer có query projection, transaction, concurrency, tests và quality gate.
- Mục tiêu không phải có nhiều layer; mục tiêu là query đúng, observable, testable và đủ đơn giản để Module 11 dùng tiếp.
- Hoàn thành khi bạn bảo vệ được cả quyết định **dùng EF** lẫn quyết định **không dùng abstraction/pattern thừa**.

## 1. Mục tiêu

- build CommerceLab.Data trên .NET 10;
- chạy relational tests;
- chạy SQL Server 2025 smoke flow;
- review generated SQL/model/query strategy;
- đạt rubric correctness/performance/security/testability;
- chuẩn bị data layer cho Web API module sau.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Capstone này không kiểm tra bạn nhớ bao nhiêu API EF. Nó kiểm tra bạn có thể **ghép cả chuỗi reasoning data-access** hay không:

~~~text
business requirement
→ relational model
→ EF mapping
→ query shape
→ generated SQL
→ index/transaction
→ tests
→ production trade-off
~~~

Nếu chỉ làm code chạy nhưng không giải thích được query chạy đâu, vì sao dùng tracking/no-tracking, hoặc vì sao không thêm repository, capstone chưa đạt mục tiêu.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| read model | shape tối ưu cho đọc/response |
| command flow | flow thay đổi state |
| data-access boundary | nơi application nói chuyện với persistence |
| smoke test | test nhanh chứng minh flow chính chạy |
| regression test | test ngăn bug cũ quay lại |
| ADR | record quyết định kiến trúc và trade-off |

CommerceLab là cầu nối sang ASP.NET Core: Module 09 chịu trách nhiệm data layer, Module 11 mới thêm HTTP/API concern.

Bạn cần bàn giao data layer để team API dùng mà không phải hiểu tất cả chi tiết SQL mỗi lần, nhưng vẫn phải giữ constraint/index/transaction của Module 08 và không khóa kiến trúc vào generic repository boilerplate.

## 3. Lời giải chạy được

Artifact:

~~~text
samples/module-09/
├── CommerceLab.Data/
│   ├── Entities/
│   ├── CommerceDbContext.cs
│   ├── OrderReadService.cs
│   └── CheckoutService.cs
├── CommerceLab.Data.Demo/
└── CommerceLab.Data.Tests/
~~~

Build/test:

~~~bash
dotnet build samples/module-09/CommerceLab.Data/CommerceLab.Data.csproj
dotnet test samples/module-09/CommerceLab.Data.Tests/CommerceLab.Data.Tests.csproj
~~~

SQL Server smoke:

~~~bash
export COMMERCE_DB='<SQL Server connection string from secret/env>'
dotnet run --project samples/module-09/CommerceLab.Data.Demo
~~~

Expected shape:

~~~text
OrderId=<generated>
Orders=1
Total=2400000
RemainingStock=8
~~~

### Walkthrough end-to-end

Checkout sample:

~~~text
1. nhận CustomerId/ProductId/Quantity
2. validate quantity
3. bắt đầu DB transaction
4. đọc Product cần thiết
5. atomic update Stock nếu đủ quantity
6. tạo Order + OrderItem snapshot + Payment
7. SaveChanges
8. Commit
9. trả OrderId
~~~

Read sample:

~~~text
request order history
→ IQueryable
→ filter CustomerId
→ deterministic order
→ projection OrderSummary
→ AsNoTracking semantics
→ SQL
→ DTO list
~~~

Hai flow cố ý khác nhau: command cần invariant/state change; read cần shape nhỏ và ít overhead.

## 4. Cơ chế hoạt động

### Mental model kiến trúc tối thiểu

~~~text
Application/use-case code
  ├─ OrderReadService
  └─ CheckoutService
          ↓
CommerceDbContext
          ↓
EF Core provider
          ↓
SQL Server
~~~

Không có Repository/CQRS/Microservice mặc định vì chưa có driver cần chúng.

### Checklist reasoning cho mỗi query/command

| Câu hỏi | Read | Write |
|---|---|---|
| Chạy ở đâu? | DB càng nhiều càng tốt | DB + tracked command |
| Shape? | DTO/projection | entity/aggregate state |
| Tracking? | thường không | thường có |
| Transaction? | thường implicit/no explicit | tùy atomic operation |
| Concurrency? | ít hơn | cần policy |
| Test? | translation/provider | invariant/transaction/conflict |

### Misconception check

**Đúng hay sai?** Capstone tốt phải có nhiều layer để trông enterprise.

**Đáp án:** Sai. Chỉ thêm layer khi có responsibility/driver cụ thể.

**Đúng hay sai?** SQL Server smoke pass nghĩa là mọi performance issue đã được giải quyết.

**Đáp án:** Sai. Nó chứng minh flow chính chạy, không thay load/profile/plan analysis.

### Mini-check

Nếu Module 11 cần endpoint list order, nên trả thẳng tracked `Order` graph hay dùng projection DTO từ data layer?

Đáp án: thường projection DTO/read model rõ và an toàn hơn.

`CheckoutService` dùng explicit transaction + atomic stock update + snapshot OrderItem.

`OrderReadService` dùng `AsNoTracking` + projection để tránh entity graph/N+1.

`CommerceDbContext` map schema/index/relationship và query filter.

Tests dùng relational SQLite cho fast behavior; CI còn chạy SQL Server 2025 provider-real smoke.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** chạy và giải thích flow read/write.

**Working developer:** migration/test/query/concurrency decisions có evidence.

**Deep dive:** ADR, performance profiling, provider-specific optimization và evolutionary architecture.

Đây là output của Module 09 và input cho Module 11 ASP.NET Core.

Module 08 vẫn là source của relational reasoning; EF layer không được phá invariant database.

Module 07 Big-O được dùng khi chọn collection/lookup in-memory; không kéo bài toán database về C# vô lý.

## 6. Lỗi thường gặp

**Thêm Controller/API vào module data access.** Trộn concern trước khi học Web foundation/API.

**Generic repository hóa toàn bộ sample.** Mất access tới projection/provider features mà không có driver.

**Chỉ test SQLite.** Bỏ provider-specific failure.

**Commit connection string.** Security failure.

## 7. Khi nào KHÔNG dùng

Không tách microservice/database riêng cho CommerceLab chỉ vì capstone đã có nhiều schema.

Không CQRS/MediatR/repository/specification đồng loạt nếu chưa có driver.

Không tối ưu compiled query/bulk path nếu benchmark chưa chỉ ra bottleneck.

## 8. Production notes & scale check

### Ở quy mô nhỏ có thật sự cần kiến trúc phức tạp không?

Không. Team 2–3 người có thể bắt đầu bằng modular monolith, một DbContext, application services rõ và SQL Server. Chỉ tách thêm layer/service khi ownership, scale, deploy independence hoặc isolation tạo driver.

Production checklist: secret store, migration deployment identity, observability DB commands, backup/restore, query plan cho hot path, concurrency conflict policy.

Capstone phải giữ code đủ đơn giản để người khác debug.

## 9. Bài tập kỹ thuật

1. Thêm OrderNumber unique và migration.
2. Thêm query order history có keyset pagination.
3. Viết concurrency integration test hai context.
4. Thêm SQL Server Testcontainers test cho critical query.
5. Profile query read service và đề xuất index nếu cần.

## 10. Bài tập tích hợp liên module — Judgment

**Bài tích hợp Module 07 + 08 + 09:** cần tìm top SKU bán chạy và phát hiện SKU thuộc danh sách cấm. Quyết định phần nào chạy SQL aggregate/index, phần nào LINQ/HashSet C#, và giải thích ranh giới dựa trên data size/data locality.

**Architecture judgment:** với team 3 người và 50 request/s, bắt đầu từ DbContext/application service hay Repository+CQRS+microservice? Ghi ADR một trang.

## 11. Retrieval practice

1. Vì sao projection là default tốt cho read list?
2. Khi nào transaction explicit cần?
3. Vì sao SQLite test chưa đủ?
4. Generic repository có driver nào trong CommerceLab hiện tại không?
5. Nếu query chậm, bạn kiểm tra LINQ, SQL hay index theo thứ tự nào?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy/build được sample liên quan.
- [ ] Tôi biết query/side effect thực sự chạy ở đâu.
- [ ] Tôi phân biệt convenience với abstraction có driver.
- [ ] Tôi nêu được lựa chọn đơn giản hơn cho team nhỏ.

- Bài trước: [Repository Pattern có nên dùng?](./23-repository-pattern-co-nen-dung.md)
- Bài tiếp theo: [Module 10 — Web nền tảng](../PROGRESS.md#10-web-nen-tang)
- Spaced review: [Review 05 — Performance, testing & architecture](./reviews/review-05-performance-testing-and-architecture.md)
- Failure Lab: [Concurrency và stale state](./failure-labs/04-concurrency-va-stale-state.md)
- PR Review: [Order Search](./pr-review-labs/01-review-linq-search-service.md) · [EF Production Risks](./pr-review-labs/02-review-ef-production-risks.md)
- Career checkpoint: [Junior Data/Backend](./career-checkpoint/index.md)
