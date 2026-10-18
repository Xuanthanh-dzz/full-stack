# PR Review Lab 01 — Order search service

Bạn là reviewer. Không sửa code trước; hãy review như PR thật.

## Diff

Source diff: [`01-order-search-service.diff`](./diffs/01-order-search-service.diff).

~~~diff
diff --git a/OrderSearchService.cs b/OrderSearchService.cs
new file mode 100644
--- /dev/null
+++ b/OrderSearchService.cs
@@
+public sealed class OrderSearchService(CommerceDbContext db)
+{
+    public async Task<List<Order>> SearchAsync(
+        string? status,
+        decimal? minTotal,
+        int page,
+        int pageSize)
+    {
+        var all = await db.Orders.ToListAsync();
+
+        IEnumerable<Order> query = all;
+
+        if (!string.IsNullOrWhiteSpace(status))
+        {
+            query = query.Where(order => order.Status == status);
+        }
+
+        if (minTotal is not null)
+        {
+            query = query.Where(order => order.TotalAmount >= minTotal.Value);
+        }
+
+        return query
+            .Skip((page - 1) * pageSize)
+            .Take(pageSize)
+            .ToList();
+    }
+}

~~~

## Nhiệm vụ review

Tìm **ít nhất 7 vấn đề hoặc câu hỏi cần làm rõ**. Không phải mọi finding đều cùng severity.

Mỗi comment phải có:

~~~text
Severity:
Location:
Problem:
Impact:
Evidence/Reasoning:
Suggested smallest fix:
~~~

## Rubric

| Nhóm | Trọng số |
|---|---:|
| Correctness | 20% |
| Query execution location | 25% |
| Pagination/determinism | 20% |
| Performance/data movement | 20% |
| API/cancellation/maintainability | 15% |

## Câu hỏi reviewer bắt buộc

1. Filter chạy ở SQL hay process?
2. Page có deterministic không?
3. Request có thể yêu cầu page size vô hạn không?
4. Read-only query có cần tracking không?
5. Method có hỗ trợ cancellation không?

## Submission format

Viết review summary tối đa 12 dòng, sau đó comment theo file/line. Kết thúc bằng một trong ba kết luận: `approve`, `comment`, hoặc `request changes`, kèm lý do.

Không có đáp án đầy đủ trong trang này.