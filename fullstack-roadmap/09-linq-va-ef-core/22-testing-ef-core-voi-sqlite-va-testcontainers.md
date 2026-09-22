# Testing EF Core với SQLite và Testcontainers

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/provider major update, API/security/testing behavior change, sample CI failure

## TL;DR

- Test data-access cần relational behavior; fake/in-memory provider có thể bỏ qua SQL translation, constraint và provider-specific semantics.
- SQLite in-memory nhanh cho nhiều relational test nhưng **không phải SQL Server**; critical query/migration nên chạy trên SQL Server thật qua container/Testcontainers.
- Chọn test pyramid theo rủi ro: nhiều test nhanh + một số provider-real integration test có giá trị hơn việc mock mọi `DbSet`.

## 1. Mục tiêu

- viết SQLite in-memory integration test;
- giải thích provider difference;
- khởi động SQL Server bằng Testcontainers;
- chọn test nào cần provider thật;
- tránh mock query provider giả tạo confidence.

## 2. Bài toán mở đầu

Test dùng EF InMemory pass, production SQL Server fail vì query không translate hoặc constraint/case sensitivity khác. Test đã kiểm tra business list behavior, không kiểm tra relational contract thật.

## 3. Lời giải chạy được

Sample repo có SQLite test tại `samples/module-09/CommerceLab.Data.Tests`.

~~~csharp
await using var connection = new SqliteConnection("Data Source=:memory:");
await connection.OpenAsync();

var options = new DbContextOptionsBuilder<CommerceDbContext>()
    .UseSqlite(connection)
    .Options;

await using var db = new CommerceDbContext(options);
await db.Database.EnsureCreatedAsync();
~~~

Provider-real test bằng Testcontainers.MsSql 4.15.0:

~~~csharp
var container = new MsSqlBuilder(
        "mcr.microsoft.com/mssql/server:2025-latest")
    .Build();

await container.StartAsync();
var connectionString = container.GetConnectionString();
~~~

## 4. Cơ chế hoạt động

SQLite in-memory vẫn có relational engine, SQL generation và constraints nhất định, nên tốt hơn pure fake cho nhiều test.

Nhưng provider differences vẫn tồn tại: schema, SQL functions, type behavior, case/collation, migrations.

Testcontainers quản lifecycle Docker dependency, cấp connection string tạm và cleanup sau test.

## 5. Kiến thức nền và prerequisites

Testing strategy phải mirror failure mode cần bắt. Unit test domain không cần database; query translation/provider semantics thì cần relational/provider integration.

CI của module dùng SQL Server 2025 container trực tiếp; Testcontainers là cách đóng gói lifecycle tương tự trong test code.

## 6. Lỗi thường gặp

**Mock `DbSet` để test LINQ translation.** Mock không phải EF provider.

**Tin SQLite chứng minh SQL Server migration đúng.** Provider khác.

**Mọi test đều spin SQL Server container riêng.** Suite chậm, resource waste.

## 7. Khi nào KHÔNG dùng

Không dùng Testcontainers cho pure domain function không chạm persistence.

Không dùng SQLite để assert SQL Server-specific feature.

Không integration-test mọi getter/setter; tập trung query, mapping, constraint, transaction và migration critical.

## 8. Production notes & scale check

Team nhỏ: shared SQL Server container per test collection/CI job + SQLite tests nhanh là balance tốt.

Pin image/package version; tránh `latest` nếu reproducibility critical — course CI có thể reverify image cập nhật theo freshness policy.

Seed test deterministic và isolation rõ; không phụ thuộc state test trước.

## 9. Bài tập kỹ thuật

1. Viết SQLite test cho global filter.
2. Viết test constraint unique Email.
3. Chạy cùng query trên SQLite và SQL Server container.
4. Tìm một provider difference và biến thành regression test.

## 10. Bài tập tích hợp liên module — Judgment

Query dùng SQL Server full-text/vector/provider function. Bạn giữ SQLite test hay chuyển critical test sang Testcontainers? Thiết kế test pyramid không làm CI quá chậm.

## 11. Retrieval practice

1. Vì sao EF InMemory không đủ cho translation test?
2. SQLite giúp gì và thiếu gì?
3. Testcontainers kiểm tra failure mode nào?
4. Test nào không cần database?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy/build được sample liên quan.
- [ ] Tôi biết query/side effect thực sự chạy ở đâu.
- [ ] Tôi phân biệt convenience với abstraction có driver.
- [ ] Tôi nêu được lựa chọn đơn giản hơn cho team nhỏ.

- Bài trước: [Performance: no-tracking, compiled query và bulk update](./21-performance-no-tracking-compiled-query-bulk-update.md)
- Bài tiếp theo: [Repository Pattern có nên dùng?](./23-repository-pattern-co-nen-dung.md)
