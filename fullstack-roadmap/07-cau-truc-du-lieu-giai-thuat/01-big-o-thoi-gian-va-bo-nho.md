# Big-O: thời gian và bộ nhớ

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- Big-O mô tả chặn trên tốc độ tăng công việc khi input tăng.
- Dùng để so scaling theo n và mô hình chi phí đã nêu.
- Không phải số milliseconds; O(1) theo số key vẫn có thể đọc toàn key dài.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích Big-O dùng để mô tả tốc độ tăng của chi phí khi input lớn dần, không phải để đo số mili-giây cụ thể;
- phân biệt (O(1)), (O(log n)), (O(n)), (O(n log n)), (O(n^2));
- phân tích time complexity của vòng lặp, vòng lặp lồng nhau và các thao tác collection quen thuộc;
- phân biệt worst case, average case và best case khi điều đó có ý nghĩa;
- phân biệt time complexity với space complexity;
- nhận ra khi nào một thuật toán có cùng Big-O nhưng vẫn khác nhau đáng kể trong thực tế;
- dùng `Stopwatch` để kiểm chứng xu hướng tăng, nhưng không nhầm benchmark nhỏ với bằng chứng tuyệt đối.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Tìm tên trên từng dòng sổ cần đọc thêm khi sổ dày. Một bảng tra xây sẵn đổi thêm bộ nhớ và công chuẩn bị để giảm lượng đọc mỗi lần. Hãy đếm việc trước khi nhìn đồng hồ.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| input size | kích thước bài toán được chọn | n phần tử |
| time complexity | cách lượng công việc tăng | linear n, pairs n² |
| auxiliary space | bộ nhớ thêm ngoài input | HashSet index |
| amortized | chi phí chia đều trên chuỗi thao tác | List.Add qua nhiều resize |

### Ví dụ nhỏ — tính tay trước

Với n = 4, tìm tuyến tính một giá trị không có cần 4 lần so sánh; xét mọi cặp có thứ tự cần 16 lượt. Với n = 8, hai con số là 8 và 64. Input tăng gấp đôi có thể làm công việc tăng gấp đôi hoặc gấp bốn.

Một hệ thống cần kiểm tra một mã sản phẩm có tồn tại trong kho hay không.

Cách thứ nhất dùng `List<string>`:

```csharp
bool exists = productCodes.Contains(target);
```

Cách thứ hai dùng `HashSet<string>`:

```csharp
bool exists = productCodeSet.Contains(target);
```

Hai dòng code gần như giống nhau. Với 10 phần tử, người dùng khó nhận ra khác biệt. Với hàng triệu phần tử và hàng nghìn lần tra cứu, lựa chọn cấu trúc dữ liệu bắt đầu ảnh hưởng trực tiếp tới latency và chi phí CPU.

Câu hỏi quan trọng không phải chỉ là:

> Đoạn code này mất bao nhiêu mili-giây trên máy của tôi?

Mà còn là:

> Khi số phần tử tăng gấp 10 lần, lượng công việc tăng như thế nào?

Big-O cung cấp ngôn ngữ để trả lời câu hỏi thứ hai.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project:

```bash
mkdir BigODemo
cd BigODemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `BigODemo.csproj` bằng:

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

Thay toàn bộ `Program.cs`:

```csharp
using System.Diagnostics;

namespace BigODemo;

internal static class Program
{
    private static void Main()
    {
        int[] sizes = [1_000, 10_000, 100_000];

        foreach (int size in sizes)
        {
            int[] values = Enumerable.Range(0, size).ToArray();
            int missingValue = -1;

            long linearOperations = LinearSearch(values, missingValue);
            long pairOperations = EstimateOrderedPairOperations(size);

            Console.WriteLine(
                $"n={size:N0}: linear={linearOperations:N0}, pairs={pairOperations:N0}");
        }

        Console.WriteLine();
        CompareLookupStructures(50_000, 200);
    }

    private static long LinearSearch(int[] values, int target)
    {
        long operations = 0;

        foreach (int value in values)
        {
            operations++;

            if (value == target)
            {
                break;
            }
        }

        return operations;
    }

