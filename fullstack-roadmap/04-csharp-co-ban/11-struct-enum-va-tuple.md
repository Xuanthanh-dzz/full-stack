# Struct, enum và tuple trong C#

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, culture hoặc serialization; CI failure

## TL;DR

- Struct giữ value semantics; enum đặt tên giá trị; tuple gom kết quả nhỏ có quan hệ.
- Dùng Money cho amount/currency và flags cho các tùy chọn độc lập.
- default struct có thể bỏ qua constructor; enum nhận số ngoài tên đã khai báo.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng `struct` cho một giá trị nhỏ, có ngữ nghĩa độc lập và ưu tiên bất biến;
- giải thích việc gán hoặc truyền một `struct` tạo ra bản sao giá trị;
- dùng `enum` để thay số “ma thuật” bằng một tập trạng thái có tên;
- thiết kế bit flags đúng bằng `[Flags]` và các giá trị lũy thừa của hai;
- trả về nhiều giá trị bằng named tuple và biết giới hạn của cách làm này;
- phân biệt `new` với cấp phát heap: `new SomeStruct(...)` không tự động đồng nghĩa với tạo object riêng trên heap;
- nhận ra lúc boxing tạo một object mới trên heap.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một cặp tiền và đơn vị cần đi cùng nhau. Các lựa chọn ký nhận, dễ vỡ, cuối tuần có thể bật đồng thời nên mỗi lựa chọn cần một bit riêng, khác trạng thái chỉ chọn một.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| readonly struct | value type giới hạn mutation member | Money |
| enum | kiểu số có các hằng đặt tên | OrderStatus |
| flags | các bit biểu diễn lựa chọn kết hợp | DeliveryOptions |
| tuple | nhóm value trả về cùng nhau | Fee/EstimatedDays |

### Ví dụ nhỏ — tính tay trước

Ký nhận1 OR dễ vỡ2 =3; kiểm tra3 AND2 →2 nên có dễ vỡ. 1200g:20000+12000+5000+15000=52000,3 ngày.

Một hệ thống giao hàng cần tính phí và số ngày dự kiến. Dữ liệu có ba đặc điểm:

1. Tiền gồm số tiền và mã tiền tệ, phải được truyền như **một giá trị**.
2. Đơn hàng chỉ có một trạng thái tại một thời điểm.
3. Một kiện hàng có thể đồng thời cần chữ ký, là hàng dễ vỡ và giao cuối tuần.

Nếu dùng `decimal`, `int` và các `bool` rời rạc, lời gọi hàm rất dễ bị đảo tham số hoặc tạo tổ hợp trạng thái vô nghĩa. Ta sẽ mô hình hóa bằng `struct`, `enum`, flags và trả về kết quả bằng tuple.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project target `.NET 9`:

```bash
mkdir StructEnumTupleDemo
cd StructEnumTupleDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay toàn bộ `Program.cs` bằng nội dung sau:

```csharp
using System;

namespace StructEnumTupleDemo;

public enum OrderStatus
{
    Draft = 0,
    Confirmed = 1,
    Shipped = 2,
    Delivered = 3,
    Cancelled = 4
}

[Flags]
public enum DeliveryOptions
{
    None = 0,
    SignatureRequired = 1 << 0, // 0001
    Fragile = 1 << 1,           // 0010
    Weekend = 1 << 2,           // 0100
    All = SignatureRequired | Fragile | Weekend
}

// readonly ngăn việc thay đổi trạng thái của value sau khi khởi tạo.
public readonly struct Money
{
    public decimal Amount { get; }
    public string Currency { get; }

    public Money(decimal amount, string currency)
    {
        if (amount < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(amount));
        }

        if (string.IsNullOrWhiteSpace(currency))
        {
            throw new ArgumentException("Currency is required.", nameof(currency));
        }

        Amount = amount;
        Currency = currency.ToUpperInvariant();
    }

    public Money Add(decimal amount) => new(Amount + amount, Currency);

    public override string ToString() => $"{Amount:N0} {Currency}";
}

