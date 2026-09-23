# Design by contract và invariant

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, invariant hoặc adapter; CI failure

## TL;DR

- Design by contract ghi nghĩa vụ caller và bảo đảm state sau thao tác.
- Dùng guard runtime cho input, assert cho giả định nội bộ.
- Assert Debug không bảo vệ Release; overflow cũng là đường phá invariant.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- viết hợp đồng của một method gồm precondition, postcondition và lỗi có thể xảy ra;
- xác định invariant của một type và bảo vệ nó tại constructor cùng mọi method thay đổi state;
- phân biệt **vi phạm hợp đồng** (bug của người gọi) với **từ chối nghiệp vụ** (kết quả hợp lệ);
- chọn đúng loại exception cho từng dạng vi phạm, và chọn kiểu trả về cho từng dạng từ chối;
- dùng `Debug.Assert` cho giả định nội bộ mà không biến nó thành cơ chế kiểm tra input;
- áp dụng fail fast để lỗi lộ ra gần nơi gây ra nó;
- giảm số hợp đồng phải viết bằng cách thiết kế type khiến trạng thái sai không biểu diễn được.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Kho có10 món, giữ12 là không thể. Mỗi thao tác phải nói trước nhận gì và hứa sau đó còn bao nhiêu hàng/giữ chỗ; người điều tra nhìn hai con số để tìm lần đầu lời hứa bị phá.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| invariant | quan hệ đúng trước/sau API | 0<=Reserved<=OnHand |
| precondition | đầu vào/trạng thái được phép | Ship quantity<=Reserved |
| postcondition | quan hệ state sau operation | Ship giảm cả hai |
| assert | kiểm giả định để phát hiện bug | Debug.Assert |

### Ví dụ nhỏ — tính tay trước

OnHand10,R0 →reserve8 →10,8,available2 →ship3 →7,5,available2. Ship6 bị chặn và giữ7,5. Receive vượt int.MaxValue ném trước assignment.

Kho hàng theo dõi hai con số cho mỗi SKU: số lượng đang có (`OnHand`) và số lượng đã giữ chỗ cho đơn hàng (`Reserved`). Ba điều phải luôn đúng:

1. `OnHand >= 0`;
2. `Reserved >= 0`;
3. `Reserved <= OnHand` — không thể giữ chỗ nhiều hơn số hàng thực có.

Điều thứ ba là thứ hay hỏng nhất, và khi nó hỏng thì hậu quả không xuất hiện ngay. Kho báo còn hàng, đơn được nhận, tới lúc lấy hàng mới phát hiện thiếu, và không ai truy được thao tác nào đã làm sai.

Cách viết thường gặp làm hỏng chuyện này:

```csharp
public sealed class StockItem
{
    public int OnHand { get; set; }     // ai cũng gán được, kể cả số âm
    public int Reserved { get; set; }   // và không ai kiểm tra quan hệ giữa hai số
}
```

Design by contract trả lời ba câu hỏi cho từng thao tác: **người gọi phải bảo đảm gì**, **thao tác hứa gì**, và **điều gì luôn đúng trước lẫn sau mọi thao tác**. Câu hỏi thứ ba chính là invariant.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project `.NET 9`:

