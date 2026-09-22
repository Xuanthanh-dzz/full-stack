# Aggregate, GroupBy và ToLookup

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14  
> **Review cycle:** 180 days  
> **Re-verify triggers:** .NET/EF Core major update, LINQ behavior/API change, sample CI failure

## TL;DR

- Aggregate operator biến nhiều phần tử thành metric; `GroupBy` tạo các group có key, còn `ToLookup` materialize một multi-value index in-memory.
- `GroupBy` trên LINQ to Objects và `GROUP BY` database không nên bị coi là cùng cơ chế thực thi.
- `ToLookup` hữu ích khi cần tra nhiều lần theo key trong memory, nhưng trả giá bằng materialization và memory.

## 1. Mục tiêu

- dùng `Count`, `Sum`, `Average`, `Min`, `Max`;
- group theo key và projection summary;
- phân biệt `GroupBy` với `ToLookup`;
- tránh multiple enumeration khi aggregate lặp;
- chọn database aggregate hay in-memory aggregate theo data volume.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Aggregate trả lời câu hỏi “từ nhiều phần tử, ta muốn **một số đo** gì?”. Ví dụ: count, sum, average.

`GroupBy` thêm một bước: trước tiên chia dữ liệu thành các “rổ” theo key, rồi aggregate từng rổ.

`ToLookup` giống một cuốn danh bạ in-memory: đưa một key vào và nhận **nhiều value** tương ứng.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| aggregate | gộp nhiều giá trị thành summary |
| grouping key | giá trị dùng để chia nhóm |
| `IGrouping<TKey,T>` | một group có `Key` và các phần tử |
| lookup | cấu trúc tra key → nhiều value |
| materialize | thực sự đọc dữ liệu và tạo object/collection |

Điểm quan trọng: `GroupBy` in-memory và `GROUP BY` trong SQL **có cùng ý tưởng nhưng khác engine**. Với database lớn, nơi thực thi quan trọng hơn syntax.

Dashboard cần số order và tổng doanh thu theo status. Một màn hình khác cần tra nhanh danh sách order theo customer nhiều lần trong cùng request.

## 3. Lời giải chạy được

~~~csharp
var orders = new[]
{
    new Order(1, 10, "Paid", 1_000m),
    new Order(2, 10, "Paid", 2_000m),
    new Order(3, 20, "Pending", 500m),
};

var summaries = orders
    .GroupBy(order => order.Status)
    .Select(group => new
    {
        Status = group.Key,
        Count = group.Count(),
        Revenue = group.Sum(order => order.TotalAmount),
    })
    .OrderBy(x => x.Status)
    .ToList();

var byCustomer = orders.ToLookup(order => order.CustomerId);

foreach (var summary in summaries)
{
    Console.WriteLine($"{summary.Status}:{summary.Count}:{summary.Revenue}");
}

Console.WriteLine(byCustomer[10].Count());

public sealed record Order(int Id, int CustomerId, string Status, decimal TotalAmount);
~~~

### Walkthrough bằng tay

Dữ liệu:

~~~text
1  Paid     1000
2  Paid     2000
3  Pending   500
~~~

Sau `GroupBy(Status)`:

~~~text
Paid    → [1000, 2000]
Pending → [500]
~~~

Sau projection aggregate:

~~~text
Paid    Count=2 Revenue=3000
Pending Count=1 Revenue=500
~~~

`ToLookup(CustomerId)` lại tạo mental model khác:

~~~text
10 → [Order1, Order2]
20 → [Order3]
~~~

## 4. Cơ chế hoạt động

### `GroupBy` vs `ToLookup`

| Tiêu chí | `GroupBy` | `ToLookup` |
|---|---|---|
| Deferred | thường có | không, materialize ngay |
| Key có nhiều value | có | có |
| Dùng để tiếp tục query pipeline | tự nhiên | ít hơn |
| Dùng để tra cùng key nhiều lần in-memory | được nhưng không tối ưu intent | phù hợp |

### Multiple enumeration ở aggregate

Nếu source expensive và bạn viết:

~~~csharp
var count = source.Count();
var sum = source.Sum(x => x.Amount);
~~~

thì source có thể bị enumerate hai lần. Với list nhỏ có thể không đáng kể; với stream/database, đó có thể là hai lượt I/O/query.

