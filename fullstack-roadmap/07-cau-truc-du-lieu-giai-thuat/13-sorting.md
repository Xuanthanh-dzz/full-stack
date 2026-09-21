# Sorting

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích vì sao sorting là primitive quan trọng của nhiều thuật toán khác;
- phân biệt stable/unstable và in-place/out-of-place;
- phân tích `O(n²)` và `O(n log n)`;
- cài insertion sort và merge sort;
- mô tả quicksort ở mức cơ chế;
- biết khi nào nên dùng `Array.Sort`, `List<T>.Sort` thay vì tự viết;
- chọn comparer/key phù hợp với nghiệp vụ.

## 2. Bài toán mở đầu

Một trang admin cần sắp xếp 100.000 đơn hàng theo:

```text
CreatedAt desc
Total desc
OrderId asc
```

Sorting không chỉ là “xếp số tăng dần”. Trong phần mềm thật, nó liên quan:

- multi-key ordering;
- stability;
- pagination;
- database index;
- ranking;
- merge dữ liệu.

## 3. Lời giải bằng code

```bash
mkdir SortingDemo
cd SortingDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

```csharp
namespace SortingDemo;

internal static class Program
{
    private static void Main()
    {
        int[] values = [7, 3, 9, 1, 5, 2];

        int[] insertion = (int[])values.Clone();
        InsertionSort(insertion);
        Console.WriteLine($"Insertion: {string.Join(", ", insertion)}");

        int[] merged = MergeSort(values);
        Console.WriteLine($"Merge    : {string.Join(", ", merged)}");

        int[] builtIn = (int[])values.Clone();
        Array.Sort(builtIn);
        Console.WriteLine($"Built-in : {string.Join(", ", builtIn)}");
    }

    private static void InsertionSort(int[] values)
    {
        for (int i = 1; i < values.Length; i++)
        {
            int current = values[i];
            int j = i - 1;

            while (j >= 0 && values[j] > current)
            {
                values[j + 1] = values[j];
                j--;
            }

            values[j + 1] = current;
        }
    }

    private static int[] MergeSort(int[] values)
    {
        if (values.Length <= 1)
        {
            return (int[])values.Clone();
        }

        int middle = values.Length / 2;

        int[] left = MergeSort(values[..middle]);
        int[] right = MergeSort(values[middle..]);

        return Merge(left, right);
    }

    private static int[] Merge(int[] left, int[] right)
    {
        var result = new int[left.Length + right.Length];
        int i = 0;
        int j = 0;
        int k = 0;

        while (i < left.Length && j < right.Length)
        {
            if (left[i] <= right[j])
            {
                result[k++] = left[i++];
            }
            else
            {
                result[k++] = right[j++];
            }
        }

        while (i < left.Length)
        {
            result[k++] = left[i++];
        }

        while (j < right.Length)
        {
            result[k++] = right[j++];
        }

        return result;
    }
}
```

Output:

```text
Insertion: 1, 2, 3, 5, 7, 9
Merge    : 1, 2, 3, 5, 7, 9
Built-in : 1, 2, 3, 5, 7, 9
```

## 4. Giải thích cơ chế

### Insertion sort

Ý tưởng: phần bên trái đã sort, lấy phần tử tiếp theo chèn vào đúng vị trí.

```text
[3,7] | 5
       ^
dịch 7 sang phải
chèn 5

[3,5,7]
```

Worst-case:

```text
O(n²)
```

Nhưng insertion sort:

- đơn giản;
- ít overhead;
- hiệu quả với input nhỏ hoặc gần sorted.

### Merge sort

Chia:

```text
[7,3,9,1,5,2]
       /      \
 [7,3,9]     [1,5,2]
```

chia tiếp tới mảng nhỏ, rồi merge hai sequence đã sort.

Có khoảng `log n` tầng.
Mỗi tầng merge tổng cộng `n` phần tử.

```text
O(n log n)
```

Sample tạo array mới nên extra space khoảng `O(n)`.

### Quicksort

Ý tưởng:

1. chọn pivot;
2. partition nhỏ hơn/lớn hơn pivot;
3. recursively sort hai phía.

Average thường:

```text
O(n log n)
```

Worst case có thể:

```text
O(n²)
```

Implementation production dùng chiến lược pivot/threshold/hybrid phức tạp hơn bản textbook.

## 5. Kiến thức nền

### Stable sort

Nếu hai record có cùng key, stable sort giữ thứ tự tương đối ban đầu.

Ví dụ:

```text
(Alice, score 10)
(Bob,   score 10)
```

sau stable sort theo score vẫn Alice trước Bob nếu đó là thứ tự ban đầu.

Stability hữu ích trong multi-stage ordering.

### In-place

In-place thường dùng rất ít extra memory ngoài input.

Insertion sort là in-place.

Sample merge sort là out-of-place vì tạo array mới.

### Comparison sort lower bound

Với sorting chỉ dựa trên comparison tổng quát, giới hạn lý thuyết phổ biến:

```text
Ω(n log n)
```

cho worst/average theo mô hình comparison phù hợp.

Các thuật toán như counting/radix sort vượt giới hạn này bằng cách dùng thêm giả định về domain key.

### Sorting trong LINQ

```csharp
orders
    .OrderByDescending(x => x.CreatedAt)
    .ThenByDescending(x => x.Total)
    .ThenBy(x => x.Id);
```

Rất dễ đọc, nhưng nếu data ở database qua `IQueryable`, cần hiểu provider sẽ translate thành SQL thay vì sort tất cả trong memory.

## 6. Lỗi thường gặp

### Tự viết sort trong production mà không có lý do

BCL đã có implementation được tối ưu và test kỹ.

Tự viết chủ yếu phục vụ học thuật toán hoặc requirement rất đặc thù.

### Sort rồi mới filter dù filter giảm dữ liệu mạnh

Nếu có thể filter trước:

```text
filter -> sort
```

thường giảm lượng dữ liệu cần sort.

### So sánh string sai culture

Tên hiển thị, identifier kỹ thuật và key case-insensitive có semantics khác nhau.

Chọn comparer rõ ràng.

### Quên overflow khi comparer trả a-b

Sai:

```csharp
(a, b) => a.Id - b.Id
```

có thể overflow.

Dùng:

```csharp
a.Id.CompareTo(b.Id)
```

## 7. Bài tập

### Bài 1 — Selection sort

Cài selection sort và phân tích `O(n²)`.

### Bài 2 — Stable records

Tạo record có `Score` bằng nhau và kiểm tra stable ordering.

### Bài 3 — Sort nhiều key

Sort danh sách Order theo:

1. status;
2. created desc;
3. id.

### Bài 4 — Đếm comparison

Thêm counter vào insertion sort và merge sort với input:

- sorted;
- reverse sorted;
- random.

### Bài 5 — Chọn thuật toán

Giải thích lựa chọn cho:

- 20 phần tử gần sorted;
- 10 triệu số;
- stream chỉ cần top 10.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt `O(n²)` và `O(n log n)`.
- [ ] Tôi mô tả insertion/merge/quicksort.
- [ ] Tôi hiểu stable và in-place.
- [ ] Tôi dùng comparer phù hợp.
- [ ] Tôi không tự viết sort production khi BCL đã đáp ứng.
- [ ] Tôi biết top-k không nhất thiết cần sort toàn bộ.

Điều hướng:

- Bài trước: [Shortest path và minimum spanning tree](./12-shortest-path-va-minimum-spanning-tree.md)
- Bài tiếp theo: [Searching](./14-searching.md)
