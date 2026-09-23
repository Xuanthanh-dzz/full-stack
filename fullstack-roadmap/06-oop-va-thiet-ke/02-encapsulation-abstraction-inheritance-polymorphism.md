# Encapsulation, abstraction, inheritance và polymorphism

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, invariant hoặc adapter; CI failure

## TL;DR

- Bốn trụ cột giải quyết quyền sửa state và khả năng thay hành vi.
- Dùng interface theo caller, base class khi phần khung thực sự chung.
- Inheritance không cần có trong mọi thiết kế; virtual và method hiding khác nhau.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phát biểu bốn trụ cột OOP theo mục đích thiết kế, không chỉ theo cú pháp;
- dùng encapsulation để bảo vệ invariant thay vì chỉ bọc field bằng property;
- thiết kế abstraction theo nhu cầu của caller, không theo cấu trúc của implementation;
- dùng inheritance để chia sẻ phần khung chung và chỉ khi quan hệ đúng là “là một”;
- gọi cùng một method trên nhiều type khác nhau qua polymorphism và giải thích cách runtime chọn implementation;
- phân biệt `override`, `new` và overload;
- nhận ra khi bốn trụ cột bị dùng sai: getter/setter công khai cho mọi thứ, interface sao chép nguyên class, kế thừa để dùng lại code.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Người mua chỉ yêu cầu “in chứng từ”, không cần biết máy dùng text hay CSV. Ví tiền chỉ mở cửa nạp và thanh toán, không mở ô số dư cho mọi người gõ tùy ý.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| encapsulation | giới hạn cách sửa dữ liệu | StoreCredit |
| abstraction | hợp đồng caller cần biết | IReceiptFormatter |
| inheritance | lớp con dùng khung của lớp cha | ReceiptFormatterBase |
| dispatch | chọn thân method để chạy | FormatLine override |

### Ví dụ nhỏ — tính tay trước

Nạp100, trả40 →60 với hai dòng lịch sử. Trả90 →false, vẫn60 và không thêm lịch sử. Hai formatter nhận cùng receipt nhưng sinh chuỗi khác.

Tiếp tục hệ thống đặt hàng ở [bài 1](./01-mo-hinh-hoa-doi-tuong.md). Cửa hàng cần thêm hai việc:

1. In chứng từ của một đơn hàng theo nhiều định dạng: dạng text cho khách xem trên màn hình, dạng CSV cho kế toán nhập vào bảng tính. Danh sách định dạng sẽ còn tăng.
2. Quản lý ví trả trước của khách: nạp tiền, trừ tiền khi thanh toán, số dư không bao giờ âm, và mọi lần thay đổi số dư đều phải để lại một dòng lịch sử.

Nếu viết theo kiểu thẳng tay, ta sẽ có một `if (format == "text") ... else if (format == "csv") ...` cho việc thứ nhất, và một `public decimal Balance { get; set; }` cho việc thứ hai. Cả hai đều chạy được hôm nay và cả hai đều hỏng theo cách quen thuộc: thêm định dạng thứ ba phải sửa lại đúng cái `if` cũ, còn số dư thì bất kỳ ai cũng gán được, kể cả gán số âm và không ghi lịch sử.

Bốn trụ cột OOP tồn tại để trả lời chính xác hai vấn đề đó: giấu cái gì, lộ ra cái gì, dùng chung cái gì và thay thế được cái gì.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project `.NET 9`:

```bash
mkdir OopPillarsDemo
cd OopPillarsDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `OopPillarsDemo.csproj` bằng:

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
using System.Text;

namespace OopPillarsDemo;

public sealed record ReceiptLine(string Sku, int Quantity, decimal LineTotal);

public sealed record Receipt(
    string OrderId,
    string CustomerName,
    IReadOnlyList<ReceiptLine> Lines,
    decimal Total);

// ABSTRACTION: caller chỉ cần "đưa tôi chuỗi chứng từ", không cần biết cách dựng chuỗi.
public interface IReceiptFormatter
{
    string Name { get; }

    string Format(Receipt receipt);
}

// INHERITANCE: base class giữ phần khung dùng chung cho mọi định dạng.
public abstract class ReceiptFormatterBase : IReceiptFormatter
{
    public abstract string Name { get; }

    // Không virtual: thứ tự header - dòng - footer là quy tắc chung, không cho phép đổi.
    public string Format(Receipt receipt)
    {
        ArgumentNullException.ThrowIfNull(receipt);

        var builder = new StringBuilder();
        builder.AppendLine(FormatHeader(receipt));

        foreach (ReceiptLine line in receipt.Lines)
        {
            builder.AppendLine(FormatLine(line));
        }

        builder.Append(FormatFooter(receipt));
        return builder.ToString();
    }

    // Bắt buộc lớp con quyết định: mỗi định dạng viết một dòng theo cách riêng.
    protected abstract string FormatLine(ReceiptLine line);

    // Có sẵn bản mặc định, lớp con override khi cần.
    protected virtual string FormatHeader(Receipt receipt) =>
        $"RECEIPT {receipt.OrderId} - {receipt.CustomerName}";

    protected virtual string FormatFooter(Receipt receipt) =>
        $"TOTAL: {receipt.Total:N0} VND";
}

public sealed class TextReceiptFormatter : ReceiptFormatterBase
{
    public override string Name => "text";

    protected override string FormatLine(ReceiptLine line) =>
        $"  {line.Sku} x{line.Quantity} = {line.LineTotal:N0}";
}

public sealed class CsvReceiptFormatter : ReceiptFormatterBase
{
    public override string Name => "csv";

    protected override string FormatHeader(Receipt receipt) => "sku,quantity,line_total";

    protected override string FormatLine(ReceiptLine line) =>
        $"{line.Sku},{line.Quantity},{line.LineTotal}";

    protected override string FormatFooter(Receipt receipt) =>
        $"TOTAL,,{receipt.Total}";
}

// ENCAPSULATION: số dư và lịch sử chỉ đổi được qua hai thao tác có kiểm tra.
public sealed class StoreCredit
{
    private readonly List<string> _history = new();
    private readonly IReadOnlyList<string> _historyView;
    private decimal _balance;

    public StoreCredit(string customerId)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(customerId);
        _historyView = _history.AsReadOnly();
        CustomerId = customerId.Trim().ToUpperInvariant();
    }

    public string CustomerId { get; }

    public decimal Balance => _balance;

    public IReadOnlyList<string> History => _historyView;

    public void Deposit(decimal amount)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(amount);

        _balance += amount;
        _history.Add($"deposit {amount:N0} -> balance {_balance:N0}");
    }

    public bool TryPay(decimal amount, out string message)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(amount);

        if (amount > _balance)
        {
            message = $"not enough credit: need {amount:N0}, have {_balance:N0}";
            return false;
        }

        _balance -= amount;
        _history.Add($"pay {amount:N0} -> balance {_balance:N0}");
        message = $"paid {amount:N0}";
        return true;
    }
}

internal static class Program
{
    private static void Main()
    {
        var receipt = new Receipt(
            OrderId: "ORD-001",
            CustomerName: "An Nguyen",
            Lines: new[]
            {
                new ReceiptLine("KEYBOARD", 2, 1_500_000m),
                new ReceiptLine("MOUSE", 1, 350_000m)
            },
            Total: 1_850_000m);

        // POLYMORPHISM: một vòng lặp, hai hành vi khác nhau, không có if theo type.
        IReceiptFormatter[] formatters =
        {
            new TextReceiptFormatter(),
            new CsvReceiptFormatter()
        };

        foreach (IReceiptFormatter formatter in formatters)
        {
            Console.WriteLine($"--- {formatter.Name} ---");
            Console.WriteLine(formatter.Format(receipt));
        }

        var credit = new StoreCredit("cus-001");
        credit.Deposit(1_000_000m);

        Console.WriteLine($"--- credit {credit.CustomerId} ---");
        Console.WriteLine($"Pay 400,000: {credit.TryPay(400_000m, out string first)} ({first})");
        Console.WriteLine($"Pay 900,000: {credit.TryPay(900_000m, out string second)} ({second})");
        Console.WriteLine($"Balance: {credit.Balance:N0}");

        foreach (string entry in credit.History)
        {
            Console.WriteLine($"  {entry}");
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
--- text ---
RECEIPT ORD-001 - An Nguyen
  KEYBOARD x2 = 1,500,000
  MOUSE x1 = 350,000
TOTAL: 1,850,000 VND
--- csv ---
sku,quantity,line_total
KEYBOARD,2,1500000
MOUSE,1,350000
TOTAL,,1850000
--- credit CUS-001 ---
Pay 400,000: True (paid 400,000)
Pay 900,000: False (not enough credit: need 900,000, have 600,000)
Balance: 600,000
  deposit 1,000,000 -> balance 1,000,000
  pay 400,000 -> balance 600,000
```

