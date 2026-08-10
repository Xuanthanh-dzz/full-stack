# Code smell và refactoring

## 1. Mục tiêu

Sau bài này, bạn có thể:

- gọi tên các code smell phổ biến bằng dấu hiệu quan sát được;
- chốt hành vi hiện tại bằng characterization test trước khi đụng vào code;
- thực hiện các refactoring có tên: Extract Method, Introduce Parameter Object, Extract Class, Move Method, Replace Conditional with Polymorphism;
- refactor theo bước nhỏ, chạy kiểm chứng sau mỗi bước;
- phân biệt refactoring (giữ nguyên hành vi) với sửa lỗi và thêm tính năng;
- quyết định khi nào **không** refactor;
- ghi lại chuỗi bước để người khác review được từng bước một.

## 2. Bài toán mở đầu

Hàm dựng nhãn vận chuyển đã tồn tại nhiều năm:

```csharp
public static string BuildLabel(
    string n, string s, string c, string z,
    decimal v, string cur, decimal w, bool ex)
{
    decimal cost = w * 10000m;
    if (cost < 20000m) { cost = 20000m; }
    if (ex) { cost += 25000m; }

    string val = v.ToString("N0") + " " + cur.ToUpperInvariant();
    string cst = cost.ToString("N0") + " " + cur.ToUpperInvariant();

    return "TO: " + n + "\n" + s + ", " + c + " " + z +
           "\nVALUE: " + val + "\nCOST: " + cst +
           (ex ? " (EXPRESS)" : " (STANDARD)");
}
```

Nó chạy đúng, và đó là điều khiến việc sửa trở nên đáng sợ. Trước khi chạm vào, hãy đọc ra các mùi:

| Mùi | Dấu hiệu trong đoạn trên |
|---|---|
| Long parameter list | tám tham số, dễ truyền nhầm thứ tự |
| Data clump | `s`, `c`, `z` luôn đi cùng nhau — đó là một địa chỉ |
| Primitive obsession | số tiền là `decimal` rời khỏi đơn vị tiền `string` |
| Duplicated code | công thức định dạng tiền lặp hai lần |
| Control coupling | `bool ex` vừa đổi chi phí vừa đổi chuỗi hiển thị |
| Mixed levels | công thức tính phí nằm chung với việc nối chuỗi |

Refactoring là quá trình **đổi cấu trúc mà không đổi hành vi**. Điều kiện tiên quyết: phải có cách biết hành vi có đổi hay không.

## 3. Lời giải bằng code

Tạo project `.NET 9`:

```bash
mkdir RefactoringDemo
cd RefactoringDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `RefactoringDemo.csproj` bằng:

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

Chương trình gồm ba phần: bản cũ giữ nguyên, bản đã refactor, và một harness đối chiếu hai bản trên nhiều trường hợp.

Thay toàn bộ `Program.cs`:

```csharp
using System.Collections.Generic;
using System.Globalization;

namespace RefactoringDemo;

// ============ Bản cũ, không sửa một ký tự ============

public static class LegacyLabelBuilder
{
    public static string BuildLabel(
        string n, string s, string c, string z,
        decimal v, string cur, decimal w, bool ex)
    {
        decimal cost = w * 10000m;
        if (cost < 20000m) { cost = 20000m; }
        if (ex) { cost += 25000m; }

        string val = v.ToString("N0", CultureInfo.InvariantCulture) + " " + cur.ToUpperInvariant();
        string cst = cost.ToString("N0", CultureInfo.InvariantCulture) + " " + cur.ToUpperInvariant();

        return "TO: " + n + "\n" + s + ", " + c + " " + z +
               "\nVALUE: " + val + "\nCOST: " + cst +
               (ex ? " (EXPRESS)" : " (STANDARD)");
    }
}

// ============ Bản đã refactor ============

// Bước 2 — Introduce Parameter Object: ba trường luôn đi cùng nhau.
public sealed record Address(string Street, string City, string PostalCode)
{
    public string ToSingleLine() => $"{Street}, {City} {PostalCode}";
}

// Bước 3 — Replace Primitive with Value Object: tiền luôn đi kèm đơn vị.
public sealed record Money(decimal Amount, string Currency)
{
    public static Money Of(decimal amount, string currency)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(amount);
        ArgumentException.ThrowIfNullOrWhiteSpace(currency);

        return new Money(amount, currency.Trim().ToUpperInvariant());
    }

    // Bước 4 — Extract Method: một chỗ duy nhất định dạng tiền.
    public override string ToString() =>
        $"{Amount.ToString("N0", CultureInfo.InvariantCulture)} {Currency}";
}

