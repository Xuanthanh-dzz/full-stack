# Property, encapsulation và access modifier

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, culture hoặc serialization; CI failure

## TL;DR

- Property cung cấp cách đọc/ghi có kiểm soát; access modifier giới hạn nơi gọi.
- Dùng operation Sell/Restock/ChangePrice thay public setter cho tồn kho.
- required, init và private giải quyết các việc khác nhau; không tự validate mọi giá trị.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- Dùng property để cung cấp API đọc/ghi có kiểm soát thay vì public field.
- Viết auto-property, computed property và property có backing field.
- Phân biệt `set`, `private set`, get-only và `init`.
- Duy trì invariant bằng constructor, property accessor và method nghiệp vụ.
- Chọn đúng `public`, `private`, `protected`, `internal`, `protected internal` và `private protected`.
- Hiểu giới hạn của encapsulation: `init` không tạo deep immutability, và access modifier không thay thế validation nghiệp vụ.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Có thông tin chỉ cần điền lúc lập phiếu, có thông tin chỉ đọc, có thông tin phải đổi qua quầy có kiểm tra. Property giúp biểu diễn từng cửa này mà không mở toàn bộ field.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| property | member có accessor đọc/ghi | Price và Stock |
| init | cho gán trong ngữ cảnh khởi tạo phù hợp | Sku |
| required | yêu cầu caller khởi tạo member | required Sku |
| access modifier | phạm vi code được phép truy cập | public/private/internal |

### Ví dụ nhỏ — tính tay trước

Stock3, Sell2 → còn1. Sell2 lần nữa bị từ chối giữ1. Đổi giá5→7 làm InventoryValue đổi5→7 khi đọc, không phải kho tự thêm hàng.

Một kho hàng quản lý sản phẩm. Nếu khai báo mọi dữ liệu là public field:

```csharp
public decimal Price;
public int Stock;
```

bất kỳ caller nào cũng có thể gán `Price = -100` hoặc `Stock = -20`. Object vẫn tồn tại nhưng không còn hợp lệ. Ta cần API thỏa các quy tắc:

- `Sku` bắt buộc, được chuẩn hóa và không được đổi sau lúc khởi tạo.
- Tên chỉ đổi qua thao tác có validation.
- Giá và tồn kho đọc được từ ngoài nhưng chỉ class được phép cập nhật.
- Tồn kho không bao giờ âm.
- Giá trị tồn kho được tính từ giá và số lượng, không lưu trùng thành state thứ ba.

Đây là bài toán bảo vệ invariant của object, không đơn thuần là đổi cú pháp field thành property.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project .NET 9:

```bash
mkdir csharp-encapsulation-demo
cd csharp-encapsulation-demo
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
        InventoryItem keyboard = new InventoryItem(
            name: "Mechanical Keyboard",
            initialPrice: 1_500_000m)
        {
            Sku = " kb-001 ",
            Description = "Hot-swappable keyboard"
        };

        keyboard.Restock(10);
        keyboard.Sell(3);
        keyboard.ChangePrice(1_400_000m);
        keyboard.Rename("Mechanical Keyboard V2");

        Console.WriteLine(keyboard.GetPublicSummary());
        Console.WriteLine($"Inventory value: {keyboard.InventoryValue:N0} VND");

        // Các dòng sau không compile, nhờ đó caller không thể phá invariant trực tiếp:
        // keyboard.Stock = -100;       // private setter
        // keyboard.Price = -1m;        // private setter
        // keyboard.Sku = "KB-999";    // init-only, object đã khởi tạo xong

        try
        {
            keyboard.Sell(100);
        }
        catch (InvalidOperationException exception)
        {
            Console.WriteLine($"Rejected: {exception.Message}");
        }

        Console.WriteLine($"Stock remains valid: {keyboard.Stock}");
    }
}

internal sealed class InventoryItem
{
    private string _sku = string.Empty;
    private string _name;

    // required buộc caller gán property trong object initializer hoặc constructor.
    // init cho phép gán trong giai đoạn khởi tạo, không cho đổi về sau.
    public required string Sku
    {
        get => _sku;
        init
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                throw new ArgumentException("SKU must not be empty.", nameof(value));
            }

            _sku = value.Trim().ToUpperInvariant();
        }
    }

    // Auto-property init-only. String là immutable, nhưng property này vẫn có thể null.
    public string? Description { get; init; }

    // Getter public, setter private: caller chỉ đọc; class vẫn cập nhật được.
    public string Name
    {
        get => _name;
        private set => _name = NormalizeName(value);
    }

    public decimal Price { get; private set; }
    public int Stock { get; private set; }

    // Get-only auto-property được gán khi tạo object.
    public DateTimeOffset CreatedAtUtc { get; } = DateTimeOffset.UtcNow;

    // Computed property: không lưu field riêng, luôn tính từ state hiện tại.
    public decimal InventoryValue => Price * Stock;

    public InventoryItem(string name, decimal initialPrice)
    {
        _name = NormalizeName(name);
        EnsureValidPrice(initialPrice);
        Price = initialPrice;
    }

    public void Rename(string newName)
    {
        Name = newName;
    }

    public void ChangePrice(decimal newPrice)
    {
        EnsureValidPrice(newPrice);
        Price = newPrice;
    }

    public void Restock(int quantity)
    {
        EnsurePositiveQuantity(quantity);
        Stock = checked(Stock + quantity);
    }

    public void Sell(int quantity)
    {
        EnsurePositiveQuantity(quantity);

        if (quantity > Stock)
        {
            throw new InvalidOperationException(
                $"Cannot sell {quantity}; only {Stock} item(s) available.");
        }

        Stock -= quantity;
    }

    public string GetPublicSummary()
    {
        return $"{Sku} | {Name} | price {Price:N0} | stock {Stock}";
    }

    // Chỉ code trong cùng assembly mới gọi được member này.
    internal string GetAuditSummary()
    {
        return $"{GetPublicSummary()} | created {CreatedAtUtc:O}";
    }

    private static string NormalizeName(string value)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new ArgumentException("Name must not be empty.", nameof(value));
        }

        return value.Trim();
    }

    private static void EnsureValidPrice(decimal price)
    {
        if (price < 0m)
        {
            throw new ArgumentOutOfRangeException(
                nameof(price),
                "Price must not be negative.");
        }
    }

    private static void EnsurePositiveQuantity(int quantity)
    {
        if (quantity <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(quantity),
                "Quantity must be positive.");
        }
    }
}
```

Kết quả chính:

```text
KB-001 | Mechanical Keyboard V2 | price 1,400,000 | stock 7
Inventory value: 9,800,000 VND
Rejected: Cannot sell 100; only 7 item(s) available.
Stock remains valid: 7
```

### Walkthrough — execution / state / cost

1. Object initializer điền Sku, init accessor chuẩn hóa mã.
2. Restock10 rồi Sell3 giữ Stock7; ChangePrice cập nhật giá1.4M.
3. InventoryValue tính lại Price×Stock khi đọc; Sell100 ném lỗi trước mutation.
4. State nằm trong một item; required được compiler kiểm tra, validation runtime vẫn cần. Getter tính toán có cost, không nhất thiết chỉ đọc một field.

### Mini-check

Price và Stock riêng lẻ hợp lệ nhưng Price×Stock quá miền decimal: getter có thể ném lỗi không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1 Property là API, không nhất thiết là một ô nhớ riêng

Property có cú pháp truy cập giống field:

```csharp
decimal price = keyboard.Price; // gọi getter
```

nhưng về mặt cơ chế, compiler phát sinh lời gọi accessor (`get`/`set`/`init`). Property có thể:

- Đọc/ghi một backing field.
- Validate và chuẩn hóa dữ liệu.
- Tính kết quả từ state khác.
- Có quyền đọc và quyền ghi khác nhau.

Ví dụ `InventoryValue => Price * Stock` không cần `_inventoryValue`. Mỗi lần đọc, getter lấy state hiện tại để tính. Nhờ không lưu dữ liệu dẫn xuất, ta tránh trường hợp giá hoặc stock đã đổi nhưng `_inventoryValue` bị quên cập nhật.

### 4.2 Auto-property và backing field

Auto-property:

```csharp
public decimal Price { get; private set; }
```

làm compiler tạo một backing field ẩn. Khi cần logic trong accessor, khai báo field rõ:

```csharp
private string _sku = string.Empty;

public required string Sku
{
    get => _sku;
    init => _sku = Normalize(value);
}
```

Caller không biết hoặc phụ thuộc cách state được lưu. Sau này bạn có thể thay implementation mà vẫn giữ API property nếu contract không đổi.

