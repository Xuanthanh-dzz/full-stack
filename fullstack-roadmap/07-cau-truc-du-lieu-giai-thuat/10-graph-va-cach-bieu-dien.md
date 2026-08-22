# Graph và cách biểu diễn

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng đúng thuật ngữ đồ thị: vertex, edge, directed/undirected, weighted, degree, cycle;
- biểu diễn đồ thị bằng **adjacency list** và **adjacency matrix**;
- so sánh hai cách biểu diễn về bộ nhớ và tốc độ các truy vấn;
- cài đặt đồ thị vô hướng với `AddEdge`, `Neighbors`, `HasEdge`, `Degree`;
- đọc độ phức tạp theo `V` (số đỉnh) và `E` (số cạnh);
- chọn cách biểu diễn phù hợp với đồ thị thưa hay dày.

## 2. Bài toán mở đầu

Rất nhiều thứ quanh ta là **mạng lưới các quan hệ**: thành phố nối bằng đường, người kết bạn với người, task phụ thuộc task, trang web dẫn link tới trang web. Cây (bài [07](./07-tree-va-binary-search-tree.md)) chỉ mô tả được quan hệ phân cấp một-cha; nhưng ở đây một nút có thể nối tới **nhiều** nút khác, và có thể tạo thành **vòng** (A→B→C→A). Cây không diễn tả nổi.

**Graph** là mô hình tổng quát cho mọi mạng lưới như vậy: một tập **đỉnh (vertex)** và một tập **cạnh (edge)** nối các cặp đỉnh. Trước khi chạy bất kỳ thuật toán nào trên đồ thị (tìm đường, lan truyền, sắp thứ tự), ta phải **lưu** nó trong bộ nhớ. Có hai cách kinh điển với đánh đổi rõ rệt — bài này dựng cả hai và chỉ ra khi nào dùng cái nào.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `GraphDemo` với cấu hình `.csproj` chuẩn của module, rồi thay `Program.cs`:

```csharp
namespace GraphDemo;

internal static class Program
{
    private static void Main()
    {
        // Đồ thị vô hướng: các thành phố nối nhau bằng đường.
        var g = new Graph<string>();
        g.AddEdge("A", "B");
        g.AddEdge("A", "C");
        g.AddEdge("B", "C");
        g.AddEdge("B", "D");
        g.AddEdge("C", "D");
        // E là đỉnh cô lập, không cạnh
        g.AddVertex("E");

        Console.WriteLine("== Adjacency list (danh sách kề) ==");
        g.PrintAdjacencyList();
        Console.WriteLine($"Số đỉnh V = {g.VertexCount}, số cạnh E = {g.EdgeCount}");

        Console.WriteLine();
        Console.WriteLine("== Truy vấn ==");
        Console.WriteLine($"  Hàng xóm của B: [{string.Join(", ", g.Neighbors("B"))}]");
        Console.WriteLine($"  Có cạnh A-D? {g.HasEdge("A", "D")}");
        Console.WriteLine($"  Có cạnh C-D? {g.HasEdge("C", "D")}");
        Console.WriteLine($"  Bậc (degree) của C: {g.Degree("C")}");

        Console.WriteLine();
        Console.WriteLine("== Cùng đồ thị dưới dạng adjacency matrix ==");
        g.PrintAdjacencyMatrix();
    }
}

internal sealed class Graph<T> where T : notnull
{
    // Mỗi đỉnh ánh xạ tới tập đỉnh kề nó.
    private readonly Dictionary<T, HashSet<T>> _adj = new();

    public int VertexCount => _adj.Count;

    public int EdgeCount
    {
        // Vô hướng: mỗi cạnh được đếm ở cả hai đầu -> chia 2.
        get
        {
            int half = 0;
            foreach (var set in _adj.Values) half += set.Count;
            return half / 2;
        }
    }

    public void AddVertex(T v)
    {
        if (!_adj.ContainsKey(v))
        {
            _adj[v] = new HashSet<T>();
        }
    }

    public void AddEdge(T u, T v)
    {
        AddVertex(u);
        AddVertex(v);
        _adj[u].Add(v); // vô hướng -> thêm cả hai chiều
        _adj[v].Add(u);
    }

    public IEnumerable<T> Neighbors(T v)
    {
        return _adj.TryGetValue(v, out var set)
            ? set.OrderBy(x => x)
            : Enumerable.Empty<T>();
    }

    public bool HasEdge(T u, T v)
    {
        return _adj.TryGetValue(u, out var set) && set.Contains(v);
    }

    public int Degree(T v)
    {
        return _adj.TryGetValue(v, out var set) ? set.Count : 0;
    }

    public void PrintAdjacencyList()
    {
        foreach (T v in _adj.Keys.OrderBy(x => x))
        {
            Console.WriteLine($"  {v}: [{string.Join(", ", Neighbors(v))}]");
        }
    }

    public void PrintAdjacencyMatrix()
    {
        var vertices = _adj.Keys.OrderBy(x => x).ToList();
        Console.WriteLine("     " + string.Join(" ", vertices));
        foreach (T row in vertices)
        {
            var cells = vertices.Select(col => HasEdge(row, col) ? "1" : "0");
            Console.WriteLine($"  {row}  {string.Join(" ", cells)}");
        }
    }
}
```

