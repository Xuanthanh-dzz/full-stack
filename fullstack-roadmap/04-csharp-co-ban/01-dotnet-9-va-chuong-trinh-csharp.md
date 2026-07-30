# .NET 9 và chương trình C# đầu tiên

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt C#, .NET SDK, .NET Runtime và CLR;
- tạo một console project target `net9.0` bằng `dotnet` CLI;
- đọc vai trò của `.csproj`, `Program.cs`, `obj/` và `bin/`;
- build rồi chạy chương trình mà không phụ thuộc IDE;
- mô tả đường đi từ source code C# đến IL, CLR, JIT và machine code;
- đọc lỗi build cơ bản theo `file:line:column`.

## 2. Bài toán mở đầu

Một cửa hàng cần báo nhanh tổng tiền của đơn hàng gồm 3 bàn phím, đơn giá `250000` VND, VAT `8%`. Nhân viên hiện phải bấm máy tính và dễ quên VAT. Ta cần một chương trình console in tên hàng, tiền trước thuế, tiền thuế và tổng thanh toán.

Trước khi học nhiều cú pháp, ta sẽ tạo đúng một project, chạy được nó, rồi theo dõi cách .NET biến file C# thành chương trình thực thi.

## 3. Lời giải bằng code

### 3.1. Tạo project

Yêu cầu: .NET SDK 9. Kiểm tra SDK terminal đang sử dụng:

```bash
dotnet --version
```

Kết quả phải bắt đầu bằng `9.`. Tạo project với entry point `Main` tường minh:

```bash
mkdir csharp-labs
cd csharp-labs
dotnet new console --name SalesQuote --framework net9.0 --use-program-main
cd SalesQuote
```

Lệnh trên sinh ra `SalesQuote.csproj` tương đương cấu hình tối thiểu sau:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
```

Thay toàn bộ `Program.cs` bằng:

```csharp
namespace SalesQuote;

