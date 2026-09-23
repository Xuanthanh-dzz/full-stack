# Backtracking

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- Backtracking thử lựa chọn, đi sâu rồi hoàn tác state để thử nhánh khác.
- Dùng khi cần liệt kê tổ hợp và quy mô cho phép vét cạn.
- Phải copy đáp án; pruning chỉ hợp lệ dưới giả định đã nêu.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- mô tả backtracking là thử lựa chọn, tiến sâu, rồi hoàn tác khi không hợp lệ;
- phân biệt decision tree với call stack;
- cài bài toán sinh tổ hợp bằng backtracking;
- áp dụng pruning để giảm nhánh;
- phân tích vì sao nhiều bài backtracking có complexity exponential;
- nhận ra các use case như permutation, subset, N-Queens, Sudoku và constraint search.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Đi trong mê cung, đặt một viên sỏi khi rẽ và nhặt lại khi quay lui. Danh sách đường đang đi là một object dùng lại; ảnh chụp đường tới đích phải được giữ riêng.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| backtracking | thử rồi hoàn tác lựa chọn | Add/RemoveAt |
| pruning | bỏ nhánh chắc chắn không ra đáp án | tổng vượt target |
| snapshot | bản sao state tại thời điểm tìm thấy | current.ToArray() |

### Ví dụ nhỏ — tính tay trước

[2,3,5,7],target 10 →[2,3,5] và[3,7]. Số dương và mỗi giá trị dùng tối đa một lần; Distinct trong mẫu gộp giá trị trùng, không giữ identity của item.

Cho các số:

```text
2, 3, 5, 7
```

Tìm mọi tập con có tổng bằng 10.

Ta có nhiều quyết định:

```text
chọn 2 / bỏ 2
chọn 3 / bỏ 3
chọn 5 / bỏ 5
...
```

Nếu một nhánh đã vượt target và toàn bộ số đều dương, có thể dừng nhánh đó sớm.

Đây là cấu trúc điển hình của backtracking.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```bash
mkdir BacktrackingDemo
cd BacktrackingDemo
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
namespace BacktrackingDemo;

internal static class Program
{
    private static void Main()
    {
        int[] values = [2, 3, 5, 7];

        foreach (int[] combination in FindCombinations(values, 10))
        {
            Console.WriteLine($"[{string.Join(", ", combination)}]");
        }
    }

    private static IReadOnlyList<int[]> FindCombinations(
        int[] values,
        int target)
    {
        ArgumentNullException.ThrowIfNull(values);
        ArgumentOutOfRangeException.ThrowIfNegative(target);

        if (values.Any(x => x <= 0))
        {
            throw new ArgumentException(
                "This pruning strategy requires positive values.",
                nameof(values));
        }

        int[] ordered = values
            .Distinct()
            .OrderBy(x => x)
            .ToArray();

        var results = new List<int[]>();
        var current = new List<int>();

        Search(
            ordered,
            target,
            startIndex: 0,
            currentSum: 0,
            current,
            results);

        return results;
    }

    private static void Search(
        int[] values,
        int target,
        int startIndex,
        int currentSum,
        List<int> current,
        List<int[]> results)
    {
        if (currentSum == target)
        {
            results.Add(current.ToArray());
            return;
        }

        for (int i = startIndex; i < values.Length; i++)
        {
            // Tránh overflow trước khi quyết định prune.
            if (values[i] > target - currentSum)
            {
                break;
            }

            int nextSum = currentSum + values[i];
            current.Add(values[i]);

            Search(
                values,
                target,
                i + 1,
                nextSum,
                current,
                results);

            current.RemoveAt(current.Count - 1);
        }
    }
}
```

Output:

```text
[2, 3, 5]
[3, 7]
```

### Walkthrough — execution / state / cost

1. Validate target và các số dương, chuẩn hóa Distinct rồi sort.
2. Tại mỗi vị trí, thêm một số, gọi sâu với index tiếp theo.
3. Khi đạt target, copy current vào results; quay về thì xóa lựa chọn cuối.
4. Có tối đa 2^n tập con; output và copying có thể lớn. Guard value>target-currentSum chạy trước cộng để tránh int overflow.

### Mini-check

Nếu hai sản phẩm cùng giá 5 phải được phân biệt, Distinct có giữ đúng bài toán không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Chọn -> gọi đệ quy -> hoàn tác

Đoạn cốt lõi:

```csharp
current.Add(values[i]);

Search(...);

current.RemoveAt(current.Count - 1);
```

Ba bước:

1. **choose**: thêm lựa chọn;
2. **explore**: đi sâu;
3. **unchoose**: hoàn tác.

Nếu quên bước 3, state của nhánh trước sẽ rò sang nhánh sau.

### Decision tree

Với tập `[2,3,5]`:

```text
[]
├── [2]
│   ├── [2,3]
│   │   └── [2,3,5]
│   └── [2,5]
├── [3]
│   └── [3,5]
└── [5]
```

