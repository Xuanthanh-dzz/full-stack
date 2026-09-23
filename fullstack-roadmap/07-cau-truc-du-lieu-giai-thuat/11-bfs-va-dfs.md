# BFS và DFS

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- BFS đi theo lớp, DFS đi sâu theo nhánh.
- Dùng BFS cho ít cạnh nhất khi mọi trọng số bằng nhau.
- Visited và thời điểm đánh dấu quyết định work trùng và memory.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- thực hiện Breadth-First Search và Depth-First Search;
- giải thích queue trong BFS và stack/recursion trong DFS;
- dùng `visited` để tránh cycle;
- phân tích complexity `O(V + E)`;
- dùng BFS tìm shortest path theo số edge trong unweighted graph;
- dùng DFS cho traversal, cycle/component và backtracking foundation.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Từ điểm A, BFS hỏi mọi người cách một bước rồi hai bước. DFS theo một lối đến sâu mới quay lại. Cả hai cần ghi ai đã gặp để không đi vòng mãi.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| frontier | các đỉnh chờ xử lý | queue/stack |
| visited | đỉnh đã phát hiện/xử lý | HashSet |
| predecessor | đỉnh trước trên đường tìm được | previous |
| component | nhóm đỉnh nối tới nhau | phần start đi tới |

### Ví dụ nhỏ — tính tay trước

A cóB,C;B cóD;C cũng cóD. BFS markD khi enqueue nên D vào queue một lần. Previous[D] giữB theo neighbor order này.

Graph:

```text
A -- B -- D
|    |
C -- E -- F
```

Nếu cần tìm các node theo từng “lớp” cách A:

```text
distance 0: A
distance 1: B, C
distance 2: D, E
distance 3: F
```

BFS phù hợp.

Nếu cần đi thật sâu một nhánh trước rồi quay lại, DFS phù hợp.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

```bash
mkdir GraphTraversalDemo
cd GraphTraversalDemo
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
namespace GraphTraversalDemo;

internal static class Program
{
    private static readonly Dictionary<string, string[]> Graph = new()
    {
        ["A"] = ["B", "C"],
        ["B"] = ["A", "D", "E"],
        ["C"] = ["A", "E"],
        ["D"] = ["B"],
        ["E"] = ["B", "C", "F"],
        ["F"] = ["E"]
    };

    private static void Main()
    {
        Console.WriteLine(
            $"BFS: {string.Join(" -> ", Bfs("A"))}");

        Console.WriteLine(
            $"DFS: {string.Join(" -> ", Dfs("A"))}");

        Console.WriteLine(
            $"Shortest A->F: {string.Join(" -> ", ShortestPath("A", "F"))}");
    }

    private static IReadOnlyList<string> Bfs(string start)
    {
        var visited = new HashSet<string> { start };
        var queue = new Queue<string>();
        var order = new List<string>();

        queue.Enqueue(start);

        while (queue.TryDequeue(out string? current))
        {
            order.Add(current);

            foreach (string next in Graph[current])
            {
                if (visited.Add(next))
                {
                    queue.Enqueue(next);
                }
            }
        }

        return order;
    }

    private static IReadOnlyList<string> Dfs(string start)
    {
        var visited = new HashSet<string>();
        var stack = new Stack<string>();
        var order = new List<string>();

        stack.Push(start);

        while (stack.TryPop(out string? current))
        {
            if (!visited.Add(current))
            {
                continue;
            }

            order.Add(current);

            foreach (string next in Graph[current].Reverse())
            {
                if (!visited.Contains(next))
                {
                    stack.Push(next);
                }
            }
        }

        return order;
    }

    private static IReadOnlyList<string> ShortestPath(
        string start,
        string target)
    {
        var previous = new Dictionary<string, string?>();
        var queue = new Queue<string>();

        previous[start] = null;
        queue.Enqueue(start);

        while (queue.TryDequeue(out string? current))
        {
            if (current == target)
            {
                break;
            }

            foreach (string next in Graph[current])
            {
                if (previous.ContainsKey(next))
                {
                    continue;
                }

                previous[next] = current;
                queue.Enqueue(next);
            }
        }

        if (!previous.ContainsKey(target))
        {
            return [];
        }

        var path = new List<string>();

        for (string? current = target;
             current is not null;
             current = previous[current])
        {
            path.Add(current);
        }

        path.Reverse();
        return path;
    }
}
```

Một output hợp lệ:

```text
BFS: A -> B -> C -> D -> E -> F
DFS: A -> B -> D -> E -> C -> F
Shortest A->F: A -> B -> E -> F
```

Traversal order có thể khác nếu thứ tự neighbor khác, nhưng tính đúng của thuật toán không thay đổi.

### Walkthrough — execution / state / cost

1. Bfs đánh dấu start rồi enqueue; mỗi neighbor mới được đánh dấu trước enqueue.
2. Dfs push thứ tự đảo và đánh dấu lúc pop; entry trùng được bỏ trước duyệt neighbors.
3. ShortestPath dùng previous như visited, trace ngược target về start rồi reverse.
4. BFS time O(V+E),bộ nhớ O(V); DFS hiện tại có thể O(E) entry đang chờ do mark-on-pop. Chỉ xét component từ start, graph/input cố định trong khi chạy.

### Mini-check

Nếu B,C cùng trỏ D, mark-on-pop cho phép D nằm trong stack mấy entry trước khi một entry được xử lý?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### BFS dùng queue

