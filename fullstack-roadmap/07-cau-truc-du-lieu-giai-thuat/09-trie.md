# Trie

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích **trie** (cây tiền tố) lưu tập chuỗi thế nào: cạnh mang ký tự, đường đi tạo thành từ;
- cài đặt `Insert`, `Contains`, `StartsWith` và liệt kê từ theo tiền tố (autocomplete);
- phân biệt "khớp trọn từ" (`IsEndOfWord`) với "tồn tại đường đi" (prefix);
- lý giải vì sao các thao tác là `O(L)` với `L` là độ dài chuỗi, **không** phụ thuộc số từ;
- so sánh trie với hash table và biết khi nào trie thắng (truy vấn theo tiền tố);
- nhận ra chi phí bộ nhớ của trie và các biến thể tiết kiệm.

## 2. Bài toán mở đầu

Ô tìm kiếm gợi ý: người dùng gõ `"car"`, ứng dụng phải lập tức liệt kê mọi từ bắt đầu bằng `"car"` — `car`, `card`, `care`. Đây là **truy vấn theo tiền tố**.

Hash table (bài [06](./06-hash-table-va-hash-function.md)) chịu thua bài này: nó băm **trọn khóa** ra một bucket, nên `"car"` và `"card"` nằm ở hai chỗ chẳng liên quan; muốn tìm mọi từ có tiền tố `"car"` phải quét **toàn bộ** từ điển — `O(n × L)`. BST theo thứ tự từ điển thì làm được range query nhưng lằng nhằng.

**Trie** sinh ra đúng cho bài này. Các từ chia sẻ tiền tố cũng **chia sẻ đường đi** trong cây: `car`, `card`, `care` đi chung nhánh `c → a → r` rồi mới tách. Nhờ vậy tìm mọi từ theo một tiền tố chỉ là "đi tới node cuối của tiền tố rồi gom cây con bên dưới". Bài này dựng một trie phục vụ autocomplete.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `TrieDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace TrieDemo;

internal static class Program
{
    private static void Main()
    {
        var trie = new Trie();
        string[] words = { "can", "cat", "car", "card", "care", "dog" };
        foreach (string w in words)
        {
            trie.Insert(w);
        }
        Console.WriteLine($"Đã thêm: [{string.Join(", ", words)}]");

        Console.WriteLine();
        Console.WriteLine("== Contains: khớp trọn từ (IsEndOfWord) ==");
        foreach (string w in new[] { "car", "ca", "care", "cars" })
        {
            Console.WriteLine($"  Contains(\"{w}\") = {trie.Contains(w)}");
        }

        Console.WriteLine();
        Console.WriteLine("== StartsWith: có từ nào bắt đầu bằng tiền tố? ==");
        foreach (string p in new[] { "ca", "car", "do", "x" })
        {
            Console.WriteLine($"  StartsWith(\"{p}\") = {trie.StartsWith(p)}");
        }

        Console.WriteLine();
        Console.WriteLine("== Autocomplete: liệt kê mọi từ theo tiền tố ==");
        foreach (string p in new[] { "car", "ca", "d" })
        {
            var matches = trie.WordsWithPrefix(p);
            Console.WriteLine($"  \"{p}\" -> [{string.Join(", ", matches)}]");
        }
    }
}

internal sealed class TrieNode
{
    // Mỗi ký tự dẫn tới một node con.
    public Dictionary<char, TrieNode> Children { get; } = new();
    public bool IsEndOfWord { get; set; }
}

internal sealed class Trie
{
    private readonly TrieNode _root = new();

    public void Insert(string word)
    {
        TrieNode node = _root;
        foreach (char c in word)
        {
            if (!node.Children.TryGetValue(c, out TrieNode? next))
            {
                next = new TrieNode();
                node.Children[c] = next; // tạo nhánh mới cho ký tự
            }
            node = next;
        }
        node.IsEndOfWord = true; // đánh dấu kết thúc một từ hoàn chỉnh
    }

    public bool Contains(string word)
    {
        TrieNode? node = Walk(word);
        return node is not null && node.IsEndOfWord;
    }

    public bool StartsWith(string prefix)
    {
        return Walk(prefix) is not null; // chỉ cần đường đi tồn tại
    }

    // Đi theo từng ký tự; trả node cuối hoặc null nếu đứt đường.
    private TrieNode? Walk(string text)
    {
        TrieNode node = _root;
        foreach (char c in text)
        {
            if (!node.Children.TryGetValue(c, out TrieNode? next))
            {
                return null;
            }
            node = next;
        }
        return node;
    }

    public List<string> WordsWithPrefix(string prefix)
    {
        var results = new List<string>();
        TrieNode? start = Walk(prefix);
        if (start is not null)
        {
            Collect(start, prefix, results);
        }
        return results;
    }

    // Duyệt cây con, gom mọi từ hoàn chỉnh; sắp ký tự để kết quả tất định.
    private static void Collect(TrieNode node, string current, List<string> results)
    {
        if (node.IsEndOfWord)
        {
            results.Add(current);
        }
        foreach (char c in node.Children.Keys.OrderBy(k => k))
        {
            Collect(node.Children[c], current + c, results);
        }
    }
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
Đã thêm: [can, cat, car, card, care, dog]

== Contains: khớp trọn từ (IsEndOfWord) ==
  Contains("car") = True
  Contains("ca") = False
  Contains("care") = True
  Contains("cars") = False

== StartsWith: có từ nào bắt đầu bằng tiền tố? ==
  StartsWith("ca") = True
  StartsWith("car") = True
  StartsWith("do") = True
  StartsWith("x") = False

== Autocomplete: liệt kê mọi từ theo tiền tố ==
  "car" -> [car, card, care]
  "ca" -> [can, car, card, care, cat]
  "d" -> [dog]
```

