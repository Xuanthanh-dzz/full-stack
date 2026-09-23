# Greedy

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- Greedy chọn tốt nhất theo tiêu chí cục bộ và cần lập luận để đúng toàn cục.
- Bài chọn nhiều cuộc họp nhất dùng thời điểm kết thúc sớm nhất.
- Không chuyển tiêu chí ấy sang lợi nhuận hoặc ràng buộc khác mà không chứng minh.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- mô tả greedy là chọn quyết định tốt nhất cục bộ ở mỗi bước;
- hiểu greedy không đúng cho mọi bài toán;
- giải interval scheduling;
- nhận biết greedy-choice property và optimal substructure ở mức trực giác;
- biết cách phản ví dụ một chiến lược greedy sai;
- liên hệ greedy với scheduling, MST và resource allocation.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Chọn cuộc họp kết thúc sớm để chừa nhiều thời gian cho phần còn lại. Ý tưởng có lý nhưng phải chứng minh đổi cuộc họp đầu của một lời giải tối ưu sang lựa chọn này không làm giảm số cuộc họp.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| greedy | chọn cục bộ rồi không quay lại | earliest finish |
| exchange argument | đổi một lựa chọn mà không làm lời giải tệ hơn | thay cuộc họp đầu |
| half-open interval | gồm đầu nhưng không gồm cuối | [9,10) nối được [10,11) |

### Ví dụ nhỏ — tính tay trước

A[9,10),B[9,12),C[10,11) →chọn A,C. Giờ trong code là mốc int rời rạc; lịch 09:30 cần đổi sang phút hoặc kiểu thời gian trước.

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

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```bash
mkdir GreedyDemo
cd GreedyDemo
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
        ArgumentNullException.ThrowIfNull(sessions);
        Session[] input = sessions.ToArray();
        foreach (Session session in input)
        {
            ArgumentNullException.ThrowIfNull(session);
            if (session.End <= session.Start)
                throw new ArgumentException("Sessions must have positive duration.", nameof(sessions));
        }

        Session[] ordered = input
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

### Walkthrough — execution / state / cost

1. Materialize input một lần và chặn interval có End<=Start.
2. Sort theo End, quét lần lượt, nhận khi Start>=lastEnd.
3. Giữ danh sách đã nhận và mốc kết thúc cuối; không sửa input array.
4. Sort O(n log n), scan O(n), bộ nhớ O(n). Tối ưu số lượng, không tối ưu tổng tiền hay mức ưu tiên.

### Mini-check

Với B trả 100 và A,C mỗi cuộc trả 1, greedy hiện tại tối ưu đại lượng nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| earliest finish | tối đa số interval không giao | có exchange argument |
| highest profit first | bài có trọng số | không tự đúng |
| dynamic programming | cần xét nhiều phương án liên quan | thêm state khi greedy không có chứng minh |

### Misconception check

**Đúng hay sai?** Cuộc họp ngắn nhất luôn là lựa chọn đúng.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: có thể chắn hai cuộc họp khác.

</details>

**Đúng hay sai?** Kết thúc10 và bắt đầu10 bị giao nhau.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai trong contract [Start,End); đổi quy tắc biên sẽ đổi kết quả.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace lựa chọn.

- **Working Developer — dùng khi làm việc:** proof và counterexample.

- **Deep Dive — có thể quay lại sau:** weighted interval scheduling khi cần.

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

## 7. Khi nào KHÔNG dùng

Không dùng greedy như mẹo vì chạy nhanh nếu chưa có lý do đúng. Không trộn ràng buộc phòng, di chuyển hoặc trọng số vào bài mà giữ nguyên lời giải.

## 8. Production notes & scale check

Gate so số lượng chọn với vét cạn tập con nhỏ và kiểm tính không giao nhau. Các lời giải tối ưu có thể khác ID khi hòa; chỉ so đặc tính cần bảo đảm. Input lớn vẫn cần tính chi phí materialization.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Từ contract Module06, thêm phí từng cuộc họp là thay đổi output format hay thay bài toán? Nêu phản ví dụ trước khi đề xuất weighted scheduling.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Greedy đang tối ưu gì?
2. Exchange argument bảo vệ bước nào?
3. Biên chạm nhau được nhận không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi hiểu greedy là quyết định cục bộ.
- [ ] Tôi không áp dụng greedy nếu chưa có lý do đúng.
- [ ] Tôi giải được interval scheduling.
- [ ] Tôi biết dùng counterexample để bác heuristic.
- [ ] Tôi phân biệt greedy và DP.
- [ ] Tôi nhận ra weighted version có thể đổi bản chất bài toán.

Điều hướng:

- Bài trước: [Searching](./14-searching.md)
- Bài tiếp theo: [Backtracking](./16-backtracking.md)

### Checkpoint sau cụm bài

- [Failure Lab](./failure-labs/03-search.md)
- [Spaced Review](./reviews/review-03.md)
