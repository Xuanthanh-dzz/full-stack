# Mô hình hóa đối tượng

## 1. Mục tiêu

Sau bài này, bạn có thể:

- đọc một mô tả nghiệp vụ và rút ra được type, dữ liệu và hành vi cần có;
- phân biệt **entity** (được nhận diện bằng identity) với **value object** (được nhận diện bằng giá trị);
- đặt invariant vào constructor để object không bao giờ tồn tại ở trạng thái sai;
- đặt hành vi cạnh dữ liệu thay vì viết class chỉ có property rồi xử lý bên ngoài;
- vẽ được object graph trên heap sau mỗi lần `new`;
- nhận ra ranh giới giữa model nghiệp vụ và phần nhập/xuất, lưu trữ;
- tránh mô hình hóa thừa: không tạo type cho mọi danh từ xuất hiện trong tài liệu.

## 2. Bài toán mở đầu

Một cửa hàng linh kiện mô tả nghiệp vụ đặt hàng như sau:

1. Đơn hàng thuộc về đúng một khách hàng và có mã đơn riêng.
2. Đơn gồm nhiều dòng hàng; mỗi dòng có mã SKU, số lượng và đơn giá.
3. Số lượng phải lớn hơn `0`; đơn giá không âm.
4. Mọi số tiền đều đi kèm đơn vị tiền tệ; không được cộng hai loại tiền khác nhau.
5. Chỉ đơn ở trạng thái nháp mới thêm được dòng hàng.
6. Đơn rỗng không được đặt.

Cách viết đầu tiên mà nhiều người chọn là giữ tất cả trong `Main`:

```csharp
string orderId = "ORD-001";
string customerId = "CUS-001";
var skus = new List<string>();
var quantities = new List<int>();
var prices = new List<decimal>();
bool placed = false;
```

Code này chạy được, nhưng mọi quy tắc ở trên đều nằm ngoài dữ liệu. Bất kỳ chỗ nào cũng có thể `quantities.Add(0)`, hoặc thêm dòng vào đơn đã đặt, hoặc cộng `decimal` của hai loại tiền tệ. Ba `List` phải luôn cùng độ dài, và không ai bảo đảm điều đó. Khi có thêm quy tắc thứ bảy, người viết phải tìm lại toàn bộ chỗ đụng tới ba `List`.

Mô hình hóa đối tượng là bước biến các quy tắc đó thành type: mỗi type giữ dữ liệu của mình, tự bảo vệ quy tắc của mình, và chỉ mở ra những hành vi hợp lệ.

## 3. Lời giải bằng code

Tạo project `.NET 9`:

```bash
mkdir OrderModelingDemo
cd OrderModelingDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `OrderModelingDemo.csproj` bằng:

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

Model dưới đây dùng lại đúng các công cụ đã học ở module 04–05: `class`, `record`, `enum`, property, constructor, `IReadOnlyList<T>` và exception. Điểm mới nằm ở cách chọn type nào cho khái niệm nào, chứ không nằm ở cú pháp.

Thay toàn bộ `Program.cs`:

```csharp
using System.Collections.Generic;

namespace OrderModelingDemo;

public enum OrderStatus
{
    Draft = 0,
    Placed = 1
}

// Value object: hai Money có cùng số tiền và cùng đơn vị thì được coi là như nhau.
public sealed record Money
{
    public decimal Amount { get; }

    public string Currency { get; }

    public Money(decimal amount, string currency)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(amount);
        ArgumentException.ThrowIfNullOrWhiteSpace(currency);

        Amount = amount;
        Currency = currency.Trim().ToUpperInvariant();
    }

    public static Money Vnd(decimal amount) => new(amount, "VND");

    public Money Add(Money other)
    {
        ArgumentNullException.ThrowIfNull(other);

        if (!string.Equals(Currency, other.Currency, StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                $"Cannot add {other.Currency} to {Currency}.");
        }

        return new Money(Amount + other.Amount, Currency);
    }

    public Money Multiply(int factor)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(factor);
        return new Money(Amount * factor, Currency);
    }

    public override string ToString() => $"{Amount:N0} {Currency}";
}

