# Dependency injection và inversion of control

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, invariant hoặc adapter; CI failure

## TL;DR

- DI truyền phụ thuộc từ ngoài; lifetime quyết định tái sử dụng object.
- Dùng composition root và scope khi state dùng chung khác state theo yêu cầu.
- Transient không tự chết sau call; singleton không tự thread-safe.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt IoC (ai điều khiển) với DI (cách nhận phụ thuộc) và với DIP (chiều phụ thuộc);
- dùng constructor injection làm mặc định và biết khi nào method injection hợp lý hơn;
- gom toàn bộ việc nối dây vào một composition root duy nhất;
- tự cài đặt ba lifetime — singleton, scoped, transient — và giải thích hệ quả của từng loại;
- nhận ra captive dependency và các lỗi lifetime khác;
- giải thích vì sao service locator là antipattern;
- biết vị trí của DI container trong .NET và khi nào bạn chưa cần tới nó.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Hai yêu cầu dùng chung tủ đơn hàng nhưng mỗi yêu cầu có nhãn theo dõi riêng. Người lắp ứng dụng quyết định vật nào dùng chung, vật nào tạo mới; handler chỉ dùng vật được giao.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| composition root | nơi nối các collaborator | Main và CompositionRoot |
| singleton | một instance trong root/provider | store/log |
| scoped | một instance trong đơn vị công việc | RequestContext |
| transient | instance mới mỗi lần tạo | CreateHandler |

### Ví dụ nhỏ — tính tay trước

CreateHandler hai lần trong req1 →hai handler khác nhau, cùng audit. req2 →audit/context khác nhưng cùng store; duplicate ORD1 vẫn được thấy.

Sau [bài 8](./08-dependency-inversion.md), các class nghiệp vụ đã nhận phụ thuộc qua constructor. Câu hỏi kế tiếp rất thực tế: **ai tạo ra chúng, và tạo bao nhiêu lần?**

Ứng dụng xử lý nhiều yêu cầu đặt hàng trong một lần chạy. Với mỗi yêu cầu, ta cần:

- một kho dữ liệu **dùng chung** cho cả chương trình — nếu mỗi yêu cầu tạo một kho riêng, đơn hàng lưu ở yêu cầu trước sẽ biến mất;
- một mã tương quan (correlation id) **riêng cho từng yêu cầu**, để mọi dòng nhật ký của cùng một yêu cầu gắn với nhau;
- một handler xử lý **tạo mới mỗi lần** cho gọn, vì nó không giữ trạng thái nào đáng chia sẻ.

Nếu để mỗi class tự `new` phụ thuộc của mình, ba yêu cầu trên không thể cùng đúng: `new InMemoryOrderStore()` bên trong handler nghĩa là mỗi yêu cầu có một kho riêng. Nếu ngược lại, để tất cả thành `static`, mã tương quan của hai yêu cầu sẽ đè lên nhau — đúng dạng common coupling đã thấy ở [bài 9](./09-coupling-va-cohesion.md).

Câu trả lời là tách hẳn việc **tạo object** ra khỏi việc **dùng object**, rồi đặt việc tạo vào đúng một nơi.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project `.NET 9`:

```bash
mkdir DependencyInjectionDemo
cd DependencyInjectionDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `DependencyInjectionDemo.csproj` bằng:

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

Sample tự cài đặt ba lifetime bằng tay để bạn thấy chúng chỉ là quy ước về **thời điểm và số lần gọi `new`**, không phải phép màu của framework.

Thay toàn bộ `Program.cs`:

```csharp
using System.Collections.Generic;

namespace DependencyInjectionDemo;

public interface IClock
{
    DateTimeOffset UtcNow { get; }
}

public sealed class FixedClock : IClock
{
    public FixedClock(DateTimeOffset now) => UtcNow = now;

    public DateTimeOffset UtcNow { get; }
}

public sealed record PlacedOrder(string OrderId, decimal Total, DateTimeOffset PlacedAtUtc);

public interface IOrderStore
{
    int Count { get; }

    bool TryAdd(PlacedOrder order);
}

// SINGLETON: một instance cho cả chương trình.
public sealed class InMemoryOrderStore : IOrderStore
{
    private readonly Dictionary<string, PlacedOrder> _orders = new(StringComparer.Ordinal);

