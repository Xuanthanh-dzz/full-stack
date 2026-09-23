# Trie

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- Trie chia sẻ đường ký tự chung để tìm prefix.
- Dùng khi prefix query lặp lại là operation chính.
- Nhiều node/dictionary và string copy có thể tốn memory lớn.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích trie lưu chuỗi theo prefix;
- cài insert, contains và prefix search;
- phân tích complexity theo độ dài key thay vì số lượng key;
- hiểu trade-off giữa tốc độ prefix lookup và memory;
- áp dụng trie cho autocomplete, dictionary và routing theo prefix;
- phân biệt trie với hash table.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Các từ product/program cùng đi qua cổng p,r,o rồi rẽ. Đi tới cổng pro giúp bỏ toàn bộ từ order mà không đọc từng từ, nhưng vẫn phải đi tiếp để thu kết quả.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| prefix | đoạn đầu chuỗi | pro |
| terminal marker | đánh dấu đường là từ hoàn chỉnh | IsWord |
| alphabet | tập đơn vị ký tự làm cạnh | char UTF-16 |
| normalization | quy tắc đưa chuỗi về dạng so sánh | Trim/ToLowerInvariant |

### Ví dụ nhỏ — tính tay trước

Add product: Contains prod=false nhưng prefix prod trả product. Add prod rồi marker tại node đó true; prefix prod trả prod trước product.

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

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```bash
mkdir TrieDemo
cd TrieDemo
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

### Walkthrough — execution / state / cost

1. Add normalize rồi tạo node còn thiếu theo từng char.
2. Contains tìm path và còn kiểm IsWord, không chỉ node tồn tại.
3. FindByPrefix tới node bắt đầu rồi Collect theo child key tăng dần đến limit.
4. Lookup average O(L); Collect còn sort child và nối string mỗi cạnh. Memory nodes/dictionaries theo tổng prefix khác nhau, recursion depth theo độ dài từ.

### Mini-check

Normalize cùng viết thường có làm hai cách viết Unicode composed/decomposed tự bằng nhau không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| HashSet string | exact lookup | hash đọc key, prefix phải scan |
| Trie | chia sẻ prefix và subtree | thêm nhiều object, hợp autocomplete |
| sorted strings | binary range prefix | ít node overhead, update cần cân nhắc |

### Misconception check

**Đúng hay sai?** Giới hạn 10 kết quả bảo đảm chỉ thăm 10 node.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: có thể đi sâu nhiều node mới gặp một từ.

</details>

**Đúng hay sai?** char là một ký tự người dùng nhìn thấy.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: một đơn vị mã UTF-16 khác một Unicode scalar hoặc một ký tự người dùng nhìn thấy.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** path và marker.

- **Working Developer — dùng khi làm việc:** normalization/output cost.

- **Deep Dive — có thể quay lại sau:** compressed trie khi có driver.

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

lưu từng code unit UTF-16. Một Unicode scalar ngoài BMP có hai char; sample chưa chuẩn hóa Unicode composed/decomposed và không sắp theo ngôn ngữ người dùng.

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

## 7. Khi nào KHÔNG dùng

Không dựng trie cho lookup exact nhỏ khi HashSet đủ. Không dùng recursion Collect cho từ dài không kiểm soát hoặc trả mọi kết quả không có budget.

## 8. Production notes & scale check

Gate normalization, duplicate, prefix-only marker, limit, missing và thứ tự ordinal char. Prefix rỗng bị từ chối theo contract hiện tại. Chưa làm accent-insensitive, ranking theo frequency hay Unicode normalization; không gọi limit là giới hạn tổng memory.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Từ string/rune ở Module 04 và phép đo allocation ở Module 05, chỉ ra chi phí nối `current + ch` trên một nhánh dài. Chọn duyệt 100 từ hay dựng trie cho 100.000 lần tìm dựa trên cách sử dụng thực tế.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. IsWord giữ thông tin gì?
2. Chi phí tìm prefix khác thu output ra sao?
3. Policy prefix rỗng là gì?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi mô tả được trie theo prefix.
- [ ] Tôi hiểu cần marker `IsWord`.
- [ ] Tôi cài được Add/Contains/FindByPrefix.
- [ ] Tôi phân tích lookup theo độ dài key.
- [ ] Tôi biết trie đổi thêm memory để prefix query nhanh.
- [ ] Tôi phân biệt use case trie và hash table.

Điều hướng:

- Bài trước: [Heap và priority queue](./08-heap-va-priority-queue.md)
- Bài tiếp theo: [Graph và cách biểu diễn](./10-graph-va-cach-bieu-dien.md)
