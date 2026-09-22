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

### Trực giác 60 giây

Deferred execution nghĩa là: **bạn mới viết công thức, chưa nấu món ăn**.

Ví dụ:

~~~csharp
var evens = numbers.Where(x => x % 2 == 0);
~~~

Dòng này thường chưa duyệt toàn bộ `numbers`. Nó tạo một object biết rằng: “khi ai đó hỏi dữ liệu, hãy lấy source rồi giữ số chẵn”.

Đến khi bạn `foreach`, `ToList()`, `Count()`... thì công thức mới được chạy.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| deferred execution | trì hoãn chạy tới khi cần kết quả |
| enumeration | quá trình lấy lần lượt phần tử |
| terminal operator | operation cần kết quả thật |
| materialization | tạo collection/result cụ thể trong memory |
| snapshot | ảnh chụp dữ liệu tại một thời điểm |
| multiple enumeration | chạy lại cùng sequence nhiều lần |

Đây không chỉ là lý thuyết. Nếu source là database, mỗi terminal operation có thể biến thành một SQL roundtrip riêng.

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

### Walkthrough thời gian

Giả sử:

~~~text
T0: numbers = [1,2,3,4]
T1: var evens = numbers.Where(...)
T2: numbers.Add(6)
T3: foreach(evens)
~~~

Tại `T1`, chưa có snapshot `[2,4]`.

Đến `T3`, sequence đọc source hiện tại:

~~~text
1 → reject
2 → keep
3 → reject
4 → keep
6 → keep
~~~

nên kết quả là `[2,4,6]`.

Nếu ở `T2` bạn đã gọi `var snapshot = evens.ToList()`, list đó sẽ giữ dữ liệu materialize tại thời điểm chạy.

## 4. Cơ chế hoạt động

### Deferred vs materialized

| Thuộc tính | Deferred sequence | Materialized collection |
|---|---|---|
| Chạy ngay | thường không | có |
| Phản ánh source thay đổi sau đó | có thể | không tự động |
| Có thể enumerate lại | có | có, nhưng data đã có sẵn |
| I/O có thể lặp | có | không cho cùng snapshot |
| Memory upfront | thấp hơn | cao hơn |

### Vì sao multiple enumeration nguy hiểm?

Với list nhỏ, hai lần enumerate có thể chỉ là vài microseconds. Với EF:

~~~text
CountAsync()   → SQL query 1
ToListAsync()  → SQL query 2
~~~

Đôi khi hai query là đúng thiết kế. Nhưng bạn phải biết mình đang trả giá hai roundtrip và có thể nhìn thấy dữ liệu ở hai thời điểm khác nhau.

### Misconception check

**Đúng hay sai?** Gán LINQ query vào biến nghĩa là kết quả đã được tính.

**Đáp án:** Sai với nhiều operator deferred.

**Đúng hay sai?** `ToList()` chỉ đổi type trả về.

**Đáp án:** Sai. Nó còn tạo execution/materialization boundary.

### Mini-check

Nếu bạn gọi `Count()` rồi `ToList()` trên một iterator có side effect, side effect có thể chạy mấy lượt?

Đáp án: thường hai lượt.

`Where` trả enumerable mới giữ reference/source + predicate. Nó không chạy predicate ngay.

Mỗi lần `foreach`, `ToList`, `Count` hoặc terminal operator cần dữ liệu, pipeline được enumerate theo semantics của operator.

`ToList` materialize thành snapshot tại thời điểm đó. Sau boundary, thay đổi source không tự đi vào list.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** biết query chưa chắc đã chạy khi được khai báo.

**Working developer:** nhận ra execution boundary và multiple enumeration.

**Deep dive:** iterator state machine, streaming/buffering operator và EF roundtrip consistency.

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
