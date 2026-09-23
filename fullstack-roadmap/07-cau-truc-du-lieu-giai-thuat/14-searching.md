# Searching

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- Binary search loại nửa khoảng tìm kiếm khi dữ liệu đã có thứ tự.
- Dùng lower bound để tìm vị trí đầu tiên không nhỏ hơn khóa.
- Sai invariant hoặc bỏ chi phí sort có thể làm kết quả đúng tình cờ.

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

### Trực giác 60 giây

Tra từ điển bằng cách mở giữa, xem từ cần tìm nằm trước hay sau rồi bỏ một nửa. Cách này chỉ đúng vì trang đã sắp theo cùng quy tắc so sánh.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| search interval | khoảng chỉ số còn có thể chứa đáp án | [left,right) |
| lower bound | vị trí đầu tiên có giá trị >= khóa | đầu nhóm số 4 |
| invariant | điều luôn đúng qua mỗi vòng | đáp án vẫn thuộc khoảng |

### Ví dụ nhỏ — tính tay trước

[1,4,4,4,7], lower bound 4=1; lower bound 5=4; lower bound 8=5. Kết quả5 là vị trí chèn, không phải index có thể đọc.

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

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```bash
mkdir SearchingDemo
cd SearchingDemo
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

### Walkthrough — execution / state / cost

1. Khởi tạo khoảng chứa tất cả vị trí ứng viên.
2. Tính mid bằng left+(right-left)/2 tránh cộng hai index lớn.
3. So phần tử giữa với khóa rồi thu hẹp khoảng; mỗi vòng phải tiến.
4. O(log n) so sánh, O(1) state; chuẩn bị sort có thể O(n log n), array lookup O(1) là giả định.

### Mini-check

Vì sao phải kiểm index<Length trước đọc phần tử ở lower bound?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| linear search | không cần sort | O(n), hợp cho một lần tìm nhỏ |
| binary search | dữ liệu đã sort | O(log n), phải giữ comparator nhất quán |
| hash lookup | chỉ cần equality | trung bình O(1), thêm index và không tìm khoảng |

### Misconception check

**Đúng hay sai?** lower bound luôn trả phần tử bằng khóa.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: có thể trả phần tử lớn hơn hoặc length.

</details>

**Đúng hay sai?** Binary search trên linked list vẫn nhanh tương tự array.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: truy cập mid có thể phải đi qua nhiều node.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace chỉ số.

- **Working Developer — dùng khi làm việc:** boundary và duplicates.

- **Deep Dive — có thể quay lại sau:** amortize preprocessing.

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

## 7. Khi nào KHÔNG dùng

Không dùng trên dữ liệu chưa sort hoặc đang bị sửa đồng thời. Không sort toàn bộ chỉ để trả lời một query nhỏ nếu linear scan đủ.

## 8. Production notes & scale check

Gate so với linear oracle trên arrays có trùng, rỗng và khóa ngoài miền. Contract yêu cầu input tăng dần; không thêm kiểm O(n) vào mỗi query rồi vẫn quảng cáo tổng O(log n).

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

So Dictionary ở Module05: với1000 phần tử, một query và 100000 query, chi phí xây index/sort đổi quyết định thế nào?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Lower bound có thể bằng Length không?
2. Invariant của nửa khoảng là gì?
3. Chi phí sort tính ở đâu?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi biết binary search yêu cầu ordering/monotonicity.
- [ ] Tôi duy trì invariant của search range.
- [ ] Tôi cài được lower bound.
- [ ] Tôi chọn linear/binary/hash theo workload.
- [ ] Tôi không sort chỉ vì muốn dùng binary search.
- [ ] Tôi biết binary search áp dụng được cho monotonic answer.

Điều hướng:

- Bài trước: [Sorting](./13-sorting.md)
- Bài tiếp theo: [Greedy](./15-greedy.md)
