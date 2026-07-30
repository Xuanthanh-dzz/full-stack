# Extension method

## 1. Mục tiêu

Sau bài này, bạn có thể:

- thêm cú pháp gọi method lên một type mà không sửa source hay kế thừa type đó;
- khai báo extension method bằng static class, static method và `this` ở parameter đầu;
- giải thích lời gọi extension được bind ở compile time và hạ thành static method call;
- viết generic extension method cho interface collection;
- phân biệt extension method với instance method, polymorphism và mutation;
- vẽ allocation thật: extension call không tạo wrapper, nhưng thân method vẫn có thể tạo object;
- tổ chức namespace và tránh biến extension thành “thùng utility” khó khám phá.

## 2. Bài toán mở đầu

Ứng dụng bán hàng có class `Order` tập trung bảo vệ dữ liệu order. Nhiều màn hình lại cần các operation đọc:

- tính tổng từ các line;
- lấy các order có tổng tối thiểu;
- format một dòng hiển thị;
- kiểm tra một collection có rỗng không.

Ta không muốn nhét mọi format/report theo từng UI vào domain class. Ta cũng không thể kế thừa `List<Order>` chỉ để thêm một helper, và cách gọi `OrderUtilities.CalculateTotal(order)` làm pipeline đọc kém tự nhiên.

Extension method cho phép viết `order.Total()` hoặc `orders.WithMinimumTotal(...)` trong khi implementation vẫn là static method bình thường. Nó là công cụ tổ chức API ở compile time, không thay đổi object hay CLR type gốc.

## 3. Lời giải bằng code

Tạo project:

```bash
dotnet new console --name ExtensionMethodDemo --framework net9.0 --use-program-main
cd ExtensionMethodDemo
```

Thay `ExtensionMethodDemo.csproj` bằng:

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
namespace ExtensionMethodDemo;

internal static class Program
{
    private static void Main()
    {
        var orders = new List<Order>
        {
            new Order(
                "ORD-1001",
                new List<OrderLine>
                {
                    new OrderLine("Keyboard", quantity: 2, unitPrice: 300_000m),
                    new OrderLine("Cable", quantity: 1, unitPrice: 100_000m)
                }),
            new Order(
                "ORD-1002",
                new List<OrderLine>
                {
                    new OrderLine("Mouse", quantity: 1, unitPrice: 250_000m)
                })
        };

        List<Order> selected = orders.WithMinimumTotal(500_000m);

        Console.WriteLine($"Selected count: {selected.Count}");
        foreach (Order order in selected)
        {
            Console.WriteLine(order.ToDisplayLine());
        }

        // Hai cú pháp dưới gọi cùng implementation.
        decimal staticCallTotal = OrderExtensions.Total(orders[0]);
        Console.WriteLine($"Static call total: {staticCallTotal}");

        Console.WriteLine($"Orders empty: {orders.IsEmpty()}");
    }
}

internal static class OrderExtensions
{
    public static decimal Total(this Order order)
    {
        ArgumentNullException.ThrowIfNull(order);

        decimal total = 0m;
        foreach (OrderLine line in order.Lines)
        {
            total += line.LineTotal;
        }

        return total;
    }

    public static List<Order> WithMinimumTotal(
        this IReadOnlyList<Order> source,
        decimal minimumTotal)
    {
        ArgumentNullException.ThrowIfNull(source);

        if (minimumTotal < 0m)
        {
            throw new ArgumentOutOfRangeException(nameof(minimumTotal));
        }

        var result = new List<Order>();
        foreach (Order order in source)
        {
            if (order.Total() >= minimumTotal)
            {
                result.Add(order);
            }
        }

        return result;
    }

    public static string ToDisplayLine(this Order order)
    {
        ArgumentNullException.ThrowIfNull(order);
        return $"{order.Id} | {order.Lines.Count} line(s) | total {order.Total()}";
    }

    public static bool IsEmpty<T>(this IReadOnlyCollection<T> source)
    {
        ArgumentNullException.ThrowIfNull(source);
        return source.Count == 0;
    }
}

internal sealed class Order
{
    private readonly IReadOnlyList<OrderLine> _lines;

    public string Id { get; }
    public IReadOnlyList<OrderLine> Lines => _lines;

    public Order(string id, IReadOnlyList<OrderLine> lines)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentNullException.ThrowIfNull(lines);

        if (lines.Count == 0)
        {
            throw new ArgumentException("Order must have at least one line.", nameof(lines));
        }

        Id = id.Trim();

        // Defensive copy: caller không thể Add/Remove line qua list đầu vào.
        _lines = new List<OrderLine>(lines).AsReadOnly();
    }
}

internal sealed class OrderLine
{
    public string ProductName { get; }
    public int Quantity { get; }
    public decimal UnitPrice { get; }
    public decimal LineTotal => Quantity * UnitPrice;

