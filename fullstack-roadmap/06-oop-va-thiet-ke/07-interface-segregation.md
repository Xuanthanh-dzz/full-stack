# Interface segregation

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phát biểu ISP từ góc nhìn của client: không ai bị buộc phụ thuộc vào thứ mình không dùng;
- nhận ra chi phí thật của một fat interface: test double phình, thay đổi lan rộng, phụ thuộc giả;
- tách một interface lớn thành các role interface theo nhu cầu từng client;
- để một class implement nhiều role interface mà không tạo thêm class;
- viết test double nhỏ nhờ hợp đồng hẹp;
- phân biệt ISP với việc chẻ nhỏ interface một cách máy móc;
- chọn đúng mức tách khi các nhóm method luôn được dùng cùng nhau.

## 2. Bài toán mở đầu

Hệ thống đơn hàng có một interface duy nhất cho việc lưu trữ:

```csharp
public interface IOrderRepository
{
    void Save(OrderSummary order);
    OrderSummary? Find(string orderId);
    IReadOnlyList<OrderSummary> FindByCustomer(string customerId);
    void Delete(string orderId);
    int ArchiveOlderThan(DateOnly cutoff);
    string ExportCsv();
    decimal GetTotalRevenue();
}
```

Ba nơi dùng nó:

- màn hình tra cứu chỉ gọi `Find`;
- luồng đặt hàng chỉ gọi `Save`;
- job dọn dẹp ban đêm chỉ gọi `ArchiveOlderThan`.

Không nơi nào dùng quá một hoặc hai method, nhưng cả ba đều phụ thuộc vào toàn bộ bảy method. Hậu quả:

1. **Test khó viết.** Muốn kiểm tra màn hình tra cứu, bạn phải tạo một object implement đủ bảy method, sáu trong số đó ném `NotImplementedException` — và đó là vi phạm Liskov đã học ở [bài 6](./06-liskov-substitution.md), chỉ khác là nó nằm trong code test.
2. **Thay đổi lan rộng.** Thêm `ExportPdf()` vào interface buộc **mọi** implementation phải viết thêm, kể cả những implementation không liên quan gì tới xuất file.
3. **Phụ thuộc giả.** Đọc `LookupService` mà thấy `IOrderRepository`, người đọc phải tự hỏi: nó có xóa dữ liệu không? Có xuất báo cáo không? Chữ ký không trả lời được.

ISP giải quyết đúng điều này: **kích thước của interface do client quyết định**, không do implementation quyết định.

## 3. Lời giải bằng code

Tạo project `.NET 9`:

```bash
mkdir InterfaceSegregationDemo
cd InterfaceSegregationDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `InterfaceSegregationDemo.csproj` bằng:

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

namespace InterfaceSegregationDemo;

public sealed record OrderSummary(
    string OrderId,
    string CustomerId,
    decimal Total,
    DateOnly PlacedOn,
    bool Archived = false);

// Ba vai (role) tách theo nhu cầu của ba client khác nhau.
public interface IOrderReader
{
    OrderSummary? Find(string orderId);
}

public interface IOrderWriter
{
    void Save(OrderSummary order);
}

public interface IOrderArchiver
{
    int ArchiveOlderThan(DateOnly cutoff);
}

// Một implementation vẫn có thể đảm nhiệm nhiều vai.
public sealed class InMemoryOrderStore : IOrderReader, IOrderWriter, IOrderArchiver
{
    private readonly Dictionary<string, OrderSummary> _orders = new(StringComparer.Ordinal);

    public int Count => _orders.Count;

    public void Save(OrderSummary order)
    {
        ArgumentNullException.ThrowIfNull(order);
        _orders[order.OrderId] = order;
    }

    public OrderSummary? Find(string orderId)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(orderId);
        return _orders.TryGetValue(orderId, out OrderSummary? found) ? found : null;
    }

    public int ArchiveOlderThan(DateOnly cutoff)
    {
        var toArchive = new List<string>();
        foreach (KeyValuePair<string, OrderSummary> entry in _orders)
        {
            if (!entry.Value.Archived && entry.Value.PlacedOn < cutoff)
            {
                toArchive.Add(entry.Key);
            }
        }

        foreach (string orderId in toArchive)
        {
            _orders[orderId] = _orders[orderId] with { Archived = true };
        }

        return toArchive.Count;
    }
}

// Client 1: chỉ cần đọc. Chữ ký nói rõ nó không ghi, không xóa.
public sealed class OrderLookupService
{
    private readonly IOrderReader _reader;

    public OrderLookupService(IOrderReader reader)
    {
        ArgumentNullException.ThrowIfNull(reader);
        _reader = reader;
    }

    public string Describe(string orderId)
    {
        OrderSummary? order = _reader.Find(orderId);
        return order is null
            ? $"{orderId}: not found"
            : $"{order.OrderId}: {order.Total:N0} VND on {order.PlacedOn:yyyy-MM-dd}" +
              $"{(order.Archived ? " (archived)" : string.Empty)}";
    }
}

// Client 2: chỉ cần ghi.
public sealed class PlaceOrderHandler
{
    private readonly IOrderWriter _writer;

    public PlaceOrderHandler(IOrderWriter writer)
    {
        ArgumentNullException.ThrowIfNull(writer);
        _writer = writer;
    }

    public void Handle(string orderId, string customerId, decimal total, DateOnly placedOn)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(orderId);
        ArgumentException.ThrowIfNullOrWhiteSpace(customerId);
        ArgumentOutOfRangeException.ThrowIfNegative(total);

        _writer.Save(new OrderSummary(orderId, customerId, total, placedOn));
    }
}

// Client 3: chỉ cần lưu trữ lịch sử.
public sealed class NightlyArchiveJob
{
    private readonly IOrderArchiver _archiver;

    public NightlyArchiveJob(IOrderArchiver archiver)
    {
        ArgumentNullException.ThrowIfNull(archiver);
        _archiver = archiver;
    }

    public string Run(DateOnly today, int keepDays)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(keepDays);

        DateOnly cutoff = today.AddDays(-keepDays);
        int archived = _archiver.ArchiveOlderThan(cutoff);
        return $"archived {archived} order(s) placed before {cutoff:yyyy-MM-dd}";
    }
}

// Test double cho client 1: hợp đồng hẹp nên chỉ cần đúng 6 dòng.
public sealed class SingleOrderReader : IOrderReader
{
    private readonly OrderSummary _order;

    public SingleOrderReader(OrderSummary order) => _order = order;

    public OrderSummary? Find(string orderId) =>
        string.Equals(orderId, _order.OrderId, StringComparison.Ordinal) ? _order : null;
}

internal static class Program
{
    private static void Main()
    {
        var store = new InMemoryOrderStore();

        var handler = new PlaceOrderHandler(store);
        handler.Handle("ORD-001", "CUS-001", 1_850_000m, new DateOnly(2026, 5, 10));
        handler.Handle("ORD-002", "CUS-002", 350_000m, new DateOnly(2026, 7, 20));

        var lookup = new OrderLookupService(store);
        Console.WriteLine(lookup.Describe("ORD-001"));
        Console.WriteLine(lookup.Describe("ORD-999"));

        var job = new NightlyArchiveJob(store);
        Console.WriteLine(job.Run(today: new DateOnly(2026, 7, 31), keepDays: 30));

        Console.WriteLine(lookup.Describe("ORD-001"));
        Console.WriteLine(lookup.Describe("ORD-002"));
        Console.WriteLine($"Store still holds {store.Count} order(s)");

        // Cùng OrderLookupService, không cần store thật.
        var stubbed = new OrderLookupService(
            new SingleOrderReader(
                new OrderSummary("ORD-777", "CUS-009", 99_000m, new DateOnly(2026, 7, 30))));

        Console.WriteLine(stubbed.Describe("ORD-777"));
        Console.WriteLine(stubbed.Describe("ORD-001"));
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
ORD-001: 1,850,000 VND on 2026-05-10
ORD-999: not found
archived 1 order(s) placed before 2026-07-01
ORD-001: 1,850,000 VND on 2026-05-10 (archived)
ORD-002: 350,000 VND on 2026-07-20
Store still holds 2 order(s)
ORD-777: 99,000 VND on 2026-07-30
ORD-001: not found
```

