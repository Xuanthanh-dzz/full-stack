# Dependency inversion

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, invariant hoặc adapter; CI failure

## TL;DR

- DIP đặt contract theo nhu cầu nghiệp vụ và cho adapter phụ thuộc contract đó.
- Dùng ở ranh giới file, mạng, thời gian để policy kiểm thử được độc lập.
- Interface không tự tạo transaction, chống trùng đồng thời hay bảo đảm gửi thông báo.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phát biểu DIP theo chiều phụ thuộc: module cấp cao không phụ thuộc module cấp thấp, cả hai phụ thuộc abstraction;
- xác định đâu là **policy** (quy tắc nghiệp vụ) và đâu là **detail** (file, database, mạng, đồng hồ);
- đặt interface ở phía policy và diễn đạt nó bằng ngôn ngữ của policy;
- cắt phụ thuộc vào thời gian hệ thống và I/O để code chạy tất định;
- vẽ được chiều mũi tên phụ thuộc trước và sau khi đảo;
- phân biệt DIP (nguyên tắc về chiều) với DI (kỹ thuật truyền phụ thuộc);
- tránh interface “đảo hình thức” chỉ sao chép API của thư viện hạ tầng.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Người xử lý đơn đưa ra yêu cầu “lưu đơn này”, thay vì dặn tên file và cách nối chuỗi. Người giữ kho chọn cách thực hiện; thay kho không bắt người xử lý học lại công nghệ lưu.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| policy | quy tắc quyết định nghiệp vụ | PlaceOrderService |
| detail | cách giao tiếp với bên ngoài | SystemClock/store |
| adapter | implementation nối contract với chi tiết | ConsoleNotifier |
| dependency direction | chiều code cần biết type nào | adapter biết interface |

### Ví dụ nhỏ — tính tay trước

Place A lần1 →Save rồi Notify. Lần2 cùng A →Duplicate, không đọc clock hay Notify nữa. Notifier ném sau Save: A vẫn có thể đã lưu.

Luồng đặt hàng được viết như sau:

```csharp
public sealed class PlaceOrderService
{
    private readonly FileOrderStore _store = new("orders.txt");
    private readonly SmtpEmailSender _email = new("smtp.company.local");

    public string Place(string orderId, string customerId, decimal total)
    {
        if (_store.Exists(orderId)) { return "duplicate"; }

        _store.Save(orderId, customerId, total, DateTimeOffset.UtcNow);
        _email.Send(customerId, $"Order {orderId} placed.");
        return "placed";
    }
}
```

Quy tắc nghiệp vụ ở đây rất nhỏ: không nhận đơn trùng, lưu đơn, báo cho khách. Nhưng class này không thể tồn tại nếu thiếu ổ đĩa và máy chủ SMTP:

- **Không kiểm thử được.** Chạy một lần là ghi file thật và gửi mail thật.
- **Không tất định.** `DateTimeOffset.UtcNow` khiến mỗi lần chạy ra kết quả khác nhau; không thể kiểm tra “đơn được ghi nhận đúng thời điểm nào”.
- **Không thay được hạ tầng.** Chuyển sang database nghĩa là sửa chính class chứa quy tắc nghiệp vụ.
- **Chiều phụ thuộc sai.** Phần ổn định nhất của hệ thống (quy tắc nghiệp vụ) đang phụ thuộc vào phần dễ đổi nhất (công nghệ lưu trữ, hạ tầng mail).

Dependency Inversion Principle nói: hãy để cả hai phía cùng phụ thuộc vào một abstraction, và abstraction đó phải được định nghĩa theo nhu cầu của phía nghiệp vụ.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project `.NET 9`:

```bash
mkdir DependencyInversionDemo
cd DependencyInversionDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `DependencyInversionDemo.csproj` bằng:

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

Thay toàn bộ `Program.cs`:

```csharp
using System.Collections.Generic;

namespace DependencyInversionDemo;

// ===== Phía POLICY: nghiệp vụ và các hợp đồng do nghiệp vụ định nghĩa =====

public sealed record PlacedOrder(
    string OrderId,
    string CustomerId,
    decimal Total,
    DateTimeOffset PlacedAtUtc);

public enum PlaceOutcome
{
    Placed = 0,
    Duplicate = 1,
    Rejected = 2
}

public sealed record PlaceResult(PlaceOutcome Outcome, string Message);

