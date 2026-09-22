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

### Trực giác 60 giây

Join trả lời câu hỏi: **làm sao nối dữ liệu từ hai nguồn theo một key chung?**

Ví dụ:

~~~text
Customers                  Orders
1  An                      101  CustomerId=1
2  Bình                    102  CustomerId=1
3  Chi                     201  CustomerId=2
~~~

Nếu muốn biết `Order 101` thuộc ai, ta so `Customer.Id` với `Order.CustomerId`.

`Join` cho ta từng cặp match. `GroupJoin` thì khác: nó giữ mỗi customer một lần và gom tất cả order match thành một nhóm bên cạnh customer đó.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| join key | giá trị dùng để nối hai tập |
| outer sequence | tập bên ngoài/được duyệt chính |
| inner sequence | tập được match vào outer |
| inner join | chỉ giữ phần có match |
| group join | mỗi outer giữ một nhóm inner matches |
| cardinality | số row/phần tử sau join |

Cardinality là trọng tâm: nếu một customer có 10 orders, `Join` tạo 10 result cho customer đó; `GroupJoin` vẫn tạo một result nhưng bên trong chứa 10 order.

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

### Walkthrough từng bước

Với `customers.Join(orders, ...)`:

~~~text
Customer 1 (An)
  compare key 1 với Order.CustomerId
  → match 101
  → match 102

Customer 2 (Bình)
  → match 201

Customer 3 (Chi)
  → không có match
~~~

Output inner join:

~~~text
An:101
An:102
Bình:201
~~~

Với `GroupJoin`, output về mặt ý tưởng:

~~~text
An   → [101, 102]
Bình → [201]
Chi  → []
~~~

Vì vậy `GroupJoin` đặc biệt hữu ích khi bạn muốn giữ outer element kể cả không có inner match.

## 4. Cơ chế hoạt động

### `Join` vs `GroupJoin` vs navigation

| Cách | Output | Khi dễ đọc nhất |
|---|---|---|
| `Join` | mỗi cặp match một row | hai tập độc lập, inner join rõ |
| `GroupJoin` | outer + nhóm matches | cần outer kể cả không match |
| navigation EF | đi qua quan hệ model | entity relationship đã map tốt |

### Vì sao navigation thường rõ hơn trong EF?

Nếu `Order` đã có `Customer`, code:

~~~csharp
order.Customer.Email
~~~

thể hiện domain relationship trực tiếp. EF vẫn có thể sinh JOIN SQL bên dưới; bạn không cần tự viết join chỉ để chứng minh mình biết join.

### Misconception check

**Đúng hay sai?** `GroupJoin` chỉ là cách viết khác của `Join` và output cardinality giống nhau.

**Đáp án:** Sai. `GroupJoin` giữ một outer result và đặt matches vào sequence.

**Đúng hay sai?** Có duplicate sau join thì cứ thêm `Distinct()` là được.

**Đáp án:** Không. Duplicate có thể phản ánh cardinality thật hoặc join condition sai. `Distinct` có thể che bug.

### Mini-check

Một customer có 5 orders. `Join` customer-orders tạo mấy result cho customer đó? `GroupJoin` tạo mấy outer result?

Đáp án: `Join` tạo 5; `GroupJoin` tạo 1 outer result chứa 5 matches.

`Join` build/match key pairs và phát một result cho mỗi match. Với one-to-many, outer row lặp theo số child match.

`GroupJoin` phát đúng một result cho mỗi outer element, nhưng inner part là sequence. Nó là nền cho pattern left join cổ điển bằng `GroupJoin + DefaultIfEmpty`.

Trong .NET 10, `LeftJoin` và `RightJoin` là operator trực tiếp; EF Core 10 nhận diện và dịch chúng. Tuy vậy codebase cũ vẫn đầy `GroupJoin`, nên hiểu cơ chế là bắt buộc.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** hiểu key matching và cardinality.

**Working developer:** biết khi nào navigation rõ hơn manual join.

**Deep dive:** translation sang SQL, left/right join API .NET 10 và row multiplication.

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
- Spaced review: [Review 01 — LINQ core](./reviews/review-01-linq-core.md)
