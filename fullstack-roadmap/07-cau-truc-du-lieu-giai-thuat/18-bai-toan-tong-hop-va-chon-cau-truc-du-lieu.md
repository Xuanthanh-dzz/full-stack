# Bài toán tổng hợp và chọn cấu trúc dữ liệu

## 1. Mục tiêu

Sau bài này, bạn có thể:

- xuất phát từ **các thao tác cần làm** để chọn cấu trúc dữ liệu, thay vì chọn theo thói quen;
- **kết hợp** nhiều cấu trúc để đạt độ phức tạp mà một cấu trúc đơn không cho được;
- cài đặt hai bài tổng hợp kinh điển: top-K phần tử hay gặp và **LRU cache**;
- phân tích một bài toán theo bảng "thao tác → độ phức tạp mong muốn → cấu trúc";
- nhận ra khi một cấu trúc đơn không đủ và cần ghép chúng lại;
- tự tin đối chiếu trade-off khi thiết kế, không chỉ khi cài thuật toán mẫu.

## 2. Bài toán mở đầu

Suốt module này, mỗi bài giới thiệu một cấu trúc và trả lời "nó làm được gì". Nhưng thực tế đi ngược lại: bạn có **một bài toán** với các thao tác cụ thể, và phải **chọn** cấu trúc phù hợp — thường là ghép nhiều loại.

Ví dụ điển hình: một **LRU cache** (least recently used) cần đồng thời `Get(key)` **O(1)**, `Put(key, value)` **O(1)**, và khi đầy thì **đẩy phần tử ít dùng nhất ra O(1)**. Không cấu trúc đơn nào cho cả ba: `Dictionary` tra O(1) nhưng không biết "ai ít dùng nhất"; `LinkedList` giữ được thứ tự dùng nhưng tra O(n). Lời giải là **ghép** chúng: hash map cho tra cứu tức thì, doubly linked list cho thứ tự — mỗi cấu trúc gánh đúng điểm mạnh của nó.