// Hợp đồng nói bằng ngôn ngữ nghiệp vụ: "lưu đơn", "đơn này đã tồn tại chưa".
public interface IOrderStore
{
    bool Exists(string orderId);

    void Save(PlacedOrder order);
}

public interface ICustomerNotifier
{
    void OrderPlaced(PlacedOrder order);
}

// Thời gian cũng là một phụ thuộc bên ngoài.
public interface IClock
{
    DateTimeOffset UtcNow { get; }
}

public sealed class PlaceOrderService
{
    private readonly IOrderStore _store;
    private readonly ICustomerNotifier _notifier;
    private readonly IClock _clock;
    private readonly decimal _maxTotal;

    public PlaceOrderService(
        IOrderStore store,
        ICustomerNotifier notifier,
        IClock clock,
        decimal maxTotal)
    {
        ArgumentNullException.ThrowIfNull(store);
        ArgumentNullException.ThrowIfNull(notifier);
        ArgumentNullException.ThrowIfNull(clock);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(maxTotal);

        _store = store;
        _notifier = notifier;
        _clock = clock;
        _maxTotal = maxTotal;
    }

    public PlaceResult Place(string orderId, string customerId, decimal total)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(orderId);
        ArgumentException.ThrowIfNullOrWhiteSpace(customerId);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(total);

        if (total > _maxTotal)
        {
            return new PlaceResult(
                PlaceOutcome.Rejected,
                $"{orderId} exceeds the {_maxTotal:N0} limit.");
        }

        if (_store.Exists(orderId))
        {
            return new PlaceResult(PlaceOutcome.Duplicate, $"{orderId} was already placed.");
        }

        var order = new PlacedOrder(orderId, customerId, total, _clock.UtcNow);
        _store.Save(order);
        _notifier.OrderPlaced(order);

        return new PlaceResult(PlaceOutcome.Placed, $"{orderId} placed at {order.PlacedAtUtc:O}.");
    }
}

// ===== Phía DETAIL: các adapter implement hợp đồng của policy =====

public sealed class InMemoryOrderStore : IOrderStore
{
    private readonly Dictionary<string, PlacedOrder> _orders = new(StringComparer.Ordinal);

    public IReadOnlyDictionary<string, PlacedOrder> Orders => _orders;

    public bool Exists(string orderId) => _orders.ContainsKey(orderId);

    public void Save(PlacedOrder order)
    {
        ArgumentNullException.ThrowIfNull(order);
        _orders[order.OrderId] = order;
    }
}

public sealed class CollectingNotifier : ICustomerNotifier
{
    private readonly List<string> _sent = new();

    public IReadOnlyList<string> Sent => _sent;

    public void OrderPlaced(PlacedOrder order)
    {
        ArgumentNullException.ThrowIfNull(order);
        _sent.Add($"{order.CustomerId} <- {order.OrderId}");
    }
}

public sealed class ConsoleNotifier : ICustomerNotifier
{
    public void OrderPlaced(PlacedOrder order)
    {
        ArgumentNullException.ThrowIfNull(order);
        Console.WriteLine($"  [notify] {order.CustomerId}: order {order.OrderId} confirmed");
    }
}

public sealed class FixedClock : IClock
{
    public FixedClock(DateTimeOffset now) => UtcNow = now.ToUniversalTime();

    public DateTimeOffset UtcNow { get; }
}

// Adapter thật cho môi trường chạy: chỉ nó biết về đồng hồ hệ thống.
public sealed class SystemClock : IClock
{
    public DateTimeOffset UtcNow => DateTimeOffset.UtcNow;
}

internal static class Program
{
    private static void Main()
    {
        // Composition root: nơi duy nhất biết cả policy lẫn detail.
        var store = new InMemoryOrderStore();
        var notifier = new CollectingNotifier();
        var clock = new FixedClock(new DateTimeOffset(2026, 7, 31, 9, 0, 0, TimeSpan.Zero));

        var service = new PlaceOrderService(store, notifier, clock, maxTotal: 10_000_000m);

        Print(service.Place("ORD-001", "CUS-001", 1_850_000m));
        Print(service.Place("ORD-001", "CUS-001", 1_850_000m));
        Print(service.Place("ORD-002", "CUS-002", 50_000_000m));
        Print(service.Place("ORD-003", "CUS-003", 350_000m));

        Console.WriteLine($"Stored: {store.Orders.Count}, notified: {notifier.Sent.Count}");
        foreach (string entry in notifier.Sent)
        {
            Console.WriteLine($"  {entry}");
        }

        // Đổi adapter, không đổi một dòng nào của PlaceOrderService.
        Console.WriteLine("--- cùng service, notifier khác ---");
        var second = new PlaceOrderService(
            new InMemoryOrderStore(),
            new ConsoleNotifier(),
            clock,
            maxTotal: 10_000_000m);

        Print(second.Place("ORD-010", "CUS-010", 99_000m));

        // SystemClock dành cho môi trường thật; demo không in giá trị của nó.
        IClock production = new SystemClock();
        Console.WriteLine($"Production clock uses UTC offset: {production.UtcNow.Offset == TimeSpan.Zero}");
    }

