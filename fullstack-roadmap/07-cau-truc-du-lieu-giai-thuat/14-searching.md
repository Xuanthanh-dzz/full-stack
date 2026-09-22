# Searching

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt linear search, binary search và hash lookup;
- cài binary search an toàn;
- hiểu invariant của vùng tìm kiếm;
- phân tích `O(n)` và `O(log n)`;
- cài lower bound để tìm vị trí đầu tiên thỏa điều kiện;
- chọn chiến lược search theo dữ liệu và operation;
- liên hệ search với database index và API filtering.

## 2. Bài toán mở đầu

Danh sách 1.000.000 mã đơn đã sort:

```text
100001
100002
100003
...
```

Tìm `875421`.

Linear search có thể phải kiểm tra hàng trăm nghìn phần tử.

Binary search mỗi bước loại một nửa:

```text
1,000,000
500,000
250,000
125,000
...
```

chỉ khoảng 20 lần chia đôi.

## 3. Lời giải bằng code

```bash
mkdir SearchingDemo
cd SearchingDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

```csharp
namespace SearchingDemo;

internal static class Program
{
    private static void Main()
    {
        int[] values = [2, 4, 4, 4, 7, 9, 12, 20];

        Console.WriteLine($"Index of 9 = {BinarySearch(values, 9)}");
        Console.WriteLine($"Index of 5 = {BinarySearch(values, 5)}");
        Console.WriteLine($"LowerBound(4) = {LowerBound(values, 4)}");
        Console.WriteLine($"LowerBound(5) = {LowerBound(values, 5)}");
    }

    private static int BinarySearch(int[] values, int target)
    {
        int left = 0;
        int right = values.Length - 1;

        while (left <= right)
        {
            int middle = left + ((right - left) / 2);
            int value = values[middle];

            if (value == target)
            {
                return middle;
            }

            if (value < target)
            {
                left = middle + 1;
            }
            else
            {
                right = middle - 1;
            }
        }

        return -1;
    }

    private static int LowerBound(int[] values, int target)
    {
        int left = 0;
        int right = values.Length;

        while (left < right)
        {
            int middle = left + ((right - left) / 2);

            if (values[middle] < target)
            {
                left = middle + 1;
            }
            else
            {
                right = middle;
            }
        }

        return left;
    }
}
```

Output:

```text
Index of 9 = 5
Index of 5 = -1
LowerBound(4) = 1
LowerBound(5) = 4
```

## 4. Giải thích cơ chế

### Binary search cần dữ liệu sorted

Invariant:

```text
nếu target tồn tại, nó nằm trong vùng [left, right]
```

Nếu middle nhỏ hơn target:

```text
left = middle + 1
```

Nếu middle lớn hơn target:

```text
right = middle - 1
```

Mỗi vòng giảm gần một nửa search space.

```text
O(log n)
```

### Công thức middle

Dùng:

```csharp
left + ((right - left) / 2)
```

thay vì:

```csharp
(left + right) / 2
```

để tránh overflow trong integer domain lớn.

### Lower bound

Lower bound trả index đầu tiên sao cho:

```text
values[index] >= target
```

Với:

```text
[2,4,4,4,7,9]
```

`LowerBound(4) = 1`.

Nếu target không tồn tại, nó trả insertion position.

```text
LowerBound(5) = 4
```

vì 5 nên được chèn trước 7.

## 5. Kiến thức nền

### Linear search

Không cần sorted data.

Time:

```text
O(n)
```

Phù hợp khi:

- collection nhỏ;
- chỉ search một lần;
- predicate phức tạp;
- sorting trước còn đắt hơn search.

### Binary search

Cần sorted data hoặc monotonic condition.

Time:

```text
O(log n)
```

Nhưng duy trì sorted collection có cost.

### Hash lookup

Exact key lookup:

```text
Dictionary/HashSet average O(1)
```

Đổi lại:

- thêm memory;
- không tự cung cấp range ordering.

### Search trên answer

Binary search không chỉ tìm value trong array.

Nếu predicate có tính monotonic:

```text
false false false true true true
```

ta có thể binary search điểm chuyển.

Ví dụ:

> capacity nhỏ nhất để xử lý workload trong <= 8 giờ.

## 6. Lỗi thường gặp

### Binary search trên dữ liệu chưa sort

Code vẫn chạy nhưng kết quả không đáng tin.

### Infinite loop do boundary sai

Nếu dùng half-open interval `[left, right)`, phải cập nhật nhất quán.

LowerBound sample dùng:

```text
left inclusive
right exclusive
```

### Tìm duplicate nhưng tưởng binary search trả phần tử đầu

Binary search cơ bản có thể trả bất kỳ occurrence nào.

Muốn occurrence đầu, dùng lower bound.

### Sort O(n log n) chỉ để search đúng một lần

Với một search duy nhất trên dữ liệu unsorted:

```text
linear O(n)
```

có thể tốt hơn:

```text
sort O(n log n) + search O(log n)
```

## 7. Bài tập

### Bài 1 — Upper bound

Trả index đầu tiên có:

```text
value > target
```

### Bài 2 — Count occurrences

Dùng lower/upper bound đếm số lần target xuất hiện.

### Bài 3 — First true

Cho mảng bool monotonic:

```text
false false true true
```

tìm index true đầu tiên.

### Bài 4 — Rotated array

Nghiên cứu search trong sorted array đã rotate.

### Bài 5 — Decision table

Chọn linear/binary/hash cho:

- exact lookup nhiều lần;
- range query;
- collection nhỏ;
- data chưa sort và search một lần.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi biết binary search yêu cầu ordering/monotonicity.
- [ ] Tôi duy trì invariant của search range.
- [ ] Tôi cài được lower bound.
- [ ] Tôi chọn linear/binary/hash theo workload.
- [ ] Tôi không sort chỉ vì muốn dùng binary search.
- [ ] Tôi biết binary search áp dụng được cho monotonic answer.

Điều hướng:

- Bài trước: [Sorting](./13-sorting.md)
- Bài tiếp theo: [Greedy](./15-greedy.md)
