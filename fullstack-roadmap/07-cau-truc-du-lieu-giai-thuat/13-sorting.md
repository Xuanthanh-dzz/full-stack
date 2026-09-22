# Sorting

## 1. Mục tiêu

Sau bài này, bạn có thể:

- cài đặt insertion sort (`O(n^2)`), merge sort và quicksort (`O(n log n)`);
- giải thích chiến lược **chia để trị** trong merge sort và quicksort;
- phân biệt thuật toán **ổn định (stable)** và không ổn định, **in-place** và không;
- hiểu vì sao quicksort có worst case `O(n^2)` và cách chọn pivot để tránh;
- biết cận dưới `O(n log n)` của sắp xếp dựa trên so sánh;
- dùng `Array.Sort`, `List.Sort`, `OrderBy` đúng cách và biết chúng có ổn định không.

## 2. Bài toán mở đầu

Sắp xếp là thao tác nền của vô số bài toán khác: tìm nhị phân (bài [14](./14-searching.md)) cần dữ liệu đã sắp; gộp nhóm, khử trùng, xếp hạng đều dựa vào sắp xếp trước. Ta đã dùng `OrderBy` và `List.Sort` như hộp đen; bài này mở nó ra.

Câu hỏi trung tâm: **có bao nhiêu cách sắp xếp và chúng khác nhau ra sao?** Cách ngây thơ (như insertion sort) dễ viết nhưng `O(n^2)` — với một triệu phần tử là hàng nghìn tỉ thao tác, bất khả thi. Các thuật toán chia để trị (merge, quick) hạ xuống `O(n log n)`, biến bài toán triệu phần tử thành khả thi. Nhưng chúng đánh đổi bộ nhớ, tính ổn định và độ phức tạp worst case khác nhau. Hiểu những khác biệt này là biết chọn (hoặc tin dùng) đúng công cụ.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `SortingDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace SortingDemo;

internal static class Program
{
    private static void Main()
    {
        int[] sample = { 5, 2, 9, 1, 5, 6, 3, 8 };
        Console.WriteLine($"Mảng gốc: [{string.Join(", ", sample)}]");
        Console.WriteLine();

        Console.WriteLine("== Ba thuật toán, cùng kết quả, khác số phép so sánh ==");
        RunSort("Insertion sort O(n^2)", sample, InsertionSort);
        RunSort("Merge sort   O(n log n)", sample, MergeSort);
        RunSort("Quick sort   O(n log n) tb", sample, QuickSort);

        Console.WriteLine();
        Console.WriteLine("== Số phép so sánh tăng thế nào khi n lớn (đầu vào đảo ngược) ==");
        Console.WriteLine($"{"n",5} | {"insertion",10} | {"merge",8} | {"quick",8}");
        Console.WriteLine(new string('-', 40));
        foreach (int n in new[] { 8, 32, 128, 512 })
        {
            int[] reversed = Enumerable.Range(0, n).Reverse().ToArray();
            long ins = Count(reversed, InsertionSort);
            long mer = Count(reversed, MergeSort);
            long qui = Count(reversed, QuickSort);
            Console.WriteLine($"{n,5} | {ins,10} | {mer,8} | {qui,8}");
        }

        Console.WriteLine();
        Console.WriteLine("== Tính ổn định (stable): giữ thứ tự các phần tử bằng khóa ==");
        var people = new (string Name, int Age)[]
        {
            ("An", 30), ("Bình", 25), ("Cường", 30), ("Dũng", 25)
        };
        Console.WriteLine($"Gốc:   {Format(people)}");
        var stable = people.OrderBy(p => p.Age).ToArray(); // OrderBy là stable
        Console.WriteLine($"OrderBy theo tuổi (stable): {Format(stable)}");
        Console.WriteLine("An trước Cường (cùng 30), Bình trước Dũng (cùng 25) -> thứ tự gốc được giữ");
    }

    private static long _comparisons;

    private static void RunSort(string name, int[] original, Action<int[]> sort)
    {
        int[] copy = (int[])original.Clone();
        _comparisons = 0;
        sort(copy);
        Console.WriteLine($"  {name,-26} -> [{string.Join(", ", copy)}]  ({_comparisons} so sánh)");
    }

    private static long Count(int[] original, Action<int[]> sort)
    {
        int[] copy = (int[])original.Clone();
        _comparisons = 0;
        sort(copy);
        return _comparisons;
    }

    // Insertion sort: chèn từng phần tử vào phần đã sắp phía trước.
    private static void InsertionSort(int[] a)
    {
        for (int i = 1; i < a.Length; i++)
        {
            int key = a[i];
            int j = i - 1;
            while (j >= 0 && Greater(a[j], key))
            {
                a[j + 1] = a[j]; // dịch phần tử lớn sang phải
                j--;
            }
            a[j + 1] = key;
        }
    }

    // Merge sort: chia đôi, sắp mỗi nửa, rồi trộn hai nửa đã sắp.
    private static void MergeSort(int[] a)
    {
        if (a.Length <= 1) return;
        int mid = a.Length / 2;
        int[] left = a[..mid];
        int[] right = a[mid..];
        MergeSort(left);
        MergeSort(right);
        Merge(a, left, right);
    }

    private static void Merge(int[] a, int[] left, int[] right)
    {
        int i = 0, j = 0, k = 0;
        while (i < left.Length && j < right.Length)
        {
            if (!Greater(left[i], right[j])) // left[i] <= right[j] -> lấy left (giữ ổn định)
            {
                a[k++] = left[i++];
            }
            else
            {
                a[k++] = right[j++];
            }
        }
        while (i < left.Length) a[k++] = left[i++];
        while (j < right.Length) a[k++] = right[j++];
    }

    // Quick sort: chọn pivot, phân hoạch, đệ quy hai phía.
    private static void QuickSort(int[] a) => QuickSort(a, 0, a.Length - 1);

    private static void QuickSort(int[] a, int lo, int hi)
    {
        if (lo >= hi) return;
        int p = Partition(a, lo, hi);
        QuickSort(a, lo, p - 1);
        QuickSort(a, p + 1, hi);
    }

    private static int Partition(int[] a, int lo, int hi)
    {
        int pivot = a[hi]; // Lomuto: pivot là phần tử cuối
        int i = lo - 1;
        for (int j = lo; j < hi; j++)
        {
            if (!Greater(a[j], pivot)) // a[j] <= pivot
            {
                i++;
                (a[i], a[j]) = (a[j], a[i]);
            }
        }
        (a[i + 1], a[hi]) = (a[hi], a[i + 1]);
        return i + 1;
    }

    private static bool Greater(int x, int y)
    {
        _comparisons++;
        return x > y;
    }

    private static string Format((string Name, int Age)[] items) =>
        "[" + string.Join(", ", items.Select(p => $"{p.Name}/{p.Age}")) + "]";
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
Mảng gốc: [5, 2, 9, 1, 5, 6, 3, 8]

== Ba thuật toán, cùng kết quả, khác số phép so sánh ==
  Insertion sort O(n^2)      -> [1, 2, 3, 5, 5, 6, 8, 9]  (16 so sánh)
  Merge sort   O(n log n)    -> [1, 2, 3, 5, 5, 6, 8, 9]  (17 so sánh)
  Quick sort   O(n log n) tb -> [1, 2, 3, 5, 5, 6, 8, 9]  (15 so sánh)

== Số phép so sánh tăng thế nào khi n lớn (đầu vào đảo ngược) ==
    n |  insertion |    merge |    quick
----------------------------------------
    8 |         28 |       12 |       28
   32 |        496 |       80 |      496
  128 |       8128 |      448 |     8128
  512 |     130816 |     2304 |   130816

== Tính ổn định (stable): giữ thứ tự các phần tử bằng khóa ==
Gốc:   [An/30, Bình/25, Cường/30, Dũng/25]
OrderBy theo tuổi (stable): [Bình/25, Dũng/25, An/30, Cường/30]
An trước Cường (cùng 30), Bình trước Dũng (cùng 25) -> thứ tự gốc được giữ
```

