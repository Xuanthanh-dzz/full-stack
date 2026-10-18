# Shortest path và minimum spanning tree

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt shortest path với minimum spanning tree;
- cài Dijkstra cho graph có weight không âm;
- hiểu vai trò của priority queue;
- phân tích complexity ở mức ứng dụng;
- mô tả ý tưởng Prim/Kruskal cho MST;
- nhận ra khi nào hai bài toán có vẻ giống nhưng mục tiêu khác nhau.

## 2. Bài toán mở đầu

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

## 3. Lời giải bằng code

```bash
mkdir DijkstraDemo
cd DijkstraDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

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
        (int distance, IReadOnlyList<string> path) =
            ShortestPath("A", "D");

        Console.WriteLine($"Distance = {distance}");
        Console.WriteLine($"Path = {string.Join(" -> ", path)}");
    }

    private static (int Distance, IReadOnlyList<string> Path)
        ShortestPath(string start, string target)
    {
        var distances = Graph.Keys.ToDictionary(
            vertex => vertex,
            _ => int.MaxValue);

        var previous = new Dictionary<string, string?>();
        var queue = new PriorityQueue<string, int>();

        distances[start] = 0;
        previous[start] = null;
        queue.Enqueue(start, 0);

        while (queue.TryDequeue(
            out string? current,
            out int queuedDistance))
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

                int candidate = checked(queuedDistance + edge.Weight);

                if (candidate >= distances[edge.To])
                {
                    continue;
                }

                distances[edge.To] = candidate;
                previous[edge.To] = current;
                queue.Enqueue(edge.To, candidate);
            }
        }

        if (distances[target] == int.MaxValue)
        {
            return (int.MaxValue, []);
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

## 4. Giải thích cơ chế

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

## 5. Kiến thức nền

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

Nếu weight lớn và cộng vào `int.MaxValue`, có thể overflow.

Sample chỉ cộng từ distance đã được dequeue hợp lệ và dùng `checked`.

### Không xử lý graph disconnected

Dijkstra có thể không tới target.
MST trên graph disconnected tạo minimum spanning forest, không phải một tree duy nhất.

## 7. Bài tập

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

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt shortest path và MST.
- [ ] Tôi hiểu relaxation.
- [ ] Tôi biết Dijkstra cần weight không âm.
- [ ] Tôi hiểu priority queue giúp chọn distance nhỏ nhất.
- [ ] Tôi mô tả được ý tưởng Prim và Kruskal.
- [ ] Tôi không nhầm shortest-path tree với MST.

Điều hướng:

- Bài trước: [BFS và DFS](./11-bfs-va-dfs.md)
- Bài tiếp theo: [Sorting](./13-sorting.md)
