# Inheritance và polymorphism

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, culture hoặc serialization; CI failure

## TL;DR

- Kế thừa cho phép dùng derived qua base contract; virtual chọn implementation theo object runtime.
- Dùng khi các cách giao hàng thực sự đáp ứng cùng phép tính phí.
- Upcast không clone hoặc cắt bỏ phần derived như copy base value trong C++.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- Tạo derived class bằng cú pháp `: BaseClass` và gọi base constructor bằng `base(...)`.
- Phân biệt member được kế thừa, member truy cập được và state thuộc phần base của object.
- Dùng `virtual`/`override` để có runtime polymorphism.
- Giải thích vai trò của compile-time type và runtime type khi gọi method.
- Dùng `base.Member()` để tái sử dụng implementation của base class mà không tạo object thứ hai.
- Dùng `sealed class` và `sealed override` khi cần đóng điểm mở rộng.
- Hiểu rằng class object trong C# không bị “object slicing” khi gán derived reference cho base variable.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một quầy hỏi mọi đơn vị giao hàng cùng câu “phí là bao nhiêu?”. Câu hỏi chung, nhưng đơn vị thực trả lời theo cách riêng. Không cần đổi loại object chỉ để gọi qua tên chung.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| base/derived | kiểu nền và kiểu mở rộng contract | ShippingMethod/ExpressShipping |
| virtual/override | cho phép và cung cấp hành vi runtime | CalculateFee |
| upcast | nhìn derived qua kiểu base | ShippingMethod reference |
| sealed override | khóa việc override tiếp member | phí quốc tế |

### Ví dụ nhỏ — tính tay trước

Express mức2, nặng2.5kg: phí nền25000+20000=45000; thêm60000 →105000. Cùng object nhìn qua ShippingMethod vẫn cho105000.

Một hệ thống bán hàng cần báo giá nhiều cách giao hàng:

- Giao tiêu chuẩn dùng công thức cơ sở.
- Giao nhanh dùng công thức cơ sở cộng phụ phí.
- Giao nhanh quốc tế tiếp tục cộng phí quốc tế.
- Nhận tại cửa hàng miễn phí.

Màn hình báo giá phải duyệt một mảng duy nhất và gọi cùng một method, không viết chuỗi `if/else` kiểm tra từng loại. Đồng thời, mỗi loại vẫn có thể thay đổi cách tính của mình.

Đây là lúc inheritance mô tả quan hệ “là một loại của” (`is-a`) và runtime polymorphism chọn implementation dựa trên object thật.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project .NET 9:

```bash
mkdir csharp-polymorphism-demo
cd csharp-polymorphism-demo
dotnet new console --framework net9.0
# Thay toàn bộ Program.cs bằng code bên dưới.
dotnet build
dotnet run
```

`Program.cs`:

