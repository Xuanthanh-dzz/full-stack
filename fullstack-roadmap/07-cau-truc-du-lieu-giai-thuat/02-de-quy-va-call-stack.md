# Đệ quy và call stack

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích đệ quy là gì và vì sao mọi lời gọi đệ quy cần một điều kiện dừng;
- vẽ được call stack khi một hàm tự gọi chính nó;
- phân biệt recursive case và base case;
- phân tích time complexity và space complexity của một hàm đệ quy đơn giản;
- nhận ra lỗi stack overflow và nguyên nhân thường gặp;
- chuyển một số thuật toán đệ quy sang dạng lặp bằng loop hoặc stack tường minh;
- quyết định khi nào đệ quy làm code rõ hơn và khi nào nên tránh.

## 2. Bài toán mở đầu

Giả sử cần tính tổng các số từ `1` đến `n`.

Cách lặp:

```csharp
static long SumIterative(int n)
{
    long total = 0;

    for (int i = 1; i <= n; i++)
    {
        total += i;
    }

    return total;
}
```

Cách đệ quy:

```csharp
static long SumRecursive(int n)
{
    if (n == 0)
    {
        return 0;
    }

    return n + SumRecursive(n - 1);
}
```

Hai phiên bản cho cùng kết quả. Nhưng phiên bản đệ quy tạo thêm nhiều stack frame. Nếu không hiểu call stack, bạn rất dễ viết một hàm chạy đúng với input nhỏ rồi crash khi input lớn.

Đệ quy không chỉ xuất hiện trong bài toán toán học. Nó là cách tự nhiên để duyệt:

- cây thư mục;
- cây DOM;
- biểu thức cú pháp;
- cấu trúc tree;
- DFS trên graph;
- các cấu trúc có tính chất "một phần chứa các phần cùng kiểu".

## 3. Lời giải bằng code

Tạo project:

```bash
mkdir RecursionDemo
cd RecursionDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `RecursionDemo.csproj` bằng:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
</Project>
```

Thay `Program.cs`:

```csharp
namespace RecursionDemo;

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine($"SumRecursive(5) = {SumRecursive(5)}");
        Console.WriteLine($"SumIterative(5) = {SumIterative(5)}");
        Console.WriteLine();

        Console.WriteLine("Trace factorial(4):");
        Console.WriteLine($"Result = {FactorialWithTrace(4)}");
        Console.WriteLine();

        int[] values = [3, 8, 2, 9, 5];
        Console.WriteLine($"Max = {FindMax(values, 0)}");

        Console.WriteLine();
        Console.WriteLine("Countdown:");
        Countdown(3);
    }

    private static long SumRecursive(int n)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(n);

        if (n == 0)
        {
            return 0;
        }

        return n + SumRecursive(n - 1);
    }

    private static long SumIterative(int n)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(n);

        long total = 0;

        for (int i = 1; i <= n; i++)
        {
            total += i;
        }

        return total;
    }

    private static long FactorialWithTrace(int n, int depth = 0)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(n);

        Console.WriteLine($"{new string(' ', depth * 2)}enter n={n}");

        if (n <= 1)
        {
            Console.WriteLine($"{new string(' ', depth * 2)}return 1");
            return 1;
        }

        long result = n * FactorialWithTrace(n - 1, depth + 1);

        Console.WriteLine(
            $"{new string(' ', depth * 2)}return {n} * ... = {result}");

        return result;
    }

    private static int FindMax(int[] values, int index)
    {
        ArgumentNullException.ThrowIfNull(values);

        if (values.Length == 0)
        {
            throw new ArgumentException("Array must not be empty.", nameof(values));
        }

        if ((uint)index >= (uint)values.Length)
        {
            throw new ArgumentOutOfRangeException(nameof(index));
        }

        if (index == values.Length - 1)
        {
            return values[index];
        }

        int maxOfRest = FindMax(values, index + 1);
        return Math.Max(values[index], maxOfRest);
    }

    private static void Countdown(int n)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(n);

        if (n == 0)
        {
            Console.WriteLine("Go!");
            return;
        }

        Console.WriteLine(n);
        Countdown(n - 1);
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Output chính:

```text
SumRecursive(5) = 15
SumIterative(5) = 15

Trace factorial(4):
enter n=4
  enter n=3
    enter n=2
      enter n=1
      return 1
    return 2 * ... = 2
  return 3 * ... = 6
return 4 * ... = 24
Result = 24

Max = 9

Countdown:
3
2
1
Go!
```

## 4. Giải thích cơ chế

### Một lời gọi hàm tạo một stack frame

Khi gọi:

```csharp
FactorialWithTrace(4)
```

runtime chưa thể trả kết quả ngay vì phải biết:

```text
4 * Factorial(3)
```

Để tính `Factorial(3)`, nó lại cần:

```text
3 * Factorial(2)
```

Call stack tăng dần:

```text
TOP
+----------------------+
| Factorial(1)         |
| n = 1                |
+----------------------+
| Factorial(2)         |
| n = 2                |
+----------------------+
| Factorial(3)         |
| n = 3                |
+----------------------+
| Factorial(4)         |
| n = 4                |
+----------------------+
| Main                 |
+----------------------+
BOTTOM
```

Khi đạt base case `n <= 1`, các frame bắt đầu được tháo ra theo thứ tự ngược lại.

### Base case là điều kiện dừng

Hàm đệ quy thường có hai phần:

```text
base case      -> trả lời trực tiếp
recursive case -> giảm bài toán và gọi lại chính nó
```

Ví dụ:

```csharp
if (n == 0)
{
    return 0;
}

