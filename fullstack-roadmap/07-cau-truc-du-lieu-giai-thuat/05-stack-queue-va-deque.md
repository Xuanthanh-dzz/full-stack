# Stack, queue và deque

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt **stack** (LIFO — vào sau ra trước) và **queue** (FIFO — vào trước ra trước);
- cài đặt stack trên mảng và queue trên **circular buffer**, hiểu vì sao cả hai đạt `O(1)`;
- dùng stack để giải bài kiểm tra ngoặc cân bằng;
- giải thích vì sao dequeue ngây thơ trên mảng là `O(n)` còn ring buffer là `O(1)`;
- biết **deque** (hàng đợi hai đầu) và các collection có sẵn `Stack<T>`, `Queue<T>`;
- chọn đúng stack/queue theo thứ tự xử lý mà bài toán yêu cầu.

## 2. Bài toán mở đầu

Hai tính năng quen thuộc, hai thứ tự xử lý ngược nhau:

- **Undo trong trình soạn thảo.** Thao tác vừa làm gần nhất phải được hoàn tác **đầu tiên**. Vào sau, ra trước — đây là **stack** (LIFO).
- **Hàng đợi in.** Tài liệu gửi in **trước** phải được in **trước**. Vào trước, ra trước — đây là **queue** (FIFO).

Cả hai đều là "danh sách có kỷ luật": ta không truy cập tùy tiện phần tử thứ `k`, mà chỉ thêm/bớt ở đầu quy định. Chính sự hạn chế đó cho phép cài đặt cực nhanh (`O(1)` mọi thao tác) và làm code rõ ý định. Bài này dựng cả hai từ đầu, rồi dùng stack giải một bài kinh điển — kiểm tra ngoặc cân bằng.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `StackQueueDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace StackQueueDemo;

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine("== Stack (LIFO): vào sau ra trước ==");
        var undo = new ArrayStack<string>();
        undo.Push("gõ 'Xin'");
        undo.Push("gõ ' chào'");
        undo.Push("xóa ' chào'");
        Console.WriteLine($"Đỉnh stack (Peek): {undo.Peek()}");
        Console.WriteLine($"Undo -> {undo.Pop()}");
        Console.WriteLine($"Undo -> {undo.Pop()}");
        Console.WriteLine($"Còn lại {undo.Count} thao tác");

        Console.WriteLine();
        Console.WriteLine("== Ứng dụng stack: kiểm tra ngoặc cân bằng ==");
        foreach (string expr in new[] { "(a+[b*c])", "(a+[b)*c]", "{[()]}", "(((" })
        {
            Console.WriteLine($"  {expr,-12} -> {(IsBalanced(expr) ? "cân bằng" : "SAI")}");
        }

        Console.WriteLine();
        Console.WriteLine("== Queue (FIFO) trên circular buffer: vào trước ra trước ==");
        var jobs = new CircularQueue<int>(capacity: 3);
        jobs.Enqueue(101);
        jobs.Enqueue(102);
        Console.WriteLine($"Dequeue -> {jobs.Dequeue()} (job 101 vào trước, ra trước)");
        jobs.Enqueue(103);
        jobs.Enqueue(104); // dùng lại ô mà 101 để trống (wrap-around)
        Console.WriteLine($"Front hiện tại: {jobs.Peek()}");
        Console.WriteLine($"Lấy hết: {jobs.Dequeue()}, {jobs.Dequeue()}, {jobs.Dequeue()}");

        Console.WriteLine();
        Console.WriteLine("== Collection có sẵn: Stack<T> và Queue<T> ==");
        var s = new Stack<int>();
        s.Push(1); s.Push(2);
        var q = new Queue<int>();
        q.Enqueue(1); q.Enqueue(2);
        Console.WriteLine($"Stack.Pop() = {s.Pop()} (2 ra trước)");
        Console.WriteLine($"Queue.Dequeue() = {q.Dequeue()} (1 ra trước)");
    }

    private static bool IsBalanced(string expr)
    {
        var stack = new ArrayStack<char>();
        foreach (char c in expr)
        {
            if (c is '(' or '[' or '{')
            {
                stack.Push(c);
            }
            else if (c is ')' or ']' or '}')
            {
                if (stack.Count == 0)
                {
                    return false; // ngoặc đóng mà không có ngoặc mở
                }
                char open = stack.Pop();
                bool match = (c == ')' && open == '(')
                          || (c == ']' && open == '[')
                          || (c == '}' && open == '{');
                if (!match)
                {
                    return false;
                }
            }
        }
        return stack.Count == 0; // còn dư ngoặc mở là sai
    }
}

internal sealed class ArrayStack<T>
{
    private T[] _items = new T[4];
    public int Count { get; private set; }

    public void Push(T value)
    {
        if (Count == _items.Length)
        {
            Array.Resize(ref _items, _items.Length * 2);
        }
        _items[Count++] = value; // thêm ở "đỉnh" = cuối mảng: O(1)
    }

    public T Pop()
    {
        if (Count == 0)
        {
            throw new InvalidOperationException("Stack rỗng.");
        }
        T value = _items[--Count]; // lấy từ đỉnh: O(1)
        _items[Count] = default!;  // tránh giữ tham chiếu thừa
        return value;
    }

    public T Peek()
    {
        if (Count == 0)
        {
            throw new InvalidOperationException("Stack rỗng.");
        }
        return _items[Count - 1];
    }
}

internal sealed class CircularQueue<T>
{
    private readonly T[] _items;
    private int _head;  // vị trí phần tử ra tiếp theo
    private int _tail;  // vị trí thêm phần tử tiếp theo
    public int Count { get; private set; }

    public CircularQueue(int capacity)
    {
        _items = new T[capacity];
    }

    public void Enqueue(T value)
    {
        if (Count == _items.Length)
        {
            throw new InvalidOperationException("Queue đầy.");
        }
        _items[_tail] = value;
        _tail = (_tail + 1) % _items.Length; // quay vòng khi tới cuối mảng
        Count++;
    }

    public T Dequeue()
    {
        if (Count == 0)
        {
            throw new InvalidOperationException("Queue rỗng.");
        }
        T value = _items[_head];
        _items[_head] = default!;
        _head = (_head + 1) % _items.Length; // O(1): không dịch phần tử
        Count--;
        return value;
    }

    public T Peek()
    {
        if (Count == 0)
        {
            throw new InvalidOperationException("Queue rỗng.");
        }
        return _items[_head];
    }
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
== Stack (LIFO): vào sau ra trước ==
Đỉnh stack (Peek): xóa ' chào'
Undo -> xóa ' chào'
Undo -> gõ ' chào'
Còn lại 1 thao tác

== Ứng dụng stack: kiểm tra ngoặc cân bằng ==
  (a+[b*c])    -> cân bằng
  (a+[b)*c]    -> SAI
  {[()]}       -> cân bằng
  (((          -> SAI

== Queue (FIFO) trên circular buffer: vào trước ra trước ==
Dequeue -> 101 (job 101 vào trước, ra trước)
Front hiện tại: 102
Lấy hết: 102, 103, 104

== Collection có sẵn: Stack<T> và Queue<T> ==
Stack.Pop() = 2 (2 ra trước)
Queue.Dequeue() = 1 (1 ra trước)
```

