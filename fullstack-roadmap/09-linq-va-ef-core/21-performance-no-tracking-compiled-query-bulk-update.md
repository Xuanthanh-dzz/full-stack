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

### Trực giác 60 giây

Performance trong EF Core có nhiều tầng. Nếu query chậm, bạn cần biết cost nằm ở đâu:

~~~text
C# query construction
→ EF translation
→ network roundtrip
→ SQL execution
→ rows transferred
→ materialization
→ change tracking
~~~

`AsNoTracking`, compiled query và `ExecuteUpdate` tối ưu **những tầng khác nhau**. Dùng sai tầng thì gần như không giải quyết bottleneck.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| no-tracking | không đưa entity vào change tracker |
| compiled query | precompile query pipeline delegate |
| set-based update | update nhiều row bằng một DB statement |
| materialization cost | cost tạo object từ row |
| query compilation | cost EF xử lý query shape |
| hot path | đoạn chạy rất thường xuyên/quan trọng |

Thứ tự tối ưu tốt thường là: query đúng shape và index trước, micro-optimization framework sau.

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

### Walkthrough: update 2 triệu rows

Cách tracked loop:

~~~text
SELECT 2,000,000 rows
→ materialize 2,000,000 entities
→ track 2,000,000 entries
→ foreach set IsExpired=true
→ generate/execute many updates/batches
~~~

Set-based:

~~~text
UPDATE Orders
SET IsExpired = 1
WHERE ...
~~~

Database xử lý tập rows trực tiếp, không cần materialize từng entity.

Nhưng đổi lại, domain behavior/change tracker/interceptor logic dựa trên entity có thể không chạy như flow tracked.

## 4. Cơ chế hoạt động

### Ba kỹ thuật tối ưu khác nhau

| Kỹ thuật | Tối ưu gì | Không giải quyết gì |
|---|---|---|
| `AsNoTracking` | tracker CPU/memory | SQL scan/index tệ |
| compiled query | query compilation overhead | DB execution chậm |
| `ExecuteUpdate` | row-by-row materialization/update | invariant cần per-entity behavior |

### Thứ tự điều tra thực dụng

~~~text
1. Query trả đúng số row/column chưa?
2. Filter/order có chạy ở DB không?
3. SQL/index/plan có ổn không?
4. Có tracking không cần thiết không?
5. Có row-by-row operation không?
6. Profiler có chỉ query compilation đáng kể không?
~~~

### Misconception check

**Đúng hay sai?** Compiled query giúp mọi query nhanh đáng kể.

**Đáp án:** Sai. Nó chỉ giảm một phần overhead EF và cần đo.

**Đúng hay sai?** `ExecuteUpdate` tương đương load entity rồi save về mặt behavior.

**Đáp án:** Sai. Nó bypass change tracker/entity lifecycle.

### Mini-check

Nếu SQL Server mất 900 ms để scan table, còn EF query compilation mất 0,2 ms, nên tối ưu gì trước?

Đáp án: SQL/index/query shape.

No-tracking bỏ entry khỏi change tracker; `AsNoTrackingWithIdentityResolution` deduplicate entity instance trong result mà không giữ tracking lâu dài.

Compiled query precompile query pipeline delegate cho query shape hot; lợi ích cần benchmark vì EF đã cache normal query compilation.

`ExecuteUpdate/Delete` dịch trực tiếp set-based DML, không load entity và không sync tracked instances đang tồn tại.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** hiểu no-tracking và set-based update.

**Working developer:** đo bottleneck theo tầng, projection/index trước.

**Deep dive:** compiled query benchmark, context pooling, allocation/materialization internals.

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
