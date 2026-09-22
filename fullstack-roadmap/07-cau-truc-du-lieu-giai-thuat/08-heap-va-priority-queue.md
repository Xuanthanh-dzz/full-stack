# Heap và priority queue

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phát biểu **heap property** và phân biệt min-heap với max-heap;
- giải thích cách lưu một cây nhị phân đầy đủ trong **mảng** bằng công thức chỉ số cha/con;
- cài đặt `Insert` (sift-up) và `ExtractMin` (sift-down) ở `O(log n)`;
- dùng heap để hiện thực **priority queue** — hàng đợi lấy ra theo độ ưu tiên;
- so sánh heap với danh sách sắp xếp và BST cho bài toán lấy phần tử nhỏ/lớn nhất;
- dùng `PriorityQueue<TElement, TPriority>` có sẵn trong .NET.

## 2. Bài toán mở đầu

Một bộ điều phối công việc phải luôn xử lý **việc khẩn cấp nhất trước**: "cứu hỏa: sập server" (ưu tiên 1) phải chạy trước "gửi email" (ưu tiên 3), dù email được thêm vào trước.

Queue thường (bài [05](./05-stack-queue-va-deque.md)) không giúp được — nó là FIFO, không quan tâm ưu tiên. Giữ một danh sách **luôn sắp xếp** thì lấy phần tử nhỏ nhất là `O(1)` nhưng mỗi lần chèn phải tìm chỗ và dịch — `O(n)`. Còn BST (bài [07](./07-tree-va-binary-search-tree.md)) cho `O(log n)` nhưng có thể suy biến và phải lo cân bằng.

**Heap** là cấu trúc chuyên trị bài toán này: lấy phần tử nhỏ nhất (hoặc lớn nhất) ở `O(log n)`, chèn ở `O(log n)`, không bao giờ suy biến, và lưu gọn trong một mảng không cần con trỏ. Nó không giữ **toàn bộ** thứ tự như BST — chỉ bảo đảm phần tử ưu tiên nhất luôn ở đỉnh — và chính sự "làm ít hơn" đó khiến nó nhanh và đơn giản.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `HeapDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace HeapDemo;

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine("== Min-heap: chèn và xem mảng nền ==");
        var heap = new MinHeap<int>();
        foreach (int v in new[] { 5, 3, 8, 1, 9, 2 })
        {
            heap.Insert(v);
            Console.WriteLine($"  Insert({v}) -> mảng: [{heap.Dump()}]  (đỉnh = {heap.Peek()})");
        }

        Console.WriteLine();
        Console.WriteLine("== ExtractMin liên tục -> lấy ra theo thứ tự tăng dần ==");
        var order = new List<int>();
        while (heap.Count > 0)
        {
            order.Add(heap.ExtractMin());
        }
        Console.WriteLine($"Thứ tự lấy ra: [{string.Join(", ", order)}]");

        Console.WriteLine();
        Console.WriteLine("== Ứng dụng: hàng đợi ưu tiên xử lý công việc ==");
        var scheduler = new MinHeap<(int Priority, string Name)>();
        scheduler.Insert((3, "gửi email"));
        scheduler.Insert((1, "cứu hỏa: sập server"));
        scheduler.Insert((2, "duyệt đơn hàng"));
        while (scheduler.Count > 0)
        {
            var job = scheduler.ExtractMin();
            Console.WriteLine($"  [ưu tiên {job.Priority}] {job.Name}");
        }

        Console.WriteLine();
        Console.WriteLine("== PriorityQueue<TElement,TPriority> có sẵn trong .NET ==");
        var pq = new PriorityQueue<string, int>();
        pq.Enqueue("việc thường", 3);
        pq.Enqueue("việc gấp", 1);
        Console.WriteLine($"Dequeue (ưu tiên nhỏ nhất trước): {pq.Dequeue()}");
    }
}

// Min-heap: cha luôn <= con. Lưu trên mảng, không cần con trỏ.
internal sealed class MinHeap<T> where T : IComparable<T>
{
    private readonly List<T> _items = new();
    public int Count => _items.Count;

    public T Peek()
    {
        if (Count == 0) throw new InvalidOperationException("Heap rỗng.");
        return _items[0]; // đỉnh heap luôn ở chỉ số 0
    }

    public void Insert(T value)
    {
        _items.Add(value);        // thêm vào cuối
        SiftUp(_items.Count - 1); // đẩy lên cho đúng vị trí: O(log n)
    }

    public T ExtractMin()
    {
        if (Count == 0) throw new InvalidOperationException("Heap rỗng.");
        T min = _items[0];
        int last = _items.Count - 1;
        _items[0] = _items[last];  // đưa phần tử cuối lên đỉnh
        _items.RemoveAt(last);
        if (_items.Count > 0)
        {
            SiftDown(0);           // đẩy xuống cho đúng vị trí: O(log n)
        }
        return min;
    }

    private void SiftUp(int i)
    {
        while (i > 0)
        {
            int parent = (i - 1) / 2;
            if (_items[i].CompareTo(_items[parent]) >= 0)
            {
                break; // đã >= cha -> đúng chỗ
            }
            Swap(i, parent);
            i = parent;
        }
    }

    private void SiftDown(int i)
    {
        int n = _items.Count;
        while (true)
        {
            int left = 2 * i + 1;
            int right = 2 * i + 2;
            int smallest = i;
            if (left < n && _items[left].CompareTo(_items[smallest]) < 0) smallest = left;
            if (right < n && _items[right].CompareTo(_items[smallest]) < 0) smallest = right;
            if (smallest == i)
            {
                break; // cả hai con đều >= -> đúng chỗ
            }
            Swap(i, smallest);
            i = smallest;
        }
    }

    private void Swap(int a, int b)
    {
        (_items[a], _items[b]) = (_items[b], _items[a]);
    }

    public string Dump() => string.Join(", ", _items);
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
== Min-heap: chèn và xem mảng nền ==
  Insert(5) -> mảng: [5]  (đỉnh = 5)
  Insert(3) -> mảng: [3, 5]  (đỉnh = 3)
  Insert(8) -> mảng: [3, 5, 8]  (đỉnh = 3)
  Insert(1) -> mảng: [1, 3, 8, 5]  (đỉnh = 1)
  Insert(9) -> mảng: [1, 3, 8, 5, 9]  (đỉnh = 1)
  Insert(2) -> mảng: [1, 3, 2, 5, 9, 8]  (đỉnh = 1)

== ExtractMin liên tục -> lấy ra theo thứ tự tăng dần ==
Thứ tự lấy ra: [1, 2, 3, 5, 8, 9]

== Ứng dụng: hàng đợi ưu tiên xử lý công việc ==
  [ưu tiên 1] cứu hỏa: sập server
  [ưu tiên 2] duyệt đơn hàng
  [ưu tiên 3] gửi email

== PriorityQueue<TElement,TPriority> có sẵn trong .NET ==
Dequeue (ưu tiên nhỏ nhất trước): việc gấp
```

