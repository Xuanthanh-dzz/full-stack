# Hash table và hash function

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích vì sao hash table cho tra cứu `O(1)` **trung bình** — điều `List<T>` không làm được;
- mô tả vai trò của **hash function**: biến khóa thành chỉ số bucket;
- xử lý **đụng độ (collision)** bằng chaining và biết open addressing là gì;
- hiểu **load factor** và vì sao hash table phải resize;
- nêu vì sao trường hợp xấu nhất của hash table là `O(n)`;
- tôn trọng hợp đồng `GetHashCode`/`Equals` khi dùng type tự định nghĩa làm khóa.

## 2. Bài toán mở đầu

Ở bài [01](./01-big-o-thoi-gian-va-bo-nho.md) ta thấy: kiểm tra một giá trị có trong `List<T>` là `O(n)` (phải quét), còn `HashSet<T>`/`Dictionary<K,V>` làm việc đó ở `O(1)` trung bình. Lúc đó ta chấp nhận điều này như một sự thật. Bài này trả lời câu hỏi *bằng cách nào*.

Ý tưởng cốt lõi đơn giản đến bất ngờ: thay vì đi tìm khóa, hãy **tính thẳng ra chỗ chứa nó**. Nếu một hàm biến khóa `"buoi"` thành một chỉ số mảng, ta nhảy tới đúng ô đó ngay — không quét. Hàm đó là **hash function**, mảng đó là **bảng bucket**. Toàn bộ nghệ thuật nằm ở chỗ: tính nhanh, phân bố đều, và xử lý khi hai khóa khác nhau lỡ tính ra cùng một ô. Ta sẽ dựng một hash table để thấy cả ba.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `HashTableDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace HashTableDemo;

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine("== Hash function: khóa -> chỉ số bucket ==");
        var table = new SimpleHashTable<int>(capacity: 4);
        string[] keys = { "cam", "quyt", "buoi", "chanh", "tao" };
        foreach (string k in keys)
        {
            int bucket = SimpleHashTable<int>.BucketOf(k, 4);
            Console.WriteLine($"  hash(\"{k}\") % 4 = bucket {bucket}");
        }

        Console.WriteLine();
        Console.WriteLine("== Thêm vào bảng và xử lý đụng độ bằng chaining ==");
        for (int i = 0; i < keys.Length; i++)
        {
            table.Put(keys[i], i + 1); // giá trị = số thứ tự cho dễ theo dõi
        }
        table.PrintBuckets();

        Console.WriteLine();
        Console.WriteLine("== Tra cứu vẫn đúng dù có đụng độ ==");
        foreach (string k in new[] { "buoi", "tao", "xoai" })
        {
            bool found = table.TryGet(k, out int value);
            Console.WriteLine($"  Get(\"{k}\") -> {(found ? value.ToString() : "không có")}");
        }

        Console.WriteLine();
        Console.WriteLine($"Số phần tử: {table.Count}, số bucket: 4");
        Console.WriteLine($"Load factor = {table.Count / 4.0:0.00} (trung bình mỗi bucket)");
    }
}

internal sealed class SimpleHashTable<TValue>
{
    // Mỗi bucket là một danh sách các cặp (key, value) — đây là "chaining".
    private readonly List<(string Key, TValue Value)>[] _buckets;

    public int Count { get; private set; }

    public SimpleHashTable(int capacity)
    {
        _buckets = new List<(string, TValue)>[capacity];
        for (int i = 0; i < capacity; i++)
        {
            _buckets[i] = new List<(string, TValue)>();
        }
    }

    // Hàm băm tự viết, tất định (khác string.GetHashCode() vốn ngẫu nhiên mỗi tiến trình).
    public static int BucketOf(string key, int capacity)
    {
        int hash = 0;
        foreach (char c in key)
        {
            hash = hash * 31 + c; // polynomial rolling hash, cơ số 31
        }
        // & int.MaxValue để bỏ dấu âm do tràn số, rồi lấy dư theo số bucket.
        return (hash & int.MaxValue) % capacity;
    }

    public void Put(string key, TValue value)
    {
        var bucket = _buckets[BucketOf(key, _buckets.Length)];
        for (int i = 0; i < bucket.Count; i++)
        {
            if (bucket[i].Key == key)
            {
                bucket[i] = (key, value); // đã có -> cập nhật
                return;
            }
        }
        bucket.Add((key, value)); // chưa có -> thêm vào cuối chuỗi
        Count++;
    }

    public bool TryGet(string key, out TValue value)
    {
        var bucket = _buckets[BucketOf(key, _buckets.Length)];
        foreach (var entry in bucket)
        {
            if (entry.Key == key)
            {
                value = entry.Value;
                return true;
            }
        }
        value = default!;
        return false;
    }

    public void PrintBuckets()
    {
        for (int i = 0; i < _buckets.Length; i++)
        {
            string content = _buckets[i].Count == 0
                ? "(trống)"
                : string.Join(" -> ", _buckets[i].Select(e => $"{e.Key}={e.Value}"));
            Console.WriteLine($"  bucket {i}: {content}");
        }
    }
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
== Hash function: khóa -> chỉ số bucket ==
  hash("cam") % 4 = bucket 3
  hash("quyt") % 4 = bucket 3
  hash("buoi") % 4 = bucket 1
  hash("chanh") % 4 = bucket 2
  hash("tao") % 4 = bucket 2

== Thêm vào bảng và xử lý đụng độ bằng chaining ==
  bucket 0: (trống)
  bucket 1: buoi=3
  bucket 2: chanh=4 -> tao=5
  bucket 3: cam=1 -> quyt=2

== Tra cứu vẫn đúng dù có đụng độ ==
  Get("buoi") -> 3
  Get("tao") -> 5
  Get("xoai") -> không có

Số phần tử: 5, số bucket: 4
Load factor = 1.25 (trung bình mỗi bucket)
```

