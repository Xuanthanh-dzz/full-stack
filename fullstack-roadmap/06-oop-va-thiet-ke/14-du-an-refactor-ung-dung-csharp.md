# Dự án: refactor một ứng dụng C# theo SOLID

## 1. Mục tiêu

Sau bài này, bạn có thể:

- nhận một chương trình console “chạy được nhưng khó sửa” và biến nó thành thiết kế có ranh giới rõ, không đổi hành vi;
- dựng characterization harness trước khi refactor và dùng nó làm lưới an toàn cho từng bước;
- áp dụng đồng thời các nguyên tắc của module: mô hình hóa đối tượng, SRP, OCP, LSP, ISP, DIP, composition, DI và design by contract;
- tổ chức project thành các thư mục theo vai trò: domain, application, presentation, infrastructure;
- giữ chiều phụ thuộc đúng và chứng minh bằng chính cấu trúc thư mục/namespace;
- viết composition root duy nhất và đổi adapter mà không đụng tới nghiệp vụ;
- chứng minh kết quả bằng cách chạy song song bản cũ và bản mới trên cùng dữ liệu.

## 2. Bài toán mở đầu

Cửa hàng có một công cụ chạy cuối ngày: đọc danh sách đơn hàng dạng text, tính tiền và in báo cáo. Toàn bộ công cụ nằm trong một method:

```csharp
public static string Run(IReadOnlyList<string> lines, DateOnly d)
{
    // tách chuỗi "id|tier|city|sku:qty:price;..."
    // kiểm tra dữ liệu
    // cộng tạm tính, tính chiết khấu theo hạng và theo số lượng, cắt trần
    // tính phí ship theo thành phố và ngưỡng miễn phí
    // tính thuế
    // dựng từng dòng báo cáo và phần tổng kết
}
```

Nó chạy đúng và đang được dùng thật. Đó vừa là lý do phải giữ hành vi, vừa là lý do phải dọn:

| Vấn đề | Hệ quả cụ thể |
|---|---|
| Một method làm sáu việc | mọi yêu cầu thay đổi đều đụng cùng một chỗ |
| Thuế, chiết khấu, phí ship viết thẳng trong vòng lặp | không kiểm thử được từng quy tắc |
| Thêm chương trình khuyến mãi phải sửa vòng lặp | rủi ro làm hỏng công thức cũ |
| Định dạng tiền lặp năm lần | sửa một chỗ, quên bốn chỗ |
| Đọc/ghi file nằm chung với nghiệp vụ | muốn chạy thử phải có file thật |
| Biến `sub`, `cnt`, `err`, `p`, `f` | phải đọc cả method mới hiểu một dòng |

Mục tiêu của dự án **không** phải viết lại từ đầu cho đẹp. Mục tiêu là: giữ nguyên từng ký tự của báo cáo, nhưng đưa hệ thống về trạng thái mà một yêu cầu mới chỉ chạm vào một chỗ.

### Tiêu chí chấp nhận

1. Bản cũ được giữ nguyên trong project, không sửa một ký tự, làm chuẩn đối chiếu.
2. Có harness so sánh bản cũ và bản mới trên nhiều bộ dữ liệu, kể cả batch rỗng và các dòng lỗi.
3. Mọi trường hợp so sánh phải cho kết quả `same`.
4. Quy tắc tiền (chiết khấu, phí ship, thuế) mỗi thứ nằm ở một type riêng, kiểm thử được mà không cần file.
5. Thêm một chương trình khuyến mãi mới chỉ cần thêm một class và một dòng đăng ký.
6. Đọc dữ liệu và ghi báo cáo đi qua interface do phía nghiệp vụ định nghĩa; đổi adapter không đụng nghiệp vụ.
7. Có đúng một composition root.
8. Báo cáo được ghi qua file tạm rồi thay thế file đích.
9. Build bật `Nullable` và coi warning là error; không dùng package ngoài.

## 3. Lời giải bằng code

### 3.1. Tạo project

Yêu cầu .NET SDK 9.x:

```bash
dotnet --version
mkdir OrderTool
cd OrderTool
dotnet new console --framework net9.0 --use-program-main -o .
mkdir -p Legacy Domain Domain/Pricing Application Presentation Infrastructure Testing
```

Thay `OrderTool.csproj` bằng:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
    <RootNamespace>OrderTool</RootNamespace>
  </PropertyGroup>
</Project>
```

Cấu trúc thư mục phản ánh vai trò, không phản ánh loại kỹ thuật:

```text
OrderTool/
├── Legacy/          bản cũ, chỉ để đối chiếu
├── Domain/          khái niệm và quy tắc nghiệp vụ (không biết file, không biết console)
│   └── Pricing/     chiết khấu, phí ship, thuế
├── Application/     use case, hợp đồng với thế giới bên ngoài, parser
├── Presentation/    dựng chuỗi báo cáo
├── Infrastructure/  adapter: bộ nhớ, file, đồng hồ
├── Testing/         characterization harness
└── Program.cs       composition root
```

### 3.2. Giữ nguyên bản cũ làm chuẩn

`Legacy/LegacyOrderProcessor.cs`:

```csharp
using System.Globalization;
using System.Text;

namespace OrderTool.Legacy;

