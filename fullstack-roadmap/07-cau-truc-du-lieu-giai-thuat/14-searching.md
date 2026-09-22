# Searching

## 1. Mục tiêu

Sau bài này, bạn có thể:

- cài đặt linear search (`O(n)`) và binary search (`O(log n)`);
- giải thích vì sao binary search cần dữ liệu **đã sắp xếp** và loại nửa mảng mỗi bước;
- viết binary search đúng, tránh lỗi off-by-one và tràn số khi tính `mid`;
- tìm **vị trí chèn** (lower bound) khi phần tử không tồn tại;
- so sánh ba cách tra cứu: linear, binary, hash — và chọn theo bài toán;
- dùng `Array.BinarySearch`/`List.BinarySearch` và hiểu giá trị âm nó trả về.

## 2. Bài toán mở đầu

Tra một giá trị trong tập dữ liệu là thao tác thường xuyên nhất trong lập trình. Có ba mức tốc độ, đổi bằng ba mức chuẩn bị:

- **Không chuẩn bị gì:** quét tuyến tính — `O(n)`. Với một tỉ phần tử là một tỉ bước.
- **Sắp xếp trước:** tìm nhị phân — `O(log n)`. Một tỉ phần tử chỉ **30 bước**.
- **Băm trước (hash):** tra `O(1)` trung bình (bài [06](./06-hash-table-va-hash-function.md)), nhưng mất thứ tự và tốn bộ nhớ.

Con số `O(n)` so với `O(log n)` nghe trừu tượng cho tới khi thấy: gấp đôi dữ liệu, linear search tốn gấp đôi công, còn binary search chỉ tốn **thêm đúng một bước**. Bài này cài cả hai, đo tận mắt sự khác biệt đó, và chỉ những cái bẫy khiến binary search — tưởng đơn giản — lại là một trong những đoạn code hay sai nhất.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `SearchingDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace SearchingDemo;

internal static class Program
{
    private static void Main()
    {
        int[] sorted = { 2, 5, 8, 12, 16, 23, 38, 45, 56, 72, 91 };
        Console.WriteLine($"Mảng đã sắp: [{string.Join(", ", sorted)}]");
        Console.WriteLine();

        Console.WriteLine("== Linear vs Binary search: tìm 23 ==");
        int li = LinearSearch(sorted, 23, out long lsteps);
        int bi = BinarySearch(sorted, 23, out long bsteps);
        Console.WriteLine($"  Linear: index {li} sau {lsteps} bước");
        Console.WriteLine($"  Binary: index {bi} sau {bsteps} bước");

        Console.WriteLine();
        Console.WriteLine("== Binary search: mỗi bước loại nửa còn lại (O(log n)) ==");
        Console.WriteLine($"{"n",8} | {"linear (xấu nhất)",18} | {"binary (xấu nhất)",18}");
        Console.WriteLine(new string('-', 52));
        foreach (int n in new[] { 15, 1000, 1_000_000, 1_000_000_000 })
        {
            Console.WriteLine($"{n,8} | {n,18} | {MaxBinarySteps(n),18}");
        }

        Console.WriteLine();
        Console.WriteLine("== Không tìm thấy: trả vị trí nên chèn để giữ thứ tự ==");
        int target = 30;
        int pos = LowerBound(sorted, target);
        Console.WriteLine($"  {target} không có; nên chèn ở index {pos} (giữa {sorted[pos - 1]} và {sorted[pos]})");

        Console.WriteLine();
        Console.WriteLine("== Array.BinarySearch có sẵn ==");
        int found = Array.BinarySearch(sorted, 45);
        int notFound = Array.BinarySearch(sorted, 30);
        Console.WriteLine($"  BinarySearch(45) = {found} (>= 0: tìm thấy tại index đó)");
        Console.WriteLine($"  BinarySearch(30) = {notFound} (< 0: ~kết quả là vị trí nên chèn = {~notFound})");
    }

    private static int LinearSearch(int[] a, int target, out long steps)
    {
        steps = 0;
        for (int i = 0; i < a.Length; i++)
        {
            steps++;
            if (a[i] == target) return i;
        }
        return -1;
    }

    // Binary search: cần mảng ĐÃ SẮP. Thu hẹp [lo, hi] một nửa mỗi bước.
    private static int BinarySearch(int[] a, int target, out long steps)
    {
        steps = 0;
        int lo = 0, hi = a.Length - 1;
        while (lo <= hi)
        {
            steps++;
            int mid = lo + (hi - lo) / 2; // tránh tràn số so với (lo+hi)/2
            if (a[mid] == target) return mid;
            if (a[mid] < target) lo = mid + 1; // đích ở nửa phải
            else hi = mid - 1;                 // đích ở nửa trái
        }
        return -1;
    }

    // Lower bound: chỉ số đầu tiên có a[i] >= target (vị trí chèn giữ thứ tự).
    private static int LowerBound(int[] a, int target)
    {
        int lo = 0, hi = a.Length;
        while (lo < hi)
        {
            int mid = lo + (hi - lo) / 2;
            if (a[mid] < target) lo = mid + 1;
            else hi = mid;
        }
        return lo;
    }

    private static long MaxBinarySteps(int n)
    {
        long steps = 0;
        while (n > 0) { n /= 2; steps++; }
        return steps;
    }
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
Mảng đã sắp: [2, 5, 8, 12, 16, 23, 38, 45, 56, 72, 91]

== Linear vs Binary search: tìm 23 ==
  Linear: index 5 sau 6 bước
  Binary: index 5 sau 1 bước

== Binary search: mỗi bước loại nửa còn lại (O(log n)) ==
       n |  linear (xấu nhất) |  binary (xấu nhất)
----------------------------------------------------
      15 |                 15 |                  4
    1000 |               1000 |                 10
 1000000 |            1000000 |                 20
1000000000 |         1000000000 |                 30

== Không tìm thấy: trả vị trí nên chèn để giữ thứ tự ==
  30 không có; nên chèn ở index 6 (giữa 23 và 38)

== Array.BinarySearch có sẵn ==
  BinarySearch(45) = 7 (>= 0: tìm thấy tại index đó)
  BinarySearch(30) = -7 (< 0: ~kết quả là vị trí nên chèn = 6)
```

