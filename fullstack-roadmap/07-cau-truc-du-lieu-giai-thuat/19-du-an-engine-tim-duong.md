# Dự án: engine tìm đường

> **Last verified:** 2026-09-23  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, cấu trúc dữ liệu hoặc thuật toán; CI failure

## TL;DR

- Route engine ghép graph, shortest path và contract input thành luồng kiểm chứng được.
- Dùng Dijkstra cho bản đồ có cost dương, chạy trong một process.
- Route đúng trên demo không chứng minh dữ liệu cập nhật đồng thời hoặc cost ngoài miền luôn an toàn.

## 1. Mục tiêu

Đây là checkpoint cuối Module 07. Sau dự án này, bạn phải có thể:

- biến một bài toán route thành weighted graph;
- chọn cấu trúc dữ liệu dựa trên operation;
- dùng `Dictionary`, `HashSet`, `PriorityQueue` và graph trong cùng một chương trình;
- cài Dijkstra và reconstruct route;
- phân biệt route ít chặng với route có tổng chi phí thấp nhất;
- xử lý input sai, vertex không tồn tại và route không thể đi tới;
- phân tích time/space complexity của solution;
- refactor code thành các component có trách nhiệm rõ ràng;
- viết test case cho success path và failure path;
- giải thích trade-off như khi code review trong công ty.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Mỗi địa điểm là một chấm, mỗi đường là một nối có giá. Bộ tìm đường giữ giá tốt nhất đã biết cho từng chấm và nhớ chấm trước đó để dựng lại hành trình.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| adjacency list | danh sách đường đi ra ở mỗi đỉnh | WeightedGraph |
| predecessor | đỉnh trước trên đường tốt nhất | previous |
| read-only view | API không cho caller sửa trực tiếp | GetRoads |
| unreachable | không có đường tới đích | Found=false |

### Ví dụ nhỏ — tính tay trước

Warehouse →Port có tổng 13 trong bản đồ mẫu. Input có khoảng trắng ngoài phải được Trim trước lookup và tra adjacency; start=target trả một đỉnh và cost 0.

Xây một **Route Engine** cho hệ thống giao hàng nội bộ.

Hệ thống có các điểm:

```text
Warehouse
District-1
District-2
District-3
Airport
Port
```

Mỗi tuyến đường có một cost:

```text
Warehouse --4-- District-1
Warehouse --2-- District-2
District-1 --1-- District-2
District-1 --5-- District-3
District-2 --8-- District-3
District-2 --10-- Airport
District-3 --2-- Airport
District-3 --6-- Port
Airport --3-- Port
```

Yêu cầu:

1. thêm location;
2. thêm road hai chiều có cost dương;
3. tìm route rẻ nhất giữa hai location;
4. trả cả tổng cost và danh sách location;
5. phát hiện location không tồn tại;
6. trả trạng thái rõ ràng khi không có route;
7. không cho road có cost âm;
8. không phụ thuộc UI, database hay web framework;
9. có thể mở rộng thành ASP.NET Core service ở module sau.

<a id="3-loi-giai-bang-code"></a>

<a id="3-loi-giai-tham-chieu-bang-code"></a>

## 3. Lời giải chạy được

Tạo project:

```bash
mkdir RouteEngine
cd RouteEngine
dotnet new console --framework net9.0 --use-program-main
```

`RouteEngine.csproj`:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
</Project>
```

Để dễ chạy và kiểm chứng, lời giải đầu tiên đặt toàn bộ type trong một `Program.cs`. Sau khi chạy đúng, phần 5 sẽ tách thành nhiều file.

`Program.cs`:

```csharp
namespace RouteEngine;

public sealed record Road(string To, int Cost);

public sealed record RouteResult(
    bool Found,
    long TotalCost,
    IReadOnlyList<string> Path)
{
    public static RouteResult NotFound() =>
        new(false, 0, Array.Empty<string>());
}

public sealed class WeightedGraph
{
    private readonly Dictionary<string, List<Road>> _adjacency =
        new(StringComparer.OrdinalIgnoreCase);

    public int VertexCount => _adjacency.Count;

    public IEnumerable<string> Vertices => _adjacency.Keys;

    public void AddLocation(string location)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(location);