// Bản gốc: giữ nguyên từng ký tự, chỉ dùng làm chuẩn đối chiếu.
public static class LegacyOrderProcessor
{
    public static string Run(IReadOnlyList<string> lines, DateOnly d)
    {
        CultureInfo inv = CultureInfo.InvariantCulture;
        StringBuilder sb = new();
        sb.AppendLine("=== ORDER REPORT " + d.ToString("yyyy-MM-dd", inv) + " ===");

        int ok = 0;
        int bad = 0;
        decimal rev = 0m;

        foreach (string l in lines)
        {
            string[] p = l.Split('|');
            if (p.Length != 4)
            {
                sb.AppendLine((p.Length > 0 ? p[0].Trim().ToUpperInvariant() : "?") +
                              " | INVALID: expected 4 fields");
                bad++;
                continue;
            }

            string id = p[0].Trim().ToUpperInvariant();
            string tier = p[1].Trim().ToLowerInvariant();
            string city = p[2].Trim();
            string[] items = p[3].Split(';', StringSplitOptions.RemoveEmptyEntries);

            if (items.Length == 0)
            {
                sb.AppendLine(id + " | INVALID: order has no line");
                bad++;
                continue;
            }

            decimal sub = 0m;
            int cnt = 0;
            string err = string.Empty;

            foreach (string it in items)
            {
                string[] f = it.Split(':');
                if (f.Length != 3)
                {
                    err = "invalid line format";
                    break;
                }

                if (!int.TryParse(f[1].Trim(), NumberStyles.Integer, inv, out int q) ||
                    !decimal.TryParse(f[2].Trim(), NumberStyles.Number, inv, out decimal pr))
                {
                    err = "invalid number";
                    break;
                }

                if (q <= 0)
                {
                    err = "quantity must be positive";
                    break;
                }

                if (pr < 0m)
                {
                    err = "price must not be negative";
                    break;
                }

                sub += q * pr;
                cnt += q;
            }

            if (err.Length > 0)
            {
                sb.AppendLine(id + " | INVALID: " + err);
                bad++;
                continue;
            }

            decimal disc = 0m;
            if (tier == "gold") { disc += decimal.Round(sub * 0.05m, 0); }
            if (cnt >= 5) { disc += decimal.Round(sub * 0.03m, 0); }

            decimal cap = decimal.Round(sub * 0.10m, 0);
            if (disc > cap) { disc = cap; }

            decimal ship = sub >= 500000m ? 0m : (city == "Ha Noi" ? 20000m : 35000m);
            decimal taxable = sub - disc;
            decimal tax = decimal.Round(taxable * 0.08m, 0);
            decimal total = taxable + tax + ship;

            sb.AppendLine(id +
                          " | subtotal=" + sub.ToString("N0", inv) + " VND" +
                          " | discount=" + disc.ToString("N0", inv) + " VND" +
                          " | shipping=" + ship.ToString("N0", inv) + " VND" +
                          " | tax=" + tax.ToString("N0", inv) + " VND" +
                          " | total=" + total.ToString("N0", inv) + " VND");

            ok++;
            rev += total;
        }

        sb.AppendLine("--- SUMMARY ---");
        sb.Append("processed=" + ok + ", invalid=" + bad +
                  ", revenue=" + rev.ToString("N0", inv) + " VND");
        return sb.ToString();
    }
}
```

Đọc kỹ method này một lần: nó là đặc tả duy nhất mà bạn có. Mỗi chi tiết nhỏ — làm tròn ở đâu, so sánh thành phố có phân biệt hoa thường không, trần chiết khấu áp trước hay sau phí ship — đều là hành vi phải giữ.

### 3.3. Kế hoạch refactor

| Bước | Việc làm | Nguyên tắc |
|---|---|---|
| 1 | Viết characterization harness | [bài 12](./12-code-smell-va-refactoring.md) |
| 2 | Tách `Money` thành value object | [bài 1](./01-mo-hinh-hoa-doi-tuong.md) |
| 3 | Tách `Order`, `OrderLine`, `CustomerTier` | [bài 1](./01-mo-hinh-hoa-doi-tuong.md), [bài 13](./13-design-by-contract-va-invariant.md) |
| 4 | Tách quy tắc tiền thành `DiscountEngine`, `ShippingPolicy`, `TaxPolicy` | [bài 4](./04-single-responsibility.md), [bài 5](./05-open-closed.md) |
| 5 | Tách parser và tách dựng báo cáo | [bài 4](./04-single-responsibility.md), [bài 11](./11-clean-code-ten-ham-va-cau-truc.md) |
| 6 | Định nghĩa `IOrderSource`, `IReportWriter`, `IClock` ở phía nghiệp vụ | [bài 7](./07-interface-segregation.md), [bài 8](./08-dependency-inversion.md) |
| 7 | Viết use case và composition root | [bài 10](./10-dependency-injection-va-inversion-of-control.md) |

Sau **mỗi** bước, chạy lại harness. Thứ tự trên không ngẫu nhiên: các bước đầu chỉ di chuyển dữ liệu, ít rủi ro nhất, và tạo chỗ đứng cho các bước sau.

### 3.4. Domain: giá trị và thực thể

`Domain/Money.cs`:

```csharp
using System.Globalization;

namespace OrderTool.Domain;

// Value object: số tiền luôn đi kèm đơn vị và không bao giờ âm.
public sealed record Money
{
    private Money(decimal amount, string currency)
    {
        Amount = amount;
        Currency = currency;
    }

    public decimal Amount { get; }

    public string Currency { get; }

    public static Money Of(decimal amount, string currency = "VND")
    {
        ArgumentOutOfRangeException.ThrowIfNegative(amount);
        ArgumentException.ThrowIfNullOrWhiteSpace(currency);

        return new Money(amount, currency.Trim().ToUpperInvariant());
    }

    public static Money Zero(string currency = "VND") => Of(0m, currency);

    public Money Add(Money other)
    {
        EnsureSameCurrency(other);
        return new Money(Amount + other.Amount, Currency);
    }

    public Money Subtract(Money other)
    {
        EnsureSameCurrency(other);
        return Of(Amount - other.Amount, Currency);
    }

    public Money Multiply(int factor)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(factor);
        return new Money(Amount * factor, Currency);
    }

    // Làm tròn tới đơn vị nhỏ nhất của tiền tệ; quy tắc làm tròn là một quyết định nghiệp vụ.
    public Money Percentage(decimal rate)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(rate);
        return new Money(decimal.Round(Amount * rate, 0), Currency);
    }

    public bool IsGreaterThan(Money other)
    {
        EnsureSameCurrency(other);
        return Amount > other.Amount;
    }

    public bool IsAtLeast(Money other)
    {
        EnsureSameCurrency(other);
        return Amount >= other.Amount;
    }

    // Định dạng tiền chỉ có một bản duy nhất trong toàn hệ thống.
    public override string ToString() =>
        $"{Amount.ToString("N0", CultureInfo.InvariantCulture)} {Currency}";

    private void EnsureSameCurrency(Money other)
    {
        ArgumentNullException.ThrowIfNull(other);

        if (!string.Equals(Currency, other.Currency, StringComparison.Ordinal))
        {
            throw new InvalidOperationException(
                $"Cannot combine {other.Currency} with {Currency}.");
        }
    }
}
```

`Domain/Order.cs`:

```csharp
namespace OrderTool.Domain;

public enum CustomerTier
{
    Standard = 0,
    Gold = 1
}

