# Open/closed

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phát biểu nguyên tắc open/closed: mở để mở rộng, đóng với sửa đổi;
- nhận ra “trục biến đổi” của một bài toán trước khi tạo abstraction;
- thay một chuỗi `switch` đang phình to bằng tập hợp các implementation của một interface;
- thêm hành vi mới bằng cách thêm file, không sửa code đang chạy đúng;
- giữ phần chính sách chung (giới hạn, thứ tự áp dụng) ở nơi cố định;
- giải thích vì sao vẫn phải sửa một chỗ — nơi đăng ký — và vì sao chỗ đó chấp nhận được;
- tránh abstraction đầu cơ khi trục biến đổi chưa xuất hiện.

## 2. Bài toán mở đầu

Tiếp tục từ `PricingPolicy` ở [bài 4](./04-single-responsibility.md). Marketing bắt đầu ra khuyến mãi liên tục, và code chiết khấu tiến hóa theo kiểu quen thuộc:

```csharp
public decimal ComputeDiscount(Cart cart)
{
    decimal discount = 0m;

    if (cart.CustomerTier == "gold")
    {
        discount += cart.Subtotal * 0.05m;
    }

    if (cart.ItemCount >= 5)
    {
        discount += cart.Subtotal * 0.03m;
    }

    // tháng 7 có campaign, nhớ xóa sau ngày 31
    if (cart.OrderDate.Month == 7 && cart.Subtotal >= 500_000m)
    {
        discount += 100_000m;
    }

    return discount;
}
```

Mỗi chương trình khuyến mãi mới là một lần sửa đúng method này. Hệ quả rất cụ thể:

- một sửa đổi cho campaign mới có thể làm hỏng công thức của campaign cũ, và người sửa thường không chạy lại toàn bộ tình huống cũ;
- method dài dần, các điều kiện bắt đầu chồng nhau, và không ai dám xóa nhánh nào;
- hai người làm hai campaign song song sẽ sửa cùng một method và đụng nhau khi merge;
- muốn tắt tạm một campaign phải comment code rồi deploy lại.

Điều đáng chú ý: **cấu trúc của bài toán không đổi** — luôn là “xét giỏ hàng, trả ra một khoản giảm”. Chỉ có **danh sách quy tắc** là đổi. Đó chính là trục biến đổi cần được mở ra.

## 3. Lời giải bằng code

Tạo project `.NET 9`:

```bash
mkdir OpenClosedDemo
cd OpenClosedDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `OpenClosedDemo.csproj` bằng:

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

namespace OpenClosedDemo;

public sealed record Cart(
    string CustomerTier,
    decimal Subtotal,
    int ItemCount,
    DateOnly OrderDate);

public sealed record DiscountResult(decimal Amount, IReadOnlyList<string> AppliedCodes);

// Trục biến đổi được mở ra: mỗi quy tắc là một implementation.
public interface IDiscountRule
{
    string Code { get; }

    // Trả 0 nghĩa là quy tắc không áp dụng cho giỏ hàng này.
    decimal ComputeDiscount(Cart cart);
}

public sealed class TierDiscountRule : IDiscountRule
{
    private readonly string _tier;
    private readonly decimal _rate;

    public TierDiscountRule(string tier, decimal rate)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(tier);
        ArgumentOutOfRangeException.ThrowIfNegative(rate);

        _tier = tier.Trim().ToLowerInvariant();
        _rate = rate;
    }

    public string Code => $"tier-{_tier}";

    public decimal ComputeDiscount(Cart cart)
    {
        ArgumentNullException.ThrowIfNull(cart);

        bool matches = string.Equals(
            cart.CustomerTier,
            _tier,
            StringComparison.OrdinalIgnoreCase);

        return matches ? decimal.Round(cart.Subtotal * _rate, 0) : 0m;
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

    public decimal ComputeDiscount(Cart cart)
    {
        ArgumentNullException.ThrowIfNull(cart);

        return cart.ItemCount >= _minimumItems
            ? decimal.Round(cart.Subtotal * _rate, 0)
            : 0m;
    }
}

public sealed class SeasonalDiscountRule : IDiscountRule
{
    private readonly DateOnly _from;
    private readonly DateOnly _to;
    private readonly decimal _minimumSubtotal;
    private readonly decimal _amount;

    public SeasonalDiscountRule(
        string code,
        DateOnly from,
        DateOnly to,
        decimal minimumSubtotal,
        decimal amount)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(code);
        ArgumentOutOfRangeException.ThrowIfNegative(minimumSubtotal);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(amount);

        if (to < from)
        {
            throw new ArgumentException("Campaign end must not be before start.", nameof(to));
        }

        Code = code.Trim().ToLowerInvariant();
        _from = from;
        _to = to;
        _minimumSubtotal = minimumSubtotal;
        _amount = amount;
    }

    public string Code { get; }

    public decimal ComputeDiscount(Cart cart)
    {
        ArgumentNullException.ThrowIfNull(cart);

        bool inWindow = cart.OrderDate >= _from && cart.OrderDate <= _to;
        return inWindow && cart.Subtotal >= _minimumSubtotal ? _amount : 0m;
    }
}

// Phần ĐÓNG: cách cộng dồn và mức trần không đổi khi có campaign mới.
public sealed class DiscountEngine
{
    private readonly IReadOnlyList<IDiscountRule> _rules;
    private readonly decimal _maxRate;

    public DiscountEngine(IReadOnlyList<IDiscountRule> rules, decimal maxRate)
    {
        ArgumentNullException.ThrowIfNull(rules);
        ArgumentOutOfRangeException.ThrowIfNegative(maxRate);

        _rules = rules;
        _maxRate = maxRate;
    }

    public DiscountResult Apply(Cart cart)
    {
        ArgumentNullException.ThrowIfNull(cart);

        decimal total = 0m;
        var codes = new List<string>();

        foreach (IDiscountRule rule in _rules)
        {
            decimal amount = rule.ComputeDiscount(cart);
            if (amount <= 0m)
            {
                continue;
            }

            total += amount;
            codes.Add(rule.Code);
        }

        decimal cap = decimal.Round(cart.Subtotal * _maxRate, 0);
        if (total > cap)
        {
            total = cap;
            codes.Add("capped");
        }

        return new DiscountResult(total, codes);
    }
}

// Campaign mới: THÊM file, không sửa DiscountEngine và không sửa quy tắc cũ.
public sealed class FirstOrderDiscountRule : IDiscountRule
{
    private readonly decimal _amount;

    public FirstOrderDiscountRule(decimal amount)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(amount);
        _amount = amount;
    }

    public string Code => "first-order";

    public decimal ComputeDiscount(Cart cart)
    {
        ArgumentNullException.ThrowIfNull(cart);

        return string.Equals(cart.CustomerTier, "new", StringComparison.OrdinalIgnoreCase)
            ? _amount
            : 0m;
    }
}

internal static class Program
{
    private static void Main()
    {
        var july = new SeasonalDiscountRule(
            code: "july-sale",
            from: new DateOnly(2026, 7, 1),
            to: new DateOnly(2026, 7, 31),
            minimumSubtotal: 500_000m,
            amount: 100_000m);

        var rules = new List<IDiscountRule>
        {
            new TierDiscountRule("gold", 0.05m),
            new VolumeDiscountRule(5, 0.03m),
            july
        };

        var engine = new DiscountEngine(rules, maxRate: 0.10m);

        var goldCart = new Cart("gold", 2_000_000m, 6, new DateOnly(2026, 7, 15));
        var silverCart = new Cart("silver", 400_000m, 2, new DateOnly(2026, 8, 2));

        Print("gold, 6 items, July", engine.Apply(goldCart));
        Print("silver, 2 items, August", engine.Apply(silverCart));

        // Mở rộng: thêm một rule mới vào danh sách, engine giữ nguyên.
        rules.Add(new FirstOrderDiscountRule(50_000m));
        var newCustomerCart = new Cart("new", 300_000m, 1, new DateOnly(2026, 8, 2));

        Print("new customer", engine.Apply(newCustomerCart));
        Print("gold again", engine.Apply(goldCart));
    }

    private static void Print(string label, DiscountResult result)
    {
        string codes = result.AppliedCodes.Count == 0
            ? "none"
            : string.Join(", ", result.AppliedCodes);

        Console.WriteLine($"{label}: {result.Amount:N0} [{codes}]");
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
gold, 6 items, July: 200,000 [tier-gold, volume-5, july-sale, capped]
silver, 2 items, August: 0 [none]
new customer: 30,000 [first-order, capped]
gold again: 200,000 [tier-gold, volume-5, july-sale, capped]
```