// Value object: một dòng hàng được mô tả trọn vẹn bởi SKU, số lượng và đơn giá.
public sealed record OrderLine
{
    public string Sku { get; }

    public int Quantity { get; }

    public Money UnitPrice { get; }

    public OrderLine(string sku, int quantity, Money unitPrice)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sku);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity);
        ArgumentNullException.ThrowIfNull(unitPrice);

        Sku = sku.Trim().ToUpperInvariant();
        Quantity = quantity;
        UnitPrice = unitPrice;
    }

    public Money Subtotal => UnitPrice.Multiply(Quantity);
}

// Entity: khách hàng vẫn là chính người đó dù đổi tên hiển thị.
public sealed class Customer
{
    private string _displayName;

    public Customer(string id, string displayName)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentException.ThrowIfNullOrWhiteSpace(displayName);

        Id = id.Trim().ToUpperInvariant();
        _displayName = displayName.Trim();
    }

    public string Id { get; }

    public string DisplayName => _displayName;

    public void Rename(string newDisplayName)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(newDisplayName);
        _displayName = newDisplayName.Trim();
    }
}

// Entity: đơn hàng có identity riêng và có vòng đời trạng thái.
public sealed class Order
{
    private readonly List<OrderLine> _lines = new();

    public Order(string id, Customer customer, string currency)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentNullException.ThrowIfNull(customer);
        ArgumentException.ThrowIfNullOrWhiteSpace(currency);

        Id = id.Trim().ToUpperInvariant();
        CustomerId = customer.Id;
        Currency = currency.Trim().ToUpperInvariant();
    }

    public string Id { get; }

    public string CustomerId { get; }

    public string Currency { get; }

    public OrderStatus Status { get; private set; } = OrderStatus.Draft;

    // Caller đọc được danh sách nhưng không thêm/bớt sau lưng Order.
    public IReadOnlyList<OrderLine> Lines => _lines;

    public Money Total
    {
        get
        {
            Money total = new(0m, Currency);
            foreach (OrderLine line in _lines)
            {
                total = total.Add(line.Subtotal);
            }

            return total;
        }
    }

    public void AddLine(OrderLine line)
    {
        ArgumentNullException.ThrowIfNull(line);

        if (Status != OrderStatus.Draft)
        {
            throw new InvalidOperationException(
                $"Order {Id} is {Status} and cannot receive new lines.");
        }

        if (!string.Equals(line.UnitPrice.Currency, Currency, StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                $"Order {Id} uses {Currency}; line uses {line.UnitPrice.Currency}.");
        }

        _lines.Add(line);
    }

    public void Place()
    {
        if (_lines.Count == 0)
        {
            throw new InvalidOperationException($"Order {Id} has no line to place.");
        }

        Status = OrderStatus.Placed;
    }
}

internal static class Program
{
    private static void Main()
    {
        var customer = new Customer("cus-001", "An Nguyen");
        var order = new Order("ord-001", customer, "VND");

        order.AddLine(new OrderLine("keyboard", 2, Money.Vnd(750_000m)));
        order.AddLine(new OrderLine("mouse", 1, Money.Vnd(350_000m)));
        order.Place();

        Console.WriteLine($"Order {order.Id} for {customer.DisplayName}: {order.Status}");
        Console.WriteLine($"Lines: {order.Lines.Count}, total: {order.Total}");

        // Value object: bằng nhau theo giá trị, không theo object.
        Money first = Money.Vnd(750_000m);
        Money second = Money.Vnd(750_000m);
        Console.WriteLine($"Equal money values: {first == second}");
        Console.WriteLine($"Same money object: {ReferenceEquals(first, second)}");

        // Entity: đổi tên hiển thị nhưng vẫn là cùng một khách hàng.
        customer.Rename("An Nguyen (VIP)");
        Console.WriteLine($"Customer {customer.Id} is now {customer.DisplayName}");

        Report(() => order.AddLine(new OrderLine("cable", 1, Money.Vnd(50_000m))));
        Report(() => new OrderLine("monitor", 0, Money.Vnd(3_000_000m)));
        Report(() => Money.Vnd(10_000m).Add(new Money(5m, "usd")));
    }