    public OrderLine(string productName, int quantity, decimal unitPrice)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(productName);

        if (quantity <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(quantity));
        }

        if (unitPrice < 0m)
        {
            throw new ArgumentOutOfRangeException(nameof(unitPrice));
        }

        ProductName = productName.Trim();
        Quantity = quantity;
        UnitPrice = unitPrice;
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
Selected count: 1
ORD-1001 | 2 line(s) | total 700000
Static call total: 700000
Orders empty: False
```

## 4. Giải thích cơ chế

### 4.1 Ba điều kiện cú pháp

Extension method truyền thống cần:

1. nằm trong một non-generic static class;
2. bản thân method là static;
3. parameter đầu có modifier `this` và xác định receiver type.

```csharp
internal static class OrderExtensions
{
    public static decimal Total(this Order order) { ... }
}
```

Modifier `this` ở đây không biến method thành instance member thật. Nó chỉ cho compiler cho phép cú pháp `order.Total()` khi extension nằm trong scope.

### 4.2 Compiler hạ lời gọi thành static call

Hai câu tương đương về semantics:

```csharp
decimal a = order.Total();
decimal b = OrderExtensions.Total(order);
```

Receiver `order` được truyền làm argument đầu theo pass-by-value. Vì `Order` là reference type, value được copy là reference tới cùng object; extension không clone order.

Việc chọn extension xảy ra ở compile time dựa trên namespace đang import, compile-time type của receiver và overload resolution. Đây không phải virtual dispatch theo runtime type.

### 4.3 Extension trên interface mở rộng nhiều implementation

`WithMinimumTotal` nhận:

```csharp
this IReadOnlyList<Order> source
```

nên mọi concrete type implement interface đó có thể dùng extension khi namespace phù hợp. Method chỉ yêu cầu contract đọc theo index/count/enumeration, không yêu cầu caller phải là `List<Order>`.

Chọn receiver abstraction nhỏ nhất thật sự cần giúp extension tái sử dụng được, nhưng đừng chọn `IEnumerable<T>` nếu thuật toán cần `Count`/index và bạn chưa quy định chi phí enumeration. Signature phải nói đúng operation.

### 4.4 Generic extension method

```csharp
public static bool IsEmpty<T>(this IReadOnlyCollection<T> source)
```

`T` được suy luận từ receiver. Với `List<Order>`, compiler suy ra `T` là `Order`, caller chỉ viết `orders.IsEmpty()`. Đây là generic method bình thường cộng thêm receiver syntax; mọi quy tắc type parameter/constraint vẫn như bài generics.

### 4.5 Instance member thắng extension method

Nếu `Order` tự khai báo instance method `Total()` có thể gọi được, compiler ưu tiên instance member. Extension không override, hide theo runtime polymorphism hay “chèn” member vào metadata của `Order`.

Điều này giúp thư viện thêm instance member mới nhưng cũng có thể làm behavior source code đổi sau upgrade nếu trước đó caller đang chọn extension cùng tên. Vì vậy chọn tên extension cụ thể và tránh cạnh tranh với API tự nhiên của type.

### 4.6 Mô hình bộ nhớ và allocation

Lời gọi `orders.WithMinimumTotal(...)` không tạo object wrapper chỉ vì dấu chấm:

```text
Main local                              Managed heap
+----------------------+                +--------------------------+
| orders ref -----------+-------------->| List<Order> H1           |
| selected ref ---------+------+        | [ref O1, ref O2]         |
+----------------------+      |        +--------------------------+
                              |
                              v
                       +--------------------------+
                       | result List<Order> H2    |
                       | [ref O1]                 |
                       +--------------------------+
