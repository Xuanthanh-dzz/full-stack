# Shortest path và minimum spanning tree

## 1. Mục tiêu

Sau bài này, bạn có thể:

- giải thích vì sao đồ thị **có trọng số** cần thuật toán khác BFS để tìm đường rẻ nhất;
- cài đặt **Dijkstra** tìm đường đi ngắn nhất một nguồn bằng priority queue;
- cài đặt **Prim** tìm **cây khung nhỏ nhất (MST)** nối mọi đỉnh với tổng trọng số bé nhất;
- phân biệt hai bài toán: đường rẻ nhất giữa hai đỉnh khác với nối tất cả đỉnh rẻ nhất;
- nêu giới hạn của Dijkstra (không dùng được với trọng số âm) và biết Bellman-Ford, Kruskal là gì;
- đọc độ phức tạp `O(E log V)` của cả hai và hiểu vai trò của heap.

## 2. Bài toán mở đầu

Bài [11](./11-bfs-va-dfs.md), BFS tìm đường **ít cạnh nhất**. Nhưng thực tế cạnh có **chi phí** khác nhau: quãng đường km, giá vé, độ trễ mạng. Đi từ A tới E qua **2 chặng** (A-B-E) có thể tốn 14, trong khi đi **4 chặng** (A-C-B-D-E) chỉ tốn 11. BFS chọn ít chặng, nên chọn sai. Ta cần **Dijkstra** — thuật toán tìm đường **rẻ nhất theo tổng trọng số**.

Một bài toán họ hàng nhưng khác hẳn: cần rải cáp nối **tất cả** các thành phố sao cho tổng chiều dài cáp nhỏ nhất, không cần biết đường giữa hai thành phố cụ thể. Đó là **minimum spanning tree** — chọn một tập cạnh nối liền mọi đỉnh, không tạo chu trình, tổng trọng số bé nhất. **Prim** giải nó. Cả hai thuật toán đều dựa vào priority queue (bài [08](./08-heap-va-priority-queue.md)) để mỗi bước lấy ra lựa chọn rẻ nhất.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `PathMstDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace PathMstDemo;

internal static class Program
{
    private static void Main()
    {
        var g = new WeightedGraph();
        // (u, v, trọng số) — khoảng cách giữa các thành phố
        g.AddEdge("A", "B", 4);
        g.AddEdge("A", "C", 1);
        g.AddEdge("C", "B", 2);
        g.AddEdge("B", "D", 5);
        g.AddEdge("C", "D", 8);
        g.AddEdge("D", "E", 3);
        g.AddEdge("B", "E", 10);

        Console.WriteLine("== Dijkstra: đường đi RẺ NHẤT từ A (theo trọng số) ==");
        var (dist, prev) = g.Dijkstra("A");
        foreach (var kv in dist.OrderBy(k => k.Key))
        {
            Console.WriteLine($"  A -> {kv.Key}: chi phí {kv.Value}");
        }
        Console.WriteLine($"Đường A -> E: {string.Join(" -> ", WeightedGraph.BuildPath(prev, "A", "E"))}");
        Console.WriteLine("(BFS chỉ đếm số cạnh, sẽ chọn A-B-E = 2 cạnh nhưng chi phí 14)");

        Console.WriteLine();
        Console.WriteLine("== Prim: cây khung nhỏ nhất (MST) nối mọi thành phố ==");
        var (edges, total) = g.PrimMst("A");
        foreach (var e in edges)
        {
            Console.WriteLine($"  {e.U} - {e.V} (trọng số {e.Weight})");
        }
        Console.WriteLine($"Tổng trọng số MST = {total}");
    }
}

internal sealed class WeightedGraph
{
    private readonly Dictionary<string, List<(string To, int Weight)>> _adj = new();

    public void AddEdge(string u, string v, int weight)
    {
        Add(u); Add(v);
        _adj[u].Add((v, weight));
        _adj[v].Add((u, weight)); // vô hướng
    }

    private void Add(string v)
    {
        if (!_adj.ContainsKey(v)) _adj[v] = new List<(string, int)>();
    }

    // Dijkstra: dùng priority queue lấy đỉnh có chi phí tạm nhỏ nhất.
    public (Dictionary<string, int> Dist, Dictionary<string, string> Prev) Dijkstra(string source)
    {
        var dist = new Dictionary<string, int>();
        var prev = new Dictionary<string, string>();
        foreach (string v in _adj.Keys) dist[v] = int.MaxValue;
        dist[source] = 0;

        var pq = new PriorityQueue<string, int>();
        pq.Enqueue(source, 0);

        while (pq.TryDequeue(out string? u, out int d))
        {
            if (d > dist[u]) continue; // bản cũ đã lỗi thời, bỏ qua
            foreach (var (to, w) in _adj[u])
            {
                int nd = d + w; // chi phí đi qua u tới to
                if (nd < dist[to])
                {
                    dist[to] = nd;   // tìm được đường rẻ hơn
                    prev[to] = u;
                    pq.Enqueue(to, nd);
                }
            }
        }
        return (dist, prev);
    }

    public static List<string> BuildPath(Dictionary<string, string> prev, string source, string goal)
    {
        var path = new List<string>();
        string? node = goal;
        while (node is not null)
        {
            path.Add(node);
            if (node == source) break;
            node = prev.TryGetValue(node, out var p) ? p : null;
        }
        path.Reverse();
        return path;
    }

    // Prim: mọc cây khung từ một đỉnh, mỗi bước thêm cạnh rẻ nhất ra ngoài cây.
    public (List<(string U, string V, int Weight)> Edges, int Total) PrimMst(string start)
    {
        var inTree = new HashSet<string> { start };
        var result = new List<(string, string, int)>();
        int total = 0;

        // pq chứa các cạnh biên (trọng số, từ, tới)
        var pq = new PriorityQueue<(string From, string To), int>();
        foreach (var (to, w) in _adj[start]) pq.Enqueue((start, to), w);

        while (pq.TryDequeue(out var edge, out int w) && inTree.Count < _adj.Count)
        {
            if (inTree.Contains(edge.To)) continue; // đã trong cây -> bỏ (tránh chu trình)
            inTree.Add(edge.To);
            result.Add((edge.From, edge.To, w));
            total += w;
            foreach (var (to, nw) in _adj[edge.To])
            {
                if (!inTree.Contains(to)) pq.Enqueue((edge.To, to), nw);
            }
        }
        return (result, total);
    }
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
== Dijkstra: đường đi RẺ NHẤT từ A (theo trọng số) ==
  A -> A: chi phí 0
  A -> B: chi phí 3
  A -> C: chi phí 1
  A -> D: chi phí 8
  A -> E: chi phí 11
Đường A -> E: A -> C -> B -> D -> E
(BFS chỉ đếm số cạnh, sẽ chọn A-B-E = 2 cạnh nhưng chi phí 14)

== Prim: cây khung nhỏ nhất (MST) nối mọi thành phố ==
  A - C (trọng số 1)
  C - B (trọng số 2)
  B - D (trọng số 5)
  D - E (trọng số 3)
Tổng trọng số MST = 11
```

