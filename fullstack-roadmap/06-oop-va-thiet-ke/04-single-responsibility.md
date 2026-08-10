# Single responsibility

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phát biểu SRP theo “một lý do để thay đổi” và chỉ ra lý do đó thuộc về ai;
- nhận diện god class bằng các dấu hiệu quan sát được, không bằng cảm tính;
- tách một quy trình lớn thành các type có trách nhiệm rời nhau nhưng vẫn ghép được;
- giữ lại một type điều phối mà không biến nó thành god class mới;
- giải thích vì sao SRP không có nghĩa là “mỗi class một method”;
- đo lợi ích bằng câu hỏi “yêu cầu này đổi thì phải sửa mấy file”;
- tránh tách quá tay tới mức mỗi thay đổi phải chạm mười file.

## 2. Bài toán mở đầu

Sau vài tháng, phần xử lý đặt hàng của cửa hàng gom về một class duy nhất:

```csharp
public sealed class OrderService
{
    public string PlaceOrder(string rawInput)
    {
        // 1. tách chuỗi "SKU:số lượng:đơn giá" từ form nhập
        // 2. kiểm tra dữ liệu
        // 3. tính tạm tính, chiết khấu theo bậc, thuế 8%
        // 4. dựng chuỗi chứng từ
        // 5. ghi chứng từ xuống ổ đĩa
        // 6. gửi email cho khách
        // 7. ghi log cho vận hành
        return "...";
    }
}
```

Class này chạy đúng. Vấn đề xuất hiện khi có yêu cầu thay đổi:

- Kế toán đổi thuế suất từ `8%` sang `10%` → phải sửa `OrderService`.
- Marketing đổi bậc chiết khấu → phải sửa `OrderService`.
- Bộ phận chăm sóc khách đổi bố cục chứng từ → phải sửa `OrderService`.
- Vận hành muốn chứng từ lưu lên object storage thay vì ổ đĩa → phải sửa `OrderService`.

Bốn nhóm người khác nhau, bốn lịch thay đổi khác nhau, nhưng cùng chạm vào một file. Hệ quả rất cụ thể: hai thay đổi song song đụng nhau khi merge; sửa công thức thuế lại làm hỏng bố cục chứng từ; và muốn kiểm thử công thức chiết khấu thì phải chấp nhận nó ghi file và gửi email.

Single Responsibility Principle nói đúng về tình huống này: **một module chỉ nên có một lý do để thay đổi**, và “lý do” gắn với một nhóm người dùng/nghiệp vụ, không phải với số dòng code.

## 3. Lời giải bằng code

Tạo project `.NET 9`:

```bash
mkdir SingleResponsibilityDemo
cd SingleResponsibilityDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `SingleResponsibilityDemo.csproj` bằng:

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

Bản tách dưới đây giữ nguyên hành vi, chỉ đổi chỗ ở của từng phần. Nơi lưu chứng từ dùng bản in-memory để chạy được ở mọi máy; bản ghi file thật chỉ khác ở một class.

Thay toàn bộ `Program.cs`:

```csharp
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace SingleResponsibilityDemo;

public sealed record OrderLine(string Sku, int Quantity, decimal UnitPrice)
{
    public decimal LineTotal => Quantity * UnitPrice;
}

public sealed record PriceBreakdown(
    decimal Subtotal,
    decimal Discount,
    decimal Tax,
    decimal Total);

// Trách nhiệm 1: đọc dữ liệu thô thành model. Đổi khi định dạng nhập liệu đổi.
public sealed class OrderLineParser
{
    public IReadOnlyList<OrderLine> Parse(string rawInput)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(rawInput);

        var lines = new List<OrderLine>();
        foreach (string entry in rawInput.Split(';', StringSplitOptions.RemoveEmptyEntries))
        {
            string[] parts = entry.Split(':');
            if (parts.Length != 3)
            {
                throw new FormatException($"Invalid entry '{entry}'; expected sku:qty:price.");
            }

            string sku = parts[0].Trim().ToUpperInvariant();
            int quantity = int.Parse(parts[1], CultureInfo.InvariantCulture);
            decimal unitPrice = decimal.Parse(parts[2], CultureInfo.InvariantCulture);

            if (quantity <= 0 || unitPrice < 0m)
            {
                throw new FormatException($"Invalid numbers in entry '{entry}'.");
            }

            lines.Add(new OrderLine(sku, quantity, unitPrice));
        }

        if (lines.Count == 0)
        {
            throw new FormatException("An order needs at least one line.");
        }

        return lines;
    }
}

// Trách nhiệm 2: quy tắc tiền. Đổi khi kế toán hoặc marketing đổi chính sách.
public sealed class PricingPolicy
{
    private readonly decimal _taxRate;
    private readonly decimal _discountThreshold;
    private readonly decimal _discountRate;

    public PricingPolicy(decimal taxRate, decimal discountThreshold, decimal discountRate)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(taxRate);
        ArgumentOutOfRangeException.ThrowIfNegative(discountThreshold);
        ArgumentOutOfRangeException.ThrowIfNegative(discountRate);

        _taxRate = taxRate;
        _discountThreshold = discountThreshold;
        _discountRate = discountRate;
    }

    public PriceBreakdown Calculate(IReadOnlyList<OrderLine> lines)
    {
        ArgumentNullException.ThrowIfNull(lines);

        decimal subtotal = 0m;
        foreach (OrderLine line in lines)
        {
            subtotal += line.LineTotal;
        }

        decimal discount = subtotal >= _discountThreshold
            ? decimal.Round(subtotal * _discountRate, 0)
            : 0m;

        decimal taxable = subtotal - discount;
        decimal tax = decimal.Round(taxable * _taxRate, 0);

        return new PriceBreakdown(subtotal, discount, tax, taxable + tax);
    }
}

// Trách nhiệm 3: trình bày. Đổi khi bố cục chứng từ đổi.
public sealed class ReceiptFormatter
{
    public string Format(string orderId, IReadOnlyList<OrderLine> lines, PriceBreakdown price)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(orderId);
        ArgumentNullException.ThrowIfNull(lines);
        ArgumentNullException.ThrowIfNull(price);

        var builder = new StringBuilder();
        builder.AppendLine($"RECEIPT {orderId}");

        foreach (OrderLine line in lines)
        {
            builder.AppendLine($"  {line.Sku} x{line.Quantity} = {line.LineTotal:N0}");
        }

        builder.AppendLine($"  subtotal: {price.Subtotal:N0}");
        builder.AppendLine($"  discount: {price.Discount:N0}");
        builder.AppendLine($"  tax:      {price.Tax:N0}");
        builder.Append($"  total:    {price.Total:N0}");
        return builder.ToString();
    }
}

// Trách nhiệm 4: lưu trữ. Đổi khi hạ tầng lưu trữ đổi.
public interface IReceiptStore
{
    void Save(string orderId, string content);
}

public sealed class InMemoryReceiptStore : IReceiptStore
{
    private readonly Dictionary<string, string> _saved = new(StringComparer.Ordinal);

    public IReadOnlyDictionary<string, string> Saved => _saved;

    public void Save(string orderId, string content)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(orderId);
        ArgumentNullException.ThrowIfNull(content);

        _saved[orderId] = content;
    }
}

// Trách nhiệm 5: điều phối một use case. Đổi khi các BƯỚC của quy trình đổi.
public sealed class PlaceOrderUseCase
{
    private readonly OrderLineParser _parser;
    private readonly PricingPolicy _pricing;
    private readonly ReceiptFormatter _formatter;
    private readonly IReceiptStore _store;

    public PlaceOrderUseCase(
        OrderLineParser parser,
        PricingPolicy pricing,
        ReceiptFormatter formatter,
        IReceiptStore store)
    {
        ArgumentNullException.ThrowIfNull(parser);
        ArgumentNullException.ThrowIfNull(pricing);
        ArgumentNullException.ThrowIfNull(formatter);
        ArgumentNullException.ThrowIfNull(store);

        _parser = parser;
        _pricing = pricing;
        _formatter = formatter;
        _store = store;
    }

    public string Execute(string orderId, string rawInput)
    {
        IReadOnlyList<OrderLine> lines = _parser.Parse(rawInput);
        PriceBreakdown price = _pricing.Calculate(lines);
        string receipt = _formatter.Format(orderId, lines, price);
        _store.Save(orderId, receipt);
        return receipt;
    }
}

internal static class Program
{
    private static void Main()
    {
        var store = new InMemoryReceiptStore();
        var useCase = new PlaceOrderUseCase(
            new OrderLineParser(),
            new PricingPolicy(taxRate: 0.08m, discountThreshold: 1_000_000m, discountRate: 0.05m),
            new ReceiptFormatter(),
            store);

        Console.WriteLine(useCase.Execute("ORD-001", "keyboard:2:750000;mouse:1:350000"));
        Console.WriteLine($"Stored receipts: {store.Saved.Count}");

        // Kế toán đổi thuế suất: chỉ đổi tham số của PricingPolicy, không đụng class nào khác.
        var pricing = new PricingPolicy(taxRate: 0.10m, discountThreshold: 1_000_000m, discountRate: 0.05m);
        PriceBreakdown recalculated = pricing.Calculate(new[]
        {
            new OrderLine("KEYBOARD", 2, 750_000m),
            new OrderLine("MOUSE", 1, 350_000m)
        });

        Console.WriteLine($"Tax at 10%: {recalculated.Tax:N0}, total: {recalculated.Total:N0}");

        // Kiểm thử quy tắc tiền không cần file, không cần email, không cần chuỗi nhập liệu.
        PriceBreakdown small = pricing.Calculate(new[] { new OrderLine("CABLE", 1, 50_000m) });
        Console.WriteLine($"No discount under threshold: {small.Discount:N0}");

        try
        {
            useCase.Execute("ORD-002", "keyboard:0:750000");
        }
        catch (FormatException ex)
        {
            Console.WriteLine($"Rejected by parser: {ex.Message}");
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
RECEIPT ORD-001
  KEYBOARD x2 = 1,500,000
  MOUSE x1 = 350,000
  subtotal: 1,850,000
  discount: 92,500
  tax:      140,600
  total:    1,898,100
Stored receipts: 1
Tax at 10%: 175,750, total: 1,933,250
No discount under threshold: 0
Rejected by parser: Invalid numbers in entry 'keyboard:0:750000'.
```

Project được kiểm tra bằng .NET SDK `9.0.119`, target `net9.0`, không dùng package ngoài.

## 4. Giải thích cơ chế

### “Lý do để thay đổi” gắn với một nhóm người

Cách kiểm tra SRP có tính thao tác: lập bảng từ nguồn thay đổi tới file phải sửa.

| Ai yêu cầu | Thay đổi gì | Trước khi tách | Sau khi tách |
|---|---|---|---|
| Kế toán | thuế suất | `OrderService` | `PricingPolicy` |
| Marketing | bậc chiết khấu | `OrderService` | `PricingPolicy` |
| Chăm sóc khách | bố cục chứng từ | `OrderService` | `ReceiptFormatter` |
| Vận hành | nơi lưu chứng từ | `OrderService` | một implementation của `IReceiptStore` |
| Frontend | định dạng chuỗi nhập | `OrderService` | `OrderLineParser` |

Cột “trước” chỉ có một ô lặp lại năm lần — đó chính là định nghĩa vi phạm SRP. Kế toán và marketing cùng rơi vào `PricingPolicy`; nếu hai bên thường xuyên đổi độc lập và đụng nhau, đó là tín hiệu tách tiếp thành `TaxPolicy` và `DiscountPolicy`. SRP không cấm gộp; nó chỉ yêu cầu bạn tách khi các lý do thực sự khác nhau về nhịp và nguồn.

### Điều phối cũng là một trách nhiệm

`PlaceOrderUseCase.Execute` có bốn dòng và không chứa quy tắc nghiệp vụ nào. Trách nhiệm của nó là **thứ tự các bước**: parse → tính tiền → định dạng → lưu. Nếu ngày mai quy trình thêm bước “kiểm tra tồn kho”, chỉ file này đổi.

Ranh giới cần giữ: khi bạn thấy công thức tính tiền hoặc chuỗi định dạng bắt đầu xuất hiện trong `Execute`, class điều phối đang trên đường trở thành god class mới.

### Tách xong thì test dễ hơn ở đâu

Trước khi tách, muốn kiểm tra công thức chiết khấu thì phải chạy cả quy trình, tức là phải có chuỗi nhập đúng định dạng, phải ghi được file và phải gửi được email. Sau khi tách:

```csharp
PriceBreakdown small = pricing.Calculate(new[] { new OrderLine("CABLE", 1, 50_000m) });
```

Một dòng, không I/O, không phụ thuộc gì khác. Đó là lý do SRP thường được nhắc chung với khả năng kiểm thử. Công cụ test chuẩn sẽ học ở [module 14](../PROGRESS.md#14-testing-chat-luong); ở đây `Main` đóng vai người gọi thử.

### Sơ đồ phụ thuộc sau khi tách

```text
                     PlaceOrderUseCase
                      │      │      │      │
        ┌─────────────┘      │      │      └─────────────┐
        ▼                    ▼      ▼                    ▼
OrderLineParser      PricingPolicy  ReceiptFormatter   IReceiptStore
   (định dạng           (quy tắc       (trình bày)      (hạ tầng)
    nhập liệu)           tiền)                              │
                                                            ▼
                                                  InMemoryReceiptStore
```

Bốn nhánh không biết gì về nhau: `PricingPolicy` không biết có chứng từ, `ReceiptFormatter` không biết chứng từ được lưu ở đâu. Chỉ `PlaceOrderUseCase` biết cả bốn, và nó là nơi duy nhất phải sửa khi trình tự đổi.

### Đào sâu (có thể quay lại sau)

#### SRP không phải “mỗi class một method”

`PricingPolicy` có một method công khai, nhưng `InMemoryReceiptStore` có thể có `Save`, `Load`, `Delete` mà vẫn đúng SRP: cả ba cùng phục vụ một trách nhiệm là lưu trữ chứng từ, và cùng đổi khi hạ tầng lưu trữ đổi.

Ngược lại, một class chỉ có một method vẫn có thể vi phạm SRP nếu method đó vừa tính tiền vừa gửi email.

#### SRP ở nhiều mức

Cùng một câu hỏi áp dụng cho method, class, namespace, project và service. Ở mức method, “một trách nhiệm” thường có nghĩa là “một mức trừu tượng” — nội dung của [bài 11](./11-clean-code-ten-ham-va-cau-truc.md). Ở mức project và service, nó dẫn tới bounded context và cách chia microservice ở [module 17](../PROGRESS.md#17-kien-truc-phan-mem).

#### Vì sao `IReceiptStore` là interface còn ba cái kia thì không

Chỉ phần chạm tới thế giới bên ngoài mới cần thay được: ổ đĩa, object storage, hay bộ nhớ trong test. Ba class còn lại là logic thuần, chạy nhanh và tất định, nên chưa cần abstraction. Nguyên tắc chọn chỗ đặt interface là nội dung của [bài 8](./08-dependency-inversion.md).

#### Chi phí của việc tách

Tách tạo thêm file, thêm tên phải nhớ, thêm chỗ nối dây trong `Main`. Với một script dùng một lần, chi phí đó không đáng bỏ ra. SRP có giá trị khi code còn sống lâu và có nhiều người cùng sửa.

## 5. Kiến thức nền

### Dấu hiệu quan sát được của god class

- Tên chứa `Manager`, `Helper`, `Util`, `Processor` mà không nói được nó quản lý cái gì.
- `using` gom đủ thứ: I/O, mạng, serialize, tiền tệ.
- Lịch sử Git cho thấy file bị sửa bởi nhiều nhóm với lý do khác nhau.
- Muốn viết một test nhỏ thì phải chuẩn bị rất nhiều thứ không liên quan.
- Danh sách field trộn lẫn state nghiệp vụ với handle hạ tầng.

Dấu hiệu cuối cùng là dấu hiệu mạnh nhất: một class giữ cả `decimal _taxRate` lẫn `FileStream _stream` gần như chắc chắn có hai lý do để thay đổi.

### Ba loại trách nhiệm hay bị trộn

| Loại | Ví dụ | Đặc điểm |
|---|---|---|
| Quy tắc nghiệp vụ | tính thuế, chiết khấu, kiểm tra trạng thái | thuần, tất định, dễ test |
| Trình bày | chứng từ text, CSV, JSON | phụ thuộc người xem |
| Hạ tầng | file, database, mạng, đồng hồ | chậm, có thể lỗi, khó test |

Giữ ba loại này ở ba nơi khác nhau là phần lớn giá trị thực tế của SRP.

### Cohesion là mặt còn lại của SRP

Một class có trách nhiệm rõ thường có cohesion cao: các method của nó dùng chung phần lớn field. Nếu nửa số method chỉ đụng `_taxRate` còn nửa kia chỉ đụng `_stream`, class đó đang là hai class dán lại. [Bài 9](./09-coupling-va-cohesion.md) sẽ định lượng ý này.

### Cách tách an toàn

1. Đặt tên cho từng trách nhiệm bạn thấy, ngay trong comment.
2. Nhóm các method và field theo tên vừa đặt.
3. Trích một nhóm thành class mới, để class cũ gọi sang.
4. Chạy lại chương trình, so sánh output với bản trước.
5. Lặp lại cho nhóm tiếp theo.

Từng bước nhỏ giữ cho hành vi không đổi. Kỹ thuật refactor có kỷ luật là nội dung của [bài 12](./12-code-smell-va-refactoring.md).

## 6. Lỗi thường gặp

### Tách theo tầng kỹ thuật mà quên nguồn thay đổi

Chia thành `Models`, `Services`, `Helpers` rồi coi là xong SRP. Nếu `OrderService` vẫn chứa cả thuế lẫn định dạng chứng từ, việc đổi thư mục không giải quyết gì.

### Tách quá tay

Mỗi công thức một class, mỗi class một method một dòng. Khi đó một thay đổi nhỏ phải mở mười file, và người đọc không thấy được bức tranh chung. Nếu hai type luôn đổi cùng nhau, chúng nên ở cùng một chỗ.

### Class điều phối phình ra

`PlaceOrderUseCase` bắt đầu chứa `if` về loại khách, rồi công thức phụ, rồi định dạng riêng cho một đối tác. Hãy đẩy các quy tắc đó về đúng type sở hữu chúng và giữ use case chỉ còn trình tự.

### Trộn quyết định với thực thi

Một method vừa quyết định “có nên giảm giá không” vừa thực hiện “ghi log và gửi mail” thì không thể kiểm tra quyết định mà không gây side effect. Hãy để phần quyết định trả về dữ liệu, phần thực thi nhận dữ liệu đó.

### Coi DTO/record là vi phạm SRP vì “không có hành vi”

`PriceBreakdown` chỉ mang dữ liệu và đó là đúng vai của nó: kết quả của một phép tính. SRP nói về lý do thay đổi, không đòi mọi type phải có method.

### Tách nhưng vẫn dính qua state chung

Nếu `PricingPolicy` và `ReceiptFormatter` cùng đọc/ghi một `static` chung, chúng vẫn phải đổi cùng nhau. Tách thật sự nghĩa là dữ liệu đi qua parameter và giá trị trả về, không đi qua biến toàn cục.

### Dùng SRP để biện minh cho việc viết lại tất cả

Không cần tách một file chỉ vì nó dài. Hãy đợi tới khi có lý do thay đổi thứ hai xuất hiện thật, hoặc khi bạn thấy hai nhóm người liên tục đụng cùng một chỗ.

## 7. Bài tập

### Bài 1 — Lập bảng nguồn thay đổi

Với `OrderService` ở phần 2, viết bảng “ai yêu cầu → đổi gì → sửa ở đâu” cho ít nhất năm thay đổi và chỉ ra ô nào lặp lại.

**Gợi ý:** thêm một cột “bao lâu đổi một lần”; hai lý do có nhịp rất khác nhau là tín hiệu tách mạnh.

### Bài 2 — Tách thuế khỏi chiết khấu

Chia `PricingPolicy` thành `TaxPolicy` và `DiscountPolicy`, giữ nguyên output của chương trình.

**Gợi ý:** quyết định trước thứ tự áp dụng và viết nó vào tên method; kiểm tra lại `total` không đổi.

### Bài 3 — Thêm bước vào use case

Thêm bước kiểm tra tồn kho trước khi tính tiền, dùng một type mới. Chỉ được sửa `PlaceOrderUseCase` và thêm file mới.

**Gợi ý:** nếu bạn buộc phải sửa `PricingPolicy`, hãy xem lại ranh giới trách nhiệm giữa hai bước.

### Bài 4 — Store ghi file

Viết `FileReceiptStore` implement `IReceiptStore`, ghi vào thư mục tạm. Chương trình chính không được sửa quá một dòng.

**Gợi ý:** ghi ra file tạm rồi đổi tên là kỹ thuật đã dùng ở [module 05, bài 19](../05-csharp-nang-cao/19-du-an-xu-ly-du-lieu-bat-dong-bo.md).

### Bài 5 — Nhận diện god class thật

Tìm trong code cũ của bạn (hoặc project ở module 04/05) một class có từ hai lý do thay đổi trở lên. Viết kế hoạch tách năm bước theo phần kiến thức nền, không cần thực hiện.

**Gợi ý:** dùng lịch sử Git để xem ai đã sửa file đó và vì sao.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phát biểu SRP theo lý do thay đổi và gắn nó với một nhóm người.
- [ ] Tôi lập được bảng “nguồn thay đổi → file phải sửa”.
- [ ] Tôi tách được quy tắc nghiệp vụ khỏi trình bày và khỏi hạ tầng.
- [ ] Tôi giữ được class điều phối chỉ chứa trình tự các bước.
- [ ] Tôi hiểu SRP không đồng nghĩa với “một class một method”.
- [ ] Tôi nêu được chi phí của việc tách và biết khi nào chưa nên tách.
- [ ] Tôi build/run được sample trên `net9.0` và đối chiếu đúng output.

Điều hướng:

- Bài prerequisite: [Composition over inheritance](./03-composition-over-inheritance.md)
- Ôn lại nền tảng: [Method, parameter và return](../04-csharp-co-ban/04-method-parameter-va-return.md)
- Bài tiếp theo: [Open/closed](./05-open-closed.md)
