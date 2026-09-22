# Dynamic programming

## 1. Mục tiêu

Sau bài này, bạn có thể:

- nhận ra hai điều kiện của DP: **optimal substructure** và **overlapping subproblems**;
- biến một đệ quy `O(2^n)` thành `O(n)` bằng **memoization** (top-down);
- viết lời giải **tabulation** (bottom-up) và tối ưu bộ nhớ;
- giải bài đổi tiền tối thiểu bằng DP — bài mà greedy đã thất bại;
- đọc và điền một **bảng DP**, hiểu ý nghĩa từng ô;
- phân biệt DP với greedy và backtracking, biết khi nào chọn cái nào.

## 2. Bài toán mở đầu

Nhớ lại bài [02](./02-de-quy-va-call-stack.md): `Fibonacci` đệ quy ngây thơ cần **2,6 triệu** lời gọi cho `fib(30)`, vì nó **tính lại** `fib(k)` vô số lần. Và bài [15](./15-greedy.md): đổi tiền tham lam cho đáp án sai với bộ mệnh giá `[4, 3, 1]`.

Cả hai đều là dấu hiệu của cùng một kỹ thuật: **dynamic programming**. Ý tưởng trung tâm chỉ có một câu: *nếu cùng một bài con bị giải đi giải lại, hãy giải một lần rồi nhớ kết quả.* Với Fibonacci, "nhớ lại" cắt `2^n` xuống `n`. Với đổi tiền, "xét mọi lựa chọn và nhớ kết quả bài con tối ưu" cho đáp án đúng nơi greedy sai.

DP nghe cao siêu nhưng cốt lõi bình dân: đừng làm lại việc đã làm. Bài này chỉ ra hai cách hiện thực ý tưởng đó và cách nhận diện bài toán DP.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `DpDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace DpDemo;

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine("== Fibonacci: ngây thơ vs memoization ==");
        Console.WriteLine($"{"n",4} | {"fib",10} | {"gọi (ngây thơ)",16} | {"gọi (memo)",12}");
        Console.WriteLine(new string('-', 52));
        foreach (int n in new[] { 10, 20, 30, 40 })
        {
            _naiveCalls = 0;
            long naive = FibNaive(n);
            _memoCalls = 0;
            long memo = FibMemo(n, new Dictionary<int, long>());
            Console.WriteLine($"{n,4} | {naive,10} | {_naiveCalls,16} | {_memoCalls,12}");
        }

        Console.WriteLine();
        Console.WriteLine("== Fibonacci tabulation (bottom-up), O(n) thời gian, O(1) bộ nhớ ==");
        Console.WriteLine($"fib(40) = {FibTabulation(40)}");

        Console.WriteLine();
        Console.WriteLine("== Đổi tiền tối thiểu bằng DP (bài greedy đã THUA) ==");
        int[] coins = { 4, 3, 1 };
        int amount = 6;
        int[] table = MinCoinsTable(coins, amount);
        Console.WriteLine($"Mệnh giá [{string.Join(", ", coins)}], đổi {amount}:");
        Console.Write("Bảng dp[0..6] = [");
        Console.Write(string.Join(", ", table.Select(x => x == int.MaxValue ? "∞" : x.ToString())));
        Console.WriteLine("]");
        Console.WriteLine($"Số đồng tối thiểu để đổi {amount} = {table[amount]} (greedy cho 3, DP cho đúng 2)");

        Console.WriteLine();
        Console.WriteLine("== Cùng thuật toán DP dùng cho tiền VND ==");
        int[] vnd = { 1000, 5000, 10000, 20000, 50000 };
        int[] t2 = MinCoinsTable(vnd, 87000);
        Console.WriteLine($"Đổi 87000 với mệnh giá VND: {t2[87000]} tờ");
    }

    private static long _naiveCalls;
    private static long _memoCalls;

    private static long FibNaive(int n)
    {
        _naiveCalls++;
        if (n < 2) return n;
        return FibNaive(n - 1) + FibNaive(n - 2);
    }

    // Top-down: đệ quy nhưng NHỚ kết quả đã tính (memoization).
    private static long FibMemo(int n, Dictionary<int, long> cache)
    {
        _memoCalls++;
        if (n < 2) return n;
        if (cache.TryGetValue(n, out long cached)) return cached; // đã tính -> tái dùng
        long result = FibMemo(n - 1, cache) + FibMemo(n - 2, cache);
        cache[n] = result;
        return result;
    }

    // Bottom-up: xây từ bài nhỏ lên, chỉ giữ hai giá trị gần nhất.
    private static long FibTabulation(int n)
    {
        if (n < 2) return n;
        long prev = 0, curr = 1;
        for (int i = 2; i <= n; i++)
        {
            (prev, curr) = (curr, prev + curr);
        }
        return curr;
    }

    // dp[a] = số đồng tối thiểu để đổi số tiền a.
    private static int[] MinCoinsTable(int[] coins, int amount)
    {
        var dp = new int[amount + 1];
        Array.Fill(dp, int.MaxValue);
        dp[0] = 0; // đổi 0 cần 0 đồng
        for (int a = 1; a <= amount; a++)
        {
            foreach (int coin in coins)
            {
                if (coin <= a && dp[a - coin] != int.MaxValue)
                {
                    dp[a] = Math.Min(dp[a], dp[a - coin] + 1);
                }
            }
        }
        return dp;
    }
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
== Fibonacci: ngây thơ vs memoization ==
   n |        fib |   gọi (ngây thơ) |   gọi (memo)
----------------------------------------------------
  10 |         55 |              177 |           19
  20 |       6765 |            21891 |           39
  30 |     832040 |          2692537 |           59
  40 |  102334155 |        331160281 |           79

== Fibonacci tabulation (bottom-up), O(n) thời gian, O(1) bộ nhớ ==
fib(40) = 102334155

== Đổi tiền tối thiểu bằng DP (bài greedy đã THUA) ==
Mệnh giá [4, 3, 1], đổi 6:
Bảng dp[0..6] = [0, 1, 2, 1, 1, 2, 2]
Số đồng tối thiểu để đổi 6 = 2 (greedy cho 3, DP cho đúng 2)

== Cùng thuật toán DP dùng cho tiền VND ==
Đổi 87000 với mệnh giá VND: 6 tờ
```

