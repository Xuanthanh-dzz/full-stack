# Cú pháp, biến và kiểu dữ liệu

## 1. Mục tiêu

Sau bài này, bạn có thể:

- khai báo, khởi tạo, đọc và cập nhật biến với tên có ý nghĩa;
- chọn type số phù hợp cho số lượng, tiền, đo lường và cờ logic;
- phân biệt `var`, explicit type, `const` và nullable value type;
- hiểu implicit conversion, explicit conversion và nguy cơ mất dữ liệu;
- dùng `TryParse` để biến text không tin cậy thành dữ liệu có kiểu;
- dùng `checked` hoặc type rộng hơn để phát hiện/tránh integer overflow;
- không suy luận sai rằng value type luôn nằm trên stack.

## 2. Bài toán mở đầu

Một quầy hàng nhận số lượng và đơn giá dưới dạng text từ command line. Hệ thống phải:

- từ chối text không phải số, số lượng ngoài tồn kho hoặc giá không hợp lệ;
- tính giảm giá và tổng tiền chính xác;
- tính điểm thưởng mà không bị overflow;
- chuyển tổng tiền sang số VND nguyên để gửi sang thiết bị chỉ nhận `int`.

Nếu chọn type hoặc conversion tùy tiện, `"abc"` có thể làm chương trình dừng, `double` có thể tạo sai số không phù hợp với tiền, còn phép nhân hai `int` có thể overflow trước khi được gán sang `long`.

## 3. Lời giải bằng code

Tạo project:

```bash
dotnet new console --name SafeOrder --framework net9.0 --use-program-main
cd SafeOrder
```

Thay `Program.cs` bằng:

```csharp
using System.Globalization;

namespace SafeOrder;

internal static class Program
{
    private static void Main(string[] args)
    {
        // Command line luôn đi vào chương trình dưới dạng string.
        string quantityText = args.Length > 0 ? args[0] : "3";
        string priceText = args.Length > 1 ? args[1] : "249900.50";

        const byte stock = 12;
        const decimal discountRate = 0.10m;

        bool quantityIsValid = int.TryParse(
            quantityText,
            NumberStyles.Integer,
            CultureInfo.InvariantCulture,
            out int quantity);

        bool priceIsValid = decimal.TryParse(
            priceText,
            NumberStyles.Number,
            CultureInfo.InvariantCulture,
            out decimal unitPrice);

        if (!quantityIsValid || quantity <= 0 || quantity > stock)
        {
            Console.WriteLine($"Quantity must be an integer from 1 to {stock}.");
            return;
        }

        // Giới hạn miền dữ liệu còn giúp conversion sang int ở dưới an toàn.
        if (!priceIsValid || unitPrice < 0m || unitPrice > 100_000_000m)
        {
            Console.WriteLine("Unit price must be from 0 to 100000000.");
            return;
        }

        decimal subtotal = quantity * unitPrice;
        decimal discountAmount = subtotal * discountRate;
        var grandTotal = subtotal - discountAmount; // var vẫn có static type decimal.

        // Ép một toán hạng sang long TRƯỚC phép nhân để phép nhân diễn ra bằng long.
        long rewardPoints = checked((long)quantity * 1_500_000_000L);

        // Thiết bị chỉ nhận số nguyên VND. Quy tắc làm tròn phải được nêu rõ.
        decimal rounded = decimal.Round(
            grandTotal,
            decimals: 0,
            mode: MidpointRounding.AwayFromZero);
        int payableVnd = checked((int)rounded);

        int remainingStock = stock - quantity; // byte được implicit convert sang int.
        bool isLargeOrder = quantity >= 10;
        char sizeCode = isLargeOrder ? 'L' : 'S';

        Console.WriteLine($"Quantity: {quantity}");
        Console.WriteLine($"Unit price: {unitPrice:F2}");
        Console.WriteLine($"Discount: {discountAmount:F2}");
        Console.WriteLine($"Payable: {payableVnd} VND");
        Console.WriteLine($"Reward points: {rewardPoints}");
        Console.WriteLine($"Remaining stock: {remainingStock}");
        Console.WriteLine($"Order size: {sizeCode}");
    }
}
```

Build và chạy với dữ liệu mặc định, rồi thử dữ liệu sai:

```bash
dotnet build
dotnet run --no-build
dotnet run --no-build -- abc 100000
dotnet run --no-build -- 4 125000.75
```

Dấu `--` tách option của `dotnet run` khỏi argument gửi vào `Main`. Lần chạy mặc định có kết quả:

```text
Quantity: 3
Unit price: 249900.50
Discount: 74970.15
Payable: 674731 VND
Reward points: 4500000000
Remaining stock: 9
Order size: S
```

Project đã được kiểm tra bằng .NET SDK `9.0.119`, target `net9.0`, không dùng package ngoài.

## 4. Giải thích cơ chế

### 4.1. Biến giữ một giá trị có type xác định

Với statement:

```csharp
decimal subtotal = quantity * unitPrice;
```

- `decimal` là static type;
- `subtotal` là tên biến;
- biểu thức bên phải được tính trước;
- kết quả được gán vào storage của `subtotal`.

Compiler kiểm tra phép gán dựa trên type. Sau khi khai báo, `subtotal` không thể tự đổi thành `string`. C# là statically typed.

`var grandTotal = ...` yêu cầu compiler suy luận type từ biểu thức khởi tạo. Ở đây type được chốt là `decimal` ngay lúc compile; `var` không phải `dynamic` và không có nghĩa “không có type”. Dùng explicit type khi nó làm ý nghĩa domain rõ hơn; dùng `var` khi type đã hiển nhiên từ vế phải.

### 4.2. Text phải được parse và kiểm tra miền

`args[0]` có type `string` dù người dùng gõ `3`. `int.TryParse` thực hiện hai việc:

```text
quantityText = "3"
       |
       v
int.TryParse(..., out quantity)
       |
       +-- true  -> quantity nhận 3
       |
       +-- false -> quantity nhận 0; không ném FormatException
```

Parse thành công chỉ chứng minh text có dạng số và nằm trong range của type. Quy tắc nghiệp vụ vẫn phải kiểm tra riêng: `quantity > 0` và `quantity <= stock`.

`InvariantCulture` làm dấu âm, dấu thập phân và nhóm chữ số không phụ thuộc máy chạy. Nếu giao diện nhận số theo văn hóa người dùng, hãy parse bằng culture đã chọn rõ ràng thay vì mặc định ngẫu nhiên.

### 4.3. Conversion xảy ra trước hay sau phép toán?

Đoạn đúng:

```csharp
long rewardPoints = (long)quantity * 1_500_000_000L;
```

Sau khi một toán hạng là `long`, phép nhân dùng arithmetic của `long`. Đoạn nguy hiểm sau overflow ở `int` **trước** khi gán:

```csharp
// Sai về cơ chế nếu cả hai toán hạng là int:
long wrong = quantity * 1_500_000_000;
```

Type của biến nhận bên trái không thay đổi type dùng để tính biểu thức bên phải.

`checked` yêu cầu runtime ném `OverflowException` nếu integral arithmetic/conversion vượt range, thay vì âm thầm wrap. Tốt hơn nữa là chọn type và giới hạn input sao cho range phản ánh domain.

### 4.4. Conversion sang số nguyên cần quy tắc làm tròn

`grandTotal` có phần thập phân. Ép trực tiếp `(int)grandTotal` loại phần lẻ về phía 0, không phải làm tròn. Code gọi `decimal.Round(..., AwayFromZero)` trước, nên trường hợp `.5` có quy tắc rõ ràng, rồi mới convert.

Giới hạn `unitPrice <= 100_000_000m` và `quantity <= 12` làm tổng tối đa nhỏ hơn `int.MaxValue`; `checked` vẫn đóng vai trò hàng rào nếu domain thay đổi.

### 4.5. Một lưu ý bộ nhớ quan trọng

`int`, `decimal`, `bool`, `char` là value type; `string` là reference type. Nhưng câu “value type nằm trên stack, reference type nằm trên heap” là sai và sẽ được sửa kỹ ở bài 05.

Type quyết định **ngữ nghĩa value/reference**, không tự quyết định một vị trí duy nhất:

- local value có thể ở stack frame hoặc CPU register theo quyết định JIT;
- value-type field được lưu inline bên trong object chứa nó;
- phần tử value type được lưu inline trong array;
- value type bị boxing sẽ nằm trong một object trên managed heap.

Ở giai đoạn này, hãy tập trung vào type và phép gán; không suy ra vị trí vật lý chỉ từ keyword `int`.