public sealed record OrderLine
{
    public OrderLine(string sku, int quantity, Money unitPrice)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sku);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity);
        ArgumentNullException.ThrowIfNull(unitPrice);

        Sku = sku.Trim().ToUpperInvariant();
        Quantity = quantity;
        UnitPrice = unitPrice;
    }

    public string Sku { get; }

    public int Quantity { get; }

    public Money UnitPrice { get; }

    public Money LineTotal => UnitPrice.Multiply(Quantity);
}

// Entity: đơn hàng tự bảo vệ invariant "luôn có ít nhất một dòng".
public sealed class Order
{
    private readonly List<OrderLine> _lines;

    public Order(string id, CustomerTier tier, string shippingCity, IReadOnlyList<OrderLine> lines)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentException.ThrowIfNullOrWhiteSpace(shippingCity);
        ArgumentNullException.ThrowIfNull(lines);

        if (lines.Count == 0)
        {
            throw new ArgumentException("An order needs at least one line.", nameof(lines));
        }

        Id = id.Trim().ToUpperInvariant();
        Tier = tier;
        ShippingCity = shippingCity.Trim();
        _lines = new List<OrderLine>(lines);
    }

    public string Id { get; }

    public CustomerTier Tier { get; }

    public string ShippingCity { get; }

    public IReadOnlyList<OrderLine> Lines => _lines;

    public int ItemCount
    {
        get
        {
            int count = 0;
            foreach (OrderLine line in _lines)
            {
                count += line.Quantity;
            }

            return count;
        }
    }

    public Money Subtotal
    {
        get
        {
            Money subtotal = Money.Zero();
            foreach (OrderLine line in _lines)
            {
                subtotal = subtotal.Add(line.LineTotal);
            }

            return subtotal;
        }
    }
}
```

### 3.5. Domain/Pricing: mỗi quy tắc một chỗ

`Domain/Pricing/DiscountRules.cs`:

```csharp
namespace OrderTool.Domain.Pricing;

// Trục biến đổi được mở: mỗi chương trình giảm giá là một implementation.
public interface IDiscountRule
{
    string Code { get; }

    Money ComputeDiscount(Order order);
}

public sealed class TierDiscountRule : IDiscountRule
{
    private readonly CustomerTier _tier;
    private readonly decimal _rate;

    public TierDiscountRule(CustomerTier tier, decimal rate)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(rate);

        _tier = tier;
        _rate = rate;
    }

    public string Code => $"tier-{_tier}";

    public Money ComputeDiscount(Order order)
    {
        ArgumentNullException.ThrowIfNull(order);

        return order.Tier == _tier ? order.Subtotal.Percentage(_rate) : Money.Zero();
    }
}

public sealed class VolumeDiscountRule : IDiscountRule
{
    private readonly int _minimumItems;
    private readonly decimal _rate;

    public VolumeDiscountRule(int minimumItems, decimal rate)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(minimumItems);
        ArgumentOutOfRangeException.ThrowIfNegative(rate);

        _minimumItems = minimumItems;
        _rate = rate;
    }

    public string Code => $"volume-{_minimumItems}";

    public Money ComputeDiscount(Order order)
    {
        ArgumentNullException.ThrowIfNull(order);

        return order.ItemCount >= _minimumItems ? order.Subtotal.Percentage(_rate) : Money.Zero();
    }
}

// Phần đóng: cách cộng dồn và mức trần không đổi khi thêm rule mới.
public sealed class DiscountEngine
{
    private readonly List<IDiscountRule> _rules;
    private readonly decimal _maxRate;

    public DiscountEngine(IReadOnlyList<IDiscountRule> rules, decimal maxRate)
    {
        ArgumentNullException.ThrowIfNull(rules);
        ArgumentOutOfRangeException.ThrowIfNegative(maxRate);

        _rules = new List<IDiscountRule>(rules);
        _maxRate = maxRate;
    }

    public Money ComputeDiscount(Order order)
    {
        ArgumentNullException.ThrowIfNull(order);

        Money total = Money.Zero();
        foreach (IDiscountRule rule in _rules)
        {
            total = total.Add(rule.ComputeDiscount(order));
        }

        Money cap = order.Subtotal.Percentage(_maxRate);
        return total.IsGreaterThan(cap) ? cap : total;
    }
}
```

`Domain/Pricing/PricingService.cs`:

```csharp
namespace OrderTool.Domain.Pricing;

public sealed record PriceBreakdown(
    Money Subtotal,
    Money Discount,
    Money Shipping,
    Money Tax,
    Money Total);

public sealed class ShippingPolicy
{
    private readonly Money _freeThreshold;
    private readonly string _localCity;
    private readonly Money _localFee;
    private readonly Money _remoteFee;

    public ShippingPolicy(Money freeThreshold, string localCity, Money localFee, Money remoteFee)
    {
        ArgumentNullException.ThrowIfNull(freeThreshold);
        ArgumentException.ThrowIfNullOrWhiteSpace(localCity);
        ArgumentNullException.ThrowIfNull(localFee);
        ArgumentNullException.ThrowIfNull(remoteFee);

        _freeThreshold = freeThreshold;
        _localCity = localCity.Trim();
        _localFee = localFee;
        _remoteFee = remoteFee;
    }

    public Money ComputeFee(Order order)
    {
        ArgumentNullException.ThrowIfNull(order);

        if (order.Subtotal.IsAtLeast(_freeThreshold))
        {
            return Money.Zero();
        }

        return string.Equals(order.ShippingCity, _localCity, StringComparison.Ordinal)
            ? _localFee
            : _remoteFee;
    }
}

public sealed class TaxPolicy
{
    private readonly decimal _rate;

    public TaxPolicy(decimal rate)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(rate);
        _rate = rate;
    }

    public Money ComputeTax(Money taxableAmount)
    {
        ArgumentNullException.ThrowIfNull(taxableAmount);
        return taxableAmount.Percentage(_rate);
    }
}

// Điều phối ba quy tắc tiền; bản thân nó không chứa công thức nào.
public sealed class PricingService
{
    private readonly DiscountEngine _discounts;
    private readonly ShippingPolicy _shipping;
    private readonly TaxPolicy _tax;

