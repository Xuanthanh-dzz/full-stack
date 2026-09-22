# Module 09 — LINQ & Entity Framework Core

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** .NET/EF Core major update, provider breaking change, sample CI failure

Module 09 nối trực tiếp từ [CSDL thương mại điện tử của Module 08](../08-sql-va-csdl/25-du-an-csdl-thuong-mai-dien-tu.md) sang data-access layer bằng C#.

## Entry test

Không nhìn tài liệu, hãy thử:

1. Viết SQL lấy 10 order mới nhất của một customer.
2. Giải thích khác nhau giữa `WHERE` và `HAVING`.
3. Nêu khi nào index `(CustomerId, OrderedAt)` có ích.
4. Giải thích transaction và optimistic concurrency.
5. Viết một lambda C# nhận `Product` và trả `bool`.
6. Phân biệt `IEnumerable<T>` với một collection cụ thể như `List<T>`.
7. Giải thích async I/O khác parallel CPU work.
8. Nêu vì sao `SELECT *` không phải default tốt cho API.
9. Nêu một trường hợp logic nên ở database thay vì C#.
10. Nêu một trường hợp logic nên ở C# thay vì database.

Nếu dưới 6/10, hãy ôn Module 05 và 08 trước khi đi sâu phần EF Core.

## Bản đồ module

```text
LINQ in-memory
    ↓
deferred execution
    ↓
IEnumerable vs IQueryable
    ↓
expression tree + query provider
    ↓
EF Core 10 model
    ↓
migration / tracking / relationship
    ↓
loading / N+1 / projection
    ↓
transaction / concurrency
    ↓
filters / interceptors / raw SQL
    ↓
performance / testing
    ↓
Repository Pattern: có nên dùng?
    ↓
CommerceLab Data Access capstone
```

## Project xuyên suốt

Artifact chính của module nằm tại:

```text
samples/module-09/
├── CommerceLab.Data
├── CommerceLab.Data.Demo
└── CommerceLab.Data.Tests
```

Nó dùng .NET 10, EF Core 10.0.12, SQL Server provider, SQLite in-memory cho một lớp integration test và CommerceLab domain từ Module 08.

## Exit test

Không copy sample:

1. Map một schema order mới bằng Fluent API.
2. Viết query projection không gây N+1.
3. Chứng minh SQL được sinh từ một `IQueryable`.
4. Xử lý optimistic concurrency cho một update.
5. Viết test chạy trên relational provider.
6. Giải thích vì sao Repository Pattern có thể thừa trên EF Core.
7. Đề xuất index cho query LINQ dựa trên SQL/plan, không dựa trên tên method C#.
8. Chọn SQL, LINQ in-memory hay LINQ-to-EF cho ba bài toán khác nhau và bảo vệ quyết định.

## Rubric capstone

| Nhóm | Trọng số |
|---|---:|
| Correctness | 25% |
| Data/model/query design | 15% |
| Error handling & concurrency | 10% |
| Testability & tests | 15% |
| Performance | 10% |
| Security | 10% |
| Maintainability/readability | 10% |
| Documentation/reproducibility | 5% |

## Learning system bắt buộc

Module 09 không chỉ có 24 bài chính. Người học phải đi qua bốn lớp assessment bổ sung:

- [Failure Labs](./failure-labs/01-multiple-enumeration-va-materialization.md) — 4 lab debug production-like;
- [Spaced Reviews](./reviews/review-01-linq-core.md) — 5 checkpoint ôn giãn cách;
- [PR Review Labs](./pr-review-labs/01-review-linq-search-service.md) — 2 PR/diff gần giống công việc thật;
- [Career Checkpoint — Junior Data/Backend](./career-checkpoint/index.md) — build + debug + review + judgment.

Khuyến nghị cadence:

~~~text
01–05 → Review 01
06–10 → Review 02 + Failure Lab 01–02
11–15 → Review 03
16–20 → Review 04 + Failure Lab 03
21–24 → Review 05 + Failure Lab 04 + PR Review + Career Checkpoint
~~~

## Quality gate

Module chỉ được đánh dấu hoàn thành khi:

- 24/24 bài đạt Lesson Authoring Standard v2;
- sample build với warnings-as-errors;
- test pass;
- SQL Server 2025 smoke test pass;
- metadata freshness pass;
- cross-link pass;
- MkDocs build pass.

Bắt đầu: [LINQ query syntax và method syntax](./01-linq-query-syntax-va-method-syntax.md).