### 4.3 `set`, `private set`, get-only và `init`

Các lựa chọn thể hiện ai được đổi state và đổi lúc nào:

```csharp
public string A { get; set; }          // Mọi caller có quyền truy cập đều gán được.
public string B { get; private set; }  // Chỉ code trong declaring type gán được.
public string C { get; }               // Chỉ gán khi khai báo/constructor (auto-property).
public string D { get; init; }         // Gán trong object initialization, rồi khóa accessor.
```

`Sku` kết hợp `required` và `init`:

- `required` khiến compiler yêu cầu caller cung cấp giá trị lúc khởi tạo.
- `init` cho phép object initializer gọi accessor, nhưng assignment thông thường sau đó bị compiler từ chối.
- Logic trong `init` vẫn validate và normalize `value` trước khi lưu.

`required` là compile-time contract cho code C# tuân thủ metadata; nó không tự chứng minh dữ liệu hợp lệ. `init` cũng là hạn chế gán ở cấp ngôn ngữ, không phải cơ chế bảo mật chống reflection hoặc serializer đặc biệt.

### 4.4 Encapsulation bảo vệ invariant qua mọi mutation path

Invariant của `InventoryItem` gồm:

```text
Sku != null/rỗng
Name != null/rỗng
Price >= 0
Stock >= 0
```

Ta kiểm tra input trước khi thay đổi state:

```text
Sell(100)
   |
   +--> quantity > 0? yes
   |
   +--> quantity <= Stock? no
   |
   +--> throw exception; Stock CHƯA bị thay đổi
```

Nếu class cung cấp public setter cho `Stock`, rule này bị vòng qua. `private set` buộc caller dùng `Restock`/`Sell`, là những operation có ý nghĩa nghiệp vụ và validation đầy đủ.

Encapsulation tốt không có nghĩa “mọi thứ đều private”. Nó nghĩa object chỉ công khai contract cần thiết và tự chịu trách nhiệm giữ trạng thái hợp lệ.

### 4.5 Mô hình bộ nhớ

Sau khi tạo object:

```csharp
InventoryItem keyboard = new InventoryItem(...) { Sku = " kb-001 " };
```

mô hình đơn giản hóa là:

```text
Stack frame Main                       Managed heap
+---------------------+                +--------------------------------+
| keyboard: reference +--------------->| InventoryItem object           |
+---------------------+                | _sku:  ref ---> "KB-001"      |
                                       | _name: ref ---> "Mechanical..."|
                                       | Price: 1,400,000m              |
                                       | Stock: 7                       |
                                       | CreatedAtUtc: value            |
                                       +--------------------------------+
```

`Price` và `Stock` auto-property có backing field ẩn bên trong object. `_sku` và `_name` giữ reference tới immutable string object. Getter trả giá trị/reference theo kiểu của property; nó không clone toàn bộ `InventoryItem`.

Gọi `keyboard.Sell(3)` truyền reference của object làm receiver (`this`), rồi method cập nhật backing field `Stock` của chính object đó.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| public set | caller có quyền gán | chỉ hợp data không cần invariant riêng |
| private set + operation | chỉ type tự cập nhật | hợp stock có kiểm tra |
| required init | phải điền lúc khởi tạo | không đảm bảo nonempty hoặc đúng nghiệp vụ |

### Misconception check

**Đúng hay sai?** required tự kiểm tra Sku không rỗng.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: accessor mới thực hiện validation.

</details>

**Đúng hay sai?** get-only hoặc private set làm toàn object immutable.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: Sell vẫn có thể thay Stock theo contract.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** accessor và quyền gọi.

- **Working Developer — dùng khi làm việc:** domain validation và checked arithmetic.

- **Deep Dive — có thể quay lại sau:** invariant liên field khi có nhu cầu.

### 5.1 Bảng access modifier

| Modifier | Có thể truy cập từ đâu? | Dùng điển hình |
|---|---|---|
| `public` | Mọi code nhìn thấy type/assembly | Contract cho consumer |
| `private` | Chỉ trong declaring type | Field, helper, implementation detail |
| `protected` | Declaring type và derived type | Extension point cho kế thừa |
| `internal` | Cùng assembly | Contract nội bộ module/assembly |
| `protected internal` | Cùng assembly **hoặc** derived type ở assembly khác | API framework cần hai đường truy cập |
| `private protected` | Derived type **và** cùng assembly | Extension point giới hạn nội bộ assembly |