```bash
mkdir DesignByContractDemo
cd DesignByContractDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `DesignByContractDemo.csproj` bằng:

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
using System.Diagnostics;
using System.Globalization;

namespace DesignByContractDemo;

public sealed class StockItem
{
    private int _onHand;
    private int _reserved;

    /// <summary>
    /// Precondition: sku không rỗng; onHand không âm.
    /// Postcondition: OnHand = onHand, Reserved = 0.
    /// </summary>
    public StockItem(string sku, int onHand)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sku);
        ArgumentOutOfRangeException.ThrowIfNegative(onHand);

        Sku = sku.Trim().ToUpperInvariant();
        _onHand = onHand;
        _reserved = 0;

        AssertInvariants();
    }

    public string Sku { get; }

    public int OnHand => _onHand;

    public int Reserved => _reserved;

    public int Available => _onHand - _reserved;

    /// <summary>
    /// Precondition: quantity > 0 (vi phạm là bug của caller).
    /// Postcondition: OnHand tăng đúng quantity; Reserved không đổi.
    /// OverflowException nếu tổng vượt int.MaxValue; state giữ nguyên.
    /// </summary>
    public void Receive(int quantity)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity);

        int reservedBefore = _reserved;
        _onHand = checked(_onHand + quantity);

        Debug.Assert(_reserved == reservedBefore, "Receive must not change Reserved.");
        AssertInvariants();
    }

    /// <summary>
    /// Precondition: quantity > 0.
    /// Từ chối nghiệp vụ (không phải lỗi): thiếu hàng khả dụng -> trả false kèm lý do.
    /// Postcondition khi thành công: Reserved tăng đúng quantity, OnHand không đổi.
    /// </summary>
    public bool TryReserve(int quantity, out string reason)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity);

        if (quantity > Available)
        {
            reason = $"only {Available} available, requested {quantity}";
            return false;
        }

        _reserved += quantity;
        reason = "reserved";

        AssertInvariants();
        return true;
    }

    /// <summary>
    /// Precondition: quantity > 0 và quantity &lt;= Reserved.
    /// Gọi khi Reserved không đủ là dùng sai object -> InvalidOperationException.
    /// Postcondition: OnHand và Reserved cùng giảm đúng quantity.
    /// </summary>
    public void Ship(int quantity)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity);

        if (quantity > _reserved)
        {
            throw new InvalidOperationException(
                $"{Sku}: cannot ship {quantity}; only {_reserved} reserved.");
        }

        _reserved -= quantity;
        _onHand -= quantity;

        AssertInvariants();
    }

    /// <summary>
    /// Precondition: quantity > 0 và quantity &lt;= Reserved.
    /// Postcondition: Reserved giảm đúng quantity; OnHand không đổi.
    /// </summary>
    public void ReleaseReservation(int quantity)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity);

        if (quantity > _reserved)
        {
            throw new InvalidOperationException(
                $"{Sku}: cannot release {quantity}; only {_reserved} reserved.");
        }

        _reserved -= quantity;

        AssertInvariants();
    }

    public override string ToString() =>
        $"{Sku}: onHand={_onHand}, reserved={_reserved}, available={Available}";

    // Invariant của type: kiểm tra ở mọi lối ra của thao tác thay đổi state.
    // Đây là giả định nội bộ, không phải công cụ kiểm tra input của người dùng.
    [Conditional("DEBUG")]
    private void AssertInvariants()
    {
        Debug.Assert(_onHand >= 0, "OnHand must never be negative.");
        Debug.Assert(_reserved >= 0, "Reserved must never be negative.");
        Debug.Assert(_reserved <= _onHand, "Reserved must never exceed OnHand.");
    }
}

// Dữ liệu do người dùng nhập: sai là chuyện bình thường, không phải bug.
public sealed record ReservationRequest(string Sku, int Quantity)
{
    public static bool TryParse(
        string? rawSku,
        string? rawQuantity,
        out ReservationRequest? request,
        out IReadOnlyList<string> errors)
    {
        var found = new List<string>();

        if (string.IsNullOrWhiteSpace(rawSku))
        {
            found.Add("SKU không được để trống.");
        }

        if (!int.TryParse(rawQuantity, NumberStyles.Integer, CultureInfo.InvariantCulture, out int quantity))
        {
            found.Add("Số lượng phải là số nguyên.");
        }
        else if (quantity <= 0)
        {
            found.Add("Số lượng phải lớn hơn 0.");
        }

        errors = found;
        if (found.Count > 0)
        {
            request = null;
            return false;
        }

        request = new ReservationRequest(rawSku!.Trim().ToUpperInvariant(), quantity);
        return true;
    }
}

internal static class Program
{
    private static void Main()
    {
        var item = new StockItem("keyboard", onHand: 10);
        Console.WriteLine(item);

        item.Receive(5);
        Console.WriteLine($"after receive 5      -> {item}");

        Console.WriteLine($"reserve 12: {item.TryReserve(12, out string first)} ({first})");
        Console.WriteLine($"after reserve 12     -> {item}");

        Console.WriteLine($"reserve 5:  {item.TryReserve(5, out string second)} ({second})");

        item.Ship(4);
        Console.WriteLine($"after ship 4         -> {item}");

        item.ReleaseReservation(8);
        Console.WriteLine($"after release 8      -> {item}");

        Console.WriteLine("--- vi phạm hợp đồng ---");
        Report(() => item.Receive(0));
        Report(() => item.Ship(99));
        Report(() => new StockItem("mouse", -1));

        Console.WriteLine("--- dữ liệu người dùng ---");
        PrintParse("keyboard", "3");
        PrintParse("", "abc");
        PrintParse("mouse", "0");
    }

    private static void Report(Action action)
    {
        try
        {
            action();
            Console.WriteLine("no exception");
        }
        catch (ArgumentException ex)
        {
            // Message của helper có thêm dòng "Actual value was ..."; chỉ lấy dòng đầu.
            Console.WriteLine($"{ex.GetType().Name}: {ex.Message.Split('\n')[0]}");
        }
        catch (InvalidOperationException ex)
        {
            Console.WriteLine($"{ex.GetType().Name}: {ex.Message}");
        }
    }

    private static void PrintParse(string sku, string quantity)
    {
        bool ok = ReservationRequest.TryParse(sku, quantity, out ReservationRequest? request, out IReadOnlyList<string> errors);
        Console.WriteLine(ok
            ? $"ok: {request!.Sku} x{request.Quantity}"
            : $"invalid: {string.Join(" ", errors)}");
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
KEYBOARD: onHand=10, reserved=0, available=10
after receive 5      -> KEYBOARD: onHand=15, reserved=0, available=15
reserve 12: True (reserved)
after reserve 12     -> KEYBOARD: onHand=15, reserved=12, available=3
reserve 5:  False (only 3 available, requested 5)
after ship 4         -> KEYBOARD: onHand=11, reserved=8, available=3
after release 8      -> KEYBOARD: onHand=11, reserved=0, available=11
--- vi phạm hợp đồng ---
ArgumentOutOfRangeException: quantity ('0') must be a non-negative and non-zero value. (Parameter 'quantity')
InvalidOperationException: KEYBOARD: cannot ship 99; only 0 reserved.
ArgumentOutOfRangeException: onHand ('-1') must be a non-negative value. (Parameter 'onHand')
--- dữ liệu người dùng ---
ok: KEYBOARD x3
invalid: SKU không được để trống. Số lượng phải là số nguyên.
invalid: Số lượng phải lớn hơn 0.
```

