# Nullable reference type

## 1. Mục tiêu

Sau bài này, bạn có thể:

- biểu diễn rõ reference bắt buộc (`string`) và reference tùy chọn (`string?`);
- đọc các nullable warning phổ biến và sửa bằng thiết kế/flow check thay vì tắt cảnh báo;
- dùng `is not null`, pattern variable, `?.`, `??` và `??=` đúng semantics;
- hiểu toán tử null-forgiving `!` chỉ im compiler, không kiểm tra runtime;
- kết hợp annotation compile-time với runtime guard ở public boundary;
- phân biệt `string?` với nullable value type `int?`;
- vẽ reference slot có thể chứa object reference hoặc `null` mà không tạo wrapper object mới.

## 2. Bài toán mở đầu

Một chức năng import customer nhận dữ liệu không đồng đều:

- `Name` bắt buộc;
- `Email` có thể thiếu hoặc chỉ chứa khoảng trắng;
- `Address` có thể chưa được cung cấp;
- tìm theo email có thể không thấy customer.

Nếu khai báo mọi thứ là `string`, `Address`, rồi hy vọng dữ liệu luôn đủ, code dễ ném `NullReferenceException`. Nếu khai báo mọi thứ nullable, mỗi caller phải kiểm tra cả những field nghiệp vụ bảo đảm luôn có và contract trở nên yếu.

Ta cần đưa khả năng `null` vào đúng vị trí của type contract, để compiler theo dõi flow trước khi dereference. Runtime guard vẫn cần ở boundary vì caller cũ, reflection, serializer hoặc dữ liệu ngoài không bị compiler của project hiện tại kiểm soát.

## 3. Lời giải bằng code

Tạo project:

```bash
dotnet new console --name NullableDemo --framework net9.0 --use-program-main
cd NullableDemo
```

Thay `NullableDemo.csproj` bằng:

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
namespace NullableDemo;

internal static class Program
{
    private static void Main()
    {
        var customers = new List<Customer>
        {
            new Customer(
                "An",
                " AN@example.com ",
                new Address("Ha Noi")),
            new Customer("Binh", email: null, address: null),
            new Customer("Chi", email: "   ", new Address("Da Nang"))
        };

        foreach (Customer customer in customers)
        {
            string emailLabel = customer.Email ?? "(missing)";
            string cityLabel = customer.Address?.City ?? "(unknown)";
            Console.WriteLine($"{customer.Name} | {emailLabel} | {cityLabel}");

            // Pattern variable email chỉ tồn tại ở nhánh non-null.
            if (customer.Email is string email)
            {
                Console.WriteLine($"  Email length: {email.Length}");
            }
            else
            {
                Console.WriteLine("  Email missing");
            }
        }

        Customer? found = CustomerSearch.FindByEmail(customers, "an@example.com");
        Console.WriteLine($"Found: {found?.Name ?? "not found"}");

        Customer? unknown = CustomerSearch.FindByEmail(customers, "nobody@example.com");
        Console.WriteLine($"Unknown search: {unknown?.Name ?? "not found"}");

        customers[1].AssignFallbackEmail("binh@fallback.invalid");
        Console.WriteLine($"Binh fallback: {customers[1].Email}");
    }
}

internal sealed class Customer
{
    public string Name { get; }
    public string? Email { get; private set; }
    public Address? Address { get; }

    public Customer(string name, string? email, Address? address)
    {
        // Runtime guard vẫn cần dù parameter được annotate non-nullable.
        ArgumentException.ThrowIfNullOrWhiteSpace(name);

        Name = name.Trim();
        Email = EmailAddress.NormalizeOptional(email);
        Address = address;
    }

    public void AssignFallbackEmail(string fallback)
    {
        string normalizedFallback = EmailAddress.NormalizeRequired(fallback);

        // Chỉ gán khi Email hiện là null.
        Email ??= normalizedFallback;
    }
}

internal sealed class Address
{
    public string City { get; }

    public Address(string city)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(city);
        City = city.Trim();
    }
}

internal static class EmailAddress
{
    public static string? NormalizeOptional(string? input)
    {
        if (string.IsNullOrWhiteSpace(input))
        {
            return null;
        }

        return input.Trim().ToLowerInvariant();
    }