Project được kiểm tra bằng .NET SDK `9.0.121`, target `net9.0`, không dùng package ngoài.

### Walkthrough — execution / state / cost

1. Main tạo receipt và hai formatter rồi gọi qua interface.
2. Format chạy khung ở base, các virtual call chọn override của object thật.
3. TryPay validate, kiểm đủ tiền rồi đổi balance và thêm history.
4. Receipt/Lines là dữ liệu tin cậy của demo, có thể alias array; formatter không deep-copy. Format tạo StringBuilder/string O(n dòng + độ dài output); history tăng theo giao dịch thành công.

### Mini-check

Base b=new Shadowing(): vì sao b.Describe không giống lời gọi qua biến Shadowing?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Encapsulation là bảo vệ invariant, không phải bọc field

`StoreCredit` có hai điều luôn đúng: số dư không âm, và mỗi lần số dư đổi thì có đúng một dòng lịch sử. Cả hai chỉ đúng được vì **không có đường nào khác** để chạm vào `_balance`:

```text
Bên ngoài  ──> Deposit(amount)   ──┐
           ──> TryPay(amount)    ──┤──> kiểm tra ──> đổi _balance ──> ghi _history
                                   ┘
_balance là private: không có con đường thứ hai.
```

So sánh với `public decimal Balance { get; set; }`: property đó vẫn “bọc field”, nhưng không bảo vệ gì cả. Bất kỳ ai cũng có thể `credit.Balance = -5_000_000m` và lịch sử không có gì. Encapsulation nằm ở việc **thu hẹp tập thao tác hợp lệ**, không nằm ở việc gõ chữ `private` rồi sinh cặp getter/setter công khai.

Chú ý `History` trả wrapper `AsReadOnly()` dưới kiểu `IReadOnlyList<string>` — cùng lý do với `Order.Lines` ở bài 1: nếu trả `List<string>`, caller thêm được dòng lịch sử giả.

### Abstraction là hợp đồng nhìn từ phía caller

`IReceiptFormatter` chỉ có `Name` và `Format`. Đó chính xác là những gì `Main` cần. Nó không có `AppendHeader`, `BuildLine` hay `StringBuilder` nào lộ ra, dù implementation dùng cả ba.

Thước đo của một abstraction tốt: caller viết được code hữu ích mà không cần biết bên trong là text, CSV, hay gọi ra thư viện PDF. Trong sample, `Main` chạy được với mọi formatter tương lai mà không sửa dòng nào.

Abstraction xấu thường là bản sao 1–1 của một class cụ thể: interface có đủ mọi method của implementation, kể cả method chỉ dùng nội bộ. Khi đó interface không giấu gì cả, chỉ thêm một file.

### Inheritance chia sẻ khung, không chia sẻ code bừa

`ReceiptFormatterBase` giữ đúng phần **không được khác nhau**: mọi chứng từ đều là header, rồi các dòng, rồi footer. Phần **được phép khác nhau** được mở ra qua `abstract`/`virtual`:

| Thành phần | Modifier | Ý nghĩa |
|---|---|---|
| `Format` | không virtual | khung cố định, lớp con không đổi được |
| `FormatLine` | `abstract` | lớp con bắt buộc quyết định |
| `FormatHeader`, `FormatFooter` | `virtual` | có mặc định, lớp con đổi khi cần |

`TextReceiptFormatter` chỉ viết 4 dòng vì nó chấp nhận header/footer mặc định. `CsvReceiptFormatter` override cả ba. Không class nào phải viết lại vòng lặp và thứ tự.

Điều kiện để dùng inheritance ở đây là quan hệ đúng nghĩa “là một”: một CSV formatter **là một** receipt formatter. Nếu quan hệ chỉ là “tôi cần dùng code trong class kia”, đó là “có một” và phải dùng composition — nội dung của [bài 3](./03-composition-over-inheritance.md).

### Polymorphism: một lời gọi, nhiều hành vi