    private static void Print(PlaceResult result) =>
        Console.WriteLine($"{result.Outcome}: {result.Message}");
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Output:

```text
Placed: ORD-001 placed at 2026-07-31T09:00:00.0000000+00:00.
Duplicate: ORD-001 was already placed.
Rejected: ORD-002 exceeds the 10,000,000 limit.
Placed: ORD-003 placed at 2026-07-31T09:00:00.0000000+00:00.
Stored: 2, notified: 2
  CUS-001 <- ORD-001
  CUS-003 <- ORD-003
--- cùng service, notifier khác ---
  [notify] CUS-010: order ORD-010 confirmed
Placed: ORD-010 placed at 2026-07-31T09:00:00.0000000+00:00.
Production clock uses UTC offset: True
```

Dòng cuối chỉ kiểm tra offset UTC bằng 0, không phụ thuộc ngày chạy. Project được kiểm tra bằng .NET SDK `9.0.121`, target `net9.0`, không dùng package ngoài.

### Walkthrough — execution / state / cost

1. Main cấp store, notifier và fixed clock; service không tạo adapter.
2. Place validate và từ chối vượt limit trước khi hỏi Exists.
3. Chưa trùng thì đọc clock một lần, Save rồi OrderPlaced.
4. Dictionary/list giữ state trong process; lookup trung bình O(1). Network/file thực tế có latency và lỗi riêng, không được suy từ in-memory success.

### Mini-check

Clock ném, Save ném, notifier ném: ở mỗi điểm, những side effect nào đã có thể xảy ra?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Chiều mũi tên trước và sau

```text
TRƯỚC — policy phụ thuộc detail
  PlaceOrderService ──> FileOrderStore ──> System.IO
                   └──> SmtpEmailSender ──> mạng
                   └──> DateTimeOffset.UtcNow

SAU — cả hai phụ thuộc abstraction
  PlaceOrderService ──> IOrderStore        <── InMemoryOrderStore
                   ──> ICustomerNotifier   <── CollectingNotifier / ConsoleNotifier
                   ──> IClock              <── FixedClock / SystemClock
```

Mũi tên của các adapter bây giờ **chỉ ngược lên** phía nghiệp vụ. Đó là ý nghĩa của chữ “inversion”: chiều phụ thuộc lúc biên dịch đã bị đảo so với chiều gọi lúc chạy. Lúc chạy, `PlaceOrderService` vẫn gọi xuống adapter; nhưng lúc biên dịch, chỉ adapter biết tới interface, còn interface thì không biết gì về adapter.

### Abstraction phải nói ngôn ngữ của policy

So sánh hai cách khai báo:

```csharp
// Đảo hình thức: interface chỉ chép lại API của thư viện lưu file.
public interface IFileWriter { void WriteAllText(string path, string content); }

// Đảo thật: hợp đồng nói điều nghiệp vụ cần.
public interface IOrderStore { bool Exists(string orderId); void Save(PlacedOrder order); }
```

Với cách thứ nhất, `PlaceOrderService` vẫn phải biết về đường dẫn, về việc dữ liệu được nối thành chuỗi ra sao — tức là vẫn phụ thuộc chi tiết, chỉ thêm một lớp bọc. Với cách thứ hai, nghiệp vụ nói “lưu đơn hàng này” và mọi chuyện định dạng, đường dẫn, kết nối đều nằm bên trong adapter.

Câu hỏi kiểm tra: **nếu đổi từ file sang database, interface có phải đổi không?** Nếu có, interface đang thuộc về detail.

### Ai sở hữu interface

`IOrderStore` được khai báo cùng chỗ với `PlaceOrderService`, không phải cùng chỗ với `InMemoryOrderStore`. Điều này quan trọng khi tách thành nhiều project:

```text
project Domain        : PlacedOrder, PlaceResult, IOrderStore, ICustomerNotifier, IClock,
                        PlaceOrderService              (không tham chiếu tới đâu cả)
project Infrastructure: InMemoryOrderStore, SqlOrderStore, SmtpNotifier, SystemClock
                        ──> tham chiếu Domain
project App           : Main, nối dây  ──> tham chiếu cả hai
```

`Domain` không tham chiếu bất kỳ project nào — đó là kiểm chứng cơ học cho việc chiều phụ thuộc đã đúng. Cách chia project đã học ở [module 04, bài 14](../04-csharp-co-ban/14-project-solution-namespace-va-assembly.md); kiến trúc đầy đủ dựa trên ý này nằm ở [module 17](../PROGRESS.md#17-kien-truc-phan-mem).

### Thời gian là một phụ thuộc

`IClock` trông thừa cho tới khi bạn cần kiểm tra “đơn quá 30 ngày thì lưu trữ”. Với `DateTimeOffset.UtcNow` nằm rải rác trong code nghiệp vụ, việc kiểm tra biên thời gian khó kiểm soát nếu không tách nguồn thời gian ra khỏi quy tắc. Với `IClock`, bạn truyền vào bất kỳ thời điểm nào.

Trong sample, cả hai đơn thành công đều có cùng dấu thời gian — chính xác vì `FixedClock` trả một giá trị cố định. Output vì thế lặp lại được ở mọi máy.

### Đào sâu (có thể quay lại sau)

#### DIP không phải DI

- **DIP** là nguyên tắc về **chiều phụ thuộc**: nghiệp vụ không được phụ thuộc chi tiết.
- **DI (dependency injection)** là **kỹ thuật** truyền phụ thuộc từ ngoài vào, thường qua constructor.

Bạn có thể dùng DI mà vẫn vi phạm DIP: nếu constructor nhận thẳng `SmtpEmailSender` thay vì một interface do nghiệp vụ định nghĩa, phụ thuộc vẫn hướng về chi tiết. Ngược lại, một hệ thống nhỏ có thể đúng DIP mà chỉ dùng tham số method. [Bài 10](./10-dependency-injection-va-inversion-of-control.md) sẽ đi sâu vào kỹ thuật.

#### Chi phí và giới hạn

Mỗi abstraction là một lần gián tiếp. Nếu một chi tiết gần như chắc chắn không đổi và dễ kiểm thử — ví dụ `StringBuilder`, `Math`, hay một hàm thuần — thì việc bọc nó chỉ thêm nhiễu. Hãy đảo phụ thuộc ở **ranh giới với thế giới bên ngoài**: lưu trữ, mạng, thời gian, ngẫu nhiên, hệ thống file, tiến trình.

#### .NET đã có sẵn trừu tượng cho thời gian

Từ .NET 8, lớp `TimeProvider` trong `System` đóng đúng vai của `IClock` ; bản giả lập `FakeTimeProvider` được cung cấp qua package `Microsoft.Extensions.TimeProvider.Testing`, không phải type sẵn có trong thư viện nền `System`. Bài này tự viết `IClock` để bạn thấy rõ cơ chế; trong dự án thật, dùng `TimeProvider` giúp bạn khớp với các thư viện khác. Nguyên tắc không đổi: nghiệp vụ nhận thời gian từ ngoài.

#### Adapter cũng cần hợp đồng đúng

Một `SqlOrderStore` trả `false` từ `Exists` khi mất kết nối là vi phạm Liskov: nghiệp vụ sẽ tạo đơn trùng. Đảo phụ thuộc không tự làm adapter đúng; hợp đồng vẫn phải được tôn trọng như đã học ở [bài 6](./06-liskov-substitution.md).

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| DI concrete detail | truyền collaborator từ ngoài | vẫn phụ thuộc công nghệ cụ thể |
| DIP contract nghiệp vụ | policy không biết adapter | thêm contract cần duy trì |
| hàm thuần trực tiếp | không có external dependency | đơn giản khi không cần seam thay thế |

### Misconception check

**Đúng hay sai?** Exists rồi Save ngăn trùng khi hai caller chạy đồng thời.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: có khoảng giữa hai thao tác; cần atomic contract nếu có concurrency.

</details>

**Đúng hay sai?** Đổi notifier không ảnh hưởng lỗi service có thể gặp.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: adapter mới phải giữ failure contract; Save có thể đã thành công trước lỗi gửi.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** policy/detail.

- **Working Developer — dùng khi làm việc:** failure boundary và test doubles.

- **Deep Dive — có thể quay lại sau:** project references khi hệ thống lớn.

### Nhận diện policy và detail

| Câu hỏi | Policy | Detail |
|---|---|---|
| Đổi khi công nghệ đổi? | không | có |
| Đổi khi luật nghiệp vụ đổi? | có | hiếm |
| Chạy được không cần mạng/ổ đĩa? | có | không |
| Diễn đạt bằng từ vựng của ai? | người làm nghiệp vụ | kỹ sư hạ tầng |

Nếu một class trả lời lẫn lộn, nó đang trộn hai vai và cần tách như ở [bài 4](./04-single-responsibility.md).

### Ba cách nhận phụ thuộc

| Cách | Ví dụ | Khi nào dùng |
|---|---|---|
| Constructor | `new PlaceOrderService(store, notifier, clock, limit)` | phụ thuộc bắt buộc, dùng suốt vòng đời |
| Tham số method | `Archive(DateOnly today)` | giá trị thay đổi theo lời gọi |
| Property tùy chọn | hiếm | phụ thuộc thật sự tùy chọn, có mặc định an toàn |

Constructor injection là mặc định vì nó biến “thiếu phụ thuộc” thành lỗi ngay lúc tạo object.

### Danh sách phụ thuộc nên đảo

- Lưu trữ: file, database, cache, object storage.
- Giao tiếp: HTTP, SMTP, message broker.
- Môi trường: đồng hồ, biến môi trường, `Random`, `Guid.NewGuid()`, đường dẫn thư mục.
- Tiến trình: gọi chương trình ngoài, đọc bàn phím.

Điểm chung: chậm, có thể lỗi, hoặc cho kết quả khác nhau giữa các lần chạy.

### Kiểm chứng bằng cấu trúc project

Cách chắc chắn nhất để giữ chiều phụ thuộc là biến nó thành ràng buộc biên dịch: đặt policy vào một project không tham chiếu project hạ tầng. Khi ai đó lỡ dùng `SqlConnection` trong domain, build sẽ hỏng ngay. Kỹ thuật kiểm tra kiến trúc tự động sẽ gặp lại ở [module 17](../PROGRESS.md#17-kien-truc-phan-mem).

## 6. Lỗi thường gặp

### `new` chi tiết ngay trong class nghiệp vụ

```csharp
private readonly SmtpEmailSender _email = new("smtp.company.local");
```

Đây là dạng vi phạm phổ biến nhất và cũng dễ thấy nhất: chỉ cần tìm từ khóa `new` theo sau là một type hạ tầng bên trong code nghiệp vụ.

### Interface đặt ở phía hạ tầng

Nếu `IOrderStore` nằm cùng project với `SqlOrderStore` và được viết theo API của SQL, domain phải tham chiếu project hạ tầng để dùng nó. Mũi tên chưa đảo, chỉ có thêm một file.

### Bọc thư viện 1–1

`ILogger` với đúng các method của thư viện log bạn đang dùng, `IHttpClient` với đúng chữ ký của `HttpClient` — những abstraction này không giảm phụ thuộc, chỉ đổi tên nó. Hãy hỏi nghiệp vụ cần gì: có thể chỉ là `INotifyOrderPlaced`.

### Đọc `DateTime.Now` rải rác

Mỗi lời gọi là một điểm không tất định. Ngoài việc khó test, nó còn gây bug múi giờ. Lấy thời gian một lần ở ranh giới và truyền xuống dưới.

### Service locator thay cho injection

```csharp
var store = ServiceRegistry.Resolve<IOrderStore>();
```

Phụ thuộc biến mất khỏi chữ ký nên không ai biết class cần gì cho tới lúc chạy. [Bài 10](./10-dependency-injection-va-inversion-of-control.md) sẽ phân tích vì sao đây là antipattern.

### Đảo mọi thứ

Tạo `IStringFormatter`, `IMathHelper`, `IListWrapper` cho những thứ thuần túy và tất định chỉ làm code khó đọc. Đảo ở ranh giới, không đảo ở giữa.

### Quên rằng adapter cũng cần được kiểm thử

Với hợp đồng đã đảo, phần nghiệp vụ được kiểm thử dễ dàng, nhưng `SqlOrderStore` thì không tự đúng. Nó cần loại test riêng chạy với hạ tầng thật — nội dung của [module 14](../PROGRESS.md#14-testing-chat-luong).

### Rò rỉ chi tiết qua kiểu dữ liệu

Interface nghiệp vụ mà có method trả `DataTable`, `HttpResponseMessage` hay `JsonDocument` thì chi tiết đã lọt lên trên. Hợp đồng chỉ nên dùng type của chính domain.

## 7. Khi nào KHÔNG dùng

Không bọc Math/StringBuilder bằng interface riêng theo phản xạ. Không đưa file path hoặc JsonDocument vào contract nghiệp vụ chỉ vì adapter đang dùng chúng.

## 8. Production notes & scale check

Demo một caller tuần tự và clock UTC cố định. FixedClock chuẩn hóa offset; SystemClock kiểm offset thay vì ngày tương lai. Test thứ tự Save/Notify, duplicate không gửi lại, clock đọc một lần và failure propagation. Exactly-once, outbox hoặc retry cần yêu cầu riêng.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Adapter ghi file

Viết `FileOrderStore : IOrderStore` ghi mỗi đơn thành một dòng trong file tạm. `PlaceOrderService` không được sửa.

**Gợi ý:** `Exists` cần đọc lại file hoặc giữ index trong bộ nhớ; ghi rõ lựa chọn của bạn vào comment vì nó ảnh hưởng hợp đồng.

### Bài 2 — Kiểm thử quy tắc trùng đơn

Viết một method kiểm tra: gọi `Place` hai lần cùng `orderId` phải cho `Placed` rồi `Duplicate`, và store chỉ có một bản ghi.

**Gợi ý:** dùng `InMemoryOrderStore` và `FixedClock`; nếu bạn phải chờ hay dọn file thì thiết kế chưa đảo đủ.

### Bài 3 — Tìm chi tiết còn sót

Đọc lại `PlaceOrderService` và tìm mọi thứ có thể khiến hai lần chạy cho kết quả khác nhau. Nếu không còn, hãy thêm một quy tắc “đơn cuối tuần bị từ chối” và chỉ ra phụ thuộc mới phát sinh.

**Gợi ý:** quy tắc mới cần biết hôm nay là thứ mấy — nó đến từ `IClock` hay từ tham số?

### Bài 4 — Tách project

Chia sample thành ba project `Domain`, `Infrastructure`, `App` theo sơ đồ ở phần cơ chế và chạy lại.

**Gợi ý:** nếu `Domain` cần tham chiếu `Infrastructure` để build, hãy tìm xem type nào đang nằm sai chỗ.

### Bài 5 — Phân biệt DIP và DI

Viết hai phiên bản: một dùng DI nhưng vi phạm DIP (constructor nhận class hạ tầng cụ thể), một đúng DIP. Chỉ ra sự khác biệt khi cần đổi công nghệ lưu trữ.

**Gợi ý:** đếm số file phải sửa trong mỗi phiên bản; đó là thước đo trực tiếp nhất.

## 10. Bài tập tích hợp liên module — Judgment

So Save trước commit trong project Module04 với Save rồi Notify ở đây: nếu notify lỗi, caller nên retry toàn bộ hay cần contract mới? Chọn theo side effect thực tế, không tự thêm broker.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Compile dependency và runtime call khác gì?
2. IClock thuộc phía nào?
3. Notifier lỗi có rollback Save không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt được policy và detail trong một hệ thống cụ thể.
- [ ] Tôi vẽ được chiều mũi tên phụ thuộc trước và sau khi đảo.
- [ ] Tôi viết interface bằng ngôn ngữ nghiệp vụ, không sao chép API hạ tầng.
- [ ] Tôi đặt interface ở phía policy và kiểm chứng bằng tham chiếu project.
- [ ] Tôi cắt được phụ thuộc vào thời gian và I/O để chạy tất định.
- [ ] Tôi giải thích được DIP khác DI ở chỗ nào.
- [ ] Tôi build/run được sample trên `net9.0` và đối chiếu đúng output.

Điều hướng:

- Bài prerequisite: [Interface segregation](./07-interface-segregation.md)
- Ôn lại nền tảng: [Project, solution, namespace và assembly](../04-csharp-co-ban/14-project-solution-namespace-va-assembly.md)
- Bài tiếp theo: [Coupling và cohesion](./09-coupling-va-cohesion.md)
