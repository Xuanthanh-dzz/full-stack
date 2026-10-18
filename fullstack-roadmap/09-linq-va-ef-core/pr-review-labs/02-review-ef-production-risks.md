# PR Review Lab 02 — EF production risks

PR này cố gắng thêm job cancel order cũ và search product bằng raw SQL.

## Diff

Source diff: [`02-ef-production-risks.diff`](./diffs/02-ef-production-risks.diff).

~~~diff
diff --git a/OrderAdminService.cs b/OrderAdminService.cs
new file mode 100644
--- /dev/null
+++ b/OrderAdminService.cs
@@
+public sealed class OrderAdminService(CommerceDbContext db)
+{
+    public async Task CancelOldOrdersAsync(DateTime cutoff)
+    {
+        var orders = await db.Orders
+            .Include(order => order.Items)
+            .Include(order => order.Payments)
+            .Where(order => order.OrderedAt < cutoff)
+            .ToListAsync();
+
+        foreach (var order in orders)
+        {
+            order.Status = "Cancelled";
+        }
+
+        try
+        {
+            await db.SaveChangesAsync();
+        }
+        catch (DbUpdateConcurrencyException)
+        {
+            // Ignore: another request probably changed the order.
+        }
+    }
+
+    public async Task<List<Product>> SearchProductsAsync(string name)
+    {
+        return await db.Products
+            .FromSqlRaw($"SELECT * FROM catalog.Products WHERE Name LIKE '%{name}%'")
+            .ToListAsync();
+    }
+}

~~~

## Nhiệm vụ review

Tìm **ít nhất 8 finding** thuộc nhiều nhóm. Đừng chỉ tìm style issue.

## Rubric

| Nhóm | Trọng số |
|---|---:|
| Correctness/concurrency | 25% |
| Security | 25% |
| Performance | 20% |
| Data integrity | 15% |
| Operability/diagnostics | 15% |

## Câu hỏi reviewer bắt buộc

1. Có SQL injection path không?
2. Có load entity graph không cần thiết không?
3. Có cách set-based tốt hơn không?
4. Việc nuốt concurrency exception làm mất thông tin gì?
5. Cancellation/logging/metrics đang ở đâu?
6. `SELECT *` ảnh hưởng contract và payload thế nào?

## Submission format

Viết review comment theo severity `blocker/high/medium/low`. Với mỗi finding, đề xuất **fix nhỏ nhất hợp lý**, không rewrite cả architecture.

Không có đáp án đầy đủ trong trang này.