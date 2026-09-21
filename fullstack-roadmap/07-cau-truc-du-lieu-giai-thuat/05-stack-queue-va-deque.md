# Stack, queue và deque

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích LIFO và FIFO;
- sử dụng `Stack<T>` và `Queue<T>`;
- mô tả deque và các thao tác ở hai đầu;
- phân tích complexity của push/pop/enqueue/dequeue;
- áp dụng stack cho undo, parsing và DFS;
- áp dụng queue cho BFS, job processing và buffering;
- phân biệt call stack với data structure stack.

## 2. Bài toán mở đầu

Một editor cần Undo:

```text
gõ "A"
gõ "B"
gõ "C"
Undo -> bỏ "C"
Undo -> bỏ "B"
```

Thứ tự cần lấy ra ngược với thứ tự đưa vào: **LIFO**.

Trong khi đó hệ thống xử lý ticket:

```text
Ticket 1 đến trước
Ticket 2 đến sau
Ticket 3 đến sau nữa
```

thường xử lý theo thứ tự đến: **FIFO**.

Đó là hai pattern dữ liệu cơ bản: stack và queue.

## 3. Lời giải bằng code

```bash
mkdir StackQueueDemo
cd StackQueueDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

```csharp
namespace StackQueueDemo;

internal static class Program
{
    private static void Main()
    {
        DemoUndo();
        Console.WriteLine();

        DemoJobQueue();
        Console.WriteLine();

        Console.WriteLine(
            $"Balanced '{{[()]}}' = {IsBalanced("{[()]}")}");
        Console.WriteLine(
            $"Balanced '{{[(])}}' = {IsBalanced("{[(])}")}");
    }

    private static void DemoUndo()
    {
        var undo = new Stack<string>();

        undo.Push("insert A");
        undo.Push("insert B");
        undo.Push("insert C");

        while (undo.TryPop(out string? action))
        {
            Console.WriteLine($"Undo: {action}");
        }
    }

    private static void DemoJobQueue()
    {
        var jobs = new Queue<string>();

        jobs.Enqueue("job-001");
        jobs.Enqueue("job-002");
        jobs.Enqueue("job-003");

        while (jobs.TryDequeue(out string? job))
        {
            Console.WriteLine($"Process: {job}");
        }
    }

    private static bool IsBalanced(string text)
    {
        var stack = new Stack<char>();

        foreach (char ch in text)
        {
            if (ch is '(' or '[' or '{')
            {
                stack.Push(ch);
                continue;
            }

            if (ch is ')' or ']' or '}')
            {
                if (!stack.TryPop(out char open))
                {
                    return false;
                }

                if (!Matches(open, ch))
                {
                    return false;
                }
            }
        }

        return stack.Count == 0;
    }

    private static bool Matches(char open, char close) =>
        (open, close) is ('(', ')') or ('[', ']') or ('{', '}');
}
```

Output:

```text
Undo: insert C
Undo: insert B
Undo: insert A

Process: job-001
Process: job-002
Process: job-003

Balanced '{[()]}' = True
Balanced '{[(])}' = False
```

## 4. Giải thích cơ chế

### Stack — Last In, First Out

```text
Push A
Push B
Push C

TOP
+---+
| C | <- Pop
+---+
| B |
+---+
| A |
+---+
```

Các thao tác chính:

- `Push`: đưa lên đỉnh;
- `Pop`: lấy và xóa phần tử đỉnh;
- `Peek`: xem đỉnh mà không xóa.

Thông thường đều `O(1)` amortized.

### Queue — First In, First Out

```text
front                       back
  |                           |
  v                           v
[A] [B] [C] [D]
 ^           ^