return n + SumRecursive(n - 1);
```

Nếu recursive case không tiến gần base case:

```csharp
return n + SumRecursive(n + 1);
```

stack sẽ tăng mãi cho tới khi không còn đủ stack memory.

### Stack overflow

Mỗi lời gọi hàm dùng một phần stack cho:

- tham số;
- local variable;
- return address;
- trạng thái cần khôi phục khi hàm con trả về.

Đệ quy sâu có thể dẫn tới `StackOverflowException`.

Trong .NET, `StackOverflowException` thường không phải kiểu lỗi bạn nên cố gắng catch để tiếp tục chương trình. Cách đúng là sửa thuật toán hoặc giới hạn độ sâu.

### Time complexity của SumRecursive

`SumRecursive(n)` gọi:

```text
SumRecursive(n - 1)
SumRecursive(n - 2)
...
SumRecursive(0)
```

Có khoảng `n + 1` lời gọi.

Time:

```text
O(n)
```

Space phụ do call stack:

```text
O(n)
```

Phiên bản iterative:

- time: `O(n)`;
- extra stack space: `O(1)`.

Đây là ví dụ điển hình: hai thuật toán cùng time complexity nhưng khác space complexity.

### Đệ quy không phải lúc nào cũng chậm hơn một cấp Big-O

Nhiều người suy luận:

> Có recursion => complexity xấu.

Không đúng.

Binary search đệ quy vẫn có time `O(log n)`.
Tree traversal thường `O(n)`.
Vấn đề là depth của call stack và số nhánh recursive call.

### Fibonacci ngây thơ: ví dụ đệ quy xấu

```csharp
static long Fibonacci(int n)
{
    if (n <= 1)
    {
        return n;
    }

    return Fibonacci(n - 1) + Fibonacci(n - 2);
}
```

Cây lời gọi lặp lại rất nhiều bài toán giống nhau:

```text
fib(5)
├── fib(4)
│   ├── fib(3)
│   │   ├── fib(2)
│   │   └── fib(1)
│   └── fib(2)
└── fib(3)
    ├── fib(2)
    └── fib(1)
```

`fib(3)`, `fib(2)` bị tính nhiều lần.

Time complexity tăng gần exponential, thường mô tả đơn giản là `O(2^n)`.

Đệ quy không phải nguyên nhân duy nhất; nguyên nhân là **cây lời gọi tạo ra nhiều bài toán con trùng lặp**.

### Tail recursion trong .NET

Một hàm dạng:

```csharp
return Recursive(nextState);
```

được gọi là tail-recursive nếu recursive call là thao tác cuối cùng.

Một số runtime/language có thể tối ưu thành loop và không tăng stack. Trong C#/.NET, bạn không nên dựa vào tail-call optimization như một bảo đảm chung cho code ứng dụng.

Nếu depth có thể rất lớn, dùng loop hoặc stack/queue tường minh thường an toàn hơn.

## 5. Kiến thức nền

### Cách thiết kế một lời giải đệ quy

Dùng bốn câu hỏi:

1. Bài toán nhỏ nhất giải trực tiếp được là gì?
2. Làm sao giảm bài toán hiện tại thành bài toán nhỏ hơn?
3. Làm sao kết hợp kết quả của bài toán nhỏ với phần hiện tại?
4. Mỗi bước có chắc chắn tiến gần base case không?

Ví dụ tìm max:

```text
max([3,8,2,9,5], index=0)
=
max(
    current = 3,
    max([8,2,9,5])
)
```

Base case: chỉ còn phần tử cuối.

### Recursive tree traversal

Giả sử:

```csharp
sealed class Node
{
    public required string Name { get; init; }
    public List<Node> Children { get; } = [];
}
```

Tree có cấu trúc đệ quy: một node chứa các node con cùng kiểu.

Do đó code tự nhiên:

```csharp
static void Print(Node node, int depth)
{
    Console.WriteLine($"{new string(' ', depth * 2)}{node.Name}");

    foreach (Node child in node.Children)
    {
        Print(child, depth + 1);
    }
}
```

Đây là trường hợp recursion làm code phản ánh trực tiếp cấu trúc dữ liệu.

### Chuyển recursion thành stack tường minh

Recursive DFS:

```csharp
Visit(node);

foreach (Node child in node.Children)
{
    Dfs(child);
}
```

Có thể chuyển thành:

```csharp
var stack = new Stack<Node>();
stack.Push(root);

