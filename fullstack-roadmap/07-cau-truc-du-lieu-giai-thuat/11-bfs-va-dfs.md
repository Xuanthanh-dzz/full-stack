# BFS và DFS

## 1. Mục tiêu

Sau bài này, bạn có thể:

- cài đặt **BFS** (duyệt theo chiều rộng) bằng queue và **DFS** (theo chiều sâu) bằng đệ quy;
- giải thích vì sao cần **visited set** để không lặp vô hạn trong đồ thị có chu trình;
- dùng BFS tìm **đường đi ngắn nhất theo số bước** trong đồ thị không trọng số;
- phân biệt thứ tự thăm của BFS (theo tầng) và DFS (đi sâu hết nhánh);
- truy vết đường đi bằng **parent map**;
- nhận ra các ứng dụng: kiểm tra liên thông, phát hiện chu trình, sắp thứ tự.

## 2. Bài toán mở đầu

Có đồ thị rồi (bài [10](./10-graph-va-cach-bieu-dien.md)), câu hỏi đầu tiên luôn là: **đi từ đỉnh này tới đỉnh kia được không, và ngắn nhất bao nhiêu bước?** Ví dụ: từ trạm A tới trạm E qua ít chặng nhất; hai người có nối được với nhau qua chuỗi bạn bè không; từ trang chủ có tới được trang đích không.

Muốn trả lời, ta phải **duyệt** đồ thị — thăm các đỉnh một cách có hệ thống. Có hai chiến lược nền tảng, và gần như mọi thuật toán đồ thị khác đều xây trên chúng:

- **BFS** lan ra theo **tầng**: thăm mọi đỉnh cách nguồn 1 bước, rồi 2 bước, rồi 3 bước... Nhờ đó nó tìm đường ngắn nhất (theo số bước) một cách tự nhiên.
- **DFS** đi **sâu** hết một nhánh rồi mới quay lại thử nhánh khác. Nó hợp cho việc khám phá toàn bộ, phát hiện chu trình, sắp thứ tự phụ thuộc.

