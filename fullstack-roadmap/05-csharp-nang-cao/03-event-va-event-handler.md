# Event và event handler

## 1. Mục tiêu

Sau bài này, bạn có thể:

- thiết kế quan hệ publisher/subscriber mà publisher không phụ thuộc concrete subscriber;
- khai báo event bằng `EventHandler<TEventArgs>`;
- tạo event data immutable và truyền `sender` đúng quy ước .NET;
- đăng ký bằng `+=`, hủy đăng ký bằng `-=` và chỉ raise event trong publisher;
- giải thích event dùng multicast delegate phía sau nhưng giới hạn quyền của caller;
- vẽ object graph từ publisher đến delegate invocation list và subscriber target;
- nhận ra rủi ro lifetime, exception và duplicate subscription của event đồng bộ.

## 2. Bài toán mở đầu

Một kho hàng cần phát tín hiệu khi tồn kho đi từ mức an toàn xuống ngưỡng thấp. Hiện có hai nơi quan tâm:

- dashboard cập nhật cảnh báo;
- email notifier gửi thông báo cho nhân viên kho.

`InventoryItem` không nên tự `new Dashboard` hoặc `new EmailNotifier`. Nếu làm vậy, domain object phụ thuộc hạ tầng hiển thị/gửi mail và phải sửa mỗi khi có kênh mới. Ngược lại, nếu công khai một delegate field, code ngoài có thể gán đè toàn bộ handler hoặc tự phát thông báo giả.

Ta cần publisher công bố rằng “một sự kiện đã xảy ra”, cho subscriber đăng ký/hủy đăng ký nhưng giữ quyền raise bên trong publisher. C# cung cấp keyword `event` cho đúng ranh giới đó.

## 3. Lời giải bằng code

Tạo project:

```bash
dotnet new console --name EventDemo --framework net9.0 --use-program-main
cd EventDemo
```

Thay `EventDemo.csproj` bằng:

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

Thay `Program.cs` bằng:

```csharp
namespace EventDemo;

internal static class Program
{
    private static void Main()
    {
        var item = new InventoryItem("KB-01", initialStock: 10, lowStockThreshold: 3);
        var dashboard = new StockDashboard();
        var email = new WarehouseEmailNotifier();

        item.StockLow += dashboard.HandleStockLow;
        item.StockLow += email.HandleStockLow;

        // 10 -> 3 đi qua ngưỡng: cả hai subscriber được gọi.
        item.Sell(7);

        // 3 -> 2 vẫn đang thấp, không phải lần mới đi qua ngưỡng.
        item.Sell(1);

        item.StockLow -= email.HandleStockLow;
        Console.WriteLine("Email subscriber removed.");

        item.Restock(8); // 2 -> 10, trở lại mức an toàn.
        item.Sell(7);    // 10 -> 3, chỉ dashboard còn đăng ký.
    }
}

internal sealed class InventoryItem
{
    public string Sku { get; }
    public int Stock { get; private set; }
    public int LowStockThreshold { get; }

    // Event ban đầu không có subscriber nên delegate backing field có thể null.
    public event EventHandler<StockLowEventArgs>? StockLow;

    public InventoryItem(string sku, int initialStock, int lowStockThreshold)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sku);

        if (initialStock < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(initialStock));
        }

        if (lowStockThreshold < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(lowStockThreshold));
        }

        Sku = sku.Trim().ToUpperInvariant();
        Stock = initialStock;
        LowStockThreshold = lowStockThreshold;
    }

    public void Sell(int quantity)
    {
        if (quantity <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(quantity));
        }

        if (quantity > Stock)
        {
            throw new InvalidOperationException("Not enough stock.");
        }

        int previousStock = Stock;
        Stock -= quantity;
        Console.WriteLine($"Stock changed: {previousStock} -> {Stock}");

        bool crossedLowThreshold =
            previousStock > LowStockThreshold && Stock <= LowStockThreshold;

        if (crossedLowThreshold)
        {
            OnStockLow();
        }
    }

    public void Restock(int quantity)
    {
        if (quantity <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(quantity));
        }

        int previousStock = Stock;
        Stock = checked(Stock + quantity);
        Console.WriteLine($"Stock changed: {previousStock} -> {Stock}");
    }

    private void OnStockLow()
    {
        var eventData = new StockLowEventArgs(Sku, Stock, LowStockThreshold);

        // ?. chỉ invoke khi invocation list khác null.
        StockLow?.Invoke(this, eventData);
    }
}

internal sealed class StockLowEventArgs : EventArgs
{
    public string Sku { get; }
    public int CurrentStock { get; }
    public int Threshold { get; }

    public StockLowEventArgs(string sku, int currentStock, int threshold)
    {
        Sku = sku;
        CurrentStock = currentStock;
        Threshold = threshold;
    }
}

internal sealed class StockDashboard
{
    public void HandleStockLow(object? sender, StockLowEventArgs eventData)
    {
        Console.WriteLine(
            $"DASHBOARD: {eventData.Sku} has {eventData.CurrentStock} item(s).");
    }
}

internal sealed class WarehouseEmailNotifier
{
    public void HandleStockLow(object? sender, StockLowEventArgs eventData)
    {
        // Demo local: chỉ in ra console, không thực hiện email I/O thật.
        Console.WriteLine(
            $"EMAIL: Restock {eventData.Sku}; threshold {eventData.Threshold}.");
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
Stock changed: 10 -> 3
DASHBOARD: KB-01 has 3 item(s).
EMAIL: Restock KB-01; threshold 3.
Stock changed: 3 -> 2
Email subscriber removed.
Stock changed: 2 -> 10
Stock changed: 10 -> 3
DASHBOARD: KB-01 has 3 item(s).
```

