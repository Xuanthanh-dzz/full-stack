# Heap và priority queue

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích binary heap và heap property;
- phân biệt min-heap với max-heap;
- ánh xạ heap vào array;
- phân tích `O(log n)` cho enqueue/dequeue và `O(1)` cho peek;
- sử dụng `PriorityQueue<TElement,TPriority>` trong .NET;
- áp dụng priority queue cho scheduler, shortest path và top-k;
- không nhầm heap data structure với managed heap memory.

## 2. Bài toán mở đầu

Một hệ thống support có ticket:

```text
P1 - server down
P3 - change avatar
P2 - payment delayed
```

FIFO queue xử lý theo thời gian đến.

Nhưng nghiệp vụ yêu cầu ticket ưu tiên cao được xử lý trước. Ta cần:

```text
dequeue phần tử có priority tốt nhất
```

Priority queue phục vụ đúng pattern này, và binary heap là một implementation phổ biến.

## 3. Lời giải bằng code

```bash
mkdir PriorityQueueDemo
cd PriorityQueueDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

```csharp
namespace PriorityQueueDemo;

public sealed record SupportTicket(
    string Id,
    string Description,
    int Priority);

internal static class Program
{
    private static void Main()
    {
        var queue = new PriorityQueue<SupportTicket, int>();

        Enqueue(queue, new("T-100", "Change avatar", 3));
        Enqueue(queue, new("T-101", "Server down", 1));
        Enqueue(queue, new("T-102", "Payment delayed", 2));
        Enqueue(queue, new("T-103", "Cannot login", 2));

        while (queue.TryDequeue(
            out SupportTicket? ticket,
            out int priority))
        {
            Console.WriteLine(
                $"P{priority}: {ticket.Id} - {ticket.Description}");
        }
    }

    private static void Enqueue(
        PriorityQueue<SupportTicket, int> queue,
        SupportTicket ticket)
    {
        queue.Enqueue(ticket, ticket.Priority);
    }
}
```

Output đảm bảo ticket priority nhỏ hơn được lấy trước; với các phần tử có priority bằng nhau, không nên dựa vào thứ tự ổn định nếu contract không bảo đảm:

```text
P1: T-101 - Server down
P2: ...
P2: ...
P3: T-100 - Change avatar
```

## 4. Giải thích cơ chế

### Min-heap

Min-heap giữ invariant:

```text
parent <= children
```

Ví dụ:

```text
        1
      /   \
     3     2
    / \   /
   8   5  7
```

Phần tử nhỏ nhất luôn ở root.

Do đó peek min:

```text
O(1)
```

### Heap lưu bằng array

Complete binary tree có thể ánh xạ vào array:

```text
tree:
        1
      /   \
     3     2
    / \   /
   8   5  7

array:
index  0  1  2  3  4  5
value [1, 3, 2, 8, 5, 7]
```

Với index `i`:

```text
left child  = 2*i + 1
right child = 2*i + 2
parent      = (i - 1) / 2
```

Không cần node object/reference cho từng cạnh.

### Enqueue — bubble up

Thêm value 0 vào cuối:

```text
[1,3,2,8,5,7,0]
```

Nó có thể vi phạm heap property.

Ta so với parent và swap dần lên:

```text
0 < 2 -> swap
0 < 1 -> swap
```

Height heap là `O(log n)`, nên enqueue:

```text
O(log n)
```

### Dequeue root — bubble down

Lấy root:

1. giữ root để trả về;
2. đưa phần tử cuối lên root;
3. giảm size;
4. swap xuống với child phù hợp cho tới khi invariant được khôi phục.

Complexity:

```text
O(log n)
```

## 5. Kiến thức nền

### Heap không sort toàn bộ dữ liệu

Heap chỉ bảo đảm quan hệ parent-child.

Array heap:

```text
[1, 3, 2, 8, 5, 7]
```

không phải sequence sorted hoàn toàn.

Đổi lại, nó lấy min/max rất hiệu quả.

### PriorityQueue trong .NET

```csharp
var queue = new PriorityQueue<Job, int>();
queue.Enqueue(job, priority);
```

Priority nhỏ hơn được xem là ưu tiên trước theo comparer mặc định.

Muốn max-priority semantics, có thể:

- đảo dấu nếu an toàn;
- dùng comparer phù hợp;
- định nghĩa priority type/comparer rõ nghĩa.

### Top-K

Nếu cần giữ 10 phần tử lớn nhất trong hàng triệu phần tử, có thể giữ min-heap size 10:

- push phần tử mới;
- nếu size > 10 thì bỏ min.

Complexity gần:

```text
O(n log k)
```

thay vì sort toàn bộ `O(n log n)`.

## 6. Lỗi thường gặp

### Nhầm heap với managed heap

Binary heap:

- data structure;
- dùng cho priority.

Managed heap:

- vùng memory nơi object .NET được cấp phát.

Hai khái niệm chỉ trùng tên.

### Dùng priority queue như sorted list

Priority queue tối ưu lấy phần tử tốt nhất tiếp theo, không tối ưu random access theo thứ tự.

### Giả định stable ordering

Hai item cùng priority không nhất thiết ra theo đúng thứ tự enqueue nếu implementation không hứa stable.

Nếu cần tie-breaker, đưa thêm sequence vào priority.

### Dùng sort mỗi lần lấy min

Nếu mỗi lần thêm job lại sort toàn list, chi phí không cần thiết lớn hơn nhiều so với heap.

## 7. Bài tập

### Bài 1 — Scheduler

Tạo 10 job có priority, dequeue theo priority.

### Bài 2 — Stable priority

Dùng priority dạng tuple:

```csharp
(int Priority, long Sequence)
```

để cùng priority thì FIFO.

### Bài 3 — Top 3

Tìm 3 số lớn nhất trong một stream bằng priority queue.

### Bài 4 — K-way merge

Có nhiều sorted list. Dùng heap để luôn lấy phần tử nhỏ nhất hiện tại giữa các list.

### Bài 5 — Heap operation trace

Vẽ array sau từng bước insert:

```text
8, 3, 10, 1, 6
```

vào min-heap.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt min-heap và max-heap.
- [ ] Tôi ánh xạ parent/child từ index array.
- [ ] Tôi giải thích bubble-up và bubble-down.
- [ ] Tôi biết peek `O(1)`, enqueue/dequeue `O(log n)`.
- [ ] Tôi dùng được `PriorityQueue<TElement,TPriority>`.
- [ ] Tôi không nhầm binary heap với managed heap.

Điều hướng:

- Bài trước: [Tree và binary search tree](./07-tree-va-binary-search-tree.md)
- Bài tiếp theo: [Trie](./09-trie.md)
