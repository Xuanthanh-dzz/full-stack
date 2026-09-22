# Linked list

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích một **node** gồm giá trị và con trỏ tới node kế tiếp tạo thành danh sách liên kết thế nào;
- cài đặt singly linked list với `AddFirst`, `AddLast`, `Remove`, `Contains`, `ElementAt`;
- lý giải vì sao chèn/xóa ở đầu là `O(1)` còn truy cập phần tử thứ `k` là `O(n)`;
- so sánh linked list với dynamic array và chọn đúng theo bài toán;
- vẽ được cách các con trỏ nối lại khi thêm và xóa node;
- biết `LinkedList<T>` có sẵn trong .NET và khi nào nên dùng nó thay vì tự viết.

## 2. Bài toán mở đầu

Ở bài [03](./03-mang-va-dynamic-array.md) ta thấy điểm yếu của cấu trúc dựa trên mảng: chèn hay xóa ở **đầu** hoặc giữa phải dịch toàn bộ phần tử phía sau — `O(n)`. Với một hàng đợi công việc mà thao tác chính là "thêm vào đầu" và "bỏ khỏi đầu" liên tục, `List<T>` trở nên chậm một cách không cần thiết.

Linked list lật ngược đánh đổi đó. Thay vì để phần tử nằm liền kề trong một khối bộ nhớ, mỗi phần tử là một **node** riêng, tự giữ một con trỏ tới node kế tiếp. Thêm vào đầu chỉ là "tạo node mới, cho nó trỏ vào đầu cũ, dời đầu" — `O(1)`, không dịch gì cả. Cái giá phải trả: mất khả năng nhảy thẳng tới phần tử thứ `k`. Bài này dựng linked list từ đầu để thấy rõ cả hai mặt.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `LinkedListDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace LinkedListDemo;

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine("== Singly linked list tự viết ==");
        var list = new SinglyLinkedList<string>();
        list.AddLast("Hà Nội");
        list.AddLast("Huế");
        list.AddLast("Sài Gòn");
        list.AddFirst("Lào Cai");
        Console.WriteLine($"Danh sách: {list}");
        Console.WriteLine($"Số phần tử: {list.Count}");

        Console.WriteLine();
        Console.WriteLine("== Chèn đầu là O(1): chỉ nối lại con trỏ ==");
        list.AddFirst("Điện Biên");
        Console.WriteLine($"Sau AddFirst: {list}");

        Console.WriteLine();
        Console.WriteLine("== Xóa theo giá trị: nối node trước vào node sau ==");
        bool removed = list.Remove("Huế");
        bool stillHasHue = list.Contains("Huế");
        Console.WriteLine($"Remove Huế = {removed} -> {list}");
        Console.WriteLine($"Còn chứa Huế? {stillHasHue}");

        Console.WriteLine();
        Console.WriteLine("== Truy cập phần tử thứ k phải duyệt: O(n) ==");
        Console.WriteLine($"Phần tử ở vị trí 2: {list.ElementAt(2)}");
    }
}

// Node: giữ giá trị và con trỏ tới node kế tiếp.
internal sealed class Node<T>
{
    public T Value { get; }
    public Node<T>? Next { get; set; }

    public Node(T value)
    {
        Value = value;
    }
}

internal sealed class SinglyLinkedList<T>
{
    private Node<T>? _head; // node đầu; null nghĩa là danh sách rỗng
    public int Count { get; private set; }

    public void AddFirst(T value)
    {
        // O(1): tạo node mới, cho nó trỏ vào head cũ, rồi dời head.
        var node = new Node<T>(value) { Next = _head };
        _head = node;
        Count++;
    }

    public void AddLast(T value)
    {
        var node = new Node<T>(value);
        if (_head is null)
        {
            _head = node;
        }
        else
        {
            // O(n): phải đi tới cuối vì không giữ con trỏ tail.
            Node<T> current = _head;
            while (current.Next is not null)
            {
                current = current.Next;
            }
            current.Next = node;
        }
        Count++;
    }

    public bool Remove(T value)
    {
        Node<T>? previous = null;
        Node<T>? current = _head;
        while (current is not null)
        {
            if (EqualityComparer<T>.Default.Equals(current.Value, value))
            {
                if (previous is null)
                {
                    _head = current.Next; // xóa head
                }
                else
                {
                    previous.Next = current.Next; // nối qua node bị xóa
                }
                Count--;
                return true;
            }
            previous = current;
            current = current.Next;
        }
        return false;
    }

    public bool Contains(T value)
    {
        Node<T>? current = _head;
        while (current is not null)
        {
            if (EqualityComparer<T>.Default.Equals(current.Value, value))
            {
                return true;
            }
            current = current.Next;
        }
        return false;
    }

    public T ElementAt(int index)
    {
        if ((uint)index >= (uint)Count)
        {
            throw new ArgumentOutOfRangeException(nameof(index));
        }
        Node<T> current = _head!;
        for (int i = 0; i < index; i++)
        {
            current = current.Next!; // O(n): không nhảy thẳng như mảng
        }
        return current.Value;
    }

    public override string ToString()
    {
        var parts = new List<string>();
        Node<T>? current = _head;
        while (current is not null)
        {
            parts.Add(current.Value?.ToString() ?? "null");
            current = current.Next;
        }
        return string.Join(" -> ", parts);
    }
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
== Singly linked list tự viết ==
Danh sách: Lào Cai -> Hà Nội -> Huế -> Sài Gòn
Số phần tử: 4

== Chèn đầu là O(1): chỉ nối lại con trỏ ==
Sau AddFirst: Điện Biên -> Lào Cai -> Hà Nội -> Huế -> Sài Gòn

== Xóa theo giá trị: nối node trước vào node sau ==
Remove Huế = True -> Điện Biên -> Lào Cai -> Hà Nội -> Sài Gòn
Còn chứa Huế? False

== Truy cập phần tử thứ k phải duyệt: O(n) ==
Phần tử ở vị trí 2: Hà Nội
```