## 4. Giải thích cơ chế

### 4.1 Cấu trúc: cạnh mang ký tự, node chia sẻ tiền tố

Trong trie, mỗi **cạnh** ứng với một ký tự và mỗi **node** ứng với một tiền tố. Các từ dùng chung tiền tố dùng chung phần đầu của đường đi. Sau khi thêm `can, cat, car, card, care, dog`:

```text
        (root)
        /     \
      c         d
      |         |
      a         o
    / | \       |
   n  t  r      g*      (n*, t*, r* là IsEndOfWord)
   *  *  *
         |
         (r nhánh tiếp)
       /   \
      d     e
      *     *
```

Nhánh `c → a` được ba từ `can/cat/car...` **chia sẻ**, chỉ tách ở ký tự thứ ba. `card` và `care` lại chia sẻ tiếp `c → a → r` rồi mới tách ở ký tự thứ tư. Đó là lý do trie gọn cho tập từ có nhiều tiền tố chung.

### 4.2 `IsEndOfWord`: phân biệt từ trọn vẹn với tiền tố

Một node được đi qua **không** có nghĩa là có một từ kết thúc ở đó. `"ca"` là đường đi tồn tại (dẫn tới các từ khác) nhưng bản thân **không** phải một từ đã thêm — nên `Contains("car") = True` còn `Contains("ca") = False`. Cờ `IsEndOfWord` đánh dấu chính xác node nào là điểm cuối của một từ hoàn chỉnh.

Đây là khác biệt cốt lõi giữa hai truy vấn:

- **`Contains(word)`** — đi hết `word` **và** node cuối có `IsEndOfWord`.
- **`StartsWith(prefix)`** — chỉ cần đi hết `prefix` mà không đứt đường; không quan tâm `IsEndOfWord`.

### 4.3 Autocomplete: đi tới tiền tố rồi gom cây con

`WordsWithPrefix("car")` làm hai bước: `Walk("car")` tới node cuối của tiền tố, rồi `Collect` duyệt toàn bộ cây con bên dưới, mỗi lần gặp `IsEndOfWord` thì ghi lại chuỗi đã đi. Kết quả `[car, card, care]` — đúng mọi từ mang tiền tố đó. Việc `OrderBy` các ký tự con khiến kết quả ra theo thứ tự từ điển và **tất định** (nếu không, thứ tự duyệt `Dictionary` là không xác định).

