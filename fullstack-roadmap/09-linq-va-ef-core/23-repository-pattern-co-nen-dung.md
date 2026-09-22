# Repository Pattern có nên dùng?

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/provider major update, API/security/testing behavior change, sample CI failure

## TL;DR

- EF Core `DbContext`/`DbSet` đã cung cấp nhiều behavior giống Unit of Work/Repository; generic repository CRUD thường chỉ bọc lại API và làm query nghèo đi.
- Repository có giá trị khi nó tạo **domain boundary/port có nghĩa**, che persistence strategy thật hoặc gom query/invariant được reuse.
- Không có câu trả lời 'luôn dùng' hay 'không bao giờ dùng'; hãy yêu cầu một driver cụ thể trước khi thêm abstraction.

## 1. Mục tiêu

- đánh giá generic repository;
- thiết kế repository theo aggregate/use-case;
- phân biệt abstraction có giá trị và forwarding wrapper;
- quyết định có expose IQueryable hay không;
- bảo vệ lựa chọn theo testability/ownership/change pressure.

## 2. Bài toán mở đầu

Team tạo `IGenericRepository<T>` với `GetAll/Add/Update/Delete`, rồi mọi query đặc thù phải thêm method hoặc expose `IQueryable`. Kết quả có thêm layer nhưng không giảm coupling hay complexity.

## 3. Lời giải chạy được

Thay generic CRUD wrapper, một boundary có nghĩa có thể là:

~~~csharp
public interface IOrderHistoryReader
{
    Task<IReadOnlyList<OrderSummary>> GetRecentAsync(
        long customerId,
        int take,
        CancellationToken cancellationToken);
}
~~~

Hoặc với app nhỏ, dùng trực tiếp `CommerceDbContext` trong application service như `OrderReadService` sample.

## 4. Cơ chế hoạt động

Abstraction có giá trị khi caller phụ thuộc capability/domain contract thay vì API persistence chi tiết.

Generic repository thường vẫn leak query need qua method explosion hoặc `IQueryable`, nên không thật sự che EF.

`DbContext` đã quản tracking/SaveChanges transaction boundary; custom UnitOfWork chỉ forward API thường duplicate.

## 5. Kiến thức nền và prerequisites

Repository Pattern từ DDD/PoEAA có context lịch sử khác với ORM hiện đại. Học pattern để nhận driver, không phải checkbox architecture.

Testability không tự tăng vì interface; nếu fake repository behavior khác DB thật, test confidence còn giảm.

## 6. Lỗi thường gặp

**Mỗi entity một repository CRUD identical.** Boilerplate.

**Generic `GetAll()` trả IQueryable rồi gọi là persistence abstraction.** EF semantics vẫn leak.

**Mock repository và bỏ integration test.** Query/mapping bugs không bị bắt.

## 7. Khi nào KHÔNG dùng

Không thêm repository vì tutorial/clean architecture diagram yêu cầu nhưng project chưa có driver.

Không generic repository cho query-rich read side nếu nó cản projection/provider features.

Không abstract provider chỉ vì 'sau này có thể đổi database' khi xác suất thấp và SQL semantics khác sâu.

## 8. Production notes & scale check

Team 2–3 người, một SQL Server, CRUD/business vừa: `DbContext` + application services/query objects thường đủ.

Repository đáng cân nhắc khi aggregate boundary mạnh, persistence phức tạp, nhiều data source, hoặc domain layer cần port độc lập có giá trị.

ADR nên ghi: driver, alternatives, cost, trigger để revisit.

## 9. Bài tập kỹ thuật

1. Review một generic repository và liệt kê forwarding methods.
2. Refactor thành use-case query service.
3. Thiết kế repository cho aggregate có invariant thật.
4. Viết ADR 'không dùng generic repository' cho CommerceLab.

## 10. Bài tập tích hợp liên module — Judgment

Hệ thống nhỏ 3 dev, SQL Server duy nhất, EF Core query-heavy. Có nên thêm generic repository? Sau đó đổi bối cảnh thành domain library cần chạy với hai persistence backend và so quyết định.

## 11. Retrieval practice

1. DbContext đã giống Unit of Work ở điểm nào?
2. Generic repository thường leak abstraction ra sao?
3. Testability có tự tăng vì interface không?
4. Driver nào làm repository có giá trị?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy/build được sample liên quan.
- [ ] Tôi biết query/side effect thực sự chạy ở đâu.
- [ ] Tôi phân biệt convenience với abstraction có driver.
- [ ] Tôi nêu được lựa chọn đơn giản hơn cho team nhỏ.

- Bài trước: [Testing EF Core với SQLite và Testcontainers](./22-testing-ef-core-voi-sqlite-va-testcontainers.md)
- Bài tiếp theo: [Dự án Data Access cho Web API](./24-du-an-data-access-cho-web-api.md)