## 4. Giải thích cơ chế

### 4.1 Memoization: nhớ để không tính lại

`FibMemo` giống hệt bản ngây thơ, chỉ thêm một `cache`: trước khi tính `fib(n)`, kiểm tra đã có trong cache chưa; tính xong thì lưu lại. Nhìn bảng — con số nói lên phép màu:

- `fib(40)` ngây thơ: **331.160.281** lời gọi.
- `fib(40)` memo: **79** lời gọi.

Vì sao? Cây đệ quy ngây thơ tính lại `fib(k)` theo cấp số nhân; memo tính **mỗi** `fib(k)` đúng một lần (còn lại là tra cache), nên tổng lời gọi chỉ cỡ `2n`. Đây gọi là **top-down**: vẫn đệ quy từ trên xuống, chỉ thêm bộ nhớ đệm. Độ phức tạp rơi từ `O(2^n)` xuống `O(n)`.

### 4.2 Tabulation: xây từ dưới lên

`FibTabulation` bỏ hẳn đệ quy: nó xây kết quả **từ bài nhỏ nhất lên** bằng một vòng lặp. `fib(i)` chỉ cần `fib(i-1)` và `fib(i-2)`, nên chỉ giữ **hai** biến `prev`, `curr` — bộ nhớ `O(1)`. Đây là **bottom-up**: điền bảng theo thứ tự phụ thuộc, mỗi ô tính từ các ô đã có.

Hai cách cùng cho `O(n)` thời gian. Top-down (memo) tự nhiên hơn khi viết từ đệ quy có sẵn và chỉ tính các bài con thực sự cần; bottom-up thường nhanh hơn (không chi phí đệ quy) và dễ tối ưu bộ nhớ như ở đây.

### 4.3 Đổi tiền: DP thắng nơi greedy thua

`MinCoinsTable` xây `dp[a]` = **số đồng tối thiểu** để đổi số tiền `a`. Công thức truy hồi:

```text
dp[a] = 1 + min( dp[a - coin] )  với mọi coin <= a
dp[0] = 0
```

Nghĩa là: để đổi `a`, thử **mọi** đồng cuối cùng là `coin`, phần còn lại `a - coin` đã có lời giải tối ưu trong `dp`. Lấy phương án tốt nhất. Nhìn bảng cho `[4,3,1]`, đổi 6:

```text
a:      0   1   2   3   4   5   6
dp[a]:  0   1   2   1   1   2   2
                            ^   ^
        dp[4]=1 (một đồng 4)  dp[6]=2 (3+3, KHÔNG phải 4+1+1)
```

`dp[6] = 2`: đổi 6 bằng `dp[3] + 1 = 1 + 1 = 2` (tức 3 + 3). DP **xét cả** phương án dùng đồng 3 trước, thứ mà greedy — luôn chọn đồng lớn nhất (4) — bỏ qua. Nhờ nhớ lời giải tối ưu của mọi bài con, DP không bị "kẹt" như greedy. Và **cùng** thuật toán này cho tiền VND ra 6 tờ, khớp kết quả greedy — vì với mệnh giá canonical, greedy tình cờ cũng tối ưu.

### 4.4 Hai điều kiện để DP áp dụng được

DP chỉ đúng khi bài toán có:

1. **Optimal substructure** — lời giải tối ưu của bài lớn ghép từ lời giải tối ưu của bài con. Đổi 6 tối ưu = 1 đồng + đổi (6 - đồng đó) tối ưu. Đúng.
2. **Overlapping subproblems** — cùng bài con xuất hiện nhiều lần. `dp[3]` được nhiều `dp[a]` lớn hơn dùng lại. Đúng.

Thiếu điều kiện 2 (bài con không trùng) thì DP không lợi gì so với đệ quy thường. Thiếu điều kiện 1 thì DP cho kết quả sai. Nhận diện hai điều kiện này là bước đầu tiên khi nghi ngờ một bài là DP.

### Đào sâu (có thể quay lại sau)

- **Truy vết lời giải.** `dp` cho *giá trị* tối ưu (2 đồng), nhưng không nói *dùng đồng nào*. Muốn liệt kê, lưu thêm "lựa chọn tốt nhất tại mỗi ô" rồi truy ngược — giống parent map ở BFS (bài [11](./11-bfs-va-dfs.md)).
- **Bài DP kinh điển.** Longest common subsequence (so hai chuỗi/diff), 0/1 knapsack, edit distance (khoảng cách chỉnh sửa), longest increasing subsequence, đường đi trên lưới. Đa số là DP hai chiều `dp[i][j]`.
- **Định nghĩa trạng thái là phần khó nhất.** Viết được công thức truy hồi (state + transition) là giải được 80% bài DP. Câu hỏi luôn là: "dp[...] đại diện cho bài con nào, và tính từ các bài con nào?"
- **Độ phức tạp.** Thường bằng **số trạng thái × chi phí mỗi transition**. Đổi tiền: `O(amount × số mệnh giá)`. Đây là DP giả-đa-thức (phụ thuộc giá trị `amount`, không chỉ số phần tử).

## 5. Kiến thức nền

### Ba mẫu hình so sánh

| | Greedy | Backtracking | DP |
|---|---|---|---|
| Cách làm | chọn tốt nhất tại chỗ | thử mọi cách, lùi khi bế tắc | thử mọi cách, **nhớ** bài con |
| Điều kiện đúng | greedy-choice property | (liệt kê/tìm cấu hình) | optimal substructure + overlapping |
| Tốc độ | nhanh nhất | mũ (có pruning) | đa thức thường |
| Rủi ro | dễ sai | có thể quá chậm | tốn bộ nhớ bảng |

DP là điểm cân bằng: đúng như backtracking (xét hết), nhanh nhờ không tính lại. Khi greedy sai và backtracking quá chậm vì bài con trùng lặp — đó là lúc của DP.

### Top-down hay bottom-up?

- **Top-down (memo):** viết từ công thức đệ quy tự nhiên, chỉ tính bài con cần tới. Dễ nghĩ, nhưng có chi phí đệ quy và nguy cơ tràn stack với trạng thái sâu.
- **Bottom-up (tabulation):** điền bảng theo thứ tự, không đệ quy, dễ tối ưu bộ nhớ (như giữ hai biến ở Fibonacci). Cần xác định đúng thứ tự phụ thuộc.

Hai cách cho cùng độ phức tạp; chọn theo bài và sở thích.

### Quy trình giải một bài DP

1. Xác định **trạng thái**: `dp[...]` nghĩa là gì.
2. Viết **công thức truy hồi**: `dp[...]` tính từ trạng thái nào.
3. Xác định **base case**: giá trị khởi đầu (`dp[0] = 0`).
4. Xác định **thứ tự tính** (bottom-up) hoặc thêm cache (top-down).
5. Đọc **đáp án** từ ô nào của bảng.