    public static string NormalizeRequired(string input)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(input);
        return input.Trim().ToLowerInvariant();
    }
}

internal static class CustomerSearch
{
    public static Customer? FindByEmail(
        IReadOnlyList<Customer> customers,
        string email)
    {
        ArgumentNullException.ThrowIfNull(customers);
        string normalizedEmail = EmailAddress.NormalizeRequired(email);

        foreach (Customer customer in customers)
        {
            if (string.Equals(
                customer.Email,
                normalizedEmail,
                StringComparison.Ordinal))
            {
                return customer;
            }
        }

        return null;
    }
}
```

Build và chạy:

```bash
dotnet build --configuration Release
dotnet run --configuration Release --no-build
```

Kết quả chính xác:

```text
An | an@example.com | Ha Noi
  Email length: 14
Binh | (missing) | (unknown)
  Email missing
Chi | (missing) | Da Nang
  Email missing
Found: An
Unknown search: not found
Binh fallback: binh@fallback.invalid
```

## 4. Giải thích cơ chế

### 4.1 Nullable context là compile-time contract

Project bật:

```xml
<Nullable>enable</Nullable>
```

Trong context này:

```csharp
string Name       // contract: reference không nên null
string? Email     // contract: null là trạng thái hợp lệ/dự kiến
```

Compiler phân tích assignment và dereference rồi phát warning khi contract có thể bị vi phạm. `TreatWarningsAsErrors` khiến warning làm build thất bại, buộc sample xử lý đầy đủ.

Annotation không tạo một runtime type `NullableString` mới. Ở CLR, cả `string` và `string?` vẫn là reference tới `System.String` hoặc `null`; nullable metadata giúp compiler/tooling trao đổi contract.

### 4.2 Flow analysis thay đổi null-state theo nhánh

Nếu viết trực tiếp:

```csharp
// Console.WriteLine(customer.Email.Length); // CS8602: có thể dereference null.
```

compiler biết `Email` có trạng thái maybe-null. Trong code đúng:

```csharp
if (customer.Email is string email)
{
    Console.WriteLine(email.Length);
}
```

pattern chỉ gán `email` khi value là một `string` non-null. Trong nhánh đó, flow state của `email` là not-null nên dereference an toàn. Ra khỏi nhánh, variable pattern hết scope.

Flow analysis theo đường điều khiển chứ không chạy chương trình. Với field/property mutable hoặc lời gọi method có side effect, compiler đôi khi thận trọng vì value có thể đổi giữa hai lần đọc. Lưu property vào local hoặc thiết kế immutable khi cần reasoning ổn định.

### 4.3 `?.`, `??` và `??=`

Ba operator giải các nhu cầu khác nhau:

```csharp
customer.Address?.City
```

- nếu `Address` là non-null, đọc `City`;
- nếu `Address` là `null`, toàn expression trả `null` thay vì ném.

```csharp
nullableValue ?? fallback
```

- trả value bên trái nếu non-null;
- nếu null mới evaluate/trả fallback bên phải.

```csharp
Email ??= normalizedFallback;
```

- chỉ gán fallback vào property khi `Email` hiện null;
- nếu đã có email, giữ nguyên.

`?.` có thể che bug nếu null thật ra là trạng thái không hợp lệ. Chỉ dùng khi contract cho phép thiếu; với reference bắt buộc, guard/fix nguồn dữ liệu thay vì nối `?.` khắp nơi.

### 4.4 Return nullable buộc caller xử lý “không tìm thấy”

`FindByEmail` trả `Customer?` vì không tìm thấy là kết quả bình thường. Caller phải kiểm tra hoặc cung cấp fallback:

```csharp
Customer? found = CustomerSearch.FindByEmail(...);
string label = found?.Name ?? "not found";
```

Nếu business yêu cầu customer chắc chắn tồn tại, một API khác như `GetRequiredByEmail` có thể trả `Customer` và ném exception phù hợp khi invariant bị vi phạm. Type contract nên phản ánh semantics, không mặc định mọi lookup đều nullable hay mọi lookup đều throw.

### 4.5 Runtime guard vẫn cần thiết

`string name` nói với caller đã bật nullable rằng không được truyền null, nhưng runtime vẫn có thể nhận null từ:

- assembly cũ/oblivious không có annotation;
- reflection hoặc serializer;
- code dùng null-forgiving sai;
- interop/dynamic boundary.

`ArgumentException.ThrowIfNullOrWhiteSpace(name)` vừa kiểm tra runtime vừa báo lỗi gần boundary. Nullable annotations cải thiện compile-time; guard bảo vệ invariant runtime. Hai lớp bổ sung nhau.

### 4.6 Null-forgiving `!` không kiểm tra runtime

Toán tử postfix `!` chỉ đổi null-state mà compiler tin:

```csharp
string? maybeName = null; // Giả lập value nhận từ một boundary không chắc chắn.
string forced = maybeName!;
```

Đây là snippet minh họa, không nằm trong code chạy. Không có `if` hay exception được chèn ở assignment. Nếu `maybeName` là null, `forced` vẫn chứa null và dereference sau đó có thể ném `NullReferenceException`.

Chỉ dùng `!` khi bạn có bằng chứng mà analyzer chưa biểu diễn được, ghi rõ invariant và ưu tiên cải thiện API/annotation. Dùng `!` để “build xanh” là anti-pattern.

### 4.7 Mô hình bộ nhớ

Với customer Binh:

```text
Main local / collection                      Managed heap
+--------------------------+                 +---------------------------+
| customers ref -----------+---------------> | List<Customer> H1         |
+--------------------------+                 | entry[1] ref ---------+   |
                                             +-----------------------|---+
                                                                     v
                                             +---------------------------+
                                             | Customer H2               |
                                             | Name ref ------> "Binh"   |
                                             | Email slot ----> null      |
                                             | Address slot --> null      |
                                             +---------------------------+
