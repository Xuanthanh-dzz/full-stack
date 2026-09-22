# Greedy

## 1. Mục tiêu

Sau bài này, bạn có thể:

- mô tả tư duy **greedy**: mỗi bước chọn phương án tốt nhất **tại chỗ**, không tính đường dài;
- nhận ra khi nào greedy cho lời giải **tối ưu toàn cục** và khi nào không;
- cài đặt đổi tiền tham lam và chọn hoạt động (interval scheduling);
- chỉ ra một phản ví dụ nơi greedy **thất bại** và giải thích vì sao;
- phát biểu hai điều kiện để greedy đúng: greedy-choice property và optimal substructure;
- phân biệt greedy với quy hoạch động (bài [17](./17-dynamic-programming.md)).

## 2. Bài toán mở đầu

Bạn ra siêu thị, cần trả lại **87.000đ** tiền thừa bằng **ít tờ nhất**. Trực giác ai cũng làm: đưa tờ lớn nhất có thể trước (50.000), rồi tiếp tục với phần còn lại (20.000, 10.000...). Đó là **greedy** — mỗi bước chọn cái tốt nhất trước mắt mà không lo tính toàn cục.

Với tiền Việt Nam, cách này **luôn** cho số tờ ít nhất. Nhưng đây là chỗ nguy hiểm: greedy **không phải lúc nào cũng đúng**. Đổi 6 đồng với bộ mệnh giá kỳ lạ `[4, 3, 1]`, greedy đưa `4 + 1 + 1` = 3 đồng, trong khi tối ưu thật là `3 + 3` = 2 đồng. Cùng một thuật toán, một bộ dữ liệu đúng, một bộ sai.

Greedy vừa mạnh (đơn giản, nhanh) vừa nguy hiểm (dễ sai mà không hay). Bài này dạy cả hai mặt: khi nào tin greedy, khi nào phải cảnh giác.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `GreedyDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace GreedyDemo;

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine("== Đổi tiền tham lam: luôn lấy đồng lớn nhất còn dùng được ==");
        int[] vnd = { 50000, 20000, 10000, 5000, 1000 };
        int amount = 87000;
        var used = GreedyCoinChange(vnd, amount);
        Console.WriteLine($"Đổi {amount} với mệnh giá [{string.Join(", ", vnd)}]:");
        Console.WriteLine($"  {string.Join(" + ", used)} = {used.Sum()} ({used.Count} tờ)");

        Console.WriteLine();
        Console.WriteLine("== Nhưng tham lam KHÔNG luôn tối ưu ==");
        int[] weird = { 4, 3, 1 };
        int target = 6;
        var greedy = GreedyCoinChange(weird, target);
        Console.WriteLine($"Đổi {target} với mệnh giá [{string.Join(", ", weird)}]:");
        Console.WriteLine($"  Tham lam: {string.Join(" + ", greedy)} = {greedy.Count} đồng");
        Console.WriteLine($"  Tối ưu thật: 3 + 3 = 2 đồng  -> tham lam thua!");

        Console.WriteLine();
        Console.WriteLine("== Chọn hoạt động: nhiều cuộc họp nhất không chồng giờ ==");
        var meetings = new (string Name, int Start, int End)[]
        {
            ("A", 1, 4), ("B", 3, 5), ("C", 0, 6), ("D", 5, 7),
            ("E", 3, 9), ("F", 5, 9), ("G", 6, 10), ("H", 8, 11)
        };
        var chosen = SelectActivities(meetings);
        Console.WriteLine("Chọn theo giờ KẾT THÚC sớm nhất (tham lam, chứng minh được tối ưu):");
        Console.WriteLine($"  {string.Join(", ", chosen.Select(m => $"{m.Name}[{m.Start}-{m.End}]"))}");
        Console.WriteLine($"  Tổng: {chosen.Count} cuộc họp");
    }

    // Tham lam: sắp mệnh giá giảm dần, lấy nhiều nhất có thể mỗi loại.
    private static List<int> GreedyCoinChange(int[] coins, int amount)
    {
        var used = new List<int>();
        foreach (int coin in coins.OrderByDescending(c => c))
        {
            while (amount >= coin)
            {
                used.Add(coin);
                amount -= coin;
            }
        }
        return used;
    }

    // Tham lam: sắp theo giờ kết thúc, chọn cuộc nào bắt đầu sau cuộc vừa chọn.
    private static List<(string Name, int Start, int End)> SelectActivities(
        (string Name, int Start, int End)[] items)
    {
        var chosen = new List<(string, int, int)>();
        int lastEnd = int.MinValue;
        foreach (var m in items.OrderBy(x => x.End))
        {
            if (m.Start >= lastEnd) // không chồng cuộc trước
            {
                chosen.Add((m.Name, m.Start, m.End));
                lastEnd = m.End;
            }
        }
        return chosen;
    }
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
== Đổi tiền tham lam: luôn lấy đồng lớn nhất còn dùng được ==
Đổi 87000 với mệnh giá [50000, 20000, 10000, 5000, 1000]:
  50000 + 20000 + 10000 + 5000 + 1000 + 1000 = 87000 (6 tờ)

== Nhưng tham lam KHÔNG luôn tối ưu ==
Đổi 6 với mệnh giá [4, 3, 1]:
  Tham lam: 4 + 1 + 1 = 3 đồng
  Tối ưu thật: 3 + 3 = 2 đồng  -> tham lam thua!

== Chọn hoạt động: nhiều cuộc họp nhất không chồng giờ ==
Chọn theo giờ KẾT THÚC sớm nhất (tham lam, chứng minh được tối ưu):
  A[1-4], D[5-7], H[8-11]
  Tổng: 3 cuộc họp
```