## 4. Giải thích cơ chế

### 4.1 Với n nhỏ, khác biệt chưa lộ

Ở mảng 8 phần tử ngẫu nhiên, cả ba cho **cùng** kết quả và số so sánh xấp xỉ nhau (16, 17, 15) — thậm chí insertion còn ít hơn merge. Đây là bài học quan trọng từ bài [01](./01-big-o-thoi-gian-va-bo-nho.md): Big-O nói về **dáng tăng khi n lớn**, không phải hằng số ở n nhỏ. Với dữ liệu bé, thuật toán đơn giản có thể thắng vì ít chi phí phụ. Phải nhìn bảng thứ hai mới thấy sự thật.

### 4.2 Với n lớn, `O(n^2)` bùng nổ

Bảng đầu vào đảo ngược nói rõ tất cả. Khi `n` gấp 4 (từ 128 lên 512):

- **insertion** tăng ~16 lần (8128 → 130816) — đúng dáng `O(n^2)`.
- **merge** tăng ~5 lần (448 → 2304) — dáng `O(n log n)`.

Ở `n = 512`, insertion cần **130.816** so sánh còn merge chỉ **2.304** — chênh gần 57 lần, và khoảng cách này càng nới rộng khi `n` lớn thêm. Đó là lý do không ai dùng `O(n^2)` để sắp mảng lớn.