```text
enqueue A

queue: [A]

dequeue A
enqueue B,C

queue: [B,C]

dequeue B
enqueue D,E

queue: [C,D,E]
```

Queue giữ nguyên thứ tự từng lớp.

Do đó trong unweighted graph, lần đầu tới một node chính là số edge ít nhất từ start.

### DFS dùng stack

```text
push A
pop A -> push C,B
pop B -> push E,D
pop D
...
```

Stack làm traversal đi sâu một nhánh trước.

Recursive DFS cũng dùng chính call stack của runtime.

### Visited

Nếu graph:

```text
A -- B
|    |
C -- D
```

ta có thể quay lại A theo cycle.

`visited` bảo đảm mỗi vertex được xử lý một lần.

### Complexity

Adjacency list:

- mỗi vertex được visit tối đa một lần;
- mỗi edge được inspect một số hằng lần.

Time:

```text
O(V + E)
```

Space:

```text
O(V) cho BFS; O(V + E) cho DFS hiện tại
```

BFS đánh dấu khi enqueue nên mỗi vertex vào queue một lần. DFS đánh dấu khi pop nên có thể giữ nhiều entry trùng chưa pop, tối đa theo số cạnh; visited/order vẫn O(V).

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| BFS queue | khoảng cách số cạnh tăng dần | shortest equal weight, frontier có thể rộng |
| DFS stack | đi sâu trước | không bảo đảm route ngắn |
| Dijkstra heap | distance có weight | cần weight không âm và cost thêm |

### Misconception check

**Đúng hay sai?** DFS đầu tiên tới target luôn là đường ít cạnh nhất.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: có thể đi nhánh dài trước.

</details>

**Đúng hay sai?** Visited lúc pop và lúc enqueue có cùng memory bound.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: duplicate pending có thể làm DFS dùng O(E).

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace queue/stack.

- **Working Developer — dùng khi làm việc:** path và reachablecomponent.

- **Deep Dive — có thể quay lại sau:** memory bounds theo implementation.

### BFS shortest path chỉ đúng với unweighted/equal-weight graph

Nếu edge có weight:

```text
A --100--> B
A --1----> C --1--> B
```

đường ít edge hơn không nhất thiết chi phí nhỏ hơn.

Khi có non-negative weight, Dijkstra phù hợp hơn.

### Connected component

Chọn một node chưa visited, BFS/DFS toàn component đó.

Lặp lại cho các node chưa visited để đếm component.

### DFS và recursion

Recursive DFS:

```csharp
void Dfs(Node node)
{
    if (!visited.Add(node))
    {
        return;
    }

    foreach (Node next in node.Neighbors)
    {
        Dfs(next);
    }
}
```

Dễ đọc nhưng graph depth rất lớn có thể gây stack overflow.

## 6. Lỗi thường gặp

### Mark visited quá muộn trong BFS

Nếu chỉ mark khi dequeue, một node có thể được enqueue nhiều lần từ các parent khác nhau.

Thường nên mark ngay khi enqueue/discover.

### Dùng BFS cho weighted shortest path

BFS tối ưu số edge, không tối ưu tổng weight khác nhau.

### Không lưu previous

Nếu chỉ lưu distance mà không lưu predecessor, bạn biết độ dài nhưng khó reconstruct path.

### Dựa vào exact traversal order

Nếu neighbor collection không có order contract, thứ tự traversal có thể khác.

## 7. Khi nào KHÔNG dùng

Không dùng BFS để tối thiểu tổng phí khác nhau. Không suy traversal của một start đã bao phủ mọi component.

## 8. Production notes & scale check

Gate kiểm thứ tự với danh sách hàng xóm cố định, mỗi đỉnh được thăm một lần khi có cycle, đường từ một đỉnh về chính nó và đích không thể tới. Sample method private dùng graph đã hợp lệ; start không tồn tại là lỗi và target không tồn tại hoặc bị tách rời trả rỗng khi không được phát hiện.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Distance map

BFS từ start và trả distance theo số edge tới mọi node.

### Bài 2 — Connected components

Đếm component trong undirected graph.

### Bài 3 — Cycle detection

Dùng DFS phát hiện cycle trong directed graph.

### Bài 4 — Maze

Biểu diễn mỗi ô đi được như vertex và tìm đường ngắn nhất bằng BFS.

### Bài 5 — Recursive DFS

Viết lại DFS bằng recursion và so sánh space behavior.

## 10. Bài tập tích hợp liên module — Judgment

So Queue Module05 async với BFSqueue: vì sao BFS không cần thread để có frontier? Với số đỉnh tăng, chi phí state thuộc RAM chứ không I/O nào?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Markvisited ở đâu trong BFS?
2. Previous khác distance thế nào?
3. DFS pending stack có thể hơnV không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi biết BFS dùng queue, DFS dùng stack/recursion.
- [ ] Tôi luôn nghĩ tới visited khi graph có cycle.
- [ ] Tôi phân tích được `O(V + E)`.
- [ ] Tôi biết BFS tìm shortest path theo số edge trong unweighted graph.
- [ ] Tôi lưu predecessor để reconstruct path.
- [ ] Tôi không dùng BFS cho weighted shortest path tổng quát.

Điều hướng:

- Bài trước: [Graph và cách biểu diễn](./10-graph-va-cach-bieu-dien.md)
- Bài tiếp theo: [Shortest path và minimum spanning tree](./12-shortest-path-va-minimum-spanning-tree.md)
