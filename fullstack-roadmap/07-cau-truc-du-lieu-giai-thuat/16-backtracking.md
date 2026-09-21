# Backtracking

## 1. Mục tiêu

Sau bài này, bạn có thể:

- mô tả backtracking là thử lựa chọn, tiến sâu, rồi hoàn tác khi không hợp lệ;
- phân biệt decision tree với call stack;
- cài bài toán sinh tổ hợp bằng backtracking;
- áp dụng pruning để giảm nhánh;
- phân tích vì sao nhiều bài backtracking có complexity exponential;
- nhận ra các use case như permutation, subset, N-Queens, Sudoku và constraint search.

## 2. Bài toán mở đầu

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

## 3. Lời giải bằng code

```bash
mkdir BacktrackingDemo
cd BacktrackingDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

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
            int nextSum = currentSum + values[i];

            if (nextSum > target)
            {
                break;
            }

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

## 4. Giải thích cơ chế

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
if (nextSum > target)
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

## 5. Kiến thức nền

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

## 7. Bài tập

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

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi hiểu choose-explore-unchoose.
- [ ] Tôi vẽ được decision tree.
- [ ] Tôi biết pruning cần giả định đúng.
- [ ] Tôi tránh lưu mutable state trực tiếp vào result.
- [ ] Tôi biết nhiều bài backtracking có exponential complexity.
- [ ] Tôi nhận ra DFS là nền traversal của backtracking.

Điều hướng:

- Bài trước: [Greedy](./15-greedy.md)
- Bài tiếp theo: [Dynamic programming](./17-dynamic-programming.md)