Project được kiểm tra bằng .NET SDK `9.0.121`, target `net9.0`, không dùng package ngoài.

### Walkthrough — execution / state / cost

1. Constructor validate rồi thiết lập state ban đầu.
2. TryReserve từ chối thiếu available như kết quả nghiệp vụ, không đổi state.
3. Ship/Release kiểm điều kiện rồi cập nhật; Receive dùng checked để không wrap thành âm.
4. State gồm hai int, mỗi thao tác O(1). Debug gọi asserts; Release vẫn chạy guards và checked, không dựa vào assert để an toàn.

### Mini-check

OnHand=int.MaxValue, Reserved1: Receive1 ném; ba property phải còn giá trị nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Ba phần của một hợp đồng

Lấy `Ship` làm ví dụ:

```text
Precondition   (nghĩa vụ của caller): quantity > 0 và quantity <= Reserved
Postcondition  (lời hứa của method) : OnHand giảm đúng quantity
                                       Reserved giảm đúng quantity
Invariant      (luôn đúng)          : 0 <= Reserved <= OnHand
Lỗi có thể xảy ra                    : ArgumentOutOfRangeException, InvalidOperationException
```

Hợp đồng viết ra được thì người gọi mới biết mình phải làm gì, và người implement mới biết mình được phép giả định gì. Trong sample, các hợp đồng nằm trong XML doc ngay trên method, nên IntelliSense hiển thị chúng tại call site.

### Vi phạm hợp đồng và từ chối nghiệp vụ là hai chuyện khác nhau

| Tình huống | Bản chất | Cách báo | Ví dụ trong sample |
|---|---|---|---|
| `quantity = 0` | bug của caller | `ArgumentOutOfRangeException` | `Receive(0)` |
| Gọi `Ship` khi chưa giữ chỗ | dùng sai vòng đời object | `InvalidOperationException` | `Ship(99)` |
| Không đủ hàng khả dụng | kết quả nghiệp vụ hợp lệ | giá trị trả về + lý do | `TryReserve(12)` rồi `TryReserve(5)` |
| Người dùng gõ `"abc"` | dữ liệu ngoài, sai là bình thường | danh sách lỗi, không exception | `ReservationRequest.TryParse` |

Ranh giới này quan trọng vì nó quyết định ai phải sửa gì. Hai dòng đầu là lỗi lập trình và phải được sửa trong code. Hai dòng sau là chuyện xảy ra hằng ngày và phải được xử lý mượt mà.

Một hệ quả thực tế: đừng dùng exception cho luồng bình thường. Nếu “hết hàng” xảy ra hàng nghìn lần mỗi ngày, việc ném exception vừa tốn kém vừa làm log đầy tiếng ồn.

