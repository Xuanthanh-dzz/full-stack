# Quan hệ one-to-one, one-to-many và many-to-many

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/provider major update, loading/concurrency behavior change, sample CI failure

## TL;DR

- EF relationship gồm principal/dependent, foreign key và navigation; cardinality phải phản ánh domain, không chỉ làm navigation 'chạy được'.
- One-to-many là case phổ biến; many-to-many skip navigation tiện khi join table không có behavior riêng.
- Khi join table có payload như Quantity/Role/CreatedAt, hãy model nó thành entity thay vì ẩn sau many-to-many.

## 1. Mục tiêu

- map one-to-one/one-to-many/many-to-many;
- phân biệt principal/dependent;
- cấu hình FK và delete behavior;
- chọn explicit join entity khi có payload;
- đọc relationship trong CommerceLab sample.

## 2. Bài toán mở đầu

Order có Customer, Items, Payments; Product có Stock và nhiều OrderItems. Nếu cardinality hoặc cascade sai, một thao tác delete có thể làm mất lịch sử hoặc schema sinh FK không mong muốn.

## 3. Lời giải chạy được

~~~csharp
modelBuilder.Entity<Order>(entity =>
{
    entity.HasOne(order => order.Customer)
        .WithMany(customer => customer.Orders)
        .HasForeignKey(order => order.CustomerId)
        .OnDelete(DeleteBehavior.Restrict);
});

modelBuilder.Entity<OrderItem>(entity =>
{
    entity.HasOne(item => item.Order)
        .WithMany(order => order.Items)
        .HasForeignKey(item => item.OrderId)
        .OnDelete(DeleteBehavior.Cascade);

    entity.HasOne(item => item.Product)
        .WithMany(product => product.OrderItems)
        .HasForeignKey(item => item.ProductId)
        .OnDelete(DeleteBehavior.Restrict);
});
~~~

## 4. Cơ chế hoạt động

Principal là phía key được tham chiếu; dependent chứa foreign key.

Navigation chỉ là object graph view của relationship; FK mới là dữ liệu quan hệ cốt lõi.

Many-to-many không payload có thể dùng skip navigation để EF quản lý join table. Khi join row có business data, entity explicit làm lifecycle/invariant rõ hơn.

## 5. Kiến thức nền và prerequisites

Module 08 ER modeling/cardinality là prerequisite trực tiếp.

Must know: optionality trong C# nullable/FK phải khớp schema.

Should know: cascade behavior nên được review theo historical retention, không chỉ theo convenience.

## 6. Lỗi thường gặp

**Navigation nullable nhưng FK NOT NULL hoặc ngược lại.** Model semantics lệch.

**Cascade delete Product → OrderItem lịch sử.** Có thể phá audit/order history.

**Ẩn join entity dù join có Quantity/Metadata.** Mất nơi đặt behavior.

## 7. Khi nào KHÔNG dùng

Không tạo navigation cả hai chiều nếu app chỉ cần một chiều và bidirectional graph làm model rối.

Không dùng many-to-many skip navigation nếu join table có identity/lifecycle riêng.

Không cascade delete aggregate lịch sử chỉ để test cleanup dễ hơn.

## 8. Production notes & scale check

Team nhỏ: explicit FK + navigation + Fluent config rõ là đủ, không cần relationship abstraction.

Review database generated FK/index sau migration.

Delete behavior phải gắn retention/compliance requirement.

## 9. Bài tập kỹ thuật

1. Map Customer one-to-many Orders.
2. Map Product one-to-one Stock.
3. Thiết kế ProductCategory có `CreatedAt` thành explicit join entity.
4. Debug cascade chain nguy hiểm.

## 10. Bài tập tích hợp liên module — Judgment

Order-Payment nên one-to-one hay one-to-many nếu provider cho retry/refund? Dùng business workflow để chọn cardinality, không chọn theo UI hiện tại.

## 11. Retrieval practice

1. Dependent thường chứa gì?
2. Khi nào join entity explicit cần thiết?
3. Navigation khác FK ở vai trò nào?
4. Vì sao cascade delete là business decision?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi map/load/update được quan hệ trong sample.
- [ ] Tôi giải thích được số query và số row có thể sinh.
- [ ] Tôi nhận ra concurrency/performance failure mode.
- [ ] Tôi biết khi nào giải pháp đơn giản hơn phù hợp.

- Bài trước: [CRUD, change tracking và Unit of Work](./14-crud-change-tracking-va-unit-of-work.md)
- Bài tiếp theo: [Eager, explicit và lazy loading](./16-eager-explicit-va-lazy-loading.md)