    public PricingService(DiscountEngine discounts, ShippingPolicy shipping, TaxPolicy tax)
    {
        ArgumentNullException.ThrowIfNull(discounts);
        ArgumentNullException.ThrowIfNull(shipping);
        ArgumentNullException.ThrowIfNull(tax);

        _discounts = discounts;
        _shipping = shipping;
        _tax = tax;
    }

    public PriceBreakdown Price(Order order)
    {
        ArgumentNullException.ThrowIfNull(order);

        Money subtotal = order.Subtotal;
        Money discount = _discounts.ComputeDiscount(order);
        Money taxable = subtotal.Subtract(discount);
        Money tax = _tax.ComputeTax(taxable);
        Money shipping = _shipping.ComputeFee(order);
        Money total = taxable.Add(tax).Add(shipping);

        return new PriceBreakdown(subtotal, discount, shipping, tax, total);
    }
}
```

### 3.6. Application: parser, hợp đồng và use case

`Application/OrderParser.cs`:

```csharp
using System.Globalization;
using OrderTool.Domain;

namespace OrderTool.Application;

// Dữ liệu vào sai là chuyện bình thường: trả kết quả, không ném exception.
public sealed record ParseOutcome(string OrderId, Order? Order, string? Error)
{
    public bool IsValid => Order is not null;

    public static ParseOutcome Success(Order order) => new(order.Id, order, null);

    public static ParseOutcome Failure(string orderId, string error) => new(orderId, null, error);
}

public sealed class OrderParser
{
    private const int ExpectedFieldCount = 4;

    public ParseOutcome Parse(string rawLine)
    {
        ArgumentNullException.ThrowIfNull(rawLine);

        string[] fields = rawLine.Split('|');
        if (fields.Length != ExpectedFieldCount)
        {
            string fallbackId = fields.Length > 0 ? fields[0].Trim().ToUpperInvariant() : "?";
            return ParseOutcome.Failure(fallbackId, "expected 4 fields");
        }

        string orderId = fields[0].Trim().ToUpperInvariant();
        CustomerTier tier = ParseTier(fields[1]);
        string city = fields[2].Trim();
        string[] rawItems = fields[3].Split(';', StringSplitOptions.RemoveEmptyEntries);

        if (rawItems.Length == 0)
        {
            return ParseOutcome.Failure(orderId, "order has no line");
        }

        var lines = new List<OrderLine>(rawItems.Length);
        foreach (string rawItem in rawItems)
        {
            string? error = TryParseLine(rawItem, out OrderLine? line);
            if (error is not null)
            {
                return ParseOutcome.Failure(orderId, error);
            }

            lines.Add(line!);
        }

        return ParseOutcome.Success(new Order(orderId, tier, city, lines));
    }

    private static CustomerTier ParseTier(string rawTier) =>
        string.Equals(rawTier.Trim(), "gold", StringComparison.OrdinalIgnoreCase)
            ? CustomerTier.Gold
            : CustomerTier.Standard;

    // Trả null nghĩa là thành công; trả chuỗi nghĩa là lý do từ chối.
    private static string? TryParseLine(string rawItem, out OrderLine? line)
    {
        line = null;
        string[] parts = rawItem.Split(':');
        if (parts.Length != 3)
        {
            return "invalid line format";
        }

        CultureInfo invariant = CultureInfo.InvariantCulture;
        if (!int.TryParse(parts[1].Trim(), NumberStyles.Integer, invariant, out int quantity) ||
            !decimal.TryParse(parts[2].Trim(), NumberStyles.Number, invariant, out decimal unitPrice))
        {
            return "invalid number";
        }

        if (quantity <= 0)
        {
            return "quantity must be positive";
        }

        if (unitPrice < 0m)
        {
            return "price must not be negative";
        }

        line = new OrderLine(parts[0], quantity, Money.Of(unitPrice));
        return null;
    }
}
```

`Application/ProcessOrdersUseCase.cs`:

```csharp
using OrderTool.Domain.Pricing;
using OrderTool.Presentation;

namespace OrderTool.Application;

// Hợp đồng do phía nghiệp vụ định nghĩa; hạ tầng đi implement.
public interface IOrderSource
{
    IReadOnlyList<string> ReadAll();
}

public interface IReportWriter
{
    void Write(string report);
}

public interface IClock
{
    DateOnly Today { get; }
}

public sealed record ProcessResult(int Processed, int Invalid, string Report);

// Chỉ điều phối trình tự các bước, không chứa công thức và không biết nơi lưu.
public sealed class ProcessOrdersUseCase
{
    private readonly OrderParser _parser;
    private readonly PricingService _pricing;
    private readonly ReportBuilder _reportBuilder;
    private readonly IOrderSource _source;
    private readonly IReportWriter _writer;
    private readonly IClock _clock;

    public ProcessOrdersUseCase(
        OrderParser parser,
        PricingService pricing,
        ReportBuilder reportBuilder,
        IOrderSource source,
        IReportWriter writer,
        IClock clock)
    {
        ArgumentNullException.ThrowIfNull(parser);
        ArgumentNullException.ThrowIfNull(pricing);
        ArgumentNullException.ThrowIfNull(reportBuilder);
        ArgumentNullException.ThrowIfNull(source);
        ArgumentNullException.ThrowIfNull(writer);
        ArgumentNullException.ThrowIfNull(clock);

        _parser = parser;
        _pricing = pricing;
        _reportBuilder = reportBuilder;
        _source = source;
        _writer = writer;
        _clock = clock;
    }

    public ProcessResult Execute()
    {
        var entries = new List<ReportEntry>();

        foreach (string rawLine in _source.ReadAll())
        {
            ParseOutcome outcome = _parser.Parse(rawLine);
            entries.Add(outcome.IsValid
                ? ReportEntry.Priced(outcome.OrderId, _pricing.Price(outcome.Order!))
                : ReportEntry.Rejected(outcome.OrderId, outcome.Error!));
        }

        string report = _reportBuilder.Build(_clock.Today, entries);
        _writer.Write(report);

        int processed = 0;
        foreach (ReportEntry entry in entries)
        {
            if (entry.Price is not null)
            {
                processed++;
            }
        }

        return new ProcessResult(processed, entries.Count - processed, report);
    }
}
```

### 3.7. Presentation và Infrastructure

`Presentation/ReportBuilder.cs`:

```csharp
using System.Globalization;
using System.Text;
using OrderTool.Domain;
using OrderTool.Domain.Pricing;

namespace OrderTool.Presentation;