dequeue     enqueue
```

- `Enqueue`: thêm cuối;
- `Dequeue`: lấy đầu;
- `Peek`: xem đầu.

Với implementation phù hợp, các thao tác chính là `O(1)` amortized.

### Deque

Deque = double-ended queue.

Cho phép:

- add first;
- add last;
- remove first;
- remove last.

Deque hữu ích khi thuật toán cần thao tác ở cả hai đầu, ví dụ sliding-window maximum.

.NET không có một type `Deque<T>` phổ biến trong BCL cơ bản; tùy phiên bản/thư viện có thể dùng cấu trúc khác hoặc tự cài đặt trên circular buffer khi thật sự cần.

### Balanced brackets dùng stack

Khi gặp opening bracket:

```text
( [ {
```

ta push.

Khi gặp closing bracket, phải khớp với **opening bracket gần nhất chưa đóng**. Đây chính xác là LIFO.

Ví dụ:

```text
{ [ ( ) ] }
    ^ ^
    gần nhất
```

## 5. Kiến thức nền

### Call stack và Stack<T> khác nhau

Call stack:

- do runtime quản lý;
- chứa stack frame của function call.

`Stack<T>`:

- là object/collection trên managed heap;
- do chương trình của bạn quản lý;
- có thể lớn hơn call-stack recursion mà không tạo một frame cho mỗi item.

### Circular queue

Một queue hiệu quả trên array thường không dịch toàn bộ phần tử sau mỗi dequeue.

Nó giữ hai chỉ số:

```text
head
 |
 v
[ ][B][C][D][ ][ ]
          ^
          |
         tail
```

Khi đến cuối array, index quay về đầu: circular buffer.

### Stack/Queue trong thực tế

Stack:

- undo/redo;
- expression parsing;
- DFS;
- backtracking;
- browser history concept.

Queue:

- BFS;
- background jobs;
- message processing;
- request buffering;
- producer/consumer.

## 6. Lỗi thường gặp

### Dùng List.RemoveAt(0) làm queue

Xóa index 0 của `List<T>` phải dịch toàn bộ phần tử: `O(n)`.

Dùng `Queue<T>` khi pattern là FIFO.

### Pop khi stack rỗng

`Pop()` ném exception.

Nếu trạng thái rỗng là bình thường, `TryPop` rõ ý định hơn.

### Dùng Queue nhưng cần priority

FIFO không phù hợp nếu job có độ ưu tiên. Khi đó xem `PriorityQueue<TElement,TPriority>`.

### Nhầm queue với concurrent queue

`Queue<T>` không tự động thread-safe cho producer/consumer đa luồng.

Trong concurrency, xem `ConcurrentQueue<T>`, `Channel<T>` hoặc abstraction phù hợp.

## 7. Bài tập

### Bài 1 — Reverse string

Dùng `Stack<char>` để đảo chuỗi.

### Bài 2 — Evaluate postfix

Tính biểu thức hậu tố:

```text
2 3 + 4 *
```

**Gợi ý:** gặp số thì push; gặp operator thì pop hai toán hạng.

### Bài 3 — Printer queue

Mô phỏng 5 print job FIFO.

Mỗi job có:

```text
Id
Pages
```

### Bài 4 — Queue bằng hai stack

Thiết kế queue chỉ dùng hai `Stack<T>`.

Phân tích amortized complexity.

### Bài 5 — Deque use case

Giải thích vì sao sliding-window maximum cần bỏ phần tử ở đầu và thêm/bỏ ở cuối.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi giải thích được LIFO và FIFO.
- [ ] Tôi dùng đúng `Stack<T>` và `Queue<T>`.
- [ ] Tôi hiểu deque thao tác được ở hai đầu.
- [ ] Tôi không dùng `List.RemoveAt(0)` làm queue lớn.
- [ ] Tôi phân biệt call stack với `Stack<T>`.
- [ ] Tôi nhận ra use case DFS/BFS tương ứng.

Điều hướng:

- Bài trước: [Linked list](./04-linked-list.md)
- Bài tiếp theo: [Hash table và hash function](./06-hash-table-va-hash-function.md)
