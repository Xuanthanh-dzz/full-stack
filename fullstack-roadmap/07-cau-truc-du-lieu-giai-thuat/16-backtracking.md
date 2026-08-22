# Backtracking

## 1. Mục tiêu

Sau bài này, bạn có thể:

- mô tả tư duy **backtracking**: xây lời giải từng bước, **lùi lại** khi bế tắc;
- cài đặt sinh hoán vị và giải N-Queens bằng đệ quy có quay lui;
- nhận ra mẫu hình "chọn → đệ quy → gỡ lựa chọn" trong code;
- dùng **cắt nhánh (pruning)** để bỏ sớm các nhánh không thể dẫn tới lời giải;
- giải thích vì sao backtracking là DFS trên **cây không gian lời giải**;
- ước lượng độ phức tạp và biết khi nào backtracking khả thi, khi nào không.

## 2. Bài toán mở đầu

Đặt **8 quân hậu** lên bàn cờ 8×8 sao cho không quân nào ăn quân nào (không cùng hàng, cột, đường chéo). Thử mọi cách đặt là `64 chọn 8` ≈ 4,4 tỉ khả năng — quá nhiều để duyệt hết.

Nhưng đa số cách đặt sai **ngay từ vài quân đầu**: nếu hai quân đầu đã ăn nhau, mọi cách đặt các quân còn lại đều vô ích — không cần thử. **Backtracking** khai thác đúng điều đó: xây lời giải dần dần, và **ngay khi** một phần lời giải trở nên bất khả thi thì **lùi lại** thử hướng khác, cắt bỏ cả một nhánh khổng lồ. Nhờ vậy N-Queens chạy được cho tới N khá lớn.

Backtracking là "brute-force có kỷ luật": vẫn duyệt không gian lời giải, nhưng bỏ sớm những nhánh chết. Đây là kỹ thuật nền cho vô số bài tổ hợp: hoán vị, tập con, tô màu đồ thị, Sudoku, giải mê cung.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `BacktrackingDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace BacktrackingDemo;

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine("== Sinh mọi hoán vị của [1,2,3] bằng backtracking ==");
        var perms = new List<string>();
        Permute(new[] { 1, 2, 3 }, new List<int>(), new bool[3], perms);
        foreach (string p in perms)
        {
            Console.WriteLine($"  {p}");
        }
        Console.WriteLine($"Tổng: {perms.Count} hoán vị (= 3!)");

        Console.WriteLine();
        Console.WriteLine("== N-Queens: đặt N hậu không ăn nhau (N=4) ==");
        var boards = new List<int[]>();
        SolveQueens(4, 0, new int[4], boards);
        Console.WriteLine($"Có {boards.Count} lời giải cho N=4:");
        foreach (int[] board in boards)
        {
            PrintBoard(board);
            Console.WriteLine();
        }

        Console.WriteLine("== Số lời giải N-Queens theo N (nhờ cắt nhánh nên chạy được) ==");
        foreach (int n in new[] { 4, 5, 6, 7, 8 })
        {
            var sols = new List<int[]>();
            SolveQueens(n, 0, new int[n], sols);
            Console.WriteLine($"  N={n}: {sols.Count} lời giải");
        }
    }

    // Backtracking: thử từng số chưa dùng cho vị trí hiện tại, rồi lùi lại.
    private static void Permute(int[] items, List<int> current, bool[] used, List<string> results)
    {
        if (current.Count == items.Length)
        {
            results.Add(string.Join("", current)); // lời giải hoàn chỉnh
            return;
        }
        for (int i = 0; i < items.Length; i++)
        {
            if (used[i]) continue;
            used[i] = true;
            current.Add(items[i]);   // chọn
            Permute(items, current, used, results);
            current.RemoveAt(current.Count - 1); // lùi (backtrack)
            used[i] = false;
        }
    }

    // Đặt hậu theo từng cột; board[c] = hàng của hậu ở cột c.
    private static void SolveQueens(int n, int col, int[] board, List<int[]> results)
    {
        if (col == n)
        {
            results.Add((int[])board.Clone()); // đủ n hậu
            return;
        }
        for (int row = 0; row < n; row++)
        {
            if (IsSafe(board, col, row))
            {
                board[col] = row;                 // đặt hậu
                SolveQueens(n, col + 1, board, results);
                // không cần "gỡ" vì ô sẽ bị ghi đè ở lần thử sau
            }
        }
    }

    // Cắt nhánh: hậu mới có bị hậu nào ở cột trước ăn không?
    private static bool IsSafe(int[] board, int col, int row)
    {
        for (int c = 0; c < col; c++)
        {
            int r = board[c];
            if (r == row) return false;                     // cùng hàng
            if (Math.Abs(r - row) == Math.Abs(c - col)) return false; // cùng đường chéo
        }
        return true;
    }

    private static void PrintBoard(int[] board)
    {
        int n = board.Length;
        for (int r = 0; r < n; r++)
        {
            var cells = new char[n];
            for (int c = 0; c < n; c++)
            {
                cells[c] = board[c] == r ? 'Q' : '.';
            }
            Console.WriteLine("  " + string.Join(' ', cells));
        }
    }
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
== Sinh mọi hoán vị của [1,2,3] bằng backtracking ==
  123
  132
  213
  231
  312
  321
Tổng: 6 hoán vị (= 3!)

== N-Queens: đặt N hậu không ăn nhau (N=4) ==
Có 2 lời giải cho N=4:
  . . Q .
  Q . . .
  . . . Q
  . Q . .

  . Q . .
  . . . Q
  Q . . .
  . . Q .

== Số lời giải N-Queens theo N (nhờ cắt nhánh nên chạy được) ==
  N=4: 2 lời giải
  N=5: 10 lời giải
  N=6: 4 lời giải
  N=7: 40 lời giải
  N=8: 92 lời giải
```