```csharp
using System;

internal static class Program
{
    private static void Main()
    {
        const decimal weightKg = 2.5m;

        // Mảng có compile-time element type là ShippingMethod.
        // Mỗi ô có thể trỏ tới object của một derived type khác nhau.
        ShippingMethod[] options =
        [
            new ShippingMethod("Standard"),
            new ExpressShipping(priorityLevel: 1),
            new InternationalExpressShipping("Singapore", priorityLevel: 1),
            new StorePickup("District 1")
        ];

        Console.WriteLine($"Quote for {weightKg} kg:");
        foreach (ShippingMethod option in options)
        {
            // Runtime dispatch chọn override theo runtime type của object.
            option.PrintQuote(weightKg);
        }

        ExpressShipping express = new ExpressShipping(priorityLevel: 2);
        ShippingMethod selected = express; // Upcast: chỉ copy reference.

        Console.WriteLine(
            $"\nUpcast keeps the same object: {ReferenceEquals(express, selected)}");
        Console.WriteLine(
            $"Runtime type: {selected.GetType().Name}; " +
            $"fee: {selected.CalculateFee(weightKg):N0} VND");

        // selected.PriorityLevel không compile vì compile-time type là ShippingMethod.
        // Object vẫn giữ member đó; pattern matching truy cập an toàn.
        if (selected is ExpressShipping expressDetails)
        {
            Console.WriteLine($"Priority level: {expressDetails.PriorityLevel}");
        }
    }
}

internal class ShippingMethod
{
    public string Name { get; }

    public ShippingMethod(string name)
    {
        if (string.IsNullOrWhiteSpace(name))
        {
            throw new ArgumentException("Name must not be empty.", nameof(name));
        }

        Name = name.Trim();
    }

    public virtual decimal CalculateFee(decimal weightKg)
    {
        EnsureValidWeight(weightKg);
        return 25_000m + (weightKg * 8_000m);
    }

    public virtual string GetEstimatedDeliveryTime()
    {
        return "3-5 days";
    }

    public void PrintQuote(decimal weightKg)
    {
        // Hai lời gọi virtual này vẫn dispatch đến override của runtime type.
        Console.WriteLine(
            $"{Name,-22} | {CalculateFee(weightKg),10:N0} VND | " +
            $"{GetEstimatedDeliveryTime()}");
    }

    protected static void EnsureValidWeight(decimal weightKg)
    {
        if (weightKg <= 0m)
        {
            throw new ArgumentOutOfRangeException(
                nameof(weightKg),
                "Weight must be positive.");
        }
    }
}

internal class ExpressShipping : ShippingMethod
{
    public int PriorityLevel { get; }

    public ExpressShipping(int priorityLevel)
        : this("Express", priorityLevel)
    {
    }

    // Constructor protected cho derived type đặt tên cụ thể hơn,
    // nhưng consumer bình thường vẫn dùng constructor public ở trên.
    protected ExpressShipping(string name, int priorityLevel)
        : base(name)
    {
        if (priorityLevel is < 1 or > 3)
        {
            throw new ArgumentOutOfRangeException(
                nameof(priorityLevel),
                "Priority level must be from 1 to 3.");
        }

        PriorityLevel = priorityLevel;
    }

    public override decimal CalculateFee(decimal weightKg)
    {
        // base gọi implementation ShippingMethod trên cùng object hiện tại.
        decimal standardFee = base.CalculateFee(weightKg);
        decimal prioritySurcharge = PriorityLevel * 30_000m;
        return standardFee + prioritySurcharge;
    }

    public override string GetEstimatedDeliveryTime()
    {
        return PriorityLevel >= 2 ? "Same day" : "1-2 days";
    }
}

internal class InternationalExpressShipping : ExpressShipping
{
    public string DestinationCountry { get; }

    public InternationalExpressShipping(string destinationCountry, int priorityLevel)
        : base("International express", priorityLevel)
    {
        if (string.IsNullOrWhiteSpace(destinationCountry))
        {
            throw new ArgumentException(
                "Destination country must not be empty.",
                nameof(destinationCountry));
        }

        DestinationCountry = destinationCountry.Trim();
    }

    // Derived class khác vẫn có thể kế thừa class này, nhưng không thể override
    // CalculateFee thêm nữa vì override này đã sealed.
    public sealed override decimal CalculateFee(decimal weightKg)
    {
        return base.CalculateFee(weightKg) + 120_000m;
    }

    public override string GetEstimatedDeliveryTime()
    {
        return $"2-4 days to {DestinationCountry}";
    }
}

// Không class nào có thể kế thừa StorePickup.
internal sealed class StorePickup : ShippingMethod
{
    public string StoreName { get; }

    public StorePickup(string storeName)
        : base("Store pickup")
    {
        StoreName = string.IsNullOrWhiteSpace(storeName)
            ? throw new ArgumentException("Store name must not be empty.", nameof(storeName))
            : storeName.Trim();
    }

    public override decimal CalculateFee(decimal weightKg)
    {
        EnsureValidWeight(weightKg);
        return 0m;
    }

    public override string GetEstimatedDeliveryTime()
    {
        return $"Ready in 2 hours at {StoreName}";
    }
}
```

