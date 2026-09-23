# Serialization với `System.Text.Json`

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, async lifecycle hoặc serializer; CI failure

## TL;DR

- Serialization đổi object sang wire format theo contract riêng.
- Dùng DTO và JsonTypeInfo rõ để kiểm soát tên, enum, required và null.
- JSON hợp cú pháp chưa có nghĩa dữ liệu hợp nghiệp vụ.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt object graph trong memory với JSON text/UTF-8 ở boundary;
- thiết kế DTO có contract tên field, required/optional và enum rõ ràng;
- serialize/deserialize bằng `System.Text.Json` trên .NET 9;
- dùng source-generated `JsonSerializerContext` thay cho discovery reflection mặc định;
- kiểm soát null, unknown member và naming policy;
- validate nghiệp vụ sau deserialization, không xem JSON hợp cú pháp là dữ liệu hợp lệ;
- phân tích trade-off tương thích khi contract thay đổi;
- nhận ra giới hạn allocation, payload size, depth và polymorphism.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Gửi phiếu qua đường dây cần thống nhất tên ô và cách ghi giá trị. Người nhận dựng phiếu mới từ text, rồi vẫn phải kiểm tra số tiền và mã đơn trước khi chấp nhận.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| DTO | dữ liệu dành cho boundary | OrderDto |
| wire contract | quy ước dữ liệu trao đổi | camelCase và enum string |
| source generation | sinh metadata lúc build | AppJsonContext |
| presence | field có xuất hiện | required Total |

### Ví dụ nhỏ — tính tay trước

Thiếu total → lỗi contract; total=-1 có mặt → deserialize được nhưng Validate từ chối. status1 bị converter chặn; statusPaid được nhận.

Dịch vụ đơn hàng cần gửi object sau qua HTTP hoặc message broker:

```text
OrderDto { Id, Total, Status, CreatedAt, Note }
```

Nếu serialize theo mặc định rồi thay tên property tùy ý, consumer có thể hỏng mà compiler hai phía không báo. Nếu nhận JSON rồi tin ngay, dữ liệu có `Total` âm hoặc field lạ có thể đi sâu vào hệ thống.

Ta cần một contract cụ thể:

- property JSON dùng `camelCase`;
- enum dùng tên string, không dùng con số khó đọc;
- `Id`, `Total`, `Status`, `CreatedAt` bắt buộc có mặt;
- `Note = null` được bỏ khỏi output;
- field JSON không biết bị từ chối trong contract nghiêm ngặt;
- metadata serializer được sinh lúc compile để thân thiện hơn với trimming/AOT.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project:

```bash
dotnet new console --name JsonContractDemo --framework net9.0 --use-program-main
cd JsonContractDemo
```

Thay `JsonContractDemo.csproj` bằng:

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
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace JsonContractDemo;

internal static class Program
{
    private static void Main()
    {
        var original = new OrderDto
        {
            Id = "ORD-1001",
            Total = 125_000.50m,
            Status = OrderStatus.Paid,
            CreatedAt = DateTimeOffset.Parse(
                "2026-07-30T08:30:00+07:00",
                CultureInfo.InvariantCulture),
            Note = null
        };

        JsonTypeInfo<OrderDto> contract = AppJsonContext.Default.OrderDto;

        string json = JsonSerializer.Serialize(original, contract);
        Console.WriteLine("Serialized JSON:");
        Console.WriteLine(json);

        OrderDto restored = JsonSerializer.Deserialize(json, contract)
            ?? throw new JsonException("JSON contained null instead of an order.");

        Validate(restored);
        Console.WriteLine(FormattableString.Invariant(
            $"Restored: {restored.Id}, {restored.Total:F2}, {restored.Status}"));

        const string jsonWithUnknownMember = """
            {
              "id": "ORD-1002",
              "total": 50000,
              "status": "Pending",
              "createdAt": "2026-07-30T09:00:00+07:00",
              "unexpected": true
            }
            """;

        try
        {
            _ = JsonSerializer.Deserialize(jsonWithUnknownMember, contract);
        }
        catch (JsonException)
        {
            Console.WriteLine("Strict contract rejected an unknown JSON member.");
        }

        const string jsonWithNumericStatus = """
            {
              "id": "ORD-1003",
              "total": 1000,
              "status": 1,
              "createdAt": "2026-07-30T10:00:00+07:00"
            }
            """;

        try
        {
            _ = JsonSerializer.Deserialize(jsonWithNumericStatus, contract);
        }
        catch (JsonException)
        {
            Console.WriteLine("Strict enum contract rejected a numeric status.");
        }
    }