## 4. Giải thích cơ chế

### 4.1 Node và con trỏ

Khác với mảng (các ô liền kề), linked list là chuỗi các object `Node<T>` **nằm rải rác** trên heap, nối với nhau bằng con trỏ `Next`. `_head` giữ node đầu; node cuối có `Next = null` báo hết danh sách:

```text
_head
  |
  v
+------+------+   +------+------+   +------+------+
| Lào  | Next-+-->| Hà   | Next-+-->| Sài  | Next-+--> null
| Cai  |      |   | Nội  |      |   | Gòn  |      |
+------+------+   +------+------+   +------+------+
```

Mỗi mũi tên là một tham chiếu (đã học ở [module 04, bài 05](../04-csharp-co-ban/05-stack-heap-value-type-reference-type.md)). Danh sách "biết" mọi phần tử chỉ qua một con trỏ `_head` duy nhất; muốn tới các node sau phải lần theo `Next`.

### 4.2 `AddFirst` là `O(1)`

Thêm vào đầu chỉ gồm ba bước, không phụ thuộc độ dài:

```text
Trước:   _head -> [A] -> [B] -> null
Thêm X:  new Node(X).Next = _head   (X trỏ vào A)
         _head = new Node            (head chỉ sang X)
Sau:     _head -> [X] -> [A] -> [B] -> null
```

Không có phần tử nào bị dịch. Đây chính là ưu thế linked list mang lại so với `List<T>.Insert(0, ...)`. Trong output, `AddFirst("Điện Biên")` chỉ nối lại vài con trỏ mà thành node đầu mới.

### 4.3 `Remove` nối qua node bị xóa

Xóa một node nghĩa là làm cho node **trước nó** trỏ thẳng tới node **sau nó**, bỏ qua node cần xóa:

```text
Trước:  [Hà Nội] -> [Huế] -> [Sài Gòn]
Xóa Huế: previous(Hà Nội).Next = current(Huế).Next   (= Sài Gòn)
Sau:    [Hà Nội] --------------> [Sài Gòn]
```