    private static long EstimateOrderedPairOperations(int count)
    {
        // Một cặp vòng lặp n x n sẽ thực hiện n² lượt.
        // Ta tính số lượt bằng công thức để demo không cố chạy
        // hàng tỷ vòng lặp trên input lớn.
        return checked((long)count * count);
    }

    private static void CompareLookupStructures(int itemCount, int lookupCount)
    {
        string[] codes = Enumerable.Range(0, itemCount)
            .Select(i => $"SKU-{i:D8}")
            .ToArray();

        var list = new List<string>(codes);
        var set = new HashSet<string>(codes, StringComparer.Ordinal);

        string missing = "SKU-MISSING";

        TimeSpan listElapsed = Measure(
            () =>
            {
                for (int i = 0; i < lookupCount; i++)
                {
                    _ = list.Contains(missing);
                }
            });

        TimeSpan setElapsed = Measure(
            () =>
            {
                for (int i = 0; i < lookupCount; i++)
                {
                    _ = set.Contains(missing);
                }
            });

        Console.WriteLine($"List.Contains : {listElapsed.TotalMilliseconds:N1} ms");
        Console.WriteLine($"HashSet.Contains: {setElapsed.TotalMilliseconds:N1} ms");
        Console.WriteLine("Do not compare these milliseconds across different machines.");
    }