Project được kiểm tra bằng .NET SDK `9.0.119`, target `net9.0`, không dùng package ngoài.

## 4. Giải thích cơ chế

### Cái gì mở, cái gì đóng

| Phần | Trạng thái | Lý do |
|---|---|---|
| Danh sách quy tắc | **mở** | mỗi campaign là một implementation mới |
| Cách cộng dồn nhiều quy tắc | **đóng** | chính sách chung, không đổi theo campaign |
| Mức trần `maxRate` | **đóng** về cấu trúc, cấu hình được về giá trị | trần là chính sách công ty |
| Hợp đồng `IDiscountRule` | **đóng** | đổi nó là đổi mọi implementation |

`DiscountEngine` đã được viết xong và không cần mở lại khi marketing ra campaign thứ mười. Trong sample, `FirstOrderDiscountRule` được thêm mà không có dòng nào của `DiscountEngine`, `TierDiscountRule` hay `VolumeDiscountRule` bị sửa.

### “Đóng với sửa đổi” không có nghĩa là không sửa gì

Một chỗ vẫn phải sửa: nơi tạo danh sách `rules`. Đó là điều không tránh được — phần mềm phải biết nó có những quy tắc nào. Điểm khác biệt nằm ở tính chất của thay đổi:

```text
Trước: sửa giữa một method dài đang chứa logic của mọi campaign
       -> rủi ro làm hỏng nhánh khác, khó review, dễ đụng merge

Sau:   thêm một dòng vào danh sách ở nơi ghép nối
       -> rủi ro cục bộ, review chỉ cần đọc class mới
```

Nơi ghép nối này chính là composition root đã nhắc tới ở [bài 3](./03-composition-over-inheritance.md), và [bài 10](./10-dependency-injection-va-inversion-of-control.md) sẽ đặt tên và tổ chức nó tử tế.

### Vì sao “trả 0 nghĩa là không áp dụng”

Hợp đồng của `IDiscountRule` chỉ có một method. Có thể tách thành `IsApplicable(cart)` và `ComputeDiscount(cart)`, nhưng khi đó caller phải nhớ gọi đúng thứ tự và hai method có thể lệch nhau. Gộp lại thành một method với quy ước rõ ràng làm hợp đồng khó dùng sai hơn.

Quy ước phải được ghi thành lời, vì `0` là một giá trị hợp lệ về mặt kiểu dữ liệu. Cách viết hợp đồng chặt chẽ hơn — precondition, postcondition — là nội dung của [bài 13](./13-design-by-contract-va-invariant.md).

### Luồng chạy của một lần `Apply`

```text
Apply(goldCart)
  ├─ TierDiscountRule("gold", 5%)   -> 2,000,000 * 0.05 = 100,000  ✔ codes += tier-gold
  ├─ VolumeDiscountRule(5, 3%)      -> 2,000,000 * 0.03 =  60,000  ✔ codes += volume-5
  ├─ SeasonalDiscountRule(july)     -> trong khoảng + đủ ngưỡng    ✔ codes += july-sale (100,000)
  │
  ├─ tổng = 260,000
  ├─ cap  = 2,000,000 * 0.10 = 200,000
  └─ 260,000 > 200,000 -> lấy 200,000, codes += capped
```

Giỏ `silver` không khớp quy tắc nào nên trả `0` và danh sách rỗng. Giỏ khách mới chỉ khớp `first-order` với `50,000`, nhưng trần của giỏ `300,000` là `30,000`, nên kết quả bị cắt — một ví dụ cho thấy phần “đóng” vẫn có quyền quyết định cuối cùng.

### Đào sâu (có thể quay lại sau)

#### Cấu trúc dữ liệu của phần mở

Trong sample, `DiscountEngine` giữ chính `List<IDiscountRule>` mà `Main` tạo, nên `rules.Add(...)` sau đó vẫn có hiệu lực với engine đã tạo. Điều này tiện cho demo nhưng là dao hai lưỡi: engine không kiểm soát được tập quy tắc của mình. Trong code thật, hãy sao chép danh sách vào bên trong constructor, và nếu cần đổi lúc chạy thì làm việc đó qua một API tường minh.

#### Khi nào `switch` vẫn tốt hơn

