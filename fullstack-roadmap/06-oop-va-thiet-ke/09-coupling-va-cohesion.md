# Coupling và cohesion

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, invariant hoặc adapter; CI failure

## TL;DR

- Coupling là phụ thuộc giữa thành phần; cohesion là mức gắn kết bên trong.
- Dùng request nhỏ và cấu hình tường minh để giảm phụ thuộc không cần thiết.
- Không đếm dấu chấm hay số interface làm thước đo tuyệt đối.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- định nghĩa coupling và cohesion bằng câu hỏi quan sát được, không bằng cảm tính;
- xếp hạng các mức coupling từ chấp nhận được tới nguy hiểm và nhận ra chúng trong code;
- chỉ ra vì sao static mutable state là dạng coupling khó gỡ nhất;
- thay control coupling (tham số `bool` điều khiển hành vi) bằng thiết kế rõ nghĩa;
- rút ngắn chuỗi truy cập kiểu `a.B.C.D` bằng cách hỏi đúng object;
- đánh giá cohesion của một class bằng việc xem method nào dùng field nào;
- cân bằng: giảm coupling tới mức hợp lý mà không tạo ra hàng chục type rời rạc.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Công thức phí chỉ cần số tiền, thành phố và tốc độ. Bắt nó lục cả hồ sơ khách để lấy ba giá trị khiến đổi địa chỉ khách cũng kéo công thức phí vào việc sửa.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| coupling | mức một phần phụ thuộc phần khác | calculator biết cấu trúc Order |
| cohesion | các phần cùng phục vụ một mục đích | Quote/Surcharge |
| common state | state chung qua đường ngầm | ShippingConfig static |
| request value | dữ liệu tường minh cho một lần gọi | ShippingQuoteRequest |

### Ví dụ nhỏ — tính tay trước

Đơn550000: threshold500000 →ship0; đổi static threshold1triệu →20000 dù tham số y hệt. Hai calculator dùng hai record rates riêng giữ kết quả0 và20000 độc lập.

Cửa hàng cần tính phí vận chuyển. Class hiện tại chạy đúng trên máy người viết:

```csharp
public static class ShippingConfig
{
    public static decimal FreeThreshold = 500_000m;
}

public sealed class LegacyShippingCalculator
{
    public decimal Calculate(LegacyOrder order, bool express)
    {
        decimal subtotal = 0m;
        foreach (LegacyOrderLine line in order.Lines)      // tự cộng dồn thay vì hỏi order
        {
            subtotal += line.UnitPrice * line.Quantity;
        }

        string city = order.Customer.Address.City;         // chuỗi ba dấu chấm
        // ...
    }
}
```

Ba tuần sau, hai lỗi được báo cùng lúc:

1. Cùng một đơn hàng, cùng một tham số, nhưng phí vận chuyển khác nhau giữa hai lần chạy. Nguyên nhân: một job khác đã gán `ShippingConfig.FreeThreshold` trong lúc chạy.
2. Người sửa muốn thêm chế độ “giao trong ngày” nhưng tham số điều khiển là `bool express`. Thêm `bool sameDay` nữa thì có bốn tổ hợp, trong đó hai tổ hợp vô nghĩa.

Ngoài ra, muốn viết một kiểm thử cho công thức phí, bạn phải dựng đủ `LegacyOrder`, `LegacyCustomer`, `LegacyAddress` và một danh sách dòng hàng — dù công thức chỉ cần hai con số và một tên thành phố.

Ba triệu chứng trên là ba dạng coupling khác nhau. Bài này gọi tên chúng và chỉ cách gỡ.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project `.NET 9`:

```bash
mkdir CouplingCohesionDemo
cd CouplingCohesionDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `CouplingCohesionDemo.csproj` bằng:

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

Sample chạy bản cũ để tái hiện lỗi, rồi chạy bản đã gỡ coupling.

Thay toàn bộ `Program.cs`:

```csharp
using System.Collections.Generic;