public sealed record ReportEntry(string OrderId, PriceBreakdown? Price, string? Error)
{
    public static ReportEntry Priced(string orderId, PriceBreakdown price) => new(orderId, price, null);

    public static ReportEntry Rejected(string orderId, string error) => new(orderId, null, error);
}

// Trình bày tách khỏi quyết định: đổi bố cục báo cáo không đụng tới quy tắc tiền.
public sealed class ReportBuilder
{
    public string Build(DateOnly reportDate, IReadOnlyList<ReportEntry> entries)
    {
        ArgumentNullException.ThrowIfNull(entries);

        var builder = new StringBuilder();
        builder.AppendLine(
            $"=== ORDER REPORT {reportDate.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture)} ===");

        int processed = 0;
        Money revenue = Money.Zero();

        foreach (ReportEntry entry in entries)
        {
            if (entry.Price is null)
            {
                builder.AppendLine($"{entry.OrderId} | INVALID: {entry.Error}");
                continue;
            }

            builder.AppendLine(FormatPricedLine(entry.OrderId, entry.Price));
            processed++;
            revenue = revenue.Add(entry.Price.Total);
        }

        builder.AppendLine("--- SUMMARY ---");
        builder.Append(
            $"processed={processed}, invalid={entries.Count - processed}, revenue={revenue}");

        return builder.ToString();
    }

    private static string FormatPricedLine(string orderId, PriceBreakdown price) =>
        $"{orderId} | subtotal={price.Subtotal} | discount={price.Discount} " +
        $"| shipping={price.Shipping} | tax={price.Tax} | total={price.Total}";
}
```

`Infrastructure/Adapters.cs`:

```csharp
using OrderTool.Application;

namespace OrderTool.Infrastructure;

public sealed class InMemoryOrderSource : IOrderSource
{
    private readonly List<string> _lines;

    public InMemoryOrderSource(IReadOnlyList<string> lines)
    {
        ArgumentNullException.ThrowIfNull(lines);
        _lines = new List<string>(lines);
    }

    public IReadOnlyList<string> ReadAll() => _lines;
}

public sealed class TextFileOrderSource : IOrderSource
{
    private readonly string _path;

    public TextFileOrderSource(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        _path = path;
    }

    public IReadOnlyList<string> ReadAll()
    {
        var lines = new List<string>();
        foreach (string line in File.ReadLines(_path))
        {
            if (!string.IsNullOrWhiteSpace(line))
            {
                lines.Add(line);
            }
        }

        return lines;
    }
}

public sealed class InMemoryReportWriter : IReportWriter
{
    public string? LastReport { get; private set; }

    public void Write(string report)
    {
        ArgumentNullException.ThrowIfNull(report);
        LastReport = report;
    }
}

// Ghi ra file tạm rồi thay thế file đích: tránh để lại báo cáo dở dang.
public sealed class FileReportWriter : IReportWriter
{
    private readonly string _path;

    public FileReportWriter(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        _path = path;
    }

    public void Write(string report)
    {
        ArgumentNullException.ThrowIfNull(report);

        string temporaryPath = _path + ".tmp";
        File.WriteAllText(temporaryPath, report);
        File.Move(temporaryPath, _path, overwrite: true);
    }
}

public sealed class FixedClock : IClock
{
    public FixedClock(DateOnly today) => Today = today;

    public DateOnly Today { get; }
}

public sealed class SystemClock : IClock
{
    public DateOnly Today => DateOnly.FromDateTime(DateTime.Now);
}
```

### 3.8. Testing: lưới an toàn

`Testing/CharacterizationHarness.cs`:

```csharp
using OrderTool.Application;
using OrderTool.Legacy;

namespace OrderTool.Testing;

public sealed record ComparisonResult(string Name, bool Matches, string? FirstDifference);

// Chốt hành vi của bản cũ: mọi bước refactor phải giữ nguyên kết quả này.
public sealed class CharacterizationHarness
{
    private readonly Func<IReadOnlyList<string>, DateOnly, ProcessResult> _refactored;

    public CharacterizationHarness(Func<IReadOnlyList<string>, DateOnly, ProcessResult> refactored)
    {
        ArgumentNullException.ThrowIfNull(refactored);
        _refactored = refactored;
    }

    public ComparisonResult Compare(string name, IReadOnlyList<string> input, DateOnly today)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(name);
        ArgumentNullException.ThrowIfNull(input);

        string legacy = LegacyOrderProcessor.Run(input, today);
        string refactored = _refactored(input, today).Report;

        if (string.Equals(legacy, refactored, StringComparison.Ordinal))
        {
            return new ComparisonResult(name, true, null);
        }

        return new ComparisonResult(name, false, FindFirstDifference(legacy, refactored));
    }

    private static string FindFirstDifference(string expected, string actual)
    {
        string[] expectedLines = expected.Split('\n');
        string[] actualLines = actual.Split('\n');
        int count = Math.Min(expectedLines.Length, actualLines.Length);

        for (int index = 0; index < count; index++)
        {
            if (!string.Equals(expectedLines[index], actualLines[index], StringComparison.Ordinal))
            {
                return $"line {index + 1}: expected '{expectedLines[index]}', actual '{actualLines[index]}'";
            }
        }

        return $"line count: expected {expectedLines.Length}, actual {actualLines.Length}";
    }
}
```

### 3.9. Composition root

`Program.cs`:

```csharp
using OrderTool.Application;
using OrderTool.Domain;
using OrderTool.Domain.Pricing;
using OrderTool.Infrastructure;
using OrderTool.Presentation;
using OrderTool.Testing;

namespace OrderTool;

internal static class Program
{
    private static readonly string[] SampleOrders =
    {
        "ord-001|gold|Ha Noi|keyboard:2:750000;mouse:1:350000",
        "ord-002|standard|Da Nang|cable:1:50000",
        "ord-003|standard|Ha Noi|usb:5:60000;pad:1:80000",
        "ord-004|gold|Ha Noi|monitor:0:3000000",
        "ord-005|standard|Hue|",
        "ord-006|standard"
    };

