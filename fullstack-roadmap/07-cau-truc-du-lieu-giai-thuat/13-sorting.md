# Sorting

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- Sorting đưa dữ liệu về thứ tự để hiển thị hoặc hỗ trợ tìm kiếm.
- Chọn theo kích thước, yêu cầu giữ thứ tự các khóa bằng nhau và bộ nhớ.
- Output đã tăng dần chưa đủ chứng minh không mất hoặc nhân đôi phần tử.

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

### Trực giác 60 giây

Xếp bộ bài trên tay có thể chèn từng lá vào đúng chỗ; chia bộ bài thành hai nửa rồi trộn là cách khác. Hai cách cho cùng thứ tự nhưng số lần di chuyển và bộ nhớ khác nhau.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| stable | giữ thứ tự ban đầu của phần tử có khóa bằng nhau | hóa đơn cùng ngày |
| in-place | sửa trực tiếp vùng dữ liệu đầu vào | InsertionSort |
| merge | trộn hai dãy đã có thứ tự | MergeSort |

### Ví dụ nhỏ — tính tay trước

[3,1,2,1] →[1,1,2,3]. Phải giữ hai số 1. InsertionSort sửa array; MergeSort trả array và không sửa input trong sample.

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

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```bash
mkdir SortingDemo
cd SortingDemo
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

### Walkthrough — execution / state / cost

1. Insertion lấy key rồi dời các phần tử lớn hơn sang phải.
2. Merge chia đến dãy một phần tử, sau đó trộn hai dãy con.
3. Array.Sort là đối chiếu thư viện; quicksort chỉ được thảo luận để so sánh, không có implementation trong sample.
4. Insertion worst-case O(n²); merge O(n log n). Merge giữ O(n) bộ nhớ sống tại một thời điểm nhưng cấp phát cộng dồn O(n log n) phần tử qua nhiều tầng.

### Mini-check

Sort [2,2,1] thành [1,2] sai điều kiện nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

Sample có peak dữ liệu phụ còn cần dùng O(n), cộng call stack O(log n), nhưng range copy và merge cấp phát tổng cộng O(n log n) phần tử qua cả lần chạy. Tổng allocation khác với peak live memory; GC có thể chưa thu gom mọi array chết ngay.

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Insertion | dãy nhỏ hoặc gần có thứ tự | ít overhead, worst-case bậc hai |
| Merge | cần thứ tự ổn định theo cách merge | bộ nhớ phụ và allocations |
| QuickSort khái niệm | học partition | worst-case bậc hai, không hứa như thư viện |

### Misconception check

**Đúng hay sai?** Dãy tăng dần nghĩa là sort đúng.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: còn phải giữ số lần xuất hiện của từng giá trị.

</details>

**Đúng hay sai?** O(n) bộ nhớ nghĩa là chỉ cấp phát tổng cộng n phần tử.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: peak live memory khác tổng allocation qua thời gian.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace insertion/merge.

- **Working Developer — dùng khi làm việc:** mutation và oracle.

- **Deep Dive — có thể quay lại sau:** partition và worst-case.

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

## 7. Khi nào KHÔNG dùng

Không tự triển khai sort production khi API thư viện đáp ứng yêu cầu. Không chọn quicksort mẫu cho input không kiểm soát mà bỏ qua worst-case.

## 8. Production notes & scale check

Gate so kết quả với Array.Sort trên dãy rỗng, trùng, đảo và seed cố định; kiểm mutation contract. Tính ổn định cần record có identity để quan sát, không suy từ dãy int trùng. Không đo thời gian một lần rồi tuyên bố thuật toán nhanh nhất.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Từ ownership Module06: caller có còn cần thứ tự gốc không? Với100 mục hiển thị, chọn sort thư viện hay tự dựng cây; nêu chi phí chuẩn bị.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Stable nói về phần tử nào?
2. Peak memory khác allocations ra sao?
3. Pivot xấu tạo vấn đề gì?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt `O(n²)` và `O(n log n)`.
- [ ] Tôi mô tả insertion/merge/quicksort.
- [ ] Tôi hiểu stable và in-place.
- [ ] Tôi dùng comparer phù hợp.
- [ ] Tôi không tự viết sort production khi BCL đã đáp ứng.
- [ ] Tôi biết top-k không nhất thiết cần sort toàn bộ.

Điều hướng:

- Bài trước: [Shortest path và minimum spanning tree](./12-shortest-path-va-minimum-spanning-tree.md)
- Bài tiếp theo: [Searching](./14-searching.md)