    private static void Validate(OrderDto order)
    {
        if (string.IsNullOrWhiteSpace(order.Id))
        {
            throw new InvalidOperationException("Order Id is required.");
        }

        if (order.Total < 0m)
        {
            throw new InvalidOperationException("Order Total cannot be negative.");
        }

        // Phòng thủ cả object được tạo trực tiếp trong code, không chỉ từ JSON.
        if (!Enum.IsDefined(order.Status))
        {
            throw new InvalidOperationException("Order Status is not defined.");
        }
    }
}

[JsonUnmappedMemberHandling(JsonUnmappedMemberHandling.Disallow)]
internal sealed record OrderDto
{
    public required string Id { get; init; }

    public required decimal Total { get; init; }

    public required OrderStatus Status { get; init; }

    public required DateTimeOffset CreatedAt { get; init; }

    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Note { get; init; }
}

[JsonConverter(typeof(StrictOrderStatusConverter))]
internal enum OrderStatus
{
    Pending,
    Paid,
    Cancelled
}

internal sealed class StrictOrderStatusConverter : JsonConverter<OrderStatus>
{
    public override OrderStatus Read(
        ref Utf8JsonReader reader,
        Type typeToConvert,
        JsonSerializerOptions options)
    {
        if (reader.TokenType != JsonTokenType.String)
        {
            throw new JsonException("Order status must be a string.");
        }

        return reader.GetString() switch
        {
            nameof(OrderStatus.Pending) => OrderStatus.Pending,
            nameof(OrderStatus.Paid) => OrderStatus.Paid,
            nameof(OrderStatus.Cancelled) => OrderStatus.Cancelled,
            _ => throw new JsonException("Unknown order status.")
        };
    }

    public override void Write(
        Utf8JsonWriter writer,
        OrderStatus value,
        JsonSerializerOptions options)
    {
        string text = value switch
        {
            OrderStatus.Pending => nameof(OrderStatus.Pending),
            OrderStatus.Paid => nameof(OrderStatus.Paid),
            OrderStatus.Cancelled => nameof(OrderStatus.Cancelled),
            _ => throw new JsonException("Unknown order status.")
        };

        writer.WriteStringValue(text);
    }
}

[JsonSourceGenerationOptions(
    PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase,
    WriteIndented = true)]