### Misconception check

**Đúng hay sai?** `GroupBy` luôn chạy ở database nếu source đến từ EF Core.

**Đáp án:** Không nên giả định. Translation phụ thuộc query shape/provider. Hãy inspect SQL.

**Đúng hay sai?** `ToLookup` giống `Dictionary<TKey,TValue>`.

**Đáp án:** Không hoàn toàn. Lookup cho phép một key có nhiều value.

### Mini-check

Nếu report từ 100 triệu rows chỉ trả 12 tháng, nơi nào nên aggregate trước tiên?

Đáp án mong đợi: database/data source, nếu query có thể được translate/tối ưu.

`GroupBy` trên LINQ to Objects trả sequence các `IGrouping<TKey,TElement>`. Group được hình thành khi source được enumerate.

`ToLookup` materialize ngay thành lookup immutable-like cho mục đích tra nhiều value theo key. Nó giống dictionary của sequence hơn là deferred query.

`Aggregate` tổng quát cho phép fold state, nhưng các operator chuyên dụng như `Sum`/`Count` thường dễ đọc và provider dễ dịch hơn.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** Count/Sum/GroupBy và shape của group.

**Working developer:** biết tránh materialize/group in-memory quá sớm.

**Deep dive:** translation của aggregate, plan, partial aggregation và index/statistics.

Liên hệ Module 08: SQL aggregate có optimizer, index/statistics và có thể xử lý dữ liệu ngay gần storage. LINQ in-memory chỉ thấy object đã tải.

Must know: `GroupBy` không tự biến workload lớn thành efficient database query; translation của provider mới quyết định.

Should know: `ToDictionary` yêu cầu key unique; `ToLookup` cho phép nhiều value cùng key.

## 6. Lỗi thường gặp

**Group in-memory sau `ToList` quá sớm.** Có thể kéo hàng triệu row khỏi database.

**Dùng `ToDictionary` cho key trùng.** Sẽ throw thay vì tạo group.

**Gọi nhiều aggregate trên source expensive mà không hiểu enumeration.** Có thể enumerate nhiều lần.

## 7. Khi nào KHÔNG dùng

Không dùng `Aggregate` custom nếu `Sum`, `Count`, `Any` diễn đạt intent rõ hơn.

Không `ToLookup` chỉ để dùng một lần; chi phí materialize/index hóa có thể không đáng.

Không group ở application nếu database có thể trả đúng summary với ít row hơn.

## 8. Production notes & scale check

Ở quy mô nhỏ, query summary trực tiếp từ EF/SQL và projection DTO thường là giải pháp đơn giản nhất.

Nếu cùng một tập dữ liệu nhỏ đã materialize cần lookup hàng chục lần, `ToLookup` có thể giảm repeated scans.

Với monetary aggregate, giữ `decimal` xuyên suốt và xác định semantics của cancelled/refunded rows.

## 9. Bài tập kỹ thuật

1. Group revenue theo CustomerId.
2. Tính average order value cho paid orders.
3. So `ToLookup` và `ToDictionary` với duplicate key.
4. Debug query gọi `ToList()` trước `GroupBy` trên source giả lập 1 triệu row.

## 10. Bài tập tích hợp liên module — Judgment

Bạn cần báo cáo doanh thu theo tháng từ 100 triệu order nhưng chỉ trả 12 row. Chọn EF-translated `GroupBy`, raw SQL hay load rồi `GroupBy` in-memory? Nêu tiêu chí translation, plan và maintainability.

## 11. Retrieval practice

1. `GroupBy` trả shape gì?
2. `ToLookup` khác `GroupBy` ở materialization thế nào?
3. Khi nào aggregate nên chạy ở database?
4. Vì sao `ToDictionary` có thể throw?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy được sample mà không sửa code.
- [ ] Tôi giải thích được cơ chế thay vì chỉ nhớ syntax.
- [ ] Tôi nêu được ít nhất một trường hợp không nên dùng kỹ thuật trong bài.
- [ ] Tôi bảo vệ được lựa chọn tầng xử lý dữ liệu.

- Bài trước: [Ordering, partitioning và distinct](./03-ordering-partitioning-va-distinct.md)
- Bài tiếp theo: [Join và GroupJoin](./05-join-va-groupjoin.md)
