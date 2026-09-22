# Eager, explicit và lazy loading

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/provider major update, loading/concurrency behavior change, sample CI failure

## TL;DR

- Eager loading lấy related data cùng query plan/query batch chủ động; explicit loading tải sau theo lệnh; lazy loading tải khi navigation được truy cập.
- Lazy loading tiện nhưng che I/O và là nguồn N+1 phổ biến, nên không bật mặc định chỉ vì ít code.
- Read API thường tốt nhất với projection đúng shape; `Include` dành cho trường hợp thật sự cần entity graph.

## 1. Mục tiêu

- dùng `Include`/`ThenInclude`;
- dùng explicit loading qua `Entry(...).Collection/Reference.LoadAsync`;
- hiểu lazy-loading proxy yêu cầu gì;
- đếm số query theo strategy;
- chọn projection thay entity graph khi phù hợp.

## 2. Bài toán mở đầu

Endpoint cần Order + customer + items. Developer có ba cách load. Nếu chọn lazy loading, `foreach` item/customer có thể âm thầm gửi hàng trăm query.

## 3. Lời giải chạy được

Eager loading:

~~~csharp
var order = await db.Orders
    .Include(order => order.Customer)
    .Include(order => order.Items)
        .ThenInclude(item => item.Product)
    .SingleAsync(order => order.OrderId == orderId);
~~~

Explicit loading:

~~~csharp
var order = await db.Orders.SingleAsync(x => x.OrderId == orderId);

await db.Entry(order)
    .Collection(x => x.Items)
    .LoadAsync(cancellationToken);
~~~

Trong CommerceLab read API, ưu tiên projection từ `OrderReadService` khi chỉ cần DTO.

## 4. Cơ chế hoạt động

`Include` thêm navigation load vào query shape; provider có thể join hoặc split tùy query/config.

Explicit loading giữ I/O visible tại call site nhưng tạo roundtrip bổ sung.

Lazy-loading proxy override virtual navigation và trigger query khi access navigation chưa load; entity/context phải còn phù hợp.

## 5. Kiến thức nền và prerequisites

Must know: navigation access có thể là memory access hoặc database I/O tùy strategy — đây là semantic difference lớn.

Projection không phải loading strategy của entity graph; nó tạo result shape mới.

## 6. Lỗi thường gặp

**Include mọi navigation 'cho chắc'.** Payload/cartesian explosion.

**Lazy load trong serialization.** Serializer đi navigation và phát query ngoài ý định.

**Explicit load trong loop.** Trở thành N+1.

## 7. Khi nào KHÔNG dùng

Không lazy loading trong API/backend nếu team không kiểm soát rất chặt query count.

Không `Include` khi endpoint chỉ cần 5 scalar fields; projection rõ hơn.

Không load full graph để chạy aggregate database có thể tính.

## 8. Production notes & scale check

Team 2–3 người: default `lazy loading = off`, read projection rõ, `Include` có chủ đích là policy dễ giữ chất lượng.

Log query count trong integration test/hot endpoint nếu N+1 risk cao.

Entity graph lớn cần xem single-vs-split query ở bài 17.

## 9. Bài tập kỹ thuật

1. Load Order + Items bằng Include.
2. Viết explicit load Customer sau khi Order đã load.
3. Tìm N+1 trong loop explicit load.
4. Refactor Include-heavy endpoint sang projection DTO.

## 10. Bài tập tích hợp liên module — Judgment

Trang admin hiển thị 50 orders, mỗi order chỉ cần item count và customer email. Chọn Include hay projection? Dự đoán row/data transfer.

## 11. Retrieval practice

1. Ba loading strategy khác nhau ở thời điểm I/O nào?
2. Vì sao lazy loading che cost?
3. Khi nào Include hợp lý?
4. Projection giải quyết vấn đề gì khác Include?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi map/load/update được quan hệ trong sample.
- [ ] Tôi giải thích được số query và số row có thể sinh.
- [ ] Tôi nhận ra concurrency/performance failure mode.
- [ ] Tôi biết khi nào giải pháp đơn giản hơn phù hợp.

- Bài trước: [Quan hệ one-to-one, one-to-many và many-to-many](./15-quan-he-one-to-one-one-to-many-many-to-many.md)
- Bài tiếp theo: [N+1, projection và split query](./17-n-plus-one-projection-va-split-query.md)