### 4.3 Merge sort: chia để trị, ổn định

Merge sort chia mảng làm đôi, **đệ quy** sắp mỗi nửa, rồi **trộn** hai nửa đã sắp thành một:

```text
        [5,2,9,1,5,6,3,8]
        /              \
   [5,2,9,1]        [5,6,3,8]      chia
     /    \           /    \
  [5,2] [9,1]     [5,6] [3,8]
   ...              ...
  trộn ngược lên: [2,5][1,9] -> [1,2,5,9] ...  -> [1,2,3,5,5,6,8,9]
```

Chia `log n` tầng, mỗi tầng trộn tốn `O(n)` → `O(n log n)` **bảo đảm** (kể cả worst case). Bước trộn `Merge` khi hai bên bằng nhau ưu tiên lấy bên **trái** (`left[i] <= right[j]`) — nhờ vậy merge sort **ổn định**. Cái giá: cần mảng phụ `O(n)` để trộn, nên **không in-place**.

### 4.4 Quicksort và cái bẫy worst case

Quicksort chọn một **pivot**, phân hoạch (partition) mảng thành "nhỏ hơn pivot" bên trái và "lớn hơn" bên phải, rồi đệ quy hai phía. Nó sắp **in-place** (chỉ hoán đổi trong mảng, bộ nhớ phụ `O(log n)` cho call stack) và trung bình rất nhanh — thường nhanh hơn merge sort trong thực tế nhờ hằng số nhỏ và thân thiện cache.

Nhưng nhìn cột **quick** trong bảng: nó trùng khít **insertion** — cũng `O(n^2)`! Đây **không** phải lỗi. Cài đặt ở đây chọn pivot là **phần tử cuối** (Lomuto). Với đầu vào **đã đảo ngược** (hoặc đã sắp), pivot luôn là phần tử nhỏ nhất/lớn nhất, nên mỗi lần phân hoạch chỉ tách được **một** phần tử — cây đệ quy cao `n` thay vì `log n`. Đó chính là **worst case `O(n^2)`** của quicksort.

Cách chữa: chọn pivot **ngẫu nhiên**, hoặc lấy **median-of-three** (trung vị của đầu/giữa/cuối). Khi đó xác suất gặp phân hoạch tệ liên tục gần như bằng 0, và quicksort trở lại `O(n log n)` kỳ vọng. Bài học: `O(n log n)` của quicksort là **trung bình**, không phải bảo đảm — khác hẳn merge sort.