public static class ShippingCalculator
{
    public static (Money Fee, int EstimatedDays) Calculate(
        int weightGrams,
        DeliveryOptions options)
    {
        if (weightGrams <= 0)
        {
            throw new ArgumentOutOfRangeException(nameof(weightGrams));
        }

        if ((options & ~DeliveryOptions.All) != 0)
        {
            throw new ArgumentOutOfRangeException(nameof(options));
        }

        decimal amount = 20_000m + (weightGrams * 10m);
        int days = 3;

        if ((options & DeliveryOptions.SignatureRequired) != 0)
        {
            amount += 5_000m;
        }

        if ((options & DeliveryOptions.Fragile) != 0)
        {
            amount += 15_000m;
        }

        if ((options & DeliveryOptions.Weekend) != 0)
        {
            amount += 25_000m;
            days = 1;
        }

        return (new Money(amount, "VND"), days);
    }
}

internal static class Program
{
    private static void Main()
    {
        OrderStatus status = OrderStatus.Confirmed;
        DeliveryOptions options =
            DeliveryOptions.SignatureRequired | DeliveryOptions.Fragile;

        (Money fee, int days) = ShippingCalculator.Calculate(1_200, options);

        Console.WriteLine($"Status: {status}");
        Console.WriteLine($"Options: {options}");
        Console.WriteLine($"Fee: {fee}; estimated days: {days}");

        // Money là value type: phép gán sao chép toàn bộ value.
        Money copiedFee = fee;
        copiedFee = copiedFee.Add(10_000m);

        Console.WriteLine($"Original fee: {fee}");
        Console.WriteLine($"Changed copy: {copiedFee}");

        Console.WriteLine(
            $"Has fragile option: {(options & DeliveryOptions.Fragile) != 0}");

        // Boxing: tạo object chứa một bản sao của fee.
        object boxedFee = fee;
        Money unboxedFee = (Money)boxedFee;
        Console.WriteLine($"Unboxed fee: {unboxedFee}");
    }
}
```

Build rồi chạy:

```bash
dotnet build
dotnet run --no-build
```

Kết quả chính (cách định dạng số có thể khác theo locale):

```text
Status: Confirmed
Options: SignatureRequired, Fragile
Fee: 52,000 VND; estimated days: 3
Original fee: 52,000 VND
Changed copy: 62,000 VND
Has fragile option: True
Unboxed fee: 52,000 VND
```

### Walkthrough — execution / state / cost

1. Main tạo tổ hợp flags rồi gọi Calculate kiểm tra weight và bit lạ.
2. Calculator cộng phụ phí cho từng bit; tuple trả Money và số ngày.
3. Money.Add tạo value mới62000, giá trị gốc52000 không đổi.
4. Box giữ bản sao Money khi chuyển object. Tính phí kiểm tra số bit cố định; Money chứa decimal inline và reference tới currency string.

### Mini-check

Vì sao options=8 bị từ chối trong khi options=3 được chấp nhận?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### `struct` được sao chép theo giá trị

`Money` là value type. Sau lệnh `Money copiedFee = fee`, hai biến chứa hai value độc lập. `Add` tạo value mới rồi gán vào `copiedFee`; nó không thể sửa `fee`.

Mô hình khái niệm trong stack frame của `Main`:

```text
Main stack frame
┌────────────────────────────────────────────┐
│ fee       : Money { 52000, ref currency ───┼──┐
│ copiedFee : Money { 62000, ref currency ───┼──┤
│ days      : 3                              │  │
│ status    : Confirmed (underlying int = 1) │  │
│ options   : 0011                           │  │
│ boxedFee  : reference ─────────────────────┼──┼────┐
└────────────────────────────────────────────┘  │    │
                                                │    │
Managed heap                                    │    │
┌───────────────────────────────┐ <─────────────┘    │
│ string object: "VND"          │                    │
└───────────────────────────────┘                    │
┌───────────────────────────────┐ <──────────────────┘
│ boxed Money copy { 52000, ref }│
└───────────────────────────────┘
```

Sơ đồ trên phục vụ suy luận ngữ nghĩa. JIT có thể giữ value trong register hoặc tối ưu vị trí vật lý. Điều luôn đúng ở cấp ngôn ngữ là phép gán `Money` sao chép các field: `decimal` được sao chép; field `Currency` sao chép **reference**, không nhân đôi string. `string` là immutable nên hai reference cùng trỏ tới `"VND"` không gây thay đổi lẫn nhau.

`new Money(...)` chạy constructor để tạo một value đã khởi tạo. Nó không đảm bảo cấp phát heap. Vị trí value phụ thuộc nơi chứa nó:

- local có thể ở stack/register;
- phần tử `Money[]` nằm inline trong vùng nhớ của array trên heap;
- field `Money` trong một class nằm inline bên trong object của class;
- khi boxing sang `object` hoặc interface, runtime tạo object bao trên heap và chép value vào đó.

### Flags hoạt động bằng bit

`SignatureRequired | Fragile` thực hiện bitwise OR:

```text
SignatureRequired  0001
Fragile            0010
                   ---- OR
options            0011
```

Biểu thức `(options & DeliveryOptions.Fragile) != 0` dùng bitwise AND để kiểm tra bit `0010`. Giá trị flags phải là `0, 1, 2, 4, 8, ...`; nếu dùng tuần tự `0, 1, 2, 3`, giá trị `3` đã trùng tổ hợp `1 | 2`.

### Tuple cũng là value type

Cú pháp `(Money Fee, int EstimatedDays)` là `System.ValueTuple<Money, int>`. Lệnh destructuring:

```csharp
(Money fee, int days) = ShippingCalculator.Calculate(1_200, options);
```

sao chép hai phần tử vào hai biến local. Tên `Fee` và `EstimatedDays` giúp code dễ đọc, nhưng tuple không chứa invariant hoặc behavior như một type chuyên biệt.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| enum trạng thái | một giá trị trong quy trình | cần validate giá trị cast từ bên ngoài |
| flags enum | nhiều lựa chọn độc lập | dùng bit không chồng, kiểm tra unknown bits |
| tuple / named struct | nhóm tạm / domain value có contract | tuple đủ cho kết quả nhỏ; struct khi cần invariant |

### Misconception check

**Đúng hay sai?** readonly struct ngăn default(Money) có Currency null.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: default không chạy constructor có tham số.

</details>

**Đúng hay sai?** Enum.IsDefined luôn phù hợp kiểm tra flags kết hợp.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: tổ hợp hợp lệ có thể không có tên riêng; kiểm tra bit ngoài All.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** struct/enum/tuple.

- **Working Developer — dùng khi làm việc:** default và bit validation.

- **Deep Dive — có thể quay lại sau:** boxing/copy khi cần đo.

### Khi nào chọn `struct`

Một `struct` phù hợp khi value:

- biểu diễn một giá trị đơn lẻ như tọa độ, khoảng thời gian hoặc số tiền;
- có kích thước nhỏ và thường được tạo ngắn hạn;
- có ngữ nghĩa sao chép độc lập;
- tốt nhất là immutable.

Không chọn `struct` chỉ với mục tiêu “đưa dữ liệu lên stack”. Value có thể nằm trên heap như đã mô tả. Struct quá lớn bị sao chép nhiều sẽ tốn chi phí; phần nâng cao sẽ học `in`, `ref` và `readonly ref` khi đo lường cho thấy cần thiết.

Không nên tạo cây kế thừa bằng struct: struct không kế thừa class/struct khác, dù có thể implement interface. Mọi struct đều kế thừa gián tiếp từ `System.ValueType` và `object` theo hệ thống kiểu.

### `enum` và giá trị số

Mặc định underlying type của `enum` là `int`. Có thể ghi rõ, ví dụ `enum SmallCode : byte`. Runtime vẫn cho phép cast một số không được khai báo sang enum:

```csharp
OrderStatus unknown = (OrderStatus)999;
```

Vì vậy dữ liệu từ API, file hoặc database phải được validate, chẳng hạn `Enum.IsDefined(unknown)`. Đừng đổi tùy tiện giá trị số enum đã lưu trong database hoặc gửi qua API; đó là thay đổi contract.

Với flags:

- luôn có `None = 0`;
- mỗi cờ đơn dùng một bit;
- tổ hợp có thể đặt tên như `All`;
- dùng bitwise operators khi cần tránh boxing và thể hiện rõ phép kiểm tra.

### Khi nào chọn tuple

Tuple phù hợp cho kết quả cục bộ, ngắn và rõ nghĩa. Khi dữ liệu đi qua public API, cần validation, behavior, serialization ổn định hoặc sẽ phát triển thêm field, hãy tạo `class`/`struct` có tên như `ShippingQuote`.

`Tuple<T1,T2>` (class cũ) khác `ValueTuple<T1,T2>` (struct mà cú pháp `(T1, T2)` sử dụng). Trong code mới, named value tuple thường là lựa chọn gọn hơn cho kết quả nội bộ.

### Đào sâu (có thể quay lại sau)

#### `default` có thể bỏ qua constructor của struct

Mọi struct luôn có một giá trị zero-initialized tạo được bằng `default`, và phần tử của `new Money[2]` cũng bắt đầu ở trạng thái đó:

```csharp
Money empty = default;
Money[] values = new Money[2];
```

Hai value trên có `Amount == 0` và field reference đứng sau `Currency` bằng `null`, dù property được khai báo `string` non-nullable và constructor công khai đã validate currency. Constructor của `Money` không chạy cho quá trình zero-initialization này.

Vì vậy constructor không thể một mình bảo đảm mọi bit-pattern của struct là domain value hợp lệ. Khi invalid default gây rủi ro lớn, hãy thiết kế struct chịu được default, kiểm tra `IsValid` tại boundary, hoặc chọn class/factory phù hợp hơn. Không gọi `Add` trên `default(Money)` trong thiết kế hiện tại vì constructor kế tiếp sẽ từ chối currency `null`.

#### Boxing và unboxing

Boxing xảy ra khi một value type được chuyển sang `object` hoặc sang interface mà runtime cần hộp chứa:

```csharp
object boxedFee = fee;          // allocation + copy
Money value = (Money)boxedFee;  // unbox đúng type + copy value ra
```

Unbox sai exact value type sẽ ném `InvalidCastException`. Boxing trong vòng lặp nóng có thể tạo nhiều allocation và tăng áp lực garbage collector; không tối ưu theo phỏng đoán, hãy đo trước.

## 6. Lỗi thường gặp

### Dùng mutable struct rồi tưởng đang sửa object gốc

Property hoặc collection có thể trả về một bản sao struct; sửa bản sao không sửa nơi chứa. Ưu tiên `readonly struct` với property chỉ đọc và method trả về value mới.

### Cho flags các giá trị tuần tự

Sai: `Read = 1, Write = 2, Delete = 3`. `Delete` không có bit riêng. Đúng: `1 << 0`, `1 << 1`, `1 << 2`.

### So sánh flags bằng dấu `==`

`options == DeliveryOptions.Fragile` chỉ đúng khi **duy nhất** cờ `Fragile` được bật. Muốn kiểm tra cờ có mặt, dùng `(options & DeliveryOptions.Fragile) != 0`.

### Tin rằng mọi `new` đều cấp phát heap

`new` gọi cơ chế khởi tạo. Với class, `new` thông thường tạo object riêng trên managed heap; với struct, value có thể nằm inline ở nơi chứa. Boxing mới tạo object bao riêng.

### Tin constructor làm mọi struct instance hợp lệ

`default(TStruct)` và array zero-initialization không gọi constructor do bạn viết. Nếu default state không hợp lệ, type hoặc boundary phải nhận biết và xử lý trạng thái đó; nullable annotation không thay đổi dữ liệu zero-initialized ở runtime.

### Dùng tuple cho domain contract lớn

`(decimal, string, int, bool)` nhanh chóng khó đọc và khó validate. Đặt tên phần tử giúp một phần; khi contract có ý nghĩa lâu dài, tạo type có tên.

### Bỏ qua giá trị enum không hợp lệ

Cast từ `int`, deserialization hoặc dữ liệu cũ có thể tạo giá trị không được khai báo. Validate ở boundary và quyết định rõ cách xử lý unknown value.

## 7. Khi nào KHÔNG dùng

Không dùng flags cho trạng thái Draft→Confirmed nếu hai trạng thái không được đồng thời đúng. Không tạo struct lớn chỉ để có value semantics mà chưa xem cost copy.

## 8. Production notes & scale check

Demo shipping nhỏ, gate thử tổ hợp, bit lạ, weight0, default Money và copy độc lập. Constructor Money chưa loại trừ mọi trạng thái default; consumer cần quy định cách xử lý trước khi dùng value trong domain thật.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Trạng thái thanh toán

Tạo `PaymentStatus` gồm `Pending`, `Paid`, `Failed`, `Refunded`; viết method chỉ cho phép chuyển trạng thái hợp lệ.

Gợi ý: dùng `switch` trên cặp `(current, next)`; từ chối số enum không được định nghĩa.

### Bài 2 — Quyền truy cập bằng flags

Tạo `[Flags] FilePermissions` gồm `Read`, `Write`, `Execute`, `Delete`. Viết `HasPermission` và `GrantPermission` bằng toán tử bit.

Gợi ý: cấp mỗi quyền một bit và nhớ `None = 0`.

### Bài 3 — Value object kích thước

Tạo immutable `Dimensions` gồm dài, rộng, cao; validate mọi chiều lớn hơn `0` và có method tính thể tích.

Gợi ý: dùng `readonly struct`; kiểm tra xem phép gán rồi tạo value mới có làm value gốc đổi không.

### Bài 4 — Báo giá có tên

Viết method trả `(Money Subtotal, Money Tax, Money Total)`, sau đó refactor thành type `InvoiceSummary`. So sánh call site và khả năng thêm validation.

Gợi ý: tuple hợp với bản đầu nhỏ; type có tên hợp khi contract bắt đầu phát triển.

### Bài 5 — Quan sát boxing

So sánh allocation của vòng lặp cộng số qua `List<int>` và một collection không generic như `System.Collections.ArrayList` bằng `GC.GetAllocatedBytesForCurrentThread()`.

Gợi ý: warm up trước khi đo; giữ cùng số phần tử và tránh in console trong vùng đo.

## 10. Bài tập tích hợp liên module — Judgment

So với bitmask trong C Module01 và struct C++ Module03, compiler C# giúp gì, còn validation nào vẫn runtime? Chọn enum trạng thái hay flags cho trạng thái đơn hàng.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. OR và AND dùng cho mục đích nào?
2. default có gọi constructor này không?
3. Tuple trả về có làm hai biến thành reference alias không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi giải thích được vì sao gán một `struct` tạo value độc lập.
- [ ] Tôi vẽ được nơi chứa field của struct và reference bên trong struct.
- [ ] Tôi biết `new SomeStruct()` không tự động tạo object trên heap.
- [ ] Tôi thiết kế được flags không trùng bit và kiểm tra đúng một cờ.
- [ ] Tôi phân biệt được `ValueTuple` với một domain type có tên.
- [ ] Tôi mô tả được boxing, unboxing và chi phí allocation/copy.
- [ ] Tôi đã tự build/run ví dụ bằng SDK .NET 9.

Bài prerequisite: [Abstract class và interface](./10-abstract-class-va-interface.md).

Bài tiếp theo: [Exception và xử lý lỗi](./12-exception-va-xu-ly-loi.md).