        _adjacency.TryAdd(
            location.Trim(),
            new List<Road>());
    }

    public void AddUndirectedRoad(
        string from,
        string to,
        int cost)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(from);
        ArgumentException.ThrowIfNullOrWhiteSpace(to);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(cost);

        from = from.Trim();
        to = to.Trim();

        AddLocation(from);
        AddLocation(to);

        AddOrUpdateDirectedRoad(from, to, cost);
        AddOrUpdateDirectedRoad(to, from, cost);
    }

    public IReadOnlyList<Road> GetRoads(string location)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(location);

        if (!_adjacency.TryGetValue(
            location.Trim(),
            out List<Road>? roads))
        {
            throw new KeyNotFoundException(
                $"Unknown location: {location}");
        }

        return roads.AsReadOnly();
    }

    public bool Contains(string location)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(location);
        return _adjacency.ContainsKey(location.Trim());
    }

    private void AddOrUpdateDirectedRoad(
        string from,
        string to,
        int cost)
    {
        List<Road> roads = _adjacency[from];

        int index = roads.FindIndex(
            road => string.Equals(
                road.To,
                to,
                StringComparison.OrdinalIgnoreCase));

        if (index >= 0)
        {
            roads[index] = new Road(to, cost);
        }
        else
        {
            roads.Add(new Road(to, cost));
        }
    }
}

public sealed class RouteFinder
{
    private readonly WeightedGraph _graph;

    public RouteFinder(WeightedGraph graph)
    {
        ArgumentNullException.ThrowIfNull(graph);
        _graph = graph;
    }

    public RouteResult FindCheapest(
        string start,
        string target)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(start);
        ArgumentException.ThrowIfNullOrWhiteSpace(target);

        start = start.Trim();
        target = target.Trim();

        if (!_graph.Contains(start))
        {
            throw new KeyNotFoundException(
                $"Unknown start location: {start}");
        }

        if (!_graph.Contains(target))
        {
            throw new KeyNotFoundException(
                $"Unknown target location: {target}");
        }

        var distances = new Dictionary<string, long>(
            StringComparer.OrdinalIgnoreCase);

        var previous = new Dictionary<string, string?>(
            StringComparer.OrdinalIgnoreCase);

        foreach (string vertex in _graph.Vertices)
        {
            distances[vertex] = long.MaxValue;
        }

        distances[start] = 0;
        previous[start] = null;

        var queue = new PriorityQueue<string, long>();
        queue.Enqueue(start, 0);

        while (queue.TryDequeue(
            out string? current,
            out long queuedDistance))
        {
            if (queuedDistance != distances[current])
            {
                continue;
            }

            if (string.Equals(
                current,
                target,
                StringComparison.OrdinalIgnoreCase))
            {
                break;
            }

            foreach (Road road in _graph.GetRoads(current))
            {
                long candidate = checked(
                    queuedDistance + road.Cost);

                if (candidate >= distances[road.To])
                {
                    continue;
                }

                distances[road.To] = candidate;
                previous[road.To] = current;
                queue.Enqueue(road.To, candidate);
            }
        }

        if (distances[target] == long.MaxValue)
        {
            return RouteResult.NotFound();
        }

        var path = new List<string>();

        for (string? current = target;
             current is not null;
             current = previous[current])
        {
            path.Add(current);
        }

        path.Reverse();

        return new RouteResult(
            Found: true,
            TotalCost: distances[target],
            Path: path.AsReadOnly());
    }
}

internal static class Program
{
    private static void Main()
    {
        WeightedGraph graph = BuildGraph();
        var finder = new RouteFinder(graph);

        PrintRoute(
            "Warehouse",
            "Port",
            finder.FindCheapest("Warehouse", "Port"));

        PrintRoute(
            "Warehouse",
            "Airport",
            finder.FindCheapest("Warehouse", "Airport"));

        graph.AddLocation("Island");

        PrintRoute(
            "Warehouse",
            "Island",
            finder.FindCheapest("Warehouse", "Island"));

        ReportFailure(
            () => finder.FindCheapest("Unknown", "Port"));

        ReportFailure(
            () => graph.AddUndirectedRoad(
                "Warehouse",
                "Invalid",
                -1));
    }

    private static WeightedGraph BuildGraph()
    {
        var graph = new WeightedGraph();

        graph.AddUndirectedRoad(
            "Warehouse", "District-1", 4);

        graph.AddUndirectedRoad(
            "Warehouse", "District-2", 2);

        graph.AddUndirectedRoad(
            "District-1", "District-2", 1);

        graph.AddUndirectedRoad(
            "District-1", "District-3", 5);

        graph.AddUndirectedRoad(
            "District-2", "District-3", 8);

        graph.AddUndirectedRoad(
            "District-2", "Airport", 10);

        graph.AddUndirectedRoad(
            "District-3", "Airport", 2);

        graph.AddUndirectedRoad(
            "District-3", "Port", 6);

        graph.AddUndirectedRoad(
            "Airport", "Port", 3);

        return graph;
    }