namespace CouplingCohesionDemo;

// ============ BẢN CŨ: coupling cao ============

public static class ShippingConfig
{
    // Common coupling: bất kỳ ai cũng đọc/ghi được, không ai biết ai đã đổi.
    public static decimal FreeThreshold = 500_000m;
}

public sealed class LegacyAddress
{
    public LegacyAddress(string city) => City = city;

    public string City { get; }
}

public sealed class LegacyCustomer
{
    public LegacyCustomer(string id, LegacyAddress address)
    {
        Id = id;
        Address = address;
    }

    public string Id { get; }

    public LegacyAddress Address { get; }
}

public sealed class LegacyOrderLine
{
    public LegacyOrderLine(string sku, int quantity, decimal unitPrice)
    {
        Sku = sku;
        Quantity = quantity;
        UnitPrice = unitPrice;
    }

    public string Sku { get; }

    public int Quantity { get; }

    public decimal UnitPrice { get; }
}

public sealed class LegacyOrder
{
    public LegacyOrder(string id, LegacyCustomer customer, List<LegacyOrderLine> lines)
    {
        Id = id;
        Customer = customer;
        Lines = lines;
    }

    public string Id { get; }

    public LegacyCustomer Customer { get; }

    public List<LegacyOrderLine> Lines { get; }
}

public sealed class LegacyShippingCalculator
{
    // Control coupling: caller phải biết bool nào bật hành vi nào.
    public decimal Calculate(LegacyOrder order, bool express)
    {
        decimal subtotal = 0m;
        foreach (LegacyOrderLine line in order.Lines)
        {
            subtotal += line.UnitPrice * line.Quantity;
        }

        // Phụ thuộc cấu trúc: đi xuyên qua ba object để lấy một chuỗi.
        string city = order.Customer.Address.City;
        decimal baseFee = string.Equals(city, "Ha Noi", StringComparison.OrdinalIgnoreCase)
            ? 20_000m
            : 35_000m;

        if (subtotal >= ShippingConfig.FreeThreshold)
        {
            baseFee = 0m;
        }

        return express ? baseFee + 25_000m : baseFee;
    }
}

// ============ BẢN ĐÃ GỠ: coupling thấp, cohesion cao ============

public enum ShippingSpeed
{
    Standard = 0,
    Express = 1,
    SameDay = 2
}

// Chỉ mang đúng dữ liệu mà phép tính cần: data coupling.
public sealed record ShippingQuoteRequest(decimal Subtotal, string City, ShippingSpeed Speed);

// Cấu hình được truyền vào, không nằm ở static.
public sealed record ShippingRates(
    decimal FreeThreshold,
    decimal LocalFee,
    decimal RemoteFee,
    decimal ExpressSurcharge,
    decimal SameDaySurcharge);

public sealed class ShippingCalculator
{
    private readonly ShippingRates _rates;
    private readonly string _localCity;

    public ShippingCalculator(ShippingRates rates, string localCity)
    {
        ArgumentNullException.ThrowIfNull(rates);
        ArgumentException.ThrowIfNullOrWhiteSpace(localCity);

        _rates = rates;
        _localCity = localCity;
    }

    public decimal Quote(ShippingQuoteRequest request)
    {
        ArgumentNullException.ThrowIfNull(request);

        if (request.Subtotal >= _rates.FreeThreshold)
        {
            return Surcharge(request.Speed);
        }

        bool isLocal = string.Equals(request.City, _localCity, StringComparison.OrdinalIgnoreCase);
        decimal baseFee = isLocal ? _rates.LocalFee : _rates.RemoteFee;
        return baseFee + Surcharge(request.Speed);
    }

    private decimal Surcharge(ShippingSpeed speed) => speed switch
    {
        ShippingSpeed.Standard => 0m,
        ShippingSpeed.Express => _rates.ExpressSurcharge,
        ShippingSpeed.SameDay => _rates.SameDaySurcharge,
        _ => throw new ArgumentOutOfRangeException(nameof(speed), speed, "Unknown speed.")
    };
}

