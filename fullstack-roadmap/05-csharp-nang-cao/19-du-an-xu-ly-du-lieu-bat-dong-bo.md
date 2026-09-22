# Dự án C# nâng cao: xử lý batch đơn hàng bất đồng bộ

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, async lifecycle hoặc serializer; CI failure

## TL;DR

- Capstone xử lý JSON async có giới hạn concurrency và policy lỗi rõ.
- Dùng cho batch hữu hạn một process, giữ thứ tự báo cáo sau khi thu kết quả.
- Semaphore giới hạn active work, không giới hạn số task đã tạo hoặc làm queue bền.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- ghép generics, delegate, event, lambda, nullable reference type, record và pattern matching vào một chương trình có ranh giới rõ ràng;
- đọc nhiều file JSON bằng API bất đồng bộ mà không chặn thread trong lúc chờ I/O;
- giới hạn số thao tác I/O đồng thời bằng `SemaphoreSlim`, chờ cả batch bằng `Task.WhenAll` và bảo toàn thứ tự output;
- truyền `CancellationToken` xuyên suốt từ entry point đến API file/JSON;
- quản lý lifetime của `FileStream`, `CancellationTokenSource` và `SemaphoreSlim` bằng `using`/`await using`;
- tách lỗi dữ liệu của từng file khỏi lỗi làm hỏng cả batch;
- ghi báo cáo qua file tạm rồi thay thế file đích để giảm rủi ro file JSON dở dang;
- giải thích object, task, closure và reference nào còn sống trong lúc batch chạy;
- build, chạy và kiểm tra failure path của một project `net9.0` không dùng package ngoài.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Nhiều phiếu chờ đọc nhưng chỉ hai cửa mở file cùng lúc. Phiếu lỗi dữ liệu được ghi riêng; yêu cầu hủy dừng operation chung. Báo cáo chỉ thay bản cũ khi file mới đã ghi và đóng.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| permit | quyền vào vùng xử lý giới hạn | SemaphoreSlim |
| input-level failure | lỗi một file được chuyển thành result | JSON sai |
| commit point | bước công bố output mới | File.Move |
| backpressure | làm producer chậm khi consumer đầy | chưa có trong task-per-file demo |

### Ví dụ nhỏ — tính tay trước

Ba file:650000,3000000 vàquantity0 →2success,1failure,total3650000,3events,exit1. Pre-cancel phải đi lên caller, không trở thành ba dòng lỗi input.

Một hệ thống bán hàng cũ xuất mỗi đơn hàng thành một file JSON. Cuối ngày, chương trình cần:

1. đọc các file mà người gọi cung cấp;
2. kiểm tra `orderId`, email và từng dòng hàng;
3. tính tổng tiền cho file hợp lệ;
4. không dừng cả batch chỉ vì một file sai dữ liệu;
5. không mở quá nhiều file cùng lúc;
6. cho phép hủy toàn bộ công việc khi hết thời gian;
7. lưu một báo cáo JSON có thể dùng ở bước sau;
8. in kết quả theo tên file, dù các file hoàn thành không theo thứ tự.

Nếu xử lý tuần tự, thời gian chờ I/O của file này không thể chồng lấp với file khác. Nếu tạo một `Task` cho mọi file mà không giới hạn, một batch lớn có thể dùng cạn file handle hoặc gây áp lực lên ổ đĩa. Nếu nhiều task cùng `Console.WriteLine`, thứ tự output trở nên không xác định. Nếu `catch (Exception)` cho từng file, lỗi lập trình cũng có thể bị biến thành một dòng “dữ liệu sai” và bị che giấu.

Ta sẽ xây một pipeline nhỏ với quyết định rõ ràng:

```text
Program
  -> tạo đúng danh sách file đầu vào
  -> OrderBatchProcessor.ProcessAsync
       -> mỗi file chờ cổng SemaphoreSlim
       -> deserialize JSON bất đồng bộ
       -> validate bằng delegate
       -> tạo FileResult; phát event tiến độ
  -> Task.WhenAll trả toàn bộ kết quả
  -> sort kết quả một lần
  -> ReportWriter ghi file tạm rồi replace
  -> Program in summary ổn định
```

Đây là project tổng kết module 05. Nó không dùng LINQ, database, dependency injection container hay framework web vì các khái niệm đó nằm ở module sau.

### Tiêu chí chấp nhận

- Ba file demo tạo ra hai kết quả thành công và một lỗi validation.
- `maxConcurrency` phải lớn hơn `0`; chương trình demo dùng giá trị `2`.
- Một file JSON/validation lỗi không chặn các file còn lại.
- Cancellation không bị đổi thành `FileResult` thất bại; nó phải đi lên entry point.
- Kết quả luôn được in theo tên file.
- Event được phát đúng một lần cho mỗi file đã chuyển thành kết quả.
- Báo cáo chỉ thay file đích sau khi serialize và đóng file tạm thành công.
- Build bật nullable và coi compiler warning là error.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

### 3.1. Tạo project

Yêu cầu .NET SDK 9.x:

```bash
dotnet --version
mkdir AsyncOrderBatch
cd AsyncOrderBatch
dotnet new console --framework net9.0 --use-program-main
mkdir -p Domain Application Infrastructure Serialization
```

Thay file project bằng nội dung sau.

`AsyncOrderBatch.csproj`:

```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>Exe</OutputType>
    <TargetFramework>net9.0</TargetFramework>
    <LangVersion>13.0</LangVersion>
    <ImplicitUsings>enable</ImplicitUsings>
    <Nullable>enable</Nullable>
    <TreatWarningsAsErrors>true</TreatWarningsAsErrors>
  </PropertyGroup>
</Project>
```

### 3.2. Domain: dữ liệu vào và dữ liệu báo cáo

`Domain/Models.cs`:

```csharp
namespace AsyncOrderBatch.Domain;

public sealed record OrderLine(
    string Sku,
    int Quantity,
    decimal UnitPrice);

public sealed record OrderDocument(
    string OrderId,
    string? CustomerEmail,
    OrderLine[] Lines);

public sealed record OrderReport(
    string OrderId,
    string? CustomerEmail,
    decimal Total);

public sealed record FileResult(
    string FileName,
    OrderReport? Order,
    string? Error)
{
    public bool IsSuccess => Order is not null && Error is null;

    public static FileResult Success(string fileName, OrderReport order)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(fileName);
        ArgumentNullException.ThrowIfNull(order);
        return new FileResult(fileName, order, Error: null);
    }

    public static FileResult Failure(string fileName, string error)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(fileName);
        ArgumentException.ThrowIfNullOrWhiteSpace(error);
        return new FileResult(fileName, Order: null, error);
    }
}

public sealed record BatchReport(
    int TotalFiles,
    int Succeeded,
    int Failed,
    decimal GrandTotal,
    FileResult[] Files);
```

Các positional `record` giúp biểu diễn data carrier ngắn gọn. Tính bất biến ở đây là *shallow*: property `Lines` và `Files` không có setter, nhưng object array vẫn có thể bị sửa qua reference đang giữ array. Project chỉ truyền quyền sở hữu các array này theo một hướng và không sửa sau khi tạo báo cáo. Nếu array phải đi qua trust boundary, hãy clone hoặc dùng immutable collection phù hợp.

### 3.3. Validation result, extension method và rule nghiệp vụ

`Application/ValidationResult.cs`:

```csharp
namespace AsyncOrderBatch.Application;

public readonly record struct ValidationResult(bool IsValid, string? Error)
{
    public static ValidationResult Valid() => new(true, Error: null);

    public static ValidationResult Invalid(string error)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(error);
        return new ValidationResult(false, error);
    }
}
```

`Application/StringExtensions.cs`:

```csharp
namespace AsyncOrderBatch.Application;

public static class StringExtensions
{
    public static string? NormalizeOptionalEmail(this string? value)
    {
        return string.IsNullOrWhiteSpace(value)
            ? null
            : value.Trim().ToLowerInvariant();
    }
}
```

`Application/OrderRules.cs`:

```csharp
using AsyncOrderBatch.Domain;

namespace AsyncOrderBatch.Application;

public static class OrderRules
{
    public static ValidationResult Validate(OrderDocument document)
    {
        ArgumentNullException.ThrowIfNull(document);

        if (string.IsNullOrWhiteSpace(document.OrderId))
        {
            return ValidationResult.Invalid("orderId không được để trống.");
        }

        string? email = document.CustomerEmail.NormalizeOptionalEmail();
        if (email is not null && !email.Contains('@', StringComparison.Ordinal))
        {
            return ValidationResult.Invalid("customerEmail không đúng định dạng tối thiểu.");
        }

        // JSON bên ngoài có thể thiếu/null dù property được khai báo non-nullable.
        if (document.Lines is not { Length: > 0 })
        {
            return ValidationResult.Invalid("Đơn hàng phải có ít nhất một dòng.");
        }

        foreach (OrderLine? line in document.Lines)
        {
            if (line is null)
            {
                return ValidationResult.Invalid("Dòng hàng không được là null.");
            }

            if (string.IsNullOrWhiteSpace(line.Sku))
            {
                return ValidationResult.Invalid("SKU không được để trống.");
            }

            if (line.Quantity <= 0)
            {
                return ValidationResult.Invalid(
                    $"Quantity của SKU {line.Sku} phải lớn hơn 0.");
            }

            if (line.UnitPrice < 0)
            {
                return ValidationResult.Invalid(
                    $"UnitPrice của SKU {line.Sku} không được âm.");
            }
        }

        return ValidationResult.Valid();
    }

    public static decimal CalculateTotal(OrderDocument document)
    {
        ArgumentNullException.ThrowIfNull(document);

        decimal total = 0m;
        foreach (OrderLine line in document.Lines)
        {
            total = checked(total + (line.Quantity * line.UnitPrice));
        }

        return total;
    }
}
```

`ValidationResult` là value nhỏ nên dùng `readonly record struct`. Rule trả lỗi dự kiến thay vì ném exception. `CalculateTotal` chỉ được gọi sau validation; `checked` làm contract overflow tường minh.

### 3.4. Event tiến độ

`Application/FileProcessedEventArgs.cs`:

```csharp
namespace AsyncOrderBatch.Application;

public sealed class FileProcessedEventArgs : EventArgs
{
    public string FileName { get; }
    public bool Succeeded { get; }

    public FileProcessedEventArgs(string fileName, bool succeeded)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(fileName);
        FileName = fileName;
        Succeeded = succeeded;
    }
}
```

### 3.5. Processor bất đồng bộ có giới hạn concurrency

`Application/OrderBatchProcessor.cs`:

```csharp
using System.Text.Json;
using AsyncOrderBatch.Domain;
using AsyncOrderBatch.Serialization;

namespace AsyncOrderBatch.Application;

public sealed class OrderBatchProcessor : IDisposable
{
    private readonly SemaphoreSlim _gate;
    private readonly Func<OrderDocument, ValidationResult> _validator;
    private bool _disposed;

    public event EventHandler<FileProcessedEventArgs>? FileProcessed;

    public OrderBatchProcessor(
        int maxConcurrency,
        Func<OrderDocument, ValidationResult> validator)
    {
        if (maxConcurrency <= 0)
        {
            throw new ArgumentOutOfRangeException(
                nameof(maxConcurrency),
                "Mức concurrency phải lớn hơn 0.");
        }

        ArgumentNullException.ThrowIfNull(validator);
        _gate = new SemaphoreSlim(maxConcurrency, maxConcurrency);
        _validator = validator;
    }

    public async Task<BatchReport> ProcessAsync(
        string[] inputPaths,
        CancellationToken cancellationToken)
    {
        ThrowIfDisposed();
        ArgumentNullException.ThrowIfNull(inputPaths);

        // Validate toàn bộ batch trước khi khởi chạy task. Nếu vừa schedule vừa
        // validate, một path sai ở cuối có thể để các task đầu chạy không được await.
        for (int index = 0; index < inputPaths.Length; index++)
        {
            ArgumentException.ThrowIfNullOrWhiteSpace(inputPaths[index]);
        }

        var tasks = new Task<FileResult>[inputPaths.Length];
        for (int index = 0; index < inputPaths.Length; index++)
        {
            tasks[index] = ProcessOneAsync(inputPaths[index], cancellationToken);
        }

        FileResult[] results = await Task.WhenAll(tasks);

        // Task hoàn thành theo timing I/O; sort một lần để output thành contract ổn định.
        Array.Sort(
            results,
            static (left, right) =>
                StringComparer.Ordinal.Compare(left.FileName, right.FileName));

        int succeeded = 0;
        decimal grandTotal = 0m;

        foreach (FileResult result in results)
        {
            if (result is { IsSuccess: true, Order: not null } successful)
            {
                succeeded++;
                grandTotal = checked(grandTotal + successful.Order.Total);
            }
        }

        return new BatchReport(
            TotalFiles: results.Length,
            Succeeded: succeeded,
            Failed: results.Length - succeeded,
            GrandTotal: grandTotal,
            Files: results);
    }

    private async Task<FileResult> ProcessOneAsync(
        string path,
        CancellationToken cancellationToken)
    {
        await _gate.WaitAsync(cancellationToken);

        try
        {
            FileResult result;

            try
            {
                await using var input = new FileStream(
                    path,
                    FileMode.Open,
                    FileAccess.Read,
                    FileShare.Read,
                    bufferSize: 4_096,
                    options: FileOptions.Asynchronous | FileOptions.SequentialScan);

                OrderDocument? document = await JsonSerializer.DeserializeAsync(
                    input,
                    BatchJsonContext.Default.OrderDocument,
                    cancellationToken);

                if (document is null)
                {
                    result = FileResult.Failure(
                        Path.GetFileName(path),
                        "JSON không chứa một đơn hàng.");
                }
                else
                {
                    ValidationResult validation = _validator(document);

                    result = validation switch
                    {
                        { IsValid: true, Error: null } => FileResult.Success(
                            Path.GetFileName(path),
                            new OrderReport(
                                document.OrderId.Trim(),
                                document.CustomerEmail.NormalizeOptionalEmail(),
                                OrderRules.CalculateTotal(document))),

                        { IsValid: false, Error: not null } => FileResult.Failure(
                            Path.GetFileName(path),
                            validation.Error),

                        _ => throw new InvalidOperationException(
                            "Validator trả về trạng thái không nhất quán.")
                    };
                }
            }
            catch (OperationCanceledException) when (cancellationToken.IsCancellationRequested)
            {
                // Hủy là trạng thái của cả operation, không phải dữ liệu hỏng của một file.
                throw;
            }
            catch (JsonException exception)
            {
                result = FileResult.Failure(
                    Path.GetFileName(path),
                    $"JSON không hợp lệ: {exception.Message}");
            }
            catch (InvalidDataException exception)
            {
                result = FileResult.Failure(Path.GetFileName(path), exception.Message);
            }
            catch (OverflowException)
            {
                result = FileResult.Failure(
                    Path.GetFileName(path),
                    "Tổng tiền vượt phạm vi decimal.");
            }
            catch (IOException exception)
            {
                result = FileResult.Failure(
                    Path.GetFileName(path),
                    $"Không đọc được file: {exception.Message}");
            }
            catch (UnauthorizedAccessException exception)
            {
                result = FileResult.Failure(
                    Path.GetFileName(path),
                    $"Không có quyền đọc file: {exception.Message}");
            }

            OnFileProcessed(result);
            return result;
        }
        finally
        {
            _gate.Release();
        }
    }

    private void OnFileProcessed(FileResult result)
    {
        EventHandler<FileProcessedEventArgs>? handler = FileProcessed;
        handler?.Invoke(
            this,
            new FileProcessedEventArgs(result.FileName, result.IsSuccess));
    }

    private void ThrowIfDisposed()
    {
        if (_disposed)
        {
            throw new ObjectDisposedException(nameof(OrderBatchProcessor));
        }
    }

    public void Dispose()
    {
        if (_disposed)
        {
            return;
        }

        _gate.Dispose();
        _disposed = true;
    }
}
```

Processor bắt có chủ đích các lỗi mà boundary file/JSON dự kiến có thể biến thành kết quả từng file. Lỗi lập trình như `NullReferenceException` không bị gom vào “file lỗi”. Handler event của project chỉ dùng `Interlocked.Increment`, nên không ném exception; publisher production phải ghi rõ policy nếu subscriber có thể lỗi.

### 3.6. JSON source generation

`Serialization/BatchJsonContext.cs`:

```csharp
using System.Text.Json.Serialization;
using AsyncOrderBatch.Domain;

namespace AsyncOrderBatch.Serialization;

[JsonSourceGenerationOptions(
    PropertyNamingPolicy = JsonKnownNamingPolicy.CamelCase,
    WriteIndented = true)]
[JsonSerializable(typeof(OrderDocument))]
[JsonSerializable(typeof(BatchReport))]
internal sealed partial class BatchJsonContext : JsonSerializerContext;
```

`partial` cho source generator của `System.Text.Json` bổ sung metadata serialize/deserialize ở compile time. Đây là code generation tích hợp trong .NET SDK, không phải package ngoài hay reflection tự viết.

### 3.7. Tạo dữ liệu demo

`Infrastructure/DemoData.cs`:

```csharp
using System.Text.Json;
using AsyncOrderBatch.Domain;
using AsyncOrderBatch.Serialization;

namespace AsyncOrderBatch.Infrastructure;

public static class DemoData
{
    public static async Task<string[]> PrepareAsync(
        string rootDirectory,
        CancellationToken cancellationToken)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(rootDirectory);

        string inputDirectory = Path.Combine(rootDirectory, "input");
        Directory.CreateDirectory(inputDirectory);

        string[] paths =
        [
            Path.Combine(inputDirectory, "01-order.json"),
            Path.Combine(inputDirectory, "02-order.json"),
            Path.Combine(inputDirectory, "03-order.json")
        ];

        var first = new OrderDocument(
            "ORD-001",
            " LAN@Example.COM ",
            [
                new OrderLine("KEYBOARD", 2, 250_000m),
                new OrderLine("MOUSE", 1, 150_000m)
            ]);

        var second = new OrderDocument(
            "ORD-002",
            CustomerEmail: null,
            [new OrderLine("MONITOR", 1, 3_000_000m)]);

        // File JSON hợp lệ về cú pháp nhưng vi phạm rule Quantity > 0.
        var invalid = new OrderDocument(
            "ORD-003",
            "buyer@example.com",
            [new OrderLine("BROKEN", 0, 10m)]);

        await WriteAsync(paths[0], first, cancellationToken);
        await WriteAsync(paths[1], second, cancellationToken);
        await WriteAsync(paths[2], invalid, cancellationToken);

        return paths;
    }

    private static async Task WriteAsync(
        string path,
        OrderDocument document,
        CancellationToken cancellationToken)
    {
        await using var output = new FileStream(
            path,
            FileMode.Create,
            FileAccess.Write,
            FileShare.None,
            bufferSize: 4_096,
            options: FileOptions.Asynchronous);

        await JsonSerializer.SerializeAsync(
            output,
            document,
            BatchJsonContext.Default.OrderDocument,
            cancellationToken);
    }
}
```

Demo trả chính xác ba path vừa ghi, không quét toàn bộ thư mục. Vì thế một file cũ do người học đặt cạnh đó không âm thầm đi vào batch.

### 3.8. Ghi báo cáo qua file tạm

`Infrastructure/ReportWriter.cs`:

```csharp
using System.Text.Json;
using AsyncOrderBatch.Domain;
using AsyncOrderBatch.Serialization;

namespace AsyncOrderBatch.Infrastructure;

public static class ReportWriter
{
    public static async Task WriteAsync(
        BatchReport report,
        string outputPath,
        CancellationToken cancellationToken)
    {
        ArgumentNullException.ThrowIfNull(report);
        ArgumentException.ThrowIfNullOrWhiteSpace(outputPath);

        string fullOutputPath = Path.GetFullPath(outputPath);
        string? outputDirectory = Path.GetDirectoryName(fullOutputPath);

        if (outputDirectory is null)
        {
            throw new InvalidOperationException("Không xác định được thư mục output.");
        }

        Directory.CreateDirectory(outputDirectory);

        string temporaryPath = Path.Combine(
            outputDirectory,
            $".{Path.GetFileName(outputPath)}.{Guid.NewGuid():N}.tmp");

        try
        {
            await using (var output = new FileStream(
                temporaryPath,
                FileMode.CreateNew,
                FileAccess.Write,
                FileShare.None,
                bufferSize: 4_096,
                options: FileOptions.Asynchronous | FileOptions.WriteThrough))
            {
                await JsonSerializer.SerializeAsync(
                    output,
                    report,
                    BatchJsonContext.Default.BatchReport,
                    cancellationToken);

                await output.FlushAsync(cancellationToken);
            }

            // Đây là cancellation checkpoint cuối trước commit đồng bộ.
            cancellationToken.ThrowIfCancellationRequested();

            // Stream đã đóng trước khi move; overwrite hoạt động cả khi report đã có.
            File.Move(temporaryPath, fullOutputPath, overwrite: true);
        }
        finally
        {
            TryDeleteTemporaryFile(temporaryPath);
        }
    }

    private static void TryDeleteTemporaryFile(string path)
    {
        try
        {
            File.Delete(path); // Không ném nếu file không tồn tại.
        }
        catch (IOException)
        {
            // Best effort cho file tạm. Production nên log để có thể dọn sau.
        }
        catch (UnauthorizedAccessException)
        {
            // Không che exception gốc bằng lỗi cleanup thứ hai.
        }
    }
}
```

Ghi file tạm rồi `File.Move(..., overwrite: true)` giảm cửa sổ để consumer thấy JSON ghi dở. Nó không tự biến filesystem thành database transaction: tính atomic/durability chính xác còn phụ thuộc filesystem, volume và hệ điều hành. Project production phải kiểm chứng guarantee trên môi trường triển khai.

### 3.9. Entry point

`Program.cs`:

```csharp
using System.Globalization;
using AsyncOrderBatch.Application;
using AsyncOrderBatch.Domain;
using AsyncOrderBatch.Infrastructure;

namespace AsyncOrderBatch;

internal static class Program
{
    private static async Task<int> Main(string[] args)
    {
        if (args is not ["demo"])
        {
            Console.Error.WriteLine("Usage: dotnet run -- demo");
            return 2;
        }

        string demoRoot = Path.Combine(
            Directory.GetCurrentDirectory(),
            "demo-data");

        using var timeout = new CancellationTokenSource(
            TimeSpan.FromSeconds(10));

        try
        {
            string[] paths = await DemoData.PrepareAsync(
                demoRoot,
                timeout.Token);

            using var processor = new OrderBatchProcessor(
                maxConcurrency: 2,
                OrderRules.Validate);

            int observedEvents = 0;

            processor.FileProcessed += (_, _) =>
                Interlocked.Increment(ref observedEvents);

            BatchReport report = await processor.ProcessAsync(
                paths,
                timeout.Token);

            string reportPath = Path.Combine(demoRoot, "report.json");
            await ReportWriter.WriteAsync(report, reportPath, timeout.Token);

            foreach (FileResult result in report.Files)
            {
                string line = result switch
                {
                    { IsSuccess: true, Order: not null } =>
                        $"{result.FileName}: OK - {result.Order.OrderId} - " +
                        $"{FormatMoney(result.Order.Total)} VND",

                    { Error: not null } =>
                        $"{result.FileName}: ERROR - {result.Error}",

                    _ => $"{result.FileName}: ERROR - Kết quả không hợp lệ."
                };

                Console.WriteLine(line);
            }

            Console.WriteLine($"Processed files: {report.TotalFiles}");
            Console.WriteLine($"Succeeded: {report.Succeeded}");
            Console.WriteLine($"Failed: {report.Failed}");
            Console.WriteLine($"Observed events: {observedEvents}");
            Console.WriteLine($"Grand total: {FormatMoney(report.GrandTotal)} VND");
            Console.WriteLine("Report: demo-data/report.json");
            return report.Failed == 0 ? 0 : 1;
        }
        catch (OperationCanceledException) when (timeout.IsCancellationRequested)
        {
            Console.Error.WriteLine("Batch đã bị hủy do hết thời gian.");
            return 3;
        }
        catch (IOException exception)
        {
            Console.Error.WriteLine($"Lỗi I/O ở boundary: {exception.Message}");
            return 4;
        }
        catch (UnauthorizedAccessException exception)
        {
            Console.Error.WriteLine($"Lỗi quyền truy cập: {exception.Message}");
            return 4;
        }
    }

    private static string FormatMoney(decimal value) =>
        value.ToString("0.##", CultureInfo.InvariantCulture);
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build -- demo
```

