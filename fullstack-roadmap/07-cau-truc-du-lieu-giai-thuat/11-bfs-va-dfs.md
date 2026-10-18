# BFS và DFS

## 1. Mục tiêu

Sau bài này, bạn có thể:

- thực hiện Breadth-First Search và Depth-First Search;
- giải thích queue trong BFS và stack/recursion trong DFS;
- dùng `visited` để tránh cycle;
- phân tích complexity `O(V + E)`;
- dùng BFS tìm shortest path theo số edge trong unweighted graph;
- dùng DFS cho traversal, cycle/component và backtracking foundation.

## 2. Bài toán mở đầu

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

## 3. Lời giải bằng code

```bash
mkdir GraphTraversalDemo
cd GraphTraversalDemo
dotnet new console --framework net9.0 --use-program-main
```

`Program.cs`:

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

## 4. Giải thích cơ chế

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
O(V)
```

cho queue/stack + visited trong worst case.

## 5. Kiến thức nền

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

## 7. Bài tập

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

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi biết BFS dùng queue, DFS dùng stack/recursion.
- [ ] Tôi luôn nghĩ tới visited khi graph có cycle.
- [ ] Tôi phân tích được `O(V + E)`.
- [ ] Tôi biết BFS tìm shortest path theo số edge trong unweighted graph.
- [ ] Tôi lưu predecessor để reconstruct path.
- [ ] Tôi không dùng BFS cho weighted shortest path tổng quát.

Điều hướng:

- Bài trước: [Graph và cách biểu diễn](./10-graph-va-cach-bieu-dien.md)
- Bài tiếp theo: [Shortest path và minimum spanning tree](./12-shortest-path-va-minimum-spanning-tree.md)