## 4. Giải thích cơ chế

### 4.1 Heap property và cây nhị phân đầy đủ

**Min-heap** thỏa: giá trị mỗi node **nhỏ hơn hoặc bằng** giá trị các con của nó. Hệ quả: phần tử nhỏ nhất luôn ở **gốc**. (Max-heap ngược lại: cha ≥ con, lớn nhất ở gốc.)

Khác BST, heap **không** yêu cầu trái < phải; nó chỉ ràng buộc quan hệ cha–con. Nên duyệt heap không cho dãy sắp xếp — heap chỉ hứa "đỉnh là nhỏ nhất", không hơn.

Heap là **cây nhị phân đầy đủ** (complete): mọi tầng đều đầy, trừ tầng cuối được lấp từ trái sang phải. Chính tính "đầy" này cho phép lưu nó trong mảng mà không để lỗ hổng.

### 4.2 Lưu cây trong mảng bằng công thức chỉ số

Không cần `TreeNode` hay con trỏ. Với node ở chỉ số `i`:

```text
cha(i)   = (i - 1) / 2
trái(i)  = 2 * i + 1
phải(i)  = 2 * i + 2
```

Nhìn mảng cuối cùng `[1, 3, 2, 5, 9, 8]` như một cây:

```text
chỉ số:   0    1    2    3    4    5
          1    3    2    5    9    8

              1 (i=0)
            /   \
        3 (i=1)  2 (i=2)
        /  \      \
   5(i=3) 9(i=4)  8(i=5)
```

Kiểm chứng heap property: `1 <= 3` và `1 <= 2`; `3 <= 5` và `3 <= 9`; `2 <= 8`. Đỉnh là 1 — nhỏ nhất. Con của chỉ số 1 là chỉ số `3` và `4`; đúng công thức.