## 4. Giải thích cơ chế

### 4.1 Publisher, subscriber và event data

Trong ví dụ:

- `InventoryItem` là publisher: nó sở hữu state và biết lúc nào sự kiện thật sự xảy ra;
- `StockDashboard` và `WarehouseEmailNotifier` là subscriber;
- `StockLowEventArgs` là snapshot dữ liệu tại thời điểm raise;
- `EventHandler<StockLowEventArgs>` là delegate contract có dạng `(object? sender, StockLowEventArgs eventData) -> void`.

Publisher không biết subscriber concrete nào đang nghe. Nó chỉ invoke contract. Subscriber không sửa stock; nó phản ứng với notification đã xảy ra.

### 4.2 `event` thêm quyền truy cập lên delegate

Khai báo:

```csharp
public event EventHandler<StockLowEventArgs>? StockLow;
```

dùng một multicast delegate làm backing storage. Tuy nhiên, code ngoài declaring type chỉ được:

```csharp
item.StockLow += handler;
item.StockLow -= handler;
```

Code ngoài không được `item.StockLow = ...`, không đọc invocation list và không `Invoke` event. Chỉ `InventoryItem` có quyền raise. Đây là khác biệt quan trọng so với public delegate field/property.

Dấu `?` nói backing delegate có thể là `null` khi chưa có subscriber. Toán tử null-conditional `?.` chỉ gọi `Invoke` khi reference khác `null`. Bài [Nullable reference type](./06-nullable-reference-type.md) sẽ giải thích đầy đủ nullable annotation và flow analysis; ở đây nó phản ánh đúng trạng thái tự nhiên của event.

### 4.3 Đăng ký và hủy đăng ký

Câu:

```csharp
item.StockLow += dashboard.HandleStockLow;
```

tạo delegate tới instance method, rồi ghép entry đó vào invocation list của event. `-=` tìm entry có cùng method và cùng target object để bỏ. Vì code giữ biến `dashboard` và dùng cùng method group, unsubscribe khớp chính xác.

Đăng ký cùng handler hai lần tạo hai entry và handler chạy hai lần. C# event không tự loại trùng. Publisher/subscriber phải quy định ownership subscription rõ ràng.

### 4.4 Raise đúng thời điểm nghiệp vụ

Event không thay validation. `Sell` kiểm tra input, commit `Stock`, rồi mới quyết định có đi qua ngưỡng không:

```text
previousStock > threshold && currentStock <= threshold
```

