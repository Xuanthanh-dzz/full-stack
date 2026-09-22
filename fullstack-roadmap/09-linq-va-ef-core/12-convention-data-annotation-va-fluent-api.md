# Convention, Data Annotation và Fluent API

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/.NET major update, provider breaking change, migration/query behavior change, sample CI failure

## TL;DR

- EF Core build model từ convention, annotation và Fluent API; cấu hình explicit nên dành cho invariant/mapping quan trọng.
- Fluent API giữ persistence concern ra khỏi entity tốt hơn khi domain model cần sạch và hỗ trợ composite/index/relationship phức tạp.
- Đừng cấu hình mọi thứ chỉ vì có thể; convention đúng và rõ thì để convention làm việc.

## 1. Mục tiêu

- map key, length, precision, index, relationship;
- phân biệt convention/annotation/Fluent API;
- chọn mapping location theo architecture;
- đọc Fluent mapping trong CommerceLab sample;
- tránh schema drift do default type/length không chủ đích.

## 2. Bài toán mở đầu

Nếu chỉ để convention, `string` có thể thành column rộng hơn business cần; decimal precision hoặc delete behavior cũng có thể không đúng invariant CommerceLab.

## 3. Lời giải chạy được

~~~csharp
modelBuilder.Entity<Product>(entity =>
{
    entity.ToTable("Products", "catalog");
    entity.HasKey(product => product.ProductId);

    entity.Property(product => product.Sku)
        .HasMaxLength(40)
        .IsUnicode(false);

    entity.Property(product => product.Name)
        .HasMaxLength(160);

    entity.Property(product => product.Price)
        .HasPrecision(19, 4);

    entity.HasIndex(product => product.Sku)
        .IsUnique();
});
~~~

Xem implementation: `samples/module-09/CommerceLab.Data/CommerceDbContext.cs`.

## 4. Cơ chế hoạt động

Convention tạo model mặc định từ CLR shape/naming.

Data Annotation gắn metadata vào class/property; Fluent API cấu hình qua `ModelBuilder`.

Fluent config có thể diễn đạt composite key/index, delete behavior, schema, precision và relationship rõ hơn annotation.

Model cuối được EF dùng cho migration, query translation và materialization.

## 5. Kiến thức nền và prerequisites

Module 08 đã xác định type, constraint, PK/FK, index. Mapping EF phải phản ánh lại các invariant đó — không được để ORM 'đoán' trái schema.

Must know: persistence model có thể khác domain/API DTO.

Should know: tách `IEntityTypeConfiguration<T>` khi `OnModelCreating` quá dài.

## 6. Lỗi thường gặp

**Không set precision cho tiền.** Risk schema/default không đúng mong muốn.

**Cascade delete theo convention mà không review.** Có thể xóa lịch sử order.

**Annotation đầy entity chỉ vì tiện.** Domain layer bị coupling nếu architecture cần reuse độc lập.

## 7. Khi nào KHÔNG dùng

Không chuyển mọi convention thành Fluent line chỉ để tăng verbosity.

Không tạo abstraction mapping generic phức tạp nếu vài entity explicit config dễ đọc hơn.

Không dùng annotation cho mapping provider-specific nếu entity nên provider-agnostic.

## 8. Production notes & scale check

Team nhỏ: một `CommerceDbContext` + vài `IEntityTypeConfiguration<T>` khi model lớn là đủ.

Review migration generated sau mọi mapping change. Mapping compile được chưa chắc migration an toàn.

Schema database là contract dữ liệu lâu dài; API naming preference không nên tùy tiện đổi column/history.

## 9. Bài tập kỹ thuật

1. Cấu hình unique Email max length 320 non-Unicode.
2. Cấu hình Order.TotalAmount `decimal(19,4)`.
3. Tạo composite unique `(OrderId, ProductId)`.
4. Debug cascade delete làm mất child lịch sử.

## 10. Bài tập tích hợp liên module — Judgment

Entity domain cần chạy cả trong service không dùng EF. Bạn sẽ dùng annotation hay Fluent API? Nêu trade-off coupling, discoverability và duplication.

## 11. Retrieval practice

1. Ba nguồn model configuration là gì?
2. Khi nào Fluent API rõ hơn annotation?
3. Vì sao delete behavior phải review?
4. Mapping change phải kiểm tra artifact nào tiếp theo?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy/build được sample liên quan.
- [ ] Tôi giải thích được behavior của EF Core thay vì chỉ nhớ API.
- [ ] Tôi phân biệt demo/local-dev với production.
- [ ] Tôi nêu được khi nào không nên dùng kỹ thuật.

- Bài trước: [EF Core 10: DbContext và entity](./11-ef-core-10-dbcontext-va-entity.md)
- Bài tiếp theo: [Migration, Code First và seeding](./13-migration-code-first-va-seeding.md)