    private static void Main()
    {
        var reportDate = new DateOnly(2026, 7, 31);

        Console.WriteLine("=== characterization ===");
        var harness = new CharacterizationHarness(RunRefactored);

        ComparisonResult[] comparisons =
        {
            harness.Compare("full batch", SampleOrders, reportDate),
            harness.Compare("empty batch", Array.Empty<string>(), reportDate),
            harness.Compare("single invalid", new[] { "ord-009|gold|Ha Noi|x:abc:1" }, reportDate),
            harness.Compare("free shipping edge", new[] { "ord-010|standard|Hue|item:1:500000" }, reportDate)
        };

        int passed = 0;
        foreach (ComparisonResult comparison in comparisons)
        {
            Console.WriteLine($"{comparison.Name}: {(comparison.Matches ? "same" : "DIFFERENT")}");
            if (comparison.Matches)
            {
                passed++;
            }
            else
            {
                Console.WriteLine($"  {comparison.FirstDifference}");
            }
        }

        Console.WriteLine($"passed={passed}, failed={comparisons.Length - passed}");

        Console.WriteLine("=== report ===");
        ProcessResult result = RunRefactored(SampleOrders, reportDate);
        Console.WriteLine(result.Report);

        Console.WriteLine("=== output file ===");
        string reportPath = Path.Combine(Path.GetTempPath(), "order-report.txt");
        BuildUseCase(new InMemoryOrderSource(SampleOrders), new FileReportWriter(reportPath), reportDate)
            .Execute();

        Console.WriteLine($"written to {Path.GetFileName(reportPath)}: {File.Exists(reportPath)}");
        Console.WriteLine($"processed={result.Processed}, invalid={result.Invalid}");

        File.Delete(reportPath);
    }

    private static ProcessResult RunRefactored(IReadOnlyList<string> rawOrders, DateOnly today) =>
        BuildUseCase(new InMemoryOrderSource(rawOrders), new InMemoryReportWriter(), today).Execute();

    // Composition root: nơi duy nhất biết class cụ thể nào ghép với class nào.
    private static ProcessOrdersUseCase BuildUseCase(
        IOrderSource source,
        IReportWriter writer,
        DateOnly today)
    {
        var discounts = new DiscountEngine(
            new IDiscountRule[]
            {
                new TierDiscountRule(CustomerTier.Gold, 0.05m),
                new VolumeDiscountRule(5, 0.03m)
            },
            maxRate: 0.10m);

        var shipping = new ShippingPolicy(
            freeThreshold: Money.Of(500_000m),
            localCity: "Ha Noi",
            localFee: Money.Of(20_000m),
            remoteFee: Money.Of(35_000m));

        var pricing = new PricingService(discounts, shipping, new TaxPolicy(0.08m));

        return new ProcessOrdersUseCase(
            new OrderParser(),
            pricing,
            new ReportBuilder(),
            source,
            writer,
            new FixedClock(today));
    }
}
```

### 3.10. Build và chạy

```bash
dotnet build
dotnet run --no-build
```

Output:

```text
=== characterization ===
full batch: same
empty batch: same
single invalid: same
free shipping edge: same
passed=4, failed=0
=== report ===
=== ORDER REPORT 2026-07-31 ===
ORD-001 | subtotal=1,850,000 VND | discount=92,500 VND | shipping=0 VND | tax=140,600 VND | total=1,898,100 VND
ORD-002 | subtotal=50,000 VND | discount=0 VND | shipping=35,000 VND | tax=4,000 VND | total=89,000 VND
ORD-003 | subtotal=380,000 VND | discount=11,400 VND | shipping=20,000 VND | tax=29,488 VND | total=418,088 VND
ORD-004 | INVALID: quantity must be positive
ORD-005 | INVALID: order has no line
ORD-006 | INVALID: expected 4 fields
--- SUMMARY ---
processed=3, invalid=3, revenue=2,405,188 VND
=== output file ===
written to order-report.txt: True
processed=3, invalid=3
```

Project được kiểm tra bằng .NET SDK `9.0.119`, target `net9.0`, không dùng package ngoài. Báo cáo được ghi vào thư mục tạm của hệ điều hành rồi xóa, nên chương trình không để lại rác.

## 4. Giải thích cơ chế

### Bản đồ phụ thuộc

```text
Program.cs (composition root)
  │  biết mọi type cụ thể
  ▼
Application ──> Domain            (use case gọi nghiệp vụ)
  │  ▲              ▲
  │  │              │
  │  │         Domain/Pricing     (quy tắc tiền, không biết gì về I/O)
  │  │
  │  └── IOrderSource, IReportWriter, IClock   ◄── Infrastructure implement
  ▼
Presentation ──> Domain           (chỉ đọc dữ liệu để dựng chuỗi)

