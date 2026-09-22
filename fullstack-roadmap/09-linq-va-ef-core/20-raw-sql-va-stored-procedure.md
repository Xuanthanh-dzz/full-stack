# Raw SQL và stored procedure

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/provider major update, API/security/testing behavior change, sample CI failure

## TL;DR

- Raw SQL là escape hatch khi LINQ không diễn đạt/translate tốt hoặc cần tận dụng SQL/stored procedure đã có.
- Value phải parameterize; `FromSqlRaw` với string input ghép tay là đường ngắn tới SQL injection.
- Raw SQL không miễn bạn khỏi mapping, transaction, permission, execution plan và migration ownership.

## 1. Mục tiêu

- dùng raw SQL query an toàn;
- parameterize input;
- gọi stored procedure/query result;
- biết khi nào quay lại LINQ;
- review security/maintainability trade-off.

## 2. Bài toán mở đầu

### Trực giác 60 giây

EF LINQ rất tiện, nhưng không phải mọi query nên hoặc có thể biểu diễn tốt bằng LINQ. Raw SQL là **lối thoát có kiểm soát** để bạn nói trực tiếp với database.

Stored procedure là chương trình/query được đặt phía database và gọi theo contract.

Điểm quan trọng: dùng raw SQL không có nghĩa “bỏ ORM” hay “khỏi lo security”. Bạn vẫn cần parameter, mapping, permission và execution plan.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| raw SQL | SQL do developer viết trực tiếp |
| parameterization | tách value khỏi SQL text |
| SQL injection | input làm thay đổi cấu trúc SQL ngoài ý muốn |
| stored procedure | routine lưu trong database |
| result shape | các column/type query trả về |
| escape hatch | lựa chọn thoát khỏi abstraction khi cần |

Default tốt là LINQ nếu rõ và plan tốt; raw SQL khi có driver cụ thể.

Report dùng window function/provider-specific hint hoặc stored procedure legacy đã được DBA tune. Viết lại thành LINQ có thể khó đọc hoặc SQL generated không đạt plan mong muốn.

## 3. Lời giải chạy được

Parameterized interpolation:

~~~csharp
var minPrice = 1_000_000m;

var products = await db.Products
    .FromSqlInterpolated($"""
        SELECT ProductId, Sku, Name, Price, IsActive, CreatedAt
        FROM catalog.Products
        WHERE Price >= {minPrice}
        """)
    .AsNoTracking()
    .ToListAsync(cancellationToken);
~~~

Không nối input:

~~~text
BAD: "... WHERE Name = '" + userInput + "'"
GOOD: parameter/interpolated API that parameterizes values
~~~

### Walkthrough parameterization

Nguy hiểm:

~~~text
input = "x' OR 1=1 --"

SQL string concatenate:
WHERE Name = 'x' OR 1=1 --'
~~~

Input đã chui vào **cấu trúc SQL**.

Parameterized approach:

~~~text
SQL:
WHERE Name = @p0

parameter @p0:
"x' OR 1=1 --"
~~~

Database coi input là **giá trị**, không phải một phần syntax SQL.

## 4. Cơ chế hoạt động

### EF LINQ vs raw SQL vs stored procedure

| Tiêu chí | EF LINQ | Raw SQL | Stored procedure |
|---|---|---|---|
| Type-safe/refactor | tốt | thấp hơn | contract riêng |
| Provider abstraction | tốt hơn | provider-specific | rất provider-specific |
| Kiểm soát SQL | gián tiếp | trực tiếp | trực tiếp |
| Query đặc thù | có thể khó | tốt | tốt |
| Deploy ownership | app | app | thường app/DBA phối hợp |

### Khi nào raw SQL đáng dùng?

- query provider không translate tốt;
- cần SQL feature/hint/provider-specific capability;
- legacy stored procedure đã có contract/tuning;
- hot query cần shape/plan kiểm soát rõ.

### Misconception check