internal static class Program
{
    private static void Main()
    {
        const string productName = "Mechanical keyboard";
        const int quantity = 3;
        const decimal unitPrice = 250_000m;
        const decimal vatRate = 0.08m;

        // decimal phù hợp với tiền. Hậu tố m tạo literal kiểu decimal.
        decimal subtotal = quantity * unitPrice;
        decimal vatAmount = subtotal * vatRate;
        decimal grandTotal = subtotal + vatAmount;

        Console.WriteLine($"Product: {productName}");
        Console.WriteLine($"Quantity: {quantity}");
        Console.WriteLine($"Subtotal: {subtotal:N0} VND");
        Console.WriteLine($"VAT (8%): {vatAmount:N0} VND");
        Console.WriteLine($"Grand total: {grandTotal:N0} VND");
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

`--no-build` yêu cầu chạy đúng kết quả vừa build, tránh build lần hai. Kết quả có dạng:

```text
Product: Mechanical keyboard
Quantity: 3
Subtotal: 750,000 VND
VAT (8%): 60,000 VND
Grand total: 810,000 VND
```

Dấu phân cách hàng nghìn phụ thuộc locale hệ điều hành; giá trị số vẫn là `750000`, `60000`, `810000`.

Project đã được kiểm tra bằng .NET SDK `9.0.119`, target `net9.0`, không dùng NuGet package bên ngoài.

## 4. Giải thích cơ chế

### 4.1. Điểm bắt đầu của chương trình

Khi chạy assembly kiểu `Exe`, CLR tìm entry point. Trong code trên, entry point là:

```csharp
private static void Main()
```

- `static`: CLR gọi method mà không cần tạo object `Program`.
- `void`: method không trả exit code cho hệ điều hành. Có thể dùng `int Main()` nếu cần exit code.
- Các lệnh trong `{ ... }` chạy tuần tự từ trên xuống dưới.
- Dấu `;` kết thúc một statement; `{}` tạo một block.

C# cũng hỗ trợ *top-level statements*, nên template mặc định có thể chỉ chứa `Console.WriteLine(...)`. Bài này dùng `Main` tường minh để bạn nhìn thấy entry point. Hai cách đều được compiler tạo thành entry point hợp lệ; không đặt top-level statements và một `Main` cạnh tranh trong cùng project.

### 4.2. Điều gì xảy ra khi chạy `dotnet build`?

```text
Program.cs + SalesQuote.csproj
              |
              v
       MSBuild + C# compiler (Roslyn)
              |
              v
 bin/Debug/net9.0/SalesQuote.dll
       [CIL/IL + metadata]
              |
              v
       CLR nạp assembly và type
              |
              v
 JIT biên dịch method được gọi thành machine code
              |
              v
          CPU thực thi
```

1. `dotnet build` gọi MSBuild đọc `.csproj`, khôi phục dependency nếu cần và gọi C# compiler.
2. Compiler kiểm tra cú pháp và kiểu tại thời điểm build. Gán `"three"` vào `int` sẽ thất bại trước khi chạy.
3. Kết quả chính là một *assembly* `.dll` chứa Common Intermediate Language (CIL, thường gọi IL) và metadata về type, method, reference.
4. Khi `dotnet` chạy assembly, CoreCLR (một triển khai CLR của .NET) nạp assembly, kiểm tra dependency và quản lý thực thi.
5. JIT (*just-in-time compiler*) chuyển IL của các method cần dùng thành machine code phù hợp CPU hiện tại. Code không nhất thiết được JIT toàn bộ ngay lúc khởi động.
6. CLR còn cung cấp garbage collection, exception handling, type safety và nhiều runtime service. Các dịch vụ đó không tự loại bỏ lỗi logic.

IL giúp assembly chạy trên nhiều hệ điều hành/kiến trúc có .NET Runtime tương ứng; machine code cuối cùng vẫn phụ thuộc môi trường. .NET cũng có AOT trong một số kiểu triển khai, nhưng JIT là mô hình mặc định của bài này.

### 4.3. SDK và Runtime khác nhau ở đâu?

```text
.NET SDK
  = CLI + compiler + MSBuild + templates + targeting packs + runtime
  dùng để: create, restore, build, test, publish, run

.NET Runtime
  = CLR + base libraries cần để chạy ứng dụng
  dùng để: run một ứng dụng đã build tương thích
```

Máy lập trình cần SDK. Máy production có thể chỉ cần runtime phù hợp nếu ứng dụng được publish kiểu framework-dependent; self-contained deployment lại đóng gói runtime cùng ứng dụng.

### 4.4. Các file sinh ra nằm ở đâu?

```text
SalesQuote/
├── SalesQuote.csproj       # cấu hình project
├── Program.cs              # source code do ta viết
├── obj/                    # file trung gian của restore/build
└── bin/
    └── Debug/
        └── net9.0/         # assembly và dependency để chạy
```

`bin/` và `obj/` là build artifacts, có thể tạo lại. Không viết source code vào đó và thông thường không commit chúng vào Git.

## 5. Kiến thức nền

### C#, .NET và CLR

- **C#** là ngôn ngữ: cú pháp, type system và quy tắc compiler.
- **.NET** là platform gồm runtime, thư viện chuẩn, SDK và hệ sinh thái công cụ.
- **CLR** (*Common Language Runtime*) là môi trường thực thi managed code.
- **Base Class Library** cung cấp type như `Console`, `String`, `Decimal` và API file/network/collection.
- **Managed code** chạy dưới dịch vụ của CLR. Nó vẫn có thể tiêu thụ bộ nhớ hoặc tài nguyên sai cách.

### Project và target framework

`.csproj` cho MSBuild biết project tạo executable hay library, target framework nào, bật nullable/implicit usings ra sao và tham chiếu package/project nào.

`<TargetFramework>net9.0</TargetFramework>` nói project compile theo API surface của .NET 9. SDK mới hơn có thể build target cũ nếu có targeting pack tương ứng; cài Runtime đơn thuần không cung cấp đủ tool để compile.

### Những lệnh CLI cần nhớ

| Lệnh | Tác dụng |
|---|---|
| `dotnet new console` | Tạo console project từ template |
| `dotnet restore` | Resolve và tải dependency; `build` thường tự restore |
| `dotnet build` | Compile project và dependency |
| `dotnet run` | Build nếu cần, sau đó chạy project |
| `dotnet clean` | Xóa phần lớn output do build tạo |
| `dotnet --info` | In SDK, runtime, RID và môi trường đang dùng |

### Một số cú pháp vừa xuất hiện

- `namespace SalesQuote;` đặt type vào namespace để tránh trùng tên.
- `class Program` gom dữ liệu và hành vi; class/object sẽ được học kỹ ở bài 07.
- `const` khai báo giá trị không đổi tại compile time.
- `int`, `decimal`, `string` là các type; bài tiếp theo phân tích chi tiết.
- `_` trong `250_000` chỉ giúp đọc số, không đổi giá trị.
- `$"...{expression}..."` là interpolated string.
- `//` bắt đầu comment một dòng; comment không trở thành lệnh thực thi.

## 6. Lỗi thường gặp

### `dotnet: command not found`

SDK chưa được cài hoặc thư mục chứa `dotnet` chưa nằm trong `PATH`. Mở terminal mới rồi kiểm tra `dotnet --info`.

### `NETSDK1045: The current .NET SDK does not support targeting .NET 9.0`

Terminal đang dùng SDK cũ. Kiểm tra `dotnet --version`, `dotnet --list-sdks` và file `global.json` ở các thư mục cha. IDE có SDK không đồng nghĩa terminal đang dùng cùng SDK.

### `MSB1003: Specify a project or solution file`

Bạn đang đứng sai thư mục. Bảo đảm thư mục hiện tại chứa `.csproj`, hoặc chỉ rõ:

```bash
dotnet run --project path/to/SalesQuote.csproj
```

### Dùng `double` hoặc bỏ hậu tố `m` cho tiền

Literal `0.08` mặc định là `double`, không nhân trực tiếp với `decimal`. Viết `0.08m`. Với tiền, ưu tiên `decimal`; đừng chuyển toàn bộ sang `double` mà không hiểu sai số nhị phân.

### Sửa file trong `bin/` hoặc `obj/`

Lần build sau sẽ ghi đè. Chỉ sửa source/config chính như `.cs`, `.csproj`.

### Nhìn dòng cuối mà bỏ qua lỗi đầu tiên

Một lỗi cú pháp có thể kéo theo nhiều lỗi phụ. Đọc diagnostic đầu tiên, ví dụ `Program.cs(10,28): error CS1002`, mở đúng dòng/cột, sửa rồi build lại.

### Dùng `dotnet run --no-build` sau khi sửa source

`--no-build` chạy assembly cũ. Sau khi sửa, dùng `dotnet run` hoặc `dotnet build` rồi `dotnet run --no-build`.

## 7. Bài tập

### Bài 1 — Đổi dữ liệu đơn hàng

Đổi sản phẩm thành 2 màn hình, đơn giá `3_750_000` VND và VAT `10%`. In đúng bốn dòng số liệu.

**Gợi ý:** chỉ thay các `const`; kiểm tra phép nhân trước thuế rồi mới tính VAT.

### Bài 2 — Thêm giảm giá

Thêm `discountRate = 0.05m`, tính giảm giá trên `subtotal`, sau đó VAT trên số tiền đã giảm.

**Gợi ý:** tạo lần lượt `discountAmount`, `discountedSubtotal`, `vatAmount`, `grandTotal`.

### Bài 3 — Khảo sát output của build

Chạy `dotnet build --configuration Release` và so sánh cây file với Debug.

**Gợi ý:** tìm dưới `bin/Release/net9.0/`; dùng `dotnet run -c Release` để chạy đúng cấu hình.

### Bài 4 — Tạo lỗi có chủ đích

Lần lượt xóa một dấu `;`, đổi `decimal vatRate` thành `int vatRate`, và viết sai `Console` thành `console`. Ghi mã lỗi `CSxxxx` đầu tiên rồi hoàn tác; mỗi lần chỉ tạo một lỗi.

**Gợi ý:** tập đọc `file(line,column)` và diagnostic đầu tiên.

### Bài 5 — Trả exit code

Đổi `Main` thành `private static int Main()`, giữ nguyên output và trả `0`.

**Gợi ý:** mọi đường đi của method trả `int` phải có `return`.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt được C#, SDK, Runtime và CLR.
- [ ] Tôi tự tạo, build và chạy được console project target `net9.0` từ terminal.
- [ ] Tôi chỉ ra được assembly `.dll` sau build nằm ở đâu.
- [ ] Tôi vẽ được luồng `C# source → IL → CLR/JIT → machine code`.
- [ ] Tôi giải thích được vai trò của `.csproj`, `Program.cs`, `obj/` và `bin/`.
- [ ] Tôi đọc được file, dòng, cột và mã lỗi từ build diagnostic.

Điều hướng:

- Prerequisite: [Roadmap tổng và yêu cầu của module 04](../00-huong-dan/roadmap.md)
- Bài tiếp theo: [Cú pháp, biến và kiểu dữ liệu](./02-cu-phap-bien-va-kieu-du-lieu.md)
