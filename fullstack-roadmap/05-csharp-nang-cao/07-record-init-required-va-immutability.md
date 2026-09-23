# Record, `init`, `required` và tính bất biến

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, async lifecycle hoặc serializer; CI failure

## TL;DR

- Record cung cấp value equality và cú pháp tạo snapshot bằng with.
- Dùng cho dữ liệu mà giá trị quan trọng hơn identity object.
- with copy nông; public init vẫn có thể mở đường tạo tổ hợp state sai.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng `record class` khi một object được nhận diện chủ yếu bởi dữ liệu của nó;
- phân biệt value equality của record với reference identity của class object;
- dùng `init` để chỉ cho phép gán property trong giai đoạn khởi tạo;
- dùng `required` để compiler buộc call site cung cấp member bắt buộc;
- tạo bản sao có thay đổi bằng biểu thức `with` mà không sửa object gốc;
- nhận ra `with` chỉ shallow-copy các reference bên trong;
- bảo vệ collection khỏi mutation ngoài ý muốn bằng defensive copy và read-only wrapper;
- hiểu vì sao `init`, `required` và record không tự động bảo đảm mọi domain invariant.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Chụp phiếu đơn mới không sửa phiếu cũ. Nhưng nếu cả hai phiếu cùng ghi địa chỉ một danh sách mutable, sửa danh sách vẫn ảnh hưởng cả hai; cần xét mọi đường tới dữ liệu.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| record | type có equality do compiler sinh | CustomerSnapshot |
| with | tạo copy rồi gán phần thay đổi | Submit |
| shallow copy | copy field/reference, không clone sâu | Lines dùng chung |
| immutability | state quan sát không đổi qua API | OrderLine init-only |

### Ví dụ nhỏ — tính tay trước

Customer copy với with{} có ==true nhưng ReferenceEqualsfalse. Submit tạo OrderDraft mới cùng line view; public Lines.init còn cho tạo submitted with{Lines=[]}, một hạn chế domain đã nêu.

Màn hình checkout cần giữ một bản nháp đơn hàng. Khi người dùng thêm dòng hàng hoặc bấm gửi:

- phiên bản cũ phải giữ nguyên để audit hoặc hỗ trợ undo;
- `Id`, khách hàng và danh sách dòng hàng không được thiếu;
- hai snapshot khách hàng có cùng dữ liệu cần so sánh bằng nhau;
- code bên ngoài không được sửa trực tiếp collection dòng hàng;
- mỗi lần chuyển trạng thái phải tạo một snapshot mới, không mutate object đang được nơi khác tham chiếu.

Một class có nhiều public setter dễ làm state thay đổi từ bất kỳ chỗ nào. Ngược lại, chỉ thay `class` bằng `record` rồi dùng một array mutable vẫn chưa có immutability thật. Lời giải dưới đây kết hợp record, `required`, `init`, `with` và defensive copy.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project `.NET 9`:

```bash
mkdir ImmutableOrderDemo
cd ImmutableOrderDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `ImmutableOrderDemo.csproj` bằng:

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

Thay toàn bộ `Program.cs` bằng nội dung sau:

Trong code, `record` yêu cầu compiler sinh value equality; `required` buộc object initializer cung cấp property; accessor `init` chỉ nhận phép gán trong giai đoạn khởi tạo; và `with` tạo một record copy rồi áp dụng các member được chỉ định. Các cơ chế này được kiểm tra chi tiết sau khi chạy sample.

```csharp
using System.Collections.Generic;

namespace ImmutableOrderDemo;

public enum OrderStatus
{
    Draft = 0,
    Submitted = 1
}

// Positional record phù hợp với snapshot nhỏ, mọi component đều chỉ đọc.
public sealed record CustomerSnapshot(string Id, string DisplayName);

public sealed record OrderLine
{
    private string _sku = string.Empty;
    private int _quantity;
    private decimal _unitPrice;

    public required string Sku
    {
        get => _sku;
        init
        {
            ArgumentException.ThrowIfNullOrWhiteSpace(value);
            _sku = value.Trim().ToUpperInvariant();
        }
    }

    public required int Quantity
    {
        get => _quantity;
        init
        {
            ArgumentOutOfRangeException.ThrowIfNegativeOrZero(value);
            _quantity = value;
        }
    }

    public required decimal UnitPrice
    {
        get => _unitPrice;
        init
        {
            ArgumentOutOfRangeException.ThrowIfNegative(value);
            _unitPrice = value;
        }
    }

    public decimal Subtotal => Quantity * UnitPrice;
}

public sealed record OrderDraft
{
    private string _id = string.Empty;
    private CustomerSnapshot _customer = null!;
    private IReadOnlyList<OrderLine> _lines = Array.Empty<OrderLine>();

