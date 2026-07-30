# Abstract class, interface và composition

## 1. Mục tiêu

Sau bài này, bạn có thể:

- Dùng abstract class khi một họ type cần chung state, constructor và implementation.
- Phân biệt abstract member, virtual member và concrete member.
- Định nghĩa/implement interface như một contract về khả năng (`capability`).
- Cho một class implement nhiều interface và dùng từng interface reference độc lập.
- Hiểu cách gọi default interface implementation và các trade-off của nó.
- Dùng composition để một object cộng tác với các object khác qua reference field.
- Chọn giữa concrete class, abstract class, interface và composition dựa trên nhu cầu thay đổi.

## 2. Bài toán mở đầu

Một chức năng checkout cần:

- Thu tiền bằng card hoặc bank transfer.
- Mọi payment gateway phải dùng chung validation và tạo cùng dạng receipt.
- Một số gateway hỗ trợ refund; không phải mọi gateway buộc phải có khả năng này.
- Receipt có thể được gửi bằng nhiều kênh.
- Checkout không nên kế thừa gateway hay receipt sender; nó chỉ cần phối hợp các thành phần đó.

Nếu `CheckoutService` tự chứa mọi nhánh `if (paymentType == ...)`, mỗi gateway mới làm class phình to. Nếu tạo một base class chứa mọi khả năng tùy chọn, derived class sẽ phải có các method vô nghĩa như `Refund()` dù provider không hỗ trợ. Ta cần chọn abstraction theo từng loại quan hệ.

## 3. Lời giải bằng code

Tạo project .NET 9:

```bash
mkdir csharp-abstraction-demo
cd csharp-abstraction-demo
dotnet new console --framework net9.0
# Thay toàn bộ Program.cs bằng code bên dưới.
dotnet build
dotnet run
```

`Program.cs`:

```csharp
using System;

internal static class Program
{
    private static void Main()
    {
        CardPaymentGateway cardGateway = new CardPaymentGateway("DemoPay");
        IReceiptSender receiptSender = new ConsoleReceiptSender();

        // Composition: CheckoutService giữ reference tới hai collaborator.
        CheckoutService cardCheckout = new CheckoutService(
            cardGateway,
            receiptSender);

        PaymentReceipt cardReceipt = cardCheckout.PlaceOrder(
            orderId: "ORD-1001",
            amount: 1_250_000m,
            receiptDestination: "an@example.com");

        // Một object có thể được nhìn qua nhiều interface reference.
        IRefundable refundable = cardGateway;
        refundable.Refund(cardReceipt, 250_000m);

        IHealthCheck healthCheck = cardGateway;
        Console.WriteLine(healthCheck.GetHealthStatus());

        Console.WriteLine();

        // Thay gateway; CheckoutService không đổi implementation.
        PaymentGateway bankGateway = new BankTransferGateway("VCB");
        CheckoutService bankCheckout = new CheckoutService(
            bankGateway,
            receiptSender);

        bankCheckout.PlaceOrder(
            orderId: "ORD-1002",
            amount: 800_000m,
            receiptDestination: "binh@example.com");

        // Không hợp lệ: abstract class không thể được tạo trực tiếp.
        // PaymentGateway invalid = new PaymentGateway("Unknown");
    }
}

internal abstract class PaymentGateway
{
    public string ProviderName { get; }

    protected PaymentGateway(string providerName)
    {
        if (string.IsNullOrWhiteSpace(providerName))
        {
            throw new ArgumentException(
                "Provider name must not be empty.",
                nameof(providerName));
        }

        ProviderName = providerName.Trim();
    }

    // Concrete template method: validation dùng chung, rồi gọi extension point.
    public PaymentReceipt Charge(string orderId, decimal amount)
    {
        if (string.IsNullOrWhiteSpace(orderId))
        {
            throw new ArgumentException("Order ID must not be empty.", nameof(orderId));
        }

        if (amount <= 0m)
        {
            throw new ArgumentOutOfRangeException(
                nameof(amount),
                "Amount must be positive.");
        }

        string providerReference = ExecuteCharge(orderId.Trim(), amount);

        return new PaymentReceipt(
            orderId.Trim(),
            amount,
            ProviderName,
            providerReference,
            DateTimeOffset.UtcNow);
    }

    // Không có implementation chung; mỗi concrete gateway bắt buộc implement.
    protected abstract string ExecuteCharge(string orderId, decimal amount);
}

internal sealed class CardPaymentGateway : PaymentGateway, IRefundable, IHealthCheck
{
    public CardPaymentGateway(string providerName)
        : base(providerName)
    {
    }

    protected override string ExecuteCharge(string orderId, decimal amount)
    {
        Console.WriteLine(
            $"Charging card via {ProviderName}: {amount:N0} VND for {orderId}");

        // Demo local: hệ thống thật nhận reference từ provider qua HTTPS/gRPC.
        return $"CARD-{Guid.NewGuid():N}";
    }

    public void Refund(PaymentReceipt receipt, decimal amount)
    {
        ArgumentNullException.ThrowIfNull(receipt);

        if (amount <= 0m || amount > receipt.Amount)
        {
            throw new ArgumentOutOfRangeException(
                nameof(amount),
                "Refund must be positive and not exceed the charged amount.");
        }

        Console.WriteLine(
            $"Refund accepted: {amount:N0} VND for {receipt.OrderId}");
    }

    // Không cần implement GetHealthStatus(): dùng default interface implementation.
}

internal sealed class BankTransferGateway : PaymentGateway, IHealthCheck
{
    public BankTransferGateway(string bankCode)
        : base(bankCode)
    {
    }

    protected override string ExecuteCharge(string orderId, decimal amount)
    {
        Console.WriteLine(
            $"Creating transfer via {ProviderName}: {amount:N0} VND for {orderId}");

        return $"BANK-{Guid.NewGuid():N}";
    }

    // Concrete implementation thắng default implementation của interface.
    public string GetHealthStatus()
    {
        return $"{ProviderName}: health endpoint configured";
    }
}

internal interface IRefundable
{
    void Refund(PaymentReceipt receipt, decimal amount);
}

internal interface IReceiptSender
{
    void Send(PaymentReceipt receipt, string destination);
}

internal interface IHealthCheck
{
    // Default interface implementation: implementer có thể dùng hoặc thay thế.
    string GetHealthStatus()
    {
        return "Healthy (default check)";
    }
}

internal sealed class ConsoleReceiptSender : IReceiptSender
{
    public void Send(PaymentReceipt receipt, string destination)
    {
        if (string.IsNullOrWhiteSpace(destination))
        {
            throw new ArgumentException(
                "Receipt destination must not be empty.",
                nameof(destination));
        }

        Console.WriteLine(
            $"Receipt sent to {destination}: {receipt.OrderId}, " +
            $"{receipt.Amount:N0} VND, provider {receipt.ProviderName}");
    }
}

internal sealed class CheckoutService
{
    private readonly PaymentGateway _paymentGateway;
    private readonly IReceiptSender _receiptSender;

    public CheckoutService(
        PaymentGateway paymentGateway,
        IReceiptSender receiptSender)
    {
        ArgumentNullException.ThrowIfNull(paymentGateway);
        ArgumentNullException.ThrowIfNull(receiptSender);

        _paymentGateway = paymentGateway;
        _receiptSender = receiptSender;
    }

    public PaymentReceipt PlaceOrder(
        string orderId,
        decimal amount,
        string receiptDestination)
    {
        PaymentReceipt receipt = _paymentGateway.Charge(orderId, amount);
        _receiptSender.Send(receipt, receiptDestination);
        return receipt;
    }
}

internal sealed class PaymentReceipt
{
    public string OrderId { get; }
    public decimal Amount { get; }
    public string ProviderName { get; }
    public string ProviderReference { get; }
    public DateTimeOffset PaidAtUtc { get; }

    public PaymentReceipt(
        string orderId,
        decimal amount,
        string providerName,
        string providerReference,
        DateTimeOffset paidAtUtc)
    {
        OrderId = orderId;
        Amount = amount;
        ProviderName = providerName;
        ProviderReference = providerReference;
        PaidAtUtc = paidAtUtc;
    }
}
```

Kết quả có dạng sau (transaction reference thay đổi mỗi lần chạy):

```text
Charging card via DemoPay: 1,250,000 VND for ORD-1001
Receipt sent to an@example.com: ORD-1001, 1,250,000 VND, provider DemoPay
Refund accepted: 250,000 VND for ORD-1001
Healthy (default check)

Creating transfer via VCB: 800,000 VND for ORD-1002
Receipt sent to binh@example.com: ORD-1002, 800,000 VND, provider VCB
```

## 4. Giải thích cơ chế

### 4.1 Abstract class là base class chưa hoàn chỉnh

`PaymentGateway` có ba loại member:

- State chung: `ProviderName`.
- Concrete behavior chung: constructor validation và `Charge()`.
- Extension point bắt buộc: abstract method `ExecuteCharge()`.

```csharp
internal abstract class PaymentGateway
{
    public PaymentReceipt Charge(...) { ... }
    protected abstract string ExecuteCharge(...);
}
```

Không thể `new PaymentGateway(...)` vì runtime sẽ không biết chạy implementation nào cho abstract member. Concrete derived class phải override mọi abstract member còn thiếu, nếu không chính derived class cũng phải là `abstract`.

`Charge()` đóng vai trò template: giữ validation và quy trình tạo receipt ở một nơi; chỉ bước giao tiếp provider thay đổi. Vì `ExecuteCharge` là `protected`, consumer không gọi trực tiếp và không thể bỏ qua validation public.

### 4.2 `abstract`, `virtual` và concrete member

| Loại member | Base có implementation? | Derived bắt buộc override? | Derived được override? |
|---|---:|---:|---:|
| Concrete, không `virtual` | Có | Không | Không |
| `virtual` | Có | Không | Có |
| `abstract` | Không | Có (ở concrete class) | Có/bắt buộc |

Trong một **class**, member có modifier `abstract` chỉ được khai báo khi class đó cũng là `abstract`. Một abstract class vẫn có constructor, field, concrete method và virtual method như class thường; chỉ bản thân nó không được tạo trực tiếp. Interface có quy tắc riêng: instance member không có thân mặc nhiên là contract trừu tượng, và C# hiện đại còn hỗ trợ một số dạng member có implementation hoặc `static abstract`.

### 4.3 Interface mô tả một vai trò

`IRefundable` không nói object phải kế thừa cây class nào. Nó chỉ hứa:

```csharp
void Refund(PaymentReceipt receipt, decimal amount);
```

`CardPaymentGateway` vừa là `PaymentGateway`, vừa cung cấp hai vai trò:

```csharp
CardPaymentGateway : PaymentGateway, IRefundable, IHealthCheck
```

C# chỉ cho kế thừa một class nhưng cho implement nhiều interface. Điều này phù hợp với capability độc lập: refundable, health-checkable, comparable, disposable, ...

Khi gán:

```csharp
IRefundable refundable = cardGateway;
IHealthCheck healthCheck = cardGateway;
```

không có object gateway mới:

```text
Stack frame Main                         Managed heap
+--------------------------+             +----------------------------+
| cardGateway: reference ---+------------>| CardPaymentGateway object |
| refundable: reference ----+------------>| ProviderName -> "DemoPay"|
| healthCheck: reference ---+------------>| ...                       |
+--------------------------+             +----------------------------+
```

Mỗi reference chỉ cung cấp compile-time contract khác nhau; runtime object vẫn là một.

### 4.4 Default interface implementation

`IHealthCheck.GetHealthStatus()` có thân method mặc định. `CardPaymentGateway` không implement method nên lời gọi qua `IHealthCheck` dùng phần mặc định:

```csharp
IHealthCheck health = cardGateway;
health.GetHealthStatus();
```

Default interface member thường không xuất hiện như một member trực tiếp của class:

```csharp
// cardGateway.GetHealthStatus(); // Không compile trong ví dụ này.
```

Ta gọi qua interface reference. `BankTransferGateway` khai báo concrete method cùng signature nên implementation đó được dùng.

### 4.5 Composition: object giữ reference tới collaborator

`CheckoutService` không phải (`is-a`) payment gateway hay receipt sender. Nó **có** (`has-a`) các collaborator:

```csharp
private readonly PaymentGateway _paymentGateway;
private readonly IReceiptSender _receiptSender;
```

Mô hình bộ nhớ:

```text
checkout variable
      |
      v
+-----------------------------+
| CheckoutService object      |
| _paymentGateway ref --------+----> CardPaymentGateway object
| _receiptSender ref ---------+----> ConsoleReceiptSender object
+-----------------------------+
```

`new CheckoutService(...)` tạo một service object mới. Nó copy hai reference vào readonly field; không clone gateway/sender và không nhúng hai object thành một object duy nhất. Các object có lifetime riêng theo reference còn tồn tại.

Đổi `CardPaymentGateway` sang `BankTransferGateway` tạo cấu hình object graph khác, nhưng `CheckoutService.PlaceOrder()` không đổi. Đây là ưu điểm chính của composition: ghép behavior tại boundary rõ ràng.

### 4.6 Constructor injection

Constructor nhận dependency bắt buộc:

```csharp
public CheckoutService(PaymentGateway paymentGateway, IReceiptSender receiptSender)
```

Nhờ đó:

- Service không thể được tạo ở trạng thái thiếu dependency.
- Caller quyết định concrete implementation.
- Test có thể cung cấp fake implementation.
- Dependency hiện rõ trong API thay vì bị tạo ẩn bên trong method.

Đây là constructor injection ở dạng cơ bản. ASP.NET Core sau này có DI container tự xây object graph, nhưng cơ chế cốt lõi vẫn là truyền reference qua constructor.

## 5. Kiến thức nền

### 5.1 Khi nào chọn abstract class?

Chọn abstract class khi các type có quan hệ `is-a` chặt và cần một hoặc nhiều yếu tố:

- Chung instance state/constructor.
- Chung protected helper hoặc concrete workflow.
- Kiểm soát extension point bằng `protected abstract`/`protected virtual`.
- Muốn tiến hóa implementation base mà không đưa mọi chi tiết vào public contract.

Chi phí: class đã dùng “một slot” base class duy nhất và derived type bị coupling vào hierarchy.

### 5.2 Khi nào chọn interface?

Chọn interface khi cần mô tả contract/capability mà nhiều type không cùng cây class có thể thực hiện:

- Một object có nhiều vai trò.
- Consumer chỉ cần một nhóm operation nhỏ.
- Cần thay implementation độc lập.
- Không cần chia sẻ instance state/constructor qua contract.

Giữ interface tập trung. Interface quá lớn buộc implementer có method không liên quan; nhiều interface nhỏ theo vai trò thường dễ dùng và kiểm thử hơn.

### 5.3 Khi nào dùng concrete class trực tiếp?

Không phải mọi class đều cần interface hoặc abstract base. Nếu chỉ có một implementation, không có boundary cần thay thế và contract ổn định, concrete dependency có thể đơn giản nhất. Tạo interface “phòng khi cần” cho mọi class làm tăng file và indirection mà chưa tạo giá trị.

Hãy thêm abstraction tại nơi có biến thiên thực hoặc boundary kiến trúc rõ, không dựa vào số lượng class mong muốn trong tương lai.

### Đào sâu (có thể quay lại sau)

Default implementation hữu ích khi tiến hóa interface mà vẫn cung cấp behavior tương thích cho implementer cũ. Tuy nhiên, nó có thể làm contract khó hiểu, gây xung đột khi nhiều interface cung cấp cùng member và không có instance state như field của class. Dùng sparingly; behavior nghiệp vụ quan trọng thường rõ hơn ở class/service hoặc implementation tường minh.

#### Interface không phải marker tùy tiện

Interface rỗng chỉ để gắn nhãn thường yếu hơn attribute hoặc metadata rõ ràng. Một interface có giá trị khi consumer thật sự gọi contract hoặc dùng nó như một ranh giới type có ý nghĩa.

#### Explicit interface implementation

Khi hai interface có member cùng tên nhưng semantics khác, hoặc muốn member chỉ thấy qua interface, class có thể implement tường minh:

```csharp
void IFirst.Reset() { }
void ISecond.Reset() { }
```

Khi đó phải cast/gán sang interface tương ứng để gọi. Dùng khi cần giải quyết xung đột contract; nếu hai operation khác nghĩa, đổi tên interface member thường dễ hiểu hơn nếu bạn kiểm soát API.

#### Interface segregation và dependency direction

`CheckoutService` chỉ cần `IReceiptSender.Send`, nên không phụ thuộc một interface khổng lồ có cả template editor, inbox reader và analytics. Contract nhỏ giảm coupling.

Ở thiết kế lớn hơn, abstraction thường được sở hữu gần consumer để dependency hướng vào policy ổn định. Các nguyên lý SOLID và dependency inversion sẽ được học trong module OOP/thiết kế.

## 6. Lỗi thường gặp

### 6.1 Cố `new` abstract class hoặc interface

Abstract type chưa đủ implementation để tạo object. Hãy tạo concrete implementation rồi giữ reference dưới abstraction:

```csharp
PaymentGateway gateway = new CardPaymentGateway("DemoPay");
```

### 6.2 Abstract base chỉ chứa abstract public member, không có state/logic chung

Nếu base class không chia sẻ state, constructor hay implementation và chỉ mô tả capability, interface có thể phù hợp hơn, tránh khóa single inheritance.

### 6.3 Interface quá lớn

