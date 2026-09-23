# Hash table và hash function

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- Hash table dùng hash chọn vùng rồi equality quyết định key khớp.
- Dùng Dictionary cho map và HashSet cho membership/uniqueness.
- Collision bình thường; key đổi phần tham gia hash có thể làm lookup hỏng.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích hash table ánh xạ key tới bucket;
- hiểu vai trò của hash function và equality;
- phân tích lookup trung bình `O(1)` và worst case `O(n)`;
- giải thích collision;
- dùng `Dictionary<TKey,TValue>` và `HashSet<T>` đúng cách;
- hiểu vì sao `GetHashCode` phải nhất quán với `Equals`;
- nhận ra rủi ro khi dùng mutable key.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Mã tủ giúp tìm đúng ngăn trước, nhưng trong ngăn vẫn phải xem đúng tên. Hai tên cùng ngăn không phải cùng người; hash chỉ giúp thu hẹp chỗ tìm.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| hash | số tính từ key để chọn vùng | GetHashCode |
| bucket | vùng ứng viên | có thể chứa nhiều key |
| collision | key khác cùng hash/vùng | cần equality tiếp |
| comparer | quy tắc hash và bằng nhau | OrdinalIgnoreCase |

### Ví dụ nhỏ — tính tay trước

Tạo key `Student@Example.com` rồi tìm `student@example.com` sẽ thấy theo quy tắc chuẩn hóa của demo. Hash bằng nhau chưa đủ chứng minh Equals; dictionary vẫn giữ được hai key khác có cùng hash.

Ta có 1.000.000 sản phẩm và cần tìm theo `ProductId`.

Dùng `List<Product>`:

```csharp
Product? product = products.FirstOrDefault(p => p.Id == id);
```

worst case phải scan toàn bộ: `O(n)`.

Dùng dictionary:

```csharp
Dictionary<int, Product> byId;
```

lookup trung bình gần `O(1)`.

Điểm cốt lõi: hash table dùng hash của key để đi gần như trực tiếp tới vùng chứa phù hợp.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```bash
mkdir HashTableDemo
cd HashTableDemo
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
namespace HashTableDemo;

public sealed record Product(int Id, string Name);

public sealed record EmailAddress
{
    public EmailAddress(string value)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(value);
        Value = value.Trim().ToLowerInvariant();
    }

    public string Value { get; }

    public override string ToString() => Value;
}

internal static class Program
{
    private static void Main()
    {
        var products = new Dictionary<int, Product>
        {
            [101] = new Product(101, "Keyboard"),
            [102] = new Product(102, "Mouse"),
            [103] = new Product(103, "Monitor")
        };

        if (products.TryGetValue(102, out Product? product))
        {
            Console.WriteLine(product);
        }

        var emails = new HashSet<EmailAddress>
        {
            new("Student@Example.com")
        };

        Console.WriteLine(
            emails.Contains(new EmailAddress("student@example.com")));

        var counts = CountWords(
            "dotnet csharp dotnet api csharp dotnet");

        foreach ((string word, int count) in counts.OrderBy(x => x.Key))
        {
            Console.WriteLine($"{word} = {count}");
        }
    }

    private static Dictionary<string, int> CountWords(string text)
    {
        var counts = new Dictionary<string, int>(
            StringComparer.OrdinalIgnoreCase);

        foreach (string word in text.Split(' ', StringSplitOptions.RemoveEmptyEntries))
        {
            counts[word] = counts.GetValueOrDefault(word) + 1;
        }

        return counts;
    }
}
```

Output:

```text
Product { Id = 102, Name = Mouse }
True
api = 1
csharp = 2
dotnet = 3
```

### Walkthrough — execution / state / cost

1. Main dựng byId và TryGetValue(102) trả reference tới Product.
2. EmailAddress normalize tại constructor, record equality trên Value.
3. CountWords split dấu cách, comparer của dictionary gộp dotnet/ DOTNET khác hoa thường.
4. Tra hash trung bình O(1) theo số key khi phân bố tốt; tính hash chuỗi tốn theo độ dài key. Split tạo các chuỗi; sort k từ để xuất mất O(k log k), không nằm trong chi phí một lookup.

### Mini-check

Equals ignorecase mà hash casesensitive có thể khiến key bằng nhau nằm ở bucket khác ra sao?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Từ key tới bucket

Khái niệm đơn giản:

```text
key
 |
 v
GetHashCode()
 |
 v
hash
 |
 v
bucket index
 |
 v
bucket
```

Ví dụ hash table có 8 bucket:

```text
0: -
1: key A
2: -
3: key B -> key C
4: -
5: key D
6: -
7: -
```

B và C cùng rơi vào bucket 3: đó là collision.

### Collision là bình thường

Không thể bảo đảm mọi key có bucket riêng khi tập key lớn hoặc số bucket hữu hạn.

Implementation phải có chiến lược xử lý collision, ví dụ chaining hoặc probing.

Điều quan trọng:

> Hai key bằng nhau phải có cùng hash.

Nhưng:

> Hai key có cùng hash không nhất thiết bằng nhau.

### Lookup trung bình O(1)

Nếu hash phân bố tốt, bucket nhỏ và load factor được kiểm soát, chương trình chỉ cần:

1. tính hash;
2. tìm bucket;
3. kiểm tra một số ít entry.

Số bước trung bình không tăng tuyến tính với tổng số phần tử.

### Worst case O(n)

