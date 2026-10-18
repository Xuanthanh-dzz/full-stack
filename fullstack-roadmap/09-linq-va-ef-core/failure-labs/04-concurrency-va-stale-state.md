# Failure Lab 04 — Concurrency conflict và stale tracked state

## Bối cảnh

Admin A và B cùng sửa một Order. Một background operation còn dùng `ExecuteUpdate` trên cùng row trong khi context web đang track entity cũ.

## Code lỗi

~~~csharp
var order = await db.Orders.SingleAsync(x => x.OrderId == orderId);

await db.Orders
    .Where(x => x.OrderId == orderId)
    .ExecuteUpdateAsync(setters => setters
        .SetProperty(x => x.Status, "Expired"));

order.Status = "Paid";
await db.SaveChangesAsync();
~~~

## Triệu chứng

- tracked `order.Status` không tự đổi sau `ExecuteUpdate`;
- `SaveChanges` có thể ghi state dựa trên dữ liệu cũ;
- nếu concurrency token không được xử lý đúng, lost update/conflict behavior khó đoán.

## Cách tái hiện

1. Tạo Order có concurrency token.
2. Load bằng context A.
3. Update cùng row bằng context B hoặc `ExecuteUpdate`.
4. Save context A.
5. Quan sát exception/state/database.

## Acceptance criteria

- giải thích change tracker biết và không biết điều gì;
- tạo test hai context;
- chọn conflict policy: reject/reload/merge/retry có điều kiện;
- giải thích khi nào set-based update không phù hợp;
- không dùng retry vô hạn.

## Hints

1. `ExecuteUpdate` có sync tracked entities không?
2. Original concurrency token nằm ở đâu?
3. Business có cho phép `Paid` ghi đè `Expired` không?

## Checklist điều tra

- [ ] tracked entries;
- [ ] original/current token;
- [ ] affected row count;
- [ ] transaction boundary;
- [ ] conflict frequency;
- [ ] retry idempotency.

## Liên module

- Module 08: ACID/isolation/deadlock.
- Module 09: change tracking, optimistic concurrency, bulk update.

Không có full solution trong trang này.