### Đào sâu (có thể quay lại sau)

- **Heapsort.** Đổ mảng vào max-heap (bài [08](./08-heap-va-priority-queue.md)) rồi rút lần lượt phần tử lớn nhất về cuối. `O(n log n)` bảo đảm, in-place, nhưng **không ổn định** và thường chậm hơn quicksort thực tế do truy cập bộ nhớ nhảy.
- **Cận dưới `O(n log n)`.** Mọi thuật toán sắp xếp **dựa trên so sánh** không thể nhanh hơn `O(n log n)` trong worst case — vì có `n!` hoán vị và mỗi so sánh chỉ chia đôi số khả năng, cần ít nhất `log2(n!) ≈ n log n` so sánh. Đây là giới hạn lý thuyết.
- **Sắp xếp không so sánh.** Counting sort, radix sort, bucket sort đạt `O(n)` bằng cách **không** so sánh phần tử mà dùng chính giá trị làm chỉ số — nhưng chỉ áp dụng khi khóa nằm trong miền hẹp (số nguyên giới hạn), không tổng quát.
- **Introsort trong .NET.** `Array.Sort`/`List.Sort` dùng **introsort**: bắt đầu bằng quicksort, chuyển sang heapsort khi độ sâu đệ quy quá lớn (chặn worst case `O(n^2)`), và dùng insertion sort cho đoạn nhỏ. Đây là lý do chúng nhanh và an toàn — nhưng **không ổn định**. Cần ổn định thì dùng LINQ `OrderBy`.

## 5. Kiến thức nền

### Bảng so sánh các thuật toán

| Thuật toán | Trung bình | Worst case | Bộ nhớ phụ | Ổn định | In-place |
|---|---|---|---|---|---|
| Insertion | `O(n^2)` | `O(n^2)` | `O(1)` | có | có |
| Merge | `O(n log n)` | `O(n log n)` | `O(n)` | có | không |
| Quick | `O(n log n)` | `O(n^2)` | `O(log n)` | không | có |
| Heap | `O(n log n)` | `O(n log n)` | `O(1)` | không | có |

Không có "thuật toán tốt nhất" tuyệt đối — chọn theo ưu tiên: cần bảo đảm worst case và ổn định thì merge; cần in-place và nhanh trung bình thì quick; dữ liệu nhỏ hoặc gần như đã sắp thì insertion.

### Ổn định nghĩa là gì

Một sắp xếp **ổn định** giữ nguyên thứ tự tương đối của các phần tử **bằng nhau theo khóa**. Trong output, sắp theo tuổi: "An/30" vẫn đứng trước "Cường/30" như ở mảng gốc, vì `OrderBy` ổn định. Điều này quan trọng khi sắp nhiều tầng (sắp theo tuổi, trong cùng tuổi giữ thứ tự tên đã sắp trước đó).

### Dùng thư viện chuẩn

Trong công việc thực tế **luôn dùng sắp xếp có sẵn**: `Array.Sort`, `List.Sort` (introsort, in-place, không ổn định) hoặc `Enumerable.OrderBy` (ổn định, tạo dãy mới). Tự viết chỉ để hiểu cơ chế và luyện tư duy chia để trị. Đừng tự cài sort trong code sản phẩm trừ khi có lý do rất đặc biệt đã được đo đạc.

## 6. Lỗi thường gặp

### Dùng `O(n^2)` cho dữ liệu lớn

Bubble/insertion/selection sort ổn cho mảng nhỏ hoặc gần như đã sắp, nhưng thảm họa với dữ liệu lớn. Với `n` lớn, luôn dùng `O(n log n)` (hoặc thư viện chuẩn).

### Tưởng quicksort luôn `O(n log n)`

Như bảng cho thấy, pivot tồi trên đầu vào đã sắp/đảo cho `O(n^2)`. Nếu tự cài quicksort, phải chọn pivot ngẫu nhiên hoặc median-of-three.