Nếu tập trường hợp **đóng và ổn định** — ví dụ bốn trạng thái đơn hàng — thì `switch` biểu đạt rõ hơn và compiler còn giúp bạn kiểm tra đủ nhánh. Pattern matching đã học ở [module 05, bài 8](../05-csharp-nang-cao/08-pattern-matching.md) rất hợp cho loại này. Hãy mở abstraction cho tập **mở** (danh sách campaign), không cho tập đóng (trạng thái).

#### Trục biến đổi phải quan sát được

Nguyên tắc thực dụng: chờ tới lần thay đổi thứ hai hoặc thứ ba cùng dạng rồi mới trừu tượng hóa. Trước đó, bạn đang đoán. Một abstraction đoán sai còn tốn kém hơn ba lần `if`, vì nó khóa cấu trúc của cả vùng code.

#### Quy tắc lấy dữ liệu từ ngoài

Nếu một campaign cần kiểm tra “khách đã mua bao nhiêu đơn trước đây”, quy tắc đó cần dữ liệu mà `Cart` không có. Hai hướng: mở rộng dữ liệu đầu vào (thêm field vào một record ngữ cảnh), hoặc để quy tắc nhận collaborator qua constructor. Hướng thứ hai kéo theo phụ thuộc vào hạ tầng — [bài 8](./08-dependency-inversion.md) sẽ chỉ cách giữ chiều phụ thuộc đúng.

## 5. Kiến thức nền

### Ba cách mở một trục biến đổi trong C#

| Cách | Khi nào hợp | Chi phí |
|---|---|---|
| Interface + nhiều implementation | hành vi có tên, có state riêng, cần test riêng | một type mỗi biến thể |
| `Func<>`/`Action<>` | hành vi ngắn, một phép tính, không cần tên | mất tên có nghĩa, khó tái sử dụng |
| `virtual` + kế thừa | có khung chung bắt buộc | ràng buộc lớp con vào base |

Sample dùng cách thứ nhất vì mỗi quy tắc có tham số riêng (`_rate`, khoảng ngày) và cần một `Code` để hiển thị.

### Dấu hiệu bạn đang cần OCP

- Một method có `switch`/`if-else` dài mà mỗi yêu cầu mới lại thêm một nhánh.
- Cùng một `enum` được `switch` ở nhiều nơi khác nhau, và thêm giá trị mới thì phải đi tìm hết.
- Người review liên tục hỏi “thay đổi này có ảnh hưởng nhánh cũ không?”.
- Có commit dạng “tạm comment campaign X”.

### OCP và các nguyên tắc khác

OCP dựa trên polymorphism ([bài 2](./02-encapsulation-abstraction-inheritance-polymorphism.md)) và chỉ hoạt động nếu các implementation thật sự thay thế được cho nhau — tức là tuân thủ Liskov ([bài 6](./06-liskov-substitution.md)). Nếu `DiscountEngine` phải viết `if (rule is SeasonalDiscountRule)`, abstraction đã hỏng và OCP không còn.

### Cấu hình cũng là một dạng mở rộng

Không phải mọi biến đổi đều cần class mới. `TierDiscountRule("gold", 0.05m)` cho phép tạo bậc `platinum` chỉ bằng một dòng cấu hình. Hãy phân biệt:

- đổi **tham số** của một quy tắc đã có → cấu hình;
- đổi **cách tính** → implementation mới.

Đưa quy tắc ra file cấu hình hoặc database là bước tiếp theo và sẽ gặp lại ở các module về backend.

## 6. Lỗi thường gặp

### Trừu tượng hóa khi chưa có trục biến đổi

Tạo `IEmailSender`, `IEmailSenderFactory`, `IEmailSenderFactoryProvider` cho một hệ thống chỉ gửi email bằng đúng một cách. Đó là abstraction đầu cơ: tốn chi phí đọc hiểu ngay lập tức, đổi lấy một lợi ích có thể không bao giờ đến.

### Mở sai trục

Bài toán đổi theo “danh sách quy tắc” nhưng lại tạo abstraction theo “loại khách hàng”. Kết quả là mỗi campaign vẫn phải sửa nhiều class. Hãy nhìn lịch sử thay đổi thật để xác định trục.

### `if (x is ConcreteType)` bên trong phần đóng

Ngay khi engine cần biết type cụ thể của một rule, phần đóng lại mở ra. Nếu thật sự cần thông tin đó, hãy đưa nó vào hợp đồng (ví dụ thêm property `Priority`), đừng ép kiểu.

