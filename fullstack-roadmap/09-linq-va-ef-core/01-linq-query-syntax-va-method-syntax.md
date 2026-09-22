# LINQ query syntax và method syntax

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14  
> **Review cycle:** 180 days  
> **Re-verify triggers:** .NET/EF Core major update, LINQ behavior/API change, sample CI failure

## TL;DR

- LINQ là cách biểu diễn pipeline truy vấn dữ liệu bằng C#; query syntax và method syntax phần lớn quy về cùng nhóm operator.
- Method syntax linh hoạt hơn và là dạng bạn cần đọc thành thạo vì nhiều operator không có query-syntax equivalent.
- Đừng chọn syntax theo sở thích thuần túy: ưu tiên dạng làm intent, composition và generated query dễ đọc nhất.

## 1. Mục tiêu

- viết cùng một truy vấn bằng query syntax và method syntax;
- đọc được pipeline `Where → OrderBy → Select`;
- giải thích query syntax được compiler chuyển thành method calls;
- chọn syntax theo readability thay vì tranh luận phong cách;
- phân biệt LINQ API với nơi query thực sự được thực thi.

## 2. Bài toán mở đầu

Một dashboard cần lấy các order đã thanh toán, sắp xếp theo giá trị giảm dần và chỉ trả shape cần hiển thị.

Nếu viết vòng lặp thủ công, code dễ trộn ba concern: filter, sort và projection. LINQ cho phép mô tả pipeline theo intent.

## 3. Lời giải chạy được

~~~csharp
var orders = new[]
{
    new Order(1, "Paid", 1_200_000m),
    new Order(2, "Pending", 500_000m),
    new Order(3, "Paid", 2_500_000m),
};

var querySyntax =
    from order in orders
    where order.Status == "Paid"
    orderby order.TotalAmount descending
    select new { order.Id, order.TotalAmount };

var methodSyntax = orders
    .Where(order => order.Status == "Paid")
    .OrderByDescending(order => order.TotalAmount)
    .Select(order => new { order.Id, order.TotalAmount });

Console.WriteLine(string.Join(", ", querySyntax.Select(x => x.Id)));
Console.WriteLine(string.Join(", ", methodSyntax.Select(x => x.Id)));

public sealed record Order(int Id, string Status, decimal TotalAmount);
~~~

Chạy:

~~~bash
dotnet new console -n Linq01 -f net10.0
# thay Program.cs bằng sample trên
dotnet run --project Linq01
~~~

Expected:

~~~text
3, 1
3, 1
~~~

## 4. Cơ chế hoạt động

Query syntax là syntax sugar cho một tập operator LINQ. Ví dụ `where` trở thành `Where`, `orderby ... descending` trở thành `OrderByDescending`, còn `select` trở thành `Select`.

Điểm quan trọng: LINQ mô tả **pipeline**. Nguồn `orders` ở đây là array nên operator chạy bằng LINQ to Objects. Khi nguồn là `IQueryable<T>` của EF Core, cùng shape C# có thể được query provider dịch sang SQL. Ta sẽ tách hai cơ chế này ở bài 07–08.

Không phải mọi method đều có query syntax đẹp tương đương. `Take`, `DistinctBy`, `Chunk`, `Any`, `All`... thường khiến method syntax trở thành dạng tự nhiên hơn.

## 5. Kiến thức nền và prerequisites

Prerequisite: lambda, generic, extension method và collection từ Module 05.

Must know: LINQ không phải database API riêng; nó là model truy vấn trên nhiều data source.

Should know: query syntax có thể trộn với method syntax, nhưng chỉ nên làm khi readability tăng.

Deep dive: compiler lowering có thể xem bằng decompiler, nhưng không cần để dùng LINQ đúng.

## 6. Lỗi thường gặp

**Dùng query syntax vì nghĩ nó nhanh hơn.** Hai dạng tương đương thường dẫn tới cùng operator pipeline.

**Select toàn entity khi chỉ cần vài field.** Với LINQ to Objects chỉ tốn object access; với EF Core có thể kéo dữ liệu thừa qua network.

**Chain quá dài trên một dòng.** Hãy format mỗi operator một dòng khi pipeline có nhiều bước.

## 7. Khi nào KHÔNG dùng

Không dùng LINQ nếu một vòng lặp imperative ngắn làm state transition rõ hơn, ví dụ parser/state machine có nhiều `break`, `continue` và mutation có chủ đích.

Không ép query syntax vào operator không phù hợp chỉ để code trông giống SQL.

Không coi LINQ là lý do chuyển mọi business rule thành một expression khổng lồ.

## 8. Production notes & scale check

Ở quy mô nhỏ, chọn syntax mà team đọc nhanh nhất; không cần style war.

Với query database, readability phải đi cùng khả năng nhìn ra `WHERE`, ordering và projection tương ứng. Một pipeline đẹp nhưng dịch thành SQL tệ vẫn là query tệ.

Rule thực dụng: query đơn giản có thể dùng query syntax; composition/dynamic query thường dễ quản lý hơn bằng method syntax.

## 9. Bài tập kỹ thuật

1. Viết truy vấn lấy order `Pending`, sort theo `Id` tăng dần bằng hai syntax.
2. Thêm projection chỉ trả `Id` và `Status`.
3. Debug: sửa một query đang `Select` trước `Where` khiến intent khó đọc; giải thích vì sao output có thể vẫn đúng.
4. Tìm ba operator LINQ không có query-syntax keyword trực tiếp.

## 10. Bài tập tích hợp liên module — Judgment

Bạn cần lấy 20 order mới nhất từ SQL Server. Bạn sẽ filter/sort ở SQL hay tải tất cả về rồi LINQ in-memory? Viết câu trả lời dựa trên row count, network cost và index `(CustomerId, OrderedAt)` từ Module 08.

## 11. Retrieval practice

1. Query syntax có phải runtime riêng không?
2. `where` và `select` thường map sang method nào?
3. Khi nào method syntax dễ maintain hơn?
4. Cùng LINQ syntax có đảm bảo cùng nơi thực thi không?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy được sample mà không sửa code.
- [ ] Tôi giải thích được cơ chế thay vì chỉ nhớ syntax.
- [ ] Tôi nêu được ít nhất một trường hợp không nên dùng kỹ thuật trong bài.
- [ ] Tôi bảo vệ được lựa chọn tầng xử lý dữ liệu.

- Bài trước: [Module 09 overview](./index.md)
- Bài tiếp theo: [Where, Select và SelectMany](./02-where-select-va-selectmany.md)
