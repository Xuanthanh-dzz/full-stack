# Join và GroupJoin

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14  
> **Review cycle:** 180 days  
> **Re-verify triggers:** .NET LINQ/API change, query-provider behavior change, sample CI failure

## TL;DR

- `Join` biểu diễn inner join theo key; `GroupJoin` giữ outer element kèm nhóm inner matches.
- Join trong LINQ to Objects dùng equality/comparer in-memory; join trên `IQueryable` phụ thuộc query provider và SQL translation.
- .NET 10 có `LeftJoin`/`RightJoin`, nhưng hiểu `Join`/`GroupJoin` vẫn cần để đọc code cũ và reasoning cardinality.

## 1. Mục tiêu

- viết inner join bằng `Join`;
- dùng `GroupJoin` để giữ customer chưa có order;
- reasoning one-to-many cardinality;
- nhận biết khi navigation property rõ hơn manual join;
- liên hệ join LINQ với SQL join ở Module 08.

## 2. Bài toán mở đầu

Ta có customer và order ở hai collection riêng. Báo cáo cần vừa lấy các order có customer hợp lệ, vừa có màn hình customer kể cả khi chưa từng order.

## 3. Lời giải chạy được

~~~csharp
var customers = new[]
{
    new Customer(1, "An"),
    new Customer(2, "Bình"),
    new Customer(3, "Chi"),
};

var orders = new[]
{
    new Order(101, 1, 1_000m),
    new Order(102, 1, 2_000m),
    new Order(201, 2, 5_000m),
};

var inner = customers.Join(
    orders,
    customer => customer.Id,
    order => order.CustomerId,
    (customer, order) => $"{customer.Name}:{order.Id}");

var grouped = customers.GroupJoin(
    orders,
    customer => customer.Id,
    order => order.CustomerId,
    (customer, matches) => new
    {
        customer.Name,
        OrderCount = matches.Count(),
    });

Console.WriteLine(string.Join(" | ", inner));
Console.WriteLine(string.Join(" | ", grouped.Select(x => $"{x.Name}:{x.OrderCount}")));

public sealed record Customer(int Id, string Name);
public sealed record Order(int Id, int CustomerId, decimal TotalAmount);
~~~

## 4. Cơ chế hoạt động

`Join` build/match key pairs và phát một result cho mỗi match. Với one-to-many, outer row lặp theo số child match.

`GroupJoin` phát đúng một result cho mỗi outer element, nhưng inner part là sequence. Nó là nền cho pattern left join cổ điển bằng `GroupJoin + DefaultIfEmpty`.

Trong .NET 10, `LeftJoin` và `RightJoin` là operator trực tiếp; EF Core 10 nhận diện và dịch chúng. Tuy vậy codebase cũ vẫn đầy `GroupJoin`, nên hiểu cơ chế là bắt buộc.

## 5. Kiến thức nền và prerequisites

Module 08 đã dạy INNER/LEFT/RIGHT/FULL/CROSS JOIN và cardinality. Dùng kiến thức đó để dự đoán số row trước khi viết LINQ.

Must know: join key phải có semantics equality ổn định.

Should know: với EF Core navigation, `order.Customer.Email` thường rõ hơn manual join; provider vẫn tạo join cần thiết.

## 6. Lỗi thường gặp

**Join theo Name/Email thay vì key ổn định.** Business field có thể đổi hoặc không unique.

**Dùng `GroupJoin` nhưng enumerate `matches` nhiều lần với work đắt.** Materialize nếu thật sự reuse.

**Dùng `Distinct` để che join condition thiếu.** Phải sửa relation/cardinality.

## 7. Khi nào KHÔNG dùng

Không manual join nếu navigation đã mô hình đúng và projection qua navigation rõ hơn.

Không join in-memory hai tập cực lớn đã được tải từ database chỉ vì LINQ syntax tiện.

Không dùng left join chỉ để rồi `WHERE right != null`; đó thường là inner join trá hình.

## 8. Production notes & scale check

Với .NET 10/EF Core 10, ưu tiên `LeftJoin` nếu nó làm intent dễ đọc hơn; không rewrite code cũ chỉ để dùng API mới nếu không có lợi ích.

Team nhỏ: navigation + projection thường đủ, không cần abstraction join helper riêng.

Luôn inspect SQL khi join nhiều navigation vì row multiplication có thể gây payload lớn.

## 9. Bài tập kỹ thuật

1. Join order với customer và projection `(OrderId, CustomerName)`.
2. GroupJoin để tìm customer có zero order.
3. Viết left join bằng API `.LeftJoin` trên .NET 10.
4. Debug một join dùng non-unique display name làm key.

## 10. Bài tập tích hợp liên module — Judgment

Bạn có Product và Category many-to-many. Chọn navigation projection, manual LINQ join hay raw SQL cho report 20 triệu rows? Nêu driver về readability, translation và plan.

## 11. Retrieval practice

1. `Join` tương ứng loại join nào?
2. `GroupJoin` giữ outer row thế nào?
3. Vì sao cardinality phải được dự đoán trước?
4. Khi nào navigation tốt hơn manual join?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy được sample.
- [ ] Tôi giải thích được cardinality/execution của operator chính.
- [ ] Tôi phân biệt được in-memory và provider-backed behavior.
- [ ] Tôi nêu được trường hợp không nên dùng kỹ thuật.

- Bài trước: [Aggregate, GroupBy và ToLookup](./04-aggregate-groupby-va-tolookup.md)
- Bài tiếp theo: [Deferred execution và materialization](./06-deferred-execution-va-materialization.md)