## 4. Giải thích cơ chế

Đồ thị có trọng số trong bài:

```text
        4
   A -------- B
   |  \      /|  \
  1|   \    / |   \10
   |    (2)   |5   \
   C ---------+     E
    \    8    |    /
     \--------D---/
              3
   (A-C:1, A-B:4, C-B:2, B-D:5, C-D:8, D-E:3, B-E:10)
```

### 4.1 Dijkstra: luôn mở rộng đỉnh rẻ nhất trước

Ý tưởng: giữ một `dist[v]` = chi phí rẻ nhất **đã biết** để tới `v` (khởi tạo vô cực, nguồn = 0). Dùng priority queue lấy ra đỉnh có `dist` nhỏ nhất, rồi thử **nới lỏng (relax)** các cạnh của nó: nếu đi qua `u` tới `to` rẻ hơn `dist[to]` hiện tại thì cập nhật.

Theo dõi từ A:
- Lấy A (0). Nới các cạnh: C = 1, B = 4.
- Lấy C (1, rẻ nhất). Nới: B = min(4, 1+2) = **3** (đường A-C-B rẻ hơn A-B trực tiếp!), D = 1+8 = 9.
- Lấy B (3). Nới: D = min(9, 3+5) = **8**, E = 3+10 = 13.
- Lấy D (8). Nới: E = min(13, 8+3) = **11**.
- Lấy E (11). Xong.

Kết quả `A→E = 11` qua `A-C-B-D-E` — đúng 4 cạnh nhưng **rẻ hơn** đường 2 cạnh A-B-E (chi phí 14). Đây chính là điều BFS không làm được.

**Vì sao đúng:** khi một đỉnh được lấy ra khỏi PQ, chi phí của nó đã là nhỏ nhất có thể — vì mọi đường khác tới nó phải đi qua một đỉnh có chi phí lớn hơn (đã hoặc sẽ lấy ra sau). Đây là bản chất "tham lam" của Dijkstra, và nó chỉ đúng khi **trọng số không âm**.

### 4.2 Xử lý "bản cũ lỗi thời" trong PQ