Điểm mới so với duyệt cây: đồ thị có **chu trình**, nên nếu không nhớ "đã thăm ai" ta sẽ đi vòng vô tận. Bài này cài cả hai.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `TraversalDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace TraversalDemo;

internal static class Program
{
    private static void Main()
    {
        var g = new Graph<string>();
        g.AddEdge("A", "B");
        g.AddEdge("A", "C");
        g.AddEdge("B", "D");
        g.AddEdge("C", "E");
        g.AddEdge("D", "E"); // D-E khép lại tạo chu trình A-B-D-E-C-A

        Console.WriteLine("== BFS từ A: duyệt theo tầng, dùng queue ==");
        var (bfsOrder, distance) = g.Bfs("A");
        Console.WriteLine($"Thứ tự thăm: [{string.Join(", ", bfsOrder)}]");
        Console.WriteLine("Khoảng cách (số bước) từ A:");
        foreach (var kv in distance.OrderBy(k => k.Key))
        {
            Console.WriteLine($"  A -> {kv.Key}: {kv.Value} bước");
        }

        Console.WriteLine();
        Console.WriteLine("== DFS từ A: đi sâu hết nhánh, dùng đệ quy ==");
        var dfsOrder = g.Dfs("A");
        Console.WriteLine($"Thứ tự thăm: [{string.Join(", ", dfsOrder)}]");

        Console.WriteLine();
        Console.WriteLine("== Đường đi ngắn nhất (số bước) bằng BFS ==");
        var path = g.ShortestPath("A", "E");
        Console.WriteLine($"A -> E: {string.Join(" -> ", path)} ({path.Count - 1} bước)");
    }
}

internal sealed class Graph<T> where T : notnull
{
    private readonly Dictionary<T, HashSet<T>> _adj = new();

    public void AddEdge(T u, T v)
    {
        Add(u); Add(v);
        _adj[u].Add(v);
        _adj[v].Add(u);
    }

    private void Add(T v)
    {
        if (!_adj.ContainsKey(v)) _adj[v] = new HashSet<T>();
    }

    private IEnumerable<T> Neighbors(T v) =>
        _adj.TryGetValue(v, out var s) ? s.OrderBy(x => x) : Enumerable.Empty<T>();

    // BFS: dùng queue (FIFO). Trả thứ tự thăm và khoảng cách từ nguồn.
    public (List<T> Order, Dictionary<T, int> Distance) Bfs(T start)
    {
        var order = new List<T>();
        var distance = new Dictionary<T, int> { [start] = 0 };
        var visited = new HashSet<T> { start }; // nhớ đã thăm -> tránh lặp vô hạn
        var queue = new Queue<T>();
        queue.Enqueue(start);

        while (queue.Count > 0)
        {
            T current = queue.Dequeue();
            order.Add(current);
            foreach (T next in Neighbors(current))
            {
                if (visited.Add(next)) // Add trả false nếu đã có
                {
                    distance[next] = distance[current] + 1;
                    queue.Enqueue(next);
                }
            }
        }
        return (order, distance);
    }

    // DFS: đệ quy (dùng call stack). Đi sâu hết một nhánh rồi mới quay lại.
    public List<T> Dfs(T start)
    {
        var order = new List<T>();
        var visited = new HashSet<T>();
        DfsVisit(start, visited, order);
        return order;
    }

    private void DfsVisit(T node, HashSet<T> visited, List<T> order)
    {
        if (!visited.Add(node)) return; // đã thăm -> dừng
        order.Add(node);
        foreach (T next in Neighbors(node))
        {
            DfsVisit(next, visited, order);
        }
    }

    // Đường ngắn nhất trong đồ thị KHÔNG trọng số = BFS + truy vết cha.
    public List<T> ShortestPath(T start, T goal)
    {
        var parent = new Dictionary<T, T>();
        var visited = new HashSet<T> { start };
        var queue = new Queue<T>();
        queue.Enqueue(start);

        while (queue.Count > 0)
        {
            T current = queue.Dequeue();
            if (current.Equals(goal)) break;
            foreach (T next in Neighbors(current))
            {
                if (visited.Add(next))
                {
                    parent[next] = current;
                    queue.Enqueue(next);
                }
            }
        }

        // dựng lại đường đi bằng cách đi ngược con trỏ cha
        var path = new List<T>();
        T? node = goal;
        while (node is not null)
        {
            path.Add(node);
            if (node.Equals(start)) break;
            node = parent.TryGetValue(node, out var p) ? p : default;
        }
        path.Reverse();
        return path;
    }
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
== BFS từ A: duyệt theo tầng, dùng queue ==
Thứ tự thăm: [A, B, C, D, E]
Khoảng cách (số bước) từ A:
  A -> A: 0 bước
  A -> B: 1 bước
  A -> C: 1 bước
  A -> D: 2 bước
  A -> E: 2 bước

== DFS từ A: đi sâu hết nhánh, dùng đệ quy ==
Thứ tự thăm: [A, B, D, E, C]

== Đường đi ngắn nhất (số bước) bằng BFS ==
A -> E: A -> C -> E (2 bước)
```

## 4. Giải thích cơ chế

Đồ thị trong bài:

```text
      A
     / \
    B   C
    |   |
    D   E
     \ /
      (D-E nối)
```

### 4.1 BFS lan theo tầng nhờ queue

BFS dùng một **queue** (FIFO, bài [05](./05-stack-queue-va-deque.md)). Ý tưởng: lấy một đỉnh ra, thăm nó, rồi **xếp mọi hàng xóm chưa thăm vào cuối hàng**. Vì FIFO, các đỉnh gần nguồn hơn luôn được lấy ra trước:

```text
queue: [A]         -> lấy A, xếp B,C     order: A
queue: [B,C]       -> lấy B, xếp D        order: A,B
queue: [C,D]       -> lấy C, xếp E        order: A,B,C
queue: [D,E]       -> lấy D               order: A,B,C,D
queue: [E]         -> lấy E               order: A,B,C,D,E
```

Thứ tự thăm `A, B, C, D, E` đúng theo **tầng**: A (tầng 0), rồi B và C (tầng 1), rồi D và E (tầng 2). Vì đi theo tầng, lần **đầu tiên** BFS chạm một đỉnh chính là qua đường ngắn nhất — nên `distance` ghi lại đúng số bước tối thiểu: `D` và `E` đều cách A 2 bước.

### 4.2 DFS đi sâu nhờ call stack

DFS thăm một đỉnh rồi **lập tức đi sâu** vào hàng xóm đầu tiên chưa thăm, chỉ quay lại khi nhánh đó cạn. Ở đây dùng đệ quy, tức mượn chính call stack (bài [02](./02-de-quy-va-call-stack.md)):

```text
A -> B -> D -> E -> (E thử C) -> C
```

Thứ tự `A, B, D, E, C`: từ A xuống B, xuống D, D nối E nên xuống E, E nối C nên xuống C. **Khác hẳn** BFS: DFS lao xuống tận đáy một nhánh trước, còn BFS trải đều từng tầng. So hai dòng output là thấy ngay bản chất khác nhau của hai chiến lược.