### Interface phình theo từng yêu cầu

Thêm `ComputeDiscount`, rồi `Describe`, rồi `IsStackable`, rồi `AppliesToShipping`. Mỗi lần thêm là một lần sửa **mọi** implementation — tức là chính điều OCP muốn tránh. Hợp đồng phải nhỏ và ổn định; [bài 7](./07-interface-segregation.md) sẽ nói về giới hạn này.

### Quên chính sách chung khi thêm implementation

Nếu mức trần được viết trong từng rule thay vì trong engine, mỗi campaign mới phải nhớ tự cắt trần. Chính sách áp dụng cho mọi biến thể phải nằm ở phần đóng.

### Coi OCP là cấm sửa file cũ

Sửa lỗi, đổi tên cho rõ, tối ưu hiệu năng đều là sửa file cũ và đều hợp lệ. OCP nói về việc **thêm hành vi mới**, không nói về việc bảo trì.

### Danh sách quy tắc phụ thuộc thứ tự mà không nói ra

Nếu kết quả đổi khi đảo thứ tự phần tử trong `rules`, thứ tự đó là một phần hợp đồng và phải được ghi rõ hoặc kiểm soát bằng một trường sắp xếp. Sample cộng dồn nên thứ tự chỉ ảnh hưởng danh sách `AppliedCodes`, không ảnh hưởng số tiền.

## 7. Bài tập

### Bài 1 — Campaign theo mã giảm giá

Viết `CouponDiscountRule` áp dụng khi giỏ hàng có mã hợp lệ. Thêm dữ liệu cần thiết vào `Cart` và giải thích vì sao thay đổi đó không phá OCP.

**Gợi ý:** thêm field vào `Cart` là sửa hợp đồng dữ liệu, không phải sửa engine — hãy cân nhắc dùng một record ngữ cảnh riêng nếu `Cart` bắt đầu phình.

### Bài 2 — Đổi chính sách cộng dồn

Sửa `DiscountEngine` sang chế độ “chỉ lấy quy tắc có giá trị lớn nhất”. Không được sửa bất kỳ rule nào.

**Gợi ý:** viết hai engine khác nhau rồi so sánh, thay vì thêm một `bool` chọn chế độ.

### Bài 3 — Nhận diện tập đóng

Với `OrderStatus` (`Draft`, `Placed`, `Cancelled`), hãy viết hàm mô tả trạng thái bằng `switch` biểu thức và giải thích vì sao ở đây `switch` tốt hơn interface.

**Gợi ý:** thử tưởng tượng phải thêm trạng thái mới — compiler có nhắc bạn không? Đó là lợi thế của tập đóng.

### Bài 4 — Rule cần dữ liệu ngoài

Thiết kế `LoyaltyDiscountRule` cần biết số đơn hàng trước đây của khách. Chỉ cần khai báo hợp đồng và giải thích hai hướng lấy dữ liệu.

**Gợi ý:** hướng nào giữ cho `DiscountEngine` không biết gì về database?

### Bài 5 — Đo lợi ích

Đếm số dòng phải sửa để thêm một campaign, ở bản `if-else` trong phần 2 và ở bản interface. Ghi lại cả số file phải mở khi review.

**Gợi ý:** đừng chỉ đếm dòng thêm mới; đếm cả số dòng cũ nằm trong vùng rủi ro của thay đổi.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi chỉ ra được phần nào mở, phần nào đóng trong một thiết kế.
- [ ] Tôi xác định trục biến đổi từ lịch sử thay đổi thật, không từ phỏng đoán.
- [ ] Tôi thêm được hành vi mới bằng một class mới và một dòng đăng ký.
- [ ] Tôi giữ chính sách chung ở phần đóng thay vì lặp lại trong từng biến thể.
- [ ] Tôi biết khi nào `switch` trên tập đóng là lựa chọn tốt hơn.
- [ ] Tôi tránh được abstraction đầu cơ khi chưa có bằng chứng biến đổi.
- [ ] Tôi build/run được sample trên `net9.0` và đối chiếu đúng output.

Điều hướng:

- Bài prerequisite: [Single responsibility](./04-single-responsibility.md)
- Ôn lại nền tảng: [Pattern matching](../05-csharp-nang-cao/08-pattern-matching.md)
- Bài tiếp theo: [Liskov substitution](./06-liskov-substitution.md)
