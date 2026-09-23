# Stack, queue và deque

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- Stack lấy mới nhất; queue lấy cũ nhất; deque thao tác cả hai đầu.
- Chọn theo thứ tự xử lý, như undo hoặc duyệt từng lớp.
- Collection trong RAM không phải queue bền hay tự thread-safe.

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

### Trực giác 60 giây

Chồng đĩa lấy đĩa trên cùng trước; hàng chờ quầy lấy người đến trước. Hai cách giữ cùng dữ liệu nhưng hứa thứ tự khác nhau.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| LIFO | vào sau ra trước | Stack undo |
| FIFO | vào trước ra trước | Queue jobs |
| deque | thêm/bớt được hai đầu | sliding window |
| peek | xem phần tử kế tiếp không lấy ra | Peek |

### Ví dụ nhỏ — tính tay trước

Push A, B, C rồi pop sẽ nhận C, B, A. Enqueue A, B, C rồi dequeue sẽ nhận A, B, C. Với `([)]`, đỉnh stack là `[` nhưng gặp `)`, nên kết quả là false ngay.

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

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```bash
mkdir StackQueueDemo
cd StackQueueDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

Project `.csproj` tạo ở bước trên dùng cấu hình sau:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <LangVersion>13</LangVersion>
  </PropertyGroup>
</Project>
```

Mã Program.cs:

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
        ArgumentNullException.ThrowIfNull(text);
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

### Walkthrough — execution / state / cost

1. DemoUndo push 3 chuỗi rồi TryPop đến rỗng.
2. DemoJobQueue enqueue 3 việc rồi TryDequeue theo FIFO.
3. IsBalanced push ngoặc mở; ngoặc đóng phải khớp đỉnh, cuối cùng stack phải rỗng.
4. Quét ngoặc mất O(L), stack tối đa O(L). Push/enqueue có chi phí amortized O(1) dù đôi lúc resize; pop/peek không copy toàn collection. Ký tự không phải ngoặc được bỏ qua, không phải parser ngôn ngữ đầy đủ.

### Mini-check

Scanner đếm số mở bằng số đóng có đủ loại bỏ([)] không? Vì sao cần lưu thứ tự?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Stack | lấy gần nhất chưa xử lý | undo/DFS, không fairnessFIFO |
| Queue | lấy đến trước | BFS, không urgency |
| PriorityQueue | lấy prioritytốt nhất | cần tie policy, không mặc nhiênFIFO |

### Misconception check

**Đúng hay sai?** Stack<T> là call stack của thread.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: collection managed heap do chương trình giữ.

</details>

**Đúng hay sai?** Chuỗi(a) được scanner xem hợp lệ.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Đúng: sample bỏ qua nonbracket, không kiểm cú pháp biểu thức.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** thứ tự thao tác.

- **Working Developer — dùng khi làm việc:** underflow và validation.

- **Deep Dive — có thể quay lại sau:** bounded/concurrentqueue khi códriver.

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

## 7. Khi nào KHÔNG dùng

Không dùng List.RemoveAt0 cho FIFO lớn. Không dùng Queue thường cho nhiều producer/consumer rồi coi thao tác ghép tự atomic.

## 8. Production notes & scale check

Gate kiểm chuỗi rỗng, đóng sớm, sai loại ngoặc, thiếu ngoặc đóng và ký tự thường; deque chỉ là concept/exercise chưa có implementation chính. Đảo char xử lý đơn vị UTF-16, không hứa đảo grapheme tiếng Việt/emoji đúng hiển thị.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

So event synchronous Module05 với job queue: enqueue đã có nghĩa job hoàn thành chưa? Chọn cầnRAMqueue haydurablequeue theo requirement cụ thể.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Peek khác Pop thế nào?
2. Vì sao bracket cầnLIFO?
3. Queue cung cấp durability không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi giải thích được LIFO và FIFO.
- [ ] Tôi dùng đúng `Stack<T>` và `Queue<T>`.
- [ ] Tôi hiểu deque thao tác được ở hai đầu.
- [ ] Tôi không dùng `List.RemoveAt(0)` làm queue lớn.
- [ ] Tôi phân biệt call stack với `Stack<T>`.
- [ ] Tôi nhận ra use case DFS/BFS tương ứng.

Điều hướng:

- Bài trước: [Linked list](./04-linked-list.md)
- Bài tiếp theo: [Hash table và hash function](./06-hash-table-va-hash-function.md)

### Checkpoint sau cụm bài

- [Failure Lab](./failure-labs/01-queue.md)
- [Spaced Review](./reviews/review-01.md)