    public int Count => _orders.Count;

    public bool TryAdd(PlacedOrder order)
    {
        ArgumentNullException.ThrowIfNull(order);
        return _orders.TryAdd(order.OrderId, order);
    }
}

// SINGLETON: nơi gom nhật ký của mọi yêu cầu.
public sealed class AuditLog
{
    private readonly List<string> _entries = new();

    public IReadOnlyList<string> Entries => _entries;

    public void Write(string line)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(line);
        _entries.Add(line);
    }
}

// SCOPED: một instance cho mỗi yêu cầu.
public sealed class RequestContext
{
    public RequestContext(string correlationId)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(correlationId);
        CorrelationId = correlationId;
    }

    public string CorrelationId { get; }
}

// SCOPED: gắn mã tương quan của yêu cầu hiện tại vào nhật ký dùng chung.
public sealed class ScopedAuditWriter
{
    private readonly RequestContext _context;
    private readonly AuditLog _log;

    public ScopedAuditWriter(RequestContext context, AuditLog log)
    {
        ArgumentNullException.ThrowIfNull(context);
        ArgumentNullException.ThrowIfNull(log);

        _context = context;
        _log = log;
    }

    public void Write(string message) => _log.Write($"[{_context.CorrelationId}] {message}");
}

// TRANSIENT: tạo mới mỗi lần cần.
public sealed class PlaceOrderHandler
{
    private readonly IOrderStore _store;
    private readonly ScopedAuditWriter _audit;
    private readonly IClock _clock;

    public PlaceOrderHandler(IOrderStore store, ScopedAuditWriter audit, IClock clock)
    {
        ArgumentNullException.ThrowIfNull(store);
        ArgumentNullException.ThrowIfNull(audit);
        ArgumentNullException.ThrowIfNull(clock);

        _store = store;
        _audit = audit;
        _clock = clock;
    }

    public string Handle(string orderId, decimal total)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(orderId);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(total);

        bool added = _store.TryAdd(new PlacedOrder(orderId, total, _clock.UtcNow));
        _audit.Write(added ? $"placed {orderId}" : $"duplicate {orderId}");
        return added ? "placed" : "duplicate";
    }
}

// Một scope giữ các object sống theo yêu cầu và tạo object transient khi được hỏi.
public sealed class RequestScope
{
    private readonly IOrderStore _store;
    private readonly IClock _clock;
    private readonly ScopedAuditWriter _audit;

    public RequestScope(IOrderStore store, IClock clock, AuditLog log, string correlationId)
    {
        _store = store;
        _clock = clock;
        Context = new RequestContext(correlationId);
        _audit = new ScopedAuditWriter(Context, log);
    }

    public RequestContext Context { get; }

    public ScopedAuditWriter Audit => _audit;

    public PlaceOrderHandler CreateHandler() => new(_store, _audit, _clock);
}

// COMPOSITION ROOT: nơi duy nhất biết class cụ thể nào ghép với class cụ thể nào.
public sealed class CompositionRoot
{
    private readonly IOrderStore _store = new InMemoryOrderStore();
    private readonly AuditLog _log = new();
    private readonly IClock _clock;

    public CompositionRoot(IClock clock)
    {
        ArgumentNullException.ThrowIfNull(clock);
        _clock = clock;
    }

    public IOrderStore Store => _store;

    public AuditLog Log => _log;

    public RequestScope BeginRequest(string correlationId) =>
        new(_store, _clock, _log, correlationId);
}

