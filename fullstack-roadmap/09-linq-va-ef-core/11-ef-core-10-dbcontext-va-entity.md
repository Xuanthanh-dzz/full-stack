# EF Core 10: DbContext và entity

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/.NET major update, provider breaking change, migration/query behavior change, sample CI failure

## TL;DR

- `DbContext` là session/unit-of-work ngắn hạn quản lý query, tracking và `SaveChanges`; nó không phải singleton thread-safe.
- Entity class mô tả state/domain shape, còn model configuration quyết định mapping relational thực tế.
- EF Core hợp cho phần lớn CRUD/data-access .NET, nhưng không loại bỏ nhu cầu hiểu SQL, index, transaction và execution plan.

## 1. Mục tiêu

- tạo project EF Core 10 với SQL Server provider;
- khai báo entity và `DbSet<T>`;
- cấu hình `DbContextOptions`;
- query dữ liệu async;
- giải thích lifetime và thread-safety của `DbContext`;
- liên hệ entity model với schema Module 08.

## 2. Bài toán mở đầu

Module 08 có CommerceLab schema bằng SQL. Bây giờ Web/API C# cần đọc và ghi dữ liệu mà không muốn tự map `SqlDataReader` cho mọi query.

EF Core cung cấp model, query provider, change tracker và persistence pipeline, nhưng vẫn dựa trên relational database bên dưới.

## 3. Lời giải chạy được

Sample hoàn chỉnh: `samples/module-09/CommerceLab.Data`.

~~~csharp
var options = new DbContextOptionsBuilder<CommerceDbContext>()
    .UseSqlServer(connectionString)
    .Options;

await using var db = new CommerceDbContext(options);

var products = await db.Products
    .AsNoTracking()
    .OrderBy(product => product.Name)
    .Select(product => new { product.ProductId, product.Name, product.Price })
    .ToListAsync(cancellationToken);
~~~

Package baseline:

~~~bash
dotnet add package Microsoft.EntityFrameworkCore.SqlServer --version 10.0.12
dotnet add package Microsoft.EntityFrameworkCore.Design --version 10.0.12
~~~

## 4. Cơ chế hoạt động

`DbContext` giữ model metadata, database connection abstractions, query provider và change tracker.

`DbSet<Product>` là entry point query/entity-set, nhưng query vẫn deferred cho tới terminal operator.

EF Core translate expression tree sang SQL, execute qua provider, đọc rows rồi materialize projection/entity.

`DbContext` không thread-safe. Một context không nên chạy nhiều operation song song.

## 5. Kiến thức nền và prerequisites

Prerequisite trực tiếp: bài 07–10 của module này + transaction/index/query tuning Module 08.

Must know: entity class không đồng nghĩa table 1:1 trong mọi design; owned/complex/projection/raw SQL có thể khác.

Should know: `DbContext` đã mang nhiều behavior của Unit of Work + identity map/change tracking.

## 6. Lỗi thường gặp

**Register `DbContext` singleton.** Tracking state sống quá lâu, thread-safety vỡ.

**Dùng một context cho batch kéo dài hàng giờ.** Tracker phình và stale state tăng.

**Nghĩ EF thay SQL knowledge.** Query LINQ cuối cùng vẫn chịu constraint/index/plan của database.

## 7. Khi nào KHÔNG dùng

Không dùng EF Core chỉ để wrap một stored procedure duy nhất trong utility cực nhỏ nếu ADO.NET/Dapper đơn giản hơn.

Không ép EF Core cho bulk ETL cực lớn nếu dedicated bulk/tooling phù hợp hơn.

Không dùng `DbContext` như cache global.

## 8. Production notes & scale check

ASP.NET Core thông thường dùng scoped `DbContext` theo request. Worker/batch nên tạo scope/context cho unit-of-work rõ.

Team 2–3 người: EF Core trực tiếp trong application service thường đủ; chưa cần repository layer chỉ để 'đúng kiến trúc'.

Connection string lấy từ configuration/secret store, không hard-code. Sample repo cũng bắt buộc `COMMERCE_DB`.

## 9. Bài tập kỹ thuật

1. Thêm entity `Category` và `DbSet<Category>`.
2. Query product projection giá trên 1 triệu.
3. Debug code dùng cùng một context từ hai task song song.
4. Viết lifecycle diagram cho request → context → query → dispose.

## 10. Bài tập tích hợp liên module — Judgment

Service chỉ chạy một query read-only cực tối ưu bằng stored procedure. Chọn EF Core, Dapper hay ADO.NET? Nêu tiêu chí complexity, mapping, profiling và team familiarity.

## 11. Retrieval practice

1. `DbContext` sở hữu những responsibility nào?
2. Vì sao context không nên singleton?
3. `DbSet` có phải list đã load không?
4. EF Core có làm index/SQL knowledge không còn cần không?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy/build được sample liên quan.
- [ ] Tôi giải thích được behavior của EF Core thay vì chỉ nhớ API.
- [ ] Tôi phân biệt demo/local-dev với production.
- [ ] Tôi nêu được khi nào không nên dùng kỹ thuật.

- Bài trước: [Lỗi LINQ và tối ưu](./10-loi-linq-va-toi-uu.md)
- Bài tiếp theo: [Convention, Data Annotation và Fluent API](./12-convention-data-annotation-va-fluent-api.md)