Buộc mọi payment gateway implement cả charge, refund, subscription, crypto conversion làm xuất hiện method `NotSupportedException`. Tách capability tùy chọn như `IRefundable`.

### 6.4 Kế thừa để biểu diễn quan hệ `has-a`

`CheckoutService : CardPaymentGateway` là sai: checkout không phải gateway. Giữ dependency trong field và truyền qua constructor.

### 6.5 Tạo dependency concrete bên trong service

```csharp
public CheckoutService()
{
    _paymentGateway = new CardPaymentGateway("DemoPay");
}
```

khóa service vào provider, giấu dependency và làm test khó. Đưa dependency bắt buộc vào constructor.

### 6.6 Cho rằng implement nhiều interface tạo nhiều object

Một object có thể được nhìn qua nhiều interface reference; assignment không clone object. State vẫn chỉ có một bản cho instance đó.

### 6.7 Lạm dụng default interface implementation

Đặt workflow phức tạp vào nhiều interface default method làm behavior phân tán và khó dự đoán. Dùng cho default nhỏ, ổn định, có semantics rõ; ưu tiên composition/service cho policy nghiệp vụ.

### 6.8 Interface chỉ tồn tại để mock

Testability là lợi ích, nhưng abstraction nên đại diện boundary/capability thật. Với class thuần tính toán, có thể test trực tiếp mà không cần interface một-implementation.

### 6.9 Trả concrete type không cần thiết

Nếu consumer chỉ cần `IReceiptSender`, nhận/trả abstraction đó giúp giảm coupling. Nhưng đừng trả interface quá hẹp nếu caller hợp lệ cần concrete behavior; contract phải xuất phát từ use case thực.

## 7. Bài tập

### Bài 1 — Kênh thông báo

Tạo interface `INotificationSender` với `Send()`, implement `EmailSender` và `SmsSender`. Viết `AlertService` nhận sender qua constructor và chứng minh thay implementation mà không sửa service.

Gợi ý: service giữ một readonly interface reference; validation recipient nằm ở sender phù hợp.

### Bài 2 — Abstract exporter

Tạo abstract class `ReportExporter` có concrete method `Export()` thực hiện validation/timing và protected abstract `WriteContent()`. Implement `CsvExporter` và `JsonExporter`.

Gợi ý: dùng template method để caller không bỏ qua bước chung; không cần package ngoài.

### Bài 3 — Nhiều interface

Tạo `SmartPrinter` implement `IPrintable`, `IScannable`, `IHealthCheck`. Giữ cùng object qua ba biến interface và dùng `ReferenceEquals` để kiểm chứng identity.

Gợi ý: mỗi interface chỉ chứa capability liên quan; vẽ reference trước khi chạy.

### Bài 4 — Default implementation

Thêm default method nhỏ vào `IHealthCheck`, tạo một class dùng mặc định và một class override. Gọi qua interface reference rồi giải thích compile-time/runtime dispatch.

Gợi ý: thử gọi default member trực tiếp qua biến concrete type và ghi lại compiler error; không biến default method thành workflow phức tạp.

### Bài 5 — Chọn abstraction

Thiết kế hệ thống lưu file có local disk và cloud storage. Quyết định phần nào là interface, có cần abstract base class không, và service nào composition chúng. Viết ADR ngắn 5–8 dòng giải thích trade-off.

Gợi ý: xác định state/implementation thật sự dùng chung trước khi chọn abstract class; đừng tạo base chỉ vì tên type giống nhau.

## 8. Checklist tự đánh giá và điều hướng

Bạn hoàn thành bài khi có thể tự trả lời:

- [ ] Tôi phân biệt abstract, virtual và concrete member.
- [ ] Tôi biết khi nào abstract class có giá trị nhờ state/constructor/implementation chung.
- [ ] Tôi định nghĩa và implement được interface nhỏ theo capability.
- [ ] Tôi hiểu một class chỉ kế thừa một class nhưng có thể implement nhiều interface.
- [ ] Tôi vẽ được nhiều interface reference cùng trỏ một object.
- [ ] Tôi gọi được default interface implementation và hiểu hạn chế của nó.
- [ ] Tôi dùng composition và constructor injection để ghép collaborator.
- [ ] Tôi chọn concrete class, abstract class hay interface dựa trên biến thiên thật, không theo thói quen.

Điều hướng:

- Bài tiên quyết: [Inheritance và polymorphism](./09-inheritance-polymorphism.md)
- Bài tiếp theo: [`struct`, `enum` và tuple](./11-struct-enum-va-tuple.md)
