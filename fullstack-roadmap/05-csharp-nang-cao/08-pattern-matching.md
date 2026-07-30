# Pattern matching trong C#

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng `is` pattern để vừa kiểm tra type/null vừa tạo biến đã được narrow type;
- dùng `switch` expression để ánh xạ input thành kết quả mà không mutate biến tạm;
- kết hợp constant, type, property, relational và logical pattern;
- destructure positional record bằng positional pattern;
- kiểm tra hình dạng array bằng list pattern;
- dùng guard `when` khi một điều kiện không biểu diễn gọn bằng pattern;
- sắp xếp các arm từ cụ thể đến tổng quát và nhận biết arm không thể tới;
- thiết kế nhánh mặc định có chủ đích thay vì âm thầm trả kết quả sai.

## 2. Bài toán mở đầu

Dịch vụ vận chuyển nhận nhiều loại kiện hàng. Giá và thời gian phụ thuộc đồng thời vào runtime type, cân nặng, cờ giao nhanh, quốc gia và hình dạng danh sách kiện con.

Nếu viết một chuỗi dài `if`, cast rồi lặp lại truy cập property, code dễ gặp ba lỗi:

1. cast sai type hoặc quên kiểm tra `null`;
2. nhánh tổng quát đặt trước che nhánh đặc biệt;
3. thêm subtype mới nhưng vô tình trả mức giá mặc định không hợp lệ.

Ta sẽ mô hình hóa mỗi loại shipment bằng record bất biến từ bài trước và dùng pattern matching để vừa kiểm tra hình dạng dữ liệu, vừa bind biến cần tính giá.

## 3. Lời giải bằng code

Tạo project:

```bash
mkdir PatternShippingDemo
cd PatternShippingDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `PatternShippingDemo.csproj` bằng:

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
namespace PatternShippingDemo;

public abstract record Shipment(string Id);

public sealed record DomesticShipment(
    string Id,
    decimal WeightKg,
    bool Express) : Shipment(Id);

public sealed record InternationalShipment(
    string Id,
    decimal WeightKg,
    string CountryCode,
    decimal DeclaredValue) : Shipment(Id);

public sealed record BulkShipment(
    string Id,
    decimal[] ItemWeights) : Shipment(Id);

public sealed record ShippingQuote(string Service, decimal Fee, int Days);

public static class ShippingCalculator
{
    public static ShippingQuote Quote(Shipment? shipment) => shipment switch
    {
        // Constant pattern xử lý null trước khi đọc property.
        null => throw new ArgumentNullException(nameof(shipment)),

        // Property + relational/logical pattern từ chối dữ liệu sai trước.
        DomesticShipment { WeightKg: <= 0m } =>
            throw new ArgumentOutOfRangeException(nameof(shipment), "Weight must be positive."),

        // Positional pattern gọi Deconstruct do positional record sinh ra.
        DomesticShipment(_, <= 2m, true) =>
            new ShippingQuote("Domestic Express", 55_000m, 1),

        DomesticShipment(_, > 0m and <= 10m, false) =>
            new ShippingQuote("Domestic Standard", 60_000m, 3),

        InternationalShipment { WeightKg: <= 0m } =>
            throw new ArgumentOutOfRangeException(nameof(shipment), "Weight must be positive."),

        // Type/property pattern bind cả object vào biến named.
        InternationalShipment
        {
            CountryCode: "TH",
            DeclaredValue: > 10_000_000m
        } named => new ShippingQuote(
            $"Insured {named.CountryCode}",
            280_000m,
            4),

        InternationalShipment { WeightKg: > 0m and <= 20m } international
            when IsSupportedCountry(international.CountryCode) =>
            new ShippingQuote("International", 220_000m, 7),

        // [] là list pattern cho array rỗng; [a, b] yêu cầu đúng hai phần tử.
        BulkShipment { ItemWeights: null } =>
            throw new ArgumentException("Item weights are required.", nameof(shipment)),

        BulkShipment { ItemWeights: [] } =>
            throw new ArgumentException("Bulk shipment cannot be empty.", nameof(shipment)),

        BulkShipment bulk when !AllPositive(bulk.ItemWeights) =>
            throw new ArgumentOutOfRangeException(
                nameof(shipment),
                "Every item weight must be positive."),

        BulkShipment { ItemWeights: [> 0m, > 0m] } bulk =>
            new ShippingQuote("Two-piece Bulk", 70_000m, 3),

        BulkShipment { ItemWeights: [_, ..] } bulk
            when AllPositive(bulk.ItemWeights) =>
            new ShippingQuote("Multi-piece Bulk", 40_000m * bulk.ItemWeights.Length, 4),

        // Không im lặng định giá input chưa được policy hỗ trợ.
        _ => throw new NotSupportedException(
            $"Shipment '{shipment.Id}' does not match a supported pricing rule.")
    };

    public static string Describe(Shipment shipment)
    {
        ArgumentNullException.ThrowIfNull(shipment);

        // Declaration pattern vừa kiểm tra type vừa tạo biến domestic.
        return shipment is DomesticShipment { Express: true } domestic
            ? $"{domestic.Id} is an express domestic shipment"
            : $"{shipment.Id} is not express domestic";
    }

    private static bool IsSupportedCountry(string countryCode) =>
        countryCode is "TH" or "SG" or "JP";

    private static bool AllPositive(decimal[] weights)
    {
        foreach (decimal weight in weights)
        {
            if (weight <= 0m)
            {
                return false;
            }
        }

        return true;
    }
}

internal static class Program
{
    private static void Main()
    {
        Shipment[] shipments =
        [
            new DomesticShipment("D-001", 1.5m, Express: true),
            new DomesticShipment("D-002", 8m, Express: false),
            new InternationalShipment("I-001", 5m, "TH", 12_000_000m),
            new BulkShipment("B-001", [1m, 2m])
        ];

        foreach (Shipment shipment in shipments)
        {
            ShippingQuote quote = ShippingCalculator.Quote(shipment);
            Console.WriteLine(
                $"{shipment.Id}: {quote.Service}, {quote.Fee:N0} VND, {quote.Days} day(s)");
        }

        Console.WriteLine(ShippingCalculator.Describe(shipments[0]));
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Output chính:

```text
D-001: Domestic Express, 55,000 VND, 1 day(s)
D-002: Domestic Standard, 60,000 VND, 3 day(s)
I-001: Insured TH, 280,000 VND, 4 day(s)
B-001: Two-piece Bulk, 70,000 VND, 3 day(s)
D-001 is an express domestic shipment
```

Phân cách hàng nghìn phụ thuộc locale.

## 4. Giải thích cơ chế

### Pattern kiểm tra rồi bind trong một bước

Biểu thức:

```csharp
shipment is DomesticShipment { Express: true } domestic
```

thực hiện ba việc logic:

```text
shipment reference
      │
      ├─ null? --------------------------> pattern false
      ├─ runtime type DomesticShipment? -> nếu không: false
      ├─ property Express == true? ------> nếu không: false
      └─ đúng hết: domestic nhận cùng reference tới object