### Cần ổn định nhưng dùng sort không ổn định

`Array.Sort`/`List.Sort` **không** ổn định. Sắp nhiều tầng mà cần giữ thứ tự tầng trước thì phải dùng `OrderBy`/`ThenBy` (ổn định), nếu không thứ tự tầng trước bị phá.

### Quên rằng `OrderBy` là lazy và tạo dãy mới

`OrderBy` không sửa collection gốc mà trả một dãy mới, và **trì hoãn thực thi** (đã học ở module 05). `list.OrderBy(...)` mà không gán/duyệt kết quả thì chẳng sắp gì cả.

### So sánh sai kiểu với generic

Sắp type tự viết cần `IComparable<T>` hoặc truyền `IComparer<T>`/khóa `OrderBy`. Dựa vào `<`/`>` không áp dụng cho mọi `T`.

## 7. Bài tập

### Bài 1 — Selection sort

Cài selection sort: mỗi vòng tìm phần tử nhỏ nhất trong phần chưa sắp rồi đưa về đầu. Đếm số so sánh và so với insertion.

**Gợi ý:** selection luôn `O(n^2)` so sánh bất kể đầu vào, khác insertion (nhanh khi gần như đã sắp).

### Bài 2 — Quicksort chọn pivot ngẫu nhiên

Sửa `Partition` để hoán đổi một phần tử ngẫu nhiên với `a[hi]` trước khi phân hoạch. Chạy lại bảng đầu vào đảo ngược và quan sát cột quick không còn `O(n^2)`.

**Gợi ý:** `Random.Shared.Next(lo, hi + 1)` chọn chỉ số; số so sánh giảm mạnh và ổn định quanh `n log n`.

### Bài 3 — Sắp nhiều tầng

Cho danh sách người có `(Name, Age)`, sắp theo tuổi tăng dần, cùng tuổi thì theo tên. Dùng `OrderBy().ThenBy()`.

**Gợi ý:** `ThenBy` chạy trên nhóm bằng khóa trước; nhờ ổn định, không phá thứ tự tầng đầu.

### Bài 4 — Kiểm tra đã sắp

Viết hàm `bool IsSorted(int[] a)` chạy `O(n)`, dùng nó để xác nhận kết quả của cả ba thuật toán.

**Gợi ý:** chỉ cần một lượt kiểm tra `a[i] <= a[i+1]` cho mọi `i`.

### Bài 5 — Đo trên đầu vào ngẫu nhiên và đã sắp

Chạy ba thuật toán trên (a) mảng ngẫu nhiên và (b) mảng đã sắp sẵn cùng cỡ. Giải thích vì sao insertion nhanh trên (b) còn quicksort (pivot cuối) lại chậm.

**Gợi ý:** insertion gần `O(n)` khi gần như đã sắp; quicksort pivot cuối gặp worst case khi đã sắp — hai hành vi ngược nhau trên cùng đầu vào.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi cài được insertion, merge và quicksort và xác nhận cùng kết quả.
- [ ] Tôi giải thích được chia để trị trong merge và quick.
- [ ] Tôi phân biệt ổn định/không ổn định và in-place/không.
- [ ] Tôi giải thích được worst case `O(n^2)` của quicksort và cách chọn pivot tránh nó.
- [ ] Tôi biết cận dưới `O(n log n)` của sắp xếp dựa trên so sánh.
- [ ] Tôi dùng đúng `Array.Sort` (không ổn định) và `OrderBy` (ổn định).

Điều hướng:

- Bài prerequisite: [Shortest path và minimum spanning tree](./12-shortest-path-va-minimum-spanning-tree.md)
- Ôn lại nền tảng: [Big-O về thời gian và bộ nhớ](./01-big-o-thoi-gian-va-bo-nho.md), [Đệ quy và call stack](./02-de-quy-va-call-stack.md), [Heap và priority queue](./08-heap-va-priority-queue.md)
- Bài tiếp theo: [Searching](./14-searching.md)