## 4. Giải thích cơ chế

### 4.1 Mẫu hình "chọn → đệ quy → gỡ"

Trái tim của mọi backtracking là ba dòng trong `Permute`:

```csharp
current.Add(items[i]);            // 1. CHỌN: cam kết một lựa chọn
Permute(...);                     // 2. ĐỆ QUY: giải phần còn lại với lựa chọn đó
current.RemoveAt(current.Count-1); // 3. GỠ: rút lại lựa chọn để thử cái khác
```

Bước "gỡ" chính là **backtrack**: sau khi khám phá hết mọi khả năng bắt đầu bằng một lựa chọn, ta **hoàn tác** nó để trạng thái sạch cho lựa chọn kế tiếp. Sinh hoán vị `[1,2,3]`: chọn 1, rồi đệ quy chọn 2, rồi 3 → "123"; gỡ 3, gỡ 2, thử 3 trước → "132"; cứ thế cho đủ 6 hoán vị. Mảng `used` đánh dấu số đã dùng để không lặp.

### 4.2 Cây không gian lời giải và DFS

Backtracking chính là **DFS** (bài [11](./11-bfs-va-dfs.md)) trên một **cây các trạng thái**: gốc là lời giải rỗng, mỗi cạnh là một lựa chọn, lá là lời giải hoàn chỉnh (hoặc ngõ cụt).

```text
                (rỗng)
          1/      2|      3\
        (1)       (2)      (3)
       2/ 3\     1/ 3\    ...
     (12)(13) (21)(23)
      3|   2|   3|   1|
    (123)(132)(213)(231) ...
```

"Đi sâu" là chọn thêm một phần tử; "lùi" là quay lên node cha thử nhánh khác. Chính vì là DFS, backtracking dùng call stack (đệ quy) và bộ nhớ chỉ `O(chiều sâu)`.

### 4.3 Cắt nhánh (pruning) — thứ làm backtracking khả thi

N-Queens cho thấy sức mạnh của cắt nhánh. Hàm `IsSafe` kiểm tra **trước khi** đặt hậu: nếu vị trí này bị một hậu ở cột trước ăn, ta **không** đi vào nhánh đó chút nào. Nhờ vậy, thay vì duyệt hàng tỉ cách đặt, thuật toán bỏ ngay các nhánh chết từ gốc.