Build và chạy (`dotnet build -c Release` rồi `dotnet run -c Release --no-build`). Kết quả:

```text
== Adjacency list (danh sách kề) ==
  A: [B, C]
  B: [A, C, D]
  C: [A, B, D]
  D: [B, C]
  E: []
Số đỉnh V = 5, số cạnh E = 5

== Truy vấn ==
  Hàng xóm của B: [A, C, D]
  Có cạnh A-D? False
  Có cạnh C-D? True
  Bậc (degree) của C: 3

== Cùng đồ thị dưới dạng adjacency matrix ==
     A B C D E
  A  0 1 1 0 0
  B  1 0 1 1 0
  C  1 1 0 1 0
  D  0 1 1 0 0
  E  0 0 0 0 0
```

## 4. Giải thích cơ chế

### 4.1 Từ vựng đồ thị

Đồ thị trong bài (vẽ lại từ output):

```text
      A --- B
      |  \  | \
      |   \ |  D
      |    \| /
      C --- +
      (E cô lập, không cạnh)
```

- **Vertex (đỉnh):** A, B, C, D, E.
- **Edge (cạnh):** A-B, A-C, B-C, B-D, C-D. Ở đây là **vô hướng (undirected)**: cạnh A-B đi được cả hai chiều.
- **Degree (bậc):** số cạnh nối vào một đỉnh. C có bậc 3 (nối A, B, D).
- **Directed (có hướng):** nếu cạnh chỉ đi một chiều (A→B khác B→A), như "theo dõi" trên mạng xã hội hay phụ thuộc task.
- **Weighted (có trọng số):** mỗi cạnh mang một số (khoảng cách, chi phí) — cần cho bài tìm đường ngắn nhất (bài [12](./12-shortest-path-va-minimum-spanning-tree.md)).
- **Cycle (chu trình):** đường đi xuất phát và quay về cùng một đỉnh, như A-B-C-A. Đồ thị không có chu trình và có hướng gọi là **DAG**.

### 4.2 Adjacency list: mỗi đỉnh giữ danh sách hàng xóm

Cách biểu diễn ở đây: `Dictionary<T, HashSet<T>>` — mỗi đỉnh ánh xạ tới **tập các đỉnh kề** nó. Nhìn output: `B: [A, C, D]` nghĩa là B nối trực tiếp tới A, C, D.

Vì là đồ thị vô hướng, `AddEdge(u, v)` thêm cạnh ở **cả hai** chiều (`u` vào tập của `v` và ngược lại). Đó cũng là lý do `EdgeCount` phải chia đôi tổng số phần tử: mỗi cạnh được đếm hai lần.

Adjacency list **tiết kiệm bộ nhớ với đồ thị thưa** (ít cạnh): chỉ lưu đúng các cạnh thực sự tồn tại — tổng bộ nhớ `O(V + E)`. Lấy danh sách hàng xóm của một đỉnh là tức thì. Đây là biểu diễn mặc định cho hầu hết thuật toán đồ thị.

### 4.3 Adjacency matrix: bảng V×V ô 0/1

Cùng đồ thị dưới dạng ma trận: ô `[hàng][cột]` bằng 1 nếu có cạnh, 0 nếu không. Hàng B là `1 0 1 1 0` — nối A, C, D. Ma trận **đối xứng** qua đường chéo vì đồ thị vô hướng (ô A-B = ô B-A).

