# Transaction và concurrency token

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 10.0.x · C# 14 · EF Core 10.0.12 · SQL Server 2025  
> **Review cycle:** 120 days  
> **Re-verify triggers:** EF Core/provider major update, loading/concurrency behavior change, sample CI failure

## TL;DR

- Một `SaveChanges` relational thường chạy trong transaction; explicit transaction cần khi business operation có nhiều save/query boundary phải atomic.
- Optimistic concurrency dùng token trong `WHERE` update/delete để phát hiện dữ liệu đã đổi kể từ lúc đọc.
- Concurrency conflict không có một cách xử lý chung: retry, client-wins, store-wins hay merge đều là business decision.

## 1. Mục tiêu

- dùng explicit transaction khi cần;
- cấu hình concurrency token;
- bắt `DbUpdateConcurrencyException`;
- phân biệt optimistic concurrency với database isolation;
- thiết kế conflict policy.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Transaction và concurrency token giải **hai bài toán khác nhau**.

- transaction hỏi: “một nhóm thao tác có cùng thành công/thất bại không?”
- concurrency token hỏi: “dữ liệu có bị người khác sửa kể từ lúc tôi đọc không?”

Hai admin cùng thấy `Pending`. Nếu A đổi thành `Paid` trước, B vẫn cầm bản cũ `Pending`. Token giúp B biết rằng mình đang update trên dữ liệu đã lỗi thời.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| transaction | nhóm thao tác atomic |
| isolation | mức độ transaction nhìn thấy thay đổi khác |
| optimistic concurrency | cho phép cùng đọc, phát hiện conflict lúc ghi |
| concurrency token | version dùng để phát hiện stale write |
| lost update | update sau ghi đè update trước ngoài ý muốn |
| affected rows | số row database thực sự update/delete |

Optimistic concurrency không khóa row từ lúc đọc; nó kiểm tra điều kiện khi ghi.

Hai admin cùng mở một Order. A chuyển `Pending → Paid`; B trên màn hình cũ chuyển `Pending → Cancelled`. Nếu blind last-write-wins, thay đổi A có thể bị ghi đè.

## 3. Lời giải chạy được

CommerceLab dùng `Guid ConcurrencyToken`:

~~~csharp
var order = await db.Orders.SingleAsync(x => x.OrderId == orderId);

order.Status = "Paid";
order.ConcurrencyToken = Guid.NewGuid();

try
{
    await db.SaveChangesAsync(cancellationToken);
}
catch (DbUpdateConcurrencyException)
{
    // Reload/merge/return 409 tùy business policy.
    throw;
}
~~~

Mapping:

~~~csharp
entity.Property(order => order.ConcurrencyToken)
    .IsConcurrencyToken();
~~~

### Walkthrough: timeline hai admin

Ban đầu:

~~~text
Order 42: Status=Pending, Token=T1
~~~

Admin A:

~~~text
read → Pending, T1
UPDATE ...
WHERE OrderId=42 AND Token=T1
SET Status=Paid, Token=T2
→ affected rows = 1
~~~

Admin B vẫn giữ bản cũ:

~~~text
read trước đó → Pending, T1
UPDATE ...
WHERE OrderId=42 AND Token=T1
SET Status=Cancelled, Token=T3
→ affected rows = 0
~~~

EF thấy 0 row và ném `DbUpdateConcurrencyException`.

Điểm quan trọng: conflict được phát hiện **vì token cũ không còn match**, không phải vì EF biết ý định business của A/B.

## 4. Cơ chế hoạt động

### Transaction vs concurrency token

| | Transaction | Concurrency token |
|---|---|---|
| Mục tiêu | atomicity/consistency trong operation | phát hiện stale write |
| Thời điểm | trong phạm vi DB work | lúc update/delete |
| Có ngăn người khác đọc/sửa? | tùy isolation/lock | thường không |
| Business conflict policy | không giải quyết hết | cần quyết định sau exception |

