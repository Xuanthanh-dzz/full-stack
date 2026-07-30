# Project, solution, namespace và assembly trong .NET

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt vai trò của solution (`.sln`) và project (`.csproj`);
- tổ chức code vào namespace mà không nhầm namespace với folder hay assembly;
- hiểu một project C# thường được build thành assembly nào;
- tạo solution nhiều project và khai báo `ProjectReference` đúng chiều phụ thuộc;
- giải thích `public`/`internal` theo boundary assembly;
- phân biệt project reference, assembly reference và NuGet `PackageReference`;
- restore, build và run toàn bộ ví dụ nhiều project bằng .NET 9 mà không cần package ngoài.

## 2. Bài toán mở đầu

Một chương trình tính hóa đơn ban đầu nằm trong một file `Program.cs`. Khi có thêm web API, background worker và test, ta muốn dùng lại quy tắc tính tiền nhưng không sao chép source code.

Yêu cầu đầu tiên là tách thành:

- `StoreBilling.Domain`: class library chứa quy tắc hóa đơn;
- `StoreBilling.Cli`: console application nhận kết quả và hiển thị;
- `StoreBilling.sln`: điểm vào để IDE và CLI thao tác cả hai project.

CLI được phép phụ thuộc Domain; Domain không được biết CLI. Namespace giúp đặt tên type rõ ràng, còn `ProjectReference` mới thực sự tạo dependency lúc build.

## 3. Lời giải bằng code

### Tạo solution và hai project

Chạy các lệnh sau trong một thư mục làm việc mới:

```bash
mkdir StoreBilling
cd StoreBilling

dotnet new sln --name StoreBilling
dotnet new classlib --name StoreBilling.Domain \
  --output src/StoreBilling.Domain \
  --framework net9.0
dotnet new console --name StoreBilling.Cli \
  --output src/StoreBilling.Cli \
  --framework net9.0 \
  --use-program-main

dotnet sln StoreBilling.sln add \
  src/StoreBilling.Domain/StoreBilling.Domain.csproj \
  src/StoreBilling.Cli/StoreBilling.Cli.csproj

dotnet add src/StoreBilling.Cli/StoreBilling.Cli.csproj reference \
  src/StoreBilling.Domain/StoreBilling.Domain.csproj
```

Xóa file mẫu `src/StoreBilling.Domain/Class1.cs`, rồi tạo các file dưới đây. Cây source cuối cùng:

```text
StoreBilling/
├── StoreBilling.sln
└── src/
    ├── StoreBilling.Domain/
    │   ├── StoreBilling.Domain.csproj
    │   ├── InvoiceLine.cs
    │   └── InvoiceCalculator.cs
    └── StoreBilling.Cli/
        ├── StoreBilling.Cli.csproj
        └── Program.cs
```

### Project Domain

`src/StoreBilling.Domain/StoreBilling.Domain.csproj`:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>
</Project>
```

`src/StoreBilling.Domain/InvoiceLine.cs`:

```csharp
using System;

namespace StoreBilling.Domain.Billing;

public sealed class InvoiceLine
{
    public string Description { get; }
    public int Quantity { get; }
    public decimal UnitPrice { get; }

    public InvoiceLine(string description, int quantity, decimal unitPrice)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(description);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity);
        ArgumentOutOfRangeException.ThrowIfNegative(unitPrice);

        Description = description;
        Quantity = quantity;
        UnitPrice = unitPrice;
    }

    public decimal GetSubtotal() => Quantity * UnitPrice;
}
```

`src/StoreBilling.Domain/InvoiceCalculator.cs`:

```csharp
using System;
using System.Collections.Generic;

namespace StoreBilling.Domain.Billing;

public static class InvoiceCalculator
{
    public static decimal CalculateTotal(IEnumerable<InvoiceLine> lines)
    {
        ArgumentNullException.ThrowIfNull(lines);

        decimal total = 0m;

        foreach (InvoiceLine line in lines)
        {
            if (line is null)
            {
                throw new ArgumentException(
                    "The sequence cannot contain null lines.",
                    nameof(lines));
            }

            total += line.GetSubtotal();
        }

        return total;
    }
}
```

### Project CLI

`src/StoreBilling.Cli/StoreBilling.Cli.csproj`:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
  </PropertyGroup>

  <ItemGroup>
    <ProjectReference Include="../StoreBilling.Domain/StoreBilling.Domain.csproj" />
  </ItemGroup>
</Project>
```

`src/StoreBilling.Cli/Program.cs`:

```csharp
using System;
using StoreBilling.Domain.Billing;

namespace StoreBilling.Cli;

internal static class Program
{
    private static void Main()
    {
        InvoiceLine[] lines =
        [
            new InvoiceLine("Keyboard", quantity: 2, unitPrice: 750_000m),
            new InvoiceLine("Mouse", quantity: 1, unitPrice: 350_000m)
        ];

        decimal total = InvoiceCalculator.CalculateTotal(lines);

        Console.WriteLine($"Invoice total: {total:N0} VND");
        Console.WriteLine(
            $"Domain assembly: {typeof(InvoiceCalculator).Assembly.GetName().Name}");
        Console.WriteLine(
            $"CLI assembly: {typeof(Program).Assembly.GetName().Name}");
    }
}
```