## 4. Giải thích cơ chế

### 4.1 Hash function biến khóa thành chỉ số

`BucketOf` gộp các ký tự của khóa thành một số nguyên (polynomial rolling hash, `hash = hash*31 + c`), rồi lấy dư theo số bucket để ra chỉ số trong `[0, capacity)`. Nhờ vậy, từ `"buoi"` ta tính thẳng ra **bucket 1** và nhảy tới đó — không dò tìm.

Một hash function tốt cần: **nhanh** (tính trong `O(độ dài khóa)`), **tất định** (cùng khóa luôn ra cùng chỉ số), và **phân bố đều** (rải khóa ra khắp các bucket). Cơ số 31 (số nguyên tố) là lựa chọn kinh điển giúp trộn các ký tự để hai chuỗi gần giống nhau vẫn cho hash khác nhau.

### 4.2 Đụng độ là không tránh khỏi

Output cho thấy `"cam"` và `"quyt"` cùng ra **bucket 3**; `"chanh"` và `"tao"` cùng ra **bucket 2**. Đó là **collision** — hai khóa khác nhau băm về cùng ô. Với 4 bucket mà 5 khóa, theo nguyên lý chuồng bồ câu (pigeonhole) chắc chắn có ít nhất một bucket chứa từ hai khóa trở lên. Ngay cả với bảng lớn, collision vẫn xảy ra vì không gian khóa lớn hơn số bucket.

### 4.3 Chaining: mỗi bucket là một chuỗi

Cách xử lý đụng độ ở đây là **chaining**: mỗi bucket giữ một danh sách các cặp `(key, value)`. Khi hai khóa trùng bucket, chúng cùng nằm trong danh sách đó, nối tiếp nhau:

```text
bucket 3:  [cam=1] -> [quyt=2]
```

Khi `Put`, ta băm ra bucket rồi duyệt danh sách nhỏ đó: nếu khóa đã có thì cập nhật, chưa có thì thêm vào cuối. Khi `TryGet("quyt")`, ta băm ra bucket 3, rồi so `"cam"` (không khớp) và `"quyt"` (khớp) — trả `2`. Việc so khớp cuối cùng dùng `==` trên khóa, nên dù đụng độ, kết quả vẫn **đúng**.

### 4.4 Vì sao trung bình là `O(1)`, xấu nhất là `O(n)`

