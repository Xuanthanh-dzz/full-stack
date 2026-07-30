# Delegate, `Action`, `Func` và `Predicate`

## 1. Mục tiêu

Sau bài này, bạn có thể:

- truyền behavior vào method thay vì chỉ truyền dữ liệu;
- khai báo custom delegate và gán method group có signature tương thích;
- chọn `Action`, `Func` hoặc `Predicate` theo input/return contract;
- gọi delegate, ghép nhiều handler bằng `+=` và bỏ handler bằng `-=`;
- giải thích delegate là immutable reference type chứa method cùng optional target object;
- dự đoán thứ tự gọi và hành vi exception của multicast delegate;
- nhận ra trường hợp delegate làm code rõ hơn một chuỗi `if/switch` chọn thuật toán.

## 2. Bài toán mở đầu

Một chức năng tính tiền cần thay đổi theo từng chiến dịch:

- rule xác định order đủ điều kiện có thể thay;
- công thức giảm giá có thể thay;
- cách format tiền có thể thay;
- kết quả cần gửi đến một hoặc nhiều audit sink.

Nếu `OrderProcessor` chứa `switch (campaignName)` rồi gọi thẳng mọi logger concrete, mỗi rule mới buộc sửa class trung tâm. Điều processor thật sự cần không phải tên campaign, mà là **các operation có signature xác định**.

Ta sẽ đóng gói reference tới method thành delegate rồi truyền chúng như value. Bài này cố ý chỉ dùng named method; lambda expression sẽ được giới thiệu sau khi cơ chế delegate đã rõ.

## 3. Lời giải bằng code

Tạo project:

```bash
dotnet new console --name DelegateDemo --framework net9.0 --use-program-main
cd DelegateDemo
```

Thay `DelegateDemo.csproj` bằng:

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
namespace DelegateDemo;

// Custom delegate: mọi method nhận Order và trả decimal đều có thể làm policy.
internal delegate decimal DiscountPolicy(Order order);

internal static class Program
{
    private static void Main()
    {
        var order = new Order("ORD-1001", subtotal: 1_200_000m);

        // Method group được convert thành delegate theo target type bên trái.
        Predicate<Order> eligibility = OrderRules.IsLarge;
        DiscountPolicy discountPolicy = DiscountPolicies.TenPercent;
        Func<decimal, string> formatter = MoneyFormatter.AsVnd;

        PaymentSummary summary = OrderProcessor.Calculate(
            order,
            eligibility,
            discountPolicy);

        Console.WriteLine($"Eligible: {summary.IsEligible}");
        Console.WriteLine($"Discount: {summary.Discount}");
        Console.WriteLine($"Payable: {summary.Payable}");

        var sink = new AuditSink();

        // Multicast Action gọi các handler theo thứ tự trong invocation list.
        Action<string> audit = sink.Write;
        audit += ConsoleAudit.Write;
        audit($"{order.Id} payable {summary.Payable}");

        Console.WriteLine($"Formatted: {formatter(summary.Payable)}");
        Console.WriteLine($"Audit count: {sink.Count}");
    }
}

internal static class OrderProcessor
{
    public static PaymentSummary Calculate(
        Order order,
        Predicate<Order> eligibility,
        DiscountPolicy discountPolicy)
    {
        ArgumentNullException.ThrowIfNull(order);
        ArgumentNullException.ThrowIfNull(eligibility);
        ArgumentNullException.ThrowIfNull(discountPolicy);

        bool isEligible = eligibility(order);
        decimal discount = isEligible ? discountPolicy(order) : 0m;

        if (discount < 0m || discount > order.Subtotal)
        {
            throw new InvalidOperationException(
                "Discount policy returned an invalid amount.");
        }

        return new PaymentSummary(
            isEligible,
            discount,
            order.Subtotal - discount);
    }
}

internal static class OrderRules
{
    public static bool IsLarge(Order order)
    {
        return order.Subtotal >= 1_000_000m;
    }
}