### Restore, build và run

Từ thư mục chứa `StoreBilling.sln`:

```bash
dotnet restore StoreBilling.sln
dotnet build StoreBilling.sln --no-restore
dotnet run --project src/StoreBilling.Cli/StoreBilling.Cli.csproj --no-build
```

Kết quả chính:

```text
Invoice total: 1,850,000 VND
Domain assembly: StoreBilling.Domain
CLI assembly: StoreBilling.Cli
```

Ký tự phân cách hàng nghìn có thể khác theo locale.

## 4. Giải thích cơ chế

### Build graph

`ProjectReference` tạo cạnh có hướng từ CLI tới Domain:

```text
StoreBilling.sln (nhóm project; không phải dependency runtime)
│
├─ StoreBilling.Domain.csproj
│       └─ build -> StoreBilling.Domain.dll
│
└─ StoreBilling.Cli.csproj
        ├─ ProjectReference ────────────────┘
        └─ build -> StoreBilling.Cli.dll + executable host

Build order: Domain trước -> CLI sau
Runtime: CLI load StoreBilling.Domain assembly khi cần type của Domain
```

Khi build solution, MSBuild đọc graph, build dependency trước và đưa output cần thiết sang thư mục output của CLI. Nếu xóa `ProjectReference`, câu `using StoreBilling.Domain.Billing;` không đủ để compiler tìm `InvoiceLine`.

### Bốn khái niệm không thay thế nhau

| Khái niệm | Chức năng |
|---|---|
| Solution | nhóm và điều phối nhiều project cho CLI/IDE |
| Project | đơn vị cấu hình restore/build; chứa target framework, source và dependency |
| Namespace | không gian tên logic để tránh trùng tên type |
| Assembly | output đã compile chứa IL, metadata và resources |

`StoreBilling.sln` không được compile thành ứng dụng. Nó có thể chứa test, tool hoặc project không nằm trên đường chạy của CLI.

`StoreBilling.Domain.Billing` là namespace. Nó không bắt buộc trùng folder và không tự tạo dependency. Hai assembly khác nhau có thể đóng góp type vào cùng namespace; ngược lại, một assembly có thể chứa nhiều namespace.

`StoreBilling.Domain.dll` là managed assembly. Metadata trong assembly mô tả type, member, reference tới assembly khác và version. CLR load assembly, JIT compile method cần chạy và quản lý object được tạo từ các type đó.

### Boundary truy cập

`public InvoiceLine` có thể được code ở assembly CLI dùng vì CLI reference Domain. Nếu đổi thành `internal`, type chỉ truy cập được từ code trong chính `StoreBilling.Domain` assembly (trừ cơ chế friend assembly được cấu hình riêng).

Namespace không phải access boundary. Đặt một type vào namespace `StoreBilling.Domain.Secret` không làm type `public` trở nên bí mật.

### Object và assembly là hai lớp khác nhau

Hai lệnh `new InvoiceLine(...)` tạo hai object riêng trên managed heap. Array `lines` giữ hai reference. Cả hai object có cùng runtime type, và metadata của type đó đến từ assembly `StoreBilling.Domain` đã load:

```text
Loaded StoreBilling.Domain assembly metadata/code
                 │ defines type
                 v
Heap: InvoiceLine object #1   InvoiceLine object #2
             ^                       ^
             └──── references in lines[] ────┘
```

Project reference không “chứa object” và không tạo bản sao type cho từng caller; nó cung cấp dependency compile/build, sau đó runtime dùng identity của type trong assembly đã load.

## 5. Kiến thức nền

### Nội dung quan trọng của `.csproj`

Project dùng SDK style:

- `Sdk="Microsoft.NET.Sdk"` nhập các target build chuẩn;
- `TargetFramework` là target framework moniker, ở đây `net9.0`;
- `OutputType` là `Exe` cho application; class library mặc định tạo library;
- `Nullable` bật phân tích nullable reference type;
- `ImplicitUsings` tự thêm một tập namespace phổ biến;
- `ItemGroup` chứa reference hoặc item khác.

SDK mặc định glob các file `**/*.cs` trong project, nên thường không cần liệt kê từng source file. `bin/` là output build, `obj/` là intermediate/restore state; không sửa chúng như source và thường không commit.

### File-scoped namespace và `using`

```csharp
namespace StoreBilling.Domain.Billing;
```

là file-scoped namespace: mọi type phía sau trong file thuộc namespace đó. `using StoreBilling.Domain.Billing;` cho phép viết tên ngắn `InvoiceLine`; nó không cài package và không thêm reference.

Khi hai namespace có type trùng tên, dùng fully qualified name hoặc alias:

```csharp
using BillingLine = StoreBilling.Domain.Billing.InvoiceLine;
```

### ProjectReference, framework reference và NuGet