Kết quả chính:

```text
Quote for 2.5 kg:
Standard               |     45,000 VND | 3-5 days
Express                |     75,000 VND | 1-2 days
International express  |    195,000 VND | 2-4 days to Singapore
Store pickup           |          0 VND | Ready in 2 hours at District 1

Upcast keeps the same object: True
Runtime type: ExpressShipping; fee: 105,000 VND
Priority level: 2
```

### Walkthrough — execution / state / cost

1. Main tạo bốn object derived/base rồi duyệt qua ShippingMethod.
2. PrintQuote gọi virtual CalculateFee; runtime chọn theo object thật.
3. InternationalExpress thêm120000 trên Express; StorePickup trả0 với weight hợp lệ.
4. List/reference giữ object sống; dispatch không copy object. Cost phép tính cố định, format/output theo text; hierarchy thêm chi phí hiểu contract.

### Mini-check

Tại sao cast để xem PriorityLevel không cần tạo object Express mới?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1 Derived object chứa state của cả base và derived type

`ExpressShipping : ShippingMethod` nghĩa `ExpressShipping` kế thừa contract/implementation thích hợp từ `ShippingMethod`. Một `ExpressShipping` object có state cần cho cả hai phần:

```text
Managed heap
+--------------------------------------+
| ExpressShipping object               |
|                                      |
| Base-class state:                    |
|   Name reference -> "Express"       |
|                                      |
| Derived-class state:                 |
|   PriorityLevel = 2                  |
+--------------------------------------+
```

Không có một `ShippingMethod` object riêng nằm bên cạnh `ExpressShipping`. “Phần base” và “phần derived” cùng thuộc một object có runtime type `ExpressShipping`.

Private member của base vẫn là state/implementation của object, nhưng source code trong derived class không được truy cập trực tiếp. Derived class dùng public/protected contract của base.

### 4.2 Chuỗi constructor và `base(...)`

Khi chạy:

```csharp
new ExpressShipping(2)
```

trình tự khái niệm là:

1. Runtime cấp bộ nhớ cho toàn bộ `ExpressShipping` object.
2. Constructor chain đi tới base constructor trước.
3. `ShippingMethod("Express")` validate và gán `Name`.
4. Thân constructor `ExpressShipping` validate và gán `PriorityLevel`.
5. Reference tới object hoàn tất được trả về.

`: base("Express")` chọn constructor của base class. Nếu base không có parameterless constructor, derived constructor bắt buộc chỉ rõ constructor base phù hợp.

### 4.3 Compile-time type và runtime type

Xét:

```csharp
ExpressShipping express = new ExpressShipping(2);
ShippingMethod selected = express;
```

- Compile-time type của `selected` là `ShippingMethod`: compiler chỉ cho truy cập member mà contract này công khai.
- Runtime type của object được trỏ tới là `ExpressShipping`: virtual dispatch dùng type này để chọn override.

Do đó `selected.CalculateFee(...)` gọi `ExpressShipping.CalculateFee`, nhưng `selected.PriorityLevel` không compile vì `ShippingMethod` không hứa có member đó.

```text
Stack frame Main                       Managed heap
+----------------------+               +---------------------------+
| express:  reference -+-------------->| ExpressShipping object    |
| selected: reference -+-------------->| Name, PriorityLevel, ...  |
+----------------------+               +---------------------------+
```

Hai biến giữ cùng reference; `ReferenceEquals` trả `true`.

### 4.4 Runtime polymorphism với `virtual` và `override`

Base class đánh dấu extension point:

```csharp
public virtual decimal CalculateFee(decimal weightKg) { ... }
```

Derived class thay implementation có chủ đích:

```csharp
public override decimal CalculateFee(decimal weightKg) { ... }
```

Khi code gọi virtual member qua base reference, runtime tra implementation phù hợp nhất theo runtime type:

```text
option runtime type                 Implementation được gọi
----------------------------------------------------------------
ShippingMethod                     ShippingMethod.CalculateFee
ExpressShipping                    ExpressShipping.CalculateFee
InternationalExpressShipping       InternationalExpressShipping.CalculateFee
StorePickup                        StorePickup.CalculateFee
```

Nhờ vậy vòng `foreach` không cần biết từng concrete type. Thêm một derived type đúng contract không buộc sửa vòng lặp báo giá.

`PrintQuote` không phải virtual, nhưng bên trong nó gọi hai virtual method trên `this`; các lời gọi đó vẫn được dispatch đến override của object thật.

### 4.5 `base` không trỏ tới object khác

Trong `ExpressShipping.CalculateFee`:

```csharp
decimal standardFee = base.CalculateFee(weightKg);
```

`base` yêu cầu compiler gọi implementation của base class cho **cùng object hiện tại**. Nó không tạo/copy `ShippingMethod`, cũng không đổi runtime type của object. Ta tái sử dụng validation và công thức cơ sở rồi cộng phụ phí.

### 4.6 `sealed class` và `sealed override`

- `sealed class StorePickup` cấm mọi class kế thừa `StorePickup`.
- `sealed override CalculateFee` cấm derived class tiếp theo override riêng method đó, dù có thể kế thừa class chứa method.

Dùng `sealed` khi invariant không an toàn nếu tiếp tục mở rộng, behavior phải cố định, hoặc type vốn không được thiết kế làm base. Không dùng chỉ để “tối ưu hiệu năng” nếu chưa có đo đạc và lý do thiết kế.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| virtual override | chọn theo runtime type | hợp thay hành vi qua base |
| overload | chọn theo signature tại compile | không thay runtime dispatch |
| new member hiding | che tên theo static type | dễ gây bất ngờ; không dùng thay override |

### Misconception check

**Đúng hay sai?** Gán Express vào biến ShippingMethod làm mất PriorityLevel khỏi object.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chỉ giới hạn member nhìn qua reference base.

</details>

**Đúng hay sai?** Method không virtual trong base không thể gọi hành vi derived.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: PrintQuote không virtual nhưng gọi CalculateFee virtual.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** base reference và dispatch.

- **Working Developer — dùng khi làm việc:** contract thay thế, validation.

- **Deep Dive — có thể quay lại sau:** thiết kế hierarchy khi có driver.

### 5.1 Quan hệ `is-a` và khả năng thay thế

Chỉ kế thừa khi mọi object của derived type có thể được dùng hợp lý ở nơi base type được yêu cầu. `ExpressShipping is a ShippingMethod` hợp lý vì vẫn tính phí/giao hàng theo contract đó.

“Tái sử dụng vài dòng code” không đủ để tạo quan hệ inheritance. Nếu quan hệ thật là “có một” (`has-a`), composition thường đúng hơn; bài tiếp theo sẽ minh họa.

### 5.2 C# chỉ cho class kế thừa một class

Một class có tối đa một direct base class. Nếu không ghi rõ, base cuối cùng là `object`. C# không có multiple class inheritance, nhưng một class có thể implement nhiều interface.

### 5.3 Member nào polymorphic?

Instance method/property/event chỉ runtime-polymorphic khi base member là `virtual`/`abstract` và derived member dùng `override`. Constructor và static member không được override.

### 5.4 Override phải giữ contract

Derived override phải giữ precondition/postcondition hợp lý của base contract. Nếu code dùng `ShippingMethod` kỳ vọng fee không âm, mọi derived type cũng phải bảo đảm fee không âm. Một override buộc caller biết concrete type để tránh lỗi đã phá khả năng thay thế.