```

Compiler truyền reference H1 vào static method. Tuy nhiên, **thân** `WithMinimumTotal` chạy `new List<Order>()`, nên tạo H2. H2 copy reference O1 vào entry; nó không clone `Order` O1. `Total()` chỉ tính `decimal` local và không tạo wrapper order.

Trong constructor `Order`, `new List<OrderLine>(lines)` và `AsReadOnly()` tạo storage/wrapper riêng để caller không đổi cấu trúc line gốc. Đây là allocation của thiết kế ownership, không phải đặc tính bắt buộc của extension method.

### 4.7 Null receiver vẫn có thể vào extension

Vì extension là static call, runtime không tự dereference receiver trước khi vào method. Code cũ, reflection hoặc boundary runtime khác vẫn có thể truyền `null`. Guard:

```csharp
ArgumentNullException.ThrowIfNull(order);
```

đưa lỗi về đúng boundary. Kiểm tra ở compile time được học trong bài kế tiếp sẽ giúp phát hiện sớm, nhưng không thay runtime validation của public API.

## 5. Kiến thức nền

### Namespace quyết định khả năng khám phá

Extension method chỉ tham gia lookup khi namespace chứa static class được import (hoặc code ở cùng namespace). Đặt extension gần domain/API liên quan và tên class theo convention `XxxExtensions`. Một namespace global chứa hàng trăm extension dễ gây collision và IntelliSense nhiễu.

### Extension không truy cập private member

Extension nằm ngoài type nên chỉ dùng member mà static class có quyền truy cập. Nó không phá encapsulation. Nếu operation cần private invariant/state, đó thường là behavior nên nằm trong type hoặc một collaborator được type công khai contract phù hợp.

### Extension thuần hay có side effect

Extension có thể mutate receiver nếu receiver công khai API mutable, nhưng cú pháp dấu chấm không cảnh báo side effect. Ưu tiên tên động từ rõ như `AddAuditEntry`; tránh tên nghe như query nhưng lại sửa state.

### Không phải mọi helper đều là extension

Operation không có receiver tự nhiên, tạo object mới từ nhiều input ngang hàng hoặc là workflow service/dependency thường rõ hơn dưới factory/service thông thường. Dùng extension khi nó thực sự đọc như một operation trên receiver contract.

## 6. Lỗi thường gặp

### Nghĩ extension sửa được source type

Metadata của `Order` không có member mới. Assembly khác không import namespace sẽ không thấy cú pháp extension; reflection trên `Order` cũng không liệt kê `Total` như instance method.

### Trông chờ runtime polymorphism

Extension được bind theo compile-time type. Hai extension cùng tên cho base/derived không dispatch như `virtual/override`. Dùng instance virtual method hoặc interface nếu behavior phải thay theo runtime type.

### Receiver quá cụ thể

Nhận `List<T>` khi chỉ cần `Count` làm giảm reuse. Chọn `IReadOnlyCollection<T>` nếu đó đúng contract; không ép abstraction nhỏ hơn khả năng thuật toán cần.

### Không guard receiver/reference input

Compiler warning không bảo vệ mọi caller runtime. Public extension nên fail fast bằng guard nếu `null` không hợp lệ.

### Extension method làm quá nhiều I/O

`order.SaveAndEmailAndLog()` giấu nhiều dependency/side effect sau cú pháp vô hại. Workflow lớn nên ở service có dependency explicit.

### Tạo collision tên phổ biến

Các tên như `Get`, `Map`, `Convert` trên type quá rộng dễ mơ hồ với namespace khác. Thu hẹp receiver/namespace và đặt tên theo domain.

## 7. Bài tập

### Bài 1 — Chuẩn hóa SKU

Viết `NormalizeSku(this string value)` trim, upper-case invariant và từ chối input rỗng.

**Gợi ý:** guard receiver trước; giải thích vì sao string immutable khiến method trả string mới.

### Bài 2 — Tổng tồn kho generic

Tạo interface `IStockItem` có `Stock`, rồi extension tính tổng cho `IReadOnlyList<T>` với constraint phù hợp.

**Gợi ý:** `where T : IStockItem`; dùng `checked` nếu policy yêu cầu phát hiện overflow.

### Bài 3 — Chứng minh static call

Gọi cùng extension bằng cú pháp dấu chấm và bằng tên static class, so sánh output và vẽ argument reference.

**Gợi ý:** không vẽ thêm wrapper object cho cú pháp dấu chấm.

### Bài 4 — Instance precedence

Tạo class có instance method trùng tên extension, gọi qua biến class rồi đổi compile-time type sang interface phù hợp để quan sát lookup.

**Gợi ý:** ghi candidate method ở compile time; đừng giải thích bằng runtime override.

### Bài 5 — Review API extension

Phân loại các candidate: `customer.FullName()`, `order.SaveToDatabase()`, `numbers.Median()`, `Payment.Create(card,amount)`. Chọn extension/class/service/factory và giải thích dependency.

**Gợi ý:** operation thuần theo receiver phù hợp hơn workflow I/O có dependency.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi khai báo đúng static class/static method/`this` parameter.
- [ ] Tôi hạ được `receiver.Method()` thành static call tương đương.
- [ ] Tôi biết extension được bind compile-time, không virtual dispatch.
- [ ] Tôi viết được generic extension trên interface phù hợp.
- [ ] Tôi hiểu instance member có ưu tiên hơn extension.
- [ ] Tôi vẽ đúng allocation do thân method, không tạo wrapper tưởng tượng.
- [ ] Tôi tổ chức namespace và side effect của extension có chủ đích.

Điều hướng:

- Bài tiên quyết: [Lambda, closure và bộ nhớ](./04-lambda-closure-va-bo-nho.md)
- Ôn static/instance member: [Class, object và constructor](../04-csharp-co-ban/07-class-object-constructor.md)
- Bài tiếp theo: [Nullable reference type](./06-nullable-reference-type.md)