DFS cũng có thể cài bằng một `Stack<T>` tường minh thay đệ quy — hữu ích khi đồ thị sâu, tránh tràn call stack.

### 4.3 Visited set: chìa khóa để không lặp vô tận

Đồ thị này có chu trình `A-B-D-E-C-A`. Nếu không nhớ đỉnh đã thăm, BFS/DFS sẽ đi vòng mãi: A→B→D→E→C→A→B... `HashSet<T> visited` chặn điều đó. Mẹo gọn: `visited.Add(next)` trả `false` nếu phần tử **đã có** — nên chỉ cần một câu `if (visited.Add(next))` vừa kiểm tra vừa đánh dấu. Đây là điểm khác biệt cốt lõi giữa duyệt đồ thị và duyệt cây (cây không có chu trình nên không cần visited).

### 4.4 Truy vết đường đi bằng parent map

`ShortestPath` chạy BFS nhưng mỗi khi khám phá `next` từ `current`, nó ghi `parent[next] = current`. Khi tới đích, ta đi **ngược** con trỏ cha từ đích về nguồn rồi đảo lại: `E ← C ← A`, đảo thành `A → C → E`. Vì BFS bảo đảm chạm đỉnh qua đường ngắn nhất, đường truy vết ra chính là đường ít bước nhất. Kỹ thuật parent map này dùng lại ở mọi thuật toán tìm đường, kể cả Dijkstra (bài [12](./12-shortest-path-va-minimum-spanning-tree.md)).

### Đào sâu (có thể quay lại sau)

- **BFS chỉ ngắn nhất khi KHÔNG trọng số.** BFS đếm **số cạnh**, coi mọi cạnh như nhau. Nếu cạnh có trọng số khác nhau (khoảng cách km), đường ít cạnh chưa chắc ngắn nhất — lúc đó cần Dijkstra. Bài [12](./12-shortest-path-va-minimum-spanning-tree.md) xử lý ca này.
- **Độ phức tạp.** Cả BFS lẫn DFS thăm mỗi đỉnh một lần và xét mỗi cạnh một lần, nên đều `O(V + E)` trên adjacency list — tuyến tính theo kích thước đồ thị. Bộ nhớ `O(V)` cho visited và queue/stack.
- **Ứng dụng DFS.** Phát hiện chu trình, sắp thứ tự topo (topological sort) cho DAG phụ thuộc, tìm thành phần liên thông, tìm cầu/khớp trong đồ thị. Nhiều bài dựa trên thứ tự "vào/ra" của DFS.
- **Đồ thị không liên thông.** Một lần BFS/DFS chỉ thăm được các đỉnh **tới được** từ nguồn. Muốn thăm toàn đồ thị (đếm thành phần liên thông), lặp qua mọi đỉnh và khởi động một lần duyệt mới cho đỉnh nào chưa thăm.

## 5. Kiến thức nền

### BFS so với DFS

| Tiêu chí | BFS | DFS |
|---|---|---|
| Cấu trúc phụ trợ | queue (FIFO) | stack / đệ quy |
| Thứ tự thăm | theo tầng | đi sâu hết nhánh |
| Đường ngắn nhất (không trọng số) | có, tự nhiên | không bảo đảm |
| Bộ nhớ xấu nhất | `O(bề rộng)` | `O(chiều sâu)` |
| Hợp cho | khoảng cách, lan tỏa | chu trình, sắp thứ tự, khám phá |

Cả hai đều `O(V + E)` thời gian. Chọn theo **câu hỏi**: cần "ngắn nhất/gần nhất" thì BFS; cần "khám phá sâu/thứ tự phụ thuộc/chu trình" thì DFS.

### Vì sao queue cho ra thứ tự theo tầng

FIFO bảo đảm: mọi đỉnh tầng `k` được xếp vào queue **trước** mọi đỉnh tầng `k+1` (vì tầng `k+1` chỉ được khám phá khi xử lý tầng `k`). Nên chúng cũng được lấy ra trước. Đó là toàn bộ lý do BFS = duyệt theo tầng = đường ngắn nhất không trọng số.

### DFS và đệ quy là bà con với backtracking

DFS "đi sâu rồi quay lui" chính là khung của backtracking (bài [16](./16-backtracking.md)): thử một lựa chọn, đi tiếp, nếu bế tắc thì lùi lại thử lựa chọn khác. Nắm DFS là nền để hiểu backtracking sau này.

## 6. Lỗi thường gặp