Backtracking duyệt một phần của cây quyết định.

### Pruning

Vì array đã sort và mọi số dương:

```csharp
if (values[i] > target - currentSum)
{
    break;
}
```

Nếu value hiện tại đã làm sum vượt target, mọi value phía sau còn lớn hơn, nên cả phần còn lại của loop không thể hợp lệ.

Pruning không đổi worst-case class trong mọi bài, nhưng có thể giảm cực lớn số node thực tế.

### Complexity

Subset search tổng quát có thể có:

```text
2^n
```

subset.

Permutation có thể tới:

```text
n!
```

Đây là lý do pruning và constraint mạnh rất quan trọng.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| liệt kê tập con | cần mọi lời giải | output có thể exponential |
| DP existence/count | chỉ cần có hay bao nhiêu | không mặc định trả mọi tổ hợp |
| greedy | chỉ chọn một nhánh | không đúng cho tổng tùy ý |

### Misconception check

**Đúng hay sai?** results.Add(current) lưu lịch sử của list.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: lưu reference, các đáp án cùng đổi theo current.

</details>

**Đúng hay sai?** Prune khi sum>target vẫn đúng với số âm.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: số âm ở phía sau có thể kéo tổng xuống.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace cây thử.

- **Working Developer — dùng khi làm việc:** alias và completeness.

- **Deep Dive — có thể quay lại sau:** quota/cancellation khi có driver.

### Backtracking khác DFS thế nào?

Backtracking thường **dùng DFS** trên decision tree.

Nhưng backtracking nhấn mạnh:

- xây partial solution;
- kiểm tra constraint;
- undo state.

DFS là chiến lược traversal rộng hơn.

### Mutable state hay copy state?

Hai cách:

1. copy list ở mỗi nhánh — code đơn giản nhưng nhiều allocation;
2. mutate rồi undo — ít allocation hơn nhưng dễ bug hơn.

Sample dùng mutate + undo.

### Constraint ordering

Nếu kiểm tra constraint rẻ và loại được nhiều nhánh, nên kiểm tra sớm.

Ví dụ Sudoku:

- chọn ô ít candidate nhất trước;
- thử constraint mạnh trước.

Đây là heuristic giúp giảm search tree.

## 6. Lỗi thường gặp

### Quên undo

State của nhánh cũ còn tồn tại, kết quả sai.

### Prune bằng giả định không đúng

Sample `break` khi sum > target chỉ đúng vì:

- values dương;
- đã sort tăng dần.

Nếu có số âm, logic này sai.

### Lưu reference tới current

Sai:

```csharp
results.Add(current);
```

Sau đó current tiếp tục thay đổi, mọi result có thể trỏ cùng list.

Phải snapshot:

```csharp
results.Add(current.ToArray());
```

### Backtracking khi có công thức/DP tốt hơn

Nếu chỉ cần số lượng hoặc optimum, exhaustive enumeration có thể không cần thiết.

## 7. Khi nào KHÔNG dùng

Không liệt kê mọi đáp án cho n lớn mà thiếu giới hạn output/thời gian. Không thêm số âm vào sample mà bỏ qua điều kiện pruning.

## 8. Production notes & scale check

Gate so tập đáp án với bitmask oracle trên input nhỏ, kiểm độc lập các snapshot, trùng giá trị, target 0 và số gần int.MaxValue. Đây là bài tập một process, không có cancellation hoặc quota tự động.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Permutation

Sinh mọi permutation của `[1,2,3]`.

### Bài 2 — Parentheses

Sinh mọi chuỗi ngoặc hợp lệ với `n` cặp.

**Gợi ý:** không bao giờ cho closing count vượt opening count.

### Bài 3 — N-Queens

Đặt N quân hậu sao cho không ăn nhau.

### Bài 4 — Sudoku

Mô tả state, choice, constraint và undo.

### Bài 5 — Compare pruning

Đếm số recursive call trước/sau khi thêm pruning trong subset-sum positive.

## 10. Bài tập tích hợp liên module — Judgment

So với iterator ở Module 05: trả IEnumerable có tự làm số đáp án ít đi không? Với UI chỉ cần lời giải đầu, đổi contract nào trước khi chọn tối ưu?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Hoàn tác bước nào?
2. Snapshot cần ở đâu?
3. Pruning phụ thuộc điều kiện gì?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi hiểu choose-explore-unchoose.
- [ ] Tôi vẽ được decision tree.
- [ ] Tôi biết pruning cần giả định đúng.
- [ ] Tôi tránh lưu mutable state trực tiếp vào result.
- [ ] Tôi biết nhiều bài backtracking có exponential complexity.
- [ ] Tôi nhận ra DFS là nền traversal của backtracking.

Điều hướng:

- Bài trước: [Greedy](./15-greedy.md)
- Bài tiếp theo: [Dynamic programming](./17-dynamic-programming.md)
