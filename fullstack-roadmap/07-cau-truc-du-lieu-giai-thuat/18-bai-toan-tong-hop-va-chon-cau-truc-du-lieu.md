# Bài toán tổng hợp và chọn cấu trúc dữ liệu

## 1. Mục tiêu

Sau bài này, bạn có thể:

- bắt đầu từ operation và constraint thay vì tên cấu trúc dữ liệu;
- lập decision table giữa array/list/hash/tree/heap/graph;
- kết hợp nhiều cấu trúc cho một feature;
- ước lượng complexity end-to-end;
- nhận ra bottleneck do I/O khác với bottleneck thuật toán;
- giải thích trade-off trong code review và phỏng vấn.

## 2. Bài toán mở đầu

Thiết kế autocomplete sản phẩm có các yêu cầu:

1. tìm exact theo ProductId;
2. kiểm tra SKU tồn tại;
3. autocomplete tên theo prefix;
4. lấy top 10 sản phẩm phổ biến;
5. tính route liên quan giữa category.

Không có một cấu trúc dữ liệu duy nhất tối ưu cho mọi operation.

Một thiết kế có thể dùng:

```text
ProductId -> Dictionary
SKU       -> HashSet
Prefix    -> Trie
Top K     -> Heap/PriorityQueue
Relation  -> Graph
```

Đây mới là cách DSA xuất hiện trong phần mềm thật: **phối hợp cấu trúc theo access pattern**.

## 3. Lời giải bằng code

Sample nhỏ minh họa nhiều index trên cùng domain:

```bash
mkdir DataStructureSelectionDemo
cd DataStructureSelectionDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

```csharp
namespace DataStructureSelectionDemo;

public sealed record Product(
    int Id,
    string Sku,
    string Name,
    int Popularity);

public sealed class ProductIndex
{
    private readonly Dictionary<int, Product> _byId = [];
    private readonly HashSet<string> _skus =
        new(StringComparer.OrdinalIgnoreCase);

    public void Add(Product product)
    {
        ArgumentNullException.ThrowIfNull(product);

        if (!_byId.TryAdd(product.Id, product))
        {
            throw new InvalidOperationException(
                $"Duplicate product id {product.Id}.");
        }

        if (!_skus.Add(product.Sku))
        {
            _byId.Remove(product.Id);
            throw new InvalidOperationException(
                $"Duplicate SKU {product.Sku}.");
        }
    }

    public Product? FindById(int id) =>
        _byId.GetValueOrDefault(id);

    public bool ContainsSku(string sku) =>
        _skus.Contains(sku);

    public IReadOnlyList<Product> TopPopular(int count)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(count);

        var queue = new PriorityQueue<Product, int>();

        foreach (Product product in _byId.Values)
        {
            queue.Enqueue(product, product.Popularity);

            if (queue.Count > count)
            {
                queue.Dequeue();
            }
        }

        var result = new List<Product>();

        while (queue.TryDequeue(out Product? product, out _))
        {
            result.Add(product);
        }

        result.Reverse();
        return result;
    }
}

