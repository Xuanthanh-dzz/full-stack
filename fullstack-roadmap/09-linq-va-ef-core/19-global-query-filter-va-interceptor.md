# Global query filter và interceptor

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/provider major update, API/security/testing behavior change, sample CI failure

## TL;DR

- Global query filter tự gắn predicate vào query entity; EF Core 10 hỗ trợ **named filters** và disable chọn lọc.
- Interceptor phù hợp cross-cutting concern ở pipeline EF như auditing/command observation, không phải nơi giấu business workflow.
- Filter không phải authorization boundary: query bị filter không đồng nghĩa user được phép truy cập tài nguyên.

## 1. Mục tiêu

- cấu hình global query filter;
- dùng named filter của EF Core 10;
- disable filter có chủ đích;
- hiểu interceptor hook ở SaveChanges/command;
- phân biệt cross-cutting concern với business logic.

## 2. Bài toán mở đầu

Product inactive không nên xuất hiện ở hầu hết query. Multi-tenant app còn cần TenantId filter. Nếu copy `Where` ở mọi query, một chỗ quên filter có thể gây bug/rò dữ liệu.

## 3. Lời giải chạy được

EF Core 10 named filters:

~~~csharp
modelBuilder.Entity<Product>()
    .HasQueryFilter("ActiveProductFilter", product => product.IsActive);

var normal = await db.Products.ToListAsync(cancellationToken);

var includingInactive = await db.Products
    .IgnoreQueryFilters(["ActiveProductFilter"])
    .ToListAsync(cancellationToken);
~~~

Sample CommerceLab dùng active-product filter trong `CommerceDbContext`.

## 4. Cơ chế hoạt động

Query filter trở thành một phần model metadata và provider inject predicate khi entity được query.

EF Core 10 cho nhiều named filter và disable theo tên thay vì buộc tắt tất cả.

Interceptor nhận callback tại các điểm pipeline. Ví dụ `SaveChangesInterceptor` có thể ghi audit metadata; command interceptor có thể observe/modify command nhưng cần cực thận trọng.

## 5. Kiến thức nền và prerequisites

Soft delete/multitenancy là use case phổ biến nhưng có semantics khác nhau.

Required navigation + global filter có thể làm parent rows biến mất vì generated inner join; cần integration test.

Authorization vẫn thuộc security layer/use-case, không giao hoàn toàn cho filter.

## 6. Lỗi thường gặp

**Dùng filter tenant nhưng có query `IgnoreQueryFilters()` không review.** Có thể cross-tenant leak.

**Interceptor gửi HTTP/email trong SaveChanges.** Side effect khó retry/transactional consistency.

**Soft delete nhưng unique constraint không được thiết kế lại.** Filter không thay database invariant.

## 7. Khi nào KHÔNG dùng

Không global-filter mọi predicate dùng một lần; local `Where` rõ hơn.

Không dùng interceptor để che business state transition.

Không coi query filter là lớp authorization duy nhất.

## 8. Production notes & scale check

Team nhỏ: một active/tenant filter rõ ràng có thể giảm bug; đừng dựng interceptor framework nếu chỉ cần set `UpdatedAt` ở một service.

Audit quan trọng cần nghĩ outbox/audit table/actor identity, không chỉ log interceptor.

Test cả query bình thường và path disable filter.

## 9. Bài tập kỹ thuật

1. Đổi sample sang named `ActiveProductFilter`.
2. Thêm soft-delete filter giả lập.
3. Viết test `IgnoreQueryFilters` chỉ disable một filter.
4. Review interceptor ghi audit và chỉ ra side effect không nên đặt ở đó.

## 10. Bài tập tích hợp liên module — Judgment

Multi-tenant SaaS nhỏ: chọn global tenant filter, database row-level security hay database-per-tenant? Nêu threat model, ops cost và blast radius.

## 11. Retrieval practice

1. Named filter mới trong EF Core 10 giúp gì?
2. Query filter có phải authorization không?
3. Interceptor phù hợp concern loại nào?
4. Required navigation có thể tương tác filter ra sao?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy/build được sample liên quan.
- [ ] Tôi biết query/side effect thực sự chạy ở đâu.
- [ ] Tôi phân biệt convenience với abstraction có driver.
- [ ] Tôi nêu được lựa chọn đơn giản hơn cho team nhỏ.

- Bài trước: [Transaction và concurrency token](./18-transaction-va-concurrency-token.md)
- Bài tiếp theo: [Raw SQL và stored procedure](./20-raw-sql-va-stored-procedure.md)
