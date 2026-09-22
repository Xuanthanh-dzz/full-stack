# Dự án: engine tìm đường

## 1. Mục tiêu

Sau bài này, bạn có thể:

- gói cả module thành một **engine tìm đường** hoàn chỉnh chạy trên lưới 2D có tường và địa hình;
- cài đặt và so sánh trực tiếp **BFS**, **Dijkstra** và **A\*** trên cùng bản đồ;
- giải thích vì sao BFS cho ít bước nhất còn Dijkstra cho chi phí thấp nhất;
- hiểu **A\*** = Dijkstra + heuristic, cho cùng lời giải tối ưu nhưng xét ít ô hơn hẳn;
- tổ chức code thành các lớp có trách nhiệm rõ ràng (`Grid`, `PathFinder`, `SearchResult`);
- đo và đối chiếu số ô đã xét để đánh giá hiệu quả thuật toán, không chỉ tính đúng/sai.

## 2. Bài toán mở đầu

Đây là dự án tổng kết module. Ta xây một **engine tìm đường** như trong game hoặc bản đồ: cho một lưới có ô trống (cỏ), ô tường không đi được, và ô địa hình khó (bùn — đi được nhưng tốn hơn), tìm đường từ điểm xuất phát `S` tới đích `G`.

Cùng một bản đồ, ba câu hỏi khác nhau:

- *Ít ô nhất?* — không quan tâm địa hình, chỉ đếm số bước. Đây là **BFS** (bài [11](./11-bfs-va-dfs.md)).
- *Rẻ nhất?* — cộng chi phí địa hình; đi vòng qua đường cỏ có thể rẻ hơn băng qua bùn. Đây là **Dijkstra** (bài [12](./12-shortest-path-va-minimum-spanning-tree.md)).
- *Rẻ nhất nhưng nhanh hơn?* — Dijkstra fan ra mọi hướng; nếu biết đích ở đâu, ta hướng tìm kiếm về phía đó. Đây là **A\***, mở rộng của Dijkstra.

Dự án này ghép graph, BFS, priority queue, Dijkstra và heuristic thành một chương trình chạy được, rồi **đo** để thấy tận mắt khác biệt giữa ba thuật toán trên cùng một bài toán.

## 3. Lời giải bằng code

Tạo project .NET 9 tên `Pathfinder` với cấu hình `.csproj` chuẩn của module (có `Nullable` và `TreatWarningsAsErrors`), rồi thay `Program.cs`:

```csharp
namespace Pathfinder;

internal static class Program
{
    private static void Main()
    {
        // '#': tường; '.': cỏ (chi phí 1); '~': bùn (chi phí 5); S: start; G: goal.
        string[] map =
        {
            "S....~~~~...G",
            ".###########.",
            ".###########.",
            ".###########.",
            ".............",
            ".............",
            ".............",
            ".............",
        };
        var grid = Grid.Parse(map);
        Console.WriteLine("Bản đồ (S=start, G=goal, #=tường, ~=bùn chi phí 5, .=cỏ chi phí 1):");
        grid.Print(grid.Start, grid.Goal, null);

        Console.WriteLine();
        Console.WriteLine("== BFS: ít Ô nhất (bỏ qua chi phí địa hình) ==");
        var bfs = PathFinder.Bfs(grid);
        Report(grid, bfs);

        Console.WriteLine();
        Console.WriteLine("== Dijkstra: RẺ nhất theo chi phí địa hình ==");
        var dij = PathFinder.Dijkstra(grid, useHeuristic: false);
        Report(grid, dij);

        Console.WriteLine();
        Console.WriteLine("== A*: cùng đường rẻ nhất, nhưng xét ít ô hơn nhờ heuristic ==");
        var astar = PathFinder.Dijkstra(grid, useHeuristic: true);
        Report(grid, astar);

        Console.WriteLine();
        Console.WriteLine("== So sánh ==");
        Console.WriteLine($"  BFS      : {bfs.Path.Count - 1} bước, chi phí {bfs.Cost}, xét {bfs.Explored} ô");
        Console.WriteLine($"  Dijkstra : {dij.Path.Count - 1} bước, chi phí {dij.Cost}, xét {dij.Explored} ô");
        Console.WriteLine($"  A*       : {astar.Path.Count - 1} bước, chi phí {astar.Cost}, xét {astar.Explored} ô");
    }

    private static void Report(Grid grid, SearchResult r)
    {
        if (r.Path.Count == 0)
        {
            Console.WriteLine("  Không có đường đi!");
            return;
        }
        grid.Print(grid.Start, grid.Goal, r.Path.ToHashSet());
        Console.WriteLine($"  Chi phí = {r.Cost}, số bước = {r.Path.Count - 1}, số ô đã xét = {r.Explored}");
    }
}

internal readonly record struct Cell(int Row, int Col);

internal sealed class Grid
{
    private readonly char[][] _cells;
    public int Rows { get; }
    public int Cols { get; }
    public Cell Start { get; }
    public Cell Goal { get; }

    private Grid(char[][] cells, Cell start, Cell goal)
    {
        _cells = cells;
        Rows = cells.Length;
        Cols = cells[0].Length;
        Start = start;
        Goal = goal;
    }

    public static Grid Parse(string[] map)
    {
        int width = map[0].Length;
        if (map.Any(row => row.Length != width))
        {
            throw new ArgumentException("Mọi hàng của bản đồ phải cùng độ rộng.");
        }
        var cells = map.Select(row => row.ToCharArray()).ToArray();
        Cell start = default, goal = default;
        for (int r = 0; r < cells.Length; r++)
            for (int c = 0; c < cells[r].Length; c++)
            {
                if (cells[r][c] == 'S') start = new Cell(r, c);
                if (cells[r][c] == 'G') goal = new Cell(r, c);
            }
        return new Grid(cells, start, goal);
    }

    public bool IsWall(Cell c) => _cells[c.Row][c.Col] == '#';

    public int CostOf(Cell c) => _cells[c.Row][c.Col] == '~' ? 5 : 1;

    public IEnumerable<Cell> Neighbors(Cell c)
    {
        // 4 hướng: lên, xuống, trái, phải
        var deltas = new[] { (-1, 0), (1, 0), (0, -1), (0, 1) };
        foreach (var (dr, dc) in deltas)
        {
            int nr = c.Row + dr, nc = c.Col + dc;
            if (nr >= 0 && nr < Rows && nc >= 0 && nc < Cols)
            {
                var next = new Cell(nr, nc);
                if (!IsWall(next)) yield return next;
            }
        }
    }

    public int Manhattan(Cell a, Cell b) => Math.Abs(a.Row - b.Row) + Math.Abs(a.Col - b.Col);

    public void Print(Cell start, Cell goal, HashSet<Cell>? path)
    {
        for (int r = 0; r < Rows; r++)
        {
            var sb = new System.Text.StringBuilder("  ");
            for (int c = 0; c < Cols; c++)
            {
                var cell = new Cell(r, c);
                char ch = _cells[r][c];
                if (cell == start) ch = 'S';
                else if (cell == goal) ch = 'G';
                else if (path is not null && path.Contains(cell)) ch = '*';
                sb.Append(ch).Append(' ');
            }
            Console.WriteLine(sb.ToString());
        }
    }
}

internal sealed class SearchResult
{
    public List<Cell> Path { get; init; } = new();
    public int Cost { get; init; }
    public int Explored { get; init; }
}

internal static class PathFinder
{
    public static SearchResult Bfs(Grid grid)
    {
        var prev = new Dictionary<Cell, Cell>();
        var visited = new HashSet<Cell> { grid.Start };
        var queue = new Queue<Cell>();
        queue.Enqueue(grid.Start);
        int explored = 0;

        while (queue.Count > 0)
        {
            Cell cur = queue.Dequeue();
            explored++;
            if (cur == grid.Goal) break;
            foreach (Cell next in grid.Neighbors(cur))
            {
                if (visited.Add(next))
                {
                    prev[next] = cur;
                    queue.Enqueue(next);
                }
            }
        }
        return Build(grid, prev, explored);
    }

    // useHeuristic = false -> Dijkstra thuần; true -> A* (thêm ước lượng Manhattan).
    public static SearchResult Dijkstra(Grid grid, bool useHeuristic)
    {
        var dist = new Dictionary<Cell, int> { [grid.Start] = 0 };
        var prev = new Dictionary<Cell, Cell>();
        var pq = new PriorityQueue<Cell, int>();
        pq.Enqueue(grid.Start, 0);
        int explored = 0;

        while (pq.TryDequeue(out Cell cur, out _))
        {
            explored++;
            if (cur == grid.Goal) break;
            foreach (Cell next in grid.Neighbors(cur))
            {
                int nd = dist[cur] + grid.CostOf(next);
                if (!dist.TryGetValue(next, out int old) || nd < old)
                {
                    dist[next] = nd;
                    prev[next] = cur;
                    // A*: ưu tiên = chi phí thực + ước lượng còn lại tới đích
                    int priority = nd + (useHeuristic ? grid.Manhattan(next, grid.Goal) : 0);
                    pq.Enqueue(next, priority);
                }
            }
        }
        return Build(grid, prev, explored, dist.GetValueOrDefault(grid.Goal));
    }

    private static SearchResult Build(Grid grid, Dictionary<Cell, Cell> prev, int explored, int? cost = null)
    {
        var path = new List<Cell>();
        if (grid.Start != grid.Goal && !prev.ContainsKey(grid.Goal))
        {
            return new SearchResult { Explored = explored };
        }
        Cell cur = grid.Goal;
        while (true)
        {
            path.Add(cur);
            if (cur == grid.Start) break;
            cur = prev[cur];
        }
        path.Reverse();
        int totalCost = cost ?? path.Skip(1).Sum(grid.CostOf);
        return new SearchResult { Path = path, Cost = totalCost, Explored = explored };
    }
}
```