Output chuẩn:

```text
01-order.json: OK - ORD-001 - 650000 VND
02-order.json: OK - ORD-002 - 3000000 VND
03-order.json: ERROR - Quantity của SKU BROKEN phải lớn hơn 0.
Processed files: 3
Succeeded: 2
Failed: 1
Observed events: 3
Grand total: 3650000 VND
Report: demo-data/report.json
```

Process trả exit code `1` vì batch có một file thất bại có chủ đích. Trong shell, có thể kiểm tra ngay sau lệnh chạy:

```bash
echo $?
```

Output:

```text
1
```

Kiểm tra nhánh usage:

```bash
dotnet run --no-build
echo $?
```

Output:

```text
Usage: dotnet run -- demo
2
```

Project đã được build và chạy bằng .NET SDK `9.0.121`, target `net9.0`, C# 13, nullable bật và không dùng NuGet package ngoài.

### Walkthrough — execution / state / cost

1. Program tạo đúng ba path; processor validate toàn bộ path trước schedule.
2. Mỗi task acquire permit, await deserialize rồi validate/calculate; finally release sau acquire thành công.
3. WhenAll thu result; sort theo FileName, tính report và ghi temp/flush/close.
4. Token được kiểm lần cuối trước move. Memory gồm O(n) tasks/results, active file buffers giới hạn; sort O(n log n), dữ liệu file vẫn có thể lớn.

### Mini-check

Event handler ném: permit có được trả và batch tiếp theo còn chạy được không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Luồng thời gian của một batch

Sau khi tạo ba `Task<FileResult>`, mỗi task đi đến `_gate.WaitAsync`:

```text
maxConcurrency = 2

time --->

file 01: [wait gate][open/read/validate/close][result]
file 02: [wait gate][open/read/validate/close][result]
file 03: [---------- wait gate ----------][open/read/...][result]
                                              ^
                         một permit được Release ở finally

Task.WhenAll: [---------------- chờ đủ cả ba ----------------][return array]
```

`SemaphoreSlim(2, 2)` có hai permit. Hai file đầu có thể đi vào vùng xử lý; file thứ ba chờ mà không cần block một thread. `finally` trả permit dù deserialize, validation hay event ném. Nếu quên `Release`, batch sau có thể treo vĩnh viễn.

Đây là **concurrency** của các operation I/O. Chương trình không cam kết hai đoạn CPU luôn chạy song song trên hai core. `async`/`await` giúp thread không phải ngồi chờ I/O; nó không đồng nghĩa “tạo thread mới”.

### 4.2. `Task.WhenAll` không quyết định thứ tự hoàn thành

Array `tasks` được điền theo `inputPaths`, nhưng file nhỏ hơn có thể hoàn thành trước. Event phản ánh thời điểm thực tế và không được dùng làm thứ tự báo cáo. `Task.WhenAll<TResult>` trả các result tương ứng theo thứ tự task đầu vào, **không phải** thứ tự hoàn thành; tuy vậy caller cũng không hứa `inputPaths` đã xếp theo tên. Vì thế processor vẫn sort `FileResult[]` theo `FileName` trước khi trả `BatchReport`.

Hai contract cần tách:

```text
completion order: do scheduler, cache và filesystem quyết định
presentation order: do code Array.Sort quyết định
```

Không thêm `lock` quanh toàn bộ `ProcessOneAsync`: giữ monitor lock qua `await` vừa không hợp lệ với `lock` thông thường, vừa vô hiệu hóa concurrency.

### 4.3. Cancellation truyền theo đường gọi

```text
CancellationTokenSource timeout
          |
          +--> DemoData.PrepareAsync
          |       +--> JsonSerializer.SerializeAsync
          |
          +--> ProcessAsync
          |       +--> SemaphoreSlim.WaitAsync
          |       +--> JsonSerializer.DeserializeAsync
          |
          +--> ReportWriter.WriteAsync
                  +--> SerializeAsync / FlushAsync
```

Token là value được copy; các copy cùng quan sát state cancellation của source. Timeout gọi `Cancel` bên trong source khi hết 10 giây. API hợp tác sẽ ném `OperationCanceledException`. Filter chỉ nhận cancellation thuộc operation này, rồi entry point đổi nó thành exit code `3`.

Processor không catch cancellation thành một `FileResult`: nếu làm vậy, caller có thể nhận báo cáo “hoàn tất” dù yêu cầu đã hủy. Cancellation cũng không rollback file demo đã ghi xong trước đó; muốn rollback cần protocol riêng.

`ReportWriter` kiểm tra token lần cuối sau khi đóng file tạm và trước `File.Move`. Khi bước move đồng bộ đã bắt đầu, cancellation không thể rollback một replace đã hoàn tất; đó là commit point của writer.

### 4.4. Ranh giới exception

```text
lỗi riêng một input
JsonException / InvalidDataException / OverflowException / read IOException
            |
            v
FileResult.Failure -> batch tiếp tục

lỗi toàn operation
OperationCanceledException do token chung
            |
            v
rethrow -> Program -> exit 3

lỗi lập trình không dự kiến
NullReferenceException, invariant nội bộ bị phá, ...
            |
            v
không bị catch ở processor -> fail fast tới boundary
```

