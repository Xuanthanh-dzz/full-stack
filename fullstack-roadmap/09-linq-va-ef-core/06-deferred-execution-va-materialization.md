# Deferred execution và materialization

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14  
> **Review cycle:** 180 days  
> **Re-verify triggers:** .NET LINQ/API change, query-provider behavior change, sample CI failure

## TL;DR

- Nhiều LINQ operator chỉ dựng pipeline; source thực sự được đọc khi bạn enumerate.
- `ToList`, `ToArray`, `First`, `Count`... tạo execution boundary theo semantics của từng operator.
- Deferred execution giúp compose query nhưng cũng gây query chạy lặp, dữ liệu thay đổi giữa hai enumeration hoặc exception xuất hiện muộn.

## 1. Mục tiêu

- chứng minh query chưa chạy trước enumeration;
- phân biệt streaming operator và materialization;
- nhận ra multiple enumeration;
- đặt execution boundary có chủ đích;
- liên hệ deferred LINQ với thời điểm EF Core gửi SQL.

## 2. Bài toán mở đầu

Một developer log 'query đã tạo xong', rồi source thay đổi trước `foreach`. Kết quả khác điều họ nghĩ vì biến LINQ giữ recipe, không phải snapshot.

## 3. Lời giải chạy được

~~~csharp
var numbers = new List<int> { 1, 2, 3, 4 };

var evens = numbers
    .Where(number =>
    {
        Console.WriteLine($"Checking {number}");
        return number % 2 == 0;
    });

Console.WriteLine("Query created");
numbers.Add(6);

Console.WriteLine("First enumeration");
Console.WriteLine(string.Join(",", evens));

var snapshot = evens.ToList();
numbers.Add(8);

Console.WriteLine("Snapshot");
Console.WriteLine(string.Join(",", snapshot));
~~~

## 4. Cơ chế hoạt động

`Where` trả enumerable mới giữ reference/source + predicate. Nó không chạy predicate ngay.

Mỗi lần `foreach`, `ToList`, `Count` hoặc terminal operator cần dữ liệu, pipeline được enumerate theo semantics của operator.

`ToList` materialize thành snapshot tại thời điểm đó. Sau boundary, thay đổi source không tự đi vào list.

## 5. Kiến thức nền và prerequisites

Iterator/yield từ C# nâng cao giúp hiểu deferred execution: enumerator kéo từng phần tử khi consumer yêu cầu.

Với `IQueryable`, deferred execution còn quan trọng hơn: expression tree được build trước, SQL thường chỉ gửi khi terminal async operator như `ToListAsync` chạy.

## 6. Lỗi thường gặp

**Enumerate cùng query nhiều lần mà tưởng cache.** Có thể chạy work/SQL lặp.

**Return deferred sequence từ scope đã dispose resource.** Enumeration sau đó có thể fail.

**Materialize quá sớm.** Mất khả năng compose/filter ở data source.

## 7. Khi nào KHÔNG dùng

Không giữ deferred query nếu caller cần snapshot ổn định tại thời điểm method return.

Không defer khi source/resource lifetime không tồn tại đến lúc enumeration.

Không thêm `ToList()` chỉ để 'chắc chắn' nếu nó khiến dữ liệu lớn rời database sớm.

## 8. Production notes & scale check

Ở request nhỏ, materialize đúng chỗ giúp lifecycle rõ và tránh query bất ngờ.

Với EF Core, một biến `IQueryable` có thể bị enumerate hai lần bởi `CountAsync` rồi `ToListAsync`; đôi khi đúng, đôi khi cần query khác/one roundtrip trade-off.

Logging query nên gắn với execution boundary, không chỉ lúc tạo `IQueryable`.

## 9. Bài tập kỹ thuật

1. Dự đoán output sample trước khi chạy.
2. Viết query được enumerate hai lần và chứng minh predicate chạy hai lần.
3. Refactor method trả `IEnumerable` từ file stream để không dùng resource đã dispose.
4. Debug `ToList()` đặt quá sớm trước `Where`.

## 10. Bài tập tích hợp liên module — Judgment

API cần trả 20 row và tổng count cho pagination. Bạn chấp nhận hai SQL query (`CountAsync` + page) hay materialize toàn bộ một lần? Quyết định theo row count và consistency requirement.

## 11. Retrieval practice

1. Deferred execution là gì?
2. `ToList` tạo boundary gì?
3. Vì sao multiple enumeration nguy hiểm với database?
4. Khi nào snapshot tốt hơn deferred sequence?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy được sample.
- [ ] Tôi giải thích được cardinality/execution của operator chính.
- [ ] Tôi phân biệt được in-memory và provider-backed behavior.
- [ ] Tôi nêu được trường hợp không nên dùng kỹ thuật.

- Bài trước: [Join và GroupJoin](./05-join-va-groupjoin.md)
- Bài tiếp theo: [IEnumerable và IQueryable](./07-ienumerable-va-iqueryable.md)