Build và chạy:

```bash
dotnet build --configuration Release
dotnet run --configuration Release --no-build
```

Kết quả:

```text
Bản đồ (S=start, G=goal, #=tường, ~=bùn chi phí 5, .=cỏ chi phí 1):
  S . . . . ~ ~ ~ ~ . . . G 
  . # # # # # # # # # # # . 
  . # # # # # # # # # # # . 
  . # # # # # # # # # # # . 
  . . . . . . . . . . . . . 
  . . . . . . . . . . . . . 
  . . . . . . . . . . . . . 
  . . . . . . . . . . . . . 

== BFS: ít Ô nhất (bỏ qua chi phí địa hình) ==
  S * * * * * * * * * * * G 
  . # # # # # # # # # # # . 
  . # # # # # # # # # # # . 
  . # # # # # # # # # # # . 
  . . . . . . . . . . . . . 
  . . . . . . . . . . . . . 
  . . . . . . . . . . . . . 
  . . . . . . . . . . . . . 
  Chi phí = 28, số bước = 12, số ô đã xét = 46

== Dijkstra: RẺ nhất theo chi phí địa hình ==
  S . . . . ~ ~ ~ ~ . . . G 
  * # # # # # # # # # # # * 
  * # # # # # # # # # # # * 
  * # # # # # # # # # # # * 
  * * * * * * * * * * * * * 
  . . . . . . . . . . . . . 
  . . . . . . . . . . . . . 
  . . . . . . . . . . . . . 
  Chi phí = 20, số bước = 20, số ô đã xét = 67

== A*: cùng đường rẻ nhất, nhưng xét ít ô hơn nhờ heuristic ==
  S . . . . ~ ~ ~ ~ . . . G 
  * # # # # # # # # # # # * 
  * # # # # # # # # # # # * 
  * # # # # # # # # # # # * 
  * * * * * * * * * * * * * 
  . . . . . . . . . . . . . 
  . . . . . . . . . . . . . 
  . . . . . . . . . . . . . 
  Chi phí = 20, số bước = 20, số ô đã xét = 27

== So sánh ==
  BFS      : 12 bước, chi phí 28, xét 46 ô
  Dijkstra : 20 bước, chi phí 20, xét 67 ô
  A*       : 20 bước, chi phí 20, xét 27 ô
```

## 4. Giải thích cơ chế

### 4.1 Kiến trúc: mỗi lớp một trách nhiệm

Engine tách bạch trách nhiệm — đúng tinh thần SOLID của [module 06](../06-oop-va-thiet-ke/04-single-responsibility.md):

- **`Cell`** — một `record struct` bất biến giữ `(Row, Col)`. Là value type nên so sánh và băm theo giá trị, dùng làm khóa `Dictionary`/`HashSet` an toàn (bài [06](./06-hash-table-va-hash-function.md)).
- **`Grid`** — biết bản đồ: đâu là tường (`IsWall`), chi phí mỗi ô (`CostOf`), hàng xóm hợp lệ (`Neighbors`), và heuristic (`Manhattan`). Đây chính là một **đồ thị ẩn**: mỗi ô là một đỉnh, mỗi cặp ô kề nhau đi được là một cạnh (bài [10](./10-graph-va-cach-bieu-dien.md)).
- **`PathFinder`** — chứa ba thuật toán, không biết gì về cách vẽ hay cách lưu bản đồ, chỉ hỏi `Grid` qua interface của nó.
- **`SearchResult`** — gói kết quả: đường đi, chi phí, số ô đã xét.