- `ProjectReference`: phụ thuộc source project trong cùng build graph; thay đổi Domain được build lại cùng CLI.
- Framework/reference packs: API nền tảng mà SDK cung cấp cho `net9.0`, ví dụ `System.Console`.
- `PackageReference`: phụ thuộc package được phân phối qua NuGet feed; `dotnet restore` tải/chọn dependency theo metadata.
- Assembly/file reference trực tiếp: trỏ tới DLL có sẵn; ít phù hợp hơn project/package vì khó tái tạo version và dependency đi kèm.

Ví dụ cú pháp NuGet (không cần thêm vào bài mẫu):

```xml
<ItemGroup>
  <PackageReference Include="Vendor.Package" Version="1.2.3" />
</ItemGroup>
```

Không ghi version giả như trên vào project thật. Khi dùng package, chọn version có chủ đích, xem license/security, cấu hình feed tin cậy và bảo đảm CI restore tái tạo được. Bài mẫu không dùng external NuGet package nên build được chỉ với .NET 9 SDK/reference packs.

### Thiết kế chiều phụ thuộc

Library nghiệp vụ nên ít phụ thuộc vào UI/host. Nếu Domain reference CLI và CLI lại reference Domain, graph tạo cycle và build bị từ chối. Dependency một chiều giúp tái sử dụng Domain cho API, worker và test.

Solution folder chỉ là cách nhóm trong solution, không tự thay đổi namespace, đường dẫn output hay dependency.

## 6. Lỗi thường gặp

### Có `using` nhưng thiếu reference

`using` chỉ rút gọn tên. Thêm `ProjectReference`/`PackageReference` phù hợp để compiler nhìn thấy assembly chứa type.

### Nhầm namespace với folder

Di chuyển file sang folder khác không tự bảo đảm namespace đổi đúng; đổi namespace cũng không bắt buộc di chuyển file. Giữ chúng đồng bộ theo convention để người đọc dễ tìm, nhưng hiểu đây không phải cùng một cơ chế.

### Tạo dependency vòng

`A -> B -> A` làm ranh giới trách nhiệm sai và MSBuild không thể lập build order hợp lệ. Tách contract chung sang project thứ ba hoặc đảo dependency bằng interface ở layer thích hợp.

### Copy DLL thủ công

DLL được copy bằng tay dễ cũ hơn source và thiếu dependency. Dùng project reference khi cùng repository, NuGet package khi phân phối version độc lập.

### Target framework không tương thích

Project target framework thấp/khác không phải lúc nào cũng reference được project target cao hơn. Thiết kế target framework theo consumer và kiểm tra build graph trên CI.

### Đưa secret vào `.csproj` hoặc NuGet config commit công khai

Không hard-code feed token, password hay signing secret. Dùng credential provider, secret store và biến môi trường của CI theo hướng dẫn triển khai sau này.

### Chỉ build project khởi động

Lỗi ở project khác trong solution có thể bị bỏ sót. CI nên restore/build/test entry phù hợp, thường là solution hoặc file điều phối build đã thống nhất.

## 7. Bài tập

### Bài 1 — Thêm project báo cáo

Tạo `StoreBilling.Reporting` class library, reference Domain và sinh một chuỗi báo cáo hóa đơn.

Gợi ý: thêm project vào solution, rồi thêm reference **từ Reporting tới Domain**.

### Bài 2 — Quan sát `internal`

Đổi `InvoiceCalculator` thành `internal`, build và đọc lỗi compiler ở CLI; sau đó đổi lại `public`.

Gợi ý: namespace không làm thay đổi assembly access boundary.

### Bài 3 — Alias khi trùng tên

Tạo hai type `Money` ở hai namespace khác nhau và dùng cả hai trong CLI.

Gợi ý: dùng fully qualified name trước, sau đó refactor sang `using` alias.

### Bài 4 — Kiểm tra output

Build Debug và Release, tìm `.dll`, `.deps.json`, `.runtimeconfig.json` và executable host trong `bin/`.

Gợi ý: dùng `dotnet build -c Release`; không sửa file output.

### Bài 5 — Vẽ dependency graph

Đề xuất solution gồm Domain, Application, Infrastructure, Api và Tests; vẽ chiều project reference, phát hiện cycle nếu có.

Gợi ý: bắt đầu từ layer ổn định nhất; test có thể reference project được kiểm thử, nhưng production project không reference test.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt được solution, project, namespace và assembly.
- [ ] Tôi tạo được solution nhiều project bằng `dotnet` CLI.
- [ ] Tôi thêm `ProjectReference` đúng chiều và giải thích build order.
- [ ] Tôi biết `using` không thay thế dependency reference.
- [ ] Tôi giải thích được `public` và `internal` theo assembly boundary.
- [ ] Tôi phân biệt project reference với NuGet `PackageReference`.
- [ ] Tôi biết mỗi `new InvoiceLine` tạo object riêng, không phải assembly mới.
- [ ] Tôi đã restore/build/run toàn bộ solution bằng .NET 9.

Bài prerequisite: [Collection: List, Dictionary, HashSet, Queue và Stack](./13-collection-list-dictionary-hashset-queue-stack.md).

Bài tiếp theo: [Debug và diagnostics cơ bản](./15-debug-va-diagnostics-co-ban.md).