Đây là nền tảng của Liskov Substitution Principle, được học sâu trong module thiết kế.

### 5.5 Ép kiểu an toàn

Cast trực tiếp có thể ném `InvalidCastException`:

```csharp
ExpressShipping express = (ExpressShipping)option;
```

Khi chưa chắc runtime type, ưu tiên pattern matching `is`. Nếu logic liên tục phải cast để chọn behavior, đó thường là dấu hiệu contract base còn thiếu operation polymorphic hoặc mô hình abstraction chưa phù hợp.

### Đào sâu (có thể quay lại sau)

#### Không có object slicing khi upcast class reference

Trong C++, copy một derived object vào một base object theo value có thể làm mất phần derived (“object slicing”). Với C# class:

```csharp
ShippingMethod selected = express;
```

phép gán chỉ copy reference. Không có object mới và không phần nào bị cắt. `PriorityLevel` vẫn nằm trong object; nó chỉ không xuất hiện qua compile-time API của biến `selected`.

Pattern matching lấy lại một reference có type hẹp hơn sau khi runtime check:

```csharp
if (selected is ExpressShipping details)
{
    Console.WriteLine(details.PriorityLevel);
}
```

Downcast không khôi phục dữ liệu đã mất vì dữ liệu chưa từng mất. Nó chỉ yêu cầu runtime xác nhận object có type tương thích.

Member không virtual được chọn theo compile-time type. Nếu derived class khai báo member cùng tên bằng `new`, đó là **method hiding**, không phải polymorphism. Kết quả thay đổi theo kiểu của biến và thường gây bất ngờ; đổi tên hoặc dùng virtual/override nếu behavior cần dispatch.

#### Đừng gọi virtual member từ constructor

Base constructor chạy trước khi derived constructor hoàn tất. Nếu base constructor gọi virtual method, runtime có thể dispatch vào override đang đọc derived field chưa được khởi tạo, gây lỗi khó hiểu. Tránh virtual call trong constructor; hoàn tất construction trước rồi mới chạy behavior polymorphic.

## 6. Lỗi thường gặp

### 6.1 Quên `virtual` hoặc `override`

Một method cùng tên không tự trở thành override. Compiler có thể cảnh báo member đang hide base member. Ghi rõ ý định bằng `virtual`/`override`; đừng dập cảnh báo bằng `new` nếu bạn cần runtime dispatch.

### 6.2 Nghĩ base reference biến object thành base object

Upcast không tạo/copy object. Runtime type và toàn bộ state derived còn nguyên; chỉ compile-time view hẹp lại.

### 6.3 Cast mọi phần tử để gọi behavior

Chuỗi `if (x is A) ... else if (x is B) ...` ở consumer làm mất lợi ích polymorphism. Nếu behavior thuộc contract chung, đưa virtual/abstract member vào abstraction và để object tự thực hiện.

### 6.4 Dùng inheritance chỉ để tái sử dụng code

`Report : DatabaseConnection` không hợp lý chỉ vì report cần query database; report **có một** dependency connection/repository, không phải là connection. Dùng composition.

### 6.5 Base class để lộ quá nhiều `protected` state

Protected field khiến derived class phụ thuộc representation và có thể phá invariant. Ưu tiên private field cùng protected method/property được thiết kế rõ làm extension point.

### 6.6 Override làm yếu invariant

Nếu derived method trả fee âm hoặc bỏ validation trọng lượng, caller dùng base contract nhận behavior không hợp lệ. Giữ contract và test tất cả implementation qua cùng bộ test hành vi.

### 6.7 Gọi virtual method trong constructor

Override có thể chạy trước khi derived field được gán. Constructor chỉ nên thiết lập state; gọi polymorphic behavior sau khi object đã hoàn tất.

### 6.8 Lạm dụng cây kế thừa sâu