## 4. Giải thích cơ chế

### 4.1 Linear search: đơn giản, luôn dùng được

Linear search quét từng phần tử. Nó `O(n)` nhưng **không cần điều kiện gì** — dữ liệu không sắp, kiểu dữ liệu không so sánh được, vẫn dùng được (chỉ cần so bằng). Tìm `23` mất 6 bước vì `23` ở vị trí thứ 6. Với dữ liệu nhỏ hoặc tìm một lần, linear là lựa chọn hợp lý — đừng phức tạp hóa.

### 4.2 Binary search: loại nửa mỗi bước

Binary search khai thác một điều kiện mạnh: **mảng đã sắp**. Nó giữ một khoảng `[lo, hi]` chứa đích, mỗi bước nhìn phần tử **giữa**:

- nếu bằng đích → xong;
- nếu giữa < đích → đích nằm ở **nửa phải**, bỏ nửa trái (`lo = mid + 1`);
- nếu giữa > đích → đích nằm ở **nửa trái**, bỏ nửa phải (`hi = mid - 1`).

Tìm `23`: `mid = 5`, `a[5] = 23` — trúng ngay bước 1 (vì 23 tình cờ ở giữa mảng). Với đích khác, mỗi bước **loại đúng một nửa** số ứng viên còn lại. Sau `k` bước, còn `n / 2^k` ứng viên; chạm 1 khi `k = log₂ n`. Đó là `O(log n)`.

### 4.3 `O(log n)` mạnh đến mức nào

Bảng nói lên tất cả: với **một tỉ** phần tử, linear cần tối đa một tỉ bước, còn binary chỉ **30**. Mỗi lần `n` gấp mười, binary chỉ thêm ~3 bước. Đây là lý do mọi cấu trúc tra cứu theo thứ tự (B-tree của index cơ sở dữ liệu ở [module 08](../08-sql-va-csdl/17-index-btree-clustered-nonclustered.md), cây tìm kiếm ở bài [07](./07-tree-va-binary-search-tree.md)) đều dựa trên ý tưởng chia đôi này.