## 4. Giải thích cơ chế

### 4.1 Stack là LIFO trên đỉnh mảng

`ArrayStack<T>` chỉ thao tác ở **cuối** mảng nền — chính là "đỉnh" stack. `Push` ghi vào ô `Count` rồi tăng `Count`; `Pop` giảm `Count` rồi trả ô đó. Cả hai đều `O(1)` (thỉnh thoảng `Push` phải resize như dynamic array, nên là `O(1)` amortized).

```text
Push A, Push B, Push C:      Pop -> trả C:
   +---+---+---+                 +---+---+
   | A | B | C | <- đỉnh          | A | B | <- đỉnh
   +---+---+---+                 +---+---+
```

Vì chỉ đụng vào đỉnh, không bao giờ phải dịch phần tử — đó là lý do stack luôn `O(1)`. Trong output, ba thao tác được `Push` theo thứ tự, và `Pop` trả về đúng thao tác mới nhất trước ("xóa ' chào'") — đúng nghĩa undo.

### 4.2 Vì sao stack giải được bài ngoặc cân bằng

Khi gặp ngoặc mở, ta `Push` nó. Khi gặp ngoặc đóng, ngoặc mở **gần nhất chưa đóng** phải khớp với nó — mà "gần nhất" chính là đỉnh stack. Ta `Pop` ra và so loại. Cuối chuỗi, stack phải rỗng (không dư ngoặc mở).

Xét `(a+[b)*c]`: khi tới `)`, đỉnh stack là `[` (mở gần nhất), không khớp `)` → SAI ngay. Cấu trúc LIFO khớp hoàn hảo với tính lồng nhau của ngoặc. Đây là mẫu hình lặp lại ở nhiều nơi: undo, gọi hàm (call stack ở bài [02](./02-de-quy-va-call-stack.md) chính là một stack), duyệt cây theo chiều sâu (bài [11](./11-bfs-va-dfs.md)).