## 4. Giải thích cơ chế

### 4.1 Khuôn tư duy greedy

Thuật toán greedy xây lời giải theo từng bước, mỗi bước **cam kết** một lựa chọn tốt nhất tại chỗ và **không bao giờ xem lại**. `GreedyCoinChange` sắp mệnh giá giảm dần rồi lấy nhiều nhất có thể ở mỗi loại. Không quay lui, không thử phương án khác — nên nó rất nhanh, thường `O(n log n)` (chi phí sắp xếp) hoặc `O(n)`.

Điểm hấp dẫn: greedy đơn giản đến mức trực giác. Điểm nguy hiểm: sự "không xem lại" đó khiến nó có thể bỏ lỡ lời giải tốt hơn cần hy sinh ở bước đầu.

### 4.2 Vì sao greedy thắng với tiền VND nhưng thua với `[4, 3, 1]`

Đổi tiền tham lam đúng khi bộ mệnh giá là **canonical** — mỗi đồng lớn "chứa gọn" các đồng nhỏ (như tiền thật: 50.000 = 5×10.000). Khi đó lấy đồng lớn nhất không bao giờ khiến phần còn lại phải dùng nhiều đồng hơn.

Bộ `[4, 3, 1]` phá vỡ điều đó. Đổi 6: greedy lấy `4` trước (tham lam), còn lại `2` phải trả bằng `1 + 1` → 3 đồng. Nhưng nếu **hy sinh** đồng 4, dùng `3 + 3` thì chỉ 2 đồng. Greedy thất bại vì lựa chọn tốt nhất tại chỗ (lấy 4) lại **chặn** đường tới lời giải tối ưu toàn cục. Đây là bài học cốt lõi: greedy đúng hay sai **tùy bài toán và dữ liệu**, phải chứng minh chứ không được mặc định.

### 4.3 Chọn hoạt động: một greedy đúng có chứng minh

Bài "nhiều cuộc họp nhất không chồng giờ" là ví dụ greedy **luôn** tối ưu. Chiến lược: sắp theo **giờ kết thúc** tăng dần, luôn chọn cuộc kết thúc sớm nhất còn không chồng cuộc đã chọn. Kết quả `A[1-4], D[5-7], H[8-11]` — 3 cuộc.

Vì sao chọn theo giờ kết thúc (không phải giờ bắt đầu, hay cuộc ngắn nhất)? Chọn cuộc kết thúc **sớm nhất** để lại **nhiều thời gian nhất** cho các cuộc sau — nên không bao giờ thiệt. Có thể chứng minh chặt: bất kỳ lời giải tối ưu nào cũng có thể "đổi" cuộc đầu của nó bằng cuộc kết thúc sớm nhất mà không giảm số cuộc. Đây gọi là **exchange argument** — cách chuẩn để chứng minh một greedy đúng.