Node "Huế" không còn ai trỏ tới, nên garbage collector sẽ thu hồi. Bản thân thao tác nối lại con trỏ là `O(1)`; nhưng vì phải **tìm** node trước đó bằng cách duyệt từ `_head`, tổng chi phí `Remove(value)` là `O(n)`. Nếu đã có sẵn tham chiếu tới node cần xóa và node trước nó, việc nối lại là `O(1)`.

### 4.4 Truy cập theo vị trí là `O(n)`

Đây là cái giá của linked list. Không có công thức `base + i * size` như mảng; muốn lấy phần tử thứ `k` phải xuất phát từ `_head` và đi `k` bước theo `Next`. `ElementAt(2)` phải nhảy qua 2 node mới tới "Hà Nội". Với mảng, cùng thao tác là `O(1)`.

### Đào sâu (có thể quay lại sau)

- **Giữ con trỏ `tail`.** `AddLast` ở đây là `O(n)` vì phải đi tới cuối. Nếu lớp giữ thêm một con trỏ `_tail` (và cập nhật nó mỗi lần thêm), `AddLast` trở thành `O(1)`. Đây là cách các cài đặt thực tế làm.
- **Doubly linked list.** Nếu mỗi node giữ **cả** `Next` lẫn `Previous`, ta đi được hai chiều và xóa một node đã biết trong `O(1)` thật sự (không cần dò `previous`). Đổi lại tốn thêm một con trỏ mỗi node. `LinkedList<T>` của .NET là doubly linked list có cả `_head` lẫn `_tail`.
- **Bộ nhớ và cache.** Node rải rác khắp heap nên duyệt linked list không thân thiện với CPU cache như mảng liền kề. Ngoài ra mỗi node tốn thêm bộ nhớ cho (các) con trỏ. Với dữ liệu nhỏ và duyệt tuần tự nhiều, mảng thường nhanh hơn trong thực tế dù cùng Big-O.

## 5. Kiến thức nền

### Linked list so với dynamic array

| Thao tác | `List<T>` (mảng động) | Singly linked list |
|---|---|---|
| Truy cập `[k]` | `O(1)` | `O(n)` |
| Thêm/xóa ở đầu | `O(n)` | `O(1)` |
| Thêm ở cuối | `O(1)` amortized | `O(1)` nếu giữ `tail`, ngược lại `O(n)` |
| Xóa node đã biết vị trí | `O(n)` (dịch) | `O(1)` nối con trỏ (doubly) |
| Bộ nhớ cache | tốt (liền kề) | kém (rải rác) |
| Bộ nhớ phụ | capacity dư | 1–2 con trỏ mỗi node |

### `LinkedList<T>` có sẵn

.NET cung cấp `System.Collections.Generic.LinkedList<T>` — doubly linked list đầy đủ với `AddFirst`, `AddLast`, `AddBefore`, `AddAfter`, `Remove`, và các thuộc tính `First`, `Last`. Trong công việc thực tế, dùng nó thay vì tự viết. Bài này tự viết chỉ để hiểu cơ chế bên trong.

### Khi nào chọn linked list

Thực tế, **`List<T>` là lựa chọn mặc định** cho hầu hết trường hợp vì truy cập ngẫu nhiên nhanh và thân thiện cache. Chỉ nghiêng về linked list khi: chèn/xóa liên tục ở hai đầu là thao tác chính, và **không** cần truy cập theo chỉ số. Ngay cả hàng đợi/ngăn xếp (bài [05](./05-stack-queue-va-deque.md)) thường được cài trên mảng vòng vì hiệu năng thực tế tốt hơn.

## 6. Lỗi thường gặp

### Mất phần đuôi khi nối con trỏ sai thứ tự

Trong `AddFirst`, nếu gán `_head = node` **trước** khi đặt `node.Next = _head cũ`, bạn mất toàn bộ phần còn lại của danh sách. Luôn cho node mới trỏ vào phần cũ trước, rồi mới dời `_head`.

### Quên cập nhật `_head` khi xóa node đầu

Xóa node đầu tiên phải gán `_head = current.Next`. Nếu chỉ xử lý trường hợp "có previous", việc xóa head sẽ sai. Đó là lý do vòng lặp `Remove` phân biệt `previous is null`.