`PriorityQueue` của .NET không hỗ trợ "giảm khóa" một phần tử đang trong hàng. Nên khi tìm được đường rẻ hơn tới `to`, ta chỉ **enqueue thêm** một bản mới với chi phí nhỏ hơn — bản cũ vẫn nằm đó. Câu `if (d > dist[u]) continue;` bỏ qua bản cũ khi nó được lấy ra: nếu chi phí lấy ra lớn hơn `dist[u]` đã biết, đó là bản lỗi thời. Đây là mẫu chuẩn khi cài Dijkstra bằng binary heap.

### 4.3 Prim: mọc cây khung, luôn thêm cạnh rẻ nhất ra ngoài

MST là bài toán **khác**: không tìm đường giữa hai đỉnh, mà chọn tập cạnh **nối liền tất cả** đỉnh với tổng trọng số nhỏ nhất, không chu trình. Prim mọc dần từ một đỉnh:

- Bắt đầu cây = {A}. Cạnh biên: A-B(4), A-C(1).
- Lấy cạnh rẻ nhất ra ngoài cây: **A-C(1)**. Cây = {A, C}. Thêm cạnh biên của C: C-B(2), C-D(8).
- Rẻ nhất: **C-B(2)**. Cây = {A, C, B}. Thêm B-D(5), B-E(10).
- Rẻ nhất: **B-D(5)**. Cây = {A, C, B, D}. Thêm D-E(3).
- Rẻ nhất: **D-E(3)**. Cây đủ 5 đỉnh. Dừng.

Tổng = 1+2+5+3 = **11** với các cạnh A-C, C-B, B-D, D-E. Câu `if (inTree.Contains(edge.To)) continue;` bỏ các cạnh dẫn vào đỉnh đã ở trong cây — tránh tạo chu trình.

### 4.4 Hai bài toán, đừng nhầm

- **Shortest path (Dijkstra):** rẻ nhất **từ một nguồn tới các đỉnh**. Kết quả là cây đường đi ngắn nhất, tối ưu cho *khoảng cách từ nguồn*.
- **MST (Prim):** rẻ nhất để **nối tất cả**. Kết quả tối ưu cho *tổng chi phí kết nối*, không quan tâm đường giữa hai điểm cụ thể ngắn hay dài.

Cùng đồ thị, hai cây kết quả có thể khác nhau. Đây là hai câu hỏi khác nhau — chọn nhầm thuật toán cho câu hỏi sai.

### Đào sâu (có thể quay lại sau)

- **Độ phức tạp.** Cả Dijkstra lẫn Prim với binary heap là `O(E log V)`: mỗi cạnh có thể đẩy một mục vào PQ (`log V` mỗi thao tác), và ta xét mỗi cạnh một lần. Với heap Fibonacci, Dijkstra xuống `O(E + V log V)` về lý thuyết, nhưng binary heap thực tế thường nhanh hơn vì hằng số nhỏ.
- **Trọng số âm.** Dijkstra **sai** khi có cạnh trọng số âm (giả định "đã lấy ra là tối ưu" đổ vỡ). Dùng **Bellman-Ford** (`O(V·E)`), thuật toán này còn phát hiện được chu trình âm.
- **Kruskal cho MST.** Cách khác để tìm MST: sắp mọi cạnh theo trọng số tăng dần, thêm lần lượt cạnh nào không tạo chu trình (kiểm tra bằng cấu trúc union-find / disjoint set). Kruskal hợp với đồ thị thưa; Prim hợp khi bắt đầu từ một đỉnh và đồ thị dày.
- **All-pairs.** Cần đường ngắn nhất giữa **mọi cặp** đỉnh: chạy Dijkstra từ mỗi đỉnh, hoặc dùng **Floyd-Warshall** `O(V^3)` trên adjacency matrix — gọn khi `V` nhỏ.

## 5. Kiến thức nền

### Vì sao priority queue là trái tim của cả hai

Cả Dijkstra và Prim đều là thuật toán **tham lam**: mỗi bước chọn phương án rẻ nhất hiện có. "Lấy phần tử rẻ nhất, thêm phần tử mới" lặp đi lặp lại chính là hợp đồng của priority queue. Không có heap, mỗi bước phải quét tuyến tính để tìm min — biến thuật toán thành `O(V^2)` thay vì `O(E log V)`. Đây là ví dụ điển hình cấu trúc dữ liệu quyết định độ phức tạp thuật toán.

### Bảng chọn thuật toán

| Bài toán | Thuật toán | Điều kiện |
|---|---|---|
| Ít cạnh nhất (không trọng số) | BFS | trọng số đều nhau |
| Rẻ nhất, một nguồn | Dijkstra | trọng số **không âm** |
| Rẻ nhất, có trọng số âm | Bellman-Ford | phát hiện chu trình âm |
| Rẻ nhất mọi cặp | Floyd-Warshall | `V` nhỏ |
| Nối tất cả rẻ nhất (MST) | Prim / Kruskal | đồ thị liên thông |

### Ứng dụng thực tế