Mỗi boundary chỉ bắt lỗi mà nó có quyết định phục hồi. `ReportWriter` không bắt lỗi ghi report rồi giả thành công; I/O đó đi lên `Program`. Nếu validator được inject trả cặp state mâu thuẫn như `IsValid = false` nhưng không có `Error`, processor coi đó là lỗi contract lập trình và để `InvalidOperationException` đi lên thay vì âm thầm chấp nhận file. Message exception có thể phụ thuộc hệ điều hành nên output chuẩn chỉ dùng lỗi validation do ta kiểm soát.

`ProcessAsync` validate **toàn bộ** `inputPaths` trước khi tạo task đầu tiên. Nếu validate và schedule trong cùng vòng lặp, một argument sai ở cuối có thể làm method thoát trong khi task của các path đầu vẫn chạy mà không còn được await.

### 4.5. Lifetime tài nguyên

```text
using var timeout       -> Dispose khi rời block Main
using var processor     -> Dispose SemaphoreSlim sau ProcessAsync
await using FileStream  -> DisposeAsync khi rời block đọc/ghi
try/finally gate        -> Release permit, không Dispose semaphore
```

GC thu hồi managed memory khi object không còn reachable; GC không phải contract đóng file đúng lúc. `await using` gọi `DisposeAsync`, cho phép bước flush/close bất đồng bộ nếu implementation hỗ trợ. `OrderBatchProcessor` sở hữu `_gate`, nên nó chịu trách nhiệm dispose. Caller không được gọi `Dispose` khi `ProcessAsync` còn chạy; trong project, `using` chỉ kết thúc sau `await`.

File tạm được đóng trước `File.Move`, điều đặc biệt quan trọng trên Windows. Block `finally` dọn file tạm còn lại. Cleanup chỉ best effort và không che exception chính; hệ thống production nên log file không dọn được.

### 4.6. Mô hình bộ nhớ và object graph

Ngay sau khi ba task đã bắt đầu, mô hình logic có dạng:

```text
MAIN ASYNC STATE (managed state-machine object khi đã suspend)
├─ timeout ref ───────────────> H1 CancellationTokenSource
├─ processor ref ─────────────> H2 OrderBatchProcessor
│                                ├─ _gate ref ─────> H3 SemaphoreSlim
│                                ├─ _validator ────> delegate(method OrderRules.Validate)
│                                └─ FileProcessed -> delegate target H4 closure
├─ observedEvents nằm trong ───> H4 closure { int observedEvents }
├─ paths ref ──────────────────> H5 string[3]
└─ current Task/awaiter state

H6 Task<FileResult> for file 01 ─┐
H7 Task<FileResult> for file 02 ─┼─> cùng H2/H3 và token state H1
H8 Task<FileResult> for file 03 ─┘

mỗi ProcessOneAsync đang đọc
  -> một FileStream object
  -> buffer/runtime I/O state
  -> sau deserialize: một OrderDocument object
       └─ Lines ref -> OrderLine[]; mỗi phần tử là reference tới OrderLine record
```

Các nhãn H1…H8 là identity logic, không phải địa chỉ vật lý cố định. CLR có thể di chuyển object khi compact heap.

Mỗi `new OrderDocument`, `new OrderLine`, `new SemaphoreSlim`, `new FileStream` tạo instance reference-type riêng. Gán các reference vào field/local không clone object. `CancellationToken` và `ValidationResult` là value type; phép gán copy value. `FileProcessed` giữ delegate tới lambda. Vì lambda capture `observedEvents`, compiler đặt biến đó trong một closure object H4; cả `Main` và event handler truy cập cùng field. `Interlocked.Increment` cập nhật field này atomically khi event có thể đến từ nhiều luồng.

`OrderDocument` là record class. `with`/value equality của record không deep-copy `Lines`; array vẫn là object riêng được trỏ tới. Project không dựa vào record để bảo vệ deep immutability.

### 4.7. Vì sao không dùng `Task.Run`?

File/JSON stream đã có API async. Bọc nó bằng `Task.Run(() => File.ReadAllText(...))` chỉ chiếm thread-pool thread để chờ I/O đồng bộ. Ta await API I/O trực tiếp. Phần tính tổng rất nhỏ và đồng bộ; đẩy từng phép nhân sang thread pool sẽ tăng scheduling overhead.

Nếu sau này transform CPU thực sự nặng, hãy đo và tách một stage parallel có giới hạn. Không suy ra “càng nhiều task càng nhanh”.

### 4.8. Ghi file tạm không phải transaction toàn hệ thống

Thứ tự của writer:

```text
serialize -> flush -> close temporary file -> cancellation check
          -> move/replace destination (commit)
```

Consumer ít có khả năng thấy nửa JSON hơn cách mở thẳng report đích bằng `FileMode.Create`. Tuy nhiên:

- crash trước `Move` có thể để lại file tạm;
- guarantee atomic khác nhau nếu source/destination ở khác volume;
- `WriteThrough` không chứng minh mọi tầng phần cứng đã durable;
- report và input không nằm trong một transaction chung.

Pattern này phù hợp bài console một máy. Database transaction, idempotency và distributed consistency sẽ được học ở các module sau.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| tuần tự | ít task/state | đủ batch nhỏ không cần overlap |
| semaphore + tasks | giới hạn active I/O | vẫn O(n) pending tasks |
| bounded producer/consumer | giới hạn work chờ | chỉ thêm khi input lớn/stream cần backpressure |

### Misconception check

**Đúng hay sai?** WhenAll trả theo thứ tự hoàn thành.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: kết quả theo thứ tự task input; sample sort thêm theo tên.

</details>

**Đúng hay sai?** Cancel tự phục hồi mọi file đã ghi.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: checkpoint hợp tác, không rollback effect trước đó.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** chạy batch và trace.

- **Working Developer — dùng khi làm việc:** cancellation/failure/resource ownership.

- **Deep Dive — có thể quay lại sau:** backpressure/durability khi có driver.

### Các abstraction được ghép lại