Nhờ tách vậy, thêm thuật toán mới hay đổi cách biểu diễn bản đồ không đụng phần còn lại.

### 4.2 Lưới là một đồ thị ẩn

Ta không dựng `Dictionary<Cell, List<Cell>>` như bài [10](./10-graph-va-cach-bieu-dien.md); thay vào đó `Neighbors` **sinh** hàng xóm khi cần, từ bốn hướng và loại ô ngoài biên hoặc là tường. Đây là adjacency list "tính tại chỗ" — tiết kiệm bộ nhớ cho lưới lớn và là cách chuẩn để coi lưới như đồ thị. Mọi thuật toán đồ thị đã học chạy được ngay trên `Neighbors` này.

### 4.3 BFS: ít bước nhất, mù chi phí

`Bfs` y hệt bài [11](./11-bfs-va-dfs.md): queue, visited, parent map. Nó tìm đường **ít ô nhất** và **bỏ qua** `CostOf`. Kết quả: băng thẳng qua cầu bùn ở hàng trên — **12 bước**, nhưng chi phí **28** (bốn ô bùn ×5). BFS trả lời đúng câu hỏi "ít bước nhất", nhưng nếu bùn là đầm lầy thật thì đây là đường tệ.

### 4.4 Dijkstra: rẻ nhất, chấp nhận đi vòng

`Dijkstra` (với `useHeuristic: false`) cộng `CostOf` mỗi bước và dùng priority queue lấy ô có **chi phí tích lũy** nhỏ nhất — đúng bài [12](./12-shortest-path-va-minimum-spanning-tree.md). Nó **né** cầu bùn, đi vòng xuống bãi cỏ phía dưới: **20 bước** nhưng chi phí chỉ **20**. Nhiều bước hơn BFS mà rẻ hơn — vì mỗi ô cỏ chỉ tốn 1, còn mỗi ô bùn tốn 5. Đây là minh họa sống động: **ít bước nhất ≠ rẻ nhất** khi địa hình có chi phí khác nhau.

### 4.5 A\*: cùng đáp án, ít công hơn nhiều

Điểm hay nhất của dự án nằm ở cột "số ô đã xét". Dijkstra và A\* cho **cùng** đường rẻ nhất (chi phí 20, 20 bước), nhưng:

- Dijkstra xét **67 ô** — nó fan ra **mọi** hướng theo chi phí, khám phá gần như cả bãi cỏ trước khi chạm đích.
- A\* xét chỉ **27 ô** — chưa tới một nửa.

Bí quyết nằm ở một dòng:

```csharp
int priority = nd + (useHeuristic ? grid.Manhattan(next, grid.Goal) : 0);
```

Dijkstra xếp ưu tiên theo **chi phí đã đi** (`nd`). A\* xếp theo **chi phí đã đi + ước lượng còn lại tới đích** (khoảng cách Manhattan). Ước lượng này kéo tìm kiếm **về hướng đích** thay vì tỏa đều, nên A\* bỏ qua những ô đi xa khỏi G. Với cùng lời giải tối ưu, A\* làm ít việc hơn hẳn.

**Vì sao A\* vẫn tối ưu:** heuristic Manhattan **không bao giờ ước lượng quá** chi phí thật còn lại (mỗi bước tốn ít nhất 1, và Manhattan đếm đúng số bước tối thiểu). Heuristic "không phóng đại" như vậy gọi là **admissible**, và đó là điều kiện để A\* bảo đảm tìm được đường tối ưu. Nếu heuristic phóng đại, A\* nhanh hơn nhưng có thể cho đường không tối ưu.

### 4.6 Một hàm, hai thuật toán

Chú ý `Dijkstra` và A\* dùng **chung một hàm**, chỉ khác một cờ `useHeuristic`. Đó không phải trùng hợp: **A\* chính là Dijkstra cộng thêm heuristic**. Đặt heuristic = 0 (không biết gì về đích) thì A\* thoái hóa về Dijkstra. Hiểu điều này là hiểu cả họ thuật toán tìm đường: chúng chỉ khác nhau ở "hàm ưu tiên" đưa vào cùng một khung priority queue.