Nhờ vậy event chỉ phát khi chuyển từ an toàn sang thấp, không phát lại ở mọi lần bán khi đã thấp. Tên event `StockLow` mô tả một fact đã xảy ra; event data chứa state sau commit.

Method `OnStockLow` gom logic tạo event data và invoke vào một điểm. Quy ước `On<EventName>` thường là `protected virtual` trong base class muốn derived type tùy biến; class `sealed` ở đây dùng `private` vì không có extension point kế thừa.

### 4.5 `sender` và `EventArgs`

Publisher truyền `this` làm `sender`, vì chính `InventoryItem` phát event. Subscriber thường ưu tiên data có type trong `StockLowEventArgs`; chỉ dùng/cast `sender` khi contract thật sự cần publisher object.

Event data dùng get-only property nên subscriber không thể gán lại snapshot. `EventArgs` là base type theo convention .NET và cho phép dùng `EventHandler<TEventArgs>` nhất quán.

### 4.6 Mô hình bộ nhớ và lifetime

Sau hai subscription:

```text
Main locals                         Managed heap
+---------------------+            +--------------------------------+
| item ref ------------+---------->| InventoryItem H1               |
| dashboard ref -------+-----+      | StockLow backing delegate D1 --+---+
| email ref -----------+--+  |      +--------------------------------+   |
+---------------------+  |  |                                           v
                         |  |      +----------------------------------------+
                         |  |      | Invocation list                        |
                         |  +------| entry 1: target H2, method Handle...  |
                         +---------| entry 2: target H3, method Handle...  |
                                  +----------------------------------------+

H2 StockDashboard object
H3 WarehouseEmailNotifier object
```

H1 giữ backing delegate; delegate giữ target reference H2/H3. Vì vậy một publisher sống lâu có thể giữ subscriber sống dù nơi khác đã bỏ reference. Sau `-= email.HandleStockLow`, entry H3 bị bỏ; nếu không còn root/reference khác, email object mới có thể trở thành GC-eligible.

`new StockLowEventArgs(...)` tạo event-data object mới cho mỗi lần raise trong demo. Từng handler nhận bản sao reference tới cùng object event data; publisher không clone cho mỗi subscriber.

### 4.7 Event trong ví dụ chạy đồng bộ

`StockLow?.Invoke(...)` gọi handler ngay trên cùng call stack và cùng thread đang chạy `Sell`. `Sell` chỉ return sau khi tất cả handler return. Nếu handler chậm, publisher chậm; nếu handler ném exception, invocation dừng và exception đi ngược về caller của `Sell`. `Stock` đã được commit trước khi raise nên exception handler không tự rollback state; contract production phải nói rõ operation thành công nhưng notification lỗi được xử lý thế nào.

Event không tự tạo background thread, queue hay retry. Những nhu cầu đó cần thiết kế riêng bằng async, channel hoặc message broker ở các module sau.

## 5. Kiến thức nền

### Event là notification, không phải command hai chiều

Publisher thông báo fact đã xảy ra; nó không nên hỏi subscriber để quyết định invariant cốt lõi. Nếu workflow cần câu trả lời bắt buộc hoặc transaction chung, gọi dependency/service có contract return rõ thường phù hợp hơn event.

### Field-like event và custom accessor

Khai báo trong ví dụ là field-like event; compiler tạo backing delegate và `add/remove` accessor. C# cũng cho tự viết custom `add`/`remove` để chuyển tiếp subscription hoặc quản lý storage đặc biệt. Đây là công cụ framework-level; code ứng dụng thường nên bắt đầu bằng field-like event đơn giản.

### Event instance và static event

Event instance thuộc một publisher object cụ thể. Static event thuộc type/process và dễ giữ subscriber rất lâu; phải có ownership unsubscribe đặc biệt rõ. Không dùng static event như một global message bus tiện tay.

### Thread safety

Việc add/remove field-like event được compiler triển khai an toàn ở mức cập nhật delegate, nhưng toàn bộ business state và quan hệ với thời điểm raise không tự thread-safe. Race giữa unsubscribe và invocation vẫn có thể khiến handler đang được gọi từ snapshot invocation hiện tại. Concurrency cần policy riêng và sẽ học sau.