while (stack.Count > 0)
{
    Node current = stack.Pop();
    Visit(current);

    for (int i = current.Children.Count - 1; i >= 0; i--)
    {
        stack.Push(current.Children[i]);
    }
}
```

Khác biệt:

- recursion dùng call stack của runtime;
- iterative DFS dùng `Stack<Node>` do bạn kiểm soát.

Stack tường minh nằm trên heap và có thể xử lý cấu trúc sâu hơn mà không phụ thuộc call-stack depth.

### Recursion và immutable state

Recursive function thường dễ hiểu hơn khi mỗi lời gọi nhận state rõ ràng:

```csharp
FindMax(values, index + 1)
```

thay vì phụ thuộc global variable.

Điều này giảm side effect và giúp reasoning/test dễ hơn.

## 6. Lỗi thường gặp

### Không có base case

```csharp
static void PrintForever(int n)
{
    Console.WriteLine(n);
    PrintForever(n + 1);
}
```

Đây không phải loop vô hạn bình thường; nó còn tăng stack ở mỗi bước.

### Có base case nhưng không tiến gần tới nó

```csharp
if (n == 0)
{
    return;
}

Recursive(n + 1);
```

Base case tồn tại nhưng không thể đạt được từ input dương.

### Sửa state sau recursive call nhưng tưởng nó chạy trước

```csharp
Recursive(n - 1);
Console.WriteLine(n);
```

Output sẽ xuất hiện trong giai đoạn stack **unwind**, nên thứ tự đảo ngược.

Với `n = 3`:

```text
1
2
3
```

Nếu `Console.WriteLine(n)` đặt trước recursive call, output là:

```text
3
2
1
```

### Dùng recursion cho input có depth không kiểm soát

Ví dụ parse một file do user upload hoặc tree có thể sâu hàng trăm nghìn node.

Nếu depth không đáng tin cậy, stack tường minh thường an toàn hơn.

### Fibonacci ngây thơ trong production

Code rất ngắn nhưng số lời gọi bùng nổ.

Nếu bài toán có overlapping subproblems, cần:

- memoization;
- dynamic programming;
- hoặc thuật toán khác.

### Nhầm call stack với heap

Stack frame không chứa toàn bộ object.

Ví dụ:

```csharp
var customer = new Customer(...);
```

local variable `customer` nằm trong stack frame, nhưng object `Customer` nằm trên managed heap. Frame giữ reference tới object.

## 7. Bài tập

### Bài 1 — Tổng mảng

Viết:

```csharp
static long Sum(int[] values, int index)
```

bằng recursion.

**Gợi ý:** base case có thể là `index == values.Length`.

Phân tích time và space complexity.

### Bài 2 — Đảo chuỗi

Viết recursive function trả về chuỗi đảo ngược.

Sau đó giải thích vì sao nối `string` liên tục có thể tạo nhiều allocation.

**Gợi ý:** mục tiêu chính là recursion; sau đó thử phiên bản dùng `char[]` hoặc `StringBuilder`.

### Bài 3 — Binary search recursive

Viết binary search nhận:

```csharp
(int[] values, int target, int left, int right)
```

**Gợi ý:** mỗi bước loại bỏ một nửa vùng tìm kiếm.

Phân tích:

- time;
- call-stack space.

### Bài 4 — Chuyển sang iterative

Chuyển `Countdown` và `FindMax` trong sample sang loop.

So sánh:

- độ dễ đọc;
- number of stack frames;
- space complexity.

### Bài 5 — Cây thư mục giả lập

Tạo class:

```csharp
sealed class Folder
{
    public required string Name { get; init; }
    public List<Folder> Children { get; } = [];
}
```

Viết hàm in toàn bộ tree có indent.

Sau đó viết lại bằng `Stack<Folder>`.

**Gợi ý:** nếu muốn giữ đúng thứ tự child, push vào stack theo thứ tự ngược.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi giải thích được base case và recursive case.
- [ ] Tôi vẽ được call stack của một hàm đệ quy đơn giản.
- [ ] Tôi biết vì sao recursion sâu có thể gây stack overflow.
- [ ] Tôi phân tích được time và stack-space complexity.
- [ ] Tôi không mặc định recursion luôn có Big-O xấu.
- [ ] Tôi nhận ra overlapping subproblems trong Fibonacci ngây thơ.
- [ ] Tôi chuyển được recursion sang loop hoặc stack tường minh.
- [ ] Tôi biết khi nào recursion phản ánh cấu trúc tree tự nhiên hơn.

Điều hướng:

- Bài trước: [Big-O: thời gian và bộ nhớ](./01-big-o-thoi-gian-va-bo-nho.md)
- Ôn lại call stack: [Module 01 — Ngăn xếp lời gọi hàm](../01-nen-tang-lap-trinh/10-ngan-xep-loi-goi-ham.md)
- Ôn lại stack/heap trong C#: [Module 04 — Stack, heap, value type và reference type](../04-csharp-co-ban/05-stack-heap-value-type-reference-type.md)
- Bài tiếp theo: [Mảng và dynamic array](./03-mang-va-dynamic-array.md)