Trong `Main`, biến có type `IReceiptFormatter`, còn object thật là `TextReceiptFormatter` hoặc `CsvReceiptFormatter`. Lời gọi `formatter.Format(receipt)` được **dispatch theo type thật lúc chạy**, không theo type của biến.

```text
STACK                      HEAP
formatters ──────────────> IReceiptFormatter[] #1
                           ├── [0] ──> TextReceiptFormatter #1
                           └── [1] ──> CsvReceiptFormatter #1

formatter (biến vòng lặp, type khai báo là IReceiptFormatter)
   ├── vòng 1 ──> TextReceiptFormatter #1  ==> FormatLine của Text chạy
   └── vòng 2 ──> CsvReceiptFormatter #1   ==> FormatLine của Csv chạy
```

Nhờ vậy, thêm `JsonReceiptFormatter` chỉ cần một class mới và một dòng trong mảng; vòng lặp không đổi. Đây là nền tảng của nguyên tắc open/closed ở [bài 5](./05-open-closed.md).

### Đào sâu (có thể quay lại sau)

#### `Format` gọi ngược xuống lớp con

`Format` nằm ở base class nhưng lại gọi `FormatLine` — một method chỉ lớp con mới có nội dung. Cơ chế vẫn là virtual dispatch: base class gọi qua bảng method của object thật. Khung này có tên riêng trong catalog design pattern và sẽ được gọi đúng tên ở [module 16](../PROGRESS.md#16-design-pattern); ở đây bạn chỉ cần thấy nó là hệ quả tự nhiên của `abstract` + `virtual`.

Một rủi ro cần biết: đừng gọi method `virtual` từ constructor của base class. Khi constructor base chạy, phần khởi tạo của lớp con chưa xong, nên override có thể đọc field còn `null`.

#### Bốn trụ cột không phải bốn thứ phải dùng đủ

Một thiết kế tốt có thể chỉ dùng encapsulation và abstraction, không có một `abstract class` nào. Inheritance là công cụ có chi phí cao nhất trong bốn thứ: nó khóa lớp con vào cấu trúc của base, và mọi thay đổi ở base lan xuống toàn bộ cây. Dùng nó khi phần khung thực sự ổn định.

#### Ba dạng polymorphism thường gặp trong C#

- **Subtype polymorphism**: qua `virtual`/`override` hoặc interface — dạng dùng trong bài này.
- **Parametric polymorphism**: generics; một `Repository<T>` chạy với nhiều `T` (đã học ở [module 05, bài 1](../05-csharp-nang-cao/01-generics-va-constraints.md)).
- **Ad-hoc polymorphism**: overload; compiler chọn method theo type của argument ngay lúc biên dịch.

Overload thông thường được chọn theo kiểu tĩnh lúc biên dịch (khác lời gọi dùng `dynamic`). Generics giữ thông tin kiểu tại runtime và vẫn có thể gọi interface/virtual; không nên kết luận mọi hoạt động generic đều được chốt hoàn toàn lúc compile.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| interface | caller thấy contract | nhiều implementation không cần base chung |
| abstract base | chia sẻ khung + extension points | thêm coupling với base |
| new method | che tên theo kiểu khai báo | không thay virtual slot; tránh dùng để sửa lỗi override |

### Misconception check

**Đúng hay sai?** Nonvirtual Format khiến subclass không thể khai báo tên Format khác.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: vẫn có thể hide; lời gọi qua base/interface dùng contract đã định nghĩa.

</details>

**Đúng hay sai?** Private balance làm cả giao dịch tự atomic với mọi lỗi.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: history allocation có thể lỗi sau thay balance; sample không là sổ tài chính bền.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** bốn mục đích.

- **Working Developer — dùng khi làm việc:** dispatch và public contract.

- **Deep Dive — có thể quay lại sau:** exception safety cùng lifecycle.

### Bốn trụ cột phát biểu theo mục đích

| Trụ cột | Câu hỏi nó trả lời | Sai lầm thường gặp |
|---|---|---|
| Encapsulation | Ai được phép đổi state này, và qua thao tác nào? | property `get; set;` cho mọi field |
| Abstraction | Caller cần biết tối thiểu những gì? | interface sao chép nguyên class |
| Inheritance | Phần khung nào chắc chắn chung cho cả họ? | kế thừa chỉ để dùng lại một method |
| Polymorphism | Chỗ nào cần thay implementation mà không sửa caller? | `switch` theo type ở khắp nơi |

### Access modifier và ý định thiết kế

| Modifier | Ai thấy được | Dùng khi |
|---|---|---|
| `private` | chỉ trong type | mặc định cho state |
| `protected` | type và lớp con | điểm mở rộng dành riêng cho lớp con |
| `internal` | trong assembly | chi tiết nội bộ của một thư viện |
| `public` | mọi nơi | hợp đồng bạn cam kết duy trì |

`protected` là một dạng public dành cho lớp con: một khi đã `protected`, bạn không đổi được nó tự do nữa.

### `override`, `new` và overload

```csharp
public class Base
{
    public virtual string Describe() => "base";
}

public class Derived : Base
{
    public override string Describe() => "derived"; // thay hành vi thật
}

public class Shadowing : Base
{
    public new string Describe() => "shadow";       // chỉ che tên, không thay hành vi
}
```

Với `Base b = new Derived();` thì `b.Describe()` trả `"derived"`. Với `Base b = new Shadowing();` thì `b.Describe()` trả `"base"` — vì `new` không tham gia virtual dispatch. Overload thì khác hẳn: cùng tên nhưng khác parameter list, và compiler chọn ngay lúc biên dịch.

### `sealed` là một quyết định thiết kế

Các implementation trong sample đều `sealed`. Ý nghĩa: “class này không được thiết kế để kế thừa tiếp”. Mở một class cho kế thừa nghĩa là bạn phải giữ nguyên hành vi của mọi method `virtual` về sau. Nếu chưa có nhu cầu rõ, `sealed` là mặc định an toàn hơn.

### Encapsulation ở mức trên class

Cùng một ý tưởng áp dụng cho namespace, project và module: chỉ một phần nhỏ được `public`, phần còn lại `internal`. Bài [coupling và cohesion](./09-coupling-va-cohesion.md) sẽ đo hệ quả của việc lộ quá nhiều.

## 6. Lỗi thường gặp

### Coi getter/setter là encapsulation

`public decimal Balance { get; set; }` không bảo vệ gì hơn một public field. Hãy hỏi: “có state nào có thể bị đặt sai từ bên ngoài không?” Nếu có, đóng setter lại và mở method mang tên nghiệp vụ.

### Tạo interface cho mọi class theo phản xạ

`IStoreCredit` chỉ có duy nhất `StoreCredit` implement và không ai cần thay thế thì chỉ là một file thừa. Tạo abstraction khi có ít nhất một trong hai: đã có nhiều implementation thật, hoặc cần cắt phụ thuộc vào thứ khó chạy trong test (file, network, đồng hồ hệ thống).

### Kế thừa để dùng lại code

“`OrderExporter` cần method `FormatMoney` của `ReceiptFormatterBase`, thôi thì kế thừa cho nhanh” — đây là nguồn của những cây kế thừa vô lý. Nếu quan hệ không phải “là một”, hãy tách method đó ra một type riêng rồi dùng qua composition.

### Gọi method `virtual` trong constructor

Khi constructor base gọi virtual, thân constructor lớp con chưa hoàn tất; field initializer của lớp con có thể đã chạy, nhưng state do thân constructor thiết lập thì chưa. Hãy để việc gọi virtual sau khi object đã dựng xong, hoặc truyền dữ liệu cần thiết qua parameter của constructor.

### Dùng `new` khi định `override`

Nếu quên `virtual` ở base, compiler gợi ý thêm `new` để hết cảnh báo. Thêm `new` làm code compile nhưng hành vi phụ thuộc type khai báo của biến — nguồn bug rất khó thấy. Hãy sửa base cho `virtual`, hoặc thiết kế lại bằng interface.

### `protected` field thay vì `protected` method

`protected decimal _total;` cho lớp con quyền sửa state trực tiếp và phá invariant của base. Hãy giữ field `private`, mở ra `protected` method có kiểm tra.

### Polymorphism giả bằng `switch` theo type

```csharp
if (formatter is CsvReceiptFormatter) { /* xử lý riêng */ }
```

Mỗi type mới lại thêm một nhánh, và các nhánh đó nằm rải rác khắp code. Nếu hành vi khác nhau theo type, hãy đặt hành vi đó vào chính type.

### Cây kế thừa quá sâu

Ba tầng trở lên thì việc đọc một method phải nhảy qua nhiều file, và không ai chắc `virtual` nào còn được override ở đâu. Ưu tiên một tầng base mỏng cộng composition.

## 7. Khi nào KHÔNG dùng

Không tạo interface 1–1 cho mọi class. Không ép JSON vào khung nối header/dòng/footer chỉ để tái sử dụng loop; interface trực tiếp có thể đơn giản hơn.

## 8. Production notes & scale check

CSV demo chỉ nhận SKU tin cậy không dấu phẩy/nháy/newline và culture đã nêu. Dữ liệu ngoài cần escaping, culture invariant và chính sách spreadsheet. Wallet chạy tuần tự, không có durability; test thiếu tiền không đổi balance/history và wrapper từ chối Clear.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Formatter thứ ba

Viết `JsonReceiptFormatter : IReceiptFormatter` dùng `System.Text.Json` đã học ở Module 05 và thêm vào mảng trong `Main`. JSON có cấu trúc riêng, không cần ép vào khung header/dòng/footer.

**Gợi ý:** dùng serializer để xử lý dấu nháy và ký tự xuống dòng; giữ caller dùng interface, giải thích vì sao không cần kế thừa base cho định dạng này.

### Bài 2 — Bịt lỗ hổng encapsulation

Cho class sau, hãy chỉ ra hai cách phá invariant rồi sửa lại:

```csharp
public sealed class Wallet
{
    public decimal Balance { get; set; }
    public List<string> History { get; } = new();
}
```

**Gợi ý:** thử gán số âm, và thử thêm một dòng lịch sử không tương ứng với thay đổi số dư nào.

### Bài 3 — `override` và `new`

Viết ba class như phần kiến thức nền, gọi qua biến kiểu base và kiểu con, in kết quả và giải thích từng dòng.

**Gợi ý:** thêm một mảng `Base[]` chứa cả hai loại; quan sát dòng nào đổi hành vi, dòng nào không.

### Bài 4 — Tách abstraction từ nhu cầu

`Main` cần “gửi chứng từ đi” qua email hoặc lưu file. Hãy định nghĩa interface tối thiểu cho việc đó và giải thích vì sao bạn không đưa `SmtpHost` hay `FilePath` vào interface.

**Gợi ý:** viết trước đoạn code trong `Main` mà bạn muốn có, rồi mới rút ra interface từ nó.

### Bài 5 — Chọn công cụ đúng

Với ba tình huống sau, quyết định dùng inheritance, composition hay chỉ cần một method: (a) hai loại chiết khấu khác công thức; (b) một loại chứng từ cần thêm mã QR; (c) mọi formatter cần ghi log số ký tự đã sinh.

**Gợi ý:** với (c), hỏi xem việc ghi log có thuộc trách nhiệm của formatter không; hãy để dành câu trả lời đầy đủ tới bài 3 và bài 4 rồi so lại.

## 10. Bài tập tích hợp liên module — Judgment

Từ delegate Module05, khi một formatter chỉ có một operation thì delegate có đủ không? So chi phí giữ base khung và interface riêng khi thêm định dạng JSON.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Encapsulation bảo vệ điều gì?
2. Ai chọn FormatLine lúc chạy?
3. Receipt record có deep immutable không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phát biểu được bốn trụ cột theo mục đích thiết kế.
- [ ] Tôi chỉ ra được invariant nào đang được encapsulation bảo vệ trong một class.
- [ ] Tôi thiết kế interface từ nhu cầu của caller, không từ implementation.
- [ ] Tôi biết phần nào nên `abstract`, phần nào `virtual`, phần nào khóa cứng.
- [ ] Tôi giải thích được vì sao `override` tham gia virtual dispatch còn `new` thì không.
- [ ] Tôi nhận ra `switch` theo type là polymorphism bị bỏ lỡ.
- [ ] Tôi build/run được sample trên `net9.0` và đối chiếu đúng output.

Điều hướng:

- Bài prerequisite: [Mô hình hóa đối tượng](./01-mo-hinh-hoa-doi-tuong.md)
- Ôn lại nền tảng: [Kế thừa và đa hình](../04-csharp-co-ban/09-inheritance-polymorphism.md), [Abstract class, interface và composition](../04-csharp-co-ban/10-abstract-class-va-interface.md)
- Bài tiếp theo: [Composition over inheritance](./03-composition-over-inheritance.md)