Nếu mọi key rơi vào một bucket:

```text
bucket 3:
A -> B -> C -> D -> ... -> n
```

lookup biến thành scan tuyến tính.

Đó là lý do chất lượng hash và chính sách resize quan trọng.

### Equality và hash code

Nếu:

```csharp
a.Equals(b) == true
```

thì bắt buộc:

```csharp
a.GetHashCode() == b.GetHashCode()
```

Nếu vi phạm, dictionary/hashset có thể tìm sai bucket và hành vi logic bị hỏng.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Dictionary | key→value | thêm indexRAMO(n) |
| HashSet | membership | không value map |
| linear scan | so từng item | O(n), ítsetup choinputnhỏ |

### Misconception check

**Đúng hay sai?** Hash bằng nhau suy ra key bằng nhau.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: collision là bình thường.

</details>

**Đúng hay sai?** GetHashCode nên lưu làm ID bền qua process.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: không có cam kết ổn định qua process/runtime.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** hash và equality.

- **Working Developer — dùng khi làm việc:** comparer/normalization.

- **Deep Dive — có thể quay lại sau:** collision workload khi cần.

### Dictionary và HashSet

`Dictionary<TKey,TValue>`:

```text
key -> value
```

Dùng khi cần map.

`HashSet<T>`:

```text
value có tồn tại không?
```

Dùng cho membership/uniqueness.

### String comparer

Đừng tự lower-case ở mọi nơi nếu mục tiêu chỉ là so sánh key không phân biệt hoa thường.

```csharp
new Dictionary<string, User>(StringComparer.OrdinalIgnoreCase)
```

thể hiện policy rõ hơn.

### Mutable key nguy hiểm

Nếu key thay đổi field tham gia hash sau khi đã insert:

```text
insert -> bucket 2
mutate key -> hash mới thuộc bucket 7
lookup -> tìm bucket 7
entry thật vẫn ở bucket 2
```

Kết quả: collection có entry nhưng không tìm lại được đúng cách.

Vì vậy key nên immutable theo các field tham gia equality/hash.

### Resize

Khi hash table quá đầy, implementation thường:

1. allocate bucket array lớn hơn;
2. phân phối lại entry;
3. cập nhật cấu trúc.

Một insert cụ thể có thể đắt, nhưng thao tác trung bình vẫn gần `O(1)`.

## 6. Lỗi thường gặp

### Dùng Dictionary nhưng vẫn scan Values

```csharp
dictionary.Values.First(x => x.Email == email)
```

Đây vẫn là `O(n)`.

Muốn lookup email nhanh, cần index/dictionary theo email.

### Override Equals mà quên GetHashCode

Hai method phải tuân contract cùng nhau.

### Dùng random hash

Hash phải ổn định trong vòng đời key khi nằm trong collection.

### Dùng hash cho security

`GetHashCode` không phải cryptographic hash và không dùng để lưu password.

Password hashing là chủ đề security khác hoàn toàn.

## 7. Khi nào KHÔNG dùng

Không dùng GetHashCode để lưu password hay IDbền. Không thêm nhiều dictionaryindex nếu workload không cần và không có cách cập nhật nhất quán.

## 8. Production notes & scale check

Email demo là identifier chọn case-insensitive, chưa validate cú pháp email hay tuyên bố mọi địa chỉ email đều cùng quy tắc so sánh. Word tokenizer chỉ tách space, không tự xử lý dấu câu/tab. Gate kiểm key chuẩn hóa bằng nhau tra được cùng entry, input trắng và đếm từ lặp. Failure Lab riêng tái hiện key đổi hash sau khi được thêm.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Word frequency

Đếm tần suất từ trong một đoạn text bằng dictionary.

### Bài 2 — Duplicate detector

Trả về phần tử trùng đầu tiên trong mảng bằng `HashSet<int>`.

Phân tích time/space.

### Bài 3 — Two Sum

Tìm hai số có tổng bằng target bằng dictionary/hashset.

So sánh với hai vòng lặp.

### Bài 4 — Composite key

Tạo value object:

```csharp
record StudentCourseKey(int StudentId, int CourseId);
```

dùng làm key dictionary.

### Bài 5 — Mutable-key experiment

Tạo một class mutable override equality/hash theo một property. Insert vào `HashSet`, sau đó đổi property và thử `Contains`.

Giải thích kết quả.

## 10. Bài tập tích hợp liên module — Judgment

Từ record/equality Module05, field nào phải bất biến khi record làmkey? Với một query trên10items, linear có thể hợp hơn index mới không?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Equality quyết định ở bước nào?
2. AverageO(1) bỏ qua kích thước nào?
3. Mutationkey có di chuyển entry không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi mô tả được key -> hash -> bucket.
- [ ] Tôi hiểu collision là bình thường.
- [ ] Tôi biết lookup average `O(1)`, worst `O(n)`.
- [ ] Tôi hiểu contract giữa `Equals` và `GetHashCode`.
- [ ] Tôi tránh mutable key.
- [ ] Tôi chọn được Dictionary hay HashSet theo use case.

Điều hướng:

- Bài trước: [Stack, queue và deque](./05-stack-queue-va-deque.md)
- Ôn lại Dictionary/HashSet: [Collection trong C#](../04-csharp-co-ban/13-collection-list-dictionary-hashset-queue-stack.md)
- Bài tiếp theo: [Tree và binary search tree](./07-tree-va-binary-search-tree.md)
