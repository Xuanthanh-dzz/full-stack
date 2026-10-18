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

### Trực giác 60 giây

Hãy tưởng tượng bạn có một bảng Excel chứa 10.000 order. Bạn muốn làm ba việc:

1. chỉ giữ order đã thanh toán;
2. sắp xếp order đắt nhất lên trước;
3. chỉ lấy `Id` và `TotalAmount` để hiển thị.

Bạn **có thể** viết một vòng lặp, tự tạo list tạm, tự sort rồi tạo object mới. LINQ tồn tại để bạn mô tả chuỗi biến đổi đó trực tiếp bằng C#: **lọc → sắp xếp → đổi shape**.

Điểm quan trọng nhất cho người mới: LINQ không phải “một database”. LINQ là **cách diễn đạt truy vấn**. Dữ liệu có thể là array trong RAM, file, hoặc query EF Core đi xuống SQL Server.

### Từ vựng cần biết trước

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| LINQ | bộ API/cú pháp để truy vấn dữ liệu bằng C# | dùng để lọc, sort, projection |
| operator | một bước trong pipeline | `Where`, `OrderByDescending`, `Select` |
| predicate | hàm trả `true/false` | `order => order.Status == "Paid"` |
| projection | đổi mỗi phần tử sang shape mới | entity → `{ Id, TotalAmount }` |
| pipeline | chuỗi bước xử lý nối nhau | source → Where → OrderBy → Select |
| query syntax | cú pháp giống SQL hơn | `from ... where ... select` |
| method syntax | gọi extension method | `.Where(...).Select(...)` |

### Nếu không có LINQ thì sao?

Bạn vẫn giải được bằng loop. LINQ **không tạo ra khả năng mới**, nó cho ta một cách mô tả intent ngắn và composable hơn. Vì vậy mục tiêu của bài không phải “học cú pháp cho đẹp”, mà là nhìn một pipeline và hiểu dữ liệu thay đổi ra sao sau từng bước.

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

### Walkthrough từng bước

Với dữ liệu ban đầu:

~~~text
Id  Status    Total
1   Paid      1,200,000
2   Pending     500,000
3   Paid      2,500,000
~~~

Pipeline method syntax chạy theo mental model:

~~~text
orders
  ↓ Where(Status == Paid)
[1, 3]
  ↓ OrderByDescending(TotalAmount)
[3, 1]
  ↓ Select(Id, TotalAmount)
[{3, 2500000}, {1, 1200000}]
~~~

Ba điều cần để ý:

1. `Where` **không đổi type của phần tử**; nó chỉ bỏ phần tử.
2. `OrderByDescending` **không tạo dữ liệu mới về mặt nghiệp vụ**; nó đổi thứ tự.
3. `Select` mới là bước **đổi shape** của mỗi phần tử.

Query syntax và method syntax ở ví dụ này mô tả cùng một ý. Compiler hạ query syntax về các method tương ứng, vì vậy đừng nghĩ query syntax là một engine chạy riêng.

## 4. Cơ chế hoạt động

### Mental model: LINQ có hai câu hỏi tách biệt

Khi đọc LINQ, luôn hỏi hai câu:

1. **Query mô tả việc gì?** — filter, sort, projection...
2. **Query chạy ở đâu?** — RAM hay data source bên ngoài?

Ở bài này, `orders` là array nên toàn bộ pipeline chạy trong process .NET. Sang EF Core, source sẽ là `IQueryable<Order>`; lúc đó C# có thể chỉ đang xây “bản kế hoạch truy vấn” để EF dịch sang SQL.

### Query syntax vs method syntax

| Tiêu chí | Query syntax | Method syntax |
|---|---|---|
| Dễ đọc với join/group đơn giản | thường tốt | tốt |
| Operator hỗ trợ trực tiếp | ít hơn | đầy đủ hơn |
| Dynamic composition | kém tự nhiên hơn | tự nhiên hơn |
| Debug pipeline từng bước | được | thường dễ hơn |
| Performance | không tự nhanh hơn | không tự nhanh hơn |

### Misconception check

**Đúng hay sai?** Query syntax nhanh hơn method syntax vì giống SQL hơn.

**Đáp án:** Sai. Với các biểu thức tương đương, compiler thường hạ về cùng nhóm operator. Performance phụ thuộc source, provider, data size và query shape — không phải vẻ ngoài của syntax.

**Đúng hay sai?** Dùng LINQ đồng nghĩa query chạy ở database.

**Đáp án:** Sai. Với array/list, LINQ chạy trong RAM. Chỉ provider-backed query như EF `IQueryable` mới có thể được dịch sang SQL.

### Mini-check

Nếu bạn đổi `orders` từ array thành dữ liệu EF Core, câu hỏi nào quan trọng hơn: “query syntax hay method syntax?” hay “operator nào được dịch xuống SQL?”.

Đáp án mong đợi: câu thứ hai.

Query syntax là syntax sugar cho một tập operator LINQ. Ví dụ `where` trở thành `Where`, `orderby ... descending` trở thành `OrderByDescending`, còn `select` trở thành `Select`.

Điểm quan trọng: LINQ mô tả **pipeline**. Nguồn `orders` ở đây là array nên operator chạy bằng LINQ to Objects. Khi nguồn là `IQueryable<T>` của EF Core, cùng shape C# có thể được query provider dịch sang SQL. Ta sẽ tách hai cơ chế này ở bài 07–08.

Không phải mọi method đều có query syntax đẹp tương đương. `Take`, `DistinctBy`, `Chunk`, `Any`, `All`... thường khiến method syntax trở thành dạng tự nhiên hơn.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core — bắt buộc:** đọc được `Where → OrderBy → Select` và tính tay intermediate result.

**Working developer:** biết chọn projection và giữ pipeline readable.

**Deep dive:** compiler lowering, overload resolution và sự khác nhau giữa `Enumerable`/`Queryable` sẽ học kỹ ở bài 07–08.

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
