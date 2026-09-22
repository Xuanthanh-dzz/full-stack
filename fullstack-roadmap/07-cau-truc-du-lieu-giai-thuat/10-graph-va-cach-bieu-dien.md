# Graph và cách biểu diễn

## 1. Mục tiêu

Sau bài này, bạn có thể:

- mô tả graph bằng vertex và edge;
- phân biệt directed/undirected, weighted/unweighted graph;
- biểu diễn graph bằng adjacency list và adjacency matrix;
- phân tích trade-off memory và lookup;
- cài đặt graph đơn giản bằng C#;
- liên hệ graph với mạng xã hội, route, dependency và workflow.

## 2. Bài toán mở đầu

Ta có các thành phố:

```text
Hanoi
Hue
Da Nang
HCMC
```

và các tuyến đường nối chúng.

Đây không còn là tree vì một thành phố có thể kết nối nhiều thành phố khác, và có thể tồn tại cycle.

Graph mô hình hóa chính xác hơn:

```text
Hanoi ---- Hue ---- Da Nang ---- HCMC
   \___________________________/
```

## 3. Lời giải bằng code

```bash
mkdir GraphDemo
cd GraphDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

```csharp
namespace GraphDemo;

public sealed class Graph<T>
    where T : notnull
{
    private readonly Dictionary<T, HashSet<T>> _adjacency = [];

    public int VertexCount => _adjacency.Count;

    public void AddVertex(T vertex)
    {
        _adjacency.TryAdd(vertex, []);
    }

    public void AddUndirectedEdge(T from, T to)
    {
        AddVertex(from);
        AddVertex(to);

        _adjacency[from].Add(to);
        _adjacency[to].Add(from);
    }

    public IReadOnlyCollection<T> Neighbors(T vertex)
    {
        if (!_adjacency.TryGetValue(vertex, out HashSet<T>? neighbors))
        {
            throw new KeyNotFoundException($"Unknown vertex: {vertex}");
        }

        return neighbors;
    }

    public IEnumerable<(T From, T To)> Edges()
    {
        var seen = new HashSet<(T, T)>();

        foreach ((T from, HashSet<T> neighbors) in _adjacency)
        {
            foreach (T to in neighbors)
            {
                if (seen.Contains((to, from)))
                {
                    continue;
                }

                seen.Add((from, to));
                yield return (from, to);
            }
        }
    }
}

internal static class Program
{
    private static void Main()
    {
        var graph = new Graph<string>();

        graph.AddUndirectedEdge("Hanoi", "Hue");
        graph.AddUndirectedEdge("Hue", "Da Nang");
        graph.AddUndirectedEdge("Da Nang", "HCMC");
        graph.AddUndirectedEdge("Hanoi", "HCMC");

        Console.WriteLine($"Vertices = {graph.VertexCount}");
        Console.WriteLine(
            $"Neighbors of Hanoi: {string.Join(", ", graph.Neighbors("Hanoi"))}");

        foreach ((string from, string to) in graph.Edges())
        {
            Console.WriteLine($"{from} <-> {to}");
        }
    }
}
```

## 4. Giải thích cơ chế

### Vertex và edge

```text
vertex = một thực thể
edge   = quan hệ giữa hai thực thể
```

Ví dụ social network:

```text
User A ---- User B
   |
 User C
```

User là vertex, friendship là edge.

### Directed graph

```text
A -> B
```

không kéo theo:

```text
B -> A
```

Ví dụ:

- user follow;
- package dependency;
- workflow transition;
- URL redirect.

### Weighted graph

Edge có cost:

```text
A --5--> B
```

Cost có thể là:

- distance;
- latency;
- price;
- risk;
- number of hops.

Shortest-path algorithm dùng weight để chọn route.

### Adjacency list

Sample dùng:

```csharp
Dictionary<T, HashSet<T>>
```

Mỗi vertex map tới tập neighbor.

Với graph thưa, memory gần:

```text
O(V + E)
```

Trong đó:

- `V` = số vertex;
- `E` = số edge.

### Adjacency matrix

Matrix `V x V`:

```text
    A B C D
A [ 0 1 0 1 ]
B [ 1 0 1 0 ]
C [ 0 1 0 1 ]
D [ 1 0 1 0 ]
```

Memory:

```text
O(V²)
```

Đổi lại, kiểm tra edge `A -> B` là `O(1)`.

## 5. Kiến thức nền

### Sparse và dense graph

Sparse graph:

```text
E nhỏ so với V²
```

Adjacency list thường hiệu quả hơn.

Dense graph:

```text
E gần V²
```

Matrix có thể hợp lý trong một số bài toán.

### Degree

Undirected graph:

```text
degree(v) = số edge nối với v
```

Directed graph:

- in-degree;
- out-degree.

### Graph có thể có cycle

```text
A -> B -> C
^         |
|_________|
```

Khác với tree, graph không bắt buộc root và không cấm cycle.

Vì vậy traversal phải có tập `visited`, nếu không có thể lặp vô hạn.

## 6. Lỗi thường gặp

### Dùng tree để mô hình dữ liệu có nhiều parent

Một package dependency hoặc social network không phải tree thuần.

### Quên visited

DFS/BFS trên graph có cycle mà không track visited có thể chạy vô hạn.

### Nhầm edge count trong undirected adjacency list

Mỗi undirected edge thường xuất hiện hai lần:

```text
A -> B
B -> A
```

nhưng về logic chỉ là một edge.

### Dùng adjacency matrix cho graph cực lớn và thưa

1 triệu vertex tạo matrix không thực tế.

## 7. Bài tập

### Bài 1 — Directed graph

Viết `AddDirectedEdge`.

### Bài 2 — Weighted graph

Tạo:

```csharp
record Edge<T>(T To, int Weight);
```

và adjacency list có weight.

### Bài 3 — Degree

Tính degree của từng vertex.

### Bài 4 — HasEdge

Viết method kiểm tra một edge tồn tại.

Phân tích complexity với HashSet neighbor.

### Bài 5 — Dependency graph

Mô hình các package:

```text
Web -> Application
Application -> Domain
Infrastructure -> Application
```

Vẽ directed graph.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt vertex và edge.
- [ ] Tôi phân biệt directed/undirected và weighted/unweighted.
- [ ] Tôi cài được adjacency list.
- [ ] Tôi giải thích trade-off adjacency matrix/list.
- [ ] Tôi biết graph có cycle nên traversal cần visited.
- [ ] Tôi liên hệ graph với bài toán thực tế.

Điều hướng:

- Bài trước: [Trie](./09-trie.md)
- Bài tiếp theo: [BFS và DFS](./11-bfs-va-dfs.md)