```

Pattern không clone object. `shipment` và `domestic` cùng trỏ một `DomesticShipment`; compiler chỉ narrow static type của biến trong vùng pattern chắc chắn đúng.

### `switch` expression chọn arm đầu tiên khớp

Runtime đánh giá input một lần rồi thử arm theo thứ tự source. Vì vậy nhánh invalid/cụ thể phải đứng trước nhánh rộng hơn. Với `InternationalShipment` từ Thái Lan có giá trị cao, arm insured khớp trước arm international thông thường.

Mỗi arm trả một `ShippingQuote`, nên toàn biểu thức có một kết quả. Compiler kiểm tra type của các kết quả, phát hiện một số arm không thể tới và cảnh báo khi switch trên type đóng như enum chưa exhaustive. Với hierarchy class mở, `_` vẫn cần policy rõ ràng.

### Property, positional và list pattern

- `{ WeightKg: > 0m and <= 10m }` đọc property rồi kết hợp hai relational pattern bằng `and`.
- `DomesticShipment(_, <= 2m, true)` dùng `Deconstruct` do positional record sinh; `_` bỏ qua `Id`.
- `ItemWeights: null` tách input thiếu collection khỏi các shape array hợp lệ.
- `ItemWeights: []` chỉ khớp array không có phần tử.
- `ItemWeights: [> 0m, > 0m]` chỉ khớp đúng hai phần tử và cả hai dương.
- `[_, ..]` nghĩa là có ít nhất một phần tử; `..` là slice pattern bỏ qua phần còn lại.

Pattern nên diễn tả **shape**. Điều kiện phải lặp toàn bộ array được đặt trong guard `when AllPositive(...)` vì không có pattern ngắn gọn để nói “mọi phần tử đều dương”.

## 5. Kiến thức nền

### Nhóm pattern cốt lõi

| Nhóm | Ví dụ | Ý nghĩa |
|---|---|---|
| constant | `x is null`, `code is "TH"` | bằng một constant |
| declaration/type | `x is Order order` | đúng type và bind biến |
| relational | `amount is > 0m` | so sánh `<`, `<=`, `>`, `>=` |
| logical | `x is >= 0 and <= 100` | kết hợp `and`, `or`, `not` |
| property | `order is { Status: Paid }` | match property lồng nhau |
| positional | `point is (0, var y)` | gọi `Deconstruct` |
| list | `items is [var first, ..]` | match Count/indexer theo hình dạng |
| discard | `_` | luôn khớp, không bind |

`var x` pattern cũng luôn khớp, kể cả input `null`, rồi bind value vào `x`. Đừng dùng nó như null check.

### Flow analysis và nullable

Sau `if (value is not null)`, compiler biết `value` non-null trong block. Property pattern cũng thất bại nếu object trung gian là `null`, nên có thể kiểm tra graph ngắn gọn:

```csharp
if (order is { Customer.Address.City: "Bangkok" })
{
    // Chuỗi property cần thiết đã match non-null.
}
```

Pattern matching hỗ trợ nullable analysis; nó không thay runtime validation ở boundary.

### Guard `when`

Guard chạy **sau** khi pattern bên trái khớp và các biến đã được bind. Guard nên thuần khiết, nhanh và không mutate state. Nếu guard ném exception, switch dừng; runtime không thử arm sau như khi guard chỉ trả `false`.

## 6. Lỗi thường gặp

### Đặt arm tổng quát trước arm cụ thể

`Shipment _` trước `DomesticShipment` sẽ che mọi subtype. Compiler bắt được nhiều trường hợp unreachable, nhưng hãy chủ động đọc từ policy cụ thể tới fallback.

### Dùng `_ => default` cho dữ liệu chưa hỗ trợ

Fallback âm thầm trả phí `0` làm đơn đi tiếp với dữ liệu sai. Tại boundary, trả validation result; trong domain calculator, ném exception cụ thể hoặc dùng result type theo contract.

### Nhồi side effect vào switch expression

Pattern matching phù hợp với phân loại/ánh xạ. Nếu mỗi arm vừa ghi database, gửi message và mutate nhiều object, tách policy khỏi effect để test và rollback rõ hơn.

### Nhầm `_` với `null`

Discard `_` khớp cả `null`. Nếu `null` cần lỗi riêng, đặt `null => ...` trước fallback.

### Dùng `when` cho mọi thứ

`when x.Weight > 0 && x.Weight <= 10` chạy được nhưng property/relational pattern diễn tả shape rõ hơn. Giữ `when` cho điều kiện gọi method hoặc quan hệ khó biểu diễn bằng pattern.

## 7. Bài tập

### Bài 1 — Phân loại điểm số

Viết switch expression đổi điểm `0..100` thành `Fail`, `Pass`, `Good`, `Excellent`; từ chối ngoài khoảng.

Gợi ý: dùng relational pattern theo thứ tự không chồng lấn.

### Bài 2 — Kết quả thanh toán

Tạo hierarchy record `Approved`, `Declined`, `Pending`; trả message theo subtype và property.

Gợi ý: xử lý `null`, nhánh cụ thể, rồi fallback ném `NotSupportedException`.

### Bài 3 — List command

Match array command-line theo các shape `[]`, `["list"]`, `["add", var title]`, `["done", var idText]`.

Gợi ý: list pattern kiểm tra số phần tử; parse ID vẫn dùng `int.TryParse` trong code nhánh hoặc guard.

### Bài 4 — Nested property

Phân loại order theo `Customer.Address.CountryCode` và `Total`, trong đó các reference trung gian có thể null.

Gợi ý: dùng property pattern lồng và một arm riêng cho dữ liệu thiếu.

### Bài 5 — Audit thứ tự arm

Cố tình đặt pattern rộng trước pattern hẹp, đọc compiler error/warning rồi sắp lại. Viết test tay cho mọi boundary value.

Gợi ý: kiểm tra đúng các mốc `0`, `1`, `10`, `10.01` thay vì chỉ giá trị giữa khoảng.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi dùng `is` pattern mà không cast lặp lại.
- [ ] Tôi giải thích được switch chọn arm đầu tiên khớp.
- [ ] Tôi kết hợp property, relational và logical pattern đúng thứ tự.
- [ ] Tôi biết positional pattern dùng `Deconstruct` và list pattern kiểm tra shape.
- [ ] Tôi chỉ dùng `when` cho điều kiện pattern không diễn tả gọn.
- [ ] Tôi xử lý `null` và fallback theo policy rõ ràng.
- [ ] Tôi đã build/run ví dụ bằng .NET 9 với warnings là errors.

Bài prerequisite: [Record, `init`, `required` và tính bất biến](./07-record-init-required-va-immutability.md).

Bài tiếp theo: [Async, await, Task và state machine](./09-async-await-task-va-state-machine.md).
