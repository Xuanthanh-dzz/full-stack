# IEnumerable và IQueryable

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14  
> **Review cycle:** 180 days  
> **Re-verify triggers:** .NET LINQ/API change, query-provider behavior change, sample CI failure

## TL;DR

- `IEnumerable<T>` mô tả enumeration object trong .NET; `IQueryable<T>` còn mang expression tree cho query provider.
- Chuyển từ `IQueryable` sang `IEnumerable` có thể đổi nơi thực thi operator sau đó từ database sang process.
- Giữ `IQueryable` ở data-access boundary đủ lâu để compose, nhưng đừng leak nó khắp architecture nếu caller không nên kiểm soát query.

## 1. Mục tiêu

- phân biệt contract của `IEnumerable<T>` và `IQueryable<T>`;
- nhận ra `AsEnumerable` là execution-location boundary logic;
- giải thích vì sao lambda của `IQueryable` có thể thành expression tree;
- tránh accidental client-side work;
- chọn boundary trả DTO/list/query theo ownership.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Đây là bài phải hiểu bằng mental model, không học thuộc interface.

`IEnumerable<T>` có thể nghĩ là: **“khi anh hỏi, tôi sẽ đưa từng object .NET cho anh.”**

`IQueryable<T>` thêm một khả năng khác: **“tôi còn giữ bản mô tả truy vấn để một provider khác có thể hiểu và thực thi.”**

Với EF Core, provider đó là EF; nó đọc bản mô tả và cố dịch sang SQL Server.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| enumerable | nguồn có thể lấy từng phần tử |
| queryable | nguồn có thể giữ/mở rộng mô tả query |
| delegate | code .NET có thể gọi |
| expression tree | object graph mô tả một biểu thức |
| query provider | thành phần đọc query description và thực thi/dịch nó |
| client-side | chạy trong process app |
| server-side | chạy ở data source, ví dụ SQL Server |

Điểm quan trọng: `IQueryable` **không phải database**. Nó chỉ là contract cho provider-backed query. `EnumerableQuery` in-memory cũng có thể implement `IQueryable`.

Một query EF đang filter ở SQL. Developer chèn `AsEnumerable()` để dùng helper C#, rồi đặt `Where` tiếp theo. Code vẫn chạy nhưng filter mới không còn được database xử lý.

## 3. Lời giải chạy được

~~~csharp
var data = new[] { 1, 2, 3, 4, 5 };

IEnumerable<int> enumerable = data;
IQueryable<int> queryable = data.AsQueryable();

var enumerableResult = enumerable
    .Where(x => x > 2)
    .Select(x => x * 10);

var queryableResult = queryable
    .Where(x => x > 2)
    .Select(x => x * 10);

Console.WriteLine(enumerableResult.GetType().Name);
Console.WriteLine(queryableResult.Expression.NodeType);
Console.WriteLine(queryableResult.Expression);
~~~

### Walkthrough: cùng `Where`, khác overload

Với:

~~~csharp
IEnumerable<Product> a = products;
IQueryable<Product> b = db.Products;
~~~

Cùng viết:

~~~csharp
.Where(p => p.Price > 1000)
~~~

nhưng compiler có thể chọn hai API khác:

~~~text
a.Where(...)
→ Enumerable.Where
→ nhận Func<Product,bool>
→ delegate chạy trên object .NET

b.Where(...)
→ Queryable.Where
→ nhận Expression<Func<Product,bool>>
→ expression được provider đọc/dịch
~~~

Đây là lý do một lambda trông giống nhau nhưng nơi thực thi khác nhau.

## 4. Cơ chế hoạt động

### Pipeline đầy đủ với EF Core

~~~text
C# code
  ↓
IQueryable<Order>
  ↓ .Where/.Select/.OrderBy
expression tree lớn dần
  ↓ terminal operator ToListAsync
EF Core query translator
  ↓
SQL
  ↓
SQL Server executes
  ↓
rows
  ↓
EF materializes DTO/entity
~~~

### `IEnumerable` vs `IQueryable`

| Tiêu chí | `IEnumerable<T>` | `IQueryable<T>` |
|---|---|---|
| Operator chính | `Enumerable.*` | `Queryable.*` |
| Lambda | delegate `Func` | expression tree |
| Thường chạy ở | process .NET | provider quyết định |
| Provider translation | không | có thể |
| Dùng cho list/array | tự nhiên | thường không cần |
| Dùng cho EF composition | sau materialization | trước materialization |