```

`Email` và `Address` là reference slot nằm trong H2. Mỗi slot chứa managed reference tới object hoặc bit pattern `null`; `string?`/`Address?` không tạo wrapper heap object. Sau `Email ??= normalizedFallback`, Email slot trỏ string object mới/được trả về từ normalize.

Flow state “maybe-null/not-null” tồn tại trong phân tích compiler, không phải một field boolean gắn cạnh reference ở runtime.

## 5. Kiến thức nền

### Nullable reference khác nullable value type

```csharp
string? email  // reference annotation; runtime reference có thể null
int? score     // shorthand của Nullable<int>, một value type có HasValue/Value
```

`int` vốn không có null value nên `int?` cần `Nullable<int>` representation. `string` vốn đã có thể là null ở runtime; `?` chủ yếu thêm compile-time contract. Hai cú pháp giống nhưng cơ chế type khác.

### Các warning thường gặp

| Warning | Ý nghĩa điển hình |
|---|---|
| `CS8600` | Convert possible null vào variable non-nullable |
| `CS8602` | Dereference reference có thể null |
| `CS8603` | Method non-nullable có thể return null |
| `CS8604` | Argument có thể null truyền vào parameter non-nullable |
| `CS8618` | Non-nullable field/property chưa chắc được khởi tạo khi constructor kết thúc |

Đọc data flow gây warning rồi sửa contract/check/initialization. Không tắt toàn bộ nullable vì một warning khó.

### Required member và constructor

Non-nullable property phải được khởi tạo trước khi object sẵn sàng. Constructor parameter là lựa chọn mạnh cho invariant bắt buộc. `required`/`init` phù hợp object initializer nhưng vẫn cần runtime validation khi dữ liệu ngoài có thể sai; chúng đã được giới thiệu ở bài property.

### Array element là bẫy runtime

`new string[2]` tạo array có hai reference slot mặc định `null`, dù element annotation là non-nullable. Compiler không thể bảo đảm mọi element đã được lấp đầy ở mọi pattern. Dùng initializer đầy đủ, `string?[]` trong giai đoạn cho phép thiếu, hoặc type/API quản lý trạng thái khởi tạo rõ ràng.

### Nullable qua generic API

Ý nghĩa `T?` phụ thuộc constraint và kind của `T`. Hãy viết constraint (`class`, `struct`, `notnull`, base/interface) phản ánh contract trước khi dùng nullable generic phức tạp. Với API thư viện nâng cao, attributes trong `System.Diagnostics.CodeAnalysis` như `NotNullWhen` có thể mô tả quan hệ flow mà signature đơn giản chưa biểu đạt; chỉ dùng khi hiểu đúng branch contract.

### Dữ liệu ngoài và domain model

DTO import có thể chứa nhiều nullable property vì dữ liệu đang chưa được validate. Sau validation, map sang domain object có non-nullable invariant mạnh. Đừng làm toàn bộ domain nullable chỉ vì JSON/form đầu vào có thể thiếu.

## 6. Lỗi thường gặp

### Thêm `?` vào mọi property để hết warning

Điều này làm contract yếu và dồn kiểm tra sang mọi caller. Xác định field nào thật sự optional; khởi tạo field bắt buộc trong constructor.

### Dùng `!` để dập warning

`!` không đổi runtime value. Nếu chưa chứng minh non-null, hãy check, return nullable hoặc sửa API nguồn.

### Dùng `?.` cho invariant bắt buộc

`order.Customer?.Name` có thể biến lỗi “order thiếu customer” thành chuỗi trống im lặng. Nếu thiếu customer là bug, guard/constructor phải từ chối object đó.

### Tin annotation thay runtime validation

Public boundary vẫn có caller/dữ liệu không chịu nullable analysis của project. Guard invariant cốt lõi ở runtime.

### Trả `null` nhưng khai báo non-nullable

Ép compiler im bằng `return null!` tạo contract dối. Đổi return thành `T?`, dùng Try-pattern hoặc ném exception nếu “không có” thật sự bất hợp lệ.

### Nhầm `string?` tạo wrapper như `int?`

Nullable reference chỉ annotation trên reference type hiện có. Không vẽ object `Nullable<string>`; hãy vẽ một reference slot chứa pointer logic hoặc null.

### Không xét mutation giữa các lần đọc property

Check một mutable property rồi đọc lại sau callback/await có thể không còn cùng value. Lưu snapshot local hoặc đồng bộ/thiết kế immutable theo concurrency contract.

## 7. Bài tập

### Bài 1 — Hồ sơ nhân viên

Thiết kế `Employee` có `Name` bắt buộc, `Manager` và `MiddleName` tùy chọn. In label an toàn mà không dùng `!`.

**Gợi ý:** constructor guard tên; dùng `?.`/`??` chỉ cho field optional.

### Bài 2 — Lookup product

Viết `FindBySku` trả `Product?`, rồi xử lý cả nhánh tìm thấy/không thấy bằng pattern matching.

**Gợi ý:** return type buộc caller thừa nhận “không có” là kết quả dự kiến.

### Bài 3 — Sửa warning

Tạo lần lượt ví dụ gây `CS8600`, `CS8602`, `CS8603`, `CS8604`; sửa bằng contract/check đúng thay vì `!`.

**Gợi ý:** build sau từng warning và giải thích data flow, không chỉ chép lời sửa.

### Bài 4 — Array chưa khởi tạo element

Tạo `string?[]` ba phần tử, lấp dần dữ liệu, rồi chuyển sang một `List<string>` chỉ chứa value đã validate.

**Gợi ý:** giai đoạn staging cho phép null; collection domain sau validation không cho null.

### Bài 5 — Vẽ memory và flow state

Vẽ một `Customer` có email, một customer không email. Ghi reference slot runtime và ghi riêng compiler state trước/sau `is not null`.

**Gợi ý:** không vẽ boolean `HasValue` cho `string?`; boolean đó chỉ phù hợp khi mô tả `Nullable<T>` value type.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt `string` bắt buộc với `string?` tùy chọn theo contract.
- [ ] Tôi xử lý warning bằng flow check/thiết kế thay vì thêm `?` hoặc `!` máy móc.
- [ ] Tôi dùng đúng `?.`, `??` và `??=`.
- [ ] Tôi biết `!` không chèn runtime null check.
- [ ] Tôi kết hợp annotation với runtime guard ở boundary.
- [ ] Tôi phân biệt nullable reference với `Nullable<T>` value type.
- [ ] Tôi vẽ được reference slot null/non-null và compiler flow state tách biệt.

Điều hướng:

- Bài tiên quyết: [Extension method](./05-extension-method.md)
- Ôn null reference cơ bản: [Class, object và constructor](../04-csharp-co-ban/07-class-object-constructor.md)
- Bài tiếp theo: [Record, init, required và immutability](./07-record-init-required-va-immutability.md)