| Thành phần | Vai trò | Bài đã chuẩn bị |
|---|---|---|
| `Func<OrderDocument, ValidationResult>` | inject rule validation bằng delegate | bài 01–02 |
| `event EventHandler<T>` | thông báo tiến độ mà processor không biết subscriber | bài 03 |
| lambda capture + `Interlocked` | đếm event an toàn | bài 04, 11 |
| extension method trên `string?` | normalize dữ liệu nullable | bài 05–06 |
| `record`, `record struct` | data carrier/value result | bài 07 |
| property/list pattern | phân nhánh kết quả và validation | bài 08 |
| `Task`, `async`, `await` | biểu diễn operation chưa hoàn tất | bài 09 |
| token, timeout, exception async | hủy có hợp tác | bài 10 |
| `SemaphoreSlim`, `Task.WhenAll`, `Interlocked` | bounded concurrency và state dùng chung | bài 11 |
| `IDisposable`, `await using` | lifetime tài nguyên xác định | bài 12 |
| JSON source generation | contract serialize/deserialize | bài 13, 17 |
| đo trước khi tối ưu | không thêm parallelism theo cảm tính | bài 14, 18 |

Bài 15–16 giải thích variance/expression tree nhưng project không ép dùng khi bài toán không cần. Dùng đủ keyword không phải mục tiêu; chọn đúng abstraction mới là mục tiêu.

### `SemaphoreSlim` là cổng, không phải hàng đợi bền vững

`WaitAsync` chỉ hoàn tất thành công sau khi đã lấy và giảm một permit; nếu bị hủy khi còn chờ, nó ném và không lấy permit. `Release` tăng lại permit sau vùng xử lý. Vì `try/finally` của `ProcessOneAsync` bắt đầu **sau** `await WaitAsync`, mỗi lần `Release` luôn ghép với một lần lấy permit thành công. Cổng này giới hạn số operation trong một process, nhưng:

- không lưu job nếu process dừng;
- không điều phối nhiều process/máy;
- không bảo đảm business ordering;
- không tự retry.

Message queue/broker cho bài toán bền vững và phân tán nằm ở module 18–19, không nên gọi `SemaphoreSlim` là message queue.

### `Task.WhenAll` và failure

`Task.WhenAll` hoàn tất thành công khi mọi task thành công. Nếu ít nhất một task fault, task tổng ở trạng thái `Faulted` dù task khác có bị cancel; `Exception` của task tổng chứa các exception đã được unwrap từ các task fault. Chỉ khi **không có task fault** nhưng có ít nhất một task bị cancel, task tổng mới ở trạng thái `Canceled`. `await` truyền exception/cancellation lên caller; nếu cần thống kê mọi fault đồng thời, giữ task tổng và đọc `Exception` của nó sau khi task đã hoàn tất.

Project chủ động chuyển lỗi *input-level* thành value để `WhenAll` thu đủ kết quả, nhưng để cancellation và bug đi lên. Đây là policy nghiệp vụ, không phải quy tắc rằng mọi exception async phải bị bắt.

### Giới hạn concurrency khác batching

- **Batching**: gom nhiều item thành một nhóm để giảm overhead mỗi lần gọi.
- **Bounded concurrency**: giới hạn số operation đang in-flight.
- **Parallelism**: thực thi CPU đồng thời trên nhiều core.
- **Backpressure**: làm producer chậm lại khi consumer không theo kịp.

Project có một batch hữu hạn và bounded concurrency. Vì tạo một task cho mỗi path ngay từ đầu, nó chưa phải pipeline backpressure tối ưu cho hàng triệu file. Với input cực lớn, dùng producer/consumer có bounded channel; API `Channel<T>` sẽ được giới thiệu ở phần kiến trúc/messaging khi có bài toán phù hợp.

### Source-generated JSON contract

`BatchJsonContext.Default.OrderDocument` là metadata type cụ thể do compiler tạo. Ưu điểm:

- lỗi thiếu metadata dễ phát hiện hơn;
- giảm reflection runtime;
- thân thiện hơn với trimming/AOT;
- contract serialize được nhìn thấy trong source.

Source generation không tự validate rule như quantity dương, không tự version schema, và không biến JSON không tin cậy thành dữ liệu an toàn. Deserialization luôn phải đi qua validation boundary.

### Exit code là API của command-line program

| Exit code | Nghĩa trong project |
|---:|---|
| `0` | toàn bộ file thành công |
| `1` | batch chạy xong nhưng có file lỗi |
| `2` | cách gọi command sai |
| `3` | operation bị timeout/cancel |
| `4` | lỗi I/O/quyền ở boundary không thể hoàn tất report |

Shell/CI dùng exit code, không nên parse câu tiếng Việt trên console để đoán thành công.

## 6. Lỗi thường gặp

### Tạo task không giới hạn

Một triệu path tạo một triệu task và cạnh tranh file handle. Với batch vừa, dùng `SemaphoreSlim`; với stream rất lớn, thiết kế producer/consumer có bounded capacity để có backpressure.

### Schedule trước khi validate hết input

Nếu path thứ ba sai sau khi hai task đầu đã chạy, method có thể thoát mà không await hai task đó. Validate toàn bộ batch trước, rồi mới tạo task để lỗi argument không để lại background work ngoài ownership.

### Dùng `Task.Run` cho I/O đã có API async

Nó không làm ổ đĩa nhanh hơn và giữ thread pool thread không cần thiết. Gọi `ReadAsync`, `DeserializeAsync`, `WriteAsync` trực tiếp.

### Quên truyền token xuống API con

Method nhận `CancellationToken` nhưng gọi `WaitAsync()`/`DeserializeAsync()` không token làm cancellation chậm hoặc vô hiệu. Truyền cùng token qua mọi operation có cùng lifetime.

### Catch `OperationCanceledException` thành lỗi file

Batch sẽ tiếp tục/ghi report như đã hoàn tất. Chỉ chuyển lỗi thuộc về một input thành `FileResult`; cancellation chung phải giữ semantics toàn operation.

### Gọi `Release` ngoài `finally`

Một exception trước `Release` làm mất permit. Đặt vùng sau `WaitAsync` trong `try/finally`. Không gọi `Release` nếu `WaitAsync` chưa thành công.