“Assembly” thường là output `.dll` hoặc `.exe` của một project. `protected internal` dùng phép **OR**; `private protected` dùng phép **AND**. Hai modifier kết hợp này hiếm cần trong code ứng dụng thông thường; chỉ dùng khi thật sự cần contract đó.

Top-level type thông thường dùng `public` hoặc `internal` (mặc định là `internal`). C# hiện đại còn có modifier `file` để type chỉ được truy cập trong cùng source file; đây là phạm vi hẹp chuyên biệt. Nested type có thể dùng thêm các modifier khác.

### 5.2 Chọn mức truy cập nhỏ nhất hợp lý

Bắt đầu từ `private`, mở thành `internal`, `protected` hoặc `public` khi có consumer cụ thể. Mỗi public member trở thành contract phải duy trì, kiểm thử và có thể ảnh hưởng tương thích phiên bản sau này.

Không biến member thành public chỉ để test truy cập implementation detail. Test behavior qua public contract; nếu thật sự cần contract nội bộ, tổ chức assembly và `internal` có chủ đích.

### 5.3 Setter riêng và method có ý nghĩa

`Stock { get; private set; }` ngăn caller gán tùy ý, nhưng giá trị thật đến từ các operation:

- `Restock(quantity)` nói rõ lý do stock tăng.
- `Sell(quantity)` nói rõ lý do stock giảm.
- Mỗi operation có rule và lỗi riêng.

Đây là khác biệt giữa data bag và domain object. Với DTO chỉ vận chuyển dữ liệu, public `get; set;` có thể hoàn toàn phù hợp; đừng áp dụng một quy tắc máy móc cho mọi type.

### 5.4 Validation đặt ở đâu?

- UI/API validation giúp trả lỗi thân thiện sớm.
- Domain object validation bảo vệ invariant dù object được gọi từ UI, test, job hay service khác.
- Database constraint là lớp bảo vệ cuối cho dữ liệu lưu trữ.

Các lớp này bổ sung nhau. Không bỏ rule cốt lõi khỏi object chỉ vì form đã kiểm tra.

### 5.5 `readonly` field và get-only property

`readonly` áp dụng cho field và cho phép gán khi khai báo hoặc trong constructor của declaring type. Get-only auto-property cũng thường được gán khi khai báo hoặc trong constructor. Cả hai ngăn gán lại storage/reference sau khởi tạo, nhưng không tự làm object con trở nên immutable.

Thông thường field là implementation detail (`private readonly`), còn property là contract muốn công khai.

### Đào sâu (có thể quay lại sau)

#### `init` không có nghĩa deep immutable

Nếu một init-only property giữ mutable object:

```csharp
public int[] Levels { get; init; } = [];
```

caller không thể gán `Levels = anotherArray` sau initialization, nhưng vẫn có thể làm `item.Levels[0] = 999`. `init` khóa việc đổi reference qua property, không đóng băng object được trỏ tới. Muốn immutable sâu hơn, cần chọn immutable type, defensive copy hoặc chỉ công khai read-only abstraction.

## 6. Lỗi thường gặp

### 6.1 Public field cho state cần rule

Public field không có chỗ chặn giá trị sai và khó thay đổi implementation mà không phá consumer. Dùng property/method khi dữ liệu là một phần contract có invariant.

### 6.2 Public setter phá invariant

```csharp
public int Stock { get; set; }
```

cho phép `Stock = -1`. Chỉ công khai setter nếu mọi giá trị của type đều hợp lệ hoặc object đúng là DTO mutable. Với domain behavior, dùng setter hẹp và operation có tên.

### 6.3 Validate sau khi đã thay đổi state

Sai:

```csharp
Stock -= quantity;
if (Stock < 0) throw new InvalidOperationException();
```

Sau exception, object đã mang state âm. Kiểm tra trước, rồi mới commit thay đổi.

### 6.4 Cho rằng `private set` nghĩa property không bao giờ đổi

Class vẫn có thể gán property có `private set` từ bất kỳ instance member nào. Nếu dữ liệu tuyệt đối không đổi sau construction, dùng get-only/init-only phù hợp và tránh method nội bộ gán lại.

### 6.5 Cho rằng `init` bảo đảm deep immutability

`init` chỉ hạn chế thời điểm assignment qua property. Array, list hoặc custom mutable object được giữ trong property vẫn có thể bị sửa. Xác định ownership và cân nhắc defensive copy.