### 4.3 Queue và bẫy `O(n)` của mảng thường

Queue thêm ở một đầu (tail), lấy ở đầu kia (head). Nếu cài ngây thơ trên `List<T>` bằng `RemoveAt(0)` cho dequeue, mỗi lần lấy phải **dịch toàn bộ** phần còn lại sang trái — `O(n)`. Với hàng đợi lớn, đó là thảm họa hiệu năng.

**Circular buffer** khắc phục bằng cách không dịch gì cả: chỉ **dời chỉ số** `_head` và `_tail`, và khi chạm cuối mảng thì quay vòng về đầu bằng `% Length`.

```text
capacity = 3, sau Enqueue 101,102 rồi Dequeue (head tiến), Enqueue 103,104:

chỉ số:    0     1     2
        +-----+-----+-----+
        | 104 | 102 | 103 |
        +-----+-----+-----+
           ^tail=1 sau khi ghi 104 vào ô 0 (ô mà 101 để trống)
        head=1 -> phần tử ra tiếp theo là 102
```

104 được ghi vào **ô 0** — chính ô mà 101 để lại sau khi dequeue. Đó là "wrap-around": mảng được tái sử dụng theo vòng tròn, nên cả `Enqueue` lẫn `Dequeue` đều `O(1)`. `Queue<T>` của .NET dùng đúng kỹ thuật này.

### 4.4 Peek không lấy ra

`Peek` trả phần tử sắp ra (đỉnh stack hoặc đầu queue) mà **không** xóa nó — hữu ích khi cần "nhìn trước" để quyết định. Cả hai lớp đều kiểm tra rỗng trước khi Peek/Pop/Dequeue để không đọc ô không hợp lệ.

### Đào sâu (có thể quay lại sau)

- **Deque (double-ended queue).** Cho thêm/lấy ở **cả hai** đầu, đều `O(1)`. Cài trên circular buffer với cả `_head` và `_tail` di chuyển hai chiều. .NET không có `Deque<T>` sẵn; thường dùng `LinkedList<T>` (mọi thao tác hai đầu `O(1)`) hoặc thư viện ngoài. Stack và queue đều là trường hợp đặc biệt của deque.
- **`Stack<T>`/`Queue<T>` cũng tự phình.** Chúng resize backing array khi đầy, y như dynamic array, nên `Push`/`Enqueue` là `O(1)` amortized. `CircularQueue` ở bài này cố định capacity để minh họa wrap-around cho gọn.
- **Priority queue khác queue thường.** Nếu phần tử ra theo **độ ưu tiên** thay vì thứ tự vào, đó là hàng đợi ưu tiên — cài bằng heap ở bài [08](./08-heap-va-priority-queue.md), không phải FIFO.

## 5. Kiến thức nền

### Stack và queue là abstract data type (ADT)

Chúng được định nghĩa bởi **hợp đồng thao tác**, không phải cách cài đặt:

- **Stack:** `Push`, `Pop`, `Peek`, `Count`. Quy tắc LIFO.
- **Queue:** `Enqueue`, `Dequeue`, `Peek`, `Count`. Quy tắc FIFO.

Cùng một ADT có thể cài trên mảng, circular buffer, hay linked list — miễn giữ đúng hợp đồng và độ phức tạp mong đợi. Người dùng ADT không cần biết bên trong.

### Bảng thao tác và độ phức tạp

| ADT | Thêm | Lấy | Xem | Thứ tự |
|---|---|---|---|---|
| Stack | `Push` `O(1)`* | `Pop` `O(1)` | `Peek` `O(1)` | LIFO |
| Queue | `Enqueue` `O(1)`* | `Dequeue` `O(1)` | `Peek` `O(1)` | FIFO |
| Deque | hai đầu `O(1)`* | hai đầu `O(1)` | hai đầu `O(1)` | hai chiều |

(*) amortized khi backing array tự phình.

### Dùng collection có sẵn

Trong công việc thực tế: `Stack<T>` và `Queue<T>` của .NET đã tối ưu, dùng chúng thay vì tự viết. Lưu ý `Stack<T>` và `Queue<T>` **không** thread-safe; khi nhiều luồng cùng dùng, có `ConcurrentStack<T>`/`ConcurrentQueue<T>` (sẽ gặp ở tuyến bất đồng bộ). Bài này tự viết chỉ để hiểu cơ chế.

## 6. Lỗi thường gặp

### Dequeue bằng `List<T>.RemoveAt(0)`

