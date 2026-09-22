# Pattern matching trong C#

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, async lifecycle hoặc serializer; CI failure

## TL;DR

- Pattern matching kiểm tra shape/type và bind biến để phân loại dữ liệu.
- Dùng cho pricing rule nhỏ, có nhánh lỗi và fallback rõ.
- Arm đầu tiên khớp thắng; thứ tự policy có thể đổi kết quả.

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

### Trực giác 60 giây

Bạn đọc phiếu giao hàng theo các tiêu chí từ cụ thể tới chung: kiện không hợp lệ bị loại trước, kiện đặc biệt có bảng giá riêng, phần còn lại phải có quyết định rõ.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| pattern | mẫu điều kiện dữ liệu cần khớp | WeightKg: >0 |
| arm | một nhánh switch expression | Domestic Express |
| guard | điều kiện thêm sau pattern | when IsSupportedCountry |
| deconstruction | tách component theo contract | positional record |

### Ví dụ nhỏ — tính tay trước

Domestic Express2kg →55000;2.01kg chưa được rule hỗ trợ nên throw. Bulk[1,2]→70000;[1,-1] bị từ chối trước rule hai kiện.

Dịch vụ vận chuyển nhận nhiều loại kiện hàng. Giá và thời gian phụ thuộc đồng thời vào runtime type, cân nặng, cờ giao nhanh, quốc gia và hình dạng danh sách kiện con.

Nếu viết một chuỗi dài `if`, cast rồi lặp lại truy cập property, code dễ gặp ba lỗi:

1. cast sai type hoặc quên kiểm tra `null`;
2. nhánh tổng quát đặt trước che nhánh đặc biệt;
3. thêm subtype mới nhưng vô tình trả mức giá mặc định không hợp lệ.

Ta sẽ mô hình hóa mỗi loại shipment bằng record từ bài trước (BulkShipment giữ array mutable, nên chỉ bất biến nông) và dùng pattern matching để vừa kiểm tra hình dạng dữ liệu, vừa bind biến cần tính giá.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

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

### Walkthrough — execution / state / cost

1. Quote nhận một Shipment và chọn arm khớp đầu theo semantics source.
2. Pattern kiểm tra type/null/property, bind cùng reference, không clone.
3. Guard kiểm tra toàn mảng khi shape đơn giản chưa đủ.
4. Quote mới là object kết quả. Bulk validation O(n), có nhánh quét lại; compiler có thể chia sẻ kiểm tra nên getter phải không có side effect.

### Mini-check

Insured TH giá trị cao có cận weight20kg giống nhánh international thường không? Đọc đúng arm trước khi giả định policy chung.

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

Semantics chọn arm đầu tiên khớp theo thứ tự source. Compiler có thể chia sẻ/sắp xếp kiểm tra property trong cây quyết định; không dựa vào số lần hay thứ tự gọi getter có side effect. Vì vậy nhánh invalid/cụ thể phải đứng trước nhánh rộng hơn. Với `InternationalShipment` từ Thái Lan có giá trị cao, arm insured khớp trước arm international thông thường.

Mỗi arm trả một `ShippingQuote`, nên toàn biểu thức có một kết quả. Compiler kiểm tra type của các kết quả, phát hiện một số arm không thể tới và cảnh báo khi switch trên type đóng như enum chưa exhaustive. Với hierarchy class mở, `_` vẫn cần policy rõ ràng.

### Property, positional và list pattern

- `{ WeightKg: > 0m and <= 10m }` đọc property rồi kết hợp hai relational pattern bằng `and`.
- `DomesticShipment(_, <= 2m, true)` dùng `Deconstruct` do positional record sinh; `_` bỏ qua `Id`.
- `ItemWeights: null` tách input thiếu collection khỏi các shape array hợp lệ.
- `ItemWeights: []` chỉ khớp array không có phần tử.
- `ItemWeights: [> 0m, > 0m]` chỉ khớp đúng hai phần tử và cả hai dương.
- `[_, ..]` nghĩa là có ít nhất một phần tử; `..` là slice pattern bỏ qua phần còn lại.

Pattern nên diễn tả **shape**. Điều kiện phải lặp toàn bộ array được đặt trong guard `when AllPositive(...)` vì không có pattern ngắn gọn để nói “mọi phần tử đều dương”.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| if/switch | phân nhánh tường minh | đủ cho vài rule đơn giản |
| pattern expression | shape và result cạnh nhau | hợp mapping nhỏ |
| virtual operation | hành vi gắn với subtype | chọn khi contract thay thế tự nhiên, không ép |

### Misconception check

**Đúng hay sai?** Pattern variable là clone object.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: cùng reference được nhìn theo kiểu cụ thể.

</details>

**Đúng hay sai?** _ chỉ khớp non-null.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: discard khớp cả null.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** shape/type và binding.

- **Working Developer — dùng khi làm việc:** cận policy và fallback.

- **Deep Dive — có thể quay lại sau:** decision DAG chỉ khi cần hiểu compiler.

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

## 7. Khi nào KHÔNG dùng

Không giấu I/O hoặc mutation trong getter/guard. Không return phí0 cho subtype chưa hỗ trợ; cần fail rõ hoặc result validation.

## 8. Production notes & scale check

Test null, weight0/2/2.01, bulk rỗng/âm và fallback. BulkShipment chứa array mutable; positional record chưa validate mọi field. Insured TH hiện ưu tiên theo value và chỉ guard weight>0, không tự áp cận20 của nhánh khác.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

So với bảng if Module01 và inheritance Module04, chọn biểu diễn dễ review cho5rule shipping. Nêu cận và trường hợp chưa hỗ trợ trước khi chọn pattern.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Arm nào thắng khi cùng khớp?
2. when false khác throw thế nào?
3. List pattern[a,b] nhận ba phần tử không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi dùng `is` pattern mà không cast lặp lại.
- [ ] Tôi giải thích được switch chọn arm đầu tiên khớp.
- [ ] Tôi kết hợp property, relational và logical pattern đúng thứ tự.
- [ ] Tôi biết positional pattern dùng `Deconstruct` và list pattern kiểm tra shape.
- [ ] Tôi chỉ dùng `when` cho điều kiện pattern không diễn tả gọn.
- [ ] Tôi xử lý `null` và fallback theo policy rõ ràng.
- [ ] Tôi đã build/run ví dụ bằng .NET 9 với warnings là errors.

Bài prerequisite: [Record, `init`, `required` và tính bất biến](./07-record-init-required-va-immutability.md).

Bài tiếp theo: [Async, await, Task và state machine](./09-async-await-task-va-state-machine.md).