### 4.4 Độ phức tạp `O(L)`, độc lập với số từ

Đây là điểm mạnh nhất của trie. `Insert`, `Contains`, `StartsWith` đều đi tối đa `L` bước với `L` là **độ dài chuỗi** — mỗi bước là một tra cứu `Dictionary` `O(1)`. Chi phí **không** phụ thuộc số từ `n` trong trie. Từ điển một triệu từ hay mười từ, tra một chuỗi dài 5 ký tự vẫn chỉ 5 bước. Hash table cũng `O(L)` cho tra trọn khóa (phải băm cả khóa), nhưng **không** làm được truy vấn tiền tố ở chi phí đó.

### Đào sâu (có thể quay lại sau)

- **Chi phí bộ nhớ.** Trie có thể tốn nhiều bộ nhớ: mỗi node giữ một `Dictionary` con, và các từ ít chia sẻ tiền tố tạo ra nhiều node lẻ. Biến thể **radix tree (compressed trie)** gộp các chuỗi cạnh chỉ có một con thành một cạnh dài, tiết kiệm đáng kể.
- **Bảng con thay Dictionary.** Nếu bảng chữ cái nhỏ và cố định (26 chữ thường), có thể dùng mảng `TrieNode[26]` thay `Dictionary<char, TrieNode>` để nhanh hơn, đổi lấy tốn bộ nhớ cho ô trống. Dictionary linh hoạt hơn cho Unicode.
- **Xóa từ.** `Delete` phức tạp: bỏ `IsEndOfWord`, rồi dọn ngược các node không còn con và không phải end-of-word. Phải cẩn thận không xóa node còn phục vụ từ khác.
- **Ứng dụng khác.** Trie dùng cho kiểm tra chính tả, gợi ý gõ, định tuyến IP (longest prefix match), nén dữ liệu, và tìm kiếm mờ (kết hợp khoảng cách chỉnh sửa).

## 5. Kiến thức nền

### Trie so với hash table

| Tiêu chí | Hash table | Trie |
|---|---|---|
| Tra trọn khóa | `O(L)` trung bình | `O(L)` |
| Truy vấn theo tiền tố | không hiệu quả (`O(n·L)`) | `O(L + số kết quả)` |
| Liệt kê theo thứ tự | không | có (duyệt theo thứ tự ký tự) |
| Bộ nhớ | gọn | có thể tốn (nhiều node) |
| Chia sẻ tiền tố | không tận dụng | tận dụng triệt để |

Quy tắc chọn: cần **truy vấn tiền tố / autocomplete / thứ tự từ điển** thì trie; chỉ cần tra trọn khóa nhanh và tiết kiệm bộ nhớ thì hash table.

### Trie là một loại cây

Trie kế thừa mọi ý tưởng từ bài [07](./07-tree-va-binary-search-tree.md): node, con, duyệt đệ quy. Khác biệt là **cạnh mang thông tin** (ký tự) và một node có thể có nhiều con (không giới hạn hai như cây nhị phân). `Collect` chính là một phép duyệt DFS (bài [11](./11-bfs-va-dfs.md)) trên cây con.

### Vì sao cần đánh dấu end-of-word

Nếu chỉ dựa vào "node là leaf" để nhận từ, ta sẽ sai khi một từ là tiền tố của từ khác: `car` không phải leaf (còn `card`, `care` bên dưới) nhưng vẫn là một từ hợp lệ. Cờ `IsEndOfWord` là cách duy nhất đúng để đánh dấu, độc lập với việc node có con hay không.

## 6. Lỗi thường gặp

### Quên `IsEndOfWord`, dùng leaf để nhận từ

Đây là lỗi phổ biến nhất. `car` là tiền tố của `card` nên không phải leaf; dựa vào leaf sẽ bỏ sót nó. Luôn đánh dấu end-of-word tường minh.

### Nhầm `Contains` với `StartsWith`