- Dijkstra: định tuyến bản đồ (Google Maps), định tuyến gói tin mạng, tìm chuỗi thao tác rẻ nhất.
- MST: thiết kế mạng lưới (điện, cáp, ống) chi phí thấp nhất, phân cụm dữ liệu, xấp xỉ bài toán người bán hàng.

## 6. Lỗi thường gặp

### Dùng Dijkstra với trọng số âm

Đây là lỗi cơ bản: Dijkstra cho kết quả sai (không phải chậm) khi có cạnh âm. Nếu dữ liệu có thể âm (ví dụ khuyến mãi làm chi phí âm), dùng Bellman-Ford.

### Quên xử lý bản cũ trong PQ

Không có câu `if (d > dist[u]) continue;`, thuật toán vẫn ra kết quả đúng nhưng xử lý lại các đỉnh đã tối ưu, chậm hơn. Với đồ thị lớn, bỏ bước này gây phí đáng kể.

### Nhầm shortest path với MST

Chạy Prim khi cần đường từ A tới E, hoặc chạy Dijkstra khi cần nối tất cả — cho ra đáp án cho câu hỏi khác. Xác định rõ câu hỏi trước khi chọn thuật toán.

### Thêm cạnh tạo chu trình trong Prim

Quên kiểm tra `inTree.Contains(edge.To)` khiến cây khung có chu trình và sai. Cạnh chỉ hợp lệ khi nối một đỉnh **trong** cây với một đỉnh **ngoài** cây.

### Khởi tạo khoảng cách sai

`dist` phải khởi tạo vô cực (`int.MaxValue`) cho mọi đỉnh trừ nguồn (0). Quên khởi tạo, hoặc cộng vào `int.MaxValue` gây tràn số — nên kiểm tra trước khi cộng nếu dùng sentinel lớn.

## 7. Bài tập

### Bài 1 — In đường đi tới mọi đỉnh

Dùng `prev` từ Dijkstra để in đường đi rẻ nhất từ A tới **từng** đỉnh, kèm tổng chi phí.

**Gợi ý:** gọi `BuildPath(prev, "A", đích)` cho mỗi đích; kết quả khớp cột chi phí trong output.

### Bài 2 — Đếm số cạnh được relax

Thêm bộ đếm mỗi lần một cạnh làm giảm `dist[to]`. Quan sát con số này thay đổi thế nào khi đổi thứ tự thêm cạnh.

**Gợi ý:** số lần relax thành công cho thấy thuật toán "sửa" ước lượng bao nhiêu lần trước khi ổn định.

### Bài 3 — MST bằng Kruskal

Cài Kruskal: sắp mọi cạnh tăng dần theo trọng số, thêm cạnh nào không tạo chu trình. So tổng trọng số với Prim (phải bằng nhau: 11).

**Gợi ý:** cần cấu trúc union-find để kiểm tra hai đỉnh đã cùng một thành phần chưa; nếu chưa, thêm cạnh và hợp nhất.

### Bài 4 — Dijkstra có đích, dừng sớm

Sửa Dijkstra để dừng ngay khi lấy được đỉnh đích ra khỏi PQ, thay vì xử lý hết. Giải thích vì sao dừng sớm vẫn cho đường tới đích đúng.

**Gợi ý:** khi đích được lấy ra, chi phí của nó đã tối ưu; các đỉnh chưa xử lý không thể làm nó rẻ hơn.

### Bài 5 — So sánh với BFS

Trên đồ thị trong bài, chạy BFS (coi mọi cạnh trọng số 1) tìm đường A→E rồi so với Dijkstra. Giải thích vì sao hai đường khác nhau.

**Gợi ý:** BFS tối ưu số cạnh (A-B-E, 2 cạnh), Dijkstra tối ưu tổng trọng số (A-C-B-D-E, chi phí 11); hai mục tiêu khác nhau.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi giải thích được vì sao BFS không đủ cho đồ thị có trọng số.
- [ ] Tôi cài được Dijkstra bằng priority queue và xử lý bản cũ lỗi thời.
- [ ] Tôi cài được Prim và tránh chu trình khi mọc cây khung.
- [ ] Tôi phân biệt rõ shortest path và minimum spanning tree.
- [ ] Tôi biết Dijkstra sai với trọng số âm và Bellman-Ford/Kruskal là gì.
- [ ] Tôi hiểu vì sao heap khiến cả hai đạt `O(E log V)`.

Điều hướng:

- Bài prerequisite: [BFS và DFS](./11-bfs-va-dfs.md)
- Ôn lại nền tảng: [Heap và priority queue](./08-heap-va-priority-queue.md), [Graph và cách biểu diễn](./10-graph-va-cach-bieu-dien.md)
- Bài tiếp theo: [Sorting](./13-sorting.md)
