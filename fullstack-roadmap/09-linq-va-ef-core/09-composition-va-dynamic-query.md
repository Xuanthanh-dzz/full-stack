# Composition và dynamic query

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14  
> **Review cycle:** 180 days  
> **Re-verify triggers:** .NET LINQ/API change, query-provider behavior change, sample CI failure

## TL;DR

- Dynamic query tốt thường là **compose thêm operator có điều kiện** trên một query gốc, không phải nối chuỗi SQL.
- Giữ query ở dạng provider-backed cho tới projection/materialization giúp filter/sort/page chạy gần dữ liệu.
- Dynamic sorting/filtering cần whitelist field và giới hạn complexity để tránh security/performance abuse.

## 1. Mục tiêu

- compose `IQueryable` theo filter optional;
- tách query specification nhỏ dễ test;
- whitelist sort field;
- tránh SQL string concatenation;
- giữ execution boundary ở cuối pipeline.

## 2. Bài toán mở đầu

Endpoint `/orders` có optional status, minTotal, fromDate và sort. Nếu viết mọi combination bằng `if` lồng nhau hoặc raw SQL concat, code nhanh mất kiểm soát.

## 3. Lời giải chạy được

~~~csharp
var source = new[]
{
    new Order(1, "Paid", 500m),
    new Order(2, "Pending", 2_000m),
    new Order(3, "Paid", 3_000m),
}.AsQueryable();

string? status = "Paid";
decimal? minTotal = 1_000m;

IQueryable<Order> query = source;

if (!string.IsNullOrWhiteSpace(status))
{
    query = query.Where(order => order.Status == status);
}

if (minTotal is not null)
{
    query = query.Where(order => order.Total >= minTotal.Value);
}

query = query.OrderByDescending(order => order.Id);

Console.WriteLine(string.Join(",", query.Select(order => order.Id)));

public sealed record Order(int Id, string Status, decimal Total);
~~~

## 4. Cơ chế hoạt động

Mỗi `Where` tạo query expression mới; query object thường immutable về semantics. Reassign biến `query` chỉ cập nhật reference tới pipeline mới.

Optional filter không cần build expression tree thủ công nếu simple composition đủ.

Dynamic sort bằng string reflection/library có thể tiện nhưng cần whitelist để tránh field không mong muốn và query khó index.

## 5. Kiến thức nền và prerequisites

Composition là lợi thế lớn của `IQueryable`: tầng application có thể thêm filter trước khi query thực thi.

Liên hệ security Module 08: parameter value nên đi parameter, không concatenate SQL.

## 6. Lỗi thường gặp

**Nối raw SQL bằng input sort/filter.** Injection và query-plan issue.

**Materialize trước optional filters.** Mất server-side composition.

**Một method 300 dòng với 40 if.** Tách filter nhỏ hoặc request object/specification nhẹ.

## 7. Khi nào KHÔNG dùng

Không xây Specification framework phức tạp cho endpoint có ba filter.

Không cho client gửi expression/query language toàn quyền nếu không có sandbox/limit.

Không dynamic hóa mọi query; query cố định quan trọng thường rõ hơn khi viết explicit.

## 8. Production notes & scale check

Team 2–3 người: request DTO + một query method compose condition là đủ trong đa số CRUD.

Giới hạn page size, sort fields và filter complexity để tránh query abuse.

Test generated SQL/plan cho combination phổ biến và combination xấu nhất, không chỉ happy path.

## 9. Bài tập kỹ thuật

1. Thêm `fromDate` filter.
2. Whitelist sort bằng switch expression.
3. Debug query gọi `ToList()` trước các `if`.
4. Viết test ba combination filter.

## 10. Bài tập tích hợp liên module — Judgment

Endpoint admin cần 25 filter hiếm dùng. Chọn explicit composition, specification objects, query language hay reporting DB? Đưa ra ngưỡng complexity/team ownership.

## 11. Retrieval practice

1. Dynamic query có cần raw SQL không?
2. Vì sao materialization nên ở cuối?
3. Sort field từ client cần guard gì?
4. Khi nào specification framework là overengineering?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy được sample.
- [ ] Tôi giải thích được cardinality/execution của operator chính.
- [ ] Tôi phân biệt được in-memory và provider-backed behavior.
- [ ] Tôi nêu được trường hợp không nên dùng kỹ thuật.

- Bài trước: [Expression tree, query provider và SQL translation](./08-expression-tree-query-provider-va-sql-translation.md)
- Bài tiếp theo: [Lỗi LINQ và tối ưu](./10-loi-linq-va-toi-uu.md)