### 4.4 Khi không tìm thấy: vị trí chèn

Thường ta không chỉ muốn "có/không" mà cả "nếu chèn thì chèn ở đâu để giữ thứ tự". `LowerBound` là biến thể binary search trả chỉ số **đầu tiên** có `a[i] >= target`. Với `30` (không có trong mảng), nó trả `6` — đúng khe giữa `23` và `38`.

`Array.BinarySearch` mã hóa điều này thông minh: trả chỉ số ≥ 0 nếu tìm thấy; nếu không, trả **số âm** mà `~kết quả` (bù bit) chính là vị trí nên chèn. `BinarySearch(30) = -7`, và `~(-7) = 6` — cùng vị trí chèn. Quy ước số âm cho phép phân biệt "tìm thấy ở index 0" với "không thấy" mà không cần kiểu trả về phức tạp.

### Đào sâu (có thể quay lại sau)

- **Cái bẫy tính `mid`.** Viết `mid = (lo + hi) / 2` có thể **tràn số** khi `lo + hi` vượt `int.MaxValue` (mảng cực lớn) — một bug nổi tiếng tồn tại trong thư viện suốt nhiều năm. Cách an toàn: `mid = lo + (hi - lo) / 2`, luôn nằm trong khoảng và không tràn.
- **Off-by-one.** Binary search nổi tiếng khó viết đúng vì ranh giới: `hi = a.Length - 1` với vòng `lo <= hi` (khoảng đóng), hay `hi = a.Length` với vòng `lo < hi` (khoảng nửa mở) — hai kiểu dùng điều kiện khác nhau, trộn lẫn là sai. Chọn một kiểu và nhất quán.
- **Chi phí sắp xếp.** Binary search cần dữ liệu đã sắp; nếu phải sắp trước chỉ để tìm một lần, tổng chi phí là `O(n log n)` — tệ hơn linear `O(n)`. Binary search chỉ đáng khi dữ liệu **đã sắp sẵn** hoặc được tìm **nhiều lần** để bù chi phí sắp.
- **Tìm trong không gian trừu tượng.** Binary search không chỉ dùng trên mảng: bất cứ khi nào có một hàm đơn điệu (đúng/sai theo ngưỡng), ta "chia đôi đáp án" — ví dụ tìm giá trị nhỏ nhất thỏa điều kiện. Đây là kỹ thuật "binary search on answer".

## 5. Kiến thức nền

### Ba cách tra cứu

| Cách | Chuẩn bị | Tìm | Giữ thứ tự | Bộ nhớ phụ |
|---|---|---|---|---|
| Linear | không | `O(n)` | — | không |
| Binary | sắp `O(n log n)` | `O(log n)` | có | không |
| Hash | băm | `O(1)` tb | không | `O(n)` |

Quy tắc chọn:

- **Tìm một lần, dữ liệu nhỏ hoặc chưa sắp** → linear. Đơn giản nhất.
- **Dữ liệu đã sắp và tìm nhiều lần, cần cả thứ tự/range** → binary.
- **Chỉ cần tra khóa nhanh, không cần thứ tự** → hash (`Dictionary`/`HashSet`).

### Binary search và cây tìm kiếm là họ hàng

Cả hai đều loại một nửa ứng viên mỗi bước dựa trên so sánh. Binary search làm điều đó trên **mảng đã sắp** (dữ liệu tĩnh); BST (bài [07](./07-tree-va-binary-search-tree.md)) làm trên **cây** (dữ liệu thêm/xóa động). Chọn mảng + binary khi dữ liệu ít đổi; chọn cây khi chèn/xóa thường xuyên.

### Điều kiện tiên quyết của binary search

Binary search **chỉ đúng** khi mảng đã sắp theo đúng tiêu chí tìm. Áp binary search lên mảng chưa sắp cho kết quả sai một cách âm thầm (không lỗi, chỉ sai). Luôn bảo đảm dữ liệu đã sắp trước khi dùng.

## 6. Lỗi thường gặp

### Binary search trên mảng chưa sắp