### Quên visited set

Bug tai hại nhất: không đánh dấu đã thăm, đồ thị có chu trình sẽ làm chương trình chạy vô hạn hoặc tràn stack. Luôn có visited khi duyệt đồ thị.

### Đánh dấu visited sai thời điểm (BFS)

Trong BFS, đánh dấu visited **lúc enqueue**, không phải lúc dequeue. Nếu chỉ đánh dấu lúc lấy ra, một đỉnh có thể bị xếp vào queue nhiều lần trước khi được xử lý — sai khoảng cách và tốn bộ nhớ.

### Dùng BFS cho đồ thị có trọng số rồi tưởng là ngắn nhất

BFS đếm số cạnh, không cộng trọng số. Trên đồ thị có trọng số, kết quả BFS **không** phải đường rẻ nhất. Dùng Dijkstra (bài [12](./12-shortest-path-va-minimum-spanning-tree.md)).

### DFS đệ quy trên đồ thị rất sâu

Đồ thị sâu hàng chục nghìn đỉnh có thể làm tràn call stack với DFS đệ quy. Chuyển sang DFS dùng `Stack<T>` tường minh khi độ sâu lớn.

### Chỉ duyệt từ một đỉnh rồi tưởng đã thăm hết

Một lần duyệt chỉ tới được thành phần liên thông chứa nguồn. Đồ thị không liên thông cần khởi động lại từ mỗi đỉnh chưa thăm.

## 7. Bài tập

### Bài 1 — DFS bằng stack tường minh

Viết lại `Dfs` dùng `Stack<T>` thay đệ quy. So thứ tự thăm với bản đệ quy và giải thích chênh lệch (nếu có) do thứ tự đẩy hàng xóm.

**Gợi ý:** đẩy hàng xóm theo thứ tự đảo để lấy ra giống bản đệ quy; đánh dấu visited khi pop hoặc khi push (thử cả hai và quan sát).

### Bài 2 — Kiểm tra liên thông

Viết `bool IsConnected()` trả `true` nếu mọi đỉnh đều tới được từ một đỉnh bất kỳ. Dùng một lần BFS/DFS rồi so số đỉnh đã thăm với tổng số đỉnh.

**Gợi ý:** nếu số đỉnh thăm được `< V`, đồ thị không liên thông.

### Bài 3 — Đếm thành phần liên thông

Đếm số "cụm" tách rời trong đồ thị. Lặp qua mọi đỉnh, mỗi lần gặp đỉnh chưa thăm thì tăng bộ đếm và chạy một lần duyệt đánh dấu cả cụm.

**Gợi ý:** dùng chung một visited set qua các lần duyệt; số lần khởi động duyệt = số thành phần.

### Bài 4 — Phát hiện chu trình (vô hướng)

Viết hàm kiểm tra đồ thị vô hướng có chu trình không bằng DFS: gặp một đỉnh **đã thăm mà không phải cha** của node hiện tại nghĩa là có chu trình.

**Gợi ý:** truyền đỉnh cha xuống lời gọi đệ quy để phân biệt cạnh quay-lui hợp lệ với cạnh tạo chu trình.

### Bài 5 — Đường đi ngắn nhất mọi đỉnh

Mở rộng `ShortestPath` để trả về đường đi ngắn nhất từ nguồn tới **mọi** đỉnh, không chỉ một đích, chỉ với một lần BFS.

**Gợi ý:** chạy BFS đầy đủ (không dừng sớm), giữ parent map cho tất cả, rồi truy vết cho từng đích khi cần.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi cài được BFS bằng queue và DFS bằng đệ quy.
- [ ] Tôi giải thích được vì sao visited set là bắt buộc trong đồ thị có chu trình.
- [ ] Tôi dùng BFS tìm được đường ngắn nhất (số bước) trong đồ thị không trọng số.
- [ ] Tôi phân biệt thứ tự thăm theo tầng (BFS) và đi sâu (DFS).
- [ ] Tôi truy vết được đường đi bằng parent map.
- [ ] Tôi biết cả hai đều `O(V + E)` và kể được vài ứng dụng của mỗi loại.

Điều hướng:

- Bài prerequisite: [Graph và cách biểu diễn](./10-graph-va-cach-bieu-dien.md)
- Ôn lại nền tảng: [Stack, queue và deque](./05-stack-queue-va-deque.md), [Đệ quy và call stack](./02-de-quy-va-call-stack.md)
- Bài tiếp theo: [Shortest path và minimum spanning tree](./12-shortest-path-va-minimum-spanning-tree.md)