- **Trung bình `O(1)`:** nếu hash phân bố đều và số phần tử xấp xỉ số bucket, mỗi bucket chỉ chứa vài phần tử. Băm ra bucket là `O(1)`, duyệt chuỗi ngắn cũng gần như `O(1)`. Đó là lý do `Dictionary`/`HashSet` nhanh.
- **Xấu nhất `O(n)`:** nếu hash tồi (mọi khóa về cùng một bucket) hoặc bị cố ý tấn công, một bucket chứa cả `n` phần tử, và tra cứu suy biến thành quét tuyến tính một linked list — `O(n)`. Đây là "trường hợp xấu" mà bài [01](./01-big-o-thoi-gian-va-bo-nho.md) đã nhắc.

### Đào sâu (có thể quay lại sau)

- **Load factor và resize.** Load factor = số phần tử / số bucket (ở đây `1.25`). Khi nó vượt một ngưỡng (thường ~0,7–1,0), bảng **cấp thêm bucket** (thường gấp đôi) và băm lại toàn bộ khóa vào bảng mới — thao tác `O(n)` nhưng hiếm, nên trung bình `Put` vẫn amortized `O(1)`. Resize giữ các chuỗi ngắn để tra cứu ở lại `O(1)`.
- **Open addressing.** Cách xử lý đụng độ khác chaining: không dùng danh sách phụ, mà khi bucket bận thì **dò sang ô kế tiếp** (linear/quadratic probing) cho tới khi thấy ô trống. Tiết kiệm bộ nhớ, thân thiện cache hơn, nhưng phức tạp khi xóa. `Dictionary<K,V>` của .NET dùng một biến thể chaining trên mảng.
- **Hash ngẫu nhiên theo tiến trình.** `string.GetHashCode()` trong .NET **được random hóa mỗi lần chạy** để chống tấn công collision cố ý (hash flooding). Vì thế ta tự viết `BucketOf` cho bài này để output tất định; đừng bao giờ lưu trữ hay dựa vào giá trị `GetHashCode()` giữa các lần chạy.

## 5. Kiến thức nền

### Hợp đồng `GetHashCode` và `Equals`

Khi dùng type tự định nghĩa làm **khóa** của `Dictionary`/`HashSet`, C# gọi `GetHashCode()` để chọn bucket và `Equals()` để so khớp trong bucket. Hai quy tắc bắt buộc:

1. Hai object **bằng nhau** (`Equals` trả `true`) **phải** có cùng `GetHashCode()`. Vi phạm quy tắc này khiến tra cứu "mất" phần tử đã thêm.
2. `GetHashCode()` nên phân bố đều và tính nhanh; và không được đổi khi object đang nằm trong bảng.

`record` (đã học ở [module 05](../05-csharp-nang-cao/07-record-init-required-va-immutability.md)) tự sinh `Equals`/`GetHashCode` theo giá trị các thuộc tính — nên record bất biến là khóa lý tưởng.

### Ba cấu trúc dựa trên hash trong .NET

| Kiểu | Dùng khi |
|---|---|
| `HashSet<T>` | tập hợp không trùng, chỉ cần biết "có/không" |
| `Dictionary<K,V>` | ánh xạ khóa → giá trị |
| `Dictionary<K,V>` với khóa record | khóa phức hợp nhiều trường |

Tất cả đều cho thao tác trung bình `O(1)`. Trong công việc thực tế, **dùng chúng** thay vì tự viết hash table; bài này tự viết chỉ để hiểu bên trong.

### Hash table so với các cấu trúc khác

- Cần tra cứu theo khóa cực nhanh, **không** cần thứ tự → hash table.
- Cần giữ **thứ tự sắp xếp** và tra cứu theo khoảng → cây tìm kiếm (bài [07](./07-tree-va-binary-search-tree.md)), cho `O(log n)` nhưng có thứ tự.
- Cần tra theo chỉ số số nguyên liên tục → mảng, `O(1)` mà không cần băm.

## 6. Lỗi thường gặp

### Ghi đè `Equals` mà quên `GetHashCode` (và ngược lại)

Đây là bug hash kinh điển: hai object "bằng nhau" nhưng khác `GetHashCode` rơi vào hai bucket khác nhau, nên `dictionary` không tìm thấy khóa vừa thêm. Luôn ghi đè **cả hai** cùng nhau, hoặc dùng `record`.

### Dùng object khả biến làm khóa