### Ghi console từ task và khẳng định thứ tự

Timing không phải contract. Thu kết quả, sort theo key nghiệp vụ, rồi in tại một nơi. Nếu cần log realtime, mỗi record phải có timestamp/correlation và consumer không được dựa vào thứ tự hiển thị.

### Dùng event cho công việc bắt buộc phải thành công

Event phù hợp notification trong process; publisher thường không biết subscriber. Lưu report là bước bắt buộc nên gọi `ReportWriter` tường minh, không giấu nó trong event handler.

### Nghĩ record làm array bất biến sâu

`record` tạo value-based equality/cú pháp data carrier, nhưng property array vẫn trỏ mutable object. Clone/immutable collection khi phải bảo vệ ownership qua boundary.

### Dispose processor khi task còn chạy

`SemaphoreSlim` có thể bị dispose lúc operation đang `WaitAsync`/`Release`. Quy ước ownership của project là `using` bao quanh và kết thúc **sau** `await ProcessAsync`.

### Dùng output timing làm test chính xác

I/O và scheduler dao động. Test invariant như số file, tổng tiền, exit code và thứ tự sort; benchmark hiệu năng phải warm-up, chạy Release, lặp nhiều lần và báo phân phối như bài 18.

## 7. Khi nào KHÔNG dùng

Không dùng event cho lưu report bắt buộc. Không tạo một triệu task rồi gọi semaphore là giới hạn memory. Không dispose processor trước khi await tất cả work sở hữu.

## 8. Production notes & scale check

Gate JSON/null/missing/overflow, pre-cancel, validation trước schedule, handler/validator lỗi, permit reuse, report cũ giữ khi cancel và cleanup sau move lỗi. Chưa chứng minh crash durability hoặc concurrent writers; hai path cùng FileName có tie sort chưa có thứ tự phụ.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Thêm lỗi JSON cú pháp

Tạo file thứ tư chứa JSON bị cắt giữa chừng. Batch phải có `TotalFiles = 4`, không crash và giữ kết quả của ba file cũ.

**Gợi ý:** dùng `File.WriteAllTextAsync` cho riêng file này; không serialize một object hợp lệ. Không assert toàn bộ message của `JsonException` vì có thể đổi theo runtime.

### Bài 2 — Nhận `maxConcurrency` từ command line

Hỗ trợ `dotnet run -- demo 4`; từ chối `0`, số âm và chuỗi không phải số bằng exit code `2`.

**Gợi ý:** dùng `int.TryParse`, guard range và chỉ tạo `OrderBatchProcessor` sau validation.

### Bài 3 — Hủy có thể kiểm chứng

Thêm một `Func<CancellationToken, Task>` delay hook vào processor để test timeout mà không phụ thuộc file lớn. Production truyền hook hoàn tất ngay; test/demo timeout truyền `Task.Delay`.

**Gợi ý:** inject delegate qua constructor; await hook sau khi vào semaphore và truyền token. Không dùng `Thread.Sleep`.

### Bài 4 — Bảo vệ deep immutability của báo cáo

Ngăn caller sửa `BatchReport.Files` sau khi report được tạo.

**Gợi ý:** cân nhắc clone ở constructor và trả read-only wrapper/snapshot. Phân biệt wrapper chỉ đọc với từng `FileResult` immutable.

### Bài 5 — Viết integration test ở mức process

Tạo test chạy project trong thư mục tạm, kiểm tra exit code `1`, `report.json`, `Succeeded = 2` và `GrandTotal = 3650000`.

**Gợi ý:** bài này chỉ lập tiêu chí và thử thủ công; xUnit/process integration test chính thức nằm ở module 14. Không dùng thư mục source làm fixture có thể ghi đè.

## 10. Bài tập tích hợp liên module — Judgment

So với candidate+Save Module04, điểm commit file và memory khác nhau ở đâu? Cho100file và1triệufile, chọn thay đổi tối thiểu theo handle/memory/latency evidence.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Release ghép với acquire nào?
2. Lỗi nào phải đi lên toàn batch?
3. Chi phí O(n) còn ở đâu dù maxConcurrency2?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành bài khi có thể tự trả lời:

- [ ] Tôi giải thích được vì sao project dùng async I/O nhưng không gọi `Task.Run`.
- [ ] Tôi phân biệt completion order với presentation order.
- [ ] Tôi chỉ ra permit được lấy/trả ở đâu và vì sao `Release` nằm trong `finally`.
- [ ] Tôi truyền được một token từ `Main` xuống mọi API cần hủy.
- [ ] Tôi phân loại được lỗi nào thành `FileResult`, lỗi nào phải đi lên boundary.
- [ ] Tôi giải thích được closure nào chứa `observedEvents` và vì sao dùng `Interlocked`.
- [ ] Tôi chỉ ra từng tài nguyên cần `using`/`await using` và object nào chỉ do GC quản lý memory.
- [ ] Tôi giải thích được giới hạn của record shallow immutability và file-replace pattern.
- [ ] Tôi build/run được project trên `net9.0`, nhận đúng output và exit code.
- [ ] Tôi không kéo LINQ, EF Core hoặc framework web vào khi chưa có nhu cầu/prerequisite.

**Bài prerequisite trực tiếp:** [Bài 18 — Đo lường và tối ưu hiệu năng](./18-do-luong-va-toi-uu-hieu-nang.md)

**Ôn lại project nền:** [Module 04, bài 16 — Dự án console C# quản lý công việc](../04-csharp-co-ban/16-du-an-console-csharp-quan-ly-cong-viec.md)

**Bài tiếp theo theo lộ trình:** [Module 06, bài 1 — Mô hình hóa đối tượng](../06-oop-va-thiet-ke/01-mo-hinh-hoa-doi-tuong.md)

**Checkpoint cụm:** [Failure Lab](./failure-labs/04-cancel.md) · [Review](./reviews/review-04.md).

**Trước Module06:** [PR Review](./pr-review-labs/01-batch.md) · [C# Foundation](./career-checkpoint/index.md).
