# Greedy

## 1. Mục tiêu

Sau bài này, bạn có thể:

- mô tả greedy là chọn quyết định tốt nhất cục bộ ở mỗi bước;
- hiểu greedy không đúng cho mọi bài toán;
- giải interval scheduling;
- nhận biết greedy-choice property và optimal substructure ở mức trực giác;
- biết cách phản ví dụ một chiến lược greedy sai;
- liên hệ greedy với scheduling, MST và resource allocation.

## 2. Bài toán mở đầu

Một phòng học chỉ tổ chức được một lớp tại một thời điểm.

Các lớp:

```text
A: 09:00-10:00
B: 09:30-11:00
C: 10:00-11:00
D: 10:30-12:00
E: 11:00-12:00
```

Mục tiêu:

> chọn được nhiều lớp không overlap nhất.

Chiến lược đúng kinh điển:

> luôn chọn lớp kết thúc sớm nhất còn hợp lệ.

Đây là greedy.

## 3. Lời giải bằng code

```bash
mkdir GreedyDemo
cd GreedyDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

```csharp
namespace GreedyDemo;

public sealed record Session(
    string Name,
    int Start,
    int End);

internal static class Program
{
    private static void Main()
    {
        Session[] sessions =
        [
            new("A", 9, 10),
            new("B", 9, 11),
            new("C", 10, 11),
            new("D", 10, 12),
            new("E", 11, 12),
            new("F", 12, 13)
        ];

        IReadOnlyList<Session> selected =
            SelectMaximumNonOverlapping(sessions);

        foreach (Session session in selected)
        {
            Console.WriteLine(
                $"{session.Name}: {session.Start}:00-{session.End}:00");
        }
    }

    private static IReadOnlyList<Session>
        SelectMaximumNonOverlapping(IEnumerable<Session> sessions)
    {
        Session[] ordered = sessions
            .OrderBy(x => x.End)
            .ThenBy(x => x.Start)
            .ToArray();

        var result = new List<Session>();
        int lastEnd = int.MinValue;

        foreach (Session session in ordered)
        {
            if (session.Start < lastEnd)
            {
                continue;
            }

            result.Add(session);
            lastEnd = session.End;
        }

        return result;
    }
}
```

Một output:

```text
A: 9:00-10:00
C: 10:00-11:00
E: 11:00-12:00
F: 12:00-13:00
```

## 4. Giải thích cơ chế

### Quyết định cục bộ

Tại mỗi bước, chọn session kết thúc sớm nhất.

Lý do trực giác:

> kết thúc càng sớm thì càng để lại nhiều thời gian cho các session phía sau.

Sau khi chọn A kết thúc 10:

```text
loại mọi interval bắt đầu < 10
```

rồi lặp lại.

### Complexity

Sort theo end:

```text
O(n log n)
```

Scan chọn interval:

```text
O(n)
```

Tổng:

```text
O(n log n)
```

### Vì sao “chọn interval ngắn nhất” không chắc đúng

Greedy cần **quy tắc đã được chứng minh**, không phải intuition ngẫu nhiên.

Một interval rất ngắn nhưng nằm giữa có thể chặn hai interval khác.

Do đó mỗi heuristic phải được kiểm tra bằng proof hoặc counterexample.

## 5. Kiến thức nền

### Greedy-choice property

Bài toán có thể chọn một quyết định cục bộ tối ưu và vẫn tồn tại nghiệm tối ưu chứa quyết định đó.

Interval scheduling có tính chất này với “finish earliest”.

### Optimal substructure

Sau khi chọn một interval, phần bài toán còn lại vẫn là:

> chọn nhiều interval không overlap nhất từ các interval bắt đầu sau thời điểm mới.

Cấu trúc bài toán lặp lại.

### Greedy và DP

Cả hai thường tận dụng optimal substructure.

Khác biệt:

- greedy chốt lựa chọn và không quay lại;
- DP lưu/so sánh nhiều trạng thái trước khi quyết định.

Nếu greedy-choice property không có, DP có thể cần thiết.

### Greedy trong thuật toán đã học

- Dijkstra: chọn distance nhỏ nhất chưa xử lý dưới điều kiện weight không âm;
- Prim/Kruskal: chọn edge theo nguyên tắc greedy có chứng minh;
- interval scheduling.

## 6. Lỗi thường gặp

### Thấy tối ưu là dùng greedy

Không phải bài tối ưu nào cũng greedy.

### Không tìm counterexample

Một cách kiểm tra heuristic rất hữu ích:

> cố tạo input nhỏ làm nó thất bại.

### Chọn theo start sớm nhất

Start sớm nhưng end rất muộn có thể chặn nhiều interval.

### Nhầm interval scheduling với weighted interval scheduling

Nếu mỗi interval có profit khác nhau và mục tiêu tối đa profit, greedy finish-earliest không còn đủ. Bài đó thường dẫn tới dynamic programming.

## 7. Bài tập

### Bài 1 — Counterexample

Tạo input làm chiến lược “chọn interval bắt đầu sớm nhất” thất bại.

### Bài 2 — Minimum coins

Với coin chuẩn:

```text
1, 5, 10, 25
```

thử greedy lấy coin lớn nhất trước.

Sau đó tìm hệ coin mà greedy sai, ví dụ:

```text
1, 3, 4
```

cho amount 6.

### Bài 3 — Job scheduling

Mỗi job có deadline và profit, mỗi job dài 1 slot. Nghiên cứu chiến lược greedy.

### Bài 4 — Fractional knapsack

Giải bằng value/weight ratio.

Giải thích vì sao 0/1 knapsack khác.

### Bài 5 — Proof sketch

Viết exchange argument ngắn cho interval scheduling finish-earliest.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi hiểu greedy là quyết định cục bộ.
- [ ] Tôi không áp dụng greedy nếu chưa có lý do đúng.
- [ ] Tôi giải được interval scheduling.
- [ ] Tôi biết dùng counterexample để bác heuristic.
- [ ] Tôi phân biệt greedy và DP.
- [ ] Tôi nhận ra weighted version có thể đổi bản chất bài toán.

Điều hướng:

- Bài trước: [Searching](./14-searching.md)
- Bài tiếp theo: [Backtracking](./16-backtracking.md)