Nếu sửa một trường ảnh hưởng `GetHashCode` **sau khi** đã đưa object vào bảng, khóa "lạc" sang bucket mới còn bảng vẫn giữ nó ở bucket cũ — không bao giờ tìm lại được. Khóa nên bất biến.

### Lưu hoặc so sánh `GetHashCode()` giữa các lần chạy

Vì `string.GetHashCode()` random theo tiến trình, ghi nó xuống file rồi so ở lần chạy sau sẽ sai. Hash code chỉ dùng trong bộ nhớ, một lần chạy.

### Tưởng hash table luôn `O(1)`

Với hash tồi hoặc load factor quá cao, tra cứu tụt về `O(n)`. Chọn/để cho thư viện lo hàm băm tốt và để bảng tự resize; đừng cố định capacity quá nhỏ cho dữ liệu lớn.

### Trông đợi thứ tự duyệt ổn định

Duyệt `Dictionary`/`HashSet` **không** bảo đảm thứ tự (theo thứ tự thêm, sắp xếp, hay bất cứ gì). Cần thứ tự thì sắp xếp riêng, hoặc dùng cấu trúc có thứ tự.

## 7. Bài tập

### Bài 1 — Thêm `Remove`

Thêm `bool Remove(string key)` vào `SimpleHashTable`: băm ra bucket, tìm và xóa cặp khỏi danh sách, giảm `Count`. Trả `false` nếu không có khóa.

**Gợi ý:** `bucket.RemoveAll(e => e.Key == key)` trả số phần tử bị xóa; dùng nó để biết có xóa được không.

### Bài 2 — Đo phân bố

Băm 1.000 khóa `"key0".."key999"` vào bảng 128 bucket và in số phần tử ở mỗi bucket. Nhận xét mức độ đều.

**Gợi ý:** nếu hàm băm tốt, các bucket có kích thước gần nhau (~8 phần tử); một hàm băm tồi sẽ dồn cục.

### Bài 3 — Hàm băm tồi

Thay `BucketOf` bằng một hàm chỉ trả `key.Length % capacity`. Thêm nhiều khóa cùng độ dài rồi in buckets. Giải thích vì sao tra cứu chậm hẳn.

**Gợi ý:** mọi khóa cùng độ dài dồn về một bucket, biến bảng thành một linked list — `O(n)`.

### Bài 4 — Resize khi load factor cao

Cho bảng tự cấp đôi số bucket và băm lại khi `Count / capacity > 0.75`. Xác nhận các phần tử cũ vẫn tra cứu được sau resize.

**Gợi ý:** tạo mảng bucket mới rồi `Put` lại từng cặp; chỉ số bucket đổi vì `capacity` đổi.

### Bài 5 — Khóa record

Định nghĩa `record Point(int X, int Y)`, dùng `Dictionary<Point, string>` gán tên cho vài điểm. Thử tra bằng một `Point` **mới** có cùng `X, Y` và giải thích vì sao tìm thấy.

**Gợi ý:** record so sánh và băm theo giá trị, nên hai `Point(1,2)` khác object vẫn "bằng nhau" và cùng bucket.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi giải thích được hash function biến khóa thành chỉ số bucket thế nào.
- [ ] Tôi mô tả được collision và cách chaining xử lý nó.
- [ ] Tôi nêu được vì sao tra cứu trung bình `O(1)`, xấu nhất `O(n)`.
- [ ] Tôi hiểu load factor và vì sao bảng phải resize.
- [ ] Tôi tôn trọng hợp đồng `Equals`/`GetHashCode` khi tạo khóa tùy chỉnh.
- [ ] Tôi biết không được lưu/so sánh `GetHashCode()` giữa các lần chạy.

Điều hướng:

- Bài prerequisite: [Stack, queue và deque](./05-stack-queue-va-deque.md)
- Ôn lại nền tảng: [Collection: List, Dictionary, HashSet, Queue và Stack](../04-csharp-co-ban/13-collection-list-dictionary-hashset-queue-stack.md), [Record, `init`, `required` và tính bất biến](../05-csharp-nang-cao/07-record-init-required-va-immutability.md)
- Bài tiếp theo: [Tree và binary search tree](./07-tree-va-binary-search-tree.md)