### Conflict xong thì làm gì?

Không có đáp án chung:

- reload và yêu cầu user xác nhận lại;
- store-wins;
- client-wins có kiểm soát;
- merge field độc lập;
- retry nếu operation idempotent và business cho phép.

### Misconception check

**Đúng hay sai?** Bắt `DbUpdateConcurrencyException` rồi retry vô hạn là an toàn.

**Đáp án:** Sai. Bạn có thể ghi đè intent mới hoặc loop vô hạn.

**Đúng hay sai?** Có transaction thì không cần concurrency token.

**Đáp án:** Sai. Transaction scope ngắn không ngăn stale UI data giữa hai request.

### Mini-check

Nếu user mở form 10 phút rồi save, transaction có thể giữ từ lúc mở form không?

Đáp án: không hợp lý; optimistic token phù hợp hơn để phát hiện stale write khi save.

EF nhớ original token. UPDATE sinh predicate gồm key + original token. Nếu affected rows = 0, EF coi là concurrency conflict.

SQL Server `rowversion` là lựa chọn provider-specific phổ biến; application-managed Guid/token hữu ích khi muốn cross-provider hoặc kiểm soát lúc token đổi.

Transaction isolation ngăn/cho phép anomaly ở database level; optimistic token phát hiện lost-update theo entity/version. Hai khái niệm bổ sung nhau.

## 5. Kiến thức nền và prerequisites

### Ba tầng học

**Beginner core:** atomicity khác stale-write detection.

**Working developer:** token, 409/conflict flow, retry policy.

**Deep dive:** `rowversion`, isolation anomalies, conditional update và contention strategy.

Module 08 đã học ACID/isolation/deadlock. Đừng nhầm optimistic concurrency là thay thế transaction.

Must know: conflict path phải được test như happy path.

## 6. Lỗi thường gặp

**Catch concurrency exception rồi retry vô hạn.** Có thể ghi đè intent mới.

**Token không đổi khi state quan trọng đổi.** Conflict không được phát hiện.

**Giữ transaction mở khi gọi external payment API.** Lock lifetime kéo dài.

## 7. Khi nào KHÔNG dùng

Không thêm concurrency token cho dữ liệu append-only không update.

Không dùng pessimistic lock chỉ vì sợ conflict hiếm; operational cost có thể cao hơn.

Không auto-merge field business-critical nếu không có rule rõ.

## 8. Production notes & scale check

API thường map concurrency conflict thành 409 Conflict/ETag-like flow tùy contract.

Team nhỏ: token + reload + yêu cầu user retry thường đủ cho admin CRUD.

Checkout/payment cần idempotency và external consistency pattern ngoài phạm vi một DB transaction.

## 9. Bài tập kỹ thuật

1. Mở hai context, load cùng Order và tạo conflict.
2. Implement store-wins reload.
3. Thử application-managed token chỉ đổi khi Status đổi.
4. Debug code explicit transaction bao quanh HTTP call.

## 10. Bài tập tích hợp liên module — Judgment

Inventory stock có contention cao. Chọn optimistic token, atomic conditional UPDATE, serializable transaction hay distributed lock? Nêu conflict frequency và invariant.

## 11. Retrieval practice

1. EF phát hiện optimistic conflict bằng cách nào?
2. Token khác isolation level thế nào?
3. Khi nào explicit transaction cần?
4. Vì sao retry conflict là business decision?

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi map/load/update được quan hệ trong sample.
- [ ] Tôi giải thích được số query và số row có thể sinh.
- [ ] Tôi nhận ra concurrency/performance failure mode.
- [ ] Tôi biết khi nào giải pháp đơn giản hơn phù hợp.

- Bài trước: [N+1, projection và split query](./17-n-plus-one-projection-va-split-query.md)
- Bài tiếp theo: [Global query filter và interceptor](./19-global-query-filter-va-interceptor.md)