public sealed record OrderLine(string Sku, int Quantity, decimal UnitPrice)
{
    public decimal LineTotal => Quantity * UnitPrice;
}

public sealed class Order
{
    private readonly List<OrderLine> _lines;

    public Order(string id, string shippingCity, IReadOnlyList<OrderLine> lines)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentException.ThrowIfNullOrWhiteSpace(shippingCity);
        ArgumentNullException.ThrowIfNull(lines);

        Id = id;
        ShippingCity = shippingCity;
        _lines = new List<OrderLine>(lines);
    }

    public string Id { get; }

    // Order tự trả lời câu hỏi về mình, caller không phải đi vào bên trong.
    public string ShippingCity { get; }

    public decimal Subtotal
    {
        get
        {
            decimal total = 0m;
            foreach (OrderLine line in _lines)
            {
                total += line.LineTotal;
            }

            return total;
        }
    }

    public ShippingQuoteRequest ToQuoteRequest(ShippingSpeed speed) =>
        new(Subtotal, ShippingCity, speed);
}

internal static class Program
{
    private static void Main()
    {
        var legacyOrder = new LegacyOrder(
            "ORD-001",
            new LegacyCustomer("CUS-001", new LegacyAddress("Ha Noi")),
            new List<LegacyOrderLine>
            {
                new("KEYBOARD", 1, 300_000m),
                new("MOUSE", 1, 250_000m)
            });

        var legacy = new LegacyShippingCalculator();
        Console.WriteLine("--- bản cũ ---");
        Console.WriteLine($"First run:  {legacy.Calculate(legacyOrder, express: false):N0}");

        // Một job khác trong hệ thống đổi cấu hình toàn cục.
        ShippingConfig.FreeThreshold = 1_000_000m;
        Console.WriteLine($"Second run: {legacy.Calculate(legacyOrder, express: false):N0}");
        Console.WriteLine("Cùng input, khác kết quả.");

        Console.WriteLine("--- bản đã gỡ ---");
        var rates = new ShippingRates(
            FreeThreshold: 500_000m,
            LocalFee: 20_000m,
            RemoteFee: 35_000m,
            ExpressSurcharge: 25_000m,
            SameDaySurcharge: 60_000m);

        var calculator = new ShippingCalculator(rates, localCity: "Ha Noi");
        var order = new Order("ORD-001", "Ha Noi", new[]
        {
            new OrderLine("KEYBOARD", 1, 300_000m),
            new OrderLine("MOUSE", 1, 250_000m)
        });

        Console.WriteLine($"Standard:   {calculator.Quote(order.ToQuoteRequest(ShippingSpeed.Standard)):N0}");
        Console.WriteLine($"Express:    {calculator.Quote(order.ToQuoteRequest(ShippingSpeed.Express)):N0}");
        Console.WriteLine($"Same day:   {calculator.Quote(order.ToQuoteRequest(ShippingSpeed.SameDay)):N0}");

        // Kiểm tra công thức mà không cần dựng Order, Customer hay Address.
        var smallRemote = new ShippingQuoteRequest(120_000m, "Da Nang", ShippingSpeed.Express);
        Console.WriteLine($"Remote fee: {calculator.Quote(smallRemote):N0}");

        // Cấu hình khác chỉ là một object khác; hai calculator sống song song.
        var strict = new ShippingCalculator(rates with { FreeThreshold = 1_000_000m }, "Ha Noi");
        Console.WriteLine($"Strict run: {strict.Quote(order.ToQuoteRequest(ShippingSpeed.Standard)):N0}");
        Console.WriteLine($"Normal run: {calculator.Quote(order.ToQuoteRequest(ShippingSpeed.Standard)):N0}");
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
--- bản cũ ---
First run:  0
Second run: 20,000
Cùng input, khác kết quả.
--- bản đã gỡ ---
Standard:   0
Express:    25,000
Same day:   60,000
Remote fee: 60,000
Strict run: 20,000
Normal run: 0
```

Project được kiểm tra bằng .NET SDK `9.0.121`, target `net9.0`, không dùng package ngoài.

### Walkthrough — execution / state / cost

1. Legacy đọc static tại thời điểm gọi, nên input thực gồm cả hidden config.
2. Bản mới nhận rates ở constructor và quote request ở mỗi call.
3. Order copy list input; Subtotal duyệt dòng trước khi tạo request.
4. Quote chỉ làm vài phép so sánh O(1); ToQuoteRequest mất O(n) vì tính Subtotal. Config record dùng scalar/string bất biến, không bị sửa tại chỗ bởi with.

### Mini-check

Quote là O(1) có nghĩa cả order.ToQuoteRequest rồi Quote cũng O(1) không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Bốn dạng coupling trong bản cũ

| Dạng | Xuất hiện ở đâu | Vì sao nguy hiểm |
|---|---|---|
| Common coupling | `ShippingConfig.FreeThreshold` | mọi module đọc/ghi được; kết quả phụ thuộc thứ tự chạy |
| Control coupling | tham số `bool express` | caller phải biết cờ nào bật nhánh nào; thêm chế độ là nhân đôi tổ hợp |
| Structure coupling | `order.Customer.Address.City` | đổi cấu trúc `Address` làm hỏng calculator dù nó không liên quan |
| Stamp coupling | truyền cả `LegacyOrder` để lấy hai con số | test phải dựng cả đồ thị object |

Output chứng minh dạng đầu tiên bằng số liệu: cùng `legacyOrder`, cùng `express: false`, hai lần chạy cho `0` và `20.000`. Không có tham số nào thay đổi — thứ thay đổi nằm ngoài chữ ký của method.

### Bản đã gỡ đổi những gì

```text
TRƯỚC
LegacyShippingCalculator ──> LegacyOrder ──> LegacyCustomer ──> LegacyAddress
                         ──> ShippingConfig (static, ai cũng ghi được)

SAU
Order ──> ShippingQuoteRequest ──> ShippingCalculator ──> ShippingRates (truyền vào)
      (chỉ ba giá trị: subtotal, city, speed)
```

`ShippingCalculator` bây giờ chỉ phụ thuộc vào một record ba trường và một record cấu hình. Nó không biết `Order` tồn tại. Vì vậy dòng cuối cùng của sample chạy được: một `ShippingQuoteRequest` dựng tay là đủ để kiểm tra công thức.

`ShippingRates` được truyền qua constructor nên hai calculator có hai cấu hình khác nhau cùng sống được — điều bất khả thi với biến static. Hai dòng cuối output chứng minh: cùng một đơn hàng, `strict` trả `20.000` còn `calculator` trả `0`, và không cái nào ảnh hưởng cái kia.

### `bool` điều khiển hành vi và `enum`

Với `bool express`, tập hành vi là hai. Thêm `bool sameDay` sẽ thành bốn, trong đó `(express: true, sameDay: true)` vô nghĩa nhưng vẫn hợp lệ về kiểu. `ShippingSpeed` mô tả đúng ba lựa chọn loại trừ nhau và `switch` liệt kê từng lựa chọn; nhánh `_` từ chối giá trị enum chưa biết. Có `_` thì thêm enum mới không tự buộc compiler báo thiếu nhánh.

Lời gọi cũng đọc được ngay:

```csharp
calculator.Quote(order.ToQuoteRequest(ShippingSpeed.Express)); // rõ
legacy.Calculate(legacyOrder, true);                           // true nghĩa là gì?
```

### Cohesion đo bằng “method nào dùng field nào”

`ShippingCalculator` có hai field, và cả `Quote` lẫn `Surcharge` đều dùng `_rates`. Mọi thành phần phục vụ một mục đích: tính phí. Đó là cohesion cao — cụ thể là **functional cohesion**.

Ngược lại, một class kiểu này có cohesion thấp:

```csharp
public sealed class OrderHelper
{
    private readonly HttpClient _http;      // chỉ SendWebhook dùng
    private readonly decimal _taxRate;      // chỉ CalculateTax dùng
    private readonly string _dateFormat;    // chỉ FormatDate dùng
}
```

Ba field, ba method, không chia sẻ gì. Đây là **coincidental cohesion**: các thứ ở chung chỉ vì tiện. Cách sửa là tách theo nhóm field–method, đúng quy trình tách ở [bài 4](./04-single-responsibility.md).

### Đào sâu (có thể quay lại sau)

#### Thang bậc coupling

Từ tốt tới xấu:

1. **Data coupling** — truyền đúng dữ liệu cần, dạng đơn giản. Mục tiêu nên hướng tới.
2. **Stamp coupling** — truyền cả một cấu trúc lớn dù chỉ dùng vài trường. Chấp nhận được khi cấu trúc đó chính là khái niệm nghiệp vụ.
3. **Control coupling** — truyền cờ điều khiển nhánh.
4. **Common coupling** — dùng chung dữ liệu toàn cục.
5. **Content coupling** — chạm vào nội bộ của module khác.

Không có mục tiêu “coupling bằng không”: các thành phần phải nối với nhau thì hệ thống mới chạy. Mục tiêu là nối qua **hợp đồng hẹp và tường minh**.

#### Fan-in và fan-out

- **Fan-out** cao (một class dùng rất nhiều class khác) → khó test, dễ vỡ khi bất kỳ phụ thuộc nào đổi.
- **Fan-in** cao (rất nhiều class dùng nó) → thay đổi ở đây lan rộng; những type như vậy cần hợp đồng đặc biệt ổn định.

Một `Utils` với fan-in rất cao và cohesion rất thấp là kết hợp tệ nhất: ai cũng phụ thuộc vào một chỗ chẳng có chủ đề gì.

#### Law of Demeter

Quy tắc thực dụng: một method chỉ nên gọi method của chính object mình, của tham số nhận vào, của object mình tạo ra, và của field trực tiếp. Chuỗi `order.Customer.Address.City` vi phạm vì calculator phải biết ba tầng cấu trúc.

Cách sửa không phải là thêm property `CustomerCity` cho mọi thứ, mà là hỏi: “ai nên trả lời câu hỏi này?”. Trong sample, `Order` tự tạo `ShippingQuoteRequest` vì nó biết dữ liệu của mình.

#### Static không phải lúc nào cũng xấu

`static` cho hằng số và hàm thuần (`Math.Max`) không tạo coupling nguy hiểm vì không có state thay đổi. Vấn đề nằm ở **static mutable state**: nó là kênh liên lạc ngầm giữa các module và biến kết quả thành phụ thuộc vào thứ tự chạy — kể cả trong test chạy song song.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| global mutable config | ẩn trong mọi call | khó chạy hai cấu hình song song |
| explicit rates | config thuộc instance | thêm parameter nhưng dễ kiểm soát |
| strategy mỗi speed | behavior thay được | chưa cần khi ba lựa chọn đóng, switch đủ |

### Misconception check

**Đúng hay sai?** Thay bool bằng enum xóa mọi control coupling.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: vẫn chọn behavior, nhưng loại được tổ hợp cờ vô nghĩa.

</details>

**Đúng hay sai?** Hai dấu chấm luôn vi phạm thiết kế.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: xem dependency vào cấu trúc và ownership; fluent API khác truy cập nội bộ tùy tiện.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** coupling/cohesion qua ví dụ.

- **Working Developer — dùng khi làm việc:** state/config và cost.

- **Deep Dive — có thể quay lại sau:** change history để chọn boundary.

### Hai câu hỏi định nghĩa

- **Coupling:** nếu tôi đổi module A, có bao nhiêu module khác phải đổi theo?
- **Cohesion:** các thành phần trong module này có phục vụ cùng một mục đích không?

Thiết kế tốt hướng tới **coupling thấp giữa các module, cohesion cao trong mỗi module**. Hai chỉ số này đi cùng nhau: gom đúng thứ vào một chỗ (cohesion) thường tự làm giảm số dây nối ra ngoài (coupling).

### Thang bậc cohesion

| Mức | Nghĩa | Ví dụ |
|---|---|---|
| Functional | mọi thứ phục vụ một nhiệm vụ | `ShippingCalculator` |
| Sequential | đầu ra của bước này là đầu vào bước kia | parser rồi validator trong cùng pipeline |
| Communicational | cùng thao tác trên một tập dữ liệu | `InMemoryOrderStore` |
| Temporal | cùng chạy ở một thời điểm | mọi thứ trong `Startup` |
| Logical | cùng “loại” nhưng khác nhiệm vụ | `Utils.FormatDate` cạnh `Utils.SendMail` |
| Coincidental | không liên quan gì | `Helper` |

Ba mức trên cùng là mục tiêu thực tế; ba mức dưới là tín hiệu tách.

### Cách đo nhanh trên code có sẵn

1. Chọn một thay đổi nghiệp vụ có thật, ví dụ “thêm chế độ giao trong ngày”.
2. Đếm số file phải mở để thực hiện nó.
3. Với mỗi file, hỏi vì sao nó phải đổi.
4. Nếu một file phải đổi vì lý do không liên quan tới nó, đó là coupling sai chỗ.

Lịch sử Git giúp bước này: các file luôn xuất hiện cùng nhau trong một commit thường có coupling cao — nếu chúng thuộc các module khác nhau, đó là dấu hiệu cần xem lại ranh giới.

### Quan hệ với các nguyên tắc đã học

- Encapsulation giảm content coupling: không chạm được vào nội bộ thì không phụ thuộc được.
- ISP giảm coupling theo bề rộng hợp đồng.
- DIP đổi **chiều** coupling để phần ổn định không phụ thuộc phần dễ đổi.
- SRP là cách phát biểu khác của cohesion cao.

## 6. Lỗi thường gặp

### Dùng static để “tiện truyền dữ liệu”

Một biến static giải quyết vấn đề trong năm phút và tạo ra một lớp phụ thuộc ngầm cho nhiều năm. Nếu cần dùng chung cấu hình, hãy truyền nó qua constructor như `ShippingRates`.

### Thêm `bool` mỗi khi có yêu cầu mới

`Calculate(order, true, false, true)` là một lời gọi không ai đọc được. Dùng `enum` cho các lựa chọn loại trừ nhau, hoặc tách thành hai method có tên rõ ràng.

### Chuỗi dấu chấm dài

`order.Customer.Address.City.Trim().ToUpperInvariant()` khiến calculator phụ thuộc vào bốn quyết định thiết kế của người khác. Hãy để object gần dữ liệu nhất trả lời câu hỏi.

### Truyền cả object khi chỉ cần một con số

Nếu method chỉ dùng `Subtotal`, hãy nhận `decimal subtotal`. Ngoại lệ: khi tham số thật sự là một khái niệm nghiệp vụ và số trường sẽ tăng — lúc đó một record như `ShippingQuoteRequest` lại đúng hơn danh sách năm tham số rời.

### Gộp mọi hàm tiện ích vào một class

`Utils`, `Helpers`, `Common` bắt đầu với ba method và kết thúc với ba trăm. Hãy đặt mỗi hàm cạnh khái niệm mà nó phục vụ; nếu không tìm được chỗ, có lẽ khái niệm đó còn thiếu.

### Giảm coupling bằng cách thêm tầng gián tiếp vô nghĩa

Bọc mọi class bằng một interface không tự làm giảm coupling: nếu interface vẫn lộ đúng cấu trúc cũ, các module vẫn ràng vào nhau y hệt, chỉ thêm file để đọc.

### Nhầm “ít file” với “coupling thấp”

Gộp tất cả vào một file không xóa được phụ thuộc, chỉ làm chúng vô hình. Coupling đo bằng số thứ phải đổi cùng nhau, không đo bằng số file.

## 7. Khi nào KHÔNG dùng

Không tạo forwarding property cho mọi chuỗi truy cập chỉ để giảm số dấu chấm. Không chia type nếu các quyết định luôn đổi cùng nhau và không có caller khác.

## 8. Production notes & scale check

Các DTO rates/request mẫu được dựng từ dữ liệu tin cậy; chưa validate số âm mọi field. Test đồng thời tồn tại hai config, threshold đúng biên và enum chưa biết bị từ chối. Không có concurrent mutation trong demo; thống kê fan-in/out chỉ gợi điều tra.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Gỡ static

Tìm trong sample mọi ảnh hưởng của `ShippingConfig` và viết lại `LegacyShippingCalculator` để nhận ngưỡng qua constructor. Chạy lại hai lần và chứng minh kết quả không đổi.

**Gợi ý:** giữ nguyên tên method để thấy rõ chỉ chữ ký constructor thay đổi.

### Bài 2 — Bảng client × dữ liệu

Lập bảng: `ShippingCalculator` cần những dữ liệu nào của `Order`. Từ bảng đó, giải thích vì sao `ShippingQuoteRequest` chỉ có ba trường.

**Gợi ý:** nếu bảng có thêm cột mới, hãy hỏi trường đó thuộc về request hay thuộc về rates.

### Bài 3 — Đo cohesion

Với một class bất kỳ trong project của bạn, lập bảng method × field và đánh dấu ô nào được dùng. Xác định các cụm và đề xuất điểm tách.

**Gợi ý:** hai cụm hoàn toàn rời nhau là dấu hiệu hai class đang bị dán lại.

### Bài 4 — Bỏ cờ `bool`

Cho `SendReport(bool asPdf, bool compress, bool emailIt)`, hãy thiết kế lại. Nêu rõ tổ hợp nào vô nghĩa trong thiết kế cũ.

**Gợi ý:** cân nhắc một record tùy chọn hoặc tách thành các method riêng; chọn theo việc các cờ có loại trừ nhau không.

### Bài 5 — Đếm chi phí thay đổi

Thực hiện yêu cầu “thêm chế độ giao trong ngày” trên cả hai bản trong sample. Đếm số dòng và số file phải sửa ở mỗi bản.

**Gợi ý:** ở bản cũ, đừng quên các caller đang truyền `bool`; đó chính là chi phí lan tỏa của control coupling.

## 10. Bài tập tích hợp liên module — Judgment

So static mutable với closure capture Module05: cùng tham số chưa đủ bảo đảm cùng kết quả khi state nào còn ẩn? Với3 tốc độ cố định chọn enum hay strategy.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. State ẩn ở bản cũ là gì?
2. with sửa rates cũ không?
3. Ai trả chi phí tính Subtotal?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi định nghĩa được coupling và cohesion bằng câu hỏi kiểm chứng được.
- [ ] Tôi nhận ra common, control, stamp và content coupling trong code thật.
- [ ] Tôi giải thích được vì sao static mutable state làm kết quả phụ thuộc thứ tự chạy.
- [ ] Tôi thay được cờ `bool` điều khiển hành vi bằng thiết kế rõ nghĩa.
- [ ] Tôi rút ngắn được chuỗi `a.B.C.D` bằng cách hỏi đúng object.
- [ ] Tôi đo được cohesion bằng bảng method × field.
- [ ] Tôi build/run được sample trên `net9.0` và đối chiếu đúng output.

Điều hướng:

- Bài prerequisite: [Dependency inversion](./08-dependency-inversion.md)
- Ôn lại nền tảng: [Stack, heap, value type và reference type](../04-csharp-co-ban/05-stack-heap-value-type-reference-type.md)
- Bài tiếp theo: [Dependency injection và inversion of control](./10-dependency-injection-va-inversion-of-control.md)