### 4.4 Chọn tiêu chí greedy nào?

Cùng một bài, đổi **tiêu chí tham lam** cho kết quả khác nhau, và đa số tiêu chí là **sai**. Với chọn hoạt động: chọn theo giờ bắt đầu sớm nhất — sai (một cuộc bắt đầu sớm nhưng rất dài chiếm hết chỗ); chọn cuộc ngắn nhất — cũng sai (một cuộc ngắn nằm giữa có thể cắt hai cuộc khác). Chỉ "giờ kết thúc sớm nhất" mới đúng. Chọn đúng tiêu chí và **chứng minh** nó là phần khó nhất của thiết kế greedy.

### Đào sâu (có thể quay lại sau)

- **Hai điều kiện để greedy đúng.** (1) **Greedy-choice property**: có một lựa chọn tối ưu tại chỗ dẫn tới lời giải tối ưu toàn cục. (2) **Optimal substructure**: lời giải tối ưu của bài lớn chứa lời giải tối ưu của bài con. Đổi tiền `[4,3,1]` thiếu điều kiện (1) nên greedy sai.
- **Khi greedy sai, dùng gì.** Nếu bài có optimal substructure nhưng thiếu greedy-choice, thường phải **quy hoạch động** (bài [17](./17-dynamic-programming.md)) — thử mọi lựa chọn và nhớ kết quả. Đổi tiền tổng quát chính là bài DP kinh điển.
- **Các greedy nổi tiếng đúng.** Dijkstra và Prim (bài [12](./12-shortest-path-va-minimum-spanning-tree.md)) là thuật toán greedy có chứng minh. Mã hóa Huffman (nén dữ liệu) cũng greedy. Điểm chung: đều chứng minh được greedy-choice property.
- **Xấp xỉ.** Ngay cả khi greedy không cho tối ưu, đôi khi nó cho lời giải "đủ tốt" nhanh chóng (approximation) — hữu ích cho bài NP-khó nơi tối ưu tuyệt đối là bất khả thi.

## 5. Kiến thức nền

### Dấu hiệu một bài có thể giải bằng greedy

- Có thể xây lời giải **từng bước**, mỗi bước một quyết định.
- Có một **tiêu chí sắp xếp/ưu tiên** tự nhiên (giờ kết thúc, trọng số, tỉ lệ giá trị/khối lượng).
- Quyết định sớm **không cần** xem lại khi biết thông tin sau.

Nhưng dấu hiệu chỉ là gợi ý — luôn kiểm tra bằng phản ví dụ trước khi tin.

### Greedy so với quy hoạch động

| Tiêu chí | Greedy | Quy hoạch động |
|---|---|---|
| Quyết định | chọn một lần, không xem lại | thử mọi khả năng, nhớ lại |
| Tốc độ | nhanh (`O(n log n)` thường) | chậm hơn (`O(n·m)`...) |
| Đúng khi | có greedy-choice property | chỉ cần optimal substructure |
| Rủi ro | dễ sai nếu không chứng minh | đúng nhưng tốn hơn |

Greedy là "cược" rằng lựa chọn tại chỗ luôn đúng; DP "chắc ăn" bằng cách xét hết. Khi nghi ngờ greedy, hãy nghĩ tới DP.

### Cách kiểm tra một greedy

1. **Tìm phản ví dụ** — thử vài bộ dữ liệu nhỏ, đặc biệt các trường hợp "lệch" như `[4,3,1]`. Một phản ví dụ đủ để bác bỏ.
2. **Chứng minh** nếu không tìm được phản ví dụ — dùng exchange argument hoặc quy nạp.
3. **Đối chiếu với brute-force** trên dữ liệu nhỏ — chạy cả hai và so kết quả.

## 6. Lỗi thường gặp

### Mặc định greedy luôn đúng

Bẫy lớn nhất. `[4,3,1]` cho thấy greedy có thể sai mà không báo lỗi — chỉ cho đáp án tệ hơn. Luôn kiểm tra bằng phản ví dụ hoặc chứng minh trước khi dùng greedy cho bài quan trọng.