### `AsEnumerable()` thực sự làm gì?

Nó **không tự chạy query ngay**. Nó thay static view của pipeline để các operator phía sau dùng LINQ to Objects.

Ví dụ:

~~~text
db.Products                  IQueryable
.Where(IsActive)             still provider-backed
.AsEnumerable()              switch operator family
.Where(CustomHelper)         now .NET-side logic
~~~

Query database có thể chỉ filter `IsActive`; phần `CustomHelper` chạy sau khi rows được đọc.

### Misconception check

**Đúng hay sai?** `AsEnumerable()` tương đương `ToList()`.

**Đáp án:** Sai. `ToList()` materialize ngay; `AsEnumerable()` chủ yếu đổi cách các operator sau được bind.

**Đúng hay sai?** `IQueryable<T>` luôn sinh SQL.

**Đáp án:** Sai. Nó phụ thuộc provider.

### Mini-check

Nếu 2 triệu product đi qua `AsEnumerable()` trước filter SKU, nguy cơ lớn nhất là gì?

Đáp án: quá nhiều row bị kéo về process trước khi filter local.

`IEnumerable<T>` operator thường nhận `Func<T,...>` và chạy delegate trên object .NET.

`IQueryable<T>` operator nhận `Expression<Func<T,...>>`. Provider nhận expression tree, phân tích rồi quyết định cách thực thi — EF Core thường dịch phần hỗ trợ sang SQL.

`AsEnumerable()` không tự chạy query ngay, nhưng operator LINQ-to-Objects phía sau nó không còn được query provider translate.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** biết `IEnumerable` = object stream; `IQueryable` = query description + provider.

**Working developer:** biết giữ filter/projection server-side đủ lâu và đặt materialization boundary rõ.

**Deep dive:** overload resolution, provider translation internals, expression tree limitations.

Extension method overload resolution chọn `Enumerable.Where` hay `Queryable.Where` dựa trên static type của source.

Must know: `IQueryable` không đồng nghĩa SQL; provider có thể là nguồn khác.

Deep dive: expression tree không chứa mọi construct C# tùy ý; translation còn phụ thuộc provider.

## 6. Lỗi thường gặp

**`AsEnumerable` giữa query để 'fix translation'.** Có thể tải tập lớn rồi filter local.

**Return `IQueryable` từ mọi repository.** Caller có thể tạo query không kiểm soát, khó enforce performance/security rules.

**Tin type runtime mà không nhìn static chain.** Operator overload được chọn từ compile-time context.

## 7. Khi nào KHÔNG dùng

Không dùng `IQueryable` cho collection đã nhỏ và in-memory chỉ để 'trông enterprise'.

Không expose `IQueryable` qua network/service boundary.

Không ép helper business logic thành expression chỉ để giữ translation nếu logic đó thực sự nên chạy sau materialization.

## 8. Production notes & scale check

Team nhỏ có thể giữ `IQueryable` bên trong application/data-access service rồi materialize DTO trước khi return.

Boundary tốt thường là: compose query → projection → async materialization → trả result rõ shape.

Code review nên hỏi: 'operator này chạy ở database hay process?'

## 9. Bài tập kỹ thuật

1. Viết function nhận `IEnumerable<int>` và một function nhận `IQueryable<int>` rồi inspect expression.
2. Đặt `AsEnumerable()` ở ba vị trí và giải thích nơi filter chạy.
3. Debug query accidental client filtering.
4. Viết API data-service trả `Task<List<OrderSummary>>` thay vì leak `IQueryable`.

## 10. Bài tập tích hợp liên module — Judgment

Business rule dùng thư viện C# không thể translate SQL. Chọn: materialize trước rule, precompute column, viết SQL function/query khác hay đổi requirement? Nêu trade-off data volume và maintainability.

## 11. Retrieval practice

1. `IQueryable` thêm gì so với `IEnumerable`?
2. `AsEnumerable` có execute ngay không?
3. Vì sao expression tree cần provider?
4. Khi nào không nên expose `IQueryable`?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy được sample.
- [ ] Tôi giải thích được cardinality/execution của operator chính.
- [ ] Tôi phân biệt được in-memory và provider-backed behavior.
- [ ] Tôi nêu được trường hợp không nên dùng kỹ thuật.

- Bài trước: [Deferred execution và materialization](./06-deferred-execution-va-materialization.md)
- Bài tiếp theo: [Expression tree, query provider và SQL translation](./08-expression-tree-query-provider-va-sql-translation.md)