internal static class DiscountPolicies
{
    public static decimal TenPercent(Order order)
    {
        return order.Subtotal * 10m / 100m;
    }

    public static decimal NoDiscount(Order order)
    {
        ArgumentNullException.ThrowIfNull(order);
        return 0m;
    }
}

internal static class MoneyFormatter
{
    public static string AsVnd(decimal amount)
    {
        return $"{amount} VND";
    }
}

internal sealed class AuditSink
{
    public int Count { get; private set; }

    public void Write(string message)
    {
        Count++;
        Console.WriteLine($"AUDIT[{Count}]: {message}");
    }
}

internal static class ConsoleAudit
{
    public static void Write(string message)
    {
        Console.WriteLine($"AUDIT-CONSOLE: {message}");
    }
}

internal sealed class Order
{
    public string Id { get; }
    public decimal Subtotal { get; }

    public Order(string id, decimal subtotal)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        if (subtotal < 0m)
        {
            throw new ArgumentOutOfRangeException(nameof(subtotal));
        }

        Id = id.Trim();
        Subtotal = subtotal;
    }
}

internal sealed class PaymentSummary
{
    public bool IsEligible { get; }
    public decimal Discount { get; }
    public decimal Payable { get; }

    public PaymentSummary(bool isEligible, decimal discount, decimal payable)
    {
        IsEligible = isEligible;
        Discount = discount;
        Payable = payable;
    }
}
```

Build và chạy:

```bash
dotnet build --configuration Release
dotnet run --configuration Release --no-build
```

Kết quả chính xác:

```text
Eligible: True
Discount: 120000
Payable: 1080000
AUDIT[1]: ORD-1001 payable 1080000
AUDIT-CONSOLE: ORD-1001 payable 1080000
Formatted: 1080000 VND
Audit count: 1
```

## 4. Giải thích cơ chế

### 4.1 Delegate type định nghĩa signature

Khai báo:

```csharp
internal delegate decimal DiscountPolicy(Order order);
```

tạo một type. Một method có thể được gán vào `DiscountPolicy` khi parameter và return type tương thích theo quy tắc delegate conversion. `DiscountPolicies.TenPercent` nhận `Order`, trả `decimal`, nên assignment sau hợp lệ:

```csharp
DiscountPolicy policy = DiscountPolicies.TenPercent;
```

Tên method không cần trùng tên delegate; contract nằm ở signature. `DiscountPolicy` khác một method call: biến `policy` là value có thể lưu trong field, truyền làm argument, return khỏi method và gọi về sau.

### 4.2 Method group conversion

`DiscountPolicies.TenPercent` không có `()` nên chưa gọi method. Nó là **method group**. Compiler nhìn target type `DiscountPolicy`, chọn overload tương thích và tạo delegate value. Đến câu:

```csharp
decimal discount = policy(order);
```

delegate mới invoke method đã lưu.

Nếu method group có nhiều overload mà target delegate không đủ để chọn duy nhất, build thất bại. Ghi type delegate rõ ràng thường giúp overload resolution và giúp người đọc thấy contract.

### 4.3 `Action`, `Func` và `Predicate`

.NET cung cấp các generic delegate phổ biến:

```text
Action<T1,...>       nhận input, trả void
Func<T1,...,TResult> nhận input, type argument cuối là return type
Predicate<T>         nhận một T, trả bool
```

Trong code:

```csharp
Action<string> audit = sink.Write;
Func<decimal, string> formatter = MoneyFormatter.AsVnd;
Predicate<Order> eligibility = OrderRules.IsLarge;
```

`Predicate<Order>` và `Func<Order, bool>` có cùng hình dạng method nhưng là hai delegate type khác nhau. Chọn `Predicate<T>` khi tên đó làm rõ ý nghĩa kiểm tra; chọn `Func<T,bool>` khi API đã dùng họ `Func` hoặc có nhiều input.

Custom delegate có giá trị khi domain cần một tên contract rõ như `DiscountPolicy`, hoặc khi cần feature riêng của signature như parameter modifier mà họ `Func/Action` không biểu diễn phù hợp.

### 4.4 Delegate tới static và instance method

`discountPolicy` trỏ static method, nên không cần target object. `audit` ban đầu trỏ instance method `sink.Write`, nên delegate phải giữ cả reference tới `sink` và thông tin method cần gọi:

```text
Main local                         Managed heap
+-------------------+             +--------------------------+
| sink ref ----------+-----------> | AuditSink object H1      |
| audit ref ---------+------+      | Count = 0                |
+-------------------+      |      +--------------------------+
                           v                    ^
                    +----------------------+    |
                    | delegate object D1   |    |
                    | method: Write        |    |
                    | target ref ----------+----+
                    +----------------------+
