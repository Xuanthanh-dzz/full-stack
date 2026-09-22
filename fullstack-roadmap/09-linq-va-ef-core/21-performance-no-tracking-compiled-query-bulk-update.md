# Performance: no-tracking, compiled query và bulk update

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/provider major update, API/security/testing behavior change, sample CI failure

## TL;DR

- `AsNoTracking` giảm tracking overhead cho read-only entity query; projection còn có thể giảm cả column/materialization.
- Compiled query chỉ đáng cân nhắc ở hot path đã đo; EF đã cache query compilation theo shape.
- `ExecuteUpdate/Delete` chạy set-based không materialize entity nhưng bypass change tracker và entity lifecycle logic.

## 1. Mục tiêu

- dùng no-tracking đúng chỗ;
- hiểu identity-resolution trade-off;
- tạo compiled query;
- dùng `ExecuteUpdateAsync`/`ExecuteDeleteAsync`;
- đo performance theo query/IO/allocations thay vì API folklore.

## 2. Bài toán mở đầu

Job expiry load 2 triệu rows rồi foreach set flag + SaveChanges. Một endpoint read-only lại track 50.000 entities. Cả hai đúng output nhưng chọn execution model sai.

## 3. Lời giải chạy được

Read projection/no-tracking:

~~~csharp
var rows = await db.Orders
    .AsNoTracking()
    .Where(order => order.Status == "Paid")
    .Select(order => new { order.OrderId, order.TotalAmount })
    .Take(100)
    .ToListAsync(cancellationToken);
~~~

Set-based update:

~~~csharp
var affected = await db.Orders
    .Where(order => order.Status == "Pending" && order.OrderedAt < cutoff)
    .ExecuteUpdateAsync(
        setters => setters.SetProperty(order => order.Status, "Expired"),
        cancellationToken);
~~~

## 4. Cơ chế hoạt động

No-tracking bỏ entry khỏi change tracker; `AsNoTrackingWithIdentityResolution` deduplicate entity instance trong result mà không giữ tracking lâu dài.

Compiled query precompile query pipeline delegate cho query shape hot; lợi ích cần benchmark vì EF đã cache normal query compilation.

`ExecuteUpdate/Delete` dịch trực tiếp set-based DML, không load entity và không sync tracked instances đang tồn tại.

## 5. Kiến thức nền và prerequisites

Module 08 set-based SQL vs row-by-row và SARGability áp dụng nguyên vẹn.

Must know: query performance chủ yếu từ SQL shape/index/data volume, không phải chỉ EF flag.

## 6. Lỗi thường gặp

**AsNoTracking rồi sửa entity và mong SaveChanges persist.** Không tracking state.

**Compiled query mọi nơi.** Complexity tăng mà lợi ích nhỏ.

**ExecuteUpdate khi context đang track cùng rows.** Tracked state có thể stale.

## 7. Khi nào KHÔNG dùng

Không compiled query nếu profiler không cho thấy compilation overhead đáng kể.

Không ExecuteUpdate nếu update cần domain invariant/event per entity không thể bỏ qua.

Không no-tracking khi command flow cần modify entity ngay sau query.

## 8. Production notes & scale check

Ưu tiên theo thứ tự: query đúng shape → projection → index/plan → no-tracking → đo → mới cân nhắc compiled query.

Team nhỏ không cần performance abstraction; vài helper rõ và benchmark hot path là đủ.

Bulk DML cần transaction/concurrency/audit policy riêng.

## 9. Bài tập kỹ thuật

1. So tracker entry count có/không AsNoTracking.
2. Rewrite loop bulk update thành ExecuteUpdate.
3. Benchmark compiled vs normal query 10.000 lần trên dataset nhỏ.
4. Debug stale tracked entity sau ExecuteUpdate.

## 10. Bài tập tích hợp liên module — Judgment

Hot endpoint 2ms DB query nhưng 0.1ms query compilation. Có đáng compiled query không? So engineering cost với end-to-end latency.

## 11. Retrieval practice

1. No-tracking giảm cost nào?
2. Compiled query tối ưu layer nào?
3. ExecuteUpdate bypass gì?
4. Thứ tự tối ưu query thực dụng là gì?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy/build được sample liên quan.
- [ ] Tôi biết query/side effect thực sự chạy ở đâu.
- [ ] Tôi phân biệt convenience với abstraction có driver.
- [ ] Tôi nêu được lựa chọn đơn giản hơn cho team nhỏ.

- Bài trước: [Raw SQL và stored procedure](./20-raw-sql-va-stored-procedure.md)
- Bài tiếp theo: [Testing EF Core với SQLite và Testcontainers](./22-testing-ef-core-voi-sqlite-va-testcontainers.md)
