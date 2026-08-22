# Big-O về thời gian và bộ nhớ

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích vì sao ta đo thuật toán bằng **tốc độ tăng của số thao tác** thay vì bằng giây đồng hồ;
- đọc và gọi tên các lớp độ phức tạp thường gặp: `O(1)`, `O(log n)`, `O(n)`, `O(n log n)`, `O(n^2)`, `O(2^n)`;
- suy ra độ phức tạp thời gian của một đoạn code từ vòng lặp và lời gọi bên trong;
- phân biệt độ phức tạp **thời gian** và **bộ nhớ (space)**, biết thế nào là in-place;
- chọn giữa duyệt tuyến tính và cấu trúc tra cứu như `HashSet<T>` dựa trên độ phức tạp;
- hiểu ý nghĩa của worst case, average case và vì sao hằng số bị bỏ qua trong Big-O.

## 2. Bài toán mở đầu

Bạn có một danh sách mã đơn hàng và cần trả lời một câu hỏi tưởng như đơn giản: *danh sách này có mã nào bị trùng không?*

Cách đầu tiên ai cũng nghĩ ra: so từng mã với mọi mã còn lại. Với 7 phần tử thì nhanh. Nhưng khi danh sách lên 100.000 mã, cách so từng cặp phải thực hiện khoảng **5 tỉ** phép so sánh, còn cách dùng một `HashSet<T>` (đã học ở [module 04](../04-csharp-co-ban/13-collection-list-dictionary-hashset-queue-stack.md)) chỉ cần duyệt qua mỗi mã đúng một lần.

Nếu chỉ đo bằng đồng hồ trên máy của mình, kết quả phụ thuộc CPU, tải hệ thống, cách JIT tối ưu — chạy lại lần khác đã ra số khác. Ta cần một cách mô tả *bản chất* của thuật toán, không phụ thuộc máy: khi dữ liệu lớn gấp đôi thì công việc tăng bao nhiêu lần? Đó chính là Big-O.

## 3. Lời giải bằng code

Tạo project .NET 9:

```bash
dotnet new console --name BigODemo --framework net9.0 --use-program-main
cd BigODemo
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

Thay `Program.cs` bằng:

```csharp
namespace BigODemo;

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine("== Số phép tính cơ bản khi n tăng ==");
        Console.WriteLine($"{"n",6} | {"O(1)",6} | {"O(log n)",9} | {"O(n)",7} | {"O(n log n)",11} | {"O(n^2)",9}");
        Console.WriteLine(new string('-', 62));
        foreach (int n in new[] { 8, 16, 32, 64, 1000 })
        {
            long constant = CountConstant(n);
            long log = CountLog(n);
            long linear = CountLinear(n);
            long linearithmic = CountLinearithmic(n);
            long quadratic = CountQuadratic(n);
            Console.WriteLine(
                $"{n,6} | {constant,6} | {log,9} | {linear,7} | {linearithmic,11} | {quadratic,9}");
        }

        Console.WriteLine();
        Console.WriteLine("== Tìm phần tử trùng: O(n^2) so với O(n) ==");
        int[] data = { 4, 9, 2, 7, 9, 1, 5 };
        bool dupPairwise = HasDuplicatePairwise(data, out long opsPairwise);
        bool dupHashSet = HasDuplicateHashSet(data, out long opsHashSet);
        Console.WriteLine($"Mảng: [{string.Join(", ", data)}]");
        Console.WriteLine($"Pairwise  -> trùng = {dupPairwise}, số lần so sánh = {opsPairwise}");
        Console.WriteLine($"HashSet   -> trùng = {dupHashSet}, số phần tử đã xét = {opsHashSet}");
    }

    // O(1): luôn 1 thao tác, không phụ thuộc n.
    private static long CountConstant(int n) => 1;

    // O(log n): đếm số lần chia đôi n cho tới 1.
    private static long CountLog(int n)
    {
        long steps = 0;
        while (n > 1)
        {
            n /= 2;
            steps++;
        }
        return steps;
    }

    // O(n): duyệt qua từng phần tử một lần.
    private static long CountLinear(int n) => n;

    // O(n log n): mỗi phần tử làm một vòng chia đôi.
    private static long CountLinearithmic(int n) => (long)n * CountLog(n);

    // O(n^2): xét mọi cặp (i, j) với i < j.
    private static long CountQuadratic(int n) => (long)n * (n - 1) / 2;

    private static bool HasDuplicatePairwise(int[] data, out long ops)
    {
        ops = 0;
        for (int i = 0; i < data.Length; i++)
        {
            for (int j = i + 1; j < data.Length; j++)
            {
                ops++;
                if (data[i] == data[j])
                {
                    return true;
                }
            }
        }
        return false;
    }

    private static bool HasDuplicateHashSet(int[] data, out long ops)
    {
        ops = 0;
        var seen = new HashSet<int>();
        foreach (int value in data)
        {
            ops++;
            if (!seen.Add(value))
            {
                return true;
            }
        }
        return false;
    }
}
```

Build và chạy:

```bash
dotnet build --configuration Release
dotnet run --configuration Release --no-build
```

Kết quả:

```text
== Số phép tính cơ bản khi n tăng ==
     n |   O(1) |  O(log n) |    O(n) |  O(n log n) |    O(n^2)
