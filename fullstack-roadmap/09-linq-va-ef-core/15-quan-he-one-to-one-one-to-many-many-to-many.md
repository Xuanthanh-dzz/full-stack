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

### Trực giác 60 giây

Relationship trong EF có hai lớp:

1. **relational layer:** foreign key trong database;
2. **object layer:** navigation property giúp code đi từ object này sang object liên quan.

Foreign key là sự thật lưu trong database. Navigation là cách EF/C# biểu diễn mối quan hệ đó thành object graph.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| principal | entity có key được tham chiếu |
| dependent | entity chứa FK trỏ sang principal |
| foreign key | column/key biểu diễn quan hệ |
| reference navigation | navigation tới một object |
| collection navigation | navigation tới nhiều object |
| cascade delete | xóa principal kéo theo dependent |
| join entity | entity biểu diễn row trong bảng nối |

Cardinality phải đến từ nghiệp vụ, không phải từ API EF nào viết ngắn hơn.

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

### Walkthrough `Customer 1 → many Orders`

Database:

~~~text
sales.Customers
CustomerId=10

sales.Orders
OrderId=1001 CustomerId=10
OrderId=1002 CustomerId=10
~~~

C# object model:

~~~text
Customer
  CustomerId = 10
  Orders = [Order1001, Order1002]

Order1001
  CustomerId = 10   ← FK value
  Customer = Customer10  ← navigation
~~~

`CustomerId` và `Customer` liên quan nhưng không phải cùng thứ: một cái là key state, một cái là object reference/navigation.

## 4. Cơ chế hoạt động

### Ba cardinality chính

| Quan hệ | Ví dụ | FK thường nằm ở |
|---|---|---|
| one-to-one | Product ↔ Stock | dependent |
| one-to-many | Customer → Orders | many/dependent side |
| many-to-many | Products ↔ Categories | join table/entity |

### Khi nào many-to-many cần join entity?

Nếu row nối chỉ có hai FK, skip navigation có thể đủ.

Nếu row có:

~~~text
ProductId
CategoryId
CreatedAt
SortOrder
AssignedBy
~~~

thì row này có state/lifecycle riêng → explicit join entity thường rõ hơn.

### Misconception check

**Đúng hay sai?** Có navigation property nghĩa là database không cần FK.

**Đáp án:** Sai. Relational relation vẫn dựa trên key/constraint.

**Đúng hay sai?** Cascade delete luôn tiện nên nên bật rộng.

**Đáp án:** Sai. Với order/history, nó có thể xóa dữ liệu cần giữ.

### Mini-check

Nếu OrderItem cần lưu `Quantity` và `UnitPriceSnapshot`, nó có nên chỉ là hidden many-to-many join không?

Đáp án: không; nó rõ ràng là entity có payload.

Principal là phía key được tham chiếu; dependent chứa foreign key.

Navigation chỉ là object graph view của relationship; FK mới là dữ liệu quan hệ cốt lõi.

Many-to-many không payload có thể dùng skip navigation để EF quản lý join table. Khi join row có business data, entity explicit làm lifecycle/invariant rõ hơn.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** FK, navigation, cardinality.

**Working developer:** delete behavior, optionality, explicit join entity.

**Deep dive:** relationship fix-up, shadow FK, alternate key và ownership patterns.

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
- Spaced review: [Review 03 — EF modeling & tracking](./reviews/review-03-ef-modeling-and-tracking.md)