    private static void Report(Action action)
    {
        try
        {
            action();
            Console.WriteLine("Rejected: no");
        }
        catch (Exception ex)
        {
            Console.WriteLine($"Rejected by {ex.GetType().Name}: {ex.Message}");
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
Order ORD-001 for An Nguyen: Placed
Lines: 2, total: 1,850,000 VND
Equal money values: True
Same money object: False
Customer CUS-001 is now An Nguyen (VIP)
Rejected by InvalidOperationException: Order ORD-001 is Placed and cannot receive new lines.
Rejected by ArgumentOutOfRangeException: quantity ('0') must be a non-negative and non-zero value. (Parameter 'quantity')
Actual value was 0.
Rejected by InvalidOperationException: Cannot add USD to VND.
```

Dấu phân cách hàng nghìn phụ thuộc locale. Project được kiểm tra bằng .NET SDK `9.0.119`, target `net9.0`, không dùng package ngoài.

## 4. Giải thích cơ chế

### Quy tắc nghiệp vụ trở thành invariant của type

Mỗi quy tắc trong phần 2 giờ có một chỗ duy nhất để sống:

| Quy tắc | Nơi được bảo vệ |
|---|---|
| Số lượng `> 0`, đơn giá `>= 0` | constructor của `OrderLine` và `Money` |
| Tiền luôn có đơn vị | `Money` giữ cả `Amount` và `Currency` |
| Không cộng khác đơn vị | `Money.Add` |
| Chỉ đơn nháp mới thêm dòng | `Order.AddLine` |
| Đơn rỗng không được đặt | `Order.Place` |

Kết quả là **không có đường nào tạo ra object sai**. Muốn có `OrderLine`, bạn phải đi qua constructor; constructor ném exception trước khi object kịp được dùng. Đây là điểm khác biệt lớn so với ba `List` song song, nơi quy tắc chỉ tồn tại trong trí nhớ của người viết.

### Entity và value object khác nhau ở câu hỏi “cái gì làm nên danh tính”

- `Money` và `OrderLine` là **value object**: hỏi “750.000 VND này có phải cùng một tờ tiền với 750.000 VND kia không” là câu hỏi vô nghĩa. Hai giá trị bằng nhau thì thay thế được cho nhau, nên chúng bất biến và so sánh theo giá trị. `record` sinh sẵn value equality nên rất hợp vai này.
- `Customer` và `Order` là **entity**: khách hàng đổi tên vẫn là cùng người, đơn hàng thêm dòng vẫn là cùng đơn. Danh tính nằm ở `Id`, không nằm ở tập giá trị hiện tại. Vì vậy chúng là `class` thường, có state thay đổi theo thời gian, và so sánh phải theo `Id`.

Trong output, `first == second` trả `True` dù là hai object khác nhau trên heap, còn `customer` sau `Rename` vẫn là `CUS-001`.

### Hành vi nằm cạnh dữ liệu

`Order.Total` không được tính ở `Main`. Nếu để `Main` tính, mỗi nơi cần tổng tiền lại phải nhớ công thức và nhớ cả quy tắc “cùng đơn vị tiền”. Đặt `Total` trong `Order` thì công thức chỉ có một bản.

Tương tự, `AddLine` không phải là setter của `_lines`. Nó là **một thao tác nghiệp vụ**: kiểm tra trạng thái, kiểm tra đơn vị tiền, rồi mới thêm. Property `Lines` trả `IReadOnlyList<OrderLine>` nên caller đọc được nhưng không thể `Add` để đi vòng qua các kiểm tra đó.

### Object graph sau khi dựng đơn

Sau hai lời gọi `AddLine`, bộ nhớ có dạng:

```text
STACK (Main)                     HEAP
customer ──────────────────────> Customer #1
                                 ├── Id = "CUS-001"
                                 └── _displayName ──> "An Nguyen"
order ─────────────────────────> Order #1
                                 ├── Id = "ORD-001"
                                 ├── CustomerId = "CUS-001"  (chuỗi, không phải reference tới Customer)
                                 ├── Status = Placed
                                 └── _lines ──> List<OrderLine> #1
                                                 ├── [0] ──> OrderLine #1
                                                 │            ├── Sku = "KEYBOARD"
                                                 │            ├── Quantity = 2
                                                 │            └── UnitPrice ──> Money #1 (750000, VND)
                                                 └── [1] ──> OrderLine #2
                                                              ├── Sku = "MOUSE"
                                                              ├── Quantity = 1
                                                              └── UnitPrice ──> Money #2 (350000, VND)
first  ────────────────────────> Money #3 (750000, VND)
second ────────────────────────> Money #4 (750000, VND)
```

Mỗi `new` tạo một object riêng trên heap. `Money #1` và `Money #3` có cùng giá trị nhưng là hai vùng nhớ khác nhau, nên `ReferenceEquals` trả `False` trong khi `==` của record trả `True`.

`Order.Total` gọi `Money.Add` nhiều lần; mỗi lần lại tạo một `Money` mới. Với đơn hàng cỡ này, chi phí đó không đáng kể và đổi lại là tính bất biến. Khi tổng được tính trong vòng lặp nóng, hãy đo trước khi đổi thiết kế — cách đo đã học ở [module 05, bài 18](../05-csharp-nang-cao/18-do-luong-va-toi-uu-hieu-nang.md).

### Đào sâu (có thể quay lại sau)

#### Vì sao `Order` giữ `CustomerId` mà không giữ `Customer`

Sơ đồ trên cho thấy `Order` chỉ giữ chuỗi `"CUS-001"`. Nếu `Order` giữ thẳng reference tới `Customer`, mọi chỗ tải một đơn hàng đều kéo theo cả object khách hàng, và hai object bắt đầu có thể sửa lẫn nhau. Giữ ID làm ranh giới giữa hai nhóm object rõ ràng hơn: `Order` chịu trách nhiệm về dòng hàng và trạng thái, `Customer` chịu trách nhiệm về thông tin khách.

Đây mới là mức trực giác. Cách gọi tên chính thức (aggregate, aggregate root) và quy tắc đầy đủ nằm ở [module 17](../PROGRESS.md#17-kien-truc-phan-mem); bài này chỉ cần bạn thấy được lợi ích của ranh giới.

#### Value object và cấp phát

`Money` là `record class` nên mỗi giá trị là một object trên heap. Có thể viết `readonly record struct Money` để tránh cấp phát, nhưng struct luôn có `default(Money)` với `Currency` là `null` — tức là một giá trị đi vòng qua constructor và phá invariant. Muốn dùng struct thì phải xử lý trường hợp `default` một cách tường minh. Ở bài này, `record class` cho invariant chắc chắn hơn và đủ nhanh.

#### Model và I/O là hai việc khác nhau

`Order` không đọc `Console`, không ghi file, không biết JSON. Nhờ vậy nó có thể được dùng lại ở console app, web API hay batch job mà không sửa dòng nào. Việc đọc/ghi được đặt ở lớp ngoài; các bài về SRP và dependency inversion trong module này sẽ nói kỹ ranh giới đó.

## 5. Kiến thức nền

### Từ mô tả nghiệp vụ tới type

Một quy trình rút gọn nhưng đủ dùng:

1. **Gạch chân danh từ** trong mô tả: đơn hàng, khách hàng, dòng hàng, số tiền, trạng thái.
2. **Loại bớt**: danh từ nào chỉ là thuộc tính của danh từ khác thì không cần type riêng. “Số lượng” là thuộc tính của dòng hàng, không phải một type.
3. **Gạch chân động từ**: thêm dòng, đặt đơn, tính tổng, đổi tên. Mỗi động từ là ứng viên của một method, và method đó thuộc về type sở hữu dữ liệu mà nó cần.
4. **Hỏi về danh tính** cho từng type: giá trị bằng nhau là đủ, hay cần một ID? Câu trả lời quyết định entity hay value object.
5. **Hỏi về quy tắc**: quy tắc này luôn đúng ở đâu? Đưa nó vào constructor nếu luôn đúng, vào method nếu chỉ đúng khi chuyển trạng thái.

### Bảng chọn nhanh entity hay value object

| Câu hỏi | Value object | Entity |
|---|---|---|
| Hai instance cùng dữ liệu có thay thế nhau được không? | có | không |
| Có cần theo dõi qua thời gian không? | không | có |
| State có đổi tại chỗ không? | không, tạo bản mới | có |
| So sánh bằng gì? | giá trị | ID |
| Type C# thường dùng | `record`, `readonly record struct` | `class` |

### Anemic model

Một model chỉ có property `get; set;` công khai, còn toàn bộ quy tắc nằm trong các class `...Service` bên ngoài, thường được gọi là **anemic domain model**. Nó không sai về cú pháp và vẫn xuất hiện nhiều trong thực tế, nhưng nó đẩy trách nhiệm bảo vệ dữ liệu ra khỏi nơi giữ dữ liệu: mỗi service phải tự nhớ kiểm tra lại, và chỉ cần một service quên là dữ liệu hỏng.

Mức tối thiểu nên giữ: dữ liệu không thể vào trạng thái sai qua constructor và các method công khai của chính type đó.

### Mô hình hóa vừa đủ

Không phải mọi khái niệm đều xứng đáng có một type. Nếu một giá trị chỉ đọc lên rồi in ra, `string` là đủ. Hãy tạo type mới khi có ít nhất một trong các dấu hiệu:

- nó mang quy tắc riêng (`Money` không âm, luôn có đơn vị);
- nó bị dùng sai type ở nhiều nơi (`string customerId` và `string orderId` dễ truyền nhầm nhau);
- nó đi thành cụm cố định (số tiền và đơn vị luôn đi cùng nhau).

## 6. Lỗi thường gặp

### Tạo type cho mọi danh từ

Tài liệu nghiệp vụ có “hệ thống”, “báo cáo”, “thông tin”, nhưng không phải cái nào cũng thành class. Kết quả của việc tạo tràn lan là hàng chục type mỏng, mỗi type chỉ chuyển dữ liệu sang type kế tiếp.

### Public setter cho mọi property

```csharp
public OrderStatus Status { get; set; } // ai cũng đặt được Placed
```

Với setter công khai, bất kỳ đâu cũng có thể đặt `Status = Placed` cho một đơn rỗng. Hãy để `private set` và mở ra một method mang tên nghiệp vụ (`Place`) có kiểm tra.

### Trả thẳng `List<T>` ra ngoài

```csharp
public List<OrderLine> Lines => _lines; // caller gọi Add được
```

Caller có thể `order.Lines.Add(...)` và bỏ qua mọi kiểm tra của `AddLine`. Trả `IReadOnlyList<T>` như trong sample, hoặc trả bản sao khi cần chắc chắn hơn.

### Value object có thể thay đổi

Nếu `Money` cho phép gán lại `Amount`, thì hai chỗ cùng dùng một object `Money` sẽ thấy nhau đổi giá. Value object phải bất biến; muốn giá trị khác thì tạo object mới.

### Nhầm “bằng nhau” của entity với so sánh reference

`class` mặc định so sánh theo reference, nên hai object `Customer` cùng `Id` sẽ không bằng nhau. Khi cần so sánh entity, hãy so sánh `Id` một cách tường minh, hoặc override `Equals`/`GetHashCode` theo `Id` và ghi rõ lý do.

### Dùng `record` cho entity chỉ vì gõ ngắn hơn

`record` sinh equality theo tất cả property. Với entity, hai đơn hàng khác `Id` mà trùng mọi dữ liệu khác sẽ bị coi là bằng nhau khi bạn thêm một property, hoặc ngược lại — equality thay đổi mỗi lần model thêm field. Đó là nguồn bug âm thầm khi entity nằm trong `HashSet` hay `Dictionary`.

### Cho model biết về nơi lưu trữ

Nếu `Order` có method `SaveToFile()`, model bị dính chặt vào file. Khi đổi sang database, phải sửa chính type nghiệp vụ. Việc lưu trữ nằm ở lớp khác; bài về dependency inversion sẽ chỉ cách nối hai phần mà không đảo ngược sự phụ thuộc.

### Kiểm tra invariant ở tầng nhập liệu rồi bỏ luôn trong model

Kiểm tra ở tầng nhập liệu là để báo lỗi thân thiện cho người dùng; kiểm tra trong model là để giữ đúng bất biến cho mọi caller, kể cả import dữ liệu hay job nền. Hai chỗ này phục vụ hai mục đích khác nhau và không thay thế nhau.

## 7. Bài tập

### Bài 1 — Value object `Quantity`

Viết `Quantity` bọc một `int` dương, có method `Add(Quantity)` và `ToString()`. Thay `int Quantity` trong `OrderLine` bằng type mới.

**Gợi ý:** dùng `record` để có sẵn value equality; đặt toàn bộ kiểm tra vào constructor và thử tạo `new Quantity(0)` để chắc chắn nó bị chặn.

### Bài 2 — Nhận diện entity hay value object

Với các khái niệm: `Address`, `Invoice`, `EmailAddress`, `ShippingBox`, `Employee` — phân loại từng cái và viết một câu lý do dựa trên câu hỏi danh tính.

**Gợi ý:** hỏi “nếu mọi thuộc tính giống nhau, có cần phân biệt hai cái không?”; nếu công ty cần theo dõi chính chiếc hộp đó, câu trả lời sẽ đổi.

### Bài 3 — Trạng thái đơn hàng đầy đủ hơn

Thêm `Cancelled` vào `OrderStatus` và method `Cancel()`. Xác định các chuyển trạng thái hợp lệ rồi chặn phần còn lại.

**Gợi ý:** vẽ bảng `từ trạng thái → thao tác → tới trạng thái` trước khi viết code; đơn đã hủy thì `Place` phải ném exception.

### Bài 4 — Chống rò rỉ dữ liệu bên trong

Viết một chương trình cố tình phá `Order`: lấy `Lines`, ép kiểu về `List<OrderLine>` rồi `Add`. Sau đó sửa `Order` để cách phá đó không còn hiệu lực.

**Gợi ý:** so sánh hai hướng — trả bản sao, hoặc bọc bằng `AsReadOnly()`; ghi lại chi phí cấp phát của mỗi hướng.

### Bài 5 — Mô hình hóa từ mô tả mới

Mô tả: “Một phiếu bảo hành thuộc về một sản phẩm đã bán, có ngày bắt đầu và số tháng hiệu lực; chỉ phiếu còn hiệu lực mới tạo được yêu cầu sửa chữa; mỗi yêu cầu có mã riêng và mô tả lỗi.” Hãy rút ra type, quyết định entity hay value object, và viết constructor kèm invariant.

**Gợi ý:** “còn hiệu lực” phụ thuộc thời điểm hiện tại — hãy nhận `DateOnly today` làm tham số thay vì đọc `DateTime.Now` bên trong model, để còn kiểm thử được.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi rút được type và hành vi từ một mô tả nghiệp vụ, không chỉ từ danh từ.
- [ ] Tôi phân biệt được entity và value object bằng câu hỏi danh tính.
- [ ] Tôi đặt invariant vào constructor nên object không tồn tại ở trạng thái sai.
- [ ] Tôi đặt hành vi vào type sở hữu dữ liệu thay vì rải ra ngoài.
- [ ] Tôi không để collection bên trong bị sửa từ ngoài.
- [ ] Tôi vẽ được object graph trên heap sau mỗi lần `new`.
- [ ] Tôi build/run được sample trên `net9.0` và giải thích được từng dòng output.

Điều hướng:

- Bài prerequisite: [Module 05, bài 19 — Dự án xử lý dữ liệu bất đồng bộ](../05-csharp-nang-cao/19-du-an-xu-ly-du-lieu-bat-dong-bo.md)
- Ôn lại nền tảng: [Class, object và constructor](../04-csharp-co-ban/07-class-object-constructor.md), [Record, `init`, `required` và tính bất biến](../05-csharp-nang-cao/07-record-init-required-va-immutability.md)
- Bài tiếp theo: [Encapsulation, abstraction, inheritance và polymorphism](./02-encapsulation-abstraction-inheritance-polymorphism.md)