### 6.6 Dùng computed value làm field và quên đồng bộ

Lưu đồng thời `Price`, `Stock`, `InventoryValue` tạo ba nguồn state. Nếu value luôn là tích, hãy tính bằng getter. Chỉ cache khi đã đo được nhu cầu và có chiến lược invalidation đúng.

### 6.7 Mở `protected` quá sớm

`protected` tạo contract cho derived class và làm base class khó thay đổi. Chỉ mở extension point đã thiết kế; ưu tiên `private` nếu derived type không thật sự cần truy cập.

### 6.8 Dựa vào access modifier như ranh giới bảo mật

`private` là ràng buộc thiết kế/ngôn ngữ, không phải authorization. Dữ liệu bí mật vẫn cần kiểm soát truy cập, mã hóa, quản lý secret và không ghi log sai cách.

## 7. Khi nào KHÔNG dùng

Không viết property setter tùy ý chỉ để có đủ getter/setter. Không dùng required thay constructor khi invariant cần nhiều field phải hợp lệ cùng nhau.

## 8. Production notes & scale check

Demo một item, test vượt kho, giá âm, checked overflow Restock và lỗi compile khi thiếu required/sửa init/private setter. InventoryValue vẫn có thể overflow với dữ liệu cực lớn; muốn đảm bảo luôn đọc được cần cận domain kết hợp.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — `Temperature`

Tạo class lưu nhiệt độ Celsius, chỉ cho phép từ `-273.15` trở lên. Công khai property `Celsius` chỉ đọc và computed property `Fahrenheit`.

Gợi ý: validate trong constructor; không lưu `Fahrenheit` thành field.

### Bài 2 — Hồ sơ người dùng

Tạo `UserProfile` có `Id` là `required init`, `DisplayName` có `private set`, `CreatedAtUtc` get-only. Viết `Rename()` trim tên và từ chối chuỗi rỗng.

Gợi ý: dùng backing field nếu muốn validation ngay trong `init` của `Id`.

### Bài 3 — Ví điện tử

Tạo `Wallet` với `Balance { get; private set; }`, `Deposit()` và `Spend()`. Bảo đảm amount dương và balance không âm kể cả khi operation ném exception.

Gợi ý: kiểm tra tất cả precondition trước assignment; viết bảng state trước/sau cho từng nhánh.

### Bài 4 — Kiểm chứng shallow immutability

Tạo class có `int[] Values { get; init; }`. Chứng minh không thể gán array mới sau initialization nhưng có thể sửa một ô. Sau đó thiết kế lại để caller không sửa được state nội bộ.

Gợi ý: clone input bằng `values[..]` và cân nhắc trả clone/read-only view; ghi rõ chi phí allocation.

### Bài 5 — Thiết kế access modifier

Cho một assembly thư viện có `Invoice`, helper tính thuế, method tạo audit text và extension point cho loại invoice đặc biệt. Chọn modifier cho từng member và giải thích consumer nào cần thấy nó.

Gợi ý: lập bảng “member — consumer — lý do”; đừng chọn `public` nếu consumer chỉ ở cùng assembly.

## 10. Bài tập tích hợp liên module — Judgment

Đối chiếu public struct C và encapsulation C++: những quyền sửa nào compiler C# ngăn, những dữ liệu sai nào vẫn phải kiểm tra runtime?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. init khác private set thế nào?
2. InventoryValue lưu sẵn hay tính lúc đọc?
3. required có thay validation không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành bài khi có thể tự trả lời:

- [ ] Tôi phân biệt field, auto-property, full property và computed property.
- [ ] Tôi chọn được `set`, `private set`, get-only hoặc `init` theo ownership state.
- [ ] Tôi dùng `required` và hiểu nó không thay validation runtime.
- [ ] Tôi giữ invariant qua constructor và mọi mutation method.
- [ ] Tôi giải thích được `init` không tạo deep immutability.
- [ ] Tôi chọn access modifier nhỏ nhất phù hợp và phân biệt `protected internal` với `private protected`.
- [ ] Tôi vẽ được backing field/value/reference nằm trong object như thế nào.

Điều hướng:

- Bài tiên quyết: [Class, object và constructor](./07-class-object-constructor.md)
- Bài tiếp theo: [Inheritance và polymorphism](./09-inheritance-polymorphism.md)
