# Trie

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích trie lưu chuỗi theo prefix;
- cài insert, contains và prefix search;
- phân tích complexity theo độ dài key thay vì số lượng key;
- hiểu trade-off giữa tốc độ prefix lookup và memory;
- áp dụng trie cho autocomplete, dictionary và routing theo prefix;
- phân biệt trie với hash table.

## 2. Bài toán mở đầu

Autocomplete cần trả về từ bắt đầu bằng:

```text
"pro"
```

Dữ liệu:

```text
product
program
profile
project
payment
order
```

Nếu scan toàn bộ list và gọi `StartsWith`, mỗi query phải xem mọi từ.

Trie tổ chức chuỗi theo từng ký tự chung:

```text
root
 └─ p
    └─ r
       └─ o
          ├─ d...
          ├─ g...
          ├─ f...
          └─ j...
```

Prefix `pro` đưa ta trực tiếp tới subtree chứa các kết quả phù hợp.

## 3. Lời giải bằng code

```bash
mkdir TrieDemo
cd TrieDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

```csharp
namespace TrieDemo;

public sealed class Trie
{
    private sealed class Node
    {
        public Dictionary<char, Node> Children { get; } = [];
        public bool IsWord { get; set; }
    }

    private readonly Node _root = new();

    public void Add(string word)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(word);

        Node current = _root;

        foreach (char ch in Normalize(word))
        {
            if (!current.Children.TryGetValue(ch, out Node? next))
            {
                next = new Node();
                current.Children[ch] = next;
            }

            current = next;
        }

        current.IsWord = true;
    }

    public bool Contains(string word)
    {
        Node? node = FindNode(Normalize(word));
        return node?.IsWord == true;
    }

    public IReadOnlyList<string> FindByPrefix(
        string prefix,
        int limit = 10)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(limit);

        string normalized = Normalize(prefix);
        Node? start = FindNode(normalized);

        if (start is null)
        {
            return [];
        }

        var results = new List<string>();
        Collect(start, normalized, results, limit);
        return results;
    }

    private Node? FindNode(string text)
    {
        Node current = _root;

        foreach (char ch in text)
        {
            if (!current.Children.TryGetValue(ch, out Node? next))
            {
                return null;
            }

            current = next;
        }

        return current;
    }

    private static void Collect(
        Node node,
        string current,
        List<string> results,
        int limit)
    {
        if (results.Count >= limit)
        {
            return;
        }

        if (node.IsWord)
        {
            results.Add(current);
        }

        foreach ((char ch, Node child) in node.Children.OrderBy(x => x.Key))
        {
            Collect(child, current + ch, results, limit);

            if (results.Count >= limit)
            {
                return;
            }
        }
    }

    private static string Normalize(string value)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(value);
        return value.Trim().ToLowerInvariant();
    }
}

internal static class Program
{
    private static void Main()
    {
        var trie = new Trie();

        foreach (string word in new[]
        {
            "product", "program", "profile",
            "project", "payment", "order"
        })
        {
            trie.Add(word);
        }

        Console.WriteLine($"Contains product = {trie.Contains("product")}");
        Console.WriteLine($"Contains prod = {trie.Contains("prod")}");

        foreach (string word in trie.FindByPrefix("pro"))
        {
            Console.WriteLine(word);
        }
    }
}
```

Output:

```text
Contains product = True
Contains prod = False
product
profile
program
project
```

## 4. Giải thích cơ chế

### Mỗi cạnh tương ứng một ký tự

Sau khi insert:

```text
product
program
profile
project
```

các prefix chung dùng lại node:

```text
root
 |
 p
 |
 r
 |
 o
 +-- d -- u -- c -- t*
 |
 +-- g -- r -- a -- m*
 |
 +-- f -- i -- l -- e*
 |
 +-- j -- e -- c -- t*
```

Dấu `*` là `IsWord = true`.

### Contains phụ thuộc độ dài từ

Để tìm word dài `L` ký tự, ta đi tối đa `L` edge.

Nếu child lookup là average `O(1)` bằng dictionary:

```text
average O(L)
```

Điểm đáng chú ý: complexity không trực tiếp phụ thuộc số từ `n`.

### Prefix query

Tìm node của prefix:

```text
O(P)
```

với `P` là độ dài prefix.

Sau đó duyệt subtree để lấy `K` kết quả. Chi phí phụ thuộc số node/character cần thăm để tạo các kết quả.

### Prefix có thể là node nhưng chưa phải word

```text
product
```

đã insert.

Node sau "prod" tồn tại nhưng:

```text
IsWord = false
```

nên `Contains("prod")` là false.

Đây là lý do node cần marker kết thúc từ.

## 5. Kiến thức nền

### Trie và HashSet

`HashSet<string>`:

- exact membership rất tốt;
- average lookup gần `O(1)` theo số key, dù hash vẫn phải đọc chuỗi;
- prefix search không được hỗ trợ tự nhiên.

Trie:

- exact lookup theo character path;
- prefix query tự nhiên;
- memory có thể lớn vì nhiều node/dictionary.

### Alphabet và representation

Sample dùng:

```csharp
Dictionary<char, Node>
```

linh hoạt cho Unicode/character set rộng.

Nếu alphabet nhỏ cố định, có thể dùng array child để giảm lookup overhead nhưng tăng memory cho slot trống.

### Compressed trie / radix tree

Khi nhiều node chỉ có một child:

```text
p -> r -> o -> d -> u -> c -> t
```

radix tree có thể nén nhiều ký tự thành một edge.

Đây là optimization nâng cao, không cần cho trie cơ bản.

## 6. Lỗi thường gặp

### Quên IsWord

Nếu chỉ dựa vào path tồn tại, `prod` sẽ bị coi là word dù chỉ `product` được insert.

### Normalize không nhất quán

Nếu `Add` lower-case nhưng `Contains` không lower-case, lookup sai.

Policy normalization phải dùng thống nhất.

### Dùng string concatenation sâu trong hot path

Sample `current + ch` dễ đọc nhưng tạo string mới.

Nếu autocomplete lớn, cần profiling và có thể dùng buffer/StringBuilder/path structure phù hợp.

### Dùng trie cho mọi dictionary

Nếu chỉ exact lookup, `Dictionary`/`HashSet` thường đơn giản và tiết kiệm memory hơn.

## 7. Bài tập

### Bài 1 — Count prefix

Trả số word bắt đầu bằng prefix.

### Bài 2 — Remove

Xóa một word và cleanup node không còn dùng.

### Bài 3 — Top autocomplete

Mỗi word có frequency. Trả top 5 suggestion theo frequency.

### Bài 4 — Longest common prefix

Dùng trie để tìm longest common prefix của một tập từ.

### Bài 5 — Route prefix

Mô phỏng route:

```text
/api/products
/api/profile
/admin/users
```

và tìm các route có prefix `/api/`.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi mô tả được trie theo prefix.
- [ ] Tôi hiểu cần marker `IsWord`.
- [ ] Tôi cài được Add/Contains/FindByPrefix.
- [ ] Tôi phân tích lookup theo độ dài key.
- [ ] Tôi biết trie đổi thêm memory để prefix query nhanh.
- [ ] Tôi phân biệt use case trie và hash table.

Điều hướng:

- Bài trước: [Heap và priority queue](./08-heap-va-priority-queue.md)
- Bài tiếp theo: [Graph và cách biểu diễn](./10-graph-va-cach-bieu-dien.md)
