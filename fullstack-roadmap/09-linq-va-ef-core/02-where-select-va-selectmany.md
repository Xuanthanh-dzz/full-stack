# Where, Select và SelectMany

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14  
> **Review cycle:** 180 days  
> **Re-verify triggers:** .NET/EF Core major update, LINQ behavior/API change, sample CI failure

## TL;DR

- `Where` giảm số phần tử, `Select` đổi shape, còn `SelectMany` flatten collection lồng nhau.
- Projection sớm giúp code và query database chỉ mang dữ liệu cần thiết.
- `SelectMany` rất mạnh nhưng dễ làm nổ số row nếu bạn không reasoning cardinality.

## 1. Mục tiêu

- filter collection bằng `Where`;
- projection sang anonymous type/record bằng `Select`;
- flatten quan hệ one-to-many bằng `SelectMany`;
- reasoning cardinality trước và sau flatten;
- liên hệ projection LINQ với `SELECT`/`JOIN` trong SQL.

## 2. Bài toán mở đầu

Một order có nhiều item. Báo cáo cần danh sách từng dòng hàng đã bán, không phải danh sách order chứa nested collection.

Ta cần đi từ `IEnumerable<Order>` sang một stream phẳng của item kèm OrderId.

## 3. Lời giải chạy được

~~~csharp
var orders = new[]
{
    new Order(101, "Paid", [new("KB-01", 2), new("MS-01", 1)]),
    new Order(102, "Pending", [new("MN-01", 1)]),
};

var soldLines = orders
    .Where(order => order.Status == "Paid")
    .SelectMany(
        order => order.Items,
        (order, item) => new SoldLine(order.Id, item.Sku, item.Quantity))
    .ToList();

foreach (var line in soldLines)
{
    Console.WriteLine($"{line.OrderId}:{line.Sku} x{line.Quantity}");
}

public sealed record Order(int Id, string Status, IReadOnlyList<OrderItem> Items);
public sealed record OrderItem(string Sku, int Quantity);
public sealed record SoldLine(int OrderId, string Sku, int Quantity);
~~~

Expected:

~~~text
101:KB-01 x2
101:MS-01 x1
~~~

## 4. Cơ chế hoạt động

`Where` giữ nguyên type phần tử nhưng loại phần tử không đạt predicate.

`Select` ánh xạ mỗi input element thành đúng một output element. Output có thể là scalar, record, DTO hoặc anonymous type.

`SelectMany` ánh xạ mỗi outer element sang một inner sequence rồi nối các sequence đó. Cardinality có thể tăng mạnh: 1.000 order × trung bình 20 item → khoảng 20.000 output row.

## 5. Kiến thức nền và prerequisites

Liên hệ Module 08: `Where` gần với SQL `WHERE`, projection gần với column list trong `SELECT`, còn `SelectMany` có thể tương ứng join/cross apply tùy provider và expression.

Projection không phải mapping entity đầy đủ. Với API read model, projection trực tiếp thường tốt hơn load entity graph rồi map.

## 6. Lỗi thường gặp

**Flatten trước rồi mới filter outer object.** Có thể làm nhiều work hơn cần thiết.

**Select entity rồi mutate trong read pipeline.** Tách read projection khỏi command/update flow.

**Quên cardinality.** `SelectMany` trên hai collection lồng nhau có thể tạo Cartesian-like explosion.

## 7. Khi nào KHÔNG dùng

Không dùng `SelectMany` nếu domain cần giữ hierarchy. Flatten để rồi group lại ngay sau đó thường là dấu hiệu chọn shape sai.

Không projection sang DTO quá sớm nếu bước sau thật sự cần behavior/invariant của domain object.

Không dùng LINQ flatten để thay relational design sai như CSV ids trong một column.

## 8. Production notes & scale check

Với EF Core, projection là một trong những tối ưu quan trọng nhất: chỉ lấy column cần cho response.

Ở hệ thống nhỏ, một DTO projection thẳng từ query thường đủ; không cần thêm mapper/repository layer nếu không có driver.

Đo generated SQL khi `SelectMany` qua navigation phức tạp; đừng đoán nó sẽ thành join nào.

## 9. Bài tập kỹ thuật

1. Lấy SKU của tất cả item trong paid orders.
2. Projection thành `(Sku, Quantity)` tuple.
3. Debug một pipeline flatten cả pending order rồi filter item; chuyển filter về đúng tầng.
4. Tính tổng số output row trước khi chạy nếu có 50 order, mỗi order 4 item.

## 10. Bài tập tích hợp liên module — Judgment

Report cần tổng doanh thu theo SKU trên 20 triệu OrderItems. Bạn sẽ `SelectMany` sau khi load orders hay `GROUP BY` ở SQL/EF query? Bảo vệ lựa chọn theo data movement và index.

## 11. Retrieval practice

1. `Select` có đổi số phần tử không?
2. `SelectMany` làm gì với nested sequence?
3. Projection giúp query database ở điểm nào?
4. Cardinality explosion là gì?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy được sample mà không sửa code.
- [ ] Tôi giải thích được cơ chế thay vì chỉ nhớ syntax.
- [ ] Tôi nêu được ít nhất một trường hợp không nên dùng kỹ thuật trong bài.
- [ ] Tôi bảo vệ được lựa chọn tầng xử lý dữ liệu.

- Bài trước: [LINQ query syntax và method syntax](./01-linq-query-syntax-va-method-syntax.md)
- Bài tiếp theo: [Ordering, partitioning và distinct](./03-ordering-partitioning-va-distinct.md)