Bài này dạy chính kỹ năng đó: đọc yêu cầu, liệt kê thao tác, gán độ phức tạp mong muốn, rồi chọn (và ghép) cấu trúc. Đây là bài "gom" cả module lại thành một tư duy thiết kế.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `SynthesisDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace SynthesisDemo;

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine("== Bài 1: Top-K từ hay gặp nhất = Dictionary (đếm) + Heap (chọn K) ==");
        string[] words = "cam cam quyt cam tao quyt tao cam tao xoai".Split(' ');
        var top = TopKFrequent(words, 2);
        Console.WriteLine($"Văn bản: {string.Join(" ", words)}");
        foreach (var (word, count) in top)
        {
            Console.WriteLine($"  {word}: {count} lần");
        }

        Console.WriteLine();
        Console.WriteLine("== Bài 2: LRU cache = Dictionary (tra O(1)) + LinkedList (thứ tự dùng) ==");
        var cache = new LruCache<string, int>(capacity: 3);
        cache.Put("a", 1);
        cache.Put("b", 2);
        cache.Put("c", 3);
        Console.WriteLine($"Get a = {cache.Get("a")} (a vừa được dùng -> mới nhất)");
        cache.Put("d", 4); // đầy -> đẩy phần tử ÍT dùng nhất (b) ra
        Console.WriteLine($"Sau khi thêm d (capacity 3):");
        Console.WriteLine($"  Get b = {Show(cache.TryGetValue("b", out _))} (b đã bị đẩy ra)");
        Console.WriteLine($"  Get a = {cache.Get("a")}, Get c = {cache.Get("c")}, Get d = {cache.Get("d")}");
        Console.WriteLine($"  Thứ tự dùng (mới -> cũ): {cache.DumpOrder()}");
    }

    private static string Show(bool present) => present ? "có" : "không có (miss)";

    // Đếm bằng Dictionary O(1)/từ, chọn K lớn nhất bằng min-heap kích thước K.
    private static List<(string Word, int Count)> TopKFrequent(string[] words, int k)
    {
        var freq = new Dictionary<string, int>();
        foreach (string w in words)
        {
            freq[w] = freq.GetValueOrDefault(w) + 1;
        }
        // min-heap giữ K phần tử tần suất cao nhất; ưu tiên = count
        var heap = new PriorityQueue<(string Word, int Count), int>();
        foreach (var kv in freq)
        {
            heap.Enqueue((kv.Key, kv.Value), kv.Value);
            if (heap.Count > k) heap.Dequeue(); // bỏ phần tử tần suất nhỏ nhất
        }
        var result = new List<(string, int)>();
        while (heap.Count > 0) result.Add(heap.Dequeue());
        result.Reverse(); // heap cho nhỏ trước -> đảo để lớn trước
        return result;
    }
}

// LRU: kết hợp Dictionary (tra nhanh) và LinkedList (giữ thứ tự dùng gần đây).
internal sealed class LruCache<TKey, TValue> where TKey : notnull
{
    private readonly int _capacity;
    private readonly Dictionary<TKey, LinkedListNode<(TKey Key, TValue Value)>> _map = new();
    private readonly LinkedList<(TKey Key, TValue Value)> _order = new(); // đầu = mới dùng nhất

    public LruCache(int capacity) => _capacity = capacity;

    public TValue Get(TKey key)
    {
        if (!_map.TryGetValue(key, out var node))
        {
            throw new KeyNotFoundException();
        }
        Touch(node); // đánh dấu vừa dùng
        return node.Value.Value;
    }

    public bool TryGetValue(TKey key, out TValue value)
    {
        if (_map.TryGetValue(key, out var node))
        {
            Touch(node);
            value = node.Value.Value;
            return true;
        }
        value = default!;
        return false;
    }

    public void Put(TKey key, TValue value)
    {
        if (_map.TryGetValue(key, out var existing))
        {
            existing.Value = (key, value);
            Touch(existing);
            return;
        }
        if (_map.Count == _capacity)
        {
            // đẩy phần tử ít dùng nhất = cuối danh sách
            var lru = _order.Last!;
            _order.RemoveLast();
            _map.Remove(lru.Value.Key);
        }
        var node = new LinkedListNode<(TKey, TValue)>((key, value));
        _order.AddFirst(node); // mới nhất ở đầu
        _map[key] = node;
    }

    private void Touch(LinkedListNode<(TKey Key, TValue Value)> node)
    {
        _order.Remove(node);      // O(1) vì là doubly linked list và có sẵn node
        _order.AddFirst(node);    // đưa lên đầu = mới dùng nhất
    }

    public string DumpOrder() => string.Join(" > ", _order.Select(x => x.Key));
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
== Bài 1: Top-K từ hay gặp nhất = Dictionary (đếm) + Heap (chọn K) ==
Văn bản: cam cam quyt cam tao quyt tao cam tao xoai
  cam: 4 lần
  tao: 3 lần

== Bài 2: LRU cache = Dictionary (tra O(1)) + LinkedList (thứ tự dùng) ==
Get a = 1 (a vừa được dùng -> mới nhất)
Sau khi thêm d (capacity 3):
  Get b = không có (miss) (b đã bị đẩy ra)
  Get a = 1, Get c = 3, Get d = 4
  Thứ tự dùng (mới -> cũ): d > c > a
```

## 4. Giải thích cơ chế

### 4.1 Top-K: mỗi cấu trúc gánh một việc

Bài "K từ hay gặp nhất" tách làm hai thao tác, mỗi thao tác một cấu trúc:

- **Đếm tần suất** — cần tra và cộng theo khóa nhiều lần → `Dictionary<string, int>`, mỗi từ `O(1)`.
- **Chọn K lớn nhất** — không cần sắp **toàn bộ**, chỉ cần K cao nhất → min-heap kích thước K (bài [08](./08-heap-va-priority-queue.md)).

Mẹo heap kích thước K: giữ heap tối đa K phần tử; khi vượt K thì `Dequeue` bỏ phần tử **nhỏ nhất**. Cuối cùng heap chứa đúng K phần tử tần suất cao nhất. Tổng: `O(n)` đếm + `O(n log k)` chọn — rẻ hơn sắp toàn bộ `O(n log n)` khi `k` nhỏ. Với `[cam×4, tao×3, quyt×2, xoai×1]`, top-2 là `cam` và `tao`. Đây là mẫu hình "đếm bằng hash, xếp hạng bằng heap" gặp khắp nơi (thống kê, gợi ý, xử lý log).

### 4.2 LRU cache: ghép để đạt O(1) cả ba thao tác

LRU là bài "ghép cấu trúc" kinh điển nhất. Yêu cầu và lời giải:

| Thao tác | Cần | Cấu trúc gánh |
|---|---|---|
| `Get(key)` tra giá trị | `O(1)` | `Dictionary` |
| Đánh dấu "vừa dùng" | `O(1)` | dời node lên đầu `LinkedList` |
| Đẩy phần tử ít dùng nhất | `O(1)` | xóa `Last` của `LinkedList` |