Cây nhiều tầng làm behavior bị phân tán qua nhiều class và `base` call. Giữ hierarchy nông; khi các biến thể kết hợp độc lập, composition/interface thường dễ thay đổi hơn.

## 7. Khi nào KHÔNG dùng

Không kế thừa chỉ để dùng lại vài dòng tính toán khi không có contract thay thế được. Không gọi virtual trong constructor để dựa vào state derived chưa hoàn tất.

## 8. Production notes & scale check

Bốn phương thức giao hàng đủ cho demo. Test dispatch, cận weight, priority và sealed rule. Nếu pricing thay theo cấu hình thường xuyên, trước hết so sánh một bảng rule nhỏ với hierarchy; không mặc định thêm pattern.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Nhân viên và lương

Tạo base class `Employee` có `virtual CalculateMonthlyPay()`, rồi `SalariedEmployee` và `HourlyEmployee` override. Duyệt `Employee[]` để in lương.

Gợi ý: đưa validation chung vào base constructor; dùng runtime dispatch, không dùng `if` theo type trong vòng lặp.

### Bài 2 — Constructor chain

Vẽ và kiểm chứng thứ tự constructor cho `Vehicle -> Car -> ElectricCar`. Mỗi constructor in một dòng và nhận state bắt buộc của tầng mình.

Gợi ý: constructor derived gọi `: base(...)`; dự đoán output trước khi chạy.

### Bài 3 — `base` và phụ phí

Thêm `WeekendExpressShipping` kế thừa `ExpressShipping`, dùng phí express cộng phụ phí cuối tuần. Quyết định method nào nên tiếp tục override được và method nào nên `sealed override`.

Gợi ý: gọi `base.CalculateFee()` để không lặp công thức; giải thích trade-off của việc đóng extension point.

### Bài 4 — Chứng minh không slicing

Tạo `Animal` và `Dog` có property riêng của `Dog`. Gán `Dog` vào biến `Animal`, dùng `ReferenceEquals`, `GetType()` và pattern matching để chứng minh vẫn là một object.

Gợi ý: vẽ hai reference cùng trỏ một vùng nhớ trước khi chạy.

### Bài 5 — Phát hiện inheritance sai

Phân tích ba quan hệ: `Order : List<OrderLine>`, `Car : Engine`, `CsvExporter : Exporter`. Chọn inheritance hay composition cho từng trường hợp và nêu contract thay thế.

Gợi ý: hỏi “mọi X có thực sự là Y và dùng được ở mọi nơi cần Y không?”; tái sử dụng code không phải tiêu chí duy nhất.

## 10. Bài tập tích hợp liên module — Judgment

So sánh slicing C++ Module03 với upcast C#. Hãy dự đoán phí qua base reference rồi giải thích phần nào là static type, phần nào là runtime object.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Ai chọn CalculateFee khi chạy?
2. sealed override chặn điều gì?
3. ReferenceEquals chứng minh điều gì và không chứng minh gì?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành bài khi có thể tự trả lời:

- [ ] Tôi thiết kế được derived class và constructor chain bằng `base(...)`.
- [ ] Tôi phân biệt compile-time type với runtime type.
- [ ] Tôi dự đoán đúng override nào được gọi qua base reference.
- [ ] Tôi hiểu `base.Method()` chạy trên cùng object hiện tại.
- [ ] Tôi biết mỗi class chỉ kế thừa một class.
- [ ] Tôi phân biệt override với method hiding.
- [ ] Tôi giải thích được `sealed class` và `sealed override`.
- [ ] Tôi chứng minh được upcast class reference trong C# không gây object slicing.
- [ ] Tôi nhận ra khi nào quan hệ nên dùng composition thay cho inheritance.

Điều hướng:

- Bài tiên quyết: [Property, encapsulation và access modifier](./08-property-encapsulation-va-access-modifier.md)
- Bài tiếp theo: [Abstract class và interface](./10-abstract-class-va-interface.md)