Ma trận cho phép kiểm tra `HasEdge(u, v)` trong `O(1)` (tra một ô), nhưng tốn `O(V^2)` bộ nhớ **bất kể** số cạnh — đỉnh E cô lập vẫn chiếm cả một hàng và một cột toàn 0. Với đồ thị thưa (mạng xã hội: hàng tỉ người nhưng mỗi người vài trăm bạn), ma trận lãng phí khủng khiếp.

### 4.4 Đọc độ phức tạp theo `V` và `E`

Đồ thị có **hai** đại lượng kích thước, nên độ phức tạp viết theo cả hai:

| Thao tác | Adjacency list | Adjacency matrix |
|---|---|---|
| Bộ nhớ | `O(V + E)` | `O(V^2)` |
| `HasEdge(u, v)` | `O(bậc của u)` | `O(1)` |
| Duyệt hàng xóm của `u` | `O(bậc của u)` | `O(V)` |
| Thêm cạnh | `O(1)` | `O(1)` |
| Duyệt toàn bộ cạnh | `O(V + E)` | `O(V^2)` |

Các thuật toán duyệt (BFS/DFS ở bài [11](./11-bfs-va-dfs.md)) chạy `O(V + E)` trên adjacency list — chính vì thế list là lựa chọn phổ biến.

### Đào sâu (có thể quay lại sau)

- **Dày hay thưa.** Đồ thị "dày" (E gần `V^2`, gần như mọi cặp đỉnh đều nối) thì ma trận không lãng phí và nhanh hơn cho `HasEdge`. Đồ thị "thưa" (`E` cỡ `V`) thì list thắng áp đảo. Phần lớn đồ thị thực tế là thưa.
- **Có hướng và trọng số.** Đồ thị có hướng: `AddEdge` chỉ thêm một chiều. Có trọng số: thay `HashSet<T>` bằng `Dictionary<T, double>` (hàng xóm → trọng số), hoặc ma trận lưu trọng số thay vì 0/1.
- **Đỉnh tùy ý.** Ở đây đỉnh là `string`; dùng `Dictionary` cho phép đỉnh là bất kỳ type nào có `Equals`/`GetHashCode`. Nếu đỉnh là số nguyên `0..V-1` liên tục, có thể dùng `List<int>[]` (mảng các danh sách) nhanh hơn.
- **Ứng dụng.** Bản đồ/định tuyến, mạng xã hội, web crawler, trình biên dịch (phụ thuộc), lịch build, mạng máy tính, khuyến nghị. Đồ thị là một trong những mô hình dùng nhiều nhất trong thực tế.

## 5. Kiến thức nền

### Cây là một loại đồ thị đặc biệt

Cây (bài [07](./07-tree-va-binary-search-tree.md)) chính là đồ thị **liên thông, không chu trình, có gốc** với mỗi node một cha. Mọi cây đều là đồ thị, nhưng đồ thị tổng quát hơn: cho phép chu trình, nhiều đường giữa hai đỉnh, và đỉnh không có "cha". Vì vậy các kỹ thuật duyệt cây sẽ được tổng quát hóa cho đồ thị ở bài sau — kèm một điểm mới quan trọng: phải nhớ đỉnh **đã thăm** để không lặp vô hạn trong chu trình.

### Chọn cách biểu diễn

- **Adjacency list** — mặc định. Dùng khi đồ thị thưa (đa số trường hợp) và thuật toán chủ yếu duyệt hàng xóm.
- **Adjacency matrix** — khi đồ thị dày, hoặc cần `HasEdge` `O(1)` liên tục, hoặc thuật toán bản chất là phép toán ma trận (ví dụ Floyd-Warshall ở bài [12](./12-shortest-path-va-minimum-spanning-tree.md)).

### Vì sao dùng `HashSet` cho hàng xóm

Dùng `HashSet<T>` thay `List<T>` cho tập hàng xóm giúp `HasEdge` là `O(1)` trung bình và tự loại cạnh trùng. Nếu cần giữ thứ tự chèn hoặc cho phép đa cạnh (multigraph), dùng `List<T>` thay thế.

## 6. Lỗi thường gặp