### Chọn nhầm tiêu chí tham lam

Với chọn hoạt động, "giờ bắt đầu sớm nhất" hay "cuộc ngắn nhất" đều sai; chỉ "giờ kết thúc sớm nhất" đúng. Tiêu chí sai làm greedy sai dù ý tưởng tổng thể đúng.

### Không phân biệt greedy đúng và greedy xấp xỉ

Một số bài (như knapsack 0/1) không có greedy tối ưu; greedy chỉ cho xấp xỉ. Nhầm xấp xỉ thành tối ưu dẫn tới kết luận sai về tính đúng đắn.

### Quên sắp xếp trước

Nhiều greedy cần dữ liệu đã sắp theo tiêu chí (giảm dần mệnh giá, tăng dần giờ kết thúc). Bỏ bước sắp xếp làm sai toàn bộ.

### Áp greedy cho bài cần xem lại quyết định

Nếu quyết định sớm phụ thuộc thông tin chỉ biết sau, greedy (không xem lại) sẽ sai. Đó là dấu hiệu cần DP hoặc backtracking (bài [16](./16-backtracking.md)).

## 7. Bài tập

### Bài 1 — Kiểm tra bộ mệnh giá canonical

Viết hàm so kết quả greedy với brute-force (thử mọi tổ hợp) trên các số tiền `1..30` cho một bộ mệnh giá. In ra số tiền đầu tiên mà greedy khác tối ưu (hoặc "canonical" nếu không có).

**Gợi ý:** brute-force nhỏ có thể dùng đệ quy thử mọi đồng; đây là cách phát hiện bộ mệnh giá phá greedy.

### Bài 2 — Chọn tiêu chí sai

Cài lại `SelectActivities` chọn theo **giờ bắt đầu sớm nhất** và tìm một bộ dữ liệu mà nó cho ít cuộc hơn cách đúng.

**Gợi ý:** một cuộc bắt đầu lúc 0 nhưng kéo dài tới 10 sẽ chặn mọi cuộc khác.

### Bài 3 — Phân đoạn xăng

Xe cần đi qua các trạm xăng cách nhau, mỗi lần đổ đầy đi được `D` km. Tìm số lần đổ ít nhất bằng greedy (đi xa nhất có thể trước khi buộc phải đổ).

**Gợi ý:** greedy đúng ở đây — chứng minh bằng exchange: đổ muộn nhất có thể không bao giờ thiệt.

### Bài 4 — Fractional knapsack

Cho các món có giá trị và khối lượng, ba lô chịu tải `W`, **được phép lấy một phần** món. Tối đa hóa giá trị bằng greedy theo tỉ lệ giá trị/khối lượng.

**Gợi ý:** fractional knapsack có greedy tối ưu (khác 0/1 knapsack); sắp theo tỉ lệ giảm dần, lấy đầy dần.

### Bài 5 — Nối dây chi phí nhỏ nhất

Cho `n` đoạn dây độ dài khác nhau, mỗi lần nối hai đoạn tốn chi phí bằng tổng độ dài. Nối tất cả thành một với tổng chi phí nhỏ nhất.

**Gợi ý:** luôn nối **hai đoạn ngắn nhất** trước — dùng min-heap (bài [08](./08-heap-va-priority-queue.md)); đây là greedy đúng, họ hàng với mã Huffman.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi mô tả được khuôn greedy: chọn tốt nhất tại chỗ, không xem lại.
- [ ] Tôi cài được đổi tiền tham lam và chọn hoạt động.
- [ ] Tôi chỉ ra được phản ví dụ nơi greedy thất bại và giải thích vì sao.
- [ ] Tôi biết chọn đúng tiêu chí tham lam quan trọng thế nào.
- [ ] Tôi phát biểu được greedy-choice property và optimal substructure.
- [ ] Tôi biết khi nào chuyển từ greedy sang quy hoạch động.

Điều hướng:

- Bài prerequisite: [Searching](./14-searching.md)
- Ôn lại nền tảng: [Sorting](./13-sorting.md), [Heap và priority queue](./08-heap-va-priority-queue.md)
- Bài tiếp theo: [Backtracking](./16-backtracking.md)
