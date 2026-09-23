# Shortest path và minimum spanning tree

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- Shortest path tối thiểu một route; MST tối thiểu tổng mạng nối mọi đỉnh.
- Dijkstra dùng weight không âm; MST dùng graph vô hướng với mục tiêu khác.
- Early return chỉ đúng khi điều kiện weight được bảo đảm trước.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt shortest path với minimum spanning tree;
- cài Dijkstra cho graph có weight không âm;
- hiểu vai trò của priority queue;
- phân tích complexity ở mức ứng dụng;
- mô tả ý tưởng Prim/Kruskal cho MST;
- nhận ra khi nào hai bài toán có vẻ giống nhưng mục tiêu khác nhau.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Mua vé rẻ nhất đi từ nhà tới ga khác với kéo cáp rẻ nhất nối mọi nhà. Cùng bản đồ nhưng câu hỏi khác dẫn tới tập cạnh khác.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| relaxation | cải thiện distance qua một cạnh | candidate<distance |
| tentative distance | chi phí tốt nhất hiện biết | distances |
| stale entry | priority cũ đã bị cải thiện | queuedDistance mismatch |
| spanning tree | cây nối mọi đỉnh | V-1cạnh khi graphconnected |

### Ví dụ nhỏ — tính tay trước

A→B4,A→C1,C→B2,C→D1: popA0, C1, cập nhậtB3,D2; popD2 hoàn tất. B4 vẫn là entry cũ trong queue.

Graph đường đi:

```text
A --4-- B
|      /|
1     2 5
|   /   |
C --1-- D
```

Hai câu hỏi khác nhau:

1. Từ A tới D, route có tổng cost nhỏ nhất là gì?
2. Chọn tập edge có tổng cost nhỏ nhất để kết nối tất cả vertex là gì?

Câu 1: shortest path.
Câu 2: minimum spanning tree.

Không nên dùng cùng một thuật toán chỉ vì cả hai đều nói về “nhỏ nhất”.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```bash
mkdir DijkstraDemo
cd DijkstraDemo
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
namespace DijkstraDemo;

public sealed record Edge(string To, int Weight);

internal static class Program
{
    private static readonly Dictionary<string, Edge[]> Graph = new()
    {
        ["A"] = [new("B", 4), new("C", 1)],
        ["B"] = [new("A", 4), new("C", 2), new("D", 5)],
        ["C"] = [new("A", 1), new("B", 2), new("D", 1)],
        ["D"] = [new("B", 5), new("C", 1)]
    };

    private static void Main()
    {
        (long distance, IReadOnlyList<string> path) =
            ShortestPath("A", "D");

        Console.WriteLine($"Distance = {distance}");
        Console.WriteLine($"Path = {string.Join(" -> ", path)}");
    }

    private static (long Distance, IReadOnlyList<string> Path)
        ShortestPath(string start, string target)
    {
        if (!Graph.ContainsKey(start) || !Graph.ContainsKey(target))
        {
            throw new KeyNotFoundException("Both endpoints must exist.");
        }

        // Validate toàn graph trước early return khi start == target.
        foreach (Edge[] edges in Graph.Values)
        {
            foreach (Edge edge in edges)
            {
                ArgumentOutOfRangeException.ThrowIfNegative(edge.Weight);
                if (!Graph.ContainsKey(edge.To))
                    throw new ArgumentException("Edge points to an unknown vertex.");
            }
        }

        var distances = Graph.Keys.ToDictionary(
            vertex => vertex,
            _ => long.MaxValue);

        var previous = new Dictionary<string, string?>();
        var queue = new PriorityQueue<string, long>();

        distances[start] = 0;
        previous[start] = null;
        queue.Enqueue(start, 0);

        while (queue.TryDequeue(
            out string? current,
            out long queuedDistance))
        {
            if (queuedDistance != distances[current])
            {
                continue;
            }

            if (current == target)
            {
                break;
            }

            foreach (Edge edge in Graph[current])
            {
                ArgumentOutOfRangeException.ThrowIfNegative(edge.Weight);

                long candidate = checked(queuedDistance + edge.Weight);

                if (candidate >= distances[edge.To])
                {
                    continue;
                }

                distances[edge.To] = candidate;
                previous[edge.To] = current;
                queue.Enqueue(edge.To, candidate);
            }
        }

        if (distances[target] == long.MaxValue)
        {
            return (long.MaxValue, []);
        }

        var path = new List<string>();

        for (string? current = target;
             current is not null;
             current = previous[current])
        {
            path.Add(current);
        }

        path.Reverse();
        return (distances[target], path);
    }
}
```

Output:

```text
Distance = 2
Path = A -> C -> D
```

### Walkthrough — execution / state / cost

1. Validate cả graph trước early return: endpoint tồn tại, neighbor biết được, mọi weight>=0.
2. Khởi tạo long.MaxValue là unreachable và start 0, enqueue start.
3. Pop đúng distance rồi relax, lưu previous và enqueue distance mới.
4. Lazy duplicates làm queue có thể O(E); time tổng quát O(V+Elog(E+1)), trong simple graph thường viết O((V+E)logV). Validate O(V+E), path O(V).

### Mini-check

Graph A→B2,A→C5,C→B-10: dừng khi popB2 sẽ bỏ đường nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Relaxation

Giả sử đã biết:

```text
distance[A] = 0
```

Edge:

```text
A --1--> C
```

candidate:

```text
0 + 1 = 1
```

Nếu nhỏ hơn distance hiện tại của C, update:

```text
distance[C] = 1
previous[C] = A
```

Quá trình này gọi là relaxation.

### Priority queue

