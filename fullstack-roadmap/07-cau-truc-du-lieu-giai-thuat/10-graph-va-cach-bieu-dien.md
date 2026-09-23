# Graph và cách biểu diễn

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- Graph mô hình đỉnh và quan hệ có thể có chu trình, nhiều đường tới.
- Dùng adjacency list khi graph thưa, matrix khi pattern truy cập phù hợp.
- Phải chọn directed/undirected và duplicate/self-loop policy rõ.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- mô tả graph bằng vertex và edge;
- phân biệt directed/undirected, weighted/unweighted graph;
- biểu diễn graph bằng adjacency list và adjacency matrix;
- phân tích trade-off memory và lookup;
- cài đặt graph đơn giản bằng C#;
- liên hệ graph với mạng xã hội, route, dependency và workflow.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Bản đồ đường không giống cây gia phả: từ một điểm có thể vòng lại qua nhiều đường. Ta ghi danh sách láng giềng của từng điểm thay vì ép mỗi điểm chỉ có một cha.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| vertex | đỉnh đại diện thực thể | thành phố |
| edge | quan hệ giữa hai đỉnh | đường hai chiều |
| adjacency | danh sách đỉnh kề | Dictionary→HashSet |
| degree | số cạnh liên quan đỉnh | cần quy ước self-loop |

### Ví dụ nhỏ — tính tay trước

Add A-B rồi B-C: A cóB, B cóA,C, C cóB. Add A-B lại không thêm cạnh logic; Edges trả mỗi cạnh hai chiều một lần.

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

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```bash
mkdir GraphDemo
cd GraphDemo
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

        return neighbors.ToArray();
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
            $"Neighbors of Hanoi: {string.Join(", ", graph.Neighbors("Hanoi").OrderBy(x => x, StringComparer.Ordinal))}");

        foreach ((string from, string to) in graph.Edges().OrderBy(x => x.From, StringComparer.Ordinal).ThenBy(x => x.To, StringComparer.Ordinal))
        {
            Console.WriteLine($"{from} <-> {to}");
        }
    }
}
```

Output đầy đủ:

```text
Vertices = 4
Neighbors of Hanoi: HCMC, Hue
Da Nang <-> HCMC
Hanoi <-> HCMC
Hanoi <-> Hue
Hue <-> Da Nang
```

### Walkthrough — execution / state / cost

1. AddUndirectedEdge bảo đảm cả hai vertex rồi thêm vào hai neighbor sets.
2. HashSet gộp cạnh trùng; Edges dùng seen để bỏ hướng đảo đã xuất.
3. Neighbors trả array snapshot shallow, caller không sửa set nội bộ qua cast.
4. Storage O(V+E); snapshot O(degree), Edges thêm O(E) cho seen. Main sort để output ổn định, chi phí sort không thuộc AddEdge.

### Mini-check

Add A-A: set chứa A một lần; degree toán học tính self-loop hai lần khác Count neighbors thế nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| adjacency list | chỉ lưu cạnh có thật | O(V+E), hợp graph thưa |
| matrix | ô cho từng cặp đỉnh | O(V²), lookupO(1) |
| tree | một cấu trúc không cycle | không ép dependency graph đa parent vào tree |

### Misconception check

**Đúng hay sai?** Undirected edge phải đếm hai vì lưu hai hướng.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: representation khác số cạnh logic.

</details>

**Đúng hay sai?** HashSet enumeration bảo đảm alphabet order.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: Main phải sort nếu muốn output ổn định.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** vertices/edges.

- **Working Developer — dùng khi làm việc:** representation/alias.

- **Deep Dive — có thể quay lại sau:** large graph storage khi cần.

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

## 7. Khi nào KHÔNG dùng

Không cấp matrix triệu đỉnh khi graph rất thưa. Không trả mutable neighbor set để caller phá đối xứng hai chiều.

## 8. Production notes & scale check

Gate kiểm cạnh lặp, hai chiều, đỉnh không tồn tại và snapshot độc lập với graph. T:notnull là ràng buộc kiểu; vertex equality/hash phải ổn định. Snapshot shallow không clone object T và không làm graph thread-safe; API không hỗ trợ concurrent updates.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

Từ Module06 dependency inversion, vẽ compile references thành directed graph và chỉ ra khác với runtimecall graph. Chọn representation nếu chỉ vài edges/project.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Một edge hai chiều lưu mấy entry?
2. Neighbors snapshot tốn gì?
3. Tree khác graph tổng quát ở đâu?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt vertex và edge.
- [ ] Tôi phân biệt directed/undirected và weighted/unweighted.
- [ ] Tôi cài được adjacency list.
- [ ] Tôi giải thích trade-off adjacency matrix/list.
- [ ] Tôi biết graph có cycle nên traversal cần visited.
- [ ] Tôi liên hệ graph với bài toán thực tế.

Điều hướng:

- Bài trước: [Trie](./09-trie.md)
- Bài tiếp theo: [BFS và DFS](./11-bfs-va-dfs.md)

### Checkpoint sau cụm bài

- [Failure Lab](./failure-labs/02-hash.md)
- [Spaced Review](./reviews/review-02.md)