Lỗi logic phổ biến nhất: dữ liệu chưa sắp thì binary search trả kết quả vô nghĩa mà không báo lỗi. Kiểm tra (hoặc bảo đảm) đã sắp trước khi tìm.

### Tràn số khi tính `mid`

`(lo + hi) / 2` tràn với mảng lớn. Dùng `lo + (hi - lo) / 2`. Đây là bug kinh điển, đừng lặp lại.

### Vòng lặp không kết thúc

Cập nhật ranh giới sai (`lo = mid` thay vì `lo = mid + 1`) khiến khoảng không thu nhỏ và lặp vô hạn. Sau mỗi bước, khoảng `[lo, hi]` phải **thực sự** nhỏ đi.

### Hiểu nhầm giá trị âm của `Array.BinarySearch`

`Array.BinarySearch` trả số âm khi không thấy — không phải `-1` cố định, mà là `~vị_trí_chèn`. Dùng thẳng nó như chỉ số (hoặc so `== -1`) là sai; phải `if (result < 0)` rồi lấy `~result` để có vị trí chèn.

### Sắp lại chỉ để tìm một lần

Sắp `O(n log n)` rồi binary search `O(log n)` cho **một** lần tìm là chậm hơn linear `O(n)`. Chỉ sắp trước khi sẽ tìm nhiều lần.

## 7. Bài tập

### Bài 1 — Binary search đệ quy

Viết lại binary search bằng đệ quy thay vòng lặp. So độ sâu đệ quy với số bước của bản lặp.

**Gợi ý:** tham số `lo`, `hi`; base case `lo > hi` trả `-1`; độ sâu đệ quy chính là `O(log n)`.

### Bài 2 — Upper bound

Viết `UpperBound` trả chỉ số **đầu tiên** có `a[i] > target` (khác lower bound dùng `>=`). Dùng cả hai để đếm số lần xuất hiện của một giá trị trong mảng đã sắp.

**Gợi ý:** số lần xuất hiện = `UpperBound(x) - LowerBound(x)`.

### Bài 3 — Tìm phần tử đầu/cuối

Trong mảng đã sắp có phần tử lặp, tìm chỉ số **đầu tiên** và **cuối cùng** của một giá trị, mỗi cái trong `O(log n)`.

**Gợi ý:** biến thể binary search: khi trúng, tiếp tục thu hẹp về trái (tìm đầu) hoặc phải (tìm cuối).

### Bài 4 — Binary search on answer

Cho `n` chiếc bánh và `k` người, tìm số bánh **nhiều nhất** mỗi người nhận được sao cho chia đủ cho `k` người. Dùng binary search trên đáp án.

**Gợi ý:** hàm "chia được cho k người với mỗi người x bánh không?" là đơn điệu theo `x`; chia đôi khoảng `x` khả dĩ.

### Bài 5 — So sánh thực nghiệm với hash

Với một tập tìm 10.000 lần: đo (khái niệm) chi phí linear (`O(n)` mỗi lần), binary (sắp một lần rồi `O(log n)`), và `HashSet` (`O(1)`). Với `n = 10.000`, cách nào tổng thể nhanh nhất và vì sao.

**Gợi ý:** binary phải cộng chi phí sắp một lần; hash phải cộng chi phí dựng bảng; nhiều lần tìm thì chi phí chuẩn bị được chia đều.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi cài được linear search và binary search.
- [ ] Tôi giải thích được vì sao binary search cần mảng đã sắp và là `O(log n)`.
- [ ] Tôi viết `mid` tránh tràn số và cập nhật ranh giới không lặp vô hạn.
- [ ] Tôi tìm được vị trí chèn (lower bound) khi phần tử không tồn tại.
- [ ] Tôi chọn đúng giữa linear, binary và hash theo bài toán.
- [ ] Tôi hiểu giá trị âm mà `Array.BinarySearch` trả về.

Điều hướng:

- Bài prerequisite: [Sorting](./13-sorting.md)
- Ôn lại nền tảng: [Big-O về thời gian và bộ nhớ](./01-big-o-thoi-gian-va-bo-nho.md), [Hash table và hash function](./06-hash-table-va-hash-function.md)
- Bài tiếp theo: [Greedy](./15-greedy.md)