    public required string Id
    {
        get => _id;
        init
        {
            ArgumentException.ThrowIfNullOrWhiteSpace(value);
            _id = value.Trim().ToUpperInvariant();
        }
    }

    public required CustomerSnapshot Customer
    {
        get => _customer;
        init => _customer = value ?? throw new ArgumentNullException(nameof(value));
    }

    public required IReadOnlyList<OrderLine> Lines
    {
        get => _lines;
        init
        {
            ArgumentNullException.ThrowIfNull(value);

            // Clone các reference slot rồi bọc lại. Caller không giữ backing List.
            var copy = new List<OrderLine>(value.Count);
            foreach (OrderLine line in value)
            {
                copy.Add(line ?? throw new ArgumentException(
                    "Lines cannot contain null.", nameof(value)));
            }

            _lines = copy.AsReadOnly();
        }
    }

    public OrderStatus Status { get; private init; } = OrderStatus.Draft;

    public decimal Total
    {
        get
        {
            decimal total = 0m;
            foreach (OrderLine line in Lines)
            {
                total += line.Subtotal;
            }

            return total;
        }
    }

    public OrderDraft AddLine(OrderLine line)
    {
        ArgumentNullException.ThrowIfNull(line);

        if (Status != OrderStatus.Draft)
        {
            throw new InvalidOperationException(
                "A submitted order cannot receive new lines.");
        }

        var expanded = new List<OrderLine>(Lines.Count + 1);
        foreach (OrderLine current in Lines)
        {
            expanded.Add(current);
        }

        expanded.Add(line);
        return this with { Lines = expanded };
    }

    public OrderDraft Submit()
    {
        if (Lines.Count == 0)
        {
            throw new InvalidOperationException("An empty order cannot be submitted.");
        }

        return this with { Status = OrderStatus.Submitted };
    }
}

