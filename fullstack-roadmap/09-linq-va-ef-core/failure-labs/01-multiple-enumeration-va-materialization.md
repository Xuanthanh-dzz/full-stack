# Failure Lab 01 — Multiple enumeration và materialization sai chỗ

## Bối cảnh

Một endpoint tính tổng số order rồi trả page đầu tiên. Developer muốn code “dễ đọc” nên gọi `Count()` và `ToList()` trên cùng một query-like source.

## Code lỗi

~~~csharp
var source = GetOrdersFromSlowSource();

var paid = source.Where(order => order.Status == "Paid");

var total = paid.Count();
var page = paid
    .OrderByDescending(order => order.OrderedAt)
    .Take(20)
    .ToList();
~~~

Giả sử `GetOrdersFromSlowSource()` log mỗi lần enumeration và mất khoảng 600 ms.

## Triệu chứng

- request mất hơn 1 giây dù chỉ trả 20 row;
- log cho thấy source bị enumerate nhiều lần;
- khi source thay đổi giữa hai lượt, `total` và `page` có thể không cùng snapshot.

## Cách tái hiện

1. Viết iterator có `Console.WriteLine` + delay nhỏ cho mỗi lần enumeration.
2. Chạy đoạn code trên.
3. Đếm số lần source bắt đầu enumerate.
4. Thêm một phần tử giữa `Count()` và `ToList()` để quan sát consistency.

## Acceptance criteria

- xác định chính xác execution boundary;
- giải thích vì sao code đúng output trong nhiều trường hợp nhưng vẫn là bug thiết kế;
- đưa ra ít nhất **hai** phương án sửa;
- nêu trade-off consistency / memory / roundtrip của từng phương án;
- viết regression test hoặc instrumentation bắt multiple enumeration.

## Hints

1. `Where` có materialize không?
2. `Count()` có cần enumerate source không?
3. Nếu source là EF `IQueryable`, hai terminal operator sẽ thành mấy SQL query?
4. Nếu requirement cần total count + page, có nhất thiết phải một query không?

## Checklist điều tra

- [ ] source là `IEnumerable` hay `IQueryable`?
- [ ] terminal operator nằm ở đâu?
- [ ] mỗi enumeration tốn bao nhiêu?
- [ ] data có thể đổi giữa các lượt không?
- [ ] materialize một lần có làm memory tăng quá mức không?
- [ ] database có thể xử lý count/page hiệu quả hơn không?

## Liên module

- Module 07: complexity và cost lặp.
- Module 08: pagination, transaction/isolation.
- Module 09: deferred execution và materialization.

Không có full solution trong trang này. Sau khi sửa, tự viết ADR ngắn: **vì sao chọn một query, hai query hay snapshot in-memory**.
