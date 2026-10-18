# CRUD, change tracking và Unit of Work

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/.NET major update, provider breaking change, migration/query behavior change, sample CI failure

## TL;DR

- Tracking query đưa entity vào change tracker; `SaveChanges` phát DML cho state Added/Modified/Deleted.
- `DbContext` đã cung cấp identity map + Unit of Work behavior, nên thêm custom UnitOfWork wrapper thường không có giá trị nếu chỉ forward method.
- Command flow cần context ngắn hạn; read flow thường dùng projection/`AsNoTracking`.

## 1. Mục tiêu

- thêm/sửa/xóa entity và save async;
- inspect `EntityState`;
- giải thích identity resolution;
- phân biệt tracked command và no-tracking read;
- đánh giá custom Unit of Work có cần hay không.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Khi EF load một entity ở chế độ tracking, nó không chỉ trả object. Nó còn giữ một **entry** mô tả: entity nào, key gì, state hiện tại, và giá trị gốc cần để biết có gì thay đổi.

Bạn sửa property trên object. Đến `SaveChanges`, EF so/đọc state rồi quyết định cần `INSERT`, `UPDATE` hay `DELETE` gì.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| change tracker | bộ nhớ theo dõi entity state |
| entity state | Added / Unchanged / Modified / Deleted / Detached |
| original value | giá trị lúc EF bắt đầu track |
| current value | giá trị object hiện tại |
| identity map | cùng key trong context thường dùng cùng tracked instance |
| Unit of Work | gom một nhóm thay đổi thành commit boundary |

Điểm chính: `DbContext` đã có nhiều behavior của Unit of Work. Thêm wrapper chỉ để gọi `SaveChangesAsync()` thường không tạo giá trị mới.

Một request load Order, đổi Status, rồi save. EF cần biết entity nào thay đổi và statement nào phải gửi. Đồng thời developer định thêm `IUnitOfWork.SaveAsync()` chỉ gọi `DbContext.SaveChangesAsync()`.

## 3. Lời giải chạy được

~~~csharp
await using var db = new CommerceDbContext(options);

var order = await db.Orders.SingleAsync(x => x.OrderId == orderId);
Console.WriteLine(db.Entry(order).State); // Unchanged

order.Status = "Paid";
order.ConcurrencyToken = Guid.NewGuid();

Console.WriteLine(db.Entry(order).State); // Modified after DetectChanges
await db.SaveChangesAsync(cancellationToken);
~~~

Insert:

~~~csharp
db.Products.Add(product);
await db.SaveChangesAsync(cancellationToken);
~~~

### Walkthrough một update

~~~text
1. SELECT Order 42
2. EF materialize Order object
3. ChangeTracker entry:
   Key=42
   State=Unchanged
   Original Status=Pending

4. code:
   order.Status = Paid

5. DetectChanges / state evaluation
   State=Modified

6. SaveChanges
   → generate UPDATE
   → execute
   → affected rows checked

7. sau save
   State trở lại Unchanged
   current values trở thành baseline mới
~~~

Với `AsNoTracking`, bước giữ entry không xảy ra, nên sửa object rồi `SaveChanges` không tự biết phải persist.

## 4. Cơ chế hoạt động

### Tracked vs no-tracking

| | Tracking | No-tracking |
|---|---|---|
| Change tracker entry | có | không |
| Sửa entity rồi save | tự nhiên | không tự nhiên |
| Memory/CPU | cao hơn | thấp hơn |
| Read-only projection/list | thường thừa | phù hợp |
| Command load-then-update | phù hợp | không phải default |

### `DbContext` và Unit of Work

Unit of Work về ý tưởng:

~~~text
load/change nhiều entity
→ giữ pending changes
→ commit một boundary
~~~

`DbContext` đã làm việc này qua tracker + `SaveChanges` + transaction behavior. Custom `IUnitOfWork` chỉ đáng có nếu nó thêm policy/cross-resource abstraction thật.

### Misconception check

**Đúng hay sai?** Tracking làm object “live sync” với database.

**Đáp án:** Sai. Entity có thể stale nếu DB thay đổi bên ngoài context.

**Đúng hay sai?** `context.Update(entity)` luôn an toàn cho detached DTO.

**Đáp án:** Sai. Nó có thể mark nhiều property modified và gây over-posting/stale overwrite.

### Mini-check

Nếu endpoint chỉ đọc 10.000 rows để export và không sửa gì, tracking giúp gì?

Đáp án: thường rất ít; projection/no-tracking phù hợp hơn.

Change tracker giữ entry theo key/entity instance và original/current values cần thiết.

`SaveChanges` gọi DetectChanges theo config, tạo modification commands, transaction theo behavior cần thiết, execute rồi accept state.

Identity map giúp cùng key trong một context thường resolve về một tracked instance, tránh hai object cạnh tranh state.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** entity state và `SaveChanges` pipeline.

**Working developer:** tracked command vs no-tracking read, detached update risk.

**Deep dive:** DetectChanges, identity resolution, graph attach/update semantics.

Unit of Work pattern gom nhiều thay đổi thành commit boundary. `DbContext` đã làm phần lớn behavior này.

Repository Pattern sẽ được đánh giá riêng ở bài 23; không mặc định tạo wrapper cho mọi `DbSet`.

## 6. Lỗi thường gặp

**Attach detached graph rồi mark toàn bộ Modified.** Có thể update column không mong muốn.

**Context sống quá lâu.** Tracker tích lũy entity/stale values.

**Read-only query vẫn tracking hàng nghìn entity.** Tốn memory/CPU không cần.

## 7. Khi nào KHÔNG dùng

Không dùng tracking cho projection read-only.

Không tạo `IUnitOfWork` chỉ có `SaveChangesAsync` nếu nó không thêm transaction policy/cross-context abstraction thật.

Không thao tác disconnected entity bằng blind update khi security/concurrency cần kiểm soát field.

## 8. Production notes & scale check

Command handler/service ngắn hạn + tracked aggregate cần sửa là pattern đơn giản, dễ hiểu.

API update nên map field allowed vào entity được load hoặc dùng explicit update strategy; tránh over-posting.

Bulk update không cần materialize entity có thể dùng `ExecuteUpdate` — bài 21.

## 9. Bài tập kỹ thuật

1. Inspect states Added/Modified/Deleted.
2. Dùng `ChangeTracker.Clear()` rồi quan sát identity behavior.
3. Debug code update DTO bằng `context.Update(dtoMappedEntity)` làm overwrite field.
4. Viết command update Status với allowed transition check.

## 10. Bài tập tích hợp liên module — Judgment

Bạn cần update 2 triệu rows `IsExpired=true`. Chọn tracked loop hay set-based `ExecuteUpdate`/SQL? Nêu transaction/log/roundtrip cost.

## 11. Retrieval practice

1. Change tracker giữ thông tin gì?
2. `DbContext` liên quan Unit of Work thế nào?
3. Khi nào `AsNoTracking` hợp lý?
4. Vì sao blind detached update nguy hiểm?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi chạy/build được sample liên quan.
- [ ] Tôi giải thích được behavior của EF Core thay vì chỉ nhớ API.
- [ ] Tôi phân biệt demo/local-dev với production.
- [ ] Tôi nêu được khi nào không nên dùng kỹ thuật.

- Bài trước: [Migration, Code First và seeding](./13-migration-code-first-va-seeding.md)
- Bài tiếp theo: [Quan hệ one-to-one, one-to-many và many-to-many](./15-quan-he-one-to-one-one-to-many-many-to-many.md)
