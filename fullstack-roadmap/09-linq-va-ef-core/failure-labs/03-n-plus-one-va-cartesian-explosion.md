# Failure Lab 03 — Từ N+1 sang cartesian explosion

## Bối cảnh

Endpoint list order ban đầu bị N+1. Developer sửa bằng cách `Include` mọi navigation và latency vẫn tệ, thậm chí payload database lớn hơn.

## Code lỗi phiên bản 1

~~~csharp
var orders = await db.Orders.Take(100).ToListAsync();

foreach (var order in orders)
{
    await db.Entry(order).Collection(x => x.Items).LoadAsync();
    await db.Entry(order).Collection(x => x.Payments).LoadAsync();
}
~~~

## Code lỗi phiên bản 2

~~~csharp
var orders = await db.Orders
    .Include(order => order.Items)
    .Include(order => order.Payments)
    .Take(100)
    .ToListAsync();
~~~

## Triệu chứng

- version 1 tạo hàng trăm roundtrip;
- version 2 ít query hơn nhưng số row join tăng mạnh;
- endpoint chỉ cần `ItemCount`, payment status cuối cùng và total.

## Cách tái hiện

1. Seed 100 orders, mỗi order 20 items và 5 payments.
2. Log query count.
3. Tính row multiplication lý thuyết của version 2.
4. So ba hướng: projection, single Include, split query.

## Acceptance criteria

- đo query count và row count/shape;
- không chỉ “fix N+1” bằng cách giảm số query;
- tạo projection đúng response shape;
- giải thích khi nào `AsSplitQuery` là lựa chọn hợp lý;
- ghi metric before/after.

## Hints

1. 20 items × 5 payments tạo bao nhiêu combination cho mỗi order?
2. Endpoint có cần entity graph để update không?
3. `Items.Count` có thể translate thành aggregate không?

## Checklist điều tra

- [ ] query count;
- [ ] rows returned;
- [ ] columns returned;
- [ ] network bytes;
- [ ] parent pagination trước graph load;
- [ ] single vs split consistency requirement.

## Liên module

- Module 08: JOIN cardinality.
- Module 09: eager loading, projection, split query.

Không có full solution trong trang này.