### Invariant được kiểm tra ở đâu

`AssertInvariants` được gọi ở cuối constructor và cuối mọi method thay đổi state. Với cách đó, nếu một bản sửa trong tương lai làm hỏng quan hệ giữa hai con số, lỗi lộ ra ngay tại thao tác gây ra nó — chứ không phải ba tầng gọi sau đó.

Điều kiện để cách này hoạt động: **không có đường nào khác chạm vào state**. `_onHand` và `_reserved` là `private`, không có setter công khai, và không có method nào trả về tham chiếu tới chúng.

### `Debug.Assert` dành cho giả định nội bộ

`AssertInvariants` gắn `[Conditional("DEBUG")]` nên compiler bỏ các lời gọi khi không định nghĩa DEBUG. Method vẫn có thể tồn tại trong assembly; không được dựa vào nó để validate Release. Đó vừa là ưu điểm vừa là giới hạn:

- **Dùng** `Debug.Assert` cho những điều bạn tin là **không bao giờ** sai nếu code đúng.
- **Không dùng** nó để kiểm tra dữ liệu từ người dùng, từ file hay từ mạng — vì ở Release, việc kiểm tra sẽ biến mất.

Các lời gọi `ArgumentOutOfRangeException.ThrowIfNegativeOrZero` thì luôn chạy, kể cả Release, vì chúng bảo vệ ranh giới công khai.

### Fail fast

`new StockItem("mouse", -1)` ném ngay tại constructor. Nếu để object được tạo với `-1` rồi mới phát hiện lúc xuất hàng, bạn sẽ phải điều tra ngược qua nhiều tầng để tìm ai đã tạo nó.

Nguyên tắc: phát hiện càng gần nguyên nhân càng tốt. Chi phí điều tra một lỗi tăng rất nhanh theo khoảng cách giữa nơi gây lỗi và nơi lỗi lộ ra.

### Đào sâu (có thể quay lại sau)

#### Quy tắc thừa kế hợp đồng

Hợp đồng còn ràng buộc quan hệ subtype, đúng như [bài 6](./06-liskov-substitution.md): lớp con **không được** thắt chặt precondition và **không được** nới lỏng postcondition. Nếu `StockItem` có lớp con yêu cầu `quantity` phải chia hết cho 10, code viết theo hợp đồng gốc sẽ hỏng.

#### Kiểm tra postcondition

C# không có cú pháp postcondition sẵn. Cách thực dụng: chụp lại giá trị trước khi thay đổi rồi khẳng định sau khi thay đổi, như dòng `reservedBefore` trong `Receive`. Chỉ làm điều này cho các bất biến quan trọng, vì nó tốn code; phần lớn postcondition được kiểm chứng bằng test thay vì bằng assert.

#### Khiến trạng thái sai không biểu diễn được

Cách tốt hơn cả kiểm tra là làm cho trạng thái sai **không tồn tại**:

- dùng `enum` để đặt tên lựa chọn (vẫn cần từ chối số enum chưa định nghĩa) thay `string` cho tập giá trị đóng, như `DeliverySpeed` ở [bài 12](./12-code-smell-va-refactoring.md);
- dùng value object có validation, như `Money` ở [bài 1](./01-mo-hinh-hoa-doi-tuong.md), thay vì `decimal` trần;
- tách type theo trạng thái: một `DraftOrder` không có method `Ship` thì không thể ship đơn nháp.

Mỗi hợp đồng bạn xóa được bằng cách chọn type đúng là một hợp đồng không thể bị vi phạm.

#### Hợp đồng ở ranh giới hệ thống

Với dữ liệu đến từ HTTP, file hay message queue, luôn phải kiểm tra thật ở runtime — không thể tin bên gọi. Ranh giới đó cũng là nơi biến dữ liệu thô thành type đã được xác thực; từ bên trong trở đi, code làm việc với type đã hợp lệ. Các module về web sẽ dựng lại đúng mô hình này.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| validation runtime | xử lý input sai dự kiến | cần cả Release |
| Debug.Assert | báo giả định nội bộ bị phá | không thay guard/rollback |
| type constraint | loại bớt trạng thái biểu diễn | vẫn có null/enumunknown/ownership cần kiểm |

### Misconception check

**Đúng hay sai?** Nhận lượng dương luôn khiến OnHand tăng hợp lệ.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: tổng có thể overflow int.

</details>

**Đúng hay sai?** Assert sau mutation tự sửa state nếu sai.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chỉ phát hiện; phải validate/tính candidate trước commit.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** pre/post/invariant.

