# Reflection, attribute và `dynamic`

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, async lifecycle hoặc serializer; CI failure

## TL;DR

- Reflection đọc metadata runtime; attribute gắn thông tin; dynamic chọn member lúc chạy.
- Dùng tại registry/adapter khi contract thực sự cần khám phá runtime.
- Lỗi signature/member muộn hơn compile; allowlist không phải sandbox.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- dùng attribute để gắn metadata có cấu trúc vào type hoặc method;
- đọc metadata bằng reflection và phân biệt metadata với object thực thi;
- tìm method, kiểm tra signature rồi gọi `MethodInfo.Invoke` an toàn hơn;
- hiểu chi phí allocation, boxing và lỗi runtime khi dùng reflection;
- giải thích `dynamic` trì hoãn việc bind member tới runtime;
- cô lập `dynamic` ở biên tương tác thay vì để lan vào domain code;
- nhận ra rủi ro trimming, Native AOT, bảo mật và khả năng bảo trì;
- chọn code tường minh, source generation hoặc registry khi reflection không phù hợp.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Nhãn trên method không tự gọi method. Registry đọc nhãn, kiểm tra phiếu hướng dẫn rồi mới cho gọi. dynamic là quyết định “đến lúc chạy mới tìm method”, nên typo có thể qua build.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| metadata | mô tả type/member trong assembly | CommandAttribute |
| reflection | API đọc và gọi theo mô tả | MethodInfo |
| runtime binding | chọn member dựa object lúc chạy | dynamic Format |
| allowlist | tập được phép khám phá | CommandHandlers only |

### Ví dụ nhỏ — tính tay trước

sum12,30→42; sum2147483647,1 overflow bị Invoke bọc, adapter trả Command failed. Object không có Format compile qua dynamic nhưng trả lỗi contract khi chạy.

Một công cụ vận hành nhận lệnh dạng `sum 12 30`. Ta muốn thêm command mới bằng cách viết một method rồi gắn metadata, không sửa một chuỗi `if/else` trung tâm. Đồng thời, hệ thống phải gọi một formatter cũ chỉ được biết ở runtime.

Hai nhu cầu này dễ dẫn đến code nguy hiểm:

- reflection có thể gọi nhầm method hoặc làm lỗi thật bị bọc trong `TargetInvocationException`;
- `dynamic` bỏ kiểm tra member ở compile time, nên typo chỉ lộ ra khi nhánh đó chạy;
- quét toàn assembly không kiểm soát có thể vô tình công khai method không dành cho người dùng.

Ta sẽ tạo một registry chỉ từ một type cho phép, xác thực signature trước khi đăng ký, rồi giữ `dynamic` trong đúng một adapter nhỏ.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project:

```bash
dotnet new console --name RuntimeCommandRouter --framework net9.0 --use-program-main
cd RuntimeCommandRouter
```

Thay `RuntimeCommandRouter.csproj` bằng:

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
using System.Reflection;
using Microsoft.CSharp.RuntimeBinder;

namespace RuntimeCommandRouter;

internal static class Program
{
    private static void Main(string[] args)
    {
        Dictionary<string, CommandDescriptor> commands = DiscoverCommands();

        string[] request = args.Length > 0
            ? args
            : new[] { "sum", "12", "30" };

        string commandName = request[0];
        string[] commandArguments = request[1..];

        if (!commands.TryGetValue(commandName, out CommandDescriptor? command))
        {
            Console.WriteLine($"Unknown command: {commandName}");
            return;
        }

        Console.WriteLine($"Command: {command.Name}");
        Console.WriteLine($"Description: {command.Description}");

        string result = InvokeCommand(command, commandArguments);
        Console.WriteLine($"Result: {result}");

        // LegacyFormatter đại diện cho object đến từ một API cũ/COM/plugin.
        // dynamic chỉ tồn tại bên trong adapter FormatWithLegacyBoundary.
        object legacyFormatter = new LegacyFormatter();
        string formatted = FormatWithLegacyBoundary(legacyFormatter, result);
        Console.WriteLine($"Legacy output: {formatted}");
    }