### Đào sâu (có thể quay lại sau)

- **Xử lý bản cũ trong PQ.** Như bài [12](./12-shortest-path-va-minimum-spanning-tree.md), `PriorityQueue` không hỗ trợ giảm khóa, nên ta enqueue bản mới khi tìm được đường rẻ hơn. Cài đặt chặt chẽ hơn sẽ bỏ qua ô đã chốt (một `HashSet` closed) để không xử lý lại; ở đây lưới nhỏ nên giữ code gọn.
- **8 hướng và đường chéo.** `Neighbors` hiện đi 4 hướng. Cho phép đi chéo (8 hướng) cần đổi heuristic sang khoảng cách Chebyshev/octile để giữ admissible — Manhattan sẽ phóng đại khi có đường chéo.
- **Trọng số heuristic.** Nhân heuristic với hệ số > 1 (weighted A\*) làm tìm kiếm nhanh hơn nữa nhưng mất bảo đảm tối ưu — một đánh đổi tốc độ/chất lượng dùng nhiều trong game thời gian thực.
- **Quy mô thật.** Bản đồ game/robot có hàng triệu ô. Lúc đó khác biệt 27 so với 67 ô nhân lên thành hàng trăm nghìn — A\* là lý do tìm đường thời gian thực khả thi. Các tối ưu thêm: jump point search, hierarchical pathfinding, precomputed nav-mesh.

## 5. Kiến thức nền

### Ba thuật toán, một khung

| Thuật toán | Hàm ưu tiên | Trả lời | Cần |
|---|---|---|---|
| BFS | thứ tự vào (FIFO) | ít bước nhất | đồ thị không trọng số |
| Dijkstra | chi phí đã đi `g` | rẻ nhất | trọng số không âm |
| A\* | `g` + heuristic `h` | rẻ nhất, ít xét hơn | `h` admissible |

Cả ba là **cùng một phép duyệt có ưu tiên**, chỉ khác thứ gì quyết định "lấy ô nào ra tiếp theo". Đây là cái nhìn thống nhất đáng giá nhất của cả module.

### Module này đã gom vào đây những gì

Dự án chạm gần như mọi bài:

- **Big-O** (bài [01](./01-big-o-thoi-gian-va-bo-nho.md)) — đọc "số ô đã xét" là đo độ phức tạp thực nghiệm.
- **Hash** (bài [06](./06-hash-table-va-hash-function.md)) — `Cell` làm khóa `Dictionary`/`HashSet`.
- **Đồ thị + BFS/DFS** (bài [10](./10-graph-va-cach-bieu-dien.md), [11](./11-bfs-va-dfs.md)) — lưới là đồ thị ẩn, parent map dựng đường.
- **Heap/priority queue** (bài [08](./08-heap-va-priority-queue.md)) — trái tim của Dijkstra và A\*.
- **Đường ngắn nhất** (bài [12](./12-shortest-path-va-minimum-spanning-tree.md)) — Dijkstra và mở rộng A\*.
- **Chọn cấu trúc** (bài [18](./18-bai-toan-tong-hop-va-chon-cau-truc-du-lieu.md)) — mỗi lớp một cấu trúc phù hợp.

### Từ đây đi đâu tiếp

Module [08 — SQL và CSDL](../08-sql-va-csdl/01-mo-hinh-quan-he-va-cai-dat-sql-server.md) là chặng kế. Nhiều ý tưởng ở đây quay lại dưới dạng khác: index của cơ sở dữ liệu là B-tree (họ hàng BST/tìm nhị phân), query planner chọn thuật toán join dựa trên chi phí (tư duy Big-O), và mô hình quan hệ là một dạng đồ thị. Nền cấu trúc dữ liệu này theo bạn suốt phần còn lại của lộ trình.

## 6. Lỗi thường gặp

### Dùng BFS cho bản đồ có địa hình

BFS bỏ qua chi phí, nên trên bản đồ có bùn/đồi, đường "ít bước nhất" của nó có thể đắt. Có trọng số thì dùng Dijkstra/A\*.

### Heuristic không admissible

Nếu `h` phóng đại chi phí còn lại (ví dụ dùng khoảng cách Euclid nhân hệ số lớn khi chỉ đi 4 hướng), A\* có thể trả đường **không** tối ưu. Với lưới 4 hướng, Manhattan là lựa chọn an toàn.

