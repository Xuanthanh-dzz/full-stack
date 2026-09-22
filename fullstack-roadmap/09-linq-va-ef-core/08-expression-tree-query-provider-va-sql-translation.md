# Expression tree, query provider và SQL translation

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14  
> **Review cycle:** 180 days  
> **Re-verify triggers:** .NET LINQ/API change, query-provider behavior change, sample CI failure

## TL;DR

- Expression tree là data structure mô tả code expression; query provider đọc cây đó để tạo query cho nguồn dữ liệu.
- EF Core không 'chạy C# trong SQL Server'; nó translate phần expression được hỗ trợ thành SQL và materialize result về .NET.
- Method C# chạy được in-memory chưa chắc translate được; translation boundary phải được test/inspect.

## 1. Mục tiêu

- tạo và inspect expression tree;
- phân biệt compiled delegate và expression data;
- mô tả pipeline LINQ → expression → provider → SQL → materialization;
- nhận biết translation failure;
- biết dùng `ToQueryString()` khi sang EF Core.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Delegate giống một **máy đã đóng hộp**: bạn có thể bấm nút chạy, nhưng người khác không dễ nhìn vào bên trong để hiểu từng bước.

Expression tree giống một **bản thiết kế dưới dạng object**: nó nói rõ “đọc `Price`, so sánh với 1.000.000, trả bool”. Vì là dữ liệu, EF Core có thể đọc nó và chuyển ý nghĩa sang SQL.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| expression | biểu thức tạo ra giá trị |
| expression tree | object graph mô tả biểu thức |
| node | một phần tử trong tree như `GreaterThan` |
| provider | thành phần hiểu tree |
| translation | chuyển tree sang ngôn ngữ khác, ví dụ SQL |
| materialization | đổi row kết quả thành object/DTO |

Không phải mọi C# expression đều có đối tác trong SQL. Đây là nguồn gốc của nhiều lỗi translation.

Một helper `NormalizeSku()` hoạt động hoàn hảo với `List<Product>` nhưng query EF dùng helper trong `Where` lại không translate. Cần hiểu provider chỉ biết những node/method nó có translator.

## 3. Lời giải chạy được

~~~csharp
using System.Linq.Expressions;

Expression<Func<Product, bool>> expensive = product => product.Price >= 1_000_000m;

Console.WriteLine(expensive.NodeType);
Console.WriteLine(expensive.Body.NodeType);
Console.WriteLine(expensive);

var predicate = expensive.Compile();
var products = new[]
{
    new Product("A", 500_000m),
    new Product("B", 1_500_000m),
};

Console.WriteLine(string.Join(",", products.Where(predicate).Select(x => x.Sku)));

public sealed record Product(string Sku, decimal Price);
~~~

### Walkthrough expression nhỏ

Expression:

~~~csharp
product => product.Price >= 1_000_000m
~~~

Ta có thể hình dung tree:

~~~text
Lambda(product)
  ↓
GreaterThanOrEqual
  ├─ MemberAccess: product.Price
  └─ Constant: 1000000
~~~

Provider nhìn vào cấu trúc này và có thể tạo SQL tương đương:

~~~sql
WHERE Price >= @p0
~~~

Nhưng nếu tree chứa:

~~~csharp
product => MyCustomNormalization(product.Sku) == input
~~~

provider chỉ dịch được nếu nó có translator cho `MyCustomNormalization`. Thông thường nó không tự biết method tùy ý của bạn.

## 4. Cơ chế hoạt động

### Từ LINQ đến SQL từng bước

~~~text
1. C# compiler tạo expression tree object
2. Queryable operator gắn tree vào query
3. EF Core đọc tree
4. EF xác định phần nào có thể translate
5. EF tạo SQL + parameters
6. ADO.NET gửi SQL tới SQL Server
7. SQL Server optimize + execute
8. rows trả về
9. EF materialize result
~~~

### Delegate vs expression tree

| Tiêu chí | Delegate | Expression tree |
|---|---|---|
| Có thể gọi trực tiếp | có | không, trừ compile |
| Dễ inspect structure | không | có |
| Provider có thể translate | không trực tiếp | có thể |
| Chứa mọi C# construct | nhiều hơn | bị giới hạn |