Project được kiểm tra bằng .NET SDK `9.0.119`, target `net9.0`, không dùng package ngoài.

## 4. Giải thích cơ chế

### Interface thuộc về client, không thuộc về implementation

`InMemoryOrderStore` vẫn có đủ ba nhóm method như trước. Điều thay đổi là **cách các client nhìn nó**:

```text
                     ┌──────────────── IOrderReader ◄── OrderLookupService
InMemoryOrderStore ──┼──────────────── IOrderWriter ◄── PlaceOrderHandler
                     └──────────────── IOrderArchiver ◄── NightlyArchiveJob
```

Cùng một object được truyền vào cả ba client, nhưng mỗi client chỉ thấy phần mình cần. Không có class nào tăng lên, chỉ có ba interface nhỏ thay cho một interface lớn.

Đọc `PlaceOrderHandler`, bạn biết chắc nó không xóa và không đọc dữ liệu. Thông tin đó nằm ngay trong chữ ký constructor, không cần đọc thân method.

### Test double nhỏ đi bao nhiêu

`SingleOrderReader` implement đúng một method. Với fat interface, cùng mục đích đó cần bảy method, sáu cái ném exception:

| | Fat interface | Role interface |
|---|---:|---:|
| Method phải viết cho test double | 7 | 1 |
| Method ném `NotImplementedException` | 6 | 0 |
| Số client phải sửa khi thêm `ExportPdf` | tất cả | chỉ client cần xuất PDF |

Cột giữa không chỉ tốn công gõ. Mỗi `NotImplementedException` là một quả mìn: hôm nay không ai gọi tới, ngày mai code đổi và test nổ ở chỗ không ai ngờ.

### Thêm khả năng mới không lan ra ngoài

Giả sử cần thêm xuất CSV. Với thiết kế hiện tại:

```csharp
public interface IOrderExporter
{
    string ExportCsv();
}
```

`InMemoryOrderStore` implement thêm interface đó, và **không client nào hiện có phải sửa** — vì không client nào tham chiếu tới hợp đồng mới. Đây chính là open/closed ở [bài 5](./05-open-closed.md) nhìn từ phía hợp đồng: interface nhỏ thì cơ hội phải sửa nó cũng nhỏ.

### Tách bao nhiêu là đủ

Ranh giới hợp lý là **nhóm method luôn được dùng cùng nhau bởi cùng một client**. `Find` và `FindByCustomer` thường đi cùng nhau trong màn hình tra cứu, nên để chung trong `IOrderReader` là hợp lý; tách thành hai interface một-method chỉ tạo thêm file.

Câu hỏi kiểm tra: “có client nào cần method A mà không cần method B không?” Nếu không, hai method đó ở chung.

### Đào sâu (có thể quay lại sau)

#### Một interface một method có phải luôn tốt nhất

Không. Interface cực nhỏ đẩy độ phức tạp sang chỗ khác: một client cần bốn thao tác phải nhận bốn tham số constructor. Khi thấy điều đó, hãy gộp lại theo vai, hoặc xem lại xem client đó có đang làm quá nhiều việc không — nó có thể đang vi phạm SRP ở [bài 4](./04-single-responsibility.md).

#### ISP và explicit interface implementation