Xét N=4: đặt hậu cột 0 ở hàng 0, thử cột 1 — hàng 0 (cùng hàng, bỏ), hàng 1 (chéo, bỏ), hàng 2 (an toàn, đi tiếp)... Mỗi lần `IsSafe` trả `false` là **cắt** cả một cây con. Đó là lý do N-Queens chạy tới N=8 (92 lời giải) trong tích tắc, dù không gian thô là hàng tỉ. Không có pruning, backtracking chỉ là brute-force mũ.

### 4.4 Vì sao N-Queens không cần "gỡ" tường minh

Trong `Permute` ta gỡ lựa chọn rõ ràng, còn `SolveQueens` thì không có dòng gỡ. Lý do: `board[col] = row` sẽ bị **ghi đè** ở lần lặp `row` kế tiếp, và các cột `>= col` chưa được đọc cho tới khi đặt lại. Trạng thái tự làm sạch nhờ cách lưu. Đây là biến thể hợp lệ — điều quan trọng là **trạng thái đúng** khi thử nhánh mới, dù bằng gỡ tường minh hay ghi đè.

### Đào sâu (có thể quay lại sau)

- **Độ phức tạp.** Không có pruning, sinh hoán vị là `O(n! · n)`, tập con là `O(2^n)`, N-Queens là mũ. Pruning không đổi Big-O worst case nhưng cắt hằng số khổng lồ trong thực tế, biến bài "bất khả thi" thành "chạy được cho n vừa phải".
- **Ràng buộc mạnh hơn, cắt sớm hơn.** Chất lượng backtracking phụ thuộc việc phát hiện bế tắc **sớm** cỡ nào. N-Queens tối ưu dùng ba mảng đánh dấu (hàng, chéo chính, chéo phụ) để `IsSafe` là `O(1)` thay vì `O(col)`.
- **Backtracking so với DP.** Cả hai khám phá không gian lời giải, nhưng DP (bài [17](./17-dynamic-programming.md)) **nhớ lại** kết quả bài con trùng lặp, còn backtracking thường liệt kê/tìm cấu hình không trùng lặp. Khi các nhánh chồng bài con, DP thắng; khi cần liệt kê mọi cấu hình hợp lệ, backtracking là đúng.
- **Cắt theo cận (branch and bound).** Với bài tối ưu (không chỉ liệt kê), ta còn cắt nhánh nếu **cận trên tốt nhất** của nhánh đó tệ hơn lời giải đã tìm — kỹ thuật branch and bound, dùng cho knapsack, TSP.

## 5. Kiến thức nền

### Khung chung của backtracking

```text
giải(trạng_thái):
    nếu trạng_thái là lời giải hoàn chỉnh: ghi nhận, return
    với mỗi lựa_chọn hợp lệ từ trạng_thái:
        nếu lựa_chọn khả thi (pruning):
            áp dụng lựa_chọn
            giải(trạng_thái mới)
            gỡ lựa_chọn      # backtrack
```

Ba câu hỏi khi thiết kế: (1) khi nào là lời giải hoàn chỉnh? (2) các lựa chọn tại mỗi bước là gì? (3) **điều kiện cắt** — khi nào biết chắc một phần lời giải là ngõ cụt?

### Các bài kinh điển

| Bài | Lựa chọn mỗi bước | Điều kiện cắt |
|---|---|---|
| Hoán vị | phần tử chưa dùng | (đủ n phần tử) |
| Tập con | lấy/không lấy phần tử `i` | — |
| N-Queens | hàng đặt hậu cột này | không bị ăn |
| Sudoku | số điền vào ô trống | hợp lệ hàng/cột/khối |
| Tô màu đồ thị | màu cho đỉnh này | khác màu hàng xóm |

### Backtracking là DFS trên không gian trừu tượng

Nắm vững bài [11 — DFS](./11-bfs-va-dfs.md) là hiểu ngay backtracking: chỉ khác là "đồ thị" ở đây là cây trạng thái **sinh ra khi chạy** (không lưu sẵn), và ta thêm bước gỡ để tái dùng bộ nhớ. Cùng một ý tưởng đi-sâu-rồi-lùi.

## 6. Lỗi thường gặp

### Quên gỡ lựa chọn (backtrack)