- **Working Developer — dùng khi làm việc:** failure-state và checked.

- **Deep Dive — có thể quay lại sau:** concurrency contract nếu có caller song song.

### Chọn loại exception

| Loại | Dùng khi | Ví dụ helper trong .NET |
|---|---|---|
| `ArgumentNullException` | tham số `null` không được phép | `ArgumentNullException.ThrowIfNull` |
| `ArgumentException` | tham số sai định dạng/rỗng | `ArgumentException.ThrowIfNullOrWhiteSpace` |
| `ArgumentOutOfRangeException` | giá trị ngoài khoảng cho phép | `ThrowIfNegative`, `ThrowIfNegativeOrZero` |
| `InvalidOperationException` | object đang ở trạng thái không cho phép thao tác | — |
| Exception nghiệp vụ riêng | lỗi có ý nghĩa với nghiệp vụ và cần xử lý riêng | tự định nghĩa |

Đừng ném `Exception` trần: người gọi không thể bắt có chọn lọc.

### Cách viết hợp đồng đủ dùng

Với mỗi method công khai, viết ba dòng:

```csharp
/// Precondition: ...
/// Postcondition: ...
/// Ném: ... khi ...
```

Nếu không viết nổi một trong ba dòng, thường là method đang làm quá nhiều việc hoặc khái niệm chưa rõ. Bản thân việc viết hợp đồng đã là một bài kiểm tra thiết kế.

### Bốn nơi invariant hay bị rò rỉ

1. Setter công khai (`public int OnHand { get; set; }`).
2. Trả tham chiếu tới collection nội bộ, cho phép sửa từ ngoài.
3. Field `protected` cho lớp con sửa trực tiếp.
4. Deserialization tạo object mà không đi qua constructor.

Ba cái đầu đã gặp ở các bài trước. Cái thứ tư đáng nhớ khi làm việc với JSON: hãy kiểm tra lại invariant sau khi nạp dữ liệu, vì bộ deserializer có thể gán thẳng vào property.

### `Try...` hay exception

Quy ước trong .NET:

- `TryX(out ...)` khi thất bại là chuyện thường xuyên và người gọi luôn muốn xử lý.
- Method ném exception khi thất bại là bất thường và người gọi thường không xử lý được tại chỗ.

Cung cấp cả hai (`Parse` và `TryParse`) là mẫu quen thuộc khi cả hai tình huống đều phổ biến.

## 6. Lỗi thường gặp

### Dùng exception cho luồng nghiệp vụ bình thường

“Hết hàng”, “sai mật khẩu”, “mã giảm giá không hợp lệ” đều là kết quả bình thường. Trả về giá trị mô tả kết quả; giữ exception cho tình huống ngoài dự kiến.

### Dùng `Debug.Assert` để kiểm tra input

Ở bản Release, assert biến mất và dữ liệu sai đi thẳng vào hệ thống. Assert là lưới an toàn cho lập trình viên, không phải cổng kiểm tra dữ liệu.

### Bắt rồi nuốt exception

```csharp
try { item.Ship(quantity); } catch { }
```

Vi phạm hợp đồng bị che giấu, và dữ liệu sai vẫn tiếp tục lan. Nếu thật sự có lý do bỏ qua, hãy bắt đúng loại exception và ghi log kèm ngữ cảnh.

### Kiểm tra lại ở khắp nơi

Nếu mọi method nội bộ đều kiểm tra lại cùng một điều kiện, code trở nên nhiễu. Kiểm tra tại **ranh giới công khai**; bên trong, hãy tin vào invariant mà bạn đã bảo vệ.

### Hợp đồng chỉ nằm trong đầu người viết

Một precondition không được viết ra sẽ bị người khác vi phạm sau ba tháng. Viết vào XML doc, hoặc tốt hơn, biến nó thành ràng buộc của type.

### Thông điệp lỗi không có ngữ cảnh

`throw new InvalidOperationException("Invalid")` không giúp gì. Sample nêu rõ SKU, số lượng yêu cầu và số lượng thực có — đủ để tái hiện sự cố.

### Invariant được kiểm tra nhưng state vẫn hỏng

Nếu bạn kiểm tra invariant **trước** khi thay đổi thay vì sau, hoặc quên gọi ở một nhánh, lỗi vẫn lọt. Hãy kiểm tra ở mọi lối ra của thao tác thay đổi state.

### Ném exception từ constructor rồi để object nửa vời