    private static Dictionary<string, CommandDescriptor> DiscoverCommands()
    {
        var commands = new Dictionary<string, CommandDescriptor>(
            StringComparer.OrdinalIgnoreCase);

        MethodInfo[] methods = typeof(CommandHandlers).GetMethods(
            BindingFlags.Public |
            BindingFlags.Static |
            BindingFlags.DeclaredOnly);

        foreach (MethodInfo method in methods)
        {
            CommandAttribute? attribute =
                method.GetCustomAttribute<CommandAttribute>();

            if (attribute is null)
            {
                continue;
            }

            ValidateCommandSignature(method);

            var descriptor = new CommandDescriptor(
                attribute.Name,
                attribute.Description,
                method);

            if (!commands.TryAdd(attribute.Name, descriptor))
            {
                throw new InvalidOperationException(
                    $"Duplicate command name: {attribute.Name}");
            }
        }

        return commands;
    }

    private static void ValidateCommandSignature(MethodInfo method)
    {
        ParameterInfo[] parameters = method.GetParameters();
        bool valid = method.ReturnType == typeof(string)
            && parameters.Length == 1
            && parameters[0].ParameterType == typeof(string[]);

        if (!valid)
        {
            throw new InvalidOperationException(
                $"{method.Name} must have signature string Method(string[] args).");
        }
    }

    private static string InvokeCommand(
        CommandDescriptor command,
        string[] arguments)
    {
        try
        {
            object? rawResult = command.Method.Invoke(
                obj: null,
                parameters: new object?[] { arguments });

            return rawResult as string
                ?? throw new InvalidOperationException(
                    $"{command.Method.Name} returned null or a non-string value.");
        }
        catch (TargetInvocationException exception)
            when (exception.InnerException is not null)
        {
            // Không trả exception message qua boundary vì nó có thể chứa dữ liệu
            // nội bộ. Production nên log exception đầy đủ ở nơi được kiểm soát.
            Console.Error.WriteLine($"Command '{command.Name}' failed.");
            return "Command failed.";
        }
    }

    private static string FormatWithLegacyBoundary(object formatter, string value)
    {
        try
        {
            dynamic lateBoundFormatter = formatter;
            object? rawResult = lateBoundFormatter.Format(value);
            return rawResult as string
                ?? "Legacy contract error: Format must return a non-null string.";
        }
        catch (RuntimeBinderException)
        {
            return "Legacy contract error: required Format(string) member is unavailable.";
        }
    }
}

[AttributeUsage(
    AttributeTargets.Method,
    AllowMultiple = false,
    Inherited = false)]
internal sealed class CommandAttribute : Attribute
{
    public CommandAttribute(string name)
    {
        Name = name;
    }

    public string Name { get; }

    public string Description { get; set; } = string.Empty;
}

internal sealed record CommandDescriptor(
    string Name,
    string Description,
    MethodInfo Method);

internal static class CommandHandlers
{
    [Command("sum", Description = "Add two Int32 values.")]
    public static string Sum(string[] args)
    {
        if (args.Length != 2
            || !int.TryParse(args[0], out int left)
            || !int.TryParse(args[1], out int right))
        {
            return "Usage: sum <left> <right>";
        }

        return checked(left + right).ToString();
    }

    [Command("upper", Description = "Convert text to uppercase.")]
    public static string Upper(string[] args)
    {
        return args.Length == 0
            ? "Usage: upper <text>"
            : string.Join(' ', args).ToUpperInvariant();
    }
}