### Quên `Cell` phải là value type / có `Equals` đúng

`Cell` được dùng làm khóa hash khắp nơi. Nếu là class không ghi đè `Equals`/`GetHashCode`, hai ô cùng tọa độ bị coi là khác nhau — thuật toán loạn. `record struct` giải quyết gọn (bài [06](./06-hash-table-va-hash-function.md)).

### Không xử lý trường hợp không có đường

`Build` phải kiểm tra đích có nằm trong parent map không; bỏ qua sẽ ném lỗi khi truy vết đường không tồn tại. Luôn xử lý ca "bị tường vây kín".

### Đánh giá thuật toán chỉ bằng đúng/sai

BFS, Dijkstra, A\* đều cho đường "đúng" theo tiêu chí của chúng — điểm khác là **hiệu quả** (số ô xét). Bỏ qua chỉ số này là bỏ qua nửa bức tranh; đo nó mới thấy vì sao A\* đáng giá.

## 7. Bài tập

### Bài 1 — Đường đi 8 hướng

Cho `Neighbors` đi cả 4 đường chéo. Đổi heuristic sang octile distance để giữ admissible, và kiểm tra A\* vẫn tối ưu.

**Gợi ý:** octile = `max(dx,dy) + (√2−1)·min(dx,dy)`; với chi phí nguyên, có thể xấp xỉ; Manhattan sẽ phóng đại khi cho đi chéo.

### Bài 2 — Nhiều loại địa hình

Thêm ô `^` (đồi, chi phí 3) và `w` (nước, chi phí 10) vào `CostOf`. Quan sát Dijkstra/A\* đổi đường thế nào khi địa hình đổi.

**Gợi ý:** chỉ cần mở rộng `CostOf`; thuật toán không đổi — đó là ưu điểm của tách trách nhiệm.

### Bài 3 — Đếm ô xét theo kích thước bản đồ

Sinh bản đồ trống lớn dần (20×20, 50×50) và vẽ biểu đồ "số ô xét" của Dijkstra so với A\*. Khác biệt tăng thế nào?

**Gợi ý:** trên bản đồ trống, Dijkstra xét ~diện tích, A\* xét ~độ dài đường; khác biệt càng lớn khi bản đồ càng rộng.

### Bài 4 — Closed set tối ưu

Thêm một `HashSet<Cell> closed` để bỏ qua ô đã chốt, tránh xử lý lại bản cũ trong PQ. Đo số vòng lặp giảm bao nhiêu.

**Gợi ý:** khi lấy ô ra khỏi PQ, nếu đã trong `closed` thì bỏ qua; nếu không thì thêm vào rồi xử lý.

### Bài 5 — Bản đồ không có đường

Tạo bản đồ mà tường vây kín đích. Xác nhận cả ba thuật toán báo "không có đường đi" thay vì lỗi, và cùng xét đúng số ô tới được.

**Gợi ý:** `Build` trả `SearchResult` rỗng khi đích không nằm trong parent map; `Report` in thông báo phù hợp.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi tổ chức được engine thành `Grid`, `PathFinder`, `SearchResult` với trách nhiệm rõ ràng.
- [ ] Tôi cài và chạy được BFS, Dijkstra và A\* trên cùng bản đồ.
- [ ] Tôi giải thích được vì sao BFS ít bước nhất còn Dijkstra rẻ nhất.
- [ ] Tôi hiểu A\* = Dijkstra + heuristic admissible, tối ưu mà xét ít ô hơn.
- [ ] Tôi coi lưới như một đồ thị ẩn qua hàm `Neighbors`.
- [ ] Tôi đánh giá thuật toán bằng cả tính đúng lẫn số ô đã xét.

Điều hướng:

- Bài prerequisite: [Bài toán tổng hợp và chọn cấu trúc dữ liệu](./18-bai-toan-tong-hop-va-chon-cau-truc-du-lieu.md)
- Ôn lại nền tảng: [BFS và DFS](./11-bfs-va-dfs.md), [Shortest path và minimum spanning tree](./12-shortest-path-va-minimum-spanning-tree.md), [Heap và priority queue](./08-heap-va-priority-queue.md)
- Chặng tiếp theo: [Module 08 — SQL và cơ sở dữ liệu](../08-sql-va-csdl/01-mo-hinh-quan-he-va-cai-dat-sql-server.md)
- Theo dõi tiến độ: [PROGRESS.md](../PROGRESS.md)