public enum DeliverySpeed
{
    Standard = 0,
    Express = 1
}

public sealed record Parcel(decimal WeightKg, DeliverySpeed Speed);

// Bước 5 — Extract Class: công thức phí tách khỏi việc dựng chuỗi.
public sealed class ShippingCostPolicy
{
    private const decimal RatePerKilogram = 10_000m;
    private const decimal MinimumCost = 20_000m;
    private const decimal ExpressSurcharge = 25_000m;

    public Money Calculate(Parcel parcel, string currency)
    {
        ArgumentNullException.ThrowIfNull(parcel);

        decimal cost = parcel.WeightKg * RatePerKilogram;
        if (cost < MinimumCost)
        {
            cost = MinimumCost;
        }

        if (parcel.Speed == DeliverySpeed.Express)
        {
            cost += ExpressSurcharge;
        }

        return Money.Of(cost, currency);
    }
}

// Bước 6 — Move Method: việc dựng nhãn thuộc về chính dữ liệu của nhãn.
public sealed record ShippingLabel(
    string Recipient,
    Address Destination,
    Money DeclaredValue,
    Money Cost,
    DeliverySpeed Speed)
{
    public string Render() =>
        $"TO: {Recipient}\n{Destination.ToSingleLine()}\n" +
        $"VALUE: {DeclaredValue}\nCOST: {Cost} ({SpeedLabel()})";

    private string SpeedLabel() => Speed switch
    {
        DeliverySpeed.Express => "EXPRESS",
        DeliverySpeed.Standard => "STANDARD",
        _ => throw new ArgumentOutOfRangeException(nameof(Speed), Speed, "Unknown speed.")
    };
}

public sealed class LabelService
{
    private readonly ShippingCostPolicy _costPolicy;

    public LabelService(ShippingCostPolicy costPolicy)
    {
        ArgumentNullException.ThrowIfNull(costPolicy);
        _costPolicy = costPolicy;
    }

    public ShippingLabel Create(string recipient, Address destination, Parcel parcel, Money declaredValue)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(recipient);
        ArgumentNullException.ThrowIfNull(destination);
        ArgumentNullException.ThrowIfNull(parcel);
        ArgumentNullException.ThrowIfNull(declaredValue);

        Money cost = _costPolicy.Calculate(parcel, declaredValue.Currency);
        return new ShippingLabel(recipient, destination, declaredValue, cost, parcel.Speed);
    }
}

// ============ Characterization harness ============

public sealed record LabelCase(
    string Recipient,
    string Street,
    string City,
    string PostalCode,
    decimal DeclaredValue,
    string Currency,
    decimal WeightKg,
    DeliverySpeed Speed);

public static class CharacterizationHarness
{
    public static (int Passed, int Failed, IReadOnlyList<string> Report) Compare(
        IReadOnlyList<LabelCase> cases,
        LabelService service)
    {
        ArgumentNullException.ThrowIfNull(cases);
        ArgumentNullException.ThrowIfNull(service);

        int passed = 0;
        int failed = 0;
        var report = new List<string>();

        foreach (LabelCase testCase in cases)
        {
            string legacy = LegacyLabelBuilder.BuildLabel(
                testCase.Recipient,
                testCase.Street,
                testCase.City,
                testCase.PostalCode,
                testCase.DeclaredValue,
                testCase.Currency,
                testCase.WeightKg,
                testCase.Speed == DeliverySpeed.Express);

            string refactored = service.Create(
                testCase.Recipient,
                new Address(testCase.Street, testCase.City, testCase.PostalCode),
                new Parcel(testCase.WeightKg, testCase.Speed),
                Money.Of(testCase.DeclaredValue, testCase.Currency)).Render();

            bool same = string.Equals(legacy, refactored, StringComparison.Ordinal);
            if (same)
            {
                passed++;
            }
            else
            {
                failed++;
            }

            report.Add($"{testCase.Recipient} / {testCase.Speed}: {(same ? "same" : "DIFFERENT")}");
        }

        return (passed, failed, report);
    }
}