### Quên thêm cạnh cả hai chiều (đồ thị vô hướng)

Với đồ thị vô hướng, `AddEdge(u, v)` phải thêm `v` vào hàng xóm của `u` **và** `u` vào hàng xóm của `v`. Quên một chiều làm đồ thị sai lệch âm thầm — BFS/DFS sẽ bỏ sót đường.

### Dùng ma trận cho đồ thị thưa lớn

Ma trận `V^2` cho đồ thị hàng triệu đỉnh là bất khả thi về bộ nhớ. Mặc định dùng adjacency list; chỉ chọn ma trận khi đồ thị nhỏ hoặc dày.

### Đếm cạnh hai lần

Trong adjacency list vô hướng, tổng số phần tử trong mọi danh sách kề bằng `2E`. Quên chia đôi khi đếm cạnh cho ra số gấp đôi.

### Không xử lý đỉnh cô lập

Đỉnh E không có cạnh vẫn là một đỉnh hợp lệ. `AddVertex` riêng (không qua `AddEdge`) phải tạo được đỉnh với tập hàng xóm rỗng, nếu không E biến mất khỏi đồ thị.

### Lẫn lộn có hướng và vô hướng

Đọc nhầm một đồ thị có hướng thành vô hướng (hoặc ngược lại) làm sai toàn bộ thuật toán phía sau. Luôn xác định rõ cạnh đi một chiều hay hai chiều trước khi cài.

## 7. Bài tập

### Bài 1 — Đồ thị có hướng

Tạo lớp `DirectedGraph<T>` mà `AddEdge(u, v)` chỉ thêm một chiều. Thêm `InDegree`/`OutDegree` (số cạnh vào/ra). Kiểm tra với vài cạnh.

**Gợi ý:** out-degree là kích thước tập kề của `u`; in-degree phải quét mọi đỉnh khác xem có trỏ tới `v` không (hoặc bảo trì thêm một map ngược).

### Bài 2 — Đồ thị có trọng số

Đổi tập hàng xóm thành `Dictionary<T, double>` (hàng xóm → trọng số). Thêm `AddEdge(u, v, weight)` và `Weight(u, v)`.

**Gợi ý:** với vô hướng, lưu trọng số ở cả hai chiều; đây là chuẩn bị cho bài đường ngắn nhất.

### Bài 3 — Chuyển đổi qua lại

Viết hàm biến adjacency list thành adjacency matrix và ngược lại. Xác nhận hai chiều cho cùng một đồ thị.

**Gợi ý:** gán mỗi đỉnh một chỉ số `0..V-1` (một `Dictionary<T,int>`) để đánh vị trí hàng/cột.

### Bài 4 — Phát hiện đỉnh cô lập

Viết hàm liệt kê mọi đỉnh có bậc 0 (không cạnh nào). Kiểm tra với đồ thị trong bài (kết quả phải có E).

**Gợi ý:** duyệt các đỉnh, lọc theo `Degree(v) == 0`.

### Bài 5 — Bậc lớn nhất

Tìm đỉnh có bậc cao nhất (đỉnh "trung tâm" nhất). Với đồ thị trong bài, đó là B và C (cùng bậc 3).

**Gợi ý:** duyệt mọi đỉnh, giữ đỉnh có `Degree` lớn nhất; xử lý trường hợp nhiều đỉnh cùng bậc cao nhất.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi dùng đúng thuật ngữ vertex, edge, directed/undirected, degree, cycle.
- [ ] Tôi cài được đồ thị bằng adjacency list và tạo được adjacency matrix.
- [ ] Tôi so sánh được hai biểu diễn về bộ nhớ và tốc độ `HasEdge`/duyệt hàng xóm.
- [ ] Tôi đọc được độ phức tạp theo `V` và `E`.
- [ ] Tôi chọn đúng biểu diễn cho đồ thị thưa và đồ thị dày.
- [ ] Tôi hiểu cây là trường hợp đặc biệt của đồ thị.

Điều hướng:

- Bài prerequisite: [Trie](./09-trie.md)
- Ôn lại nền tảng: [Tree và binary search tree](./07-tree-va-binary-search-tree.md), [Hash table và hash function](./06-hash-table-va-hash-function.md)
- Bài tiếp theo: [BFS và DFS](./11-bfs-va-dfs.md)