Ta luôn muốn xử lý vertex có distance nhỏ nhất hiện biết.

Priority queue cung cấp:

```text
dequeue min distance
```

hiệu quả hơn việc scan toàn bộ vertex mỗi vòng.

### Entry cũ trong priority queue

.NET `PriorityQueue` không có decrease-key trực tiếp.

Ta có thể enqueue lại cùng vertex với priority tốt hơn.

Khi dequeue entry cũ:

```csharp
if (queuedDistance != distances[current])
{
    continue;
}
```

thì bỏ qua.

### Vì sao Dijkstra không dùng negative edge

Giả định cốt lõi:

> Khi vertex có distance nhỏ nhất được lấy ra, không có đường đi sau này dùng edge không âm để làm nó tốt hơn.

Negative edge phá giả định này.

Graph có negative weight cần thuật toán khác như Bellman-Ford trong bài toán phù hợp.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| BFS | ít cạnh hoặc equal weight | O(V+E), không general weighted |
| Dijkstra | route weight không âm | heap và distancemap |
| MST | tổng mạng kết nối nhỏ nhất | không bảo đảm path từ source ngắn nhất |

### Misconception check

**Đúng hay sai?** Weight âm ở cạnh chưa duyệt không quan trọng nếu target pop sớm.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: cạnh ấy có thể tạo đường tốt hơn, phải chặn trước.

</details>

**Đúng hay sai?** int.MaxValue là cost không thể hợp lệ.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: cạnh int có thể bằng nó; long distance tránh nhầm sentinel int.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** distance và route.

- **Working Developer — dùng khi làm việc:** preconditions/sentinel.

- **Deep Dive — có thể quay lại sau:** lazyheapbounds và alternative algorithms.

### Complexity Dijkstra

Với adjacency list + binary heap priority queue, thường mô tả:

```text
O((V + E) log V)
```

hoặc gần:

```text
O(E log V)
```

trong graph connected thông thường.

### Minimum spanning tree

MST áp dụng cho weighted undirected connected graph.

Mục tiêu:

```text
kết nối mọi vertex
+
không cycle
+
tổng weight nhỏ nhất
```

Một spanning tree với `V` vertex luôn có:

```text
V - 1 edges
```

### Prim

Ý tưởng:

1. bắt đầu từ một vertex;
2. luôn chọn edge rẻ nhất nối tree hiện tại tới vertex chưa vào tree;
3. lặp tới khi đủ vertex.

Priority queue rất phù hợp.

### Kruskal

Ý tưởng:

1. sort edge theo weight;
2. lấy edge rẻ nhất nếu nó không tạo cycle;
3. dùng Disjoint Set Union để kiểm tra component;
4. dừng khi có `V - 1` edge.

## 6. Lỗi thường gặp

### Dùng Dijkstra với weight âm

Kết quả có thể sai dù code chạy.

### Nhầm MST với shortest path tree

MST tối thiểu tổng chi phí toàn mạng.
Shortest-path tree tối thiểu đường từ một source tới từng node.

Hai objective khác nhau.

### Overflow distance

Nếu weight lớn và cộng vào `long.MaxValue`, có thể overflow.

Sample chỉ cộng từ distance đã được dequeue hợp lệ và dùng `checked`.

### Không xử lý graph disconnected

Dijkstra có thể không tới target.
MST trên graph disconnected tạo minimum spanning forest, không phải một tree duy nhất.

## 7. Khi nào KHÔNG dùng

Không dùng Dijkstra cho cost âm hoặc MST cho route giữa hai điểm. Không thêm MST implementation vào runtime chỉ vì bài giới thiệu thuật ngữ.

## 8. Production notes & scale check

Gate so Dijkstra với oracle Floyd–Warshall trên graph nhỏ, kiểm cạnh cost 0, unreachable, start=target, âm ở nhánh chưa tới và cost int.MaxValue. Prim/Kruskal là phần mô tả/exercise, chưa tuyên bố chạy sample MST. Long vẫn cần policy tài nguyên khi scale.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — All distances

Sửa Dijkstra trả distance từ source tới mọi vertex.

### Bài 2 — Unreachable

Thêm vertex E không nối cạnh và kiểm tra result.

### Bài 3 — Prim

Cài Prim bằng priority queue.

### Bài 4 — Kruskal concept

Mô tả DSU cần hai operation:

```text
Find
Union
```

và vì sao nó phát hiện cycle.

### Bài 5 — Chọn thuật toán

Chọn:

- BFS;
- Dijkstra;
- MST

cho ba bài toán:

1. ít bước nhất trong maze;
2. route rẻ nhất với toll khác nhau;
3. nối các chi nhánh bằng cáp với tổng chi phí thấp nhất.

## 10. Bài tập tích hợp liên module — Judgment

So checked và invariant Module06: validate weight lúc boundary khác guard trong loop ở đâu? Với graph đọc nhiều cập nhật ít, chuyển validation sang builder có ích gì?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Relax cập nhật mấy bảng?
2. Tại sao phải bỏ stale entry?
3. MST khác shortestpath tree thế nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt shortest path và MST.
- [ ] Tôi hiểu relaxation.
- [ ] Tôi biết Dijkstra cần weight không âm.
- [ ] Tôi hiểu priority queue giúp chọn distance nhỏ nhất.
- [ ] Tôi mô tả được ý tưởng Prim và Kruskal.
- [ ] Tôi không nhầm shortest-path tree với MST.

Điều hướng:

- Bài trước: [BFS và DFS](./11-bfs-va-dfs.md)
- Bài tiếp theo: [Sorting](./13-sorting.md)