```

Khi invoke D1, runtime dùng target H1 làm `this`. Vì vậy `Count++` cập nhật đúng `AuditSink` object. Delegate giữ target reachable; nếu delegate sống lâu, target cũng có thể sống lâu.

### 4.5 Multicast delegate và tính immutable

Mọi delegate có thể có invocation list. Câu:

```csharp
audit += ConsoleAudit.Write;
```

về ngữ nghĩa tạo một delegate value mới có danh sách `[sink.Write, ConsoleAudit.Write]`, rồi gán reference mới vào `audit`. Delegate object là immutable; `+=` không sửa tại chỗ D1.

Khi gọi, handler chạy theo thứ tự đăng ký. Với `Action`, mọi handler không lỗi đều được gọi. Nếu một handler ném exception và caller không bắt, invocation dừng; các handler phía sau không chạy. Runtime không tự cô lập/log/retry từng handler.

Với multicast delegate có return value, caller thông thường chỉ nhận kết quả của handler cuối. Đây thường là contract khó hiểu; multicast phù hợp nhất với notification trả `void`.

### 4.6 Bỏ handler và equality

`audit -= sink.Write` loại entry tương ứng khỏi invocation list và trả delegate mới. Delegate equality xét cùng method và cùng target object cho entry tương ứng. Hai object `AuditSink` khác nhau dù cùng method body vẫn tạo handler khác vì target identity khác.

Nếu không còn entry nào, phép trừ có thể cho kết quả `null`; nullable delegate và cách gọi an toàn sẽ được làm rõ ở bài event và nullable reference type.

## 5. Kiến thức nền

### Delegate là reference type

Biến delegate chứa reference hoặc `null`, không chứa trực tiếp toàn bộ code của method. Assignment delegate copy reference như class. Ghép invocation list thường tạo delegate object mới; nó không clone target object.

### Behavior như dữ liệu có type

Delegate cho phép caller quyết định một phần behavior trong khi processor giữ workflow chung. `OrderProcessor` vẫn sở hữu validation discount; policy chỉ tính con số. Ranh giới này giúp tránh policy tùy ý phá invariant của processor.

### Return delegate từ method

Method có thể chọn và trả delegate dựa trên configuration:

```csharp
private static DiscountPolicy SelectPolicy(bool vip)
{
    return vip
        ? DiscountPolicies.TenPercent
        : DiscountPolicies.NoDiscount;
}
```

`NoDiscount` đã có trong sample và trả `0m`. Nếu đặt `SelectPolicy` vào class `Program`, đoạn code trên compile mà không cần đổi contract. Đừng trả `null` để biểu diễn “không giảm” khi một policy trả `0m` diễn đạt rõ hơn.

### Delegate khác interface strategy

Delegate phù hợp với một operation nhỏ. Interface phù hợp khi strategy cần nhiều method liên quan, state được công khai qua contract hoặc lifecycle riêng. Không cần tạo class strategy cho một phép tính một dòng; cũng không ép workflow nhiều operation vào hàng loạt delegate rời nếu chúng phải nhất quán với nhau.

## 6. Lỗi thường gặp

### Viết `method()` khi muốn truyền method

`Process(Calculate())` truyền **kết quả** lời gọi. `Process(Calculate)` truyền method group để convert thành delegate. Nhìn parameter type của `Process` để biết API cần dữ liệu hay behavior.

### Chọn sai thứ tự type argument của `Func`

Trong `Func<decimal, string>`, `decimal` là input và `string` cuối cùng là output. `Func<string, decimal>` là contract khác hoàn toàn.

### Ghép delegate có return value rồi mong nhận mọi kết quả

Invocation thông thường chỉ trả kết quả cuối. Nếu cần gom nhiều kết quả, quản lý collection strategy và lặp rõ ràng thay vì dựa vào multicast return.

### Cho rằng multicast tự tiếp tục sau exception

Handler ném lỗi dừng lời gọi. Nếu nghiệp vụ cần best-effort, caller phải đọc invocation list và cô lập từng handler có chủ đích; cách đó cần policy logging/retry rõ, không phải `catch { }` rỗng.

### Quên target object bị delegate giữ lại

Delegate tới instance method giữ reference target. Khi delegate được lưu ở object sống rất lâu, target có thể chưa được GC dù code khác không còn dùng. Event ở bài sau là tình huống thường gặp nhất.

### Dùng delegate để che dependency quan trọng

Truyền mười delegate vào constructor làm contract rời rạc và khó đảm bảo nhất quán. Nhóm behavior liên quan thành interface/class nếu chúng cùng một capability.

## 7. Bài tập

### Bài 1 — Phí giao hàng

Khai báo `ShippingFeePolicy` nhận trọng lượng và trả phí. Viết hai named method `Standard` và `Express`, rồi truyền từng policy vào một method in báo giá.

**Gợi ý:** validation trọng lượng nên nằm ở workflow chung hoặc trong contract được quy định nhất quán.

### Bài 2 — Dùng đủ ba delegate chuẩn

Tạo `Predicate<int>` kiểm tra số dương, `Func<int,string>` format và `Action<string>` in kết quả.

**Gợi ý:** chỉ dùng named method; dự đoán signature trước khi khai báo biến.

### Bài 3 — Multicast audit

Tạo hai `AuditSink` object, ghép method `Write` của cả hai vào một `Action<string>`, gọi, bỏ một handler rồi gọi lại.

**Gợi ý:** theo dõi target identity và vẽ invocation list sau mỗi `+=`/`-=`.

### Bài 4 — Exception trong invocation list

Tạo ba handler, handler thứ hai ném exception. Quan sát handler nào chạy và thiết kế policy best-effort có log rõ.

**Gợi ý:** lab được phép dùng `GetInvocationList`; cast từng entry đúng delegate type và không nuốt exception.

### Bài 5 — Delegate hay interface?

Phân tích hai use case: một công thức tính thuế; một payment provider có `Charge`, `Refund`, `HealthCheck`. Chọn delegate hay interface và giải thích coupling.

**Gợi ý:** một operation độc lập nghiêng về delegate; capability nhiều operation/state nghiêng về interface.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi khai báo được custom delegate có signature rõ.
- [ ] Tôi phân biệt method group với lời gọi method.
- [ ] Tôi chọn đúng `Action`, `Func`, `Predicate` hoặc custom delegate.
- [ ] Tôi giải thích delegate instance method giữ target reference nào.
- [ ] Tôi biết `+=`/`-=` tạo delegate value mới và hiểu invocation order.
- [ ] Tôi dự đoán được exception sẽ dừng multicast invocation.
- [ ] Tôi chọn delegate hay interface dựa trên shape của capability.

Điều hướng:

- Bài tiên quyết: [Generics và constraints](./01-generics-va-constraints.md)
- Ôn method/parameter: [Method, parameter và return](../04-csharp-co-ban/04-method-parameter-va-return.md)
- Bài tiếp theo: [Event và event handler](./03-event-va-event-handler.md)
