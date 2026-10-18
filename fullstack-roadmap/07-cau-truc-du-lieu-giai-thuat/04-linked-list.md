# Linked list

## 1. Mục tiêu

Sau bài này, bạn có thể:

- mô tả singly linked list bằng node và reference;
- phân biệt linked list với dynamic array về layout bộ nhớ;
- phân tích độ phức tạp của thêm đầu, thêm cuối, tìm kiếm và xóa;
- tự cài đặt linked list đơn giản bằng C#;
- giải thích vì sao linked list không hỗ trợ truy cập index `O(1)`;
- nhận ra khi nào linked list hữu ích và khi nào `List<T>` vẫn là lựa chọn tốt hơn.

## 2. Bài toán mở đầu

Một danh sách tác vụ cần thường xuyên thêm phần tử vào đầu:

```text
Task C -> Task B -> Task A
```

Với `List<T>`, chèn ở index 0 phải dịch toàn bộ phần tử sang phải: `O(n)`.

Linked list giải quyết bằng cách thay đổi vài reference:

```text
new node -> old head
```

Không cần copy hay dịch phần tử.

Đổi lại, muốn lấy phần tử thứ 500, ta phải đi qua 499 node trước đó.

## 3. Lời giải bằng code

Tạo project:

```bash
mkdir LinkedListDemo
cd LinkedListDemo
dotnet new console --framework net9.0 --use-program-main
```

`LinkedListDemo.csproj`:

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

`Program.cs`:

```csharp
namespace LinkedListDemo;

public sealed class SimpleLinkedList<T>
{
    private sealed class Node(T value)
    {
        public T Value { get; } = value;
        public Node? Next { get; set; }
    }

    private Node? _head;
    private Node? _tail;

    public int Count { get; private set; }

    public void AddFirst(T value)
    {
        var node = new Node(value)
        {
            Next = _head
        };

        _head = node;

        if (_tail is null)
        {
            _tail = node;
        }

        Count++;
    }

    public void AddLast(T value)
    {
        var node = new Node(value);

        if (_tail is null)
        {
            _head = node;
            _tail = node;
        }
        else
        {
            _tail.Next = node;
            _tail = node;
        }

        Count++;
    }

    public bool Contains(T value)
    {
        var comparer = EqualityComparer<T>.Default;
        Node? current = _head;

        while (current is not null)
        {
            if (comparer.Equals(current.Value, value))
            {
                return true;
            }

            current = current.Next;
        }

        return false;
    }

    public bool RemoveFirst(T value)
    {
        var comparer = EqualityComparer<T>.Default;
        Node? previous = null;
        Node? current = _head;

        while (current is not null)
        {
            if (comparer.Equals(current.Value, value))
            {
                if (previous is null)
                {
                    _head = current.Next;
                }
                else
                {
                    previous.Next = current.Next;
                }

                if (ReferenceEquals(_tail, current))
                {
                    _tail = previous;
                }

                Count--;
                return true;
            }

            previous = current;
            current = current.Next;
        }

        return false;
    }

    public IEnumerable<T> Enumerate()
    {
        Node? current = _head;

        while (current is not null)
        {
            yield return current.Value;
            current = current.Next;
        }
    }
}

internal static class Program
{
    private static void Main()
    {
        var list = new SimpleLinkedList<string>();

        list.AddLast("B");
        list.AddLast("C");
        list.AddFirst("A");

        Console.WriteLine(string.Join(" -> ", list.Enumerate()));
        Console.WriteLine($"Count = {list.Count}");
        Console.WriteLine($"Contains B = {list.Contains("B")}");

        list.RemoveFirst("B");

        Console.WriteLine(string.Join(" -> ", list.Enumerate()));
        Console.WriteLine($"Count = {list.Count}");
    }
}
```

Chạy:

```bash
dotnet build
dotnet run --no-build
```

Output:

```text
A -> B -> C
Count = 3
Contains B = True
A -> C
Count = 2
```

## 4. Giải thích cơ chế

### Node và reference

Linked list không lưu phần tử trong một block liên tiếp.

```text
_head
  |
  v
+-------+------+      +-------+------+      +-------+------+
|  A    | next | ---> |  B    | next | ---> |  C    | null |
+-------+------+      +-------+------+      +-------+------+
                                              ^
                                              |
                                            _tail
```

Mỗi node là một object riêng trên heap.

### AddFirst là O(1)

```text
new.Next = head
head = new
```