### `NullReferenceException` khi duyệt

Điều kiện dừng phải là `current is not null`, kiểm tra **trước** khi truy cập `current.Next`. Duyệt tới `current.Next` mà không kiểm tra `current` sẽ ném lỗi ở node cuối.

### Dùng linked list rồi truy cập theo chỉ số trong vòng lặp

Viết `for (i...) list.ElementAt(i)` trên linked list biến vòng lặp `O(n)` thành `O(n^2)`, vì mỗi `ElementAt` lại duyệt lại từ đầu. Muốn duyệt tuần tự, hãy đi theo `Next` một lần (hoặc `foreach`), đừng lập chỉ số.

### Tự viết linked list trong production

Trừ khi có lý do đặc biệt, dùng `LinkedList<T>` hoặc `List<T>` sẵn có. Cài đặt tự viết dễ có bug con trỏ và không được tối ưu như thư viện chuẩn.

## 7. Bài tập

### Bài 1 — Thêm con trỏ `tail`

Sửa `SinglyLinkedList<T>` để giữ thêm `_tail`, biến `AddLast` thành `O(1)`. Cẩn thận cập nhật `_tail` trong cả `AddFirst` (khi danh sách đang rỗng) và `Remove` (khi xóa node cuối).

**Gợi ý:** mọi thao tác đổi cấu trúc đều phải xét ảnh hưởng tới `_tail`; viết vài test nhỏ cho danh sách rỗng và một phần tử.

### Bài 2 — Đảo ngược danh sách

Viết `Reverse()` đảo chiều toàn bộ linked list bằng cách đi qua một lần và lật con trỏ `Next` của từng node. Không tạo node mới.

**Gợi ý:** giữ ba con trỏ `previous`, `current`, `next`; ở mỗi bước cho `current.Next = previous` rồi tiến lên.

### Bài 3 — Tìm phần tử giữa trong một lượt

Tìm node ở giữa danh sách chỉ duyệt **một lần**, không dùng `Count`.

**Gợi ý:** kỹ thuật hai con trỏ — một đi 1 bước, một đi 2 bước; khi con nhanh tới cuối, con chậm ở giữa.

### Bài 4 — Phát hiện vòng lặp

Giả sử một node vô tình trỏ ngược lại một node trước đó tạo thành vòng. Viết hàm phát hiện danh sách có bị lặp vô hạn không.

**Gợi ý:** hai con trỏ nhanh/chậm (Floyd) — nếu chúng gặp nhau thì có vòng; nếu con nhanh chạm `null` thì không.

### Bài 5 — So sánh hiệu năng khái niệm

Không cần code: cho một ứng dụng cần (a) truy cập phần tử thứ `k` rất thường xuyên và (b) chèn ở đầu rất thường xuyên. Giải thích vì sao không cấu trúc nào tối ưu cả hai, và bạn sẽ chọn thế nào nếu buộc phải chọn một.

**Gợi ý:** đây là đánh đổi cốt lõi của bài; nêu rõ thao tác nào chi phối để quyết định.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi giải thích được node gồm giá trị và con trỏ `Next`.
- [ ] Tôi vẽ được các con trỏ thay đổi thế nào khi `AddFirst` và `Remove`.
- [ ] Tôi lý giải được vì sao chèn đầu là `O(1)` còn truy cập `[k]` là `O(n)`.
- [ ] Tôi so sánh được linked list với `List<T>` và chọn đúng theo bài toán.
- [ ] Tôi biết `LinkedList<T>` có sẵn và là doubly linked list.
- [ ] Tôi tránh được lỗi con trỏ và `NullReferenceException` khi duyệt.

Điều hướng:

- Bài prerequisite: [Mảng và dynamic array](./03-mang-va-dynamic-array.md)
- Ôn lại nền tảng: [Stack, heap, value type và reference type](../04-csharp-co-ban/05-stack-heap-value-type-reference-type.md), [Con trỏ và biến (C)](../02-c-chuyen-sau/02-con-tro-va-bien.md)
- Bài tiếp theo: [Stack, queue và deque](./05-stack-queue-va-deque.md)