internal static class Program
{
    private static void Main()
    {
        var index = new ProductIndex();

        index.Add(new(1, "KB-01", "Keyboard", 70));
        index.Add(new(2, "MS-01", "Mouse", 90));
        index.Add(new(3, "MN-01", "Monitor", 80));

        Console.WriteLine(index.FindById(2));
        Console.WriteLine(index.ContainsSku("kb-01"));

        foreach (Product product in index.TopPopular(2))
        {
            Console.WriteLine($"{product.Name}: {product.Popularity}");
        }
    }
}
```

## 4. Giải thích cơ chế

### Bắt đầu từ operation

Đừng hỏi:

> Tôi nên dùng linked list hay tree?

Hãy hỏi:

```text
operation nào thường xuyên nhất?
exact lookup?
range?
prefix?
top-k?
FIFO?
priority?
path?
```

Rồi mới chọn cấu trúc.

### Một domain có nhiều index

Database cũng làm tương tự.

Một table có:

- primary key index;
- unique SKU index;
- index theo CreatedAt;
- full-text/search index.

In-memory model có thể cần nhiều cấu trúc cho nhiều access pattern.

Đổi lại, phải giữ chúng nhất quán khi update.

### Top-K bằng heap

Nếu có `n` product nhưng chỉ cần top `k`:

```text
heap size <= k
```

Mỗi insert:

```text
O(log k)
```

Tổng:

```text
O(n log k)
```

thay vì sort toàn bộ:

```text
O(n log n)
```

### Complexity end-to-end

Một endpoint có thể:

1. query DB: 100ms;
2. deserialize: 5ms;
3. sort 100 item: 0.1ms.

Tối ưu sort từ `O(n log n)` xuống một thuật toán đặc thù không giải quyết bottleneck 100ms database.

DSA phải kết hợp với profiling.

## 5. Kiến thức nền

### Decision table

| Nhu cầu | Cấu trúc ứng viên |
|---|---|
| index access | array / List |
| append nhiều | List |
| exact membership | HashSet |
| key-value lookup | Dictionary |
| sorted/range | balanced tree / sorted structure |
| priority | heap / PriorityQueue |
| FIFO | Queue |
| LIFO | Stack |
| prefix | Trie |
| relation/path | Graph |
| recursion state | Stack / call stack |

### Time-space trade-off

Thêm dictionary index:

- tăng memory `O(n)`;
- giảm lookup từ `O(n)` về average `O(1)`.

Không có lựa chọn miễn phí.

### Maintainability cũng là constraint

Một cấu trúc custom tinh vi có thể nhanh hơn 5% nhưng làm team khó bảo trì.

Production decision cần cân bằng:

- correctness;
- latency;
- memory;
- throughput;
- complexity;
- observability;
- team skill.

## 6. Lỗi thường gặp

### Chọn theo “cấu trúc nhanh nhất”

Không tồn tại cấu trúc nhanh nhất cho mọi operation.

### Tạo quá nhiều index nhưng quên consistency

Nếu update Product mà chỉ sửa dictionary by ID, HashSet SKU/index khác có thể stale.

### Dùng DSA để che query DB sai

Nếu load 1 triệu row về RAM rồi dùng hashset, có thể vấn đề thật là query/filter/index database.

### Micro-optimize trước profiling

Big-O giúp dự đoán scaling; profiler giúp xác định bottleneck thực.

Cần cả hai.

## 7. Bài tập

### Bài 1 — Notification service

Yêu cầu:

- FIFO normal notification;
- urgent priority;
- duplicate suppression;
- lookup by id.

Chọn cấu trúc cho từng operation.

### Bài 2 — Social graph

Thiết kế:

- user lookup;
- friendship;
- mutual friend;
- shortest number of hops.

### Bài 3 — Cache

Thiết kế LRU cache cần:

- lookup O(1);
- move item tới front O(1);
- evict least recently used O(1).

**Gợi ý:** kết hợp dictionary + doubly linked list.

### Bài 4 — API performance review

Endpoint load 200k rows rồi:
- filter;
- group;
- sort;
- lấy top 20.

Đề xuất phần nào nên đẩy xuống database.

### Bài 5 — Architecture note

Viết một đoạn quyết định kỹ thuật gồm:

```text
Requirement
Chosen structure
Complexity
Memory trade-off
Alternative rejected
```

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi bắt đầu từ operation/constraint.
- [ ] Tôi biết một domain có thể cần nhiều index.
- [ ] Tôi tính được time-space trade-off.
- [ ] Tôi phân biệt bottleneck I/O và CPU algorithm.
- [ ] Tôi giải thích được lựa chọn thay vì chỉ nêu tên structure.
- [ ] Tôi có thể review một feature và chọn cấu trúc phù hợp.

Điều hướng:

- Bài trước: [Dynamic programming](./17-dynamic-programming.md)
- Bài tiếp theo: [Dự án — engine tìm đường](./19-du-an-engine-tim-duong.md)