### 4.3 Insert bằng sift-up

Thêm phần tử vào **cuối mảng** (giữ tính đầy), rồi **đẩy lên** (sift-up): so với cha, nếu nhỏ hơn thì đổi chỗ, lặp lại cho tới khi ≥ cha hoặc chạm gốc. Theo dõi `Insert(1)` trong output: `1` được thêm cuối `[3, 5, 8, 1]`, rồi đẩy lên qua `5` và `3` để thành đỉnh `[1, 3, 8, 5]`. Vì cây cao `~log n`, sift-up tối đa `log n` bước — `O(log n)`.

### 4.4 ExtractMin bằng sift-down

Lấy đỉnh (nhỏ nhất) ra. Để lấp chỗ gốc mà vẫn giữ tính đầy, ta **đưa phần tử cuối lên gốc**, rồi **đẩy xuống** (sift-down): so với hai con, đổi chỗ với con **nhỏ hơn**, lặp lại cho tới khi ≤ cả hai con hoặc chạm leaf. Cũng `O(log n)`.

Rút liên tiếp `ExtractMin` cho ra `[1, 2, 3, 5, 8, 9]` — đúng thứ tự tăng dần. Đây chính là ý tưởng của **heapsort** (bài [13](./13-sorting.md)): đổ vào heap rồi rút ra lần lượt, tổng `O(n log n)`.

### Đào sâu (có thể quay lại sau)

- **Xây heap từ mảng có sẵn.** Thay vì `Insert` từng phần tử (`O(n log n)`), có thể "heapify" một mảng bất kỳ trong `O(n)` bằng cách sift-down từ node trong cùng ra gốc. Đây là bước chuẩn bị của heapsort.
- **Priority queue với priority riêng.** Ở ứng dụng scheduler, ta dùng tuple `(int Priority, string Name)`: `ValueTuple` so sánh theo thứ tự từ điển (Priority trước, rồi Name), nên heap sắp theo ưu tiên. `PriorityQueue<TElement, TPriority>` của .NET tách hẳn phần tử và độ ưu tiên cho rõ ràng hơn.
- **Không ổn định thứ tự.** `PriorityQueue<>` của .NET **không** bảo đảm hai phần tử cùng ưu tiên ra theo thứ tự vào (không "stable"). Cần ổn định thì thêm một số thứ tự tăng dần vào khóa ưu tiên.
- **`decrease-key`.** Các thuật toán như Dijkstra (bài [12](./12-shortest-path-va-minimum-spanning-tree.md)) cần "giảm ưu tiên" một phần tử đang trong heap. Heap mảng cơ bản không hỗ trợ trực tiếp; cách phổ biến là chèn bản mới và bỏ qua bản cũ khi lấy ra.

## 5. Kiến thức nền

### Heap so với các lựa chọn khác

| Thao tác | Danh sách sắp xếp | BST cân đối | Heap |
|---|---|---|---|
| Lấy nhỏ nhất | `O(1)` | `O(log n)` | `O(1)` (peek) |
| Rút nhỏ nhất | `O(n)` (dịch) hoặc `O(1)` ở cuối | `O(log n)` | `O(log n)` |
| Chèn | `O(n)` | `O(log n)` | `O(log n)` |
| Duyệt sắp xếp | `O(n)` | `O(n)` | không trực tiếp |

Heap thắng khi thao tác chính là **chèn** và **lấy phần tử ưu tiên nhất** lặp đi lặp lại — đúng định nghĩa priority queue. Không dùng heap khi cần duyệt toàn bộ theo thứ tự thường xuyên (dùng cây).

### Priority queue là một ADT

Giống stack/queue, priority queue được định nghĩa bởi hợp đồng: `Enqueue(item, priority)`, `Dequeue()` (lấy ưu tiên cao nhất), `Peek()`. Heap là cách cài đặt phổ biến nhất, nhưng không phải duy nhất. Người dùng ADT chỉ cần biết "ra theo ưu tiên", không cần biết heap bên trong.

### Ứng dụng thực tế

- Bộ điều phối tác vụ, hàng đợi sự kiện (event simulation).
- Thuật toán đồ thị: Dijkstra, Prim (bài [12](./12-shortest-path-va-minimum-spanning-tree.md)).
- Tìm `k` phần tử nhỏ/lớn nhất mà không sắp xếp toàn bộ.
- Heapsort (bài [13](./13-sorting.md)).