[JsonSerializable(typeof(OrderDto))]
internal partial class AppJsonContext : JsonSerializerContext
{
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Output:

```text
Serialized JSON:
{
  "id": "ORD-1001",
  "total": 125000.50,
  "status": "Paid",
  "createdAt": "2026-07-30T08:30:00+07:00"
}
Restored: ORD-1001, 125000.50, Paid
Strict contract rejected an unknown JSON member.
Strict enum contract rejected a numeric status.
```

### Walkthrough — execution / state / cost

1. Generator tạo JsonTypeInfo từ DTO và attributes lúc build.
2. Serialize ghi JSON, bỏ Note null; deserialize tạo object mới.
3. Validate kiểm tra Id/Total/Status sau parse.
4. Unknown field bị từ chối theo policy strict. Text và object đều tốn memory theo payload; source generation không xóa allocation.

### Mini-check

Producer thêm field optional nhưng consumer cũ Disallow: rollout nào sẽ lỗi?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Serialization đi qua một contract

Object và JSON không cùng representation:

```text
MANAGED HEAP
OrderDto object
├── Id reference ──> string object
├── Total           decimal inline
├── Status          enum inline
├── CreatedAt       struct inline
└── Note reference  null
        |
        | JsonTypeInfo<OrderDto> contract
        v
JSON text / UTF-8 bytes
{"id":"ORD-1001", ...}
```

Serializer đọc property theo contract rồi ghi token JSON. Deserializer parse token, convert type và tạo/populate object mới. `restored` không phải cùng reference với `original`; các reference member như string cũng tuân theo allocation/interning riêng của parser/runtime, không được dựa vào identity.

### 4.2. `required` kiểm tra presence, `Validate` kiểm tra domain

Các property `required` được source-generated contract xem là bắt buộc. Thiếu `id` hoặc `total` gây `JsonException`. Nhưng presence không chứng minh dữ liệu hợp lệ:

- `id: ""` vẫn là string có mặt;
- `total: -1` vẫn parse thành decimal;
- timestamp có thể hợp format nhưng nằm ngoài policy nghiệp vụ.

Vì vậy code gọi `Validate(restored)` sau deserialization. Parsing/contract validation và business validation là hai lớp khác nhau.

### 4.3. Naming, enum và null là quyết định wire format

`JsonKnownNamingPolicy.CamelCase` ánh xạ `CreatedAt` thành `createdAt`. `StrictOrderStatusConverter` chỉ nhận đúng token string `Pending`, `Paid` hoặc `Cancelled`; token số và tên lạ gây `JsonException`. Đây là chủ ý của wire contract. Constructor mặc định của `JsonStringEnumConverter<TEnum>` vẫn cho phép integer value, nên chỉ gắn converter đó chưa đủ để thực thi yêu cầu “không dùng số”. Converter cụ thể trong sample không cần tìm enum bằng reflection và tương thích với source-generated contract.

`[JsonIgnore(Condition = WhenWritingNull)]` làm `Note = null` biến mất khi serialize. Missing `note`, JSON `"note": null` và `"note": ""` là ba trạng thái có thể mang nghĩa khác; DTO/policy phải quyết định rõ.

### 4.4. Source generation hoạt động lúc build

`[JsonSerializable(typeof(OrderDto))]` yêu cầu generator tạo `JsonTypeInfo<OrderDto>` trong partial context. Code gọi overload nhận `JsonTypeInfo`, nên contract cụ thể hiện rõ tại call site:

```text
compile
OrderDto + attributes
        |
        v
generated metadata/serialization code trong assembly

runtime
AppJsonContext.Default.OrderDto ---> JsonSerializer
```

### 4.5. Unknown member là một trade-off versioning

`JsonUnmappedMemberHandling.Disallow` bắt typo hoặc payload lệch contract sớm. Đổi lại, consumer cũ sẽ từ chối producer mới thêm field, làm giảm forward compatibility.

Không có policy đúng cho mọi boundary:

- command nội bộ nghiêm ngặt có thể `Disallow`;
- public event cần schema evolution có thể bỏ qua field mới nhưng vẫn validate field quan trọng;
- security-sensitive input có thể dùng DTO hẹp và reject phần dư.

Chọn policy cùng chiến lược version, contract test và rollout, không chỉ vì “strict tốt hơn”.

### 4.6. Date/time và number

`DateTimeOffset` giữ timestamp cùng offset và được ghi theo ISO 8601. Với một thời điểm tuyệt đối, nó rõ hơn string tùy format. Vẫn phải thống nhất UTC/offset policy ở domain.

JSON number không mang type CLR. Contract quyết định token được parse vào `decimal`, `int` hay `double`. `decimal` phù hợp tiền nhưng serializer không thay thế rounding/currency policy.

### Đào sâu (có thể quay lại sau)

#### Giới hạn của source generation

Cách này giảm nhu cầu reflection discovery runtime, cải thiện startup và khả năng trimming/Native AOT. Nó không bảo đảm zero allocation và không tự tối ưu network/I/O. Mọi type cần serialize phải có entry/context phù hợp hoặc resolver được cấu hình có chủ đích.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| typed DTO | contract biết trước | dễ validate và version |
| DOM | dữ liệu linh hoạt | thêm ownership/lookup và validation |
| strict unknown field | bắt typo sớm | producer thêm field có thể phá consumer cũ |

### Misconception check

**Đúng hay sai?** required đảm bảo Id không trắng.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: presence khác business validation.

</details>

**Đúng hay sai?** Source generation chứng minh zero allocation.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: text/object/buffer vẫn được tạo.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** object/wire contract.

- **Working Developer — dùng khi làm việc:** source generation và validation.

- **Deep Dive — có thể quay lại sau:** streaming/version rollout theo scale.

### API chính

| API | Kết quả/đầu vào | Lưu ý |
|---|---|---|
| `JsonSerializer.Serialize` | object → string/UTF-8/stream | overload source-generated làm contract rõ |
| `JsonSerializer.Deserialize` | JSON → object mới | có thể trả `null` nếu JSON là `null` |
| `JsonDocument` | DOM chỉ đọc | phải quản lý lifetime/`Dispose` |
| `JsonNode` | DOM mutable | linh hoạt nhưng kém type safety hơn DTO |
| `Utf8JsonReader/Writer` | token-level API | low-level, cần lifetime/state chính xác |

DTO typed là lựa chọn mặc định tốt khi contract đã biết. DOM/token API phù hợp payload động hoặc hot path đã đo, nhưng validation phức tạp hơn.

### Attribute contract thường gặp

- `[JsonPropertyName("...")]`: tên wire cố định, ưu tiên hơn naming policy;
- `[JsonIgnore]`: bỏ property theo điều kiện;
- `[JsonConverter]`: converter ở type/property;
- `[JsonRequired]` hoặc `required`: yêu cầu JSON property xuất hiện;
- `[JsonUnmappedMemberHandling]`: policy field không map.

Attribute gắn contract JSON vào DTO. Nếu cùng domain type phải có nhiều wire contract khác nhau, dùng DTO riêng hoặc cấu hình resolver/context riêng thay vì chồng nhiều concern lên domain object.

### Versioning cơ bản

Thay đổi thường ít phá hơn: thêm field optional với default rõ. Thay tên/xóa field, đổi type, đổi enum string hoặc biến optional thành required thường phá consumer. Enum mới cũng có thể làm consumer cũ thất bại; cần unknown-value policy hoặc version mới nếu domain yêu cầu.

### Streaming và memory

`Serialize(object)` trả string nên materialize toàn payload text. Với payload lớn, dùng async stream overload cùng `JsonTypeInfo` để tránh string trung gian, nhưng object graph và buffer serializer vẫn tiêu thụ memory. Đặt giới hạn body ở transport, `MaxDepth` phù hợp và cancellation cho I/O.

### Polymorphism

Không deserialize tên CLR type tùy ý từ payload. Nếu cần polymorphism, đăng ký discriminator và derived type allowlist rõ ràng bằng contract `System.Text.Json`. Type metadata do client tự chọn là một bề mặt tấn công và làm wire format gắn chặt implementation.

## 6. Lỗi thường gặp

### Dùng domain entity trực tiếp làm mọi JSON contract

Property nội bộ vô tình thành public API và refactor gây breaking change. Dùng DTO boundary khi contract có vòng đời/phiên bản riêng.

### Tin deserialize thành công nghĩa là hợp lệ

Serializer chủ yếu kiểm tra syntax, conversion và contract presence. Luôn validate range, cross-field rule, authorization và identity ở layer phù hợp.

### Quên xử lý JSON `null`

`Deserialize<OrderDto>("null", ...)` có thể trả `null`. Dùng `?? throw` hoặc result policy rõ như sample.

### Tin rằng string-enum converter mặc định luôn từ chối số

Constructor mặc định của `JsonStringEnumConverter<TEnum>` cho phép integer value. Nếu contract chỉ chấp nhận tên, cấu hình `allowIntegerValues: false` ở converter được đăng ký bằng options hoặc dùng converter nghiêm ngặt như sample. Giá trị số khó đọc và dễ đổi nghĩa; string enum làm contract rõ hơn nhưng rename enum member vẫn là breaking change, nên quản lý wire name như schema.

### Bật strict unknown member mà không có rollout plan

Producer thêm field trước có thể làm consumer cũ dừng. Phối hợp compatibility, version và deployment order.

### Nghĩ source generation loại mọi allocation

Nó giảm reflection metadata work; string output, object mới, collection, converter và buffer vẫn có thể allocate. Đo đúng workload ở bài 18.

### Log toàn payload nhạy cảm

JSON có thể chứa token, email hoặc dữ liệu cá nhân. Redact theo field, giới hạn độ dài và không log raw payload mặc định.

## 7. Khi nào KHÔNG dùng

Không deserialize tên CLR type tùy ý. Không serialize mọi domain property thành API công khai nếu wire contract có vòng đời riêng.

## 8. Production notes & scale check

Gate missing field, enum số/tên lạ, null payload và total âm. Chưa publish AOT; source generation chỉ là cơ chế đã build/chạy. Timestamp format hợp lệ chưa kiểm mọi policy thời gian.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Field optional

Thêm `string? CouponCode`, bỏ khi null và kiểm tra ba payload: missing, null, có text.

**Gợi ý:** ghi rõ ba trạng thái có cùng nghĩa hay không trước khi code.

### Bài 2 — Thiếu required property

Bỏ `total` khỏi JSON, bắt `JsonException` và phân biệt với lỗi `Total < 0` do `Validate` ném.

**Gợi ý:** contract error và domain error nên có test riêng.

### Bài 3 — Contract version 2

Tạo `OrderV2Dto` thêm field optional `currency = "VND"`; khảo sát consumer strict và lenient.

**Gợi ý:** viết ma trận producer V1/V2 với consumer V1/V2 trước khi chọn unknown-member policy.

### Bài 4 — Serialize ra stream

Dùng `MemoryStream` và `JsonSerializer.SerializeAsync` với source-generated `JsonTypeInfo`.

**Gợi ý:** reset `Position` trước khi đọc; truyền `CancellationToken`; dispose stream theo ownership.

### Bài 5 — Converter value object

Tạo converter cho một mã đơn có format `ORD-xxxx`, từ chối format sai.

**Gợi ý:** converter xử lý wire representation; business lookup/authorization vẫn nằm ngoài converter.

## 10. Bài tập tích hợp liên module — Judgment

So với JSON todo Module04, tách lỗi syntax/presence/domain và giữ dữ liệu cũ khi import sai. Chọn strict hoặc lenient theo nhu cầu compatibility cụ thể.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Presence khác validation thế nào?
2. Deserialize null trả gì?
3. Unknown member ảnh hưởng versioning ra sao?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi coi JSON là wire contract có version, không phải ảnh chụp object tùy ý.
- [ ] Tôi phân biệt required presence với business validation.
- [ ] Tôi kiểm soát naming, enum, null và unknown member có chủ đích.
- [ ] Tôi gọi overload dùng source-generated `JsonTypeInfo`.
- [ ] Tôi hiểu strictness và compatibility phải được thiết kế cùng nhau.
- [ ] Tôi đặt giới hạn payload/depth và không cho client chọn CLR type tùy ý.
- [ ] Tôi không tuyên bố source generation đồng nghĩa zero allocation.

Điều hướng:

- Prerequisite: [Expression tree](./16-expression-tree.md)
- Bài tiếp theo: [Đo lường và tối ưu hiệu năng](./18-do-luong-va-toi-uu-hieu-nang.md)