Lời gọi new không trả object nếu constructor ném. Tuy nhiên, constructor có thể đã làm side effect hoặc làm rò `this` trước khi ném. Validate sớm, tránh công bố object chưa dựng xong, và bảo vệ cả các đường nạp dữ liệu.

## 7. Khi nào KHÔNG dùng

Không dùng Debug.Assert thay kiểm input ngoài. Không tạo nhiều state types nếu hai guard đủ cho quy mô và làm transition rõ hơn.

## 8. Production notes & scale check

Verifier chạy chuỗi state transitions đối chiếu mô hình độc lập cả Debug/Release, kiểm overflow giữ nguyên state. Sample không thread-safe; nhiều caller cần atomicity cho check+update, không chỉ thêm assert. ReservationRequest là DTO, tạo trực tiếp vẫn có thể sai nên boundary phải dùng TryParse.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Viết hợp đồng

Viết precondition, postcondition và danh sách exception cho `TryReserve` và `ReleaseReservation` bằng lời của bạn, rồi so với XML doc trong sample.

**Gợi ý:** chú ý `TryReserve` có hai loại thất bại khác nhau; chỉ một trong hai là exception.

### Bài 2 — Thêm thao tác giữ nguyên invariant

Thêm `Adjust(int delta)` cho phép kiểm kê tăng hoặc giảm `OnHand`. Xác định điều kiện để invariant không bị phá và chọn cách báo lỗi.

**Gợi ý:** giảm `OnHand` xuống dưới `Reserved` phải bị chặn; đó là vi phạm hợp đồng hay từ chối nghiệp vụ?

### Bài 3 — Phá invariant có chủ đích

Tạm thêm một setter công khai cho `_reserved`, gọi nó với giá trị lớn hơn `OnHand`, chạy ở cấu hình Debug và quan sát assert. Sau đó xóa setter.

**Gợi ý:** chạy `dotnet run -c Debug`; ghi lại thông điệp assert và giải thích vì sao nó không xuất hiện ở Release.

### Bài 4 — Tách validation khỏi model

Mở rộng `ReservationRequest.TryParse` để gom tất cả lỗi thay vì dừng ở lỗi đầu tiên, rồi in danh sách lỗi cho người dùng.

**Gợi ý:** sample đã gom theo cách đó; hãy thêm quy tắc “SKU tối đa 20 ký tự” và kiểm tra thứ tự thông báo.

### Bài 5 — Trạng thái sai không biểu diễn được

Thiết kế lại `StockItem` sao cho không thể `Ship` khi chưa `Reserve`, bằng cách dùng type thay vì kiểm tra runtime. Nêu ưu nhược điểm.

**Gợi ý:** một `Reservation` do `TryReserve` trả về, và `Ship` chỉ nhận `Reservation`; nghĩ tới việc ai giữ đối tượng đó và điều gì xảy ra nếu ship hai lần.

## 10. Bài tập tích hợp liên module — Judgment

So integer overflow C/C++ và checked C#: runtime từ chối có giữ state cũ tự động không, phụ thuộc vị trí assignment nào? Đề xuất test bắt lỗi Receive trước bản sửa.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. False và exception khác contract nào?
2. Available giữ nguyên sau Ship vì sao?
3. Release bỏ phần nào của assert?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi viết được ba phần hợp đồng cho một method bất kỳ.
- [ ] Tôi phân biệt vi phạm hợp đồng với từ chối nghiệp vụ và chọn đúng cách báo.
- [ ] Tôi xác định invariant của type và bảo vệ nó ở constructor lẫn mọi thao tác thay đổi state.
- [ ] Tôi dùng `Debug.Assert` đúng phạm vi và biết nó biến mất ở Release.
- [ ] Tôi để lỗi lộ ra càng gần nguyên nhân càng tốt.
- [ ] Tôi biết cách giảm số hợp đồng bằng cách thiết kế type chặt hơn.
- [ ] Tôi build/run được sample trên `net9.0` và đối chiếu đúng output.

Điều hướng:

- Bài prerequisite: [Code smell và refactoring](./12-code-smell-va-refactoring.md)
- Ôn lại nền tảng: [Exception và xử lý lỗi](../04-csharp-co-ban/12-exception-va-xu-ly-loi.md), [Nullable reference type](../05-csharp-nang-cao/06-nullable-reference-type.md)
- Bài tiếp theo: [Dự án: refactor ứng dụng C#](./14-du-an-refactor-ung-dung-csharp.md)