Chìa khóa là **hai cấu trúc trỏ vào nhau**: `Dictionary` ánh xạ khóa → **chính node** trong linked list (`LinkedListNode`), không phải chỉ giá trị. Nhờ giữ tham chiếu node, thao tác `Touch` (dời node lên đầu) là `O(1)` — `LinkedList<T>` của .NET là doubly linked list nên `Remove(node)` khi đã có node là `O(1)` (bài [04](./04-linked-list.md) đã nói doubly linked list xóa node đã biết là `O(1)`).

### 4.3 Theo dõi một lượt LRU

Sức chứa 3. Thêm `a, b, c` → thứ tự (mới→cũ): `c > b > a`. `Get("a")` đưa `a` lên đầu → `a > c > b`. Giờ `b` là **ít dùng nhất** (cuối danh sách). Thêm `d` khi đã đầy → đẩy `b` ra, `d` lên đầu → `d > a > c`. Đúng như output: `b` miss, còn `a, c, d` vẫn còn, thứ tự `d > c > a` (sau các lần `Get` cuối làm xáo lại).

Điểm tinh tế: nếu chỉ dùng `Dictionary`, ta không biết ai "ít dùng nhất"; nếu chỉ dùng `LinkedList`, tra `Get` phải quét `O(n)`. **Chỉ khi ghép** mới đạt `O(1)` cho mọi thao tác. Đó là bài học trung tâm của cả module: cấu trúc phù hợp không phải lúc nào cũng là một cái tên, mà đôi khi là một **tổ hợp** được thiết kế cho đúng bộ thao tác.

### Đào sâu (có thể quay lại sau)

- **`Dictionary` giá trị là node.** Chi tiết khiến LRU chạy: value của map là `LinkedListNode<...>`, cho phép nhảy thẳng tới node để dời trong `O(1)`. Nếu map chỉ giữ giá trị, ta lại phải tìm node trong list — mất O(1).
- **Các "ghép" phổ biến khác.** Dictionary + heap (top-K, Dijkstra ở bài [12](./12-shortest-path-va-minimum-spanning-tree.md)); Dictionary + doubly linked list (LRU, LFU); trie + heap (autocomplete xếp hạng); union-find + sort (Kruskal); hai heap (median trên luồng dữ liệu).
- **Đo trước khi tối ưu.** Big-O hướng dẫn lựa chọn, nhưng với `n` nhỏ, cấu trúc "tệ hơn" về Big-O có thể nhanh hơn nhờ hằng số và cache. Chọn theo phân tích, rồi **đo** khi hiệu năng quan trọng.
- **Dùng cái có sẵn.** .NET đã có `Dictionary`, `SortedDictionary`, `PriorityQueue`, `LinkedList`, `HashSet`... Phần lớn thời gian bạn **ghép** chúng, không viết lại từ đầu. Hiểu cơ chế (module này) là để ghép đúng và đọc được độ phức tạp.

## 5. Kiến thức nền

### Quy trình chọn cấu trúc dữ liệu

1. **Liệt kê thao tác** bài toán thực sự cần (tra theo khóa? theo chỉ số? lấy min/max? theo thứ tự? theo tiền tố?).
2. **Ước lượng tần suất** mỗi thao tác và kích thước dữ liệu.
3. **Gán độ phức tạp mong muốn** cho thao tác nóng nhất.
4. **Tra bảng** thao tác → cấu trúc (dưới đây).
5. Nếu **không cấu trúc đơn nào** đáp ứng mọi thao tác nóng → **ghép** nhiều cấu trúc.
6. Kiểm tra ràng buộc bộ nhớ, rồi **đo** nếu cần.

### Bảng thao tác → cấu trúc

| Thao tác nóng | Cấu trúc |
|---|---|
| Tra theo chỉ số `O(1)` | mảng / `List<T>` |
| Tra theo khóa `O(1)` | `Dictionary` / `HashSet` |
| Giữ thứ tự sắp xếp + tra `O(log n)` | cây cân bằng (`SortedDictionary`/`SortedSet`) |
| Lấy min/max lặp lại | heap / `PriorityQueue` |
| Thêm/xóa hai đầu `O(1)` | deque / `LinkedList` |
| Truy vấn theo tiền tố | trie |
| Quan hệ mạng lưới, tìm đường | graph + BFS/DFS/Dijkstra |
| Ngắn nhất theo số bước | BFS |

### Vì sao đây là bài tổng hợp

Mỗi dòng trong bảng trên là một bài của module. Bài này không thêm cấu trúc mới; nó dạy **cách dùng cả bộ** như một hộp công cụ: đọc bài toán, phân rã thao tác, chọn và ghép. Đó chính là điều "tư duy chọn độ phức tạp phù hợp" mà roadmap [module 07](../00-huong-dan/roadmap.md) nhắm tới.