### Misconception check

**Đúng hay sai?** EF Core chạy lambda C# bên trong SQL Server.

**Đáp án:** Sai. EF dịch semantics được hỗ trợ sang SQL; SQL Server không chạy CLR lambda đó.

**Đúng hay sai?** Method compile được trong C# thì chắc chắn query EF cũng chạy.

**Đáp án:** Sai. Compile-time legality và provider translation là hai chuyện khác nhau.

### Mini-check

Nếu một query fail translation, giải pháp đầu tiên có nên là `AsEnumerable()` không?

Đáp án: không. Trước tiên phải hiểu data volume, generated query và xem có thể viết expression translatable hoặc đổi data model/query shape không.

Delegate là executable code. Expression tree là object graph như `Lambda → GreaterThanOrEqual → MemberAccess + Constant`.

`IQueryProvider` nhận expression tree và tạo query/execution phù hợp. EF Core có translation pipeline cho member/method/operator đã hỗ trợ.

Sau SQL execution, provider đọc row và materialize projection/entity. Business method tùy ý không tự nhiên tồn tại trong SQL.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** expression tree là dữ liệu mô tả code.

**Working developer:** biết translation boundary và inspect generated SQL.

**Deep dive:** provider translator pipeline, custom translation và expression visitor.

Expression tree bị giới hạn so với toàn bộ syntax C#. Đây là lý do một số lambda compile được nhưng không thể trở thành expression tree/SQL translation.

Module 08 execution plan vẫn là nguồn sự thật về cost trong SQL Server; expression tree chỉ là input cho translator.

## 6. Lỗi thường gặp

**Nghĩ mọi method .NET đều translate.** Chỉ các pattern/provider translator hỗ trợ mới đi server-side.

**Bắt exception translation rồi gọi `AsEnumerable` ngay.** Có thể biến lỗi rõ thành performance bug âm thầm.

**Đánh giá query chỉ từ C# syntax.** Phải xem generated SQL và plan khi quan trọng.

## 7. Khi nào KHÔNG dùng

Không dùng expression tree tự dựng nếu predicate tĩnh/lambda thường đã đủ; code dynamic expression dễ khó maintain.

Không viết query provider riêng cho app thông thường.

Không cố nhét domain algorithm phức tạp vào SQL translation chỉ vì có thể.

## 8. Production notes & scale check

Với EF Core, `ToQueryString()` hữu ích cho inspection nhưng không thay actual execution plan/statistics.

Ở team nhỏ, dynamic filters bằng composition lambda đơn giản thường đủ; tránh framework expression-builder quá sớm.

Khi translation thay đổi theo EF/provider version, freshness metadata và integration test là hàng rào.

## 9. Bài tập kỹ thuật

1. Inspect expression `x => x.Name.StartsWith("A") && x.Price > 10`.
2. So `Func<Product,bool>` và `Expression<Func<Product,bool>>`.
3. Tạo helper method và dự đoán liệu provider generic có thể tự translate không.
4. Vẽ pipeline từ API request tới SQL result.

## 10. Bài tập tích hợp liên module — Judgment

Bạn cần search text có normalization đặc thù. Chọn normalize trong C#, computed column/index, database function hay search engine? Đưa ra decision tree theo data size và query frequency.

## 11. Retrieval practice

1. Expression tree khác delegate ở đâu?
2. Provider dùng tree để làm gì?
3. Vì sao C# method bất kỳ không thành SQL tự động?
4. `ToQueryString` giúp gì và không giúp gì?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy được sample.
- [ ] Tôi giải thích được cardinality/execution của operator chính.
- [ ] Tôi phân biệt được in-memory và provider-backed behavior.
- [ ] Tôi nêu được trường hợp không nên dùng kỹ thuật.

- Bài trước: [IEnumerable và IQueryable](./07-ienumerable-va-iqueryable.md)
- Bài tiếp theo: [Composition và dynamic query](./09-composition-va-dynamic-query.md)
