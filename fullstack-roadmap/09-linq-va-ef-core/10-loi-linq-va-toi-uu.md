# Lỗi LINQ và tối ưu

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14  
> **Review cycle:** 180 days  
> **Re-verify triggers:** .NET LINQ/API change, query-provider behavior change, sample CI failure

## TL;DR

- LINQ performance thường hỏng vì **sai execution location, multiple enumeration, materialization sớm hoặc thuật toán O(n²)** chứ không phải vì syntax LINQ tự thân.
- Đo data size, enumeration count và generated SQL trước khi tối ưu.
- Đôi khi dictionary/hash set hoặc một vòng lặp rõ ràng tốt hơn pipeline LINQ đẹp mắt.

## 1. Mục tiêu

- phát hiện multiple enumeration;
- nhận ra nested LINQ O(n²);
- chọn `HashSet`/dictionary cho lookup;
- tránh materialization dư;
- đo trước/sau thay vì micro-optimize theo cảm giác.

## 2. Bài toán mở đầu

### Trực giác 60 giây

LINQ không tự làm code chậm. Vấn đề thường đến từ **thuật toán phía dưới** hoặc **nơi chạy sai**.

Ví dụ: với mỗi order bạn gọi `allowedSkus.Any(...)` trên một list 20.000 phần tử. Nếu có 100.000 orders, worst-case gần như 2 tỉ phép so sánh. Cú pháp LINQ đẹp không xóa Big-O.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| time complexity | tốc độ tăng của số phép toán theo input |
| lookup | tìm phần tử theo key |
| hash set | cấu trúc tối ưu cho membership lookup |
| multiple enumeration | đọc cùng source nhiều lượt |
| allocation | cấp phát object/memory |
| bottleneck | phần giới hạn hiệu năng tổng thể |

Muốn tối ưu đúng, hỏi: **data ở đâu, bao nhiêu, chạy mấy lần, và operator có complexity gì?**

Code kiểm tra 100.000 order có SKU thuộc 20.000 allowed SKU bằng `allowed.Any(...)` trong mỗi order. Output đúng nhưng complexity gần O(n×m).

## 3. Lời giải chạy được

~~~csharp
var allowed = Enumerable.Range(1, 20_000)
    .Select(id => $"SKU-{id}")
    .ToHashSet(StringComparer.Ordinal);

var orders = Enumerable.Range(1, 100_000)
    .Select(id => $"SKU-{id % 30_000}");

var matched = orders.Count(sku => allowed.Contains(sku));

Console.WriteLine(matched);
~~~

Lookup hash trung bình phù hợp hơn scan danh sách allowed cho từng order.

### Walkthrough complexity

Cách chậm:

~~~text
100,000 orders
× scan up to 20,000 allowed SKUs
≈ 2,000,000,000 comparisons worst-case
~~~

Cách dùng `HashSet`:

~~~text
build set: O(m)
100,000 lookups: ~O(n)
total gần O(n + m) average
~~~

Ta trả thêm memory để đổi lấy lookup nhanh hơn.

Đây là trade-off cấu trúc dữ liệu từ Module 07, không phải “mẹo LINQ”.

## 4. Cơ chế hoạt động

### Checklist điều tra performance

~~~text
1. Dữ liệu nằm ở DB hay RAM?
2. Bao nhiêu row/item?
3. Pipeline enumerate mấy lần?
4. Có nested scan không?
5. Có materialize sớm không?
6. Có projection dư không?
7. Nếu DB: SQL/index/plan ra sao?
8. Đo trước và sau fix.
~~~

### `List.Contains` vs `HashSet.Contains`

| Thuộc tính | List | HashSet |
|---|---|---|
| Lookup membership | O(n) | trung bình O(1) |
| Giữ thứ tự | có | không phải mục tiêu chính |
| Memory overhead | thấp hơn | cao hơn |
| Build cost | nhỏ | cần hash/index |

### Misconception check

**Đúng hay sai?** Thay mọi list bằng HashSet sẽ làm app nhanh hơn.

**Đáp án:** Sai. Nếu ít lookup hoặc cần ordering/index, HashSet có thể chỉ thêm cost.

