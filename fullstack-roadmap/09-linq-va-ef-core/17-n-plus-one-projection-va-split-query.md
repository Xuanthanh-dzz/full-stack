# N+1, projection và split query

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/provider major update, loading/concurrency behavior change, sample CI failure

## TL;DR

- N+1 là một query lấy N parent rồi thêm query cho từng parent/navigation; latency/DB load tăng theo N.
- Projection thường là fix tốt nhất cho read model; `AsSplitQuery` giải quyết cartesian explosion của nhiều collection Include nhưng tăng roundtrip/consistency trade-off.
- Không có rule 'single query luôn tốt' hay 'split query luôn tốt' — đo row multiplication, roundtrip và result size.

## 1. Mục tiêu

- nhận diện N+1 từ code/log;
- fix bằng projection/eager batch;
- giải thích cartesian explosion;
- dùng `AsSplitQuery` có chủ đích;
- so query count và row count.

## 2. Bài toán mở đầu

Endpoint list 100 orders. Lazy/explicit loading Customer và Items trong loop tạo 201 query. Refactor Include hai collection có thể lại tạo row multiplication rất lớn.

## 3. Lời giải chạy được

Projection:

~~~csharp
var result = await db.Orders
    .AsNoTracking()
    .OrderByDescending(order => order.OrderedAt)
    .Select(order => new
    {
        order.OrderId,
        CustomerEmail = order.Customer.Email,
        ItemCount = order.Items.Count,
        order.TotalAmount,
    })
    .Take(100)
    .ToListAsync(cancellationToken);
~~~

Entity graph lớn cần thiết:

~~~csharp
var orders = await db.Orders
    .Include(order => order.Items)
    .Include(order => order.Payments)
    .AsSplitQuery()
    .Take(50)
    .ToListAsync(cancellationToken);
~~~

## 4. Cơ chế hoạt động

N+1 xuất hiện khi access từng navigation kích query riêng hoặc loop explicit query.

Single query nhiều collection JOIN có thể nhân rows: `Order × Items × Payments`. EF fix-up deduplicate entity object nhưng network/DB vẫn xử lý row lớn.

Split query chạy query riêng cho collection include rồi stitch graph; giảm row multiplication nhưng tăng roundtrip và có consistency considerations nếu dữ liệu đổi giữa queries.

## 5. Kiến thức nền và prerequisites

Module 08 join cardinality là nền tảng để dự đoán cartesian explosion.

Must know: query count và row count là hai trục khác nhau.

Should know: projection aggregate như `Items.Count` thường translate thay vì load collection.

## 6. Lỗi thường gặp

**Fix N+1 bằng Include toàn bộ.** Chuyển từ nhiều query nhỏ sang một query khổng lồ.

**AsSplitQuery mọi nơi theo convention.** Roundtrip tăng không cần thiết.

**Không giới hạn parent trước graph load.** Pagination sau materialization quá muộn.

## 7. Khi nào KHÔNG dùng

Không dùng Include/split query nếu projection đáp ứng response.

Không tối ưu N+1 giả định; log/trace query thật.

Không dùng split query để che model/API trả graph quá lớn.

## 8. Production notes & scale check

Ở scale nhỏ, projection cho list endpoint + entity graph cho command/detail là policy đơn giản.

Instrumentation nên capture DB command count/duration cho endpoint quan trọng.

Threshold không cố định: 10 query local có thể nhanh nhưng 10 roundtrip cross-region rất khác.

## 9. Bài tập kỹ thuật

1. Viết code cố ý N+1 rồi đếm query.
2. Refactor thành projection.
3. Tạo Order có 10 Items và 10 Payments, tính row multiplication join lý thuyết.
4. So single/split query bằng log.

## 10. Bài tập tích hợp liên module — Judgment

Detail page có 1 Order, 5 Items, 2 Payments; list page có 100 Orders. Chọn strategy khác nhau cho hai endpoint và giải thích.

## 11. Retrieval practice

1. N+1 là gì?
2. Split query giải quyết cost nào?
3. Split query thêm cost gì?
4. Vì sao projection thường tốt cho list?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi map/load/update được quan hệ trong sample.
- [ ] Tôi giải thích được số query và số row có thể sinh.
- [ ] Tôi nhận ra concurrency/performance failure mode.
- [ ] Tôi biết khi nào giải pháp đơn giản hơn phù hợp.

- Bài trước: [Eager, explicit và lazy loading](./16-eager-explicit-va-lazy-loading.md)
- Bài tiếp theo: [Transaction và concurrency token](./18-transaction-va-concurrency-token.md)
