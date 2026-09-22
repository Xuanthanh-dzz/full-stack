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

## 4. Cơ chế hoạt động

Delegate là executable code. Expression tree là object graph như `Lambda → GreaterThanOrEqual → MemberAccess + Constant`.

`IQueryProvider` nhận expression tree và tạo query/execution phù hợp. EF Core có translation pipeline cho member/method/operator đã hỗ trợ.

Sau SQL execution, provider đọc row và materialize projection/entity. Business method tùy ý không tự nhiên tồn tại trong SQL.

## 5. Kiến thức nền và prerequisites

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