internal static class Program
{
    private static void Main()
    {
        var cases = new List<LabelCase>
        {
            new("An Nguyen", "12 Le Loi", "Ha Noi", "100000", 1_850_000m, "vnd", 2.5m, DeliverySpeed.Standard),
            new("Binh Tran", "45 Tran Phu", "Da Nang", "550000", 350_000m, "VND", 0.4m, DeliverySpeed.Express),
            new("Chi Le", "7 Nguyen Hue", "Ho Chi Minh", "700000", 12_000_000m, "vnd", 18m, DeliverySpeed.Express)
        };

        var service = new LabelService(new ShippingCostPolicy());
        (int passed, int failed, IReadOnlyList<string> report) = CharacterizationHarness.Compare(cases, service);

        foreach (string line in report)
        {
            Console.WriteLine(line);
        }

        Console.WriteLine($"passed={passed}, failed={failed}");
        Console.WriteLine("--- nhãn sinh bởi bản đã refactor ---");
        Console.WriteLine(service.Create(
            "An Nguyen",
            new Address("12 Le Loi", "Ha Noi", "100000"),
            new Parcel(2.5m, DeliverySpeed.Standard),
            Money.Of(1_850_000m, "vnd")).Render());
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
An Nguyen / Standard: same
Binh Tran / Express: same
Chi Le / Express: same
passed=3, failed=0
--- nhãn sinh bởi bản đã refactor ---
TO: An Nguyen
12 Le Loi, Ha Noi 100000
VALUE: 1,850,000 VND
COST: 25,000 VND (STANDARD)
```

Project được kiểm tra bằng .NET SDK `9.0.119`, target `net9.0`, không dùng package ngoài.

## 4. Giải thích cơ chế

### Bước 1 luôn là chốt hành vi

`CharacterizationHarness` không kiểm tra hành vi **đúng**; nó kiểm tra hành vi **không đổi**. Đó là điểm khác biệt quan trọng khi làm việc với code cũ: bạn thường không biết đâu là đúng, nhưng bạn biết chắc mình không được phép làm khác đi.

Cách chọn trường hợp: mỗi nhánh điều kiện ít nhất một lần, cộng thêm các biên. Trong sample, ba trường hợp phủ: dưới ngưỡng tối thiểu (`0.4 kg`), trên ngưỡng (`2.5 kg` và `18 kg`), cả hai tốc độ, và cả hai cách viết đơn vị tiền (`"vnd"`, `"VND"`).

Trường hợp `0.4 kg` rất đáng giá: `0.4 * 10.000 = 4.000` nhỏ hơn `20.000`, nên nhánh chi phí tối thiểu được kích hoạt. Nếu bỏ sót trường hợp đó, một lỗi refactor ở nhánh này sẽ đi qua harness mà không ai biết.

### Chuỗi bước, mỗi bước một mục tiêu

| Bước | Refactoring | Mùi được xử lý |
|---|---|---|
| 1 | viết characterization harness | (điều kiện tiên quyết) |
| 2 | Introduce Parameter Object → `Address` | data clump, long parameter list |
| 3 | Replace Primitive with Value Object → `Money` | primitive obsession |
| 4 | Extract Method → `Money.ToString` | duplicated code |
| 5 | Extract Class → `ShippingCostPolicy` | mixed levels, SRP |
| 6 | Move Method → `ShippingLabel.Render` | feature envy |
| 7 | Replace flag with enum → `DeliverySpeed` | control coupling |

Sau **mỗi** bước, chạy harness. Nếu một bước làm `failed` khác `0`, bạn biết chính xác bước nào gây ra và có thể hoàn tác một thay đổi nhỏ thay vì gỡ cả buổi làm việc.

### Vì sao `Render` chuyển vào `ShippingLabel`

Trong bản cũ, hàm dựng chuỗi phải hỏi tám mảnh dữ liệu rồi tự ghép. Một method quan tâm tới dữ liệu của người khác nhiều hơn dữ liệu của chính mình là **feature envy**. Sau khi có `ShippingLabel` giữ đúng những dữ liệu đó, việc dựng chuỗi thuộc về nó.

Ranh giới cần giữ: `ShippingLabel` chỉ biết cách trình bày chính nó; nó không tính phí, không đọc cấu hình. Nếu sau này cần nhiều định dạng nhãn, hãy tách formatter như đã làm ở [bài 2](./02-encapsulation-abstraction-inheritance-polymorphism.md).

### Refactoring không phải sửa lỗi

Bản cũ có một điểm đáng ngờ: `cur.ToUpperInvariant()` được gọi hai lần và không kiểm tra `null`. Bản refactor cũng **không sửa** hành vi đó theo cách làm đổi kết quả — `Money.Of` chuẩn hóa chữ hoa y hệt. Nếu muốn thêm kiểm tra `null` chặt hơn, đó là một thay đổi hành vi và phải là một commit riêng, có mô tả riêng.

Trộn hai việc là lý do phổ biến khiến các đợt “refactor” bị đổ lỗi cho mọi sự cố sau đó.

### Đào sâu (có thể quay lại sau)

#### Replace Conditional with Polymorphism

Khi một `switch` theo loại xuất hiện ở **nhiều** nơi và cùng phân nhánh theo cùng một khái niệm, hãy chuyển hành vi vào các type — đúng cách `IDiscountRule` ở [bài 5](./05-open-closed.md).

Ngược lại, một `switch` duy nhất, tập trường hợp đóng và ổn định, như `SpeedLabel` trong sample, thì để nguyên là hợp lý. Refactoring không phải cuộc thi loại bỏ `switch`.

#### Refactor được hỗ trợ bởi công cụ

IDE thực hiện Rename, Extract Method, Introduce Parameter một cách an toàn hơn tay người vì nó hiểu ngữ nghĩa. Hãy ưu tiên dùng công cụ; dành sức tập trung cho quyết định thiết kế, không cho việc gõ lại.

#### Bảo đảm không đổi hành vi tới mức nào

Harness so sánh chuỗi kết quả trên vài trường hợp. Nó không chứng minh hai bản tương đương với mọi input. Muốn chắc hơn: sinh dữ liệu ngẫu nhiên có seed cố định và so sánh hàng nghìn trường hợp, hoặc chạy song song hai bản trên dữ liệu thật một thời gian rồi đối chiếu. Cách thứ hai gặp lại ở các module về vận hành.

#### Nợ kỹ thuật là một quyết định

Không phải mùi nào cũng phải xử lý ngay. Một module sắp bị xóa, hoặc một script chạy một lần, không đáng đầu tư. Cách quản lý nợ kỹ thuật một cách có ý thức — ghi nhận, ước lượng, xếp ưu tiên — là nội dung của [module 20](../PROGRESS.md#20-ky-nang-architect).

## 5. Kiến thức nền

### Danh mục mùi thường gặp

| Mùi | Dấu hiệu | Hướng xử lý |
|---|---|---|
| Long method | phải cuộn màn hình; có comment chia đoạn | Extract Method |
| Large class / god class | quá nhiều field không liên quan | Extract Class |
| Long parameter list | trên bốn tham số, dễ nhầm thứ tự | Introduce Parameter Object |
| Data clump | các trường luôn xuất hiện cùng nhau | Extract Class |
| Primitive obsession | `string`/`decimal` mang khái niệm nghiệp vụ | Value Object |
| Feature envy | method dùng dữ liệu người khác nhiều hơn của mình | Move Method |
| Shotgun surgery | một thay đổi phải sửa nhiều file rải rác | gom trách nhiệm về một chỗ |
| Divergent change | một file bị sửa vì nhiều lý do khác nhau | tách theo SRP |
| Duplicated code | cùng logic ở hai nơi | Extract Method / Extract Class |
| Speculative generality | abstraction không có người dùng thứ hai | xóa bớt tầng |
| Temporary field | field chỉ có giá trị trong vài trường hợp | tách type hoặc chuyển thành tham số |
| Message chain | `a.B.C.D` | hỏi đúng object |

`Shotgun surgery` và `divergent change` là cặp đối lập đáng nhớ: một bên là thay đổi lan ra quá nhiều file, một bên là quá nhiều lý do đổ vào một file.

### Quy trình refactor an toàn

1. Chốt hành vi: characterization test hoặc harness so sánh.
2. Chọn **một** mùi, **một** refactoring.
3. Thực hiện bước nhỏ nhất có thể build được.
4. Chạy kiểm chứng.
5. Commit với thông điệp nói rõ đây là refactor.
6. Lặp lại.

Nếu bước 4 hỏng, hoàn tác bước 3 chứ đừng sửa chồng lên.

### Refactoring, sửa lỗi và tính năng

| Loại thay đổi | Hành vi quan sát được | Commit |
|---|---|---|
| Refactoring | không đổi | riêng, dễ review |
| Sửa lỗi | đổi ở trường hợp sai | riêng, kèm test tái hiện |
| Tính năng mới | thêm hành vi | riêng |

Trộn ba loại vào một commit làm review mất tác dụng và làm việc tìm nguyên nhân sự cố khó gấp nhiều lần.

### Khi nào không refactor

- Sắp có deadline và thay đổi không cần thiết cho mục tiêu.
- Module sắp bị thay thế.
- Chưa có cách kiểm chứng hành vi và cũng không có cách tạo ra nó.
- Bạn chưa hiểu code đủ để dự đoán hậu quả — hãy đọc và viết test đặc tả trước.

## 6. Lỗi thường gặp

### Refactor không có lưới an toàn

Không có test, không có harness, chỉ có “tôi chắc là tương đương”. Đây là nguyên nhân số một của các sự cố sau khi dọn code.

### Bước quá lớn

Đổi mười thứ rồi mới chạy. Khi kết quả sai, không ai biết bắt đầu từ đâu. Bước nhỏ tới mức “build được và chạy được” là đủ nhỏ.

### Refactor kèm đổi hành vi “tiện tay”

“Nhân tiện tôi sửa luôn lỗi làm tròn.” Sau đó không ai biết sự khác biệt đến từ đâu. Ghi lại lỗi vừa phát hiện, làm ở commit sau.

### Chạy theo danh mục mùi một cách máy móc

Không phải mọi `switch` đều phải thành polymorphism, không phải mọi method dài đều phải cắt. Mùi là **gợi ý điều tra**, không phải mệnh lệnh.

### Refactor mà không đọc caller

Đổi chữ ký hoặc ngữ nghĩa giá trị trả về có thể phá caller ở nơi khác. Tìm hết caller trước; đó là lúc IDE và trình biên dịch giúp bạn nhiều nhất.

### Đặt tên mới nhưng giữ khái niệm cũ

Đổi `Do` thành `Process` không giải quyết gì nếu method vẫn làm năm việc. Tên tốt phải mô tả một trách nhiệm; nếu không đặt được tên, hãy tách trước rồi đặt tên sau.

### Tạo abstraction trong lúc refactor

Refactoring là đổi cấu trúc cho phù hợp với hiện tại, không phải dịp để chuẩn bị cho tương lai tưởng tượng. Speculative generality cũng là một mùi.

## 7. Bài tập

### Bài 1 — Đọc mùi

Với đoạn code ở phần 2, viết lại danh sách mùi bằng lời của bạn và xếp thứ tự nên xử lý. Giải thích thứ tự.

**Gợi ý:** thường nên bắt đầu từ refactoring có rủi ro thấp nhất và mở đường cho các bước sau.

### Bài 2 — Thêm trường hợp cho harness

Bổ sung ít nhất ba trường hợp: khối lượng đúng bằng ngưỡng tối thiểu, giá trị khai báo bằng `0`, và một tên người nhận có dấu tiếng Việt.

**Gợi ý:** trường hợp đúng bằng biên là nơi lỗi hay ẩn nấp; `0.4` và `2.0` cho hai nhánh khác nhau.

### Bài 3 — Refactor từng bước

Bắt đầu từ bản cũ trong một file riêng, thực hiện lần lượt bảy bước ở bảng và chạy harness sau mỗi bước. Ghi lại bước nào suýt làm đổi hành vi.

**Gợi ý:** bước `Money` dễ làm đổi định dạng nhất; chú ý `CultureInfo` và việc viết hoa đơn vị.

### Bài 4 — Feature envy khác

Tìm trong các bài trước của module này một method dùng dữ liệu của object khác nhiều hơn của chính mình và đề xuất Move Method.

**Gợi ý:** xem lại các calculator; method nào phải hỏi hơn hai property của cùng một object?

### Bài 5 — Quyết định không refactor

Chọn một đoạn code có mùi rõ nhưng bạn cho rằng không nên sửa lúc này. Viết ba câu lý do và điều kiện để xem xét lại.

**Gợi ý:** điều kiện nên cụ thể, ví dụ “khi có yêu cầu thứ hai chạm vào file này”.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi gọi tên được các mùi bằng dấu hiệu quan sát được.
- [ ] Tôi luôn chốt hành vi trước khi refactor.
- [ ] Tôi thực hiện từng refactoring có tên, mỗi lần một mục tiêu.
- [ ] Tôi chạy kiểm chứng sau mỗi bước nhỏ và biết cách hoàn tác.
- [ ] Tôi không trộn refactoring với sửa lỗi hay thêm tính năng.
- [ ] Tôi nêu được trường hợp không nên refactor.
- [ ] Tôi build/run được sample trên `net9.0` và đối chiếu đúng output.

Điều hướng:

- Bài prerequisite: [Clean code: tên, hàm và cấu trúc](./11-clean-code-ten-ham-va-cau-truc.md)
- Ôn lại nền tảng: [Record, `init`, `required` và tính bất biến](../05-csharp-nang-cao/07-record-init-required-va-immutability.md)
- Bài tiếp theo: [Design by contract và invariant](./13-design-by-contract-va-invariant.md)