## 5. Kiến thức nền

### Nhóm type dựng sẵn

Tên C# như `int` là alias của type .NET như `System.Int32`.

| Nhóm | Type thường dùng | Khi dùng |
|---|---|---|
| Số nguyên có dấu | `sbyte`, `short`, `int`, `long` | đếm, ID số, chênh lệch |
| Số nguyên không dấu | `byte`, `ushort`, `uint`, `ulong` | byte dữ liệu hoặc domain thực sự không âm; đừng dùng chỉ để né validation |
| Số thực nhị phân | `float`, `double` | đo lường/khoa học, chấp nhận sai số biểu diễn |
| Số thập phân | `decimal` | tiền và phép tính thập phân cần quy tắc rõ |
| Logic | `bool` | `true` hoặc `false` |
| Ký tự UTF-16 code unit | `char` | một code unit; không đảm bảo là một ký tự người dùng nhìn thấy hoàn chỉnh |
| Chuỗi | `string` | text; immutable reference type |
| Gốc của type system | `object` | có thể tham chiếu/box mọi type; mất tính chuyên biệt khi lạm dụng |

Các range hay dùng:

| Type | Kích thước | Range xấp xỉ/chính |
|---|---:|---|
| `byte` | 8 bit | 0 đến 255 |
| `int` | 32 bit | -2,147,483,648 đến 2,147,483,647 |
| `long` | 64 bit | khoảng -9.22e18 đến 9.22e18 |
| `float` | 32 bit | khoảng 6–9 chữ số có nghĩa |
| `double` | 64 bit | khoảng 15–17 chữ số có nghĩa |
| `decimal` | 128 bit | khoảng 28–29 chữ số có nghĩa |

### Literal và hậu tố

```csharp
int count = 1_000;           // _ chỉ để dễ đọc
long population = 8_000_000_000L;
uint mask = 0xFFu;
float ratio = 0.5f;
double measurement = 0.5;   // mặc định của literal có dấu chấm
decimal money = 19.95m;
char grade = 'A';            // nháy đơn
string label = "Grade A";    // nháy kép
bool active = true;
```

Không trộn `decimal` trực tiếp với `double`; chọn một miền số có chủ đích và dùng suffix đúng.

### `const`, biến read-only theo ý nghĩa và magic number

`const` yêu cầu compile-time constant và không thể gán lại. `discountRate` là quy tắc cố định trong lần build nên phù hợp. Giá đọc từ database không thể là `const` dù nghiệp vụ coi nó ít đổi.

Đưa literal có ý nghĩa thành tên giúp code tự giải thích. `0.10m` rải khắp code là magic number; `discountRate` cho biết nó đại diện điều gì.

### Implicit và explicit conversion

- **Implicit conversion** được compiler cho phép khi có conversion định nghĩa sẵn và không cần syntax cast, ví dụ `int` sang `long`. “Implicit” không đảm bảo mọi giá trị được biểu diễn chính xác trong mọi cặp, ví dụ số nguyên lớn sang `float` có thể bị làm tròn.
- **Explicit conversion** cần cast vì có thể mất range/precision, ví dụ `long` sang `int`, `decimal` sang `int`.
- **Parsing** chuyển text thành type và có thể thất bại do format/range; đó không chỉ là numeric cast.

### Scope, khởi tạo và nullable value type

Biến local chỉ dùng được trong block `{}` nơi nó được khai báo và các block con phù hợp. Compiler áp dụng definite assignment: local phải chắc chắn được gán trước khi đọc.

`int?` là `Nullable<int>` và có thể mang một `int` hoặc `null`:

```csharp
int? optionalAge = null;
```

`null` nên biểu diễn “không có giá trị”, không nên thay thế tùy tiện bằng `0` nếu `0` là dữ liệu hợp lệ. Nullable reference type sẽ được học sâu ở module 05.

### Quy tắc đặt tên

- local/parameter: `camelCase`, ví dụ `unitPrice`;
- type/method/property: `PascalCase`, ví dụ `TryParse`;
- tên mô tả domain và đơn vị: `timeoutSeconds`, `priceVnd` tốt hơn `x`, `value`;
- keyword có phân biệt hoa thường: `string` đúng, `String` là type name, còn `STRING` không tồn tại mặc định.

