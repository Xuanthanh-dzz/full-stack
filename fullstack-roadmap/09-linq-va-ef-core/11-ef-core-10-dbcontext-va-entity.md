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

### Trực giác 60 giây

EF Core là một lớp trung gian giúp C# nói chuyện với relational database bằng object/query thay vì tự viết mapping cho mọi câu lệnh.

`DbContext` có thể hình dung như **một phiên làm việc ngắn với database**. Trong phiên đó, nó biết model nào map vào table nào, query nào đang được dựng, và entity nào đang được theo dõi để save.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| ORM | công cụ ánh xạ object ↔ relational data |
| entity | object đại diện dữ liệu có identity |
| `DbContext` | phiên làm việc/data-access unit ngắn hạn |
| `DbSet<T>` | entry point để query/attach entity loại T |
| provider | adapter EF cho database cụ thể |
| materialize | biến row thành object/DTO |
| tracking | EF nhớ entity state để phát hiện thay đổi |

EF Core **không thay database**. SQL Server vẫn chịu trách nhiệm lưu trữ, constraint, transaction, optimizer và execution plan.

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

### Walkthrough một read request

~~~text
1. App tạo DbContext với SQL Server options
2. Code gọi db.Products.Where(...).Select(...)
3. EF chưa nhất thiết query ngay
4. ToListAsync() kích hoạt execution
5. EF dịch expression → SQL
6. Provider gửi SQL qua ADO.NET
7. SQL Server execute
8. rows trả về
9. EF materialize anonymous/DTO result
10. DbContext được dispose cuối scope
~~~

Với command/update, còn thêm change tracker và `SaveChanges`.

## 4. Cơ chế hoạt động

### `DbContext` đang giữ state gì?

- model metadata;
- change tracker entries;
- service/provider configuration;
- transaction/connection abstractions;
- identity resolution trong scope;
- pending entity states như Added/Modified/Deleted.

### Vì sao không singleton?

Vì state tracking thuộc **một unit of work**, không phải toàn application. Nếu giữ context sống lâu:

- tracker phình;
- dữ liệu tracked stale;
- nhiều request chạm cùng state;
- thread-safety bị phá.

### `DbSet<T>` không phải `List<T>`

| `List<T>` | `DbSet<T>` |
|---|---|
| object đã nằm trong RAM | query entry point |
| `Where` chạy LINQ to Objects | thường tạo `IQueryable` |
| không có provider SQL | có EF provider |
| không tự persist | liên quan context persistence |

### Misconception check

**Đúng hay sai?** `db.Products` nghĩa là toàn bộ Products đã được load.

**Đáp án:** Sai. Nó là queryable entry point; rows chỉ được lấy khi query execute.

**Đúng hay sai?** EF Core cho phép bỏ qua SQL/index kiến thức.

**Đáp án:** Sai. ORM chỉ đổi cách bạn biểu diễn data access.

### Mini-check

Tại sao một context cho mỗi request thường hợp lý hơn một context cho toàn app?

Đáp án: scope state/tracking theo unit of work, tránh stale/thread-safety/memory growth.

`DbContext` giữ model metadata, database connection abstractions, query provider và change tracker.

`DbSet<Product>` là entry point query/entity-set, nhưng query vẫn deferred cho tới terminal operator.

EF Core translate expression tree sang SQL, execute qua provider, đọc rows rồi materialize projection/entity.

`DbContext` không thread-safe. Một context không nên chạy nhiều operation song song.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** entity, DbSet, DbContext và lifetime.

**Working developer:** scoped context, async query, projection, no hard-coded secrets.

**Deep dive:** model cache, service provider internals, context pooling.

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