Số thao tác không phụ thuộc số phần tử.

### AddLast là O(1) khi giữ tail

Nếu không có `_tail`, muốn thêm cuối phải duyệt từ head đến node cuối: `O(n)`.

Giữ `_tail` đổi lấy thêm một reference nhưng giúp append cuối thành `O(1)`.

### Search vẫn là O(n)

Không có index trực tiếp tới node thứ `i`.

Muốn tìm value:

```text
head -> node -> node -> node -> ...
```

worst case phải đi qua toàn bộ danh sách.

### Remove cần biết node trước

Singly linked list chỉ có `Next`.

Để bỏ node hiện tại:

```text
previous.Next = current.Next
```

nên khi duyệt phải giữ cả `previous`.

## 5. Kiến thức nền

### Dynamic array và linked list

| Thao tác | `List<T>` | Singly linked list |
|---|---:|---:|
| truy cập index | `O(1)` | `O(n)` |
| thêm đầu | `O(n)` | `O(1)` |
| thêm cuối | amortized `O(1)` | `O(1)` nếu có tail |
| tìm value | `O(n)` | `O(n)` |
| xóa sau khi đã có node trước | phải dịch | `O(1)` |
| locality | tốt | kém hơn |

Linked list không tự động “nhanh hơn”. Nó nhanh ở một số pattern thao tác cụ thể.

### Doubly linked list

Node giữ:

```text
Previous <- Node -> Next
```

Cho phép duyệt hai chiều và xóa node đã biết dễ hơn, nhưng tốn thêm memory.

.NET có sẵn `LinkedList<T>` là doubly linked list.

### Cache locality

`List<T>` có backing array liên tiếp. CPU cache thường tận dụng traversal tuần tự tốt hơn.

Linked-list node nằm rải trên heap nên pointer chasing có thể làm locality kém.

Đó là lý do complexity giống nhau không có nghĩa hiệu năng thực tế giống nhau.

## 6. Lỗi thường gặp

### Chọn linked list chỉ vì insert O(1)

Nếu trước khi insert bạn phải tìm vị trí bằng `O(n)`, tổng thao tác vẫn `O(n)`.

### Quên cập nhật tail

Khi xóa node cuối, nếu `_tail` vẫn trỏ vào node đã bị loại, lần `AddLast` sau có thể làm cấu trúc sai.

### Quên xử lý danh sách rỗng

`AddFirst` và `AddLast` đầu tiên phải cập nhật cả head và tail.

### Tự viết linked list cho production khi không cần

Bài này nhằm hiểu cơ chế. Trong ứng dụng thật, ưu tiên `LinkedList<T>`, `List<T>` hoặc cấu trúc khác của BCL tùy yêu cầu.

## 7. Bài tập

### Bài 1 — RemoveFirstNode

Viết method xóa node đầu và trả value.

**Gợi ý:** khi danh sách chỉ còn một node, head và tail đều phải về `null`.

### Bài 2 — Reverse

Đảo linked list tại chỗ.

**Gợi ý:** giữ ba reference: `previous`, `current`, `next`.

### Bài 3 — FindMiddle

Tìm phần tử giữa bằng slow/fast pointer.

**Gợi ý:** slow đi 1 bước, fast đi 2 bước.

### Bài 4 — Detect cycle

Mô tả thuật toán Floyd để phát hiện cycle.

**Gợi ý:** nếu slow và fast gặp nhau thì tồn tại cycle.

### Bài 5 — So sánh với List

Viết workload gồm:

- 100.000 lần AddFirst;
- 100.000 lần đọc index ngẫu nhiên.

Dự đoán cấu trúc phù hợp trước khi đo.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi vẽ được node graph của linked list.
- [ ] Tôi giải thích được vì sao truy cập index là `O(n)`.
- [ ] Tôi biết giữ tail giúp AddLast thành `O(1)`.
- [ ] Tôi hiểu xóa node cần nối lại reference.
- [ ] Tôi phân biệt được lợi thế complexity và locality.
- [ ] Tôi không chọn linked list chỉ vì “insert O(1)”.

Điều hướng:

- Bài trước: [Mảng và dynamic array](./03-mang-va-dynamic-array.md)
- Ôn lại reference type: [Stack, heap, value type và reference type](../04-csharp-co-ban/05-stack-heap-value-type-reference-type.md)
- Bài tiếp theo: [Stack, queue và deque](./05-stack-queue-va-deque.md)