`Contains` cần cả đường đi lẫn `IsEndOfWord`; `StartsWith` chỉ cần đường đi. Trả `true` cho `Contains("ca")` chỉ vì đi được tới `"ca"` là sai.

### Thứ tự autocomplete không tất định

Duyệt `Dictionary.Keys` không có thứ tự bảo đảm, nên kết quả autocomplete sẽ lộn xộn giữa các lần chạy. Sắp ký tự con (`OrderBy`) hoặc dùng `SortedDictionary` để có thứ tự ổn định.

### Tạo trie cho dữ liệu không phải chuỗi/tiền tố

Trie chỉ đáng giá khi khóa là chuỗi (hoặc dãy) và bài toán cần tiền tố. Với tra cứu trọn khóa thuần túy, hash table gọn và tốn ít bộ nhớ hơn.

### Bỏ qua chi phí bộ nhớ

Trie trên tập từ ít chia sẻ tiền tố có thể phình bộ nhớ vì mỗi ký tự một node. Cân nhắc radix tree hoặc mảng con khi bộ nhớ là ràng buộc.

## 7. Bài tập

### Bài 1 — Đếm số từ và số node

Thêm hàm đếm tổng số từ (số node có `IsEndOfWord`) và tổng số node trong trie. So hai con số để cảm nhận mức chia sẻ tiền tố.

**Gợi ý:** duyệt DFS đệ quy; đếm `IsEndOfWord` cho số từ, đếm mọi node cho tổng node.

### Bài 2 — `CountWithPrefix`

Viết `int CountWithPrefix(string prefix)` trả **số** từ mang tiền tố, không cần liệt kê chúng.

**Gợi ý:** `Walk(prefix)` rồi đếm số `IsEndOfWord` trong cây con; hoặc bảo trì một bộ đếm ở mỗi node khi `Insert`.

### Bài 3 — Xóa một từ

Cài `Delete(string word)`: bỏ `IsEndOfWord` ở node cuối, rồi dọn ngược các node trở nên vô dụng (không con, không end-of-word).

**Gợi ý:** đệ quy trả về `true` khi node con có thể xóa; cha chỉ gỡ con khỏi `Children` khi con báo có thể xóa.

### Bài 4 — Từ dài nhất là tiền tố hợp lệ liên tục

Cho một tập từ, tìm từ dài nhất mà **mọi** tiền tố của nó (độ dài 1, 2, ...) cũng là một từ trong tập.

**Gợi ý:** thêm hết vào trie, rồi với mỗi từ, đi từng ký tự và kiểm tra mọi node trên đường đều `IsEndOfWord`.

### Bài 5 — So sánh bộ nhớ với hash table

Không cần đo chính xác: với tập từ (a) nhiều tiền tố chung (`car, card, care, cargo`) và (b) ít tiền tố chung (`cat, dog, sun, map`), giải thích trường hợp nào trie tiết kiệm hơn so với `HashSet<string>`.

**Gợi ý:** trie thắng khi tiền tố chung được tái sử dụng nhiều; ít chia sẻ thì trie chỉ tốn thêm node.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi giải thích được trie lưu chuỗi bằng cạnh-ký-tự và đường-đi-là-từ.
- [ ] Tôi cài được `Insert`, `Contains`, `StartsWith` và autocomplete.
- [ ] Tôi phân biệt `IsEndOfWord` (từ trọn) với đường đi tồn tại (tiền tố).
- [ ] Tôi lý giải được vì sao thao tác là `O(L)`, độc lập số từ.
- [ ] Tôi biết khi nào trie thắng hash table (truy vấn tiền tố).
- [ ] Tôi ý thức được chi phí bộ nhớ của trie và các biến thể tiết kiệm.

Điều hướng:

- Bài prerequisite: [Tree và binary search tree](./07-tree-va-binary-search-tree.md)
- Ôn lại nền tảng: [Hash table và hash function](./06-hash-table-va-hash-function.md), [Chuỗi ký tự](../01-nen-tang-lap-trinh/13-chuoi-ky-tu.md)
- Bài tiếp theo: [Graph và cách biểu diễn](./10-graph-va-cach-bieu-dien.md)