**Đúng hay sai?** `Any()` luôn nhanh hơn `Count() > 0`.

**Đáp án:** Với iterator không có cheap count thường có lợi vì stop sớm; nhưng collection có `Count` property thì context khác. Đừng biến guideline thành luật mù.

### Mini-check

Nếu profiler cho thấy database scan chiếm 98% latency, tối ưu một LINQ allocation trong process có đáng ưu tiên không?

Đáp án: thường không.

LINQ là abstraction; complexity của operator vẫn tuân theo cấu trúc dữ liệu phía dưới.

`Any` trên list phải scan cho tới match/end. Đặt nó trong outer loop có thể tạo nested scan. `HashSet.Contains` đổi trade-off: tốn bước build/memory nhưng lookup trung bình nhanh.

Multiple enumeration cũng nhân work: source từ file/network/database có thể đắt hơn collection memory.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** nhìn ra nested scan/multiple enumeration.

**Working developer:** chọn cấu trúc dữ liệu, đo before/after, inspect SQL.

**Deep dive:** allocation profile, iterator fusion, compiled query và provider-specific optimization.

Liên hệ Module 07 Big-O: operator chain không xóa complexity. Liên hệ Module 08 index: HashSet in-memory giống ý tưởng dùng cấu trúc lookup thích hợp, nhưng database index giải quyết ở storage/query engine.

Must know: optimize theo bottleneck đo được, không theo số lượng method calls.

## 6. Lỗi thường gặp

**`Count() > 0` thay `Any()` trên source không có cheap Count.** Có thể enumerate toàn bộ.

**`FirstOrDefault` rồi không phân biệt default value hợp lệ.** Chọn API/nullable phù hợp.

**Nested `Any`/`Contains` trên list lớn.** Xem xét set/dictionary hoặc đưa predicate về database.

## 7. Khi nào KHÔNG dùng

Không đổi mọi list thành HashSet; build cost, memory và ordering semantics khác.

Không thay code LINQ rõ ràng bằng loop tối ưu vi mô nếu profiler không chỉ ra bottleneck.

Không cache materialized result dài hạn nếu dữ liệu cần freshness.

## 8. Production notes & scale check

Checklist production: số row? bao nhiêu enumeration? operator chạy ở đâu? có index phù hợp? projection bao nhiêu column? memory peak bao nhiêu?

Team nhỏ không cần benchmark framework cho mọi query; logging + `Stopwatch` lab + DB IO/plan khi query quan trọng là đủ.

Performance fix phải có before/after metric.

## 9. Bài tập kỹ thuật

1. Tìm ba multiple-enumeration pattern.
2. Refactor nested list lookup sang dictionary/hash set.
3. Benchmark `Any` vs `Count` trên iterator custom.
4. Debug query `ToList().Where(...)` trên giả lập database source.

## 10. Bài tập tích hợp liên module — Judgment

Bài toán deduplicate 5 triệu email: chọn HashSet C#, unique index SQL hay batch ETL? Bảo vệ theo nơi dữ liệu đang sống, memory và invariant cần lâu dài.

## 11. Retrieval practice

1. LINQ có làm Big-O biến mất không?
2. Khi nào HashSet đáng build?
3. Multiple enumeration gây loại cost nào?
4. Vì sao phải đo trước/sau?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy được sample.
- [ ] Tôi giải thích được cardinality/execution của operator chính.
- [ ] Tôi phân biệt được in-memory và provider-backed behavior.
- [ ] Tôi nêu được trường hợp không nên dùng kỹ thuật.

- Bài trước: [Composition và dynamic query](./09-composition-va-dynamic-query.md)
- Bài tiếp theo: [EF Core 10: DbContext và entity](./11-ef-core-10-dbcontext-va-entity.md)
- Spaced review: [Review 02 — Execution boundaries](./reviews/review-02-execution-boundaries.md)
- Failure Labs: [Lab 01](./failure-labs/01-multiple-enumeration-va-materialization.md) · [Lab 02](./failure-labs/02-iqueryable-client-side-filter.md)