internal static class Program
{
    private static void Main()
    {
        var root = new CompositionRoot(
            new FixedClock(new DateTimeOffset(2026, 7, 31, 9, 0, 0, TimeSpan.Zero)));

        RequestScope first = root.BeginRequest("req-1");
        PlaceOrderHandler firstHandler = first.CreateHandler();
        Console.WriteLine($"req-1: {firstHandler.Handle("ORD-001", 1_850_000m)}");
        Console.WriteLine($"req-1: {first.CreateHandler().Handle("ORD-001", 1_850_000m)}");

        RequestScope second = root.BeginRequest("req-2");
        PlaceOrderHandler secondHandler = second.CreateHandler();
        Console.WriteLine($"req-2: {secondHandler.Handle("ORD-002", 350_000m)}");

        Console.WriteLine($"Orders in shared store: {root.Store.Count}");
        Console.WriteLine($"Same handler object across scopes: {ReferenceEquals(firstHandler, secondHandler)}");
        Console.WriteLine($"Same audit writer inside one scope: {ReferenceEquals(first.Audit, first.Audit)}");
        Console.WriteLine($"Same audit writer across scopes: {ReferenceEquals(first.Audit, second.Audit)}");

        Console.WriteLine("--- audit log ---");
        foreach (string entry in root.Log.Entries)
        {
            Console.WriteLine($"  {entry}");
        }
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Output:

```text
req-1: placed
req-1: duplicate
req-2: placed
Orders in shared store: 2
Same handler object across scopes: False
Same audit writer inside one scope: True
Same audit writer across scopes: False
--- audit log ---
  [req-1] placed ORD-001
  [req-1] duplicate ORD-001
  [req-2] placed ORD-002
```

Project được kiểm tra bằng .NET SDK `9.0.121`, target `net9.0`, không dùng package ngoài.

### Walkthrough — execution / state / cost

1. CompositionRoot tạo một store/log, nhận clock từ ngoài.
2. BeginRequest tạo context/audit, giữ reference tới store/clock chung.
3. Mỗi CreateHandler new handler; Handle ghi store rồi ghi audit theo context của scope.
4. References quyết định object còn sống; RequestScope không tự dispose hay hết hiệu lực trong sample. State log/store O(số đơn + số calls); transient có allocation mỗi lần.

### Mini-check

Giữ firstHandler sau khi biến first ra khỏi scope C#: RequestContext có tự biến mất không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Ba lifetime chỉ là ba quy ước về `new`

| Lifetime | Ai gọi `new` | Bao nhiêu lần | Trong sample |
|---|---|---|---|
| Singleton | composition root | một lần cho mỗi composition root | `InMemoryOrderStore`, `AuditLog`, `FixedClock` |
| Scoped | scope | một lần cho mỗi yêu cầu | `RequestContext`, `ScopedAuditWriter` |
| Transient | mỗi lời gọi factory | mỗi lần được hỏi | `PlaceOrderHandler` |

Output xác nhận từng dòng: kho dùng chung có `2` đơn dù ba lần gọi nằm ở hai scope; hai handler ở hai scope là hai object khác nhau; audit writer giống nhau trong một scope và khác nhau giữa hai scope.

Không có framework nào tham gia. Container sau này chỉ tự động hóa đúng ba quy ước này.

### Composition root là nơi duy nhất biết class cụ thể

```text
CompositionRoot ──> InMemoryOrderStore, AuditLog, FixedClock   (biết type cụ thể)
       │
       └── BeginRequest ──> RequestScope ──> ScopedAuditWriter
                                        └──> PlaceOrderHandler

PlaceOrderHandler ──> IOrderStore, IClock, ScopedAuditWriter   (chỉ biết hợp đồng)
```

Nhìn từ dưới lên: không class nghiệp vụ nào gọi `new` một type hạ tầng. Muốn đổi `InMemoryOrderStore` thành `SqlOrderStore`, bạn sửa đúng một dòng trong `CompositionRoot`.

Vị trí của composition root là **entry point** của ứng dụng: `Main` của console app, `Program.cs` của web app, hoặc lớp khởi tạo của một background service. Càng gần entry point càng tốt, vì đó là nơi duy nhất có quyền biết mọi thứ.

### IoC, DI và DIP là ba thứ khác nhau

- **IoC (inversion of control)** là ý tưởng rộng: quyền điều khiển được chuyển từ code của bạn sang một bên khác. Một vòng lặp gọi interface tự nó chỉ minh họa dispatch; khung xử lý gọi lại implementation do người dùng cung cấp mới thể hiện quyền điều khiển được đảo. Template method ở [bài 2](./02-encapsulation-abstraction-inheritance-polymorphism.md) cũng là IoC. Câu thường được nhắc là “đừng gọi chúng tôi, chúng tôi sẽ gọi bạn”.
- **DI (dependency injection)** là một dạng IoC hẹp: object không tự tạo phụ thuộc mà nhận từ ngoài.
- **DIP** nói về **chiều** của phụ thuộc: nghiệp vụ không phụ thuộc chi tiết.

Có thể dùng DI mà vi phạm DIP (inject thẳng một class hạ tầng), và có thể tuân thủ DIP mà chưa dùng DI container nào — như chính sample này.

### Vì sao `RequestScope` tạo handler thay vì nhận sẵn

`PlaceOrderHandler` là transient, nên nó phải được tạo **khi cần**, không phải khi scope bắt đầu. Nếu `RequestScope` nhận sẵn một handler qua constructor, nó lại thành scoped.

Trong C#, cách phổ biến để diễn đạt “tạo khi cần” là một factory: một method như `CreateHandler()`, hoặc một delegate `Func<PlaceOrderHandler>` truyền vào. Delegate tiện khi người tạo và người dùng nằm ở hai chỗ khác nhau:

```csharp
public sealed class OrderBatchProcessor
{
    private readonly Func<PlaceOrderHandler> _handlerFactory;

    public OrderBatchProcessor(Func<PlaceOrderHandler> handlerFactory) =>
        _handlerFactory = handlerFactory;
}
```

### Đào sâu (có thể quay lại sau)

#### Captive dependency

Lỗi lifetime nguy hiểm nhất: một object sống lâu giữ reference tới một object đáng lẽ sống ngắn.

```text
Singleton  ──giữ──>  Scoped
   │                    │
   └── sống suốt        └── đáng lẽ chết theo yêu cầu
```

Nếu `AuditLog` (singleton) giữ thẳng một `RequestContext` (scoped), thì mọi yêu cầu về sau đều ghi mã tương quan của yêu cầu **đầu tiên**. Sample tránh điều này bằng cách để `ScopedAuditWriter` — object sống ngắn — giữ `RequestContext`, còn singleton chỉ nhận `string` đã dựng sẵn. Không giữ dependency theo request vượt quá lifetime đã cam kết. Object sống lâu có thể tạo và sở hữu scope ngắn qua factory, nhưng phải kết thúc và không giữ lại dependency của scope đó.

#### Singleton phải an toàn khi dùng đồng thời

Object singleton có thể bị nhiều luồng gọi cùng lúc. `Dictionary` và `List` trong sample không thread-safe; chương trình này chạy một luồng nên vẫn đúng, nhưng trong ứng dụng web thì phải dùng cấu trúc phù hợp hoặc khóa. Ràng buộc đó đã học ở [module 05, bài 11](../05-csharp-nang-cao/11-parallelism-concurrency-va-thread-safety.md).

#### Container trong .NET

ASP.NET Core dùng `Microsoft.Extensions.DependencyInjection` với đúng ba lifetime `AddSingleton`, `AddScoped`, `AddTransient`, và tự dựng object bằng cách đọc constructor. Bài này không dùng nó vì module 06 chưa có ASP.NET Core; bạn sẽ gặp nó ở [module 11](../PROGRESS.md#11-aspnet-core-backend). Khi đó, mọi khái niệm ở đây được giữ nguyên tên gọi.

Với ứng dụng nhỏ, nối dây thủ công là hoàn toàn hợp lệ và còn dễ đọc hơn. Container có giá trị khi số lượng phụ thuộc lớn tới mức việc nối tay trở nên rườm rà.

#### Object phải tự dọn tài nguyên

Nếu một phụ thuộc là `IDisposable` — kết nối database, file stream — thì ai tạo nó phải chịu trách nhiệm giải phóng. Trong sample không có tài nguyên nào như vậy; với scope thật, `RequestScope` thường implement `IDisposable` và dispose các object nó đã tạo, theo đúng quy tắc ở [module 05, bài 12](../05-csharp-nang-cao/12-idisposable-gc-va-quan-ly-tai-nguyen.md).

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| singleton per root | reuse cùng instance | cần bảo vệ nếu nhiều thread |
| scoped | reuse theo đơn vị công việc | phải xác định ai kết thúc scope |
| transient | tạo mới khi resolve/factory | giữ lâu vẫn sống lâu, không tự cleanup |

### Misconception check

**Đúng hay sai?** Có một singleton cho toàn máy dù tạo hai root.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: sample mỗi root có store riêng.

</details>

**Đúng hay sai?** DI bắt buộc dùng container.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: constructor/factory thủ công đã là DI.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** new và reference identity.

- **Working Developer — dùng khi làm việc:** scope owner, disposal.

- **Deep Dive — có thể quay lại sau:** container validation khi có ứng dụng thật.

### Ba cách inject

| Cách | Ưu | Nhược | Dùng khi |
|---|---|---|---|
| Constructor | phụ thuộc lộ rõ, object luôn hợp lệ | constructor dài khi có nhiều phụ thuộc | mặc định |
| Method | chỉ method cần mới nhận | lặp lại ở mọi lời gọi | giá trị đổi theo lời gọi |
| Property | linh hoạt | object có thể ở trạng thái chưa đủ | hiếm; chỉ cho phụ thuộc tùy chọn có mặc định |

Constructor injection dài quá bốn, năm tham số thường không phải lỗi của DI mà là dấu hiệu class làm quá nhiều việc — quay lại [bài 4](./04-single-responsibility.md).

### Chọn lifetime

Hỏi lần lượt:

1. Object có state chia sẻ cần tồn tại xuyên suốt không? → singleton.
2. State có gắn với một yêu cầu/một đơn vị công việc không? → scoped.
3. Không có state đáng chia sẻ? → transient, đơn giản nhất và ít bẫy nhất.

Khi phân vân, chọn lifetime **ngắn hơn**: sai lầm khi tạo nhiều object thường chỉ tốn bộ nhớ, còn sai lầm khi chia sẻ state có thể tạo dữ liệu sai.

### Service locator là antipattern

```csharp
public sealed class PlaceOrderHandler
{
    public string Handle(string orderId)
    {
        var store = ServiceRegistry.Resolve<IOrderStore>(); // phụ thuộc ẩn
        // ...
    }
}
```

Vấn đề:

- chữ ký constructor không còn nói class này cần gì; muốn biết phải đọc hết thân method;
- thiếu đăng ký chỉ lộ ra lúc chạy, ở đúng nhánh code hiếm khi chạy;
- test phải dựng cả registry toàn cục, và các test bắt đầu ảnh hưởng nhau.

Đây cũng chính là common coupling ở [bài 9](./09-coupling-va-cohesion.md), khoác một cái tên nghe kỹ thuật hơn.

### Không phải thứ gì cũng cần inject

Hàm thuần và type ổn định của thư viện chuẩn thường không cần abstraction. Giá trị cấu hình vẫn nên truyền từ ngoài khi thay đổi theo môi trường, như các tham số policy trong module. Hãy inject những thứ mà bạn muốn **thay được**: hạ tầng, thời gian, ngẫu nhiên, và các quy tắc có nhiều biến thể.

## 6. Lỗi thường gặp

### Composition root rải rác khắp nơi

Mỗi class tự `new` một phần phụ thuộc, còn `Main` nối phần còn lại. Khi đó không ai biết cấu hình thật của hệ thống. Giữ đúng một nơi nối dây.

### Nhầm scoped với singleton

Kho dữ liệu bị tạo lại theo yêu cầu thì dữ liệu biến mất; mã tương quan bị chia sẻ toàn cục thì log lẫn lộn. Hãy viết ra bảng lifetime như ở phần cơ chế trước khi code.

### Captive dependency

Đã phân tích ở phần đào sâu. Dấu hiệu: một object singleton có field kiểu `RequestContext`, `DbContext`, `UnitOfWork` hoặc bất cứ thứ gì mang chữ “per request”.

### Constructor làm việc nặng

Constructor chỉ nên gán field và kiểm tra `null`. Nếu nó mở kết nối, đọc file hay gọi mạng, việc dựng object trở nên chậm và có thể ném exception ở nơi khó xử lý.

### Inject cả container vào class nghiệp vụ

Nhận `IServiceProvider` rồi tự `GetService` bên trong là service locator đội lốt DI. Nếu thật sự cần tạo object động, hãy inject một factory có kiểu rõ ràng.

### Dùng `static` cho những thứ vốn nên inject

`Logger.Instance`, `Config.Current`, `Clock.Now` đều tạo phụ thuộc ẩn và làm test phụ thuộc thứ tự chạy. Đây là lỗi phổ biến nhất khi mới chuyển sang DI.

### Đăng ký nhiều implementation mà không định nghĩa cách chọn

Khi có hai `IOrderStore`, phải nói rõ ai dùng cái nào — bằng tên, bằng cấu hình, hoặc bằng một wrapper quyết định. Để mặc “cái nào cũng được” là nguồn bug rất khó tái hiện.

## 7. Khi nào KHÔNG dùng

Không inject IServiceProvider vào mọi service để giấu phụ thuộc. Không chọn singleton chỉ để tránh new khi object chứa request state; cũng không chọn transient cho store cần giữ dữ liệu xuyên request.

## 8. Production notes & scale check

Demo chạy tuần tự, List/Dictionary chưa thread-safe. Không có IDisposable dependency nên RequestScope không đóng tài nguyên; bản mở rộng cần owner và using rõ. Test identity trong/cross scope, root isolation và correlation IDs; không suy ra lifecycle ASP.NET đã được kiểm chứng.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Bảng lifetime

Lập bảng cho các thành phần trong sample: tên, lifetime, lý do. Thêm một dòng cho `SqlConnection` giả định và giải thích lựa chọn.

**Gợi ý:** hỏi “object này có state gì, và state đó thuộc về ai?”.

### Bài 2 — Tái hiện captive dependency

Sửa sample để `AuditLog` (singleton) nhận `RequestContext` qua constructor và tự thêm tiền tố. Chạy hai yêu cầu và quan sát log.

**Gợi ý:** kết quả sẽ cho thấy mọi dòng mang mã của yêu cầu đầu tiên; giữ lại output đó làm ví dụ đối chứng.

### Bài 3 — Factory delegate

Đổi `RequestScope.CreateHandler()` thành `Func<PlaceOrderHandler>` truyền từ composition root. Chương trình phải cho output y hệt.

**Gợi ý:** delegate phải được tạo trong root vì chỉ root biết các type cụ thể.

### Bài 4 — Từ service locator sang injection

Viết một phiên bản dùng registry tĩnh, rồi refactor về constructor injection. Ghi lại hai khác biệt bạn thấy rõ nhất.

**Gợi ý:** thử xóa một đăng ký ở mỗi phiên bản; lỗi xuất hiện lúc nào?

### Bài 5 — Scope thật sự kết thúc

Cho `RequestScope` implement `IDisposable` và giải phóng một tài nguyên giả lập, rồi bảo đảm mọi scope đều được dispose kể cả khi handler ném exception.

**Gợi ý:** `using` và `try/finally` đã học ở [module 05, bài 12](../05-csharp-nang-cao/12-idisposable-gc-va-quan-ly-tai-nguyen.md).

## 10. Bài tập tích hợp liên module — Judgment

Từ closure và IDisposable Module05, vẽ đường giữ context khi singleton giữ scoped writer. Sửa bằng thay chiều ownership hay factory scope nào mà không thêm container?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Ai tạo handler và khi nào?
2. Transient có bảo đảm lifetime ngắn không?
3. Hai root có cùng store không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt được IoC, DI và DIP bằng ví dụ cụ thể.
- [ ] Tôi dùng constructor injection làm mặc định và biết ngoại lệ.
- [ ] Tôi gom mọi việc nối dây vào một composition root.
- [ ] Tôi cài đặt và giải thích được ba lifetime bằng số lần gọi `new`.
- [ ] Tôi nhận ra captive dependency và biết chiều giữ reference đúng.
- [ ] Tôi giải thích được vì sao service locator che giấu phụ thuộc.
- [ ] Tôi build/run được sample trên `net9.0` và đối chiếu đúng output.

Điều hướng:

- Bài prerequisite: [Coupling và cohesion](./09-coupling-va-cohesion.md)
- Ôn lại nền tảng: [Delegate, Action, Func và Predicate](../05-csharp-nang-cao/02-delegate-action-func-predicate.md), [IDisposable, GC và quản lý tài nguyên](../05-csharp-nang-cao/12-idisposable-gc-va-quan-ly-tai-nguyen.md)
- Bài tiếp theo: [Clean code: tên, hàm và cấu trúc](./11-clean-code-ten-ham-va-cau-truc.md)

### Checkpoint sau cụm bài

- [Failure Lab](./failure-labs/02-captive.md)
- [Spaced Review](./reviews/review-02.md)