Nếu áp lựa chọn nhưng không hoàn tác trước khi thử cái khác, trạng thái "rò" sang nhánh kế và cho kết quả sai. Mọi thay đổi trạng thái phải được đối xứng bằng một bước gỡ (trừ khi tự ghi đè như N-Queens).

### Không cắt nhánh

Bỏ điều kiện pruning biến backtracking thành brute-force thuần, thường chậm tới mức vô dụng. Luôn tìm cách phát hiện ngõ cụt càng sớm càng tốt.

### Chia sẻ trạng thái sai giữa các nhánh

Thêm lời giải vào kết quả bằng **tham chiếu** tới mảng đang sửa (thay vì `Clone`) khiến mọi lời giải trỏ cùng một mảng bị ghi đè. `SolveQueens` phải `board.Clone()` khi lưu.

### Đệ quy quá sâu

Với `n` lớn, độ sâu đệ quy có thể gây tràn stack. Bản thân số lời giải cũng có thể bùng nổ mũ — kiểm tra khả thi trước khi chạy với `n` lớn.

### Nhầm backtracking với bài cần DP

Nếu các nhánh **tính lại** cùng bài con (như đếm số cách), backtracking thuần sẽ chậm mũ; đó là dấu hiệu cần memoization/DP (bài [17](./17-dynamic-programming.md)).

## 7. Bài tập

### Bài 1 — Sinh mọi tập con

Viết hàm sinh mọi tập con của `[1,2,3]` (8 tập, gồm tập rỗng) bằng backtracking "lấy hoặc không lấy" mỗi phần tử.

**Gợi ý:** ở mỗi phần tử, phân nhánh hai hướng; lá là một tập con hoàn chỉnh — số lá là `2^n`.

### Bài 2 — Tổ hợp `C(n, k)`

Sinh mọi cách chọn `k` phần tử từ `n` (không quan tâm thứ tự). Với `n=4, k=2` phải ra 6 tổ hợp.

**Gợi ý:** truyền chỉ số bắt đầu để tránh lặp và trùng; cắt khi số phần tử còn lại không đủ đạt `k`.

### Bài 3 — Giải mê cung

Cho lưới 0/1 (1 là tường), tìm một đường từ góc trên-trái tới góc dưới-phải bằng backtracking bốn hướng.

**Gợi ý:** đánh dấu ô đã thăm để tránh vòng; gỡ dấu khi lùi để ô còn dùng được cho đường khác.

### Bài 4 — N-Queens tối ưu `O(1)` kiểm tra

Thay `IsSafe` `O(col)` bằng ba mảng `bool` đánh dấu hàng, đường chéo chính (`row+col`), đường chéo phụ (`row-col+n`) đã bị chiếm. Đo tốc độ cải thiện cho N=10, 11.

**Gợi ý:** đặt/gỡ ba dấu quanh lời gọi đệ quy — đây là backtracking có gỡ tường minh.

### Bài 5 — Sudoku

Cài trình giải Sudoku 9×9: tìm ô trống, thử 1–9 hợp lệ, đệ quy, lùi nếu bế tắc.

**Gợi ý:** hàm hợp lệ kiểm tra hàng, cột, khối 3×3; chọn ô trống có ít lựa chọn nhất trước để cắt nhánh mạnh hơn (heuristic MRV).

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi mô tả được khuôn "chọn → đệ quy → gỡ" của backtracking.
- [ ] Tôi cài được sinh hoán vị và giải N-Queens.
- [ ] Tôi giải thích được backtracking là DFS trên cây không gian lời giải.
- [ ] Tôi dùng cắt nhánh để bỏ sớm nhánh chết và biết vì sao nó quan trọng.
- [ ] Tôi `Clone` trạng thái khi lưu lời giải để tránh chia sẻ tham chiếu.
- [ ] Tôi nhận ra khi nào bài cần DP thay vì backtracking thuần.

Điều hướng:

- Bài prerequisite: [Greedy](./15-greedy.md)
- Ôn lại nền tảng: [Đệ quy và call stack](./02-de-quy-va-call-stack.md), [BFS và DFS](./11-bfs-va-dfs.md)
- Bài tiếp theo: [Dynamic programming](./17-dynamic-programming.md)
