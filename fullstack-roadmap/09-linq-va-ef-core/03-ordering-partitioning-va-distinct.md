# Ordering, partitioning và distinct

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14  
> **Review cycle:** 180 days  
> **Re-verify triggers:** .NET/EF Core major update, LINQ behavior/API change, sample CI failure

## TL;DR

- Ordering phải deterministic khi dùng pagination; thêm unique tiebreaker nếu sort key có thể trùng.
- `Skip/Take` phù hợp page-number nhỏ-vừa, nhưng page sâu thường nên cân nhắc keyset/cursor.
- `Distinct`/`DistinctBy` giải quyết duplicate có chủ đích, không nên dùng để che join hoặc model sai.

## 1. Mục tiêu

- sort nhiều key bằng `OrderBy`/`ThenBy`;
- phân trang bằng `Skip`/`Take`;
- dùng `Distinct` và `DistinctBy` đúng semantics;
- thiết kế deterministic ordering;
- liên hệ offset pagination LINQ với Module 08.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Ba nhóm thao tác trong bài giải ba vấn đề độc lập:

- ordering: **thứ tự nào trước?**
- partitioning: **lấy đoạn nào của sequence?**
- distinct: **phần tử nào được coi là trùng?**

Với pagination, thứ tự không chỉ để đẹp. Nó là một phần của correctness. Nếu hai row có cùng `OrderedAt` mà bạn không có tiebreaker, page 1 và page 2 có thể chồng/lọt row.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| primary sort key | khóa sort chính |
| tiebreaker | khóa phụ để phá hòa |
| deterministic order | cùng dữ liệu → thứ tự ổn định |
| offset pagination | bỏ N row rồi lấy M row |
| keyset/cursor pagination | lấy tiếp từ khóa cuối của page trước |
| duplicate | hai phần tử được coi là bằng theo equality/key |

API order list cần sort theo `OrderedAt DESC` và phân trang. Nhiều order có cùng timestamp đến giây, nên chỉ sort theo thời gian chưa đủ ổn định.

## 3. Lời giải chạy được

~~~csharp
var orders = Enumerable.Range(1, 8)
    .Select(id => new Order(
        id,
        id <= 4 ? new DateTime(2026, 9, 22, 10, 0, 0) : new DateTime(2026, 9, 22, 9, 0, 0),
        id % 2 == 0 ? "Paid" : "Pending"))
    .ToList();

var page = orders
    .OrderByDescending(order => order.OrderedAt)
    .ThenByDescending(order => order.Id)
    .Skip(2)
    .Take(3)
    .Select(order => order.Id)
    .ToList();

var statuses = orders
    .Select(order => order.Status)
    .Distinct()
    .OrderBy(status => status)
    .ToList();

Console.WriteLine(string.Join(",", page));
Console.WriteLine(string.Join(",", statuses));

public sealed record Order(int Id, DateTime OrderedAt, string Status);
~~~

Expected:

~~~text
2,1,8
Paid,Pending
~~~

### Walkthrough pagination

Giả sử order theo `(OrderedAt DESC, Id DESC)` là:

~~~text
(10:00, 4)
(10:00, 3)
(10:00, 2)
(10:00, 1)
(09:00, 8)
(09:00, 7)
...
~~~

`Skip(2).Take(3)` nghĩa là:

~~~text
bỏ 4,3
→ lấy 2,1,8
~~~

Nếu chỉ sort theo `OrderedAt`, bốn row 10:00 không có thứ tự đảm bảo. Vì vậy `Id` được dùng làm tiebreaker.

## 4. Cơ chế hoạt động

### Offset và keyset khác nhau thế nào?

| Tiêu chí | Offset (`Skip/Take`) | Keyset/cursor |
|---|---|---|
| API đơn giản | rất dễ | phức tạp hơn |
| Nhảy tới page bất kỳ | tốt | không tự nhiên |
| Page rất sâu | thường đắt hơn | thường ổn định hơn |
| Dữ liệu thay đổi giữa page | dễ trượt/duplicate | thường ổn hơn nếu cursor đúng |
| Index cần | vẫn cần | cực kỳ quan trọng |

### Vì sao `Distinct` không nên là băng dính?

Nếu join condition sai làm mỗi order lặp 5 lần, thêm `Distinct()` có thể làm output “đẹp lại” nhưng root cause vẫn còn. Database vẫn tạo/di chuyển các row dư trước khi distinct.