Legacy ──> (không ai phụ thuộc, chỉ Testing dùng để đối chiếu)
```

Điểm cần kiểm tra: **không mũi tên nào đi từ `Domain` ra ngoài**. `Domain` không `using` `Infrastructure`, không `using` `System.IO`. Nếu tách thành nhiều project như gợi ý ở [bài 8](./08-dependency-inversion.md), quy tắc này trở thành ràng buộc biên dịch thay vì thỏa thuận.

### Nơi từng nguyên tắc của module xuất hiện

| Nguyên tắc | Xuất hiện ở |
|---|---|
| Mô hình hóa đối tượng | `Money` (value object), `Order` (entity có invariant) |
| Encapsulation | `Order._lines` private, `Lines` trả `IReadOnlyList` |
| Composition over inheritance | `PricingService` ghép ba policy; không có cây kế thừa nào |
| SRP | parser, quy tắc tiền, dựng báo cáo, ghi file nằm ở bốn nơi |
| OCP | thêm `IDiscountRule` mới không sửa `DiscountEngine` |
| LSP | mọi `IDiscountRule` trả `Money` hợp lệ, không cái nào ném `NotSupportedException` |
| ISP | `IOrderSource`, `IReportWriter`, `IClock` mỗi cái một method/property |
| DIP | ba interface trên được khai báo trong `Application`, hạ tầng đi implement |
| Coupling/cohesion | không còn biến static; `Order` tự trả lời `Subtotal`, `ItemCount` |
| DI/IoC | mọi phụ thuộc vào qua constructor; một composition root |
| Clean code | tên theo nghiệp vụ, hằng số có tên, guard clause |
| Refactoring an toàn | harness so sánh với bản cũ |
| Design by contract | `Money.Of` chặn số âm, `Order` chặn danh sách rỗng, parser trả lý do |

### Vì sao harness phải có “empty batch” và “free shipping edge”

Bốn bộ dữ liệu trong sample không được chọn ngẫu nhiên:

- **full batch** đi qua mọi nhánh chính: hạng gold, giảm theo số lượng, ba loại lỗi khác nhau.
- **empty batch** kiểm tra phần tổng kết khi không có dòng nào — chỗ rất dễ sai khi tách `ReportBuilder`.
- **single invalid** khóa lại thông điệp lỗi, vốn là một phần hành vi mà người dùng thấy.
- **free shipping edge** dùng `subtotal` đúng bằng ngưỡng `500.000`. Nếu bản mới viết `>` thay vì `>=`, chỉ trường hợp này phát hiện ra.

Kinh nghiệm: mỗi khi bạn thấy một hằng số so sánh trong code cũ, hãy thêm một bộ dữ liệu nằm **đúng** trên hằng số đó.

### Một số chi tiết dễ làm đổi hành vi

Trong lúc tách, ba chỗ suýt làm lệch kết quả:

1. **Thứ tự cộng và cắt trần.** Bản cũ cộng đủ hai loại chiết khấu rồi mới cắt trần. Nếu cắt trần từng rule, `ORD-001` sẽ ra số khác.
2. **So sánh thành phố.** Bản cũ dùng `city == "Ha Noi"`, tức phân biệt hoa thường. `ShippingPolicy` giữ nguyên `StringComparison.Ordinal` để không âm thầm “sửa lỗi”. Nếu muốn đổi thành so sánh không phân biệt hoa thường, đó là **thay đổi hành vi** và phải là một commit riêng.
3. **Làm tròn.** `decimal.Round(x, 0)` dùng quy tắc banker's rounding, khác với làm tròn nửa lên. `Money.Percentage` dùng đúng lời gọi đó nên kết quả trùng khớp.

Chi tiết thứ ba đáng nhớ: một “dọn dẹp” tưởng vô hại như đổi sang `Math.Round(x, MidpointRounding.AwayFromZero)` sẽ làm lệch tiền ở đúng những đơn hàng có phần lẻ `0,5`.

### Đào sâu (có thể quay lại sau)

#### Thêm một chương trình khuyến mãi

Tiêu chí chấp nhận số 5 được kiểm chứng như sau: viết `SeasonalDiscountRule` trong `Domain/Pricing`, rồi thêm một dòng vào mảng trong `BuildUseCase`. `DiscountEngine`, `PricingService`, `ProcessOrdersUseCase`, `ReportBuilder` đều không đổi.

Lưu ý: bản cũ **không** có khuyến mãi theo mùa, nên sau khi thêm, harness sẽ báo `DIFFERENT` — và đó là điều đúng, vì bạn vừa đổi hành vi có chủ đích. Lúc đó, harness phải được cập nhật kèm mô tả rõ ràng, hoặc chạy với cấu hình không bật rule mới.

#### Vì sao `ReportEntry` nằm ở `Presentation`

`ReportEntry` là dữ liệu **để hiển thị**, không phải khái niệm nghiệp vụ. Đặt nó cạnh `ReportBuilder` giữ cho `Domain` không phình vì các nhu cầu trình bày. Đổi lại, `Application` phải `using OrderTool.Presentation` — một phụ thuộc có chủ đích và được ghi rõ.

Nếu sau này có nhiều dạng đầu ra (JSON, CSV, HTML), bước tiếp theo là để use case trả về một danh sách kết quả thuần nghiệp vụ và để mỗi presenter tự dựng dữ liệu hiển thị của mình.

#### Giới hạn của thiết kế hiện tại

- Toàn bộ batch nằm trong bộ nhớ. Với file rất lớn, `IOrderSource` nên trả `IEnumerable<string>` để đọc theo luồng.
- Không có xử lý đồng thời. Nếu cần, các policy hiện tại đều không có state thay đổi nên an toàn, nhưng `ReportBuilder` cộng dồn trong một vòng lặp và phải xem lại.
- Không có logging, không có cấu hình ngoài, không có test framework. Ba thứ đó lần lượt thuộc [module 11](../PROGRESS.md#11-aspnet-core-backend), [module 15](../PROGRESS.md#15-devops-trien-khai) và [module 14](../PROGRESS.md#14-testing-chat-luong).

#### Khi nào dừng lại

Thiết kế này có thể tiếp tục được chia nhỏ: tách `Order` khỏi `OrderLine` sang hai file, tạo `SkuCode` value object, tách `TaxPolicy` theo quốc gia. Đừng làm nếu chưa có yêu cầu thật. Mỗi tầng trừu tượng phải trả lời được câu hỏi “thay đổi nào trong tương lai gần khiến nó đáng giá?”.

## 5. Kiến thức nền

### Quy trình chuẩn khi nhận code cũ

1. **Đọc và chạy** trước khi sửa. Ghi lại hành vi quan sát được, kể cả những chỗ trông như lỗi.
2. **Chốt hành vi** bằng harness hoặc test.
3. **Liệt kê mùi** và xếp thứ tự theo rủi ro tăng dần.
4. **Refactor từng bước**, chạy harness sau mỗi bước, commit riêng.
5. **Chỉ sau đó** mới thêm tính năng hoặc sửa lỗi, ở commit riêng.

Bước 1 hay bị bỏ qua nhất và cũng là bước tốn kém nhất khi bỏ qua.

### Ranh giới thư mục nên phản ánh vai trò

| Thư mục | Chứa gì | Không được chứa |
|---|---|---|
| `Domain` | khái niệm, quy tắc, invariant | I/O, framework, chuỗi hiển thị |
| `Application` | use case, hợp đồng với bên ngoài | công thức nghiệp vụ chi tiết |
| `Presentation` | dựng chuỗi/màn hình | quyết định nghiệp vụ |
| `Infrastructure` | adapter cho file, DB, mạng, đồng hồ | quy tắc nghiệp vụ |

Chia theo `Models/Services/Helpers` không đạt được điều này, vì tên thư mục không nói gì về chiều phụ thuộc.

### Dấu hiệu refactor đã đủ cho vòng này

- Mỗi yêu cầu thay đổi trong danh sách ban đầu chỉ chạm một chỗ.
- Có thể kiểm thử từng quy tắc mà không cần file, mạng hay đồng hồ.
- Người mới đọc `ProcessOrdersUseCase` là hiểu quy trình.
- Composition root là nơi duy nhất có tên các class hạ tầng.

Nếu bốn điều trên đã đúng, hãy dừng và chuyển sang việc tạo giá trị mới.

### Từ dự án này đi tiếp

Thiết kế bạn vừa dựng chính là hình dạng thu nhỏ của kiến trúc phân tầng sẽ gặp lại nhiều lần: domain ở trong, use case bọc quanh, hạ tầng ở ngoài cùng, composition root nối tất cả. [Module 16](../PROGRESS.md#16-design-pattern) sẽ đặt tên cho các cấu trúc lặp lại trong đó, còn [module 17](../PROGRESS.md#17-kien-truc-phan-mem) mở rộng nó lên quy mô hệ thống.

## 6. Lỗi thường gặp

### Sửa bản cũ trong lúc refactor

Chỉ cần đổi một khoảng trắng trong `LegacyOrderProcessor`, chuẩn đối chiếu không còn đáng tin. Nếu bản cũ có lỗi thật, hãy ghi nhận và xử lý sau khi refactor xong.

### Harness quá ít trường hợp

Ba dòng dữ liệu “trông hợp lý” không phủ được các nhánh lỗi và các biên. Hãy đọc code cũ để liệt kê nhánh, rồi tạo dữ liệu cho từng nhánh.

### “Tiện tay sửa lỗi” giữa chừng

So sánh thành phố phân biệt hoa thường trông như lỗi. Sửa nó ngay trong đợt refactor sẽ làm harness đỏ và bạn sẽ mất thời gian nghi ngờ chính bước tách của mình.

### Domain lỡ dùng tới hạ tầng

Một dòng `File.ReadAllText` hoặc `DateTime.Now` lọt vào `Domain` là đủ để phá toàn bộ tính kiểm thử. Kiểm tra định kỳ bằng cách nhìn danh sách `using` của các file trong `Domain`.

### Use case phình thành god class mới

Nếu `Execute` bắt đầu chứa `if` về loại khách hoặc công thức tiền, hãy đẩy chúng về đúng type. Use case chỉ giữ trình tự.

### Chia file quá nhỏ ngay từ đầu

Ở quy mô này, gộp `IDiscountRule` cùng hai implementation và `DiscountEngine` trong một file là hợp lý vì chúng luôn được đọc cùng nhau. Hãy tách thêm khi file vượt quá tầm đọc một lần.

### Bỏ qua việc ghi file an toàn

`File.WriteAllText` thẳng vào file đích sẽ để lại báo cáo dở dang nếu tiến trình chết giữa chừng. Mẫu ghi file tạm rồi thay thế được dùng lại từ [module 05, bài 19](../05-csharp-nang-cao/19-du-an-xu-ly-du-lieu-bat-dong-bo.md).

## 7. Bài tập

### Bài 1 — Thêm bộ dữ liệu cho harness

Bổ sung ít nhất bốn trường hợp: đơn có `subtotal` đúng `500.000`, đơn gold đúng 5 sản phẩm (đụng cả hai rule và trần), giá `0`, và một dòng có khoảng trắng thừa quanh dấu `|`.

**Gợi ý:** dự đoán kết quả trước khi chạy; nếu dự đoán sai, bạn vừa học được một hành vi ẩn của bản cũ.

### Bài 2 — Khuyến mãi theo mùa

Thêm `SeasonalDiscountRule` (khoảng ngày + ngưỡng tối thiểu + số tiền cố định) và đăng ký vào composition root. Cập nhật harness để phản ánh thay đổi hành vi có chủ đích.

**Gợi ý:** rule cần biết “hôm nay”; lấy nó từ `IClock` qua constructor thay vì `DateTime.Now`.

### Bài 3 — Đầu ra thứ hai

Viết `CsvReportBuilder` sinh báo cáo dạng CSV và cho phép chọn định dạng ở composition root, không sửa use case.

**Gợi ý:** rút một interface từ `ReportBuilder` theo đúng nhu cầu của use case, không sao chép mọi method.

### Bài 4 — Tách thành ba project

Chuyển `Domain` + `Application`, `Infrastructure`, và app console thành ba project riêng. Chứng minh `Domain` không tham chiếu project nào khác.

**Gợi ý:** `ReportEntry` sẽ buộc bạn quyết định `Presentation` thuộc về đâu; ghi lại lý do lựa chọn.

### Bài 5 — Đo lại chi phí thay đổi

Thực hiện bốn yêu cầu sau trên **cả** bản cũ và bản mới, đếm số file và số dòng phải sửa: đổi thuế suất; đổi thành phố nội thành; thêm hạng khách `Platinum`; đổi tiêu đề báo cáo.

**Gợi ý:** lập bảng hai cột; đây là bằng chứng thuyết phục nhất khi bạn phải giải thích giá trị của refactoring cho người khác.

## 8. Checklist tự đánh giá và điều hướng

Bạn hoàn thành bài khi có thể tự trả lời:

- [ ] Tôi giải thích được vì sao phải chốt hành vi trước khi refactor và harness của tôi phủ những nhánh nào.
- [ ] Tôi chỉ ra được nơi từng nguyên tắc của module xuất hiện trong project.
- [ ] Tôi chứng minh được `Domain` không phụ thuộc hạ tầng.
- [ ] Tôi thêm được một quy tắc giảm giá mới mà chỉ chạm hai chỗ.
- [ ] Tôi đổi được adapter ghi báo cáo mà không sửa nghiệp vụ.
- [ ] Tôi nêu được ba chi tiết dễ làm đổi hành vi khi tách code cũ.
- [ ] Tôi biết khi nào nên dừng refactor.
- [ ] Tôi build/run được project trên `net9.0`, mọi trường hợp so sánh đều `same`.

Điều hướng:

- **Bài prerequisite trực tiếp:** [Bài 13 — Design by contract và invariant](./13-design-by-contract-va-invariant.md)
- **Ôn lại project nền:** [Module 05, bài 19 — Dự án xử lý dữ liệu bất đồng bộ](../05-csharp-nang-cao/19-du-an-xu-ly-du-lieu-bat-dong-bo.md)
- **Bài tiếp theo theo lộ trình:** [Module 07 — Cấu trúc dữ liệu và giải thuật](../PROGRESS.md#07-cau-truc-du-lieu-giai-thuat), bắt đầu bằng `01-big-o-thoi-gian-va-bo-nho.md` khi module đó được biên soạn.
