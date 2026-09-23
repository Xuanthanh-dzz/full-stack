# Dynamic programming

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- Dynamic programming lưu đáp án bài toán con để tránh tính lại.
- Dùng khi các nhánh gặp lại cùng state và đáp án lớn ghép từ state nhỏ.
- State, base case và giá trị không thể đạt phải có nghĩa rõ.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- nhận ra overlapping subproblems và optimal substructure;
- phân biệt memoization và tabulation;
- chuyển một recursion lặp bài toán con thành DP;
- cài coin change minimum;
- phân tích time/space complexity của state transition;
- phân biệt greedy, backtracking và dynamic programming;
- biết cách thiết kế state, transition và base case.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Đổi tiền nhiều lần gặp lại câu hỏi “cần ít nhất bao nhiêu đồng để được 6”. Ghi câu trả lời cho 6 giúp những lần sau dùng lại; bảng không thay việc xác định chuyển trạng thái đúng.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| state | thông tin đủ để xác định bài toán con | amount còn lại |
| memoization | tính khi cần rồi cache | đệ quy có memo |
| tabulation | điền bảng theo thứ tự phụ thuộc | dp[0..amount] |
| unreachable | state không có lời giải | sentinel |

### Ví dụ nhỏ — tính tay trước

Coins [1, 3, 4], amount 6 → cần 2 đồng mệnh giá 3; greedy chọn 4 + 1 + 1 nên dùng 3 đồng. `dp[0] = 0`; `dp[6] = 1 + min(dp[5], dp[3], dp[2])`.

Hệ coin:

```text
1, 3, 4
```

Target:

```text
6
```

Greedy lấy coin lớn nhất:

```text
4 + 1 + 1 = 3 coins
```

Nhưng optimum:

```text
3 + 3 = 2 coins
```

Ta cần xem xét nhiều lựa chọn, nhưng không muốn tính lại cùng một amount hàng nghìn lần.

Dynamic programming lưu kết quả bài toán con.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```bash
mkdir DynamicProgrammingDemo
cd DynamicProgrammingDemo
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
namespace DynamicProgrammingDemo;

internal static class Program
{
    private static void Main()
    {
        int[] coins = [1, 3, 4];

        Console.WriteLine(
            $"Memoized 6 = {MinCoinsMemoized(coins, 6)}");

        Console.WriteLine(
            $"Tabulated 6 = {MinCoinsTabulated(coins, 6)}");
    }

    private static int MinCoinsMemoized(int[] coins, int amount)
    {
        Validate(coins, amount);
        var memo = new Dictionary<int, int>();

        return Solve(amount);

        int Solve(int remaining)
        {
            if (remaining == 0)
            {
                return 0;
            }

            if (remaining < 0)
            {
                return int.MaxValue;
            }

            if (memo.TryGetValue(remaining, out int cached))
            {
                return cached;
            }

            int best = int.MaxValue;

            foreach (int coin in coins)
            {
                int child = Solve(remaining - coin);

                if (child != int.MaxValue)
                {
                    best = Math.Min(best, checked(child + 1));
                }
            }

            memo[remaining] = best;
            return best;
        }
    }

    private static int MinCoinsTabulated(int[] coins, int amount)
    {
        Validate(coins, amount);

        var dp = Enumerable
            .Repeat(int.MaxValue, checked(amount + 1))
            .ToArray();

        dp[0] = 0;

        for (int current = 1; current <= amount; current++)
        {
            foreach (int coin in coins)
            {
                if (coin > current)
                {
                    continue;
                }

                int previous = dp[current - coin];

                if (previous != int.MaxValue)
                {
                    dp[current] = Math.Min(
                        dp[current],
                        checked(previous + 1));
                }
            }
        }

        return dp[amount];
    }

    private static void Validate(int[] coins, int amount)
    {
        ArgumentNullException.ThrowIfNull(coins);
        ArgumentOutOfRangeException.ThrowIfNegative(amount);

        if (coins.Length == 0 || coins.Any(x => x <= 0))
        {
            throw new ArgumentException(
                "Coins must contain positive denominations.",
                nameof(coins));
        }
    }
}
```

Output:

```text
Memoized 6 = 2
Tabulated 6 = 2
```

### Walkthrough — execution / state / cost

1. Validate coins dương và amount không âm; coin trùng vẫn được duyệt, không làm sai đáp án nhưng thêm công.
2. Memo hỏi state nhỏ rồi lưu kết quả; tabulation đi từ 0 lên amount.
3. Mỗi transition chỉ dùng state nhỏ hơn vì coin dương.
4. O(amount×số coin) thời gian, O(amount) bảng; memo còn có call stack. checked(amount+1) chặn overflow kích thước nhưng không bảo đảm đủ RAM.

### Mini-check

Coins [4, 6], amount 5: có được cộng 1 vào giá trị sentinel rồi coi là đáp án không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Overlapping subproblems

Naive recursion cho amount 6 có thể tính:

```text
solve(5)
solve(3)
solve(2)
...
```

Từ nhiều nhánh khác nhau, cùng `solve(2)`, `solve(3)` xuất hiện lặp lại.

Memoization lưu:

```text
amount -> best result
```

Mỗi state chỉ tính một lần.

### State

Trong bài coin change sample:

```text
state = remaining amount
```

Không cần lưu lịch sử coin đã chọn vì optimum còn lại chỉ phụ thuộc `remaining`.

Chọn state nhỏ nhất nhưng đủ thông tin là kỹ năng quan trọng nhất của DP.

### Transition

Với amount `a`:

```text
dp[a] =
1 + min(
    dp[a - coin1],
    dp[a - coin2],
    ...
)
```

cho các coin hợp lệ.

### Base case

```text
dp[0] = 0
```

Không cần coin nào để tạo amount 0.

### Complexity

Nếu:

- `A` = amount;
- `C` = số denomination;

mỗi amount thử mọi coin:

```text
O(A * C)
```

Space:

```text
O(A)
```

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| naive recursion | tính lại nhiều state | tốn nhánh lặp |
| memoization | chỉ tính state được hỏi | stack có thể sâu |
| tabulation | thứ tự tường minh | tính cả state không dùng nhưng không cần recursion |

### Misconception check

**Đúng hay sai?** Có cache nghĩa là không thể stack overflow.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: nhánh đầu vẫn có thể sâu trước khi cache được điền.

</details>

**Đúng hay sai?** O(amount) là nhỏ với mọi input int.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: amount là giá trị số, có thể hàng tỷ.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace bảng.

- **Working Developer — dùng khi làm việc:** sentinel và oracle.

- **Deep Dive — có thể quay lại sau:** state compression khi có nhu cầu.

### Memoization — top down

Bắt đầu từ bài toán lớn, recursion xuống bài toán nhỏ.

Ưu điểm:

- gần với recurrence;
- chỉ tính state thật sự cần.

Nhược:

- call stack;
- overhead recursion.

### Tabulation — bottom up

Xây từ base case lên.

Ưu điểm:

- không recursion;
- memory/layout dễ tối ưu.

Nhược:

- có thể tính state không cần;
- phải chọn đúng thứ tự dependency.

### Greedy vs DP

Greedy:

```text
chọn ngay -> không quay lại
```

DP:

```text
so sánh nhiều state -> giữ optimum
```

Coin `1,3,4`, amount 6 là counterexample cho greedy lớn nhất trước.

### Backtracking vs DP

Backtracking thường enumerate/search solution space.

DP gom nhiều path khác nhau dẫn tới cùng state thành một bài toán con duy nhất.

Nếu hai nhánh có “future” giống nhau, đó là tín hiệu có thể memoize.

## 6. Lỗi thường gặp

### State thiếu thông tin

Nếu kết quả tương lai còn phụ thuộc vào một biến khác nhưng state chỉ lưu amount, cache có thể trả kết quả sai.

### State quá lớn

Đưa cả history vào state có thể làm số state nổ.

### Sentinel overflow

Nếu dùng `int.MaxValue` cho impossible rồi cộng 1 trực tiếp, overflow.

Sample kiểm tra sentinel trước.

### Dùng DP khi greedy đã được chứng minh

DP phức tạp hơn không đồng nghĩa tốt hơn.

## 7. Khi nào KHÔNG dùng

Không cấp phát theo amount từ input ngoài mà không có budget. Không tạo DP nhiều chiều nếu chưa chứng minh mỗi chiều cần cho state.

## 8. Production notes & scale check

Gate so cả hai cách với BFS oracle trên amount nhỏ, kiểm không thể đổi, coin trùng và amount 0. Tránh gọi memo với amount cực lớn trong test vì stack overflow có thể kết thúc process.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Fibonacci memoized

So sánh số lời gọi với recursion ngây thơ.

### Bài 2 — Climbing stairs

Có thể bước 1 hoặc 2 bậc. Đếm số cách lên n bậc.

### Bài 3 — 0/1 knapsack

Thiết kế state theo:

```text
index
remaining capacity
```

### Bài 4 — Longest common subsequence

Thiết kế state `(i,j)` cho hai chuỗi.

### Bài 5 — Reconstruct coins

Không chỉ trả số coin tối thiểu; lưu predecessor để trả chính danh sách coin.

## 10. Bài tập tích hợp liên module — Judgment

Từ array và overflow ở Module 04: guard arithmetic bảo vệ gì khác budget bộ nhớ? Với đơn vị tiền rất nhỏ và amount rất lớn, cần xem lại biểu diễn hay thêm cache?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. State có đủ thông tin không?
2. Base case 0 có nghĩa gì?
3. Memo giữ thêm stack ở đâu?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi nhận ra overlapping subproblems.
- [ ] Tôi thiết kế được state/base/transition.
- [ ] Tôi phân biệt memoization và tabulation.
- [ ] Tôi tránh overflow sentinel.
- [ ] Tôi phân biệt greedy, backtracking và DP.
- [ ] Tôi phân tích số state nhân số transition.

Điều hướng:

- Bài trước: [Backtracking](./16-backtracking.md)
- Bài tiếp theo: [Bài toán tổng hợp và chọn cấu trúc dữ liệu](./18-bai-toan-tong-hop-va-chon-cau-truc-du-lieu.md)