### Misconception check

**Đúng hay sai?** Có `Take(20)` thì không cần `OrderBy`.

**Đáp án:** Sai nếu bạn cần page có ý nghĩa/ổn định. Không order, “20 row đầu” không có business ordering đáng tin.

**Đúng hay sai?** Hai `OrderBy` liên tiếp tương đương `OrderBy(...).ThenBy(...)`.

**Đáp án:** Sai. `OrderBy` thứ hai bắt đầu ordering mới.

### Mini-check

Nếu sort key chính không unique, bạn cần thêm gì để pagination deterministic?

Đáp án: một tiebreaker ổn định, thường là unique key.

`OrderBy` tạo primary ordering; `ThenBy` nối secondary key. Gọi `OrderBy` lần nữa sẽ bắt đầu ordering mới và bỏ ý nghĩa key trước.

`Skip(n).Take(m)` mô tả offset pagination. Trên `IEnumerable`, nó bỏ qua phần tử khi enumerate. Trên EF `IQueryable`, provider thường dịch sang cơ chế pagination của database.

`Distinct` dùng equality của phần tử; `DistinctBy(keySelector)` dùng key. Trên provider database, support/translation phụ thuộc provider và version.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** `OrderBy/ThenBy`, `Skip/Take`, `Distinct`.

**Working developer:** deterministic pagination, page-size limit, chọn offset vs keyset.

**Deep dive:** execution plan, seek predicate và composite index sẽ quyết định cost thật.

Module 08 đã giới thiệu deterministic order và keyset pagination. Ở đây bạn cần nhận ra LINQ chỉ là expression layer; cost cuối cùng vẫn nằm ở data source.

Must know: pagination không có ordering đáng tin là bug.

Deep dive: comparer tùy biến dùng tốt in-memory nhưng không phải comparer nào cũng dịch sang SQL.

## 6. Lỗi thường gặp

**Dùng `OrderBy` hai lần thay vì `ThenBy`.** Key đầu bị thay thế.

**`Skip/Take` không có unique tiebreaker.** Row có thể trượt giữa page khi sort key tie.

**Thêm `Distinct` để hết duplicate mà không tìm nguồn duplicate.** Có thể che join/cartesian bug.

## 7. Khi nào KHÔNG dùng

Không dùng offset pagination cho infinite scroll/page rất sâu nếu keyset đáp ứng UX.

Không dùng `Distinct` nếu duplicate mang nghĩa nghiệp vụ, ví dụ hai payment retry là hai event riêng.

Không sort in-memory sau khi tải hàng triệu row chỉ vì LINQ code dễ viết.

## 8. Production notes & scale check

Team nhỏ không cần framework pagination riêng: một helper nhận cursor/pageSize + deterministic order thường đủ.

Với EF Core, kiểm tra SQL khi pagination trên query có `Include`, `GroupBy` hoặc complex projection.

Pagination API phải đặt limit tối đa để tránh client yêu cầu page size cực lớn.

## 9. Bài tập kỹ thuật

1. Sort theo Status rồi TotalAmount DESC rồi Id.
2. Viết page 3 size 20 bằng `Skip/Take`.
3. Dùng `DistinctBy` để lấy customer đầu tiên theo Email trong dữ liệu in-memory.
4. Debug code gọi hai `OrderBy` liên tiếp.

## 10. Bài tập tích hợp liên module — Judgment

Feed order có 50 triệu row và user chỉ bấm 'Load more'. Chọn offset hay keyset? Nêu index tương ứng ở SQL Server và LINQ predicate/order cần viết.

## 11. Retrieval practice

1. Vì sao pagination cần tiebreaker unique?
2. `OrderBy` thứ hai khác `ThenBy` thế nào?
3. Khi nào `Distinct` là code smell?
4. Offset và keyset khác nhau ở cost nào?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy được sample mà không sửa code.
- [ ] Tôi giải thích được cơ chế thay vì chỉ nhớ syntax.
- [ ] Tôi nêu được ít nhất một trường hợp không nên dùng kỹ thuật trong bài.
- [ ] Tôi bảo vệ được lựa chọn tầng xử lý dữ liệu.

- Bài trước: [Where, Select và SelectMany](./02-where-select-va-selectmany.md)
- Bài tiếp theo: [Aggregate, GroupBy và ToLookup](./04-aggregate-groupby-va-tolookup.md)