**Đúng hay sai?** Dùng interpolation trong mọi raw SQL đều an toàn.

**Đáp án:** Chỉ khi API cụ thể parameterize interpolation. Phải biết method đang dùng (`FromSqlInterpolated`/safe overload) thay vì đoán.

**Đúng hay sai?** Stored procedure luôn nhanh hơn EF query.

**Đáp án:** Sai. Performance phụ thuộc SQL/plan/index/data, không phải nhãn stored procedure.

### Mini-check

Nếu LINQ tạo SQL đơn giản, readable và plan tốt, raw SQL thêm giá trị gì?

Đáp án: thường không nhiều; nó chỉ tăng maintenance/provider coupling.

Raw SQL API tạo command text + parameter. Interpolated safe API tách value thành parameter thay vì chèn literal trực tiếp.

Entity raw query phải trả shape cần cho materialization hoặc dùng API phù hợp với unmapped/scalar result.

Stored procedure có thể nằm trong cùng transaction nhưng contract/result shape cần versioning/documentation.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** parameterized raw SQL và injection mental model.

**Working developer:** chọn LINQ/raw/proc theo driver và test result shape.

**Deep dive:** command interception, TVP, provider-specific SQL, plan forcing.

Module 08 SQL injection, stored procedure và execution plan là prerequisite.

Raw SQL là persistence detail; business layer không nên phụ thuộc string SQL rải rác.

## 6. Lỗi thường gặp

**Dùng `FromSqlRaw` với user string concatenate.** Injection.

**SELECT * trong raw query.** Contract/schema change khó kiểm soát.

**Stored procedure chứa toàn bộ domain workflow chỉ vì 'gần dữ liệu'.** Test/deploy ownership phức tạp.

## 7. Khi nào KHÔNG dùng

Không raw SQL nếu LINQ translation đơn giản, readable và plan tốt.

Không stored procedure cho CRUD trivial chỉ để có thêm layer.

Không dùng raw SQL để bypass mapping/concurrency/security rules mà không có review.

## 8. Production notes & scale check

Team nhỏ: LINQ mặc định, raw SQL cho hot query/legacy SQL có bằng chứng là đủ.

SQL quan trọng nên nằm file/constant có test và review, không string fragment khắp codebase.

Runtime DB user vẫn least privilege dù query do EF hay raw SQL.

## 9. Bài tập kỹ thuật

1. Viết raw query filter Price bằng parameter.
2. Chuyển một raw SQL trivial về LINQ và so readability.
3. Tạo stored procedure report ở lab SQL Server rồi gọi từ data layer.
4. Tìm injection risk trong ba cách build command.

## 10. Bài tập tích hợp liên module — Judgment

DBA cung cấp stored procedure report ổn định nhưng app cần thêm filter động. Chọn modify proc, compose LINQ ngoài result hay query mới? Xem ownership và data volume.

## 11. Retrieval practice

1. Khi nào raw SQL là escape hatch hợp lý?
2. Interpolated parameterized API bảo vệ gì?
3. Raw SQL có bỏ qua need for execution plan không?
4. Vì sao stored procedure trivial có thể là overhead?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy/build được sample liên quan.
- [ ] Tôi biết query/side effect thực sự chạy ở đâu.
- [ ] Tôi phân biệt convenience với abstraction có driver.
- [ ] Tôi nêu được lựa chọn đơn giản hơn cho team nhỏ.

- Bài trước: [Global query filter và interceptor](./19-global-query-filter-va-interceptor.md)
- Bài tiếp theo: [Performance: no-tracking, compiled query và bulk update](./21-performance-no-tracking-compiled-query-bulk-update.md)
- Spaced review: [Review 04 — Loading, concurrency & SQL](./reviews/review-04-loading-concurrency-and-sql.md)
- Failure Lab: [N+1 và cartesian explosion](./failure-labs/03-n-plus-one-va-cartesian-explosion.md)
