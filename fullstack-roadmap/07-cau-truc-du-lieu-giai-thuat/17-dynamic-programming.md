# Dynamic programming

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

## 3. Lời giải bằng code

```bash
mkdir DynamicProgrammingDemo
cd DynamicProgrammingDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

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
            .Repeat(int.MaxValue, amount + 1)
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

## 4. Giải thích cơ chế

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

## 5. Kiến thức nền

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

## 7. Bài tập

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

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi nhận ra overlapping subproblems.
- [ ] Tôi thiết kế được state/base/transition.
- [ ] Tôi phân biệt memoization và tabulation.
- [ ] Tôi tránh overflow sentinel.
- [ ] Tôi phân biệt greedy, backtracking và DP.
- [ ] Tôi phân tích số state nhân số transition.

Điều hướng:

- Bài trước: [Backtracking](./16-backtracking.md)
- Bài tiếp theo: [Bài toán tổng hợp và chọn cấu trúc dữ liệu](./18-bai-toan-tong-hop-va-chon-cau-truc-du-lieu.md)