--------------------------------------------------------------
     8 |      1 |         3 |       8 |          24 |        28
    16 |      1 |         4 |      16 |          64 |       120
    32 |      1 |         5 |      32 |         160 |       496
    64 |      1 |         6 |      64 |         384 |      2016
  1000 |      1 |         9 |    1000 |        9000 |    499500

== Tìm phần tử trùng: O(n^2) so với O(n) ==
Mảng: [4, 9, 2, 7, 9, 1, 5]
Pairwise  -> trùng = True, số lần so sánh = 9
HashSet   -> trùng = True, số phần tử đã xét = 5
```

## 4. Giải thích cơ chế

### 4.1 Đếm thao tác, không đếm giây

Mỗi hàm `Count...` trả về **số thao tác cơ bản** mà thuật toán tương ứng phải làm với đầu vào cỡ `n`. Đây chính là điều Big-O quan tâm. Nhìn cột theo chiều dọc khi `n` đi từ 8 lên 16 (gấp đôi):

- `O(1)` giữ nguyên `1` — không phụ thuộc `n`.
- `O(log n)` chỉ tăng thêm `1` (từ 3 lên 4) — mỗi lần `n` gấp đôi, số lần chia đôi tăng đúng 1.
- `O(n)` gấp đôi (8 → 16).
- `O(n log n)` tăng nhanh hơn gấp đôi một chút (24 → 64).
- `O(n^2)` tăng khoảng **bốn lần** (28 → 120): gấp đôi đầu vào làm công việc gấp bốn.

Sự khác biệt này là toàn bộ lý do ta học Big-O. Ở `n = 1000`, thuật toán `O(n^2)` đã cần gần nửa triệu thao tác, trong khi `O(n)` chỉ cần một nghìn.

### 4.2 Suy ra Big-O từ vòng lặp

Quy tắc thực dụng để đọc độ phức tạp của một đoạn code:

- Một vòng lặp chạy qua `n` phần tử: `O(n)`.
- Vòng lặp lồng trong vòng lặp, mỗi cái chạy `n`: `O(n^2)`. Đây chính là `HasDuplicatePairwise` — hai `for` lồng nhau.
- Mỗi bước cắt đôi phần dữ liệu còn lại: `O(log n)`. Chính là `CountLog`: `n` bị chia 2 mỗi vòng.
- Chạy `n` lần, mỗi lần làm một việc `O(log n)`: nhân lại thành `O(n log n)`.

`HasDuplicateHashSet` chỉ có **một** vòng `foreach` qua `n` phần tử, mỗi bước gọi `seen.Add` — thao tác trung bình `O(1)` của hash set (bài [06](./06-hash-table-va-hash-function.md) sẽ mổ xẻ vì sao). Nên tổng thể là `O(n)`. Với mảng 7 phần tử, pairwise so sánh 9 lần trước khi thấy cặp `9 == 9`, còn hash set chỉ xét 5 phần tử là gặp `9` lần thứ hai.

### 4.3 Bỏ hằng số và số hạng nhỏ

Big-O mô tả **dáng tăng khi `n` lớn**, nên ta bỏ hằng số nhân và các số hạng bậc thấp:

- `5n` và `n` đều là `O(n)` — hằng số `5` không đổi hình dạng đường cong.
- `n^2 + 100n + 500` là `O(n^2)` — khi `n` đủ lớn, `n^2` át hẳn phần còn lại.

Điều này không có nghĩa hằng số vô nghĩa trong thực tế; nó nghĩa là *khi so sánh khả năng mở rộng*, lớp độ phức tạp quan trọng hơn hằng số. Một `O(n)` với hằng số lớn vẫn thắng `O(n^2)` khi `n` đủ lớn.

### 4.4 Độ phức tạp bộ nhớ (space)

Bên cạnh thời gian, ta còn đo **bộ nhớ phụ** thuật toán cần, cũng bằng Big-O:

- `HasDuplicatePairwise` chỉ dùng vài biến đếm — bộ nhớ phụ `O(1)`. Ta gọi nó là **in-place**.
- `HasDuplicateHashSet` phải dựng một `HashSet<int>` có thể chứa tới `n` phần tử — bộ nhớ phụ `O(n)`.

Đây là một đánh đổi kinh điển: bản hash nhanh hơn về thời gian (`O(n)` so với `O(n^2)`) nhưng tốn thêm bộ nhớ (`O(n)` so với `O(1)`). Chọn phương án nào tùy ràng buộc bài toán.

### Đào sâu (có thể quay lại sau)

- **Worst / average / best case.** `HasDuplicateHashSet` có average `O(n)` vì `Add` trung bình `O(1)`. Trường hợp xấu nhất về lý thuyết của hash (mọi khóa đụng độ cùng một bucket) có thể xuống `O(n)` cho một thao tác, nhưng với dữ liệu thực và hàm băm tốt điều đó gần như không xảy ra. Big-O mặc định trong bài này nói về worst case, trừ khi ghi rõ là average.
- **Θ và Ω.** `O` là chặn trên. Còn có `Ω` (chặn dưới) và `Θ` (chặn chặt cả trên lẫn dưới). Trong công việc hằng ngày, người ta hay nói "O(n)" với ngụ ý là chặn chặt; khi cần chính xác mới phân biệt.
- **Amortized.** Một số thao tác thỉnh thoảng tốn nhiều nhưng *trung bình qua nhiều lần* vẫn rẻ — ví dụ thêm phần tử vào dynamic array là amortized `O(1)`. Bài [03](./03-mang-va-dynamic-array.md) sẽ giải thích.

## 5. Kiến thức nền

### Bảng các lớp độ phức tạp thường gặp

Xếp từ tốt tới xấu khi `n` lớn:

| Ký hiệu | Tên | Ví dụ điển hình |
|---|---|---|
| `O(1)` | hằng số | truy cập `array[i]`, `dictionary[key]` |
| `O(log n)` | logarit | tìm nhị phân trên mảng đã sắp xếp |
| `O(n)` | tuyến tính | duyệt qua toàn bộ danh sách một lần |
| `O(n log n)` | tuyến-logarit | các thuật toán sắp xếp tốt (merge, heap) |
| `O(n^2)` | bậc hai | hai vòng lặp lồng nhau trên cùng dữ liệu |
| `O(2^n)` | mũ | duyệt mọi tập con (brute-force tổ hợp) |
| `O(n!)` | giai thừa | duyệt mọi hoán vị |

`O(2^n)` và `O(n!)` tăng quá nhanh: với `n` vài chục đã vượt khả năng tính toán thực tế. Nhận ra một thuật toán rơi vào nhóm này là tín hiệu cần đổi hướng tiếp cận.

### Big-O của các collection đã học

Ghi nhớ nhanh cho những kiểu đã dùng ở module 04:

| Thao tác | `List<T>` (mảng động) | `Dictionary<K,V>` / `HashSet<T>` |
|---|---|---|
| Truy cập theo chỉ số | `O(1)` | không áp dụng |
| Tìm theo giá trị/khóa | `O(n)` | `O(1)` trung bình |
| Thêm vào cuối | `O(1)` amortized | `O(1)` trung bình |
| Chèn/xóa ở giữa | `O(n)` | `O(1)` trung bình theo khóa |

Chính bảng này giải thích bài toán mở đầu: kiểm tra tồn tại trong `List<T>` là `O(n)`, trong `HashSet<T>` là `O(1)` trung bình.

### "n" là gì phải nói rõ

Big-O luôn gắn với *kích thước đầu vào*. Với chuỗi thì `n` thường là số ký tự; với đồ thị (bài [10](./10-graph-va-cach-bieu-dien.md)) có tới hai đại lượng: số đỉnh `V` và số cạnh `E`, nên độ phức tạp viết theo cả hai, ví dụ `O(V + E)`.

## 6. Lỗi thường gặp

### Nhầm "chạy nhanh trên máy tôi" với "thuật toán tốt"

Đo bằng đồng hồ trên một máy, một cỡ dữ liệu nhỏ, rồi kết luận thuật toán nhanh. Khi dữ liệu lớn lên, `O(n^2)` sẽ lộ ra dù ban đầu trông ổn. Hãy suy luận độ phức tạp trước, đo sau.

### Quên rằng tra cứu trong `List<T>` là `O(n)`

`list.Contains(x)` và `list.IndexOf(x)` phải quét tuyến tính. Gọi chúng bên trong một vòng lặp vô tình tạo ra `O(n^2)`. Khi cần tra cứu lặp lại nhiều lần, chuyển sang `HashSet<T>` hoặc `Dictionary<K,V>`.

### Cộng thay vì nhân (và ngược lại)

Hai vòng lặp **nối tiếp** nhau, mỗi cái `O(n)`, là `O(n) + O(n) = O(n)`. Hai vòng lặp **lồng** nhau là `O(n) * O(n) = O(n^2)`. Đọc nhầm quan hệ lồng/nối tiếp dẫn tới ước lượng sai.

### Tưởng bỏ hằng số nghĩa là hằng số không quan trọng

Big-O bỏ hằng số để *so sánh khả năng mở rộng*, không phải để nói `2n` và `n` giống nhau về mặt thời gian tường minh. Khi hai thuật toán cùng lớp `O(n)`, hằng số và chi tiết cài đặt mới là thứ quyết định — và lúc đó phải đo thật.

### Chỉ nhìn thời gian, bỏ quên bộ nhớ

Một giải pháp `O(n)` thời gian nhưng ngốn `O(n)` bộ nhớ phụ có thể không dùng được khi dữ liệu quá lớn so với RAM. Luôn cân nhắc cả hai trục.

## 7. Bài tập

### Bài 1 — Đọc độ phức tạp

Cho ba đoạn code: (a) một vòng `for` từ 0 đến `n`; (b) hai vòng `for` lồng nhau cùng chạy tới `n`; (c) một vòng `while` mỗi bước gán `n = n / 3`. Gọi tên Big-O của từng đoạn.

**Gợi ý:** với (c), hỏi "cần chia cho 3 bao nhiêu lần để về 1?" — cùng họ logarit, chỉ khác cơ số, mà cơ số bị nuốt vào hằng số.

### Bài 2 — Đếm thao tác thực

Thêm bộ đếm `long` vào một hàm tính tổng mọi cặp phần tử của mảng. Chạy với `n = 5, 10, 20` và kiểm chứng số thao tác khớp `n(n-1)/2`.

**Gợi ý:** so với cột `O(n^2)` trong bài; đây chính là công thức số cặp.

### Bài 3 — List so với HashSet

Viết chương trình đọc `n` số, rồi với mỗi số trong một danh sách truy vấn khác, kiểm tra nó có xuất hiện không — làm hai phiên bản: một dùng `List<int>.Contains`, một dùng `HashSet<int>.Contains`. Đếm số phần tử phải xét ở mỗi phiên bản.

**Gợi ý:** đừng đo bằng đồng hồ; hãy đếm thao tác để thấy `O(n*m)` so với `O(m)`.

### Bài 4 — Đổi thời gian lấy bộ nhớ

Cho một mảng, đếm số phần tử xuất hiện đúng một lần. Viết bản `O(n^2)` không dùng bộ nhớ phụ, rồi bản `O(n)` dùng `Dictionary<int,int>` đếm tần suất. Ghi rõ Big-O thời gian và bộ nhớ của mỗi bản.

**Gợi ý:** bản thứ hai đánh đổi `O(n)` bộ nhớ để hạ thời gian từ bậc hai xuống tuyến tính.

### Bài 5 — Nhận diện thuật toán mũ

Viết hàm đệ quy sinh mọi tập con của một tập `n` phần tử và đếm số tập con sinh ra. Giải thích vì sao không thể chạy với `n = 60`.

**Gợi ý:** số tập con là `2^n`; ước lượng `2^60` để thấy con số vượt xa mọi giới hạn thực tế.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi giải thích được vì sao đo bằng số thao tác đáng tin hơn đo bằng giây.
- [ ] Tôi gọi tên được `O(1)`, `O(log n)`, `O(n)`, `O(n log n)`, `O(n^2)`, `O(2^n)`.
- [ ] Tôi suy ra Big-O của một đoạn code từ cấu trúc vòng lặp lồng/nối tiếp.
- [ ] Tôi phân biệt độ phức tạp thời gian và bộ nhớ, biết thế nào là in-place.
- [ ] Tôi biết tra cứu trong `List<T>` là `O(n)` còn trong `HashSet<T>` là `O(1)` trung bình.
- [ ] Tôi build/run được sample trên `net9.0` và giải thích được từng dòng output.

Điều hướng:

- Bài prerequisite: [Module 06, bài 14 — Dự án refactor ứng dụng C#](../06-oop-va-thiet-ke/14-du-an-refactor-ung-dung-csharp.md)
- Ôn lại nền tảng: [Bài toán, thuật toán và pseudocode](../01-nen-tang-lap-trinh/01-bai-toan-thuat-toan-va-pseudocode.md), [Collection: List, Dictionary, HashSet, Queue và Stack](../04-csharp-co-ban/13-collection-list-dictionary-hashset-queue-stack.md)
- Bài tiếp theo: [Đệ quy và call stack](./02-de-quy-va-call-stack.md)