## 6. Lỗi thường gặp

### Nhầm heap với BST

Heap **không** sắp trái < phải; duyệt nó không cho dãy sắp xếp. Chỉ đỉnh được bảo đảm. Cần thứ tự đầy đủ thì dùng cây, không phải heap.

### Sai công thức chỉ số cha/con

`cha = (i-1)/2`, `trái = 2i+1`, `phải = 2i+2` (mảng đánh số từ 0). Dùng công thức của mảng đánh số từ 1 (`2i`, `2i+1`) mà không chỉnh sẽ trỏ sai node.

### Quên sift-down sau khi rút đỉnh

Sau khi đưa phần tử cuối lên gốc, phải sift-down để khôi phục heap property. Bỏ bước này làm heap sai và các `ExtractMin` sau ra kết quả loạn.

### Sift-down đổi chỗ với con lớn hơn

Trong min-heap phải đổi chỗ với con **nhỏ hơn** trong hai con; đổi nhầm với con lớn hơn phá vỡ tính chất. Luôn chọn `smallest` giữa hai con trước khi swap.

### Trông đợi tính ổn định

`PriorityQueue<>` của .NET không stable: hai phần tử cùng ưu tiên có thể ra theo thứ tự bất kỳ. Cần ổn định thì gắn thêm số thứ tự vào ưu tiên.

## 7. Bài tập

### Bài 1 — Max-heap

Sửa `MinHeap<T>` thành `MaxHeap<T>` bằng cách đảo chiều so sánh (cha ≥ con), để `ExtractMax` lấy phần tử lớn nhất.

**Gợi ý:** chỉ cần đổi dấu điều kiện trong `SiftUp`/`SiftDown`; hoặc dùng một `IComparer<T>` đảo chiều để không lặp code.

### Bài 2 — `k` phần tử nhỏ nhất

Cho một mảng lớn, tìm `k` phần tử nhỏ nhất mà **không** sắp xếp toàn bộ. Dùng heap.

**Gợi ý:** đổ hết vào min-heap rồi `ExtractMin` `k` lần — `O(n + k log n)`; hoặc dùng max-heap kích thước `k` để tiết kiệm bộ nhớ.

### Bài 3 — Heapify `O(n)`

Viết constructor nhận sẵn một `List<T>` và biến nó thành heap bằng cách sift-down từ node không phải leaf cuối cùng về gốc. Xác nhận kết quả thỏa heap property.

**Gợi ý:** node cha cuối cùng ở chỉ số `Count/2 - 1`; lặp ngược về 0 và sift-down mỗi node.

### Bài 4 — Kiểm tra một mảng có phải heap

Viết hàm nhận mảng và trả `true` nếu nó thỏa min-heap property. Kiểm tra với `[1, 3, 2, 5, 9, 8]` (đúng) và `[1, 3, 2, 0]` (sai).

**Gợi ý:** với mỗi `i`, kiểm tra `arr[i] <= arr[2i+1]` và `arr[i] <= arr[2i+2]` khi các con còn nằm trong mảng.

### Bài 5 — Trộn `k` danh sách đã sắp xếp

Cho `k` danh sách mỗi cái đã sắp xếp, trộn thành một danh sách sắp xếp bằng heap kích thước `k`.

**Gợi ý:** heap giữ phần tử đầu hiện tại của mỗi danh sách kèm chỉ số danh sách; rút nhỏ nhất rồi nạp phần tử kế tiếp của đúng danh sách đó.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phát biểu được heap property và phân biệt min/max-heap.
- [ ] Tôi ánh xạ được node ↔ chỉ số mảng bằng công thức cha/con.
- [ ] Tôi cài được `Insert` (sift-up) và `ExtractMin` (sift-down) `O(log n)`.
- [ ] Tôi dùng heap để hiện thực priority queue.
- [ ] Tôi biết heap không cho dãy sắp xếp và khi nào chọn heap thay cây/danh sách.
- [ ] Tôi dùng được `PriorityQueue<TElement, TPriority>` của .NET.

Điều hướng:

- Bài prerequisite: [Tree và binary search tree](./07-tree-va-binary-search-tree.md)
- Ôn lại nền tảng: [Mảng và dynamic array](./03-mang-va-dynamic-array.md), [Generics và constraints](../05-csharp-nang-cao/01-generics-va-constraints.md)
- Bài tiếp theo: [Trie](./09-trie.md)