Khi một class implement nhiều interface có method trùng tên, C# cho phép explicit interface implementation để mỗi vai có một thân riêng (đã nhắc ở [module 04, bài 10](../04-csharp-co-ban/10-abstract-class-va-interface.md)). Công cụ này hữu ích nhưng làm code khó đọc; nếu phải dùng thường xuyên, khả năng là các vai đang chồng chéo và cần thiết kế lại.

#### Interface hẹp giúp kiểm soát quyền

Truyền `IOrderReader` cho một module là một cách nói “module này không được ghi”. Ràng buộc nằm ở compiler chứ không ở lời dặn miệng. Ở quy mô lớn hơn, ý tưởng này trở thành ranh giới module và quyền truy cập dữ liệu giữa các bounded context ở [module 17](../PROGRESS.md#17-kien-truc-phan-mem).

#### Chi phí phía implementation

Một class implement năm interface có thể khiến người đọc phải mở năm file mới thấy đủ hợp đồng. Đặt các role interface liên quan gần nhau trong cùng thư mục/namespace, và đặt tên theo vai (`IOrderReader`) chứ không theo công nghệ (`ISqlOrderThing`).

## 5. Kiến thức nền

### Cách phát hiện fat interface

- Có implementation ném `NotImplementedException` hoặc để thân rỗng.
- Test double dài hơn cả class được test.
- Tên interface là danh từ chung chung: `IManager`, `IService`, `IRepository` không kèm vai.
- Thêm một method vào interface làm nhiều file thay đổi trong cùng một commit.
- Client chỉ gọi một trong mười method.

### Đặt tên role interface

Tên nên mô tả **vai**, và thường là một khả năng:

| Tên yếu | Tên theo vai |
|---|---|
| `IOrderRepository` | `IOrderReader`, `IOrderWriter` |
| `IFileHelper` | `IFileReader`, `IFileWriter` |
| `IUserManager` | `IPasswordHasher`, `IUserFinder` |

Hậu tố `-er`/`-able` gợi đúng ý “thứ có thể làm việc này”. Cách đặt tên tổng quát hơn là nội dung của [bài 11](./11-clean-code-ten-ham-va-cau-truc.md).

### ISP không chỉ dành cho interface

Nguyên tắc áp dụng cho mọi hợp đồng: một base class có mười `abstract` method cũng ép lớp con phụ thuộc vào cả mười. Một record tham số có mười field mà mỗi caller chỉ dùng hai cũng là cùng một vấn đề ở mức dữ liệu.

### Quan hệ với các nguyên tắc khác

- **SRP** hỏi “class này có mấy lý do thay đổi”; **ISP** hỏi “client này bị buộc biết bao nhiêu thứ”. Một class có thể đúng SRP nhưng vẫn lộ interface quá rộng.
- **LSP** được ISP hỗ trợ trực tiếp: hợp đồng hẹp thì implementation dễ giữ trọn lời hứa.
- **DIP** ở [bài 8](./08-dependency-inversion.md) quyết định interface **thuộc về ai**; ISP quyết định nó **to bao nhiêu**.

## 6. Lỗi thường gặp

### Tách interface theo implementation

Đọc class hiện có rồi cắt đôi danh sách method cho “cân” là tách sai. Hãy bắt đầu từ danh sách client và những gì từng client thật sự gọi.

### Chẻ tới mức vô nghĩa

`IHasId`, `IHasName`, `IHasCreatedAt` cho mọi property tạo ra hàng chục interface không nói lên vai trò nào. ISP nói về hợp đồng hành vi, không phải về từng thuộc tính.

### Tạo interface “tổng” gộp lại các role

```csharp
public interface IOrderRepository : IOrderReader, IOrderWriter, IOrderArchiver { }
```

Nếu client cứ tiếp tục nhận `IOrderRepository`, mọi lợi ích vừa tạo ra biến mất. Interface tổng chỉ nên tồn tại khi có client thật sự cần cả ba vai cùng lúc.

### Giữ nguyên fat interface rồi vá bằng default implementation

Default interface implementation làm code compile nhưng không giải quyết việc client vẫn nhìn thấy mọi method. Nó cũng dễ tạo hành vi mặc định sai một cách âm thầm.

### Nhầm ISP với “càng nhiều interface càng tốt”

Không phải class nào cũng cần interface. Với logic thuần, tất định như `PricingPolicy` ở [bài 4](./04-single-responsibility.md), phụ thuộc thẳng vào class cụ thể lại rõ ràng hơn.

### Bỏ quên tính nhất quán giữa các vai

Nếu `IOrderWriter.Save` và `IOrderReader.Find` có quy ước khác nhau về chuẩn hóa `orderId` (một bên phân biệt hoa thường, một bên không), việc tách interface sẽ giấu mất mâu thuẫn đó. Hợp đồng của các vai vẫn phải khớp nhau khi cùng một implementation phục vụ.

### Interface hẹp nhưng tham số phình

Tách được interface mà mỗi method lại nhận mười tham số thì client vẫn phải biết quá nhiều. Hãy gom tham số đi cùng nhau thành một record — đúng cách `OrderSummary` được dùng trong sample.

## 7. Bài tập

### Bài 1 — Tách từ danh sách client

Cho `IReportService` gồm `RenderHtml`, `RenderPdf`, `SendByEmail`, `ScheduleDaily`, `GetLastRunTime`. Liệt kê các client có thể có rồi tách thành role interface.

**Gợi ý:** bắt đầu bằng câu “ai gọi cái gì”; nếu không nghĩ ra client cho một method, hãy hỏi method đó có cần tồn tại không.

### Bài 2 — Thêm vai mới

Thêm `IOrderExporter` với `ExportCsv()` vào sample. Yêu cầu: không sửa `OrderLookupService`, `PlaceOrderHandler` và `NightlyArchiveJob`.

**Gợi ý:** chỉ `InMemoryOrderStore` và `Main` được đụng tới; nếu phải sửa chỗ khác, hãy xem lại ranh giới vai.

### Bài 3 — Test double không có exception

Viết `RecordingOrderWriter` chỉ ghi lại các đơn được `Save` vào một `List`, rồi dùng nó kiểm tra `PlaceOrderHandler`.

**Gợi ý:** đếm số phần tử và kiểm tra `Total` được truyền đúng; double này không cần biết gì về archive.

### Bài 4 — Khi nào không nên tách

Tìm một ví dụ trong sample mà việc tách thêm sẽ làm code tệ đi, và viết một câu lý do.

**Gợi ý:** thử tách `Find` và một `FindByCustomer` giả định thành hai interface rồi xem client tra cứu phải nhận mấy tham số.

### Bài 5 — Tìm fat interface thật

Trong project ở [module 05, bài 19](../05-csharp-nang-cao/19-du-an-xu-ly-du-lieu-bat-dong-bo.md) hoặc code của bạn, tìm một hợp đồng mà client chỉ dùng một phần. Vẽ bảng client × method để xác định điểm cắt.

**Gợi ý:** đánh dấu `x` vào ô client dùng method; các cụm `x` liền nhau chính là các vai.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phát biểu ISP từ phía client, không từ phía implementation.
- [ ] Tôi nêu được ba chi phí cụ thể của fat interface.
- [ ] Tôi tách interface dựa trên bảng client × method.
- [ ] Tôi để một class đảm nhiệm nhiều vai mà không nhân bản class.
- [ ] Tôi viết được test double nhỏ nhờ hợp đồng hẹp.
- [ ] Tôi biết khi nào việc tách thêm làm code tệ đi.
- [ ] Tôi build/run được sample trên `net9.0` và đối chiếu đúng output.

Điều hướng:

- Bài prerequisite: [Liskov substitution](./06-liskov-substitution.md)
- Ôn lại nền tảng: [Abstract class, interface và composition](../04-csharp-co-ban/10-abstract-class-va-interface.md)
- Bài tiếp theo: [Dependency inversion](./08-dependency-inversion.md)