Đây là bẫy phổ biến nhất: biến queue thành `O(n)` mỗi lần lấy. Dùng `Queue<T>` (circular buffer) thay vì `List<T>` cho hành vi FIFO.

### Quên kiểm tra rỗng

`Pop`/`Dequeue`/`Peek` trên cấu trúc rỗng phải ném lỗi rõ ràng (hoặc dùng `TryPop`/`TryDequeue` trả `bool`). Đọc ô khi `Count == 0` cho ra rác hoặc lỗi khó hiểu.

### Nhầm LIFO với FIFO

Chọn nhầm stack cho bài cần FIFO (hoặc ngược lại) làm sai thứ tự xử lý một cách âm thầm. Hỏi rõ: "phần tử ra trước là phần tử **mới nhất** hay **cũ nhất**?" — mới nhất là stack, cũ nhất là queue.

### Circular buffer không quay vòng

Nếu `Enqueue`/`Dequeue` tăng chỉ số bằng `_tail++` mà quên `% Length`, chỉ số vượt khỏi mảng và ném lỗi. Wrap-around bằng modulo là phần cốt lõi của ring buffer.

### Không phân biệt đầy và rỗng

Khi `_head == _tail`, queue có thể **rỗng** hoặc **đầy** tùy lịch sử. Cài đặt ở đây tránh mập mờ bằng cách giữ `Count` tường minh. Nếu chỉ dựa vào hai con trỏ, phải để trống một ô hoặc dùng cờ để phân biệt.

## 7. Bài tập

### Bài 1 — `TryPop` không ném lỗi

Thêm `bool TryPop(out T value)` vào `ArrayStack<T>`: trả `false` khi rỗng thay vì ném exception. So sánh khi nào nên dùng bản ném lỗi, khi nào nên dùng bản `Try`.

**Gợi ý:** mẫu `Try...(out ...)` phù hợp khi rỗng là tình huống bình thường, không phải lỗi lập trình.

### Bài 2 — Queue tự phình

Sửa `CircularQueue<T>` để khi đầy thì cấp mảng gấp đôi và **sao chép lại theo đúng thứ tự** (bắt đầu từ `_head`), rồi đặt lại `_head = 0`, `_tail = Count`.

**Gợi ý:** cẩn thận copy vòng — phần tử có thể đang "gãy" qua ranh giới mảng; copy lần lượt `Count` phần tử từ `_head` với modulo.

### Bài 3 — Đảo ngược queue bằng stack

Cho một `Queue<int>`, đảo ngược thứ tự các phần tử chỉ dùng thêm một `Stack<int>`.

**Gợi ý:** dequeue toàn bộ vào stack, rồi pop toàn bộ trả lại queue; LIFO sau FIFO cho ra thứ tự đảo.

### Bài 4 — Ngoặc cân bằng có báo vị trí

Mở rộng `IsBalanced` để trả về **vị trí** ký tự đầu tiên gây lỗi (hoặc `-1` nếu cân bằng), thay vì chỉ `bool`.

**Gợi ý:** khi Push, lưu kèm chỉ số; khi phát hiện sai, trả chỉ số hiện tại hoặc chỉ số ngoặc mở còn dư trên đỉnh.

### Bài 5 — Hàng đợi hai đầu

Cài `Deque<T>` trên circular buffer với `PushFront`, `PushBack`, `PopFront`, `PopBack`, tất cả `O(1)`. Kiểm tra bằng cách dùng nó vừa như stack vừa như queue.

**Gợi ý:** `PushFront` cần lùi `_head` với modulo (thêm `Length` trước khi `%` để tránh số âm).

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt được LIFO (stack) và FIFO (queue) và cho ví dụ mỗi loại.
- [ ] Tôi cài được stack trên mảng và giải thích vì sao mọi thao tác là `O(1)`.
- [ ] Tôi giải được bài ngoặc cân bằng bằng stack.
- [ ] Tôi giải thích được circular buffer và vì sao nó tránh dịch `O(n)`.
- [ ] Tôi biết deque là gì và stack/queue là trường hợp đặc biệt của nó.
- [ ] Tôi dùng được `Stack<T>`/`Queue<T>` có sẵn và biết chúng không thread-safe.

Điều hướng:

- Bài prerequisite: [Linked list](./04-linked-list.md)
- Ôn lại nền tảng: [Đệ quy và call stack](./02-de-quy-va-call-stack.md), [Vòng lặp for, while, do-while](../01-nen-tang-lap-trinh/08-vong-lap-for-while-do-while.md)
- Bài tiếp theo: [Hash table và hash function](./06-hash-table-va-hash-function.md)