    private static void PrintRoute(
        string from,
        string to,
        RouteResult result)
    {
        Console.WriteLine($"{from} -> {to}");

        if (!result.Found)
        {
            Console.WriteLine("  no route");
            return;
        }

        Console.WriteLine(
            $"  cost: {result.TotalCost}");

        Console.WriteLine(
            $"  path: {string.Join(" -> ", result.Path)}");
    }

    private static void ReportFailure(Action action)
    {
        try
        {
            action();
            Console.WriteLine("Expected failure: no");
        }
        catch (Exception ex)
        {
            Console.WriteLine(
                $"Expected {ex.GetType().Name}: {ex.Message}");
        }
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Kết quả route chính:

```text
Warehouse -> Port
  cost: 13
  path: Warehouse -> District-2 -> District-1 -> District-3 -> Airport -> Port
Warehouse -> Airport
  cost: 10
  path: Warehouse -> District-2 -> District-1 -> District-3 -> Airport
Warehouse -> Island
  no route
```

Hai dòng failure cuối phải cho thấy:

- `KeyNotFoundException` khi start location không tồn tại;
- `ArgumentOutOfRangeException` khi road cost âm.

Output đầy đủ:

```text
Warehouse -> Port
  cost: 13
  path: Warehouse -> District-2 -> District-1 -> District-3 -> Airport -> Port
Warehouse -> Airport
  cost: 10
  path: Warehouse -> District-2 -> District-1 -> District-3 -> Airport
Warehouse -> Island
  no route
Expected KeyNotFoundException: Unknown start location: Unknown
Expected ArgumentOutOfRangeException: cost ('-1') must be a non-negative and non-zero value. (Parameter 'cost')
Actual value was -1.
```

### Walkthrough — execution / state / cost

1. Builder validate tên và cost dương trước thêm cạnh; graph giữ các danh sách trong RAM.
2. FindCheapest chuẩn hóa start/target một lần, kiểm đỉnh tồn tại rồi khởi tạo distance kiểu long.
3. Heap chọn cost nhỏ nhất, bỏ entry cũ; relax lưu previous.
4. Dựng path từ target ngược về start rồi reverse. Read-only wrapper bảo vệ API, không biến graph thành snapshot bất biến hay thread-safe.

### Mini-check

Vì sao chỉ Trim trong ContainsLocation mà không Trim biến dùng tra Dictionary vẫn có thể lỗi?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Domain model

`WeightedGraph` chịu trách nhiệm:

- location;
- road;
- invariant cost dương;
- adjacency list.

`RouteFinder` chịu trách nhiệm:

- thuật toán tìm route;
- distance;
- predecessor;
- priority queue;
- reconstruct path.

`Program` chỉ:

- dựng sample;
- gọi use case;
- in output.

Ranh giới này quan trọng vì ở module ASP.NET Core, `Program`/console UI có thể được thay bằng controller hoặc endpoint nhưng thuật toán không cần đổi.

### Vì sao dùng adjacency list?

Graph tuyến đường thường sparse:

```text
mỗi location chỉ nối một số location lân cận
```

Adjacency list có memory:

```text
O(V + E)
```

phù hợp hơn matrix `O(V²)`.

### Vì sao dùng Dictionary?

Ta cần lookup adjacency theo location name thường xuyên:

```text
location -> roads
```

`Dictionary` cho average lookup gần `O(1)`.

### Vì sao dùng PriorityQueue?

Dijkstra luôn cần lấy vertex có tentative distance nhỏ nhất.

Nếu mỗi vòng scan toàn bộ vertex:

```text
O(V²)
```

Với binary heap priority queue + adjacency list, complexity điển hình:

```text
O((V + E) log V)
```

### Route reconstruction

Dijkstra không chỉ lưu distance:

```text
distance[Airport] = 10
```

mà còn lưu:

```text
previous[Airport] = District-3
previous[District-3] = District-1
...
```

Sau khi tới target:

```text
target -> previous -> previous -> ... -> start
```

rồi reverse.

### Stale queue entry

Khi tìm được distance tốt hơn cho cùng vertex, sample enqueue lại.

Entry cũ vẫn còn trong heap.

Kiểm tra:

```csharp
if (queuedDistance != distances[current])
{
    continue;
}
```

bỏ entry stale.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| BFS | mọi cạnh cùng cost | đếm bước đủ |
| Dijkstra | cost không âm; mẫu bắt buộc dương | heap, distance và predecessor |
| MST | nối toàn mạng với tổng thấp | không trả route tối ưu giữa hai điểm |

### Misconception check

**Đúng hay sai?** int.MaxValue có thể dùng làm unreachable khi cạnh cũng là int.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: đó có thể là cost hợp lệ; mẫu dùng long và sentinel khác miền một cạnh.

</details>

**Đúng hay sai?** Read-only roads không bao giờ thay đổi.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: wrapper có thể thấy thay đổi từ owner; không iterate cùng lúc mutation.

</details>

<a id="5-kien-thuc-nen"></a>

<a id="5-kien-thuc-nen-va-thiet-ke"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace từ input tới route.

- **Working Developer — dùng khi làm việc:** failure và ownership contracts.

- **Deep Dive — có thể quay lại sau:** snapshot/cache khi có workload thật.

Sau khi bản single-file chạy đúng, refactor thành:

```text
RouteEngine/
├── RouteEngine.csproj
├── Program.cs
├── Domain/
│   ├── Road.cs
│   └── RouteResult.cs
├── Graph/
│   └── WeightedGraph.cs
└── Services/
    └── RouteFinder.cs
```

### Contract của RouteFinder

Input:

```text
start
target
```

Output:

```text
RouteResult
├── Found
├── TotalCost
└── Path
```

Không trả `null` cho trường hợp không có route vì `RouteResult.NotFound()` làm state rõ ràng hơn.

### Test matrix tối thiểu

| Case | Expected |
|---|---|
| start == target | cost 0, path chứa start |
| direct edge | chọn edge đó nếu tối ưu |
| route nhiều edge rẻ hơn direct | chọn route nhiều edge |
| target disconnected | `Found=false` |
| unknown start | exception |
| unknown target | exception |
| negative/zero cost | bị từ chối |
| duplicate road | policy update rõ ràng |
| casing khác nhau | vẫn lookup được theo policy hiện tại |

### Test không chỉ happy path

Một junior developer đi làm cần quen với:

```text
success path
+
boundary
+
invalid input
+
unreachable
+
duplicate/update
```

Không chỉ chạy một route đẹp rồi coi project hoàn thành.

### Vì sao chưa dùng database?

Module 07 tập trung DSA.

Nếu nhét SQL/EF Core vào đây, ta không biết bug đến từ:

- graph;
- algorithm;
- query;
- mapping;
- connection;
- migration.

Tách concern giúp học và debug rõ hơn.

Ở module 08–09, graph data có thể được load từ SQL/EF Core.

## 6. Lỗi thường gặp

### Dùng BFS cho weighted route

BFS tối thiểu số edge, không tối thiểu tổng cost.

Ví dụ:

```text
A --100--> B

A --1--> C --1--> B
```

BFS có thể thích đường một edge, nhưng cost 100 lớn hơn 2.

### Cho phép cost âm

Dijkstra không đúng tổng quát với negative edge.

Invariant phải được chặn ngay khi add road.

### Trộn console I/O vào algorithm

Không viết:

```csharp
Console.WriteLine(...)
```

bên trong `RouteFinder`.

Service nên trả data; presentation layer quyết định hiển thị.

### Dùng string mà không có comparison policy

Sample chọn:

```csharp
StringComparer.OrdinalIgnoreCase
```

cho identifier dạng text.

Trong production, location có thể cần ID riêng thay vì dùng tên làm identity.

### Không kiểm tra overflow

Distance là tổng nhiều cost int dương. Sample dùng long và checked: cạnh int.MaxValue vẫn là route hợp lệ thay vì trùng sentinel unreachable. Long không thay chính sách giới hạn dữ liệu hoặc xử lý lỗi tài nguyên.

### Expose mutable adjacency

Không trả trực tiếp `List<Road>` cho caller sửa.

Sample trả wrapper AsReadOnly để chặn cast về List; view vẫn phản ánh update của graph. Không mutate graph khi một query đang chạy; wrapper không tự tạo snapshot hay thread safety.

## 7. Khi nào KHÔNG dùng

Không thêm database, broker hoặc kiến trúc phân tán cho bản đồ nhỏ trong RAM. Không gọi FindCheapest đồng thời với sửa graph mà chưa có policy snapshot/locking.

## 8. Production notes & scale check

Gate kiểm route/cost, unreachable, start=target, whitespace, invalid edge, read-only API và cost lớn. Seed graph nhỏ đối chiếu oracle độc lập; không coi đó là benchmark hoặc chứng minh mọi graph. Bộ nhớ search O(V+E) với lazy heap.

<a id="7-bai-tap"></a>

<a id="7-bai-tap-mo-rong"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Route ít chặng nhất

Thêm:

```csharp
FindFewestStops(start, target)
```

dùng BFS.

Sau đó tạo input mà route ít chặng khác route rẻ nhất.

### Bài 2 — Directed road

Hỗ trợ đường một chiều.

Yêu cầu API rõ:

```text
AddDirectedRoad
AddUndirectedRoad
```

### Bài 3 — Route theo thời gian

Đổi `Cost` thành minutes.

Thêm road có:

```text
DistanceKm
TravelMinutes
Toll
```

Thiết kế strategy chọn weight theo mục tiêu.

### Bài 4 — Multi-criteria

User chọn:

```text
Cheapest
Fastest
ShortestDistance
```

Không copy ba bản Dijkstra.

Hãy truyền một weight selector hoặc strategy.

### Bài 5 — Load file

Đọc CSV:

```text
from,to,cost
Warehouse,District-1,4
...
```

Parse, validate rồi build graph.

### Bài 6 — Unit tests

Tạo xUnit project và test toàn bộ test matrix ở phần 5.

### Bài 7 — Performance test

Sinh graph:

```text
1,000 vertices
10,000 edges
```

đo route lookup.

Sau đó tăng 10 lần và quan sát scaling.

Không kết luận chỉ từ một lần chạy.

### Bài 8 — API-ready contract

Thiết kế DTO tương lai:

```csharp
public sealed record RouteRequest(
    string From,
    string To);

public sealed record RouteResponse(
    long TotalCost,
    IReadOnlyList<string> Path);
```

Chưa cần ASP.NET Core, chỉ cần contract.

## 10. Bài tập tích hợp liên module — Judgment

Từ Module06: boundary nào sở hữu normalization và invariant cost? Nếu bản đồ100 đỉnh đổi mỗi ngày, chọn snapshot đơn giản hay dịch vụ phân tán; giải thích bằng workload.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Previous phục vụ bước nào?
2. Graph giữ state ở đâu?
3. Cost lớn khác unreachable thế nào?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

<a id="8-checklist-hoan-thanh-module-07"></a>

## 12. Checklist tự đánh giá & điều hướng

### Kiến thức

- [ ] Tôi phân tích được Big-O time/space.
- [ ] Tôi hiểu recursion và call stack.
- [ ] Tôi phân biệt array, linked list, stack, queue, hash table.
- [ ] Tôi hiểu tree, BST, heap và trie.
- [ ] Tôi biểu diễn được graph.
- [ ] Tôi dùng được BFS và DFS.
- [ ] Tôi hiểu Dijkstra và MST khác nhau.
- [ ] Tôi hiểu sorting/searching cơ bản.
- [ ] Tôi phân biệt greedy, backtracking và dynamic programming.
- [ ] Tôi chọn cấu trúc dữ liệu dựa trên operation.

### Project

- [ ] Route engine build với warnings-as-errors.
- [ ] Happy path cho kết quả đúng.
- [ ] Disconnected target trả `Found=false`.
- [ ] Invalid location được xử lý.
- [ ] Cost không dương bị chặn.
- [ ] Có test cho critical path.
- [ ] Có README mô tả cách chạy.
- [ ] Có phân tích complexity.
- [ ] Code đã tách domain/graph/service sau khi bản đầu chạy đúng.
- [ ] Tôi giải thích được từng lựa chọn structure/algorithm mà không đọc thuộc lòng.

Điều hướng:

- Bài trước: [Bài toán tổng hợp và chọn cấu trúc dữ liệu](./18-bai-toan-tong-hop-va-chon-cau-truc-du-lieu.md)
- Quay lại: [Big-O](./01-big-o-thoi-gian-va-bo-nho.md)
- Module tiếp theo: [SQL và cơ sở dữ liệu](../PROGRESS.md#08-sql-va-csdl)

---

## Definition of Done của project

Project chỉ hoàn thành khi:

```text
clone/build trên môi trường sạch
        +
warnings-as-errors
        +
test success/failure path
        +
không negative edge
        +
reconstruct path đúng
        +
giải thích complexity
        +
README đủ lệnh chạy
```

Mục tiêu cuối cùng của Module 07 không phải “nhớ tên 12 cấu trúc dữ liệu”, mà là có thể nhìn một requirement và trả lời:

> Operation chính là gì, constraint là gì, cấu trúc nào phù hợp, complexity ra sao và trade-off nào chấp nhận được?

### Checkpoint sau cụm bài

- [Failure Lab](./failure-labs/04-alias.md)
- [Spaced Review](./reviews/review-04.md)
- [PR Review](./pr-review-labs/01-route.md)