    private static TimeSpan Measure(Action action)
    {
        // Warm-up để giảm ảnh hưởng của JIT cho ví dụ nhỏ này.
        action();

        Stopwatch stopwatch = Stopwatch.StartNew();
        action();
        stopwatch.Stop();

        return stopwatch.Elapsed;
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Ba dòng đầu có tính xác định. Cột `pairs` là số lượt mà một cặp vòng lặp `n × n` sẽ phải thực hiện; sample tính bằng công thức thay vì cố chạy hàng tỷ vòng lặp:

```text
n=1,000: linear=1,000, pairs=1,000,000
n=10,000: linear=10,000, pairs=100,000,000
n=100,000: linear=100,000, pairs=10,000,000,000
```

Hai dòng thời gian ở cuối phụ thuộc máy, runtime, tải hệ thống và nhiều yếu tố khác. Điều cần quan sát là `List.Contains` phải quét tuyến tính trong trường hợp không tìm thấy, còn `HashSet.Contains` thường có chi phí trung bình gần hằng số.

> **Lưu ý:** đây là demo để nhìn xu hướng, không phải benchmark production. Khi cần benchmark nghiêm túc, dùng công cụ chuyên dụng như BenchmarkDotNet ở module hiệu năng.

### Walkthrough — execution / state / cost

1. Main sinh array, LinearSearch đếm đến khi tìm thấy hoặc hết.
2. EstimateOrderedPairOperations tính n² bằng long, không chạy n² loops.
3. CompareLookupStructures dựng List/HashSet trước vùng đo rồi tìm key thiếu 200 lần.
4. Warmup và Stopwatch chạy trong process; memory index O(n), string hash tốn theo độ dài. Số đo một sample không là bằng chứng complexity.

### Mini-check

Tra key dài 10.000 ký tự trong dictionary có 10 phần tử có thể tốn hơn tra key dài 5 ký tự dù cả hai cùng được mô tả là O(1) theo số phần tử không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Big-O bỏ qua hằng số và tập trung vào tốc độ tăng

Giả sử hai thuật toán có số phép toán gần đúng:

```text
A(n) = 3n + 20
B(n) = n²
```

Với input nhỏ, `B` có thể vẫn nhanh vì implementation đơn giản hoặc cache tốt. Nhưng khi `n` lớn, thành phần `n²` tăng nhanh hơn nhiều so với `n`.

Big-O giữ lại thành phần tăng nhanh nhất:

```text
3n + 20   -> O(n)
n² + 5n   -> O(n²)
7          -> O(1)
```

Nó không nói chính xác số instruction CPU, số allocation hay số mili-giây.

### O(1) — chi phí không tăng theo n

Ví dụ truy cập một phần tử mảng theo index:

```csharp
int value = values[500];
```

CPU tính địa chỉ dựa trên base address và offset. Số phần tử của mảng không buộc chương trình quét từ đầu đến index 500.

```text
array base
   |
   v
[0][1][2][3] ... [500] ...
                  ^
                  |
            base + 500 * sizeof(int)
```

### O(n) — tăng tuyến tính

`LinearSearch` trong trường hợp target không tồn tại phải kiểm tra mọi phần tử:

```text
n = 1,000     -> khoảng 1,000 lần kiểm tra
n = 10,000    -> khoảng 10,000 lần
n = 100,000   -> khoảng 100,000 lần
```

Input tăng 10 lần, công việc tăng gần 10 lần.

### O(n²) — vòng lặp lồng nhau không phải lúc nào cũng xấu, nhưng phải hiểu chi phí

`EstimateOrderedPairOperations` chạy vòng ngoài `n` lần. Mỗi lần vòng ngoài lại chạy vòng trong `n` lần:

```text
n * n = n²
```

Input tăng 10 lần, số cặp tăng khoảng 100 lần.

Đây là lý do một thuật toán có vẻ ổn với 1.000 record có thể trở nên không dùng được với 100.000 record.

### O(log n) — mỗi bước loại bỏ một phần lớn input

Binary search trên dữ liệu đã sắp xếp chia vùng tìm kiếm làm đôi sau mỗi bước:

```text
1,024 phần tử
 -> 512
 -> 256
 -> 128
 -> 64
 -> 32
 -> 16
 -> 8
 -> 4
 -> 2
 -> 1
```

Khoảng 10 bước thay vì hơn 1.000 bước.

### O(n log n)

Nhiều thuật toán sort tổng quát hiệu quả có complexity trung bình hoặc worst-case gần `O(n log n)`.

Trực giác:

- có khoảng `log n` tầng chia nhỏ;
- mỗi tầng xử lý tổng cộng khoảng `n` phần tử.

Do đó:

```text
n * log n
```

### Worst case, average case và best case

Linear search:

- best case: phần tử ở vị trí đầu tiên -> `O(1)`;
- worst case: phần tử ở cuối hoặc không tồn tại -> `O(n)`;
- average case: thường vẫn tỷ lệ với `n` -> `O(n)`.

Khi nói complexity mà không ghi rõ, tài liệu và phỏng vấn thường quan tâm worst case hoặc complexity điển hình nhất của thao tác. Đừng đoán; hãy nói rõ trường hợp bạn đang phân tích.

### Time complexity và space complexity là hai trục khác nhau

Một thuật toán có thể chạy nhanh hơn bằng cách dùng thêm bộ nhớ.

Ví dụ:

```csharp
var seen = new HashSet<int>();
```

Nếu dùng `HashSet` để phát hiện phần tử lặp:

- thời gian có thể từ cách so sánh mọi cặp `O(n²)` giảm về trung bình `O(n)`;
- nhưng phải dùng thêm `O(n)` memory để lưu các phần tử đã thấy.

Đây là trade-off phổ biến trong phần mềm thật: CPU, memory, network, storage và độ phức tạp triển khai thường đổi chỗ cho nhau.

### Cùng Big-O không có nghĩa là cùng hiệu năng

Hai thuật toán đều `O(n)` có thể khác nhau vì:

- một thuật toán cấp phát object trong mỗi vòng lặp;
- một thuật toán truy cập memory tuần tự, thuật toán kia nhảy lung tung;
- một thuật toán gọi network/database;
- một thuật toán có constant factor lớn;
- JIT, branch prediction, cache CPU và vectorization khác nhau.

Big-O là bước đầu của phân tích, không thay thế profiling.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| linear scan | không index, đọc lần lượt | O(n), đủ query hiếm/dữ liệu nhỏ |
| hash index | đổi memory/build lấy lookup | average O(1) theo n, worstO(n) |
| benchmark | đo workload trên máy cụ thể | bao gồm constant/noise; không thay chứng minh |

### Misconception check

**Đúng hay sai?** O(n) là đúng n instruction.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: là upper-bound tăng trưởng, bỏ hằng số; thường cần nêu bound chặt và case.

</details>

**Đúng hay sai?** Amortized và average-case là một.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: amortized xét tổng chuỗi operation, không cần phân phối xác suất input.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** đếm operation.

- **Working Developer — dùng khi làm việc:** nhiều kích thước input và memory.

- **Deep Dive — có thể quay lại sau:** profiling/bound chặt theo requirement.

### Quy tắc cộng

Hai đoạn chạy nối tiếp:

```csharp
ScanCustomers(); // O(n)
ScanOrders();    // O(m)
```

Complexity:

```text
O(n + m)
```

Nếu cả hai collection luôn có cùng kích thước `n`, có thể rút thành `O(n)` vì:

```text
O(n + n) = O(2n) = O(n)
```

### Quy tắc nhân

Hai vòng phụ thuộc nhau:

```csharp
foreach (Customer customer in customers)       // n
{
    foreach (Order order in orders)            // m
    {
        ...
    }
}
```

Complexity:

```text
O(n * m)
```

Nếu `n == m`:

```text
O(n²)
```

### Không phải thấy hai vòng lặp là O(n²)

Ví dụ:

```csharp
for (int i = 0; i < n; i++)
{
    ...
}

for (int i = 0; i < n; i++)
{
    ...
}
```

Hai vòng chạy nối tiếp:

```text
n + n = 2n -> O(n)
```

Không phải `O(n²)`.

### Collection phổ biến trong .NET

Bảng dưới là trực giác quan trọng, không phải hợp đồng tuyệt đối cho mọi implementation:

| Thao tác | Cấu trúc | Complexity điển hình |
|---|---|---:|
| đọc theo index | `T[]`, `List<T>` | `O(1)` |
| tìm theo value | `List<T>` | `O(n)` |
| thêm cuối | `List<T>` | amortized `O(1)` |
| insert đầu | `List<T>` | `O(n)` |
| lookup key | `Dictionary<TKey,TValue>` | average `O(1)` |
| membership | `HashSet<T>` | average `O(1)` |
| sort | `Array.Sort`, `List<T>.Sort` | khoảng `O(n log n)` |

Từ khóa **amortized** nghĩa là một thao tác đơn lẻ đôi lúc đắt hơn, nhưng tính trên một chuỗi thao tác dài thì chi phí trung bình vẫn đạt mức đã nêu. Bài về dynamic array sẽ giải thích trường hợp `List<T>.Add`.

### Big-O và database

Khi làm web, bạn hiếm khi tự viết binary tree, nhưng Big-O vẫn xuất hiện:

- quét bảng không có index;
- lookup bằng index;
- sort hàng triệu row;
- nested-loop join;
- phân trang;
- N+1 query;
- tìm kiếm trong collection sau khi load dữ liệu vào RAM.

Vì vậy DSA không tách rời backend. Nó giúp bạn hiểu tại sao một endpoint chậm khi dữ liệu tăng.

## 6. Lỗi thường gặp

### Dùng benchmark nhỏ để kết luận Big-O

Một thuật toán `O(n²)` có thể thắng `O(n log n)` ở input rất nhỏ. Điều đó không thay đổi complexity của nó.

### Tính mọi vòng lặp lồng nhau thành O(n²)

Nếu vòng trong không phụ thuộc `n`, ví dụ luôn chạy 10 lần:

```csharp
for (int i = 0; i < n; i++)
{
    for (int j = 0; j < 10; j++)
    {
        ...
    }
}
```

Complexity là:

```text
O(10n) -> O(n)
```

### Bỏ qua kích thước input khác nhau

```csharp
foreach (Customer customer in customers) // n
{
    foreach (Role role in roles)         // r
    {
        ...
    }
}
```

Đúng hơn là `O(n * r)`, không nên tự động gọi `O(n²)` nếu `customers` và `roles` là hai tập có kích thước độc lập.

### Tuyên bố HashSet luôn O(1)

Hash-based collection thường có average lookup gần `O(1)`, nhưng collision, resize và chất lượng hash function ảnh hưởng hành vi thực tế. Nói rõ đây là **average-case**.

### Tối ưu complexity khi chưa có vấn đề

Đổi code rõ ràng thành cấu trúc phức tạp để tiết kiệm vài microsecond ở đoạn không nóng có thể làm code khó bảo trì hơn. Thứ tự hợp lý:

```text
correctness
  -> đo
  -> xác định bottleneck
  -> chọn cấu trúc/thuật toán tốt hơn
  -> đo lại
```

### Chỉ nhìn CPU mà quên I/O

Một vòng `O(n)` gọi database `n` lần thường tệ hơn nhiều so với một vòng `O(n²)` nhỏ chạy hoàn toàn trong RAM. Complexity phải được đặt trong mô hình chi phí thực tế.

## 7. Khi nào KHÔNG dùng

Không đổi code nhỏ rõ ràng chỉ để có ký hiệu Big-O đẹp. Không so milliseconds khác máy hoặc Debug/Release rồi kết luận thuật toán sai.

## 8. Production notes & scale check

Gate kiểm bộ đếm, tìm ngay phần tử đầu và tìm không thấy; kiểm định dạng số đo nhưng không đặt ngưỡng HashSet phải nhanh hơn bao nhiêu. LINQ Range/Select trong setup chỉ tạo dữ liệu; chưa cần học query provider để hiểu phép đếm.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Phân tích không chạy code

Xác định complexity:

```csharp
for (int i = 0; i < n; i++)
{
    Console.WriteLine(i);
}

for (int j = 0; j < n; j++)
{
    Console.WriteLine(j);
}
```

**Gợi ý:** hai vòng chạy nối tiếp, không lồng nhau.

### Bài 2 — Hai input độc lập

Phân tích:

```csharp
foreach (string username in usernames)
{
    foreach (string bannedWord in bannedWords)
    {
        Check(username, bannedWord);
    }
}
```

Viết complexity bằng hai biến `u` và `b`.

**Gợi ý:** không ép cả hai thành cùng một `n`.

### Bài 3 — Tìm duplicate

Viết hai phiên bản:

1. so sánh từng cặp bằng hai vòng lặp;
2. dùng `HashSet<int>`.

So sánh time và extra space complexity.

**Gợi ý:** phiên bản hash đổi thêm memory để giảm thời gian.

### Bài 4 — Growth table

Tạo bảng số phép toán ước lượng cho:

```text
O(1)
O(log2 n)
O(n)
O(n log2 n)
O(n²)
```

với `n = 10, 100, 1_000, 1_000_000`.

**Gợi ý:** bạn không cần chạy code; dùng calculator cũng được. Mục tiêu là nhìn tốc độ tăng.

### Bài 5 — Code review backend

Giả sử endpoint đã load `100_000` product vào `List<Product>`, sau đó với mỗi order item lại gọi:

```csharp
products.First(p => p.Id == item.ProductId);
```

Phân tích complexity nếu có `m` order item và `n` product. Đề xuất cấu trúc dữ liệu khác.

**Gợi ý:** xây `Dictionary<int, Product>` một lần rồi lookup theo key.

## 10. Bài tập tích hợp liên module — Judgment

Từ phép đo allocation ở Module 05, tách chi phí dựng index khỏi chi phí tìm kiếm. So một lần tìm với 10.000 lần tìm; nêu dữ liệu đầu vào, chi phí CPU/bộ nhớ và khi nào index đáng giá.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Big-O chặn cái gì?
2. Worst và amortized khác nhau thế nào?
3. Chi phí dựng index được trả khi nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi giải thích được Big-O mô tả tốc độ tăng, không phải số mili-giây.
- [ ] Tôi phân biệt được `O(1)`, `O(log n)`, `O(n)`, `O(n log n)`, `O(n²)`.
- [ ] Tôi áp dụng được quy tắc cộng và quy tắc nhân.
- [ ] Tôi không tự động gọi mọi vòng lặp lồng nhau là `O(n²)`.
- [ ] Tôi phân biệt time complexity với space complexity.
- [ ] Tôi hiểu `HashSet.Contains` thường là average `O(1)`, không phải bảo đảm tuyệt đối.
- [ ] Tôi biết Big-O không thay thế benchmark và profiling.
- [ ] Tôi liên hệ được complexity với collection và backend/database.

Điều hướng:

- Prerequisite: [Module 04 — Collection: List, Dictionary, HashSet, Queue, Stack](../04-csharp-co-ban/13-collection-list-dictionary-hashset-queue-stack.md)
- Ôn lại đo hiệu năng: [Module 05 — Đo lường và tối ưu hiệu năng](../05-csharp-nang-cao/18-do-luong-va-toi-uu-hieu-nang.md)
- Bài tiếp theo: [Đệ quy và call stack](./02-de-quy-va-call-stack.md)