## 6. Lỗi thường gặp

### Bỏ memoization cho đệ quy có bài con trùng

Fibonacci ngây thơ là ví dụ kinh điển: cùng công thức đúng nhưng thiếu cache thì chậm mũ. Thấy cây đệ quy tính lại bài con là thêm memo ngay.

### Base case sai

`dp[0]` phải đặt đúng (đổi 0 cần 0 đồng). Base case sai làm sai lan toàn bảng. Luôn kiểm tra trạng thái nhỏ nhất bằng tay.

### Định nghĩa trạng thái không đủ

Nếu `dp[...]` không nắm đủ thông tin để tính transition, công thức sẽ sai. Trạng thái phải "đủ" để bài con độc lập với đường đi tới nó.

### Áp DP khi thiếu optimal substructure

Không phải bài nào cũng có optimal substructure; ép DP vào bài không thỏa cho kết quả sai. Kiểm tra điều kiện trước khi cài.

### Dùng `int.MaxValue` rồi cộng gây tràn

Trong đổi tiền, `dp[a - coin] + 1` khi `dp[a-coin]` là `int.MaxValue` sẽ **tràn số** thành số âm và phá logic `Min`. Phải kiểm tra `dp[a - coin] != int.MaxValue` trước khi cộng (như trong code).

## 7. Bài tập

### Bài 1 — Fibonacci top-down bằng mảng

Viết lại `FibMemo` dùng mảng `long[]` thay `Dictionary` làm cache. So tốc độ (mảng tra nhanh hơn dictionary).

**Gợi ý:** khởi tạo mảng với sentinel (ví dụ -1) để biết ô nào chưa tính.

### Bài 2 — Liệt kê các đồng đã dùng

Mở rộng `MinCoinsTable` để truy vết **danh sách** các đồng cho lời giải tối ưu, không chỉ số lượng.

**Gợi ý:** lưu thêm `from[a]` = đồng cuối cùng cho `dp[a]` tối ưu; truy ngược từ `amount` về 0.

### Bài 3 — Đếm số cách đổi tiền

Đổi bài từ "ít đồng nhất" sang "có bao nhiêu **cách** đổi" một số tiền (không quan tâm thứ tự). Đây là biến thể DP đếm.

**Gợi ý:** `dp[a] += dp[a - coin]`, nhưng lặp `coin` ở vòng **ngoài** để không đếm trùng thứ tự — suy nghĩ kỹ vì sao.

### Bài 4 — Leo cầu thang

Có `n` bậc thang, mỗi bước leo 1 hoặc 2 bậc. Đếm số cách leo lên đỉnh. Nhận ra nó chính là Fibonacci.

**Gợi ý:** `ways[n] = ways[n-1] + ways[n-2]`; dùng tabulation `O(1)` bộ nhớ.

### Bài 5 — Longest common subsequence

Cho hai chuỗi, tìm độ dài dãy con chung dài nhất (không cần liên tiếp). Dùng DP hai chiều `dp[i][j]`.

**Gợi ý:** nếu ký tự bằng nhau `dp[i][j] = dp[i-1][j-1] + 1`; ngược lại `max(dp[i-1][j], dp[i][j-1])`; đây là nền của công cụ diff.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi nhận ra optimal substructure và overlapping subproblems trong một bài.
- [ ] Tôi biến được một đệ quy `O(2^n)` thành `O(n)` bằng memoization.
- [ ] Tôi viết được lời giải tabulation và tối ưu bộ nhớ khi có thể.
- [ ] Tôi giải được đổi tiền tối thiểu bằng DP và giải thích vì sao greedy sai.
- [ ] Tôi đọc và điền được một bảng DP, hiểu ý nghĩa từng ô.
- [ ] Tôi phân biệt được DP với greedy và backtracking.

Điều hướng:

- Bài prerequisite: [Backtracking](./16-backtracking.md)
- Ôn lại nền tảng: [Đệ quy và call stack](./02-de-quy-va-call-stack.md), [Greedy](./15-greedy.md)
- Bài tiếp theo: [Bài toán tổng hợp và chọn cấu trúc dữ liệu](./18-bai-toan-tong-hop-va-chon-cau-truc-du-lieu.md)