## 6. Lỗi thường gặp

### Chọn cấu trúc theo thói quen, không theo thao tác

Mặc định dùng `List<T>` cho mọi thứ rồi `Contains` trong vòng lặp (thành `O(n^2)`). Hãy bắt đầu từ thao tác nóng, không từ cấu trúc quen tay.

### Ép một cấu trúc làm mọi việc

Cố dùng chỉ `Dictionary` cho LRU (không biết ai ít dùng nhất) hoặc chỉ `List` (tra chậm). Khi một cấu trúc không đủ, ghép — đừng gồng.

### Quên rằng map có thể trỏ tới node

Nhiều bài ghép cần map trỏ tới **node/vị trí** trong cấu trúc kia (như LRU), không chỉ giá trị. Bỏ qua chi tiết này làm mất O(1).

### Sắp toàn bộ khi chỉ cần top-K

Sắp `O(n log n)` để lấy vài phần tử lớn nhất là phí khi `k` nhỏ; heap kích thước K cho `O(n log k)`. Chọn công cụ theo đúng nhu cầu.

### Tối ưu Big-O mà bỏ qua thực đo

Với `n` nhỏ, cấu trúc đơn giản có thể nhanh hơn cấu trúc "tối ưu lý thuyết". Dùng Big-O để loại phương án tệ, nhưng đo khi cần chốt hiệu năng.

## 7. Bài tập

### Bài 1 — Kiểm tra anagram nhóm

Cho danh sách từ, nhóm các từ là **anagram** của nhau (cùng tập chữ cái). Chọn cấu trúc và khóa nhóm phù hợp.

**Gợi ý:** `Dictionary<string, List<string>>` với khóa là các chữ cái đã **sắp xếp**; hai anagram có cùng khóa.

### Bài 2 — LFU cache (nâng cao)

Thay chính sách LRU bằng LFU (least frequently used): đẩy phần tử **ít được dùng nhất theo số lần**. Thiết kế cấu trúc đạt `O(1)`.

**Gợi ý:** cần thêm bộ đếm tần suất và nhóm các phần tử cùng tần suất; ghép `Dictionary` với danh sách theo mức tần suất.

### Bài 3 — Median trên luồng

Đọc các số lần lượt, sau mỗi số in **trung vị** hiện tại trong `O(log n)` mỗi lần thêm.

**Gợi ý:** hai heap — max-heap giữ nửa nhỏ, min-heap giữ nửa lớn, cân bằng kích thước; trung vị nằm ở đỉnh một trong hai.

### Bài 4 — Thiết kế bảng xếp hạng (leaderboard)

Cần `AddScore(player, score)`, `GetRank(player)` và `Top(k)`. Liệt kê thao tác, gán độ phức tạp mong muốn, chọn cấu trúc.

**Gợi ý:** cây cân bằng theo điểm (`SortedSet`/`SortedDictionary`) cho thứ hạng; `Dictionary` cho tra điểm theo người chơi.

### Bài 5 — Phân tích một bài của bạn

Chọn một tính năng thực tế bạn từng viết (giỏ hàng, danh bạ, hàng đợi xử lý...). Liệt kê thao tác nóng, gán độ phức tạp mong muốn, và chỉ ra cấu trúc (hoặc tổ hợp) phù hợp nhất.

**Gợi ý:** áp đúng quy trình 6 bước ở mục Kiến thức nền; đây là bài luyện tư duy thiết kế, không cần code hoàn chỉnh.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi xuất phát từ thao tác cần làm để chọn cấu trúc, không theo thói quen.
- [ ] Tôi ghép được nhiều cấu trúc để đạt độ phức tạp một cấu trúc đơn không cho.
- [ ] Tôi cài được top-K (Dictionary + heap) và LRU cache (Dictionary + linked list).
- [ ] Tôi dùng được bảng "thao tác → độ phức tạp → cấu trúc".
- [ ] Tôi hiểu vì sao map cần trỏ tới node trong bài LRU.
- [ ] Tôi phân tích được một bài thực tế của mình theo quy trình 6 bước.

Điều hướng:

- Bài prerequisite: [Dynamic programming](./17-dynamic-programming.md)
- Ôn lại nền tảng: [Heap và priority queue](./08-heap-va-priority-queue.md), [Linked list](./04-linked-list.md), [Hash table và hash function](./06-hash-table-va-hash-function.md)
- Bài tiếp theo: [Dự án engine tìm đường](./19-du-an-engine-tim-duong.md)