## 6. Lỗi thường gặp

### Dùng `int.Parse` với input không tin cậy

`int.Parse("abc")` ném exception. Với lỗi nhập liệu dự kiến, dùng `TryParse`, kiểm tra `bool`, rồi kiểm tra miền nghiệp vụ.

### Dùng `double` cho tiền mà không có quyết định thiết kế

Nhiều phân số thập phân không biểu diễn chính xác bằng binary floating point. Dùng `decimal` cho tiền thông thường và quy định rounding tại ranh giới nghiệp vụ.

### Gán sang `long` rồi tưởng phép nhân đã dùng `long`

`long result = intA * intB;` vẫn nhân bằng `int`. Cast một toán hạng trước phép toán hoặc khai báo toán hạng `long`.

### Tin rằng default unchecked overflow sẽ báo lỗi

Integral overflow runtime thường wrap trong unchecked context. Dùng `checked`, bật overflow checks phù hợp, chọn type rộng và validate range.

### Dùng cast để “sửa” lỗi type

`(int)price` có thể cắt phần lẻ hoặc vượt range. Trước mỗi cast, trả lời ba câu: dữ liệu nào mất, quy tắc rounding nào, range đầu ra nào hợp lệ.

### Nhầm `var` với dynamic typing

`var value = 10;` vẫn là `int`; `value = "ten"` không compile. `var` chỉ bỏ phần tên type khỏi source khi compiler suy luận được.

### So sánh input theo culture ngẫu nhiên

`"12,50"` có nghĩa khác nhau giữa locale. API/command line nên chỉ định format/culture; UI địa phương hóa phải parse theo culture của người dùng một cách tường minh.

### Tin value type luôn ở stack

Đó là shortcut sai. Storage phụ thuộc local, field, array, boxing, capture và tối ưu JIT. Bài 05 sẽ vẽ từng trường hợp.

## 7. Bài tập

### Bài 1 — Tính hóa đơn có VAT

Nhận `quantity`, `unitPrice`, `vatRate` từ argument; validate rồi in tổng trước và sau VAT.

**Gợi ý:** parse VAT bằng `decimal`; giới hạn rate từ `0` đến `1`; dùng `InvariantCulture`.

### Bài 2 — Chứng minh overflow xảy ra trước phép gán

Tạo hai `int` đủ lớn, nhân chúng và so sánh phiên bản `int * int` với `(long)int * int` trong cả `checked` và `unchecked`.

**Gợi ý:** mỗi trường hợp nên nằm trong block riêng; bắt đầu với `50_000 * 50_000`; quan sát exception thay vì đoán.

### Bài 3 — Bộ chuyển đổi dung lượng

Nhận số byte kiểu `long`, in số KiB và MiB dạng `double` với hai chữ số thập phân.

**Gợi ý:** dùng `1024.0` để tránh integer division; từ chối số âm và text vượt range.

### Bài 4 — Chính sách làm tròn

Với các giá trị `12.5m`, `13.5m`, `-12.5m`, so sánh `ToEven`, `AwayFromZero` và cast sang `int`.

**Gợi ý:** in ba cột và ghi nhận cast là truncation, không phải rounding.

### Bài 5 — Dữ liệu tùy chọn

Nhận tuổi dưới dạng `string`; text rỗng được ánh xạ thành `int? = null`, còn text khác phải là tuổi 0–150.

**Gợi ý:** tách ba trạng thái: không có dữ liệu, dữ liệu hợp lệ, dữ liệu sai; không dùng `0` thay `null`.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi chọn được `int`, `long`, `double` hoặc `decimal` và giải thích lý do.
- [ ] Tôi phân biệt `var`, explicit type và `const`.
- [ ] Tôi parse input bằng `TryParse` rồi validate domain riêng.
- [ ] Tôi chỉ ra type thực hiện phép toán trước khi nhìn type bên trái phép gán.
- [ ] Tôi dùng `checked` và conversion có chủ đích.
- [ ] Tôi không còn khẳng định value type luôn nằm trên stack.

Điều hướng:

- Prerequisite: [.NET 9 và chương trình C# đầu tiên](./01-dotnet-9-va-chuong-trinh-csharp.md)
- Bài tiếp theo: [Toán tử, điều kiện và vòng lặp](./03-toan-tu-dieu-kien-vong-lap.md)