internal static class Program
{
    private static void Main()
    {
        var customer = new CustomerSnapshot("CUS-001", "An Nguyen");
        var equalCustomer = customer with { };

        var draft = new OrderDraft
        {
            Id = "ord-001",
            Customer = customer,
            Lines = Array.Empty<OrderLine>()
        };

        var keyboard = new OrderLine
        {
            Sku = "keyboard",
            Quantity = 2,
            UnitPrice = 750_000m
        };

        OrderDraft withLine = draft.AddLine(keyboard);
        OrderDraft submitted = withLine.Submit();

        Console.WriteLine($"Draft lines: {draft.Lines.Count}");
        Console.WriteLine($"New snapshot: {withLine.Lines.Count} line, {withLine.Total:N0} VND");
        Console.WriteLine($"Statuses: {withLine.Status} -> {submitted.Status}");
        Console.WriteLine($"Same order object: {ReferenceEquals(withLine, submitted)}");
        Console.WriteLine($"Shared line view: {ReferenceEquals(withLine.Lines, submitted.Lines)}");
        Console.WriteLine($"Equal customer values: {customer == equalCustomer}");
        Console.WriteLine($"Same customer object: {ReferenceEquals(customer, equalCustomer)}");
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
Draft lines: 0
New snapshot: 1 line, 1,500,000 VND
Statuses: Draft -> Submitted
Same order object: False
Shared line view: True
Equal customer values: True
Same customer object: False
```

Ký tự phân cách hàng nghìn có thể khác theo locale.

### Walkthrough — execution / state / cost

1. Main tạo draft rỗng và OrderLine hợp lệ.
2. AddLine tạo list, init accessor copy/wrap; draft cũ vẫn0line.
3. Submit copy record, thay Status, giữ reference line view vì không gán Lines.
4. Cost AddLine O(n) và có hai lượt copy container trong implementation; Submit copy số field cố định, không copy line content.

### Mini-check

Tại sao immutable OrderLine giúp chia sẻ line view an toàn nhưng chưa giải quyết transition invariant của OrderDraft?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Record có value equality nhưng vẫn là reference type

`CustomerSnapshot` được khai báo bằng `record`, viết đầy đủ là `record class`. Mỗi lần `new CustomerSnapshot(...)` hoặc `with` tạo một class object có identity riêng trên managed heap. Tuy nhiên compiler sinh equality dựa trên runtime type và các member tham gia equality.

```text
customer reference ───────> H1 CustomerSnapshot { CUS-001, An Nguyen }
equalCustomer reference ──> H2 CustomerSnapshot { CUS-001, An Nguyen }

ReferenceEquals(customer, equalCustomer) == false
customer == equalCustomer                 == true
```

Class thông thường mặc định so sánh reference identity nếu không override equality. Record thay đổi semantics equality; nó không biến reference type thành value type.

### `init` giới hạn thời điểm gán

Accessor `init` cho phép gán trong object initializer, constructor hoặc quá trình tạo bản sao bằng `with`. Sau khi initialization kết thúc, call site không thể viết `keyboard.Quantity = 3`; compiler báo lỗi.

Trong sample, accessor còn validate rồi ghi backing field. Vì vậy `init` kiểm soát **thời điểm mutation**, còn code trong accessor kiểm soát **giá trị hợp lệ**. Chỉ viết `init` mà không validate vẫn cho phép số âm hoặc chuỗi rỗng lúc khởi tạo.

### `required` là hợp đồng compile-time

`required` buộc code khởi tạo object phải cung cấp member đó:

```csharp
// Không compile vì thiếu Customer và Lines.
// var invalid = new OrderDraft { Id = "ORD-002" };
```

Nó không tự kiểm tra `null`, khoảng giá trị hoặc dữ liệu đến từ reflection/deserializer. Toán tử null-forgiving `null!` cũng có thể cố ý tắt cảnh báo. Vì vậy sample vẫn guard trong `init` accessor.

### `with` tạo object mới và shallow-copy

`withLine.Submit()` thực hiện ý tưởng:

```text
1. tạo H_new bằng copy constructor do record sinh;
2. copy các field/reference từ H_old sang H_new;
3. gán Status của H_new thành Submitted;
4. trả reference tới H_new; H_old không đổi.
```

Sau `Submit`, hai record khác object nhưng cùng giữ reference tới read-only line view:

```text
withLine  ──> OrderDraft H3 ──┐
                              ├──> ReadOnlyCollection<OrderLine> H4
submitted ──> OrderDraft H5 ──┘                 │
                                                └──> OrderLine H6
```

Đây là shallow copy. Nó an toàn trong sample vì wrapper không cho sửa cấu trúc và `OrderLine` cũng chỉ cho khởi tạo một lần. Nếu member trỏ tới `List<T>` hoặc object có public setter, cả hai record vẫn quan sát cùng mutable state.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| class identity | mặc định so reference | hợp entity có quy tắc ID riêng |
| record value equality | member tham gia equality | collection thường vẫn reference equality |
| read-only wrapper | chặn sửa slot qua wrapper | không tự làm element bất biến |

### Misconception check

**Đúng hay sai?** Hai record có array cùng nội dung luôn bằng nhau.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: equality member array mặc định theo reference.

</details>

**Đúng hay sai?** Private Status đã đóng mọi đường tạo Submitted rỗng.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: public Lines.init trên with của submitted vẫn mở đường đó.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** identity/value và with.

- **Working Developer — dùng khi làm việc:** ownership cùng cross-field invariant.

- **Deep Dive — có thể quay lại sau:** custom equality theo domain.

### Các dạng record

- `record` hoặc `record class` là reference type, hỗ trợ inheritance và value equality.
- `record struct` là value type; phép gán copy toàn bộ value và vẫn có cảnh báo về `default` như mọi struct.
- positional record như `CustomerSnapshot(string Id, string DisplayName)` sinh constructor, property `init`, `Deconstruct`, equality và `ToString`.
- record với property tường minh như `OrderDraft` phù hợp khi cần validation và behavior rõ hơn.

Record không có nghĩa là entity DDD. Entity thường được nhận diện bằng ID và có lifecycle; value equality trên toàn bộ member có thể không đúng semantics entity. Hãy chọn theo domain, không theo độ ngắn của cú pháp.

### Equality và collection member

Equality do record sinh gọi equality của từng member. `string` và record con có value equality, nhưng `List<T>`, array và nhiều collection mặc định vẫn so sánh reference. Hai `OrderDraft` được dựng độc lập với các list chứa cùng dòng hàng có thể không bằng nhau vì hai collection là hai object khác nhau.

Nếu equality theo chuỗi phần tử là requirement, hãy định nghĩa value object/collection phù hợp hoặc custom equality có chủ đích. Đừng giả định record tự deep-compare toàn bộ object graph.

### Immutability nông và sâu

- `init` ngăn gán lại property sau initialization.
- read-only wrapper ngăn thêm/xóa/thay slot qua API được công khai.
- cả hai cơ chế đều không tự làm object phần tử immutable.
- deep immutability yêu cầu mọi đường đi trong object graph cũng không cho mutation quan sát được.

Immutability giúp snapshot dễ suy luận và an toàn hơn khi chia sẻ, nhưng tạo bản sao collection lớn có chi phí. Hãy đo và chọn persistent/immutable collection ở module phù hợp khi quy mô cần đến.

## 6. Lỗi thường gặp

### Nghĩ record không tạo object mới

`with` trên `record class` tạo record object mới. Các reference field có thể vẫn dùng chung; hãy vẽ object graph thay vì nói chung chung “đã clone”.

### Nghĩ `required` là runtime validation

`required string Name` không tự từ chối `null!` hoặc chuỗi trắng. Validate trong constructor/accessor/factory và vẫn kiểm tra input ở boundary.

### Đặt mutable list vào record

```csharp
public sealed record BadOrder(List<OrderLine> Lines);
```

`bad with { }` dùng chung chính list đó. `copy.Lines.Add(...)` làm object gốc cũng thấy phần tử mới. Dùng ownership rõ ràng, defensive copy và read-only/immutable representation.

### Dùng record equality cho entity mà không xét semantics

Hai entity cùng `Id` nhưng khác snapshot có thể cần được coi là cùng entity; record mặc định lại so sánh mọi member. Hãy override hoặc dùng class theo định nghĩa equality của domain.

### Công khai `init` cho state chỉ domain method được đổi

Nếu `Status` có public `init`, caller có thể tạo `with { Status = Submitted }` và bỏ qua rule đơn không được rỗng. Sample dùng `private init` để chặn gán trực tiếp Status. Tuy nhiên public `Lines.init` vẫn cho phép `submitted with { Lines = [] }`: object cũ không đổi nhưng bản mới có Submitted và rỗng. Vì vậy đây là snapshot minh họa, chưa phải type bảo vệ toàn bộ transition qua mọi đường `with`. Khi domain cần guarantee đó, đóng đường khởi tạo Lines bằng constructor/factory và operation có kiểm tra; không dựa riêng vào private Status.

## 7. Khi nào KHÔNG dùng

Không dùng record mặc định cho entity chỉ vì ít dòng. Không hứa deep immutability khi member chứa List mutable hoặc public API cho thay tổ hợp state.

## 8. Production notes & scale check

Test defensive copy, identity/value equality, snapshot cũ và đường with bypass. Muốn type domain đóng đầy đủ: chuyển construction Lines vào API có kiểm tra, cân nhắc class/constructor thay nhiều public init; không cần framework.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Snapshot địa chỉ

Tạo positional record `Address` gồm street, city và postal code; tạo bản sao đổi city bằng `with`.

Gợi ý: in cả `==` và `ReferenceEquals` để phân biệt equality với identity.

### Bài 2 — Product có validation

Tạo record có `required Sku`, `required Name`, `required Price`; normalize SKU và từ chối giá âm trong `init` accessor.

Gợi ý: thử bỏ một required member để đọc compiler error, sau đó thử truyền chuỗi trắng để quan sát runtime guard.

### Bài 3 — Tìm shallow mutation

Tạo record chứa `List<string> Tags`, copy bằng `with`, rồi thêm tag qua bản sao. Vẽ object graph và refactor sang read-only wrapper.

Gợi ý: wrapper bảo vệ cấu trúc; nếu phần tử là object mutable, vẫn phải xét phần tử riêng.

### Bài 4 — Workflow bất biến

Tạo `PurchaseRequest` có trạng thái `Draft`, `Approved`, `Rejected`; chỉ method hợp lệ mới trả snapshot trạng thái kế tiếp.

Gợi ý: dùng `private init` cho status và ném `InvalidOperationException` khi transition sai.

### Bài 5 — Equality của collection

Tạo hai record chứa hai array khác nhau nhưng có cùng phần tử, rồi kiểm tra `==`. Thiết kế lại để equality phản ánh đúng requirement của bạn.

Gợi ý: ghi rõ bạn cần reference equality, sequence equality hay identity theo ID trước khi viết code.

## 10. Bài tập tích hợp liên module — Judgment

So với candidate list Module04 capstone, khi nào shallow copy đủ, khi nào cần item mới? Vẽ object graph và nêu invariant độc lập với “không mutate object cũ”.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. with tạo object gì mới?
2. Equality collection hoạt động ra sao?
3. required khác validation ở đâu?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt được record value equality với object reference identity.
- [ ] Tôi biết `init` giới hạn thời điểm gán nhưng không tự validate.
- [ ] Tôi biết `required` là kiểm tra compile-time, không phải runtime guarantee.
- [ ] Tôi giải thích được `with` tạo object mới nhưng shallow-copy reference member.
- [ ] Tôi bảo vệ collection bằng defensive copy/read-only representation phù hợp.
- [ ] Tôi không dùng record mặc định cho entity nếu equality không đúng domain.
- [ ] Tôi đã build/run ví dụ bằng SDK .NET 9 với warnings là errors.

Bài prerequisite: [Nullable reference type](./06-nullable-reference-type.md).

Bài tiếp theo: [Pattern matching](./08-pattern-matching.md).