internal sealed class LegacyFormatter
{
    public string Format(string value) => $"[{value}]";
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build -- sum 12 30
dotnet run --no-build -- upper hello reflection
```

Lần chạy đầu in:

```text
Command: sum
Description: Add two Int32 values.
Result: 42
Legacy output: [42]
```

### Walkthrough — execution / state / cost

1. Discovery quét public static declared methods của đúng type.
2. Attribute được materialize, signature string(string[]) được kiểm tra rồi lưu descriptor.
3. Invoke tạo argument array, gọi handler và phân biệt wrapper/inner exception.
4. Dynamic formatter sống trong boundary nhỏ. Metadata discovery/allocation có cost; cache bounded khi nhiều request, không quét assembly mỗi lần theo input.

### Mini-check

ValidateCommandSignature hiện có chặn generic method mở dù return/parameter giống không? Contract registry hiện dựa thêm assumption nào?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Attribute đi vào metadata, không tự chạy

`[Command(...)]` làm compiler ghi custom-attribute metadata vào assembly. Nó không tự đăng ký command và constructor của attribute không chạy mỗi khi `Sum` chạy. `GetCustomAttribute<CommandAttribute>()` mới đọc metadata và materialize một object attribute để code sử dụng.

```text
RuntimeCommandRouter.dll
├── IL của CommandHandlers.Sum
├── metadata của type/method
└── custom attribute record: Command("sum", Description=...)
                                   |
                                   | GetCustomAttribute
                                   v
managed heap: CommandAttribute object
```

Attribute argument bị giới hạn ở các kiểu biểu diễn được trong metadata, như primitive, `string`, `Type`, enum và mảng của các kiểu hợp lệ. Không đặt service hoặc object runtime tùy ý vào attribute.

### 4.2. Reflection biến metadata thành object mô tả

`typeof(CommandHandlers)` trả một `Type`. `GetMethods(...)` trả các `MethodInfo`; mỗi `MethodInfo` mô tả tên, modifier, return type, parameter và cách gọi method.

Ta dùng `DeclaredOnly`, `Public` và `Static` để giới hạn bề mặt quét. Sau đó `ValidateCommandSignature` kiểm tra đúng hợp đồng `string Method(string[])` trước khi registry nhận method. Attribute chỉ đánh dấu ý định; validation mới bảo vệ cấu trúc runtime.

```text
commands["sum"]
      |
      v
CommandDescriptor ----> MethodInfo ----> metadata/IL của Sum

Invoke(null, object?[])
      |
      v
runtime kiểm tra target + argument -> gọi Sum -> box result nếu cần
```

Sample trả `string`, nên result vốn là reference. Nếu method trả `int`, `Invoke` phải box `int` vào `object`. Mảng `object?[]` dùng cho argument cũng là một allocation. Reflection phù hợp ở startup, tooling hoặc extension point có kiểm soát; không mặc nhiên phù hợp một hot path gọi hàng triệu lần.

### 4.3. Exception qua `Invoke`

Lỗi kiểm tra reflection như sai số argument có thể do chính `Invoke` ném. Exception phát sinh bên trong command thường được bọc trong `TargetInvocationException`; lỗi gốc nằm ở `InnerException`.

Sample trả thông báo chung qua boundary và chỉ ghi một diagnostic không chứa exception message. Production thường phải ghi cả wrapper lẫn `InnerException` bằng structured logger ở nơi có kiểm soát truy cập, đồng thời không trả raw message/stack trace cho caller. Khi cần rethrow lỗi gốc mà giữ stack trace, dùng `ExceptionDispatchInfo`; chủ đề này chỉ nên áp dụng khi đã có policy lỗi rõ ràng.

### 4.4. `dynamic` trì hoãn binding

Với:

```csharp
dynamic lateBoundFormatter = formatter;
lateBoundFormatter.Format(value);
```

compiler không xác nhận `Format` tồn tại trên runtime type. Nó sinh một dynamic call site. Lần chạy, runtime binder xem type thật của `formatter`, tên member và argument để chọn lời gọi. Kết quả có thể được cache tại call site cho cùng dạng runtime type, nhưng lỗi contract vẫn chỉ xuất hiện khi code chạy.

`dynamic` không phải một loại object mới và không làm object “mất type”:

```text
local lateBoundFormatter = reference ──> LegacyFormatter object
compile-time binding: dynamic
runtime type của object: LegacyFormatter
```

Trong metadata, `dynamic` phần lớn được biểu diễn dựa trên `object` kèm thông tin hỗ trợ compiler. Assignment của reference vẫn tuân theo mô hình bộ nhớ bình thường.

### 4.5. Biên an toàn của sample

Domain code nhận/trả `string` tĩnh. Chỉ `FormatWithLegacyBoundary` biết `dynamic`, bắt đúng `RuntimeBinderException` và biến lỗi hợp đồng thành kết quả có kiểm soát. Khi API cũ có thể được bọc bằng interface tĩnh, interface thường tốt hơn vì IDE, compiler và refactoring đều kiểm tra được.

Không đưa tên type/method trực tiếp từ input rồi gọi mọi member. Allowlist bằng attribute và type cụ thể vẫn cần authorization ở tầng nghiệp vụ; reflection không phải cơ chế phân quyền hay sandbox. Code được gọi vẫn chạy với quyền của process. Plugin không tin cậy cần biên cô lập phù hợp như process/container riêng cùng giới hạn OS, không chỉ một allowlist reflection.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| static/interface | compiler kiểm tra | ưu tiên khi biết contract |
| reflection registry | khám phá metadata runtime | hợp tooling có allowlist |
| dynamic adapter | late-bound member | hợp interop thật, cô lập lỗi |

### Misconception check

**Đúng hay sai?** Attribute constructor chạy mỗi lần Sum được gọi.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: metadata được đọc/materialize khi reflection yêu cầu.

</details>

**Đúng hay sai?** Allowlist reflection làm plugin không tin cậy an toàn.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: method vẫn chạy với quyền process.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** metadata và binding.

- **Working Developer — dùng khi làm việc:** boundary validation và error policy.

- **Deep Dive — có thể quay lại sau:** trimming/AOT đúng target.

### API reflection thường gặp

| API | Vai trò |
|---|---|
| `typeof(T)` / `instance.GetType()` | lấy `Type` từ compile-time type hoặc object runtime |
| `GetMethods`, `GetProperties` | liệt kê member theo `BindingFlags` |
| `GetCustomAttribute<T>` | materialize attribute cụ thể |
| `Activator.CreateInstance` | tạo instance qua constructor được chọn ở runtime |
| `MethodInfo.Invoke` | gọi method qua metadata |
| `PropertyInfo.GetValue/SetValue` | đọc/ghi property qua reflection |

`BindingFlags` dễ tạo lỗi im lặng: bỏ `Instance`, `Static`, `Public`, `NonPublic` hoặc `DeclaredOnly` có thể làm tập kết quả khác hẳn. Luôn giới hạn và kiểm tra tập member nhận được.

### Reflection, trimming và Native AOT

Static analysis có thể không thấy member chỉ được gọi bằng tên string. Khi publish trimming hoặc Native AOT, member đó có thể bị loại hoặc dynamic-code API có thể không khả dụng.

Registry sinh ở compile time, source generator hoặc mapping tường minh thường thân thiện hơn với trimming/AOT.

### Khi nào `dynamic` có lý do chính đáng?

- COM interop hoặc API thật sự late-bound;
- scripting/runtime object model;
- adapter rất nhỏ quanh thư viện cũ;
- prototype ngắn có kế hoạch thay contract tĩnh.

JSON, dictionary và input người dùng không tự nhiên trở thành lý do dùng `dynamic`. Hãy parse/validate thành DTO hoặc type rõ ràng ở boundary.

### Cache metadata có kiểm soát

Nếu cùng registry được dùng nhiều lần, khám phá và validation một lần lúc startup rồi cache descriptor immutable. Không cache object vô hạn theo input tùy ý. Đo startup, throughput và memory trước khi thêm cache phức tạp.

### Đào sâu (có thể quay lại sau)

Các annotation như `DynamicallyAccessedMembers` chỉ đúng khi hợp đồng bảo toàn member được mô tả chính xác; dùng bừa sẽ che thiết kế yếu.

Quyết định dựa trên deployment target, không chỉ dựa trên số dòng code.

## 6. Lỗi thường gặp

### Quét mọi assembly và gọi mọi method có tên trùng

Điều này mở bề mặt không chủ đích và khó audit. Chỉ quét assembly/type allowlist, yêu cầu marker attribute, kiểm tra signature và thực hiện authorization riêng.

### Ép kiểu kết quả `Invoke` mà không kiểm tra

`Invoke` trả `object?`. Cast sai gây `InvalidCastException`; `null` có thể hợp lệ hoặc là violation tùy contract. Validate return type khi đăng ký và vẫn kiểm tra result ở boundary.

### Nuốt hoặc làm lộ `TargetInvocationException`

Chỉ log message của wrapper sẽ giấu lỗi gốc; trả `InnerException.Message` cho caller lại có thể lộ chi tiết nội bộ. Ghi nhận wrapper cùng `InnerException` trong log được bảo vệ, giữ stack trace và trả lỗi công khai theo policy riêng.

### Dùng `dynamic` xuyên nhiều layer

Một typo như `Fomrat` vẫn compile và có thể đi tới production. Cô lập dynamic, chuyển sớm về type tĩnh, có contract test cho adapter.

### Cho rằng dynamic nhanh như lời gọi tĩnh vì có cache

Call-site caching không xóa mọi chi phí binder, conversion và rủi ro runtime. Chỉ tối ưu sau phép đo; lời gọi tĩnh vẫn cho compiler nhiều thông tin hơn.

### Bỏ qua trimming/AOT

Code chạy trong `dotnet run` có thể hỏng sau publish trimmed/AOT. Kiểm thử đúng publish mode và ưu tiên source-generated/tường minh nếu deployment yêu cầu.

## 7. Khi nào KHÔNG dùng

Không nhận tên type/method tùy ý từ input để Invoke. Không dùng dynamic thay typed DTO chỉ vì JSON linh hoạt. Không cache vô hạn theo key từ người dùng.

## 8. Production notes & scale check

Gate sum/overflow, signature sai và missing dynamic member. Registry chỉ cho hai handler đã biết; validator signature chưa kiểm mọi dạng method tổng quát như open generic. Chưa publish trimmed/AOT, nên không tuyên bố compatibility deployment đó.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Thêm command `multiply`

Tạo method nhận đúng hai số nguyên, kiểm tra overflow và đăng ký bằng `[Command]`.

**Gợi ý:** giữ nguyên signature `string Method(string[])`; dùng `checked` và trả usage khi parse thất bại.

### Bài 2 — Phát hiện registry sai

Cố ý thêm hai command cùng tên và một method có return type `int`. Ghi lại lỗi startup tương ứng.

**Gợi ý:** mỗi lần chỉ tạo một lỗi; xác nhận lỗi xảy ra lúc discovery, trước khi nhận request.

### Bài 3 — Cache property accessor

Viết hàm đọc một property allowlist từ object bằng `PropertyInfo`, sau đó cache `PropertyInfo` theo `(Type, propertyName)`.

**Gợi ý:** giới hạn số key, từ chối property indexer và đo trước/sau; không nhận tên member tùy ý từ người dùng chưa tin cậy.

### Bài 4 — Adapter cho dynamic contract sai

Truyền `new object()` vào `FormatWithLegacyBoundary`, quan sát `RuntimeBinderException`, rồi thay dynamic bằng interface `ILegacyFormatter` khi bạn kiểm soát type.

**Gợi ý:** so sánh thời điểm lỗi: compile time của interface và runtime của dynamic.

## 10. Bài tập tích hợp liên module — Judgment

So với delegate bài02, lúc nào nên discover một lần rồi giữ callable? Với hai command cố định, switch nhỏ có đủ và dễ kiểm hơn không?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Attribute có tự thực thi không?
2. Lỗi gốc của Invoke nằm đâu?
3. Dynamic giữ runtime type object không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi giải thích được attribute là metadata và không tự thực thi.
- [ ] Tôi giới hạn tập member reflection và validate signature trước `Invoke`.
- [ ] Tôi nhận ra allocation/boxing và wrapper exception của reflection.
- [ ] Tôi giải thích được dynamic call site và runtime binder.
- [ ] Tôi giữ `dynamic` trong một adapter nhỏ có error policy.
- [ ] Tôi đánh giá trimming/AOT, bảo mật và khả năng thay bằng registry/source generation.

Điều hướng:

- Prerequisite: [`IDisposable`, GC và quản lý tài nguyên](./12-idisposable-gc-va-quan-ly-tai-nguyen.md)
- Bài tiếp theo: [`Span<T>`, `Memory<T>` và lập trình hiệu năng](./14-span-memory-va-lap-trinh-hieu-nang.md)