## 6. Lỗi thường gặp

### Công khai delegate thay vì event

Public delegate cho caller quyền gán đè hoặc invoke notification giả. Dùng `event` khi bên ngoài chỉ được subscribe/unsubscribe.

### Raise event trước khi state hợp lệ

Nếu phát event trước `Stock` được commit, subscriber đọc publisher sẽ thấy state cũ. Validate, cập nhật invariant, rồi raise fact tương ứng; nếu commit có thể rollback, định nghĩa semantics rõ hơn.

### Không unsubscribe khỏi publisher sống lâu

Publisher giữ delegate, delegate giữ subscriber target. Subscriber ngắn hạn phải hủy đăng ký khi lifecycle kết thúc hoặc dùng cơ chế ownership khác.

### Subscribe cùng handler nhiều lần

Mỗi `+=` thêm entry. Handler chạy lặp và một `-=` chỉ bỏ một matching occurrence theo quy tắc delegate. Đừng coi event như set tự loại trùng.

### Cho rằng handler tự chạy song song

Invocation mặc định đồng bộ, tuần tự. Không đặt I/O chậm vào handler của hot path nếu chưa thiết kế async/backpressure.

### Nuốt exception của mọi handler

`catch { }` làm mất lỗi và che trạng thái thiếu notification. Nếu cần cô lập, xác định handler nào best-effort, log đủ context và quyết định retry/dead-letter rõ ràng.

## 7. Bài tập

### Bài 1 — Nhiệt độ vượt ngưỡng

Tạo `TemperatureSensor` phát `TemperatureExceeded` chỉ khi value đi từ không vượt sang vượt threshold. Hai subscriber in console theo format khác nhau.

**Gợi ý:** lưu previous/current value; event data là snapshot get-only.

### Bài 2 — Subscribe và unsubscribe

Đăng ký cùng một handler hai lần, raise, hủy một lần rồi raise lại. Dự đoán số lần gọi trước khi chạy.

**Gợi ý:** vẽ invocation list như một danh sách có thứ tự, không phải set.

### Bài 3 — Publisher lifetime

Vẽ graph khi một static publisher giữ event tới một subscriber tạm thời. Giải thích vì sao subscriber chưa GC-eligible và đề xuất lifecycle hủy đăng ký.

**Gợi ý:** lần theo reference từ static root đến delegate rồi target.

### Bài 4 — Exception handler

Thêm ba subscriber, subscriber thứ hai ném exception. Quan sát thứ tự và thiết kế hai policy: fail-fast và best-effort.

**Gợi ý:** event mặc định là fail-fast theo invocation; best-effort cần gọi từng delegate có log.

### Bài 5 — Event hay lời gọi service?

Phân tích: “Order đã tạo” gửi analytics và “Order phải được thanh toán trước khi xác nhận”. Chọn event hay dependency return result cho từng trường hợp.

**Gợi ý:** notification phụ trợ có thể dùng event; precondition bắt buộc cần workflow trực tiếp/transaction rõ.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt publisher, subscriber, handler và event data.
- [ ] Tôi khai báo/raise event theo `EventHandler<TEventArgs>`.
- [ ] Tôi hiểu code ngoài chỉ được `+=`/`-=` chứ không invoke event.
- [ ] Tôi phát event sau khi state hợp lệ và đúng transition nghiệp vụ.
- [ ] Tôi vẽ được publisher → delegate → subscriber target.
- [ ] Tôi biết event giữ strong reference và có thể kéo dài lifetime subscriber.
- [ ] Tôi không giả định event tự chạy async hay tự cô lập exception.

Điều hướng:

- Bài tiên quyết: [Delegate, Action, Func và Predicate](./02-delegate-action-func-predicate.md)
- Ôn encapsulation: [Property, encapsulation và access modifier](../04-csharp-co-ban/08-property-encapsulation-va-access-modifier.md)
- Bài tiếp theo: [Lambda, closure và bộ nhớ](./04-lambda-closure-va-bo-nho.md)
