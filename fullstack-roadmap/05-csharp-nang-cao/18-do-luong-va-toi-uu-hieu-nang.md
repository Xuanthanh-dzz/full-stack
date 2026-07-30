# Đo lường và tối ưu hiệu năng

## 1. Mục tiêu

Sau bài này, bạn có thể:

- viết baseline và candidate tạo cùng kết quả trước khi so hiệu năng;
- chạy benchmark thủ công ở `Release` và ngoài debugger;
- warm up để giảm ảnh hưởng JIT/tiered compilation ban đầu;
- đo elapsed time bằng `Stopwatch` và allocation bằng `GC.GetAllocatedBytesForCurrentThread`;
- chạy nhiều sample, đảo thứ tự và dùng median thay vì tin một lần đo;
- nhận diện noise từ OS, CPU, GC, background work và môi trường;
- phân biệt microbenchmark với end-to-end production profiling;
- tối ưu theo hotspot đã đo, rồi kiểm tra correctness và regression.

## 2. Bài toán mở đầu

Một endpoint tạo chuỗi CSV `1,2,3,...` nhiều lần. Phiên bản đầu nối string trong loop; review đề xuất `StringBuilder`. Không được kết luận chỉ vì “StringBuilder luôn nhanh hơn”. Ta cần trả lời bằng dữ liệu:

- hai phiên bản có tạo **đúng cùng output** không;
- thời gian điển hình trên máy đo là bao nhiêu;
- mỗi operation cấp phát bao nhiêu managed bytes trên thread hiện tại;
- kết luận còn bị giới hạn bởi noise và workload giả lập nào.

Sample dưới đây là harness học tập không package ngoài. Với quyết định production nghiêm túc, dùng profiler và benchmark framework chuyên dụng sau khi đã xác định hotspot.

## 3. Lời giải bằng code

Tạo project:

```bash
dotnet new console --name MeasuredOptimization --framework net9.0 --use-program-main
cd MeasuredOptimization
```

Thay `MeasuredOptimization.csproj` bằng:

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
using System.Diagnostics;
using System.Globalization;
using System.Runtime.InteropServices;
using System.Text;

namespace MeasuredOptimization;

internal static class Program
{
    private const int ItemCount = 300;
    private const int OperationsPerSample = 100;
    private const int SampleCount = 7;

    private static void Main()
    {
        CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;

        Func<int, string> baseline = BuildWithConcatenation;
        Func<int, string> candidate = BuildWithStringBuilder;

        // Correctness là cổng bắt buộc trước benchmark.
        string expected = baseline(ItemCount);
        string actual = candidate(ItemCount);
        if (!string.Equals(expected, actual, StringComparison.Ordinal))
        {
            throw new InvalidOperationException("Implementations produce different output.");
        }

        int warmupChecksum = WarmUp(baseline, candidate);

        // Dọn garbage của setup/warmup một lần, ngoài vùng đo.
        // Không ép GC giữa mọi sample vì đó sẽ là workload khác.
        GC.Collect();
        GC.WaitForPendingFinalizers();
        GC.Collect();

        var baselineSamples = new Measurement[SampleCount];
        var candidateSamples = new Measurement[SampleCount];

        for (int sample = 0; sample < SampleCount; sample++)
        {
            // Đảo thứ tự để giảm bias do method luôn chạy trước/sau.
            if (sample % 2 == 0)
            {
                baselineSamples[sample] = Measure(baseline);
                candidateSamples[sample] = Measure(candidate);
            }
            else
            {
                candidateSamples[sample] = Measure(candidate);
                baselineSamples[sample] = Measure(baseline);
            }
        }

        bool checksumsMatch =
            AllChecksumsMatch(baselineSamples, candidateSamples);

        // Làm kết quả warmup observable mà không đưa nó vào timed region.
        GC.KeepAlive(warmupChecksum);

        Console.WriteLine($"Runtime: {RuntimeInformation.FrameworkDescription}");
        Console.WriteLine(
            $"Stopwatch frequency: {Stopwatch.Frequency:N0} ticks/second");
        Console.WriteLine($"Operations/sample: {OperationsPerSample}");
        Console.WriteLine($"Items/operation: {ItemCount}");
        Console.WriteLine($"Checksums equal: {checksumsMatch}");
        PrintMedian("Concatenation", baselineSamples);
        PrintMedian("StringBuilder", candidateSamples);
    }

    private static string BuildWithConcatenation(int itemCount)
    {
        string result = string.Empty;

        for (int value = 1; value <= itemCount; value++)
        {
            // Mỗi vòng tạo text số và một string kết quả mới; nội dung result
            // cũ phải được copy vào string mới.
            result = string.Concat(
                result,
                value.ToString(CultureInfo.InvariantCulture),
                ",");
        }

        return result;
    }

    private static string BuildWithStringBuilder(int itemCount)
    {
        // Capacity là estimate của workload này, không phải contract tổng quát.
        var builder = new StringBuilder(capacity: itemCount * 4);

        for (int value = 1; value <= itemCount; value++)
        {
            builder.Append(value);
            builder.Append(',');
        }

        return builder.ToString();
    }

    private static int WarmUp(
        Func<int, string> baseline,
        Func<int, string> candidate)
    {
        int checksum = 17;
        for (int iteration = 0; iteration < 30; iteration++)
        {
            checksum = Combine(checksum, ComputeChecksum(baseline(ItemCount)));
            checksum = Combine(checksum, ComputeChecksum(candidate(ItemCount)));
        }

        return checksum;
    }

    private static Measurement Measure(Func<int, string> operation)
    {
        long allocatedBefore = GC.GetAllocatedBytesForCurrentThread();
        long started = Stopwatch.GetTimestamp();

        int checksum = 17;
        for (int operationIndex = 0;
             operationIndex < OperationsPerSample;
             operationIndex++)
        {
            string result = operation(ItemCount);
            checksum = Combine(checksum, ComputeChecksum(result));
        }

        long stopped = Stopwatch.GetTimestamp();
        long allocatedAfter = GC.GetAllocatedBytesForCurrentThread();

        double nanosecondsPerOperation =
            Stopwatch.GetElapsedTime(started, stopped).TotalNanoseconds
            / OperationsPerSample;

        long bytesPerOperation =
            (allocatedAfter - allocatedBefore) / OperationsPerSample;

        return new Measurement(
            nanosecondsPerOperation,
            bytesPerOperation,
            checksum);
    }

    private static int ComputeChecksum(string value)
    {
        int checksum = 17;
        foreach (char character in value)
        {
            checksum = Combine(checksum, character);
        }

        return checksum;
    }

    private static int Combine(int left, int right)
    {
        return unchecked((left * 31) ^ right);
    }

    private static bool AllChecksumsMatch(
        Measurement[] baseline,
        Measurement[] candidate)
    {
        int expected = baseline[0].Checksum;

        for (int index = 0; index < baseline.Length; index++)
        {
            if (baseline[index].Checksum != expected
                || candidate[index].Checksum != expected)
            {
                return false;
            }
        }

        return true;
    }

    private static void PrintMedian(string name, Measurement[] samples)
    {
        var times = new double[samples.Length];
        var allocations = new long[samples.Length];

        for (int index = 0; index < samples.Length; index++)
        {
            times[index] = samples[index].NanosecondsPerOperation;
            allocations[index] = samples[index].BytesPerOperation;
        }

        Array.Sort(times);
        Array.Sort(allocations);
        int middle = samples.Length / 2;

        Console.WriteLine(
            $"{name} median: {times[middle]:N0} ns/op, "
            + $"{allocations[middle]:N0} B/op");
    }
}

internal readonly record struct Measurement(
    double NanosecondsPerOperation,
    long BytesPerOperation,
    int Checksum);
```

Build và chạy đúng cấu hình Release:

```bash
dotnet build --configuration Release
dotnet run --configuration Release --no-build
```

Output có cùng cấu trúc dưới đây; runtime version, timer frequency, thời gian và allocation cụ thể phụ thuộc máy/lần chạy:

```text
Runtime: .NET 9.0.x
Stopwatch frequency: <phụ thuộc hệ điều hành> ticks/second
Operations/sample: 100
Items/operation: 300
Checksums equal: True
Concatenation median: <giá trị đo> ns/op, <giá trị đo> B/op
StringBuilder median: <giá trị đo> ns/op, <giá trị đo> B/op
```

Trên workload này, `StringBuilder` thường cấp phát ít hơn rõ rệt vì không tạo lại toàn bộ prefix string ở mỗi vòng. Không sao chép con số của máy khác thành cam kết production.

## 4. Giải thích cơ chế

### 4.1. Correctness đứng trước tốc độ

Hai implementation được gọi một lần và so sánh `Ordinal` trước vùng benchmark. Checksum trong vùng đo làm result được quan sát và phát hiện sample bất nhất; nó không thay test case đầy đủ.

```text
baseline(input)  ----> output A --┐
                                  +--> equality gate --> benchmark
candidate(input) ----> output B --┘
```

Một candidate nhanh nhưng bỏ ký tự, đổi culture hoặc sai biên không phải tối ưu. Viết unit test cho nhiều input ngoài benchmark.

### 4.2. Vì sao concatenation cấp phát nhiều?

`string` immutable. Với mỗi vòng:

```text
iteration 1: H1 "1,"
iteration 2: H2 "1,2,"       H1 trở thành GC-eligible nếu không còn ref
iteration 3: H3 "1,2,3,"     H2 trở thành GC-eligible
...
```

Mỗi string mới phải chứa cả prefix cũ lẫn phần thêm. `StringBuilder` sở hữu một buffer mutable, append vào buffer và chỉ materialize string kết quả ở cuối. Buffer vẫn có thể tăng và allocate nếu capacity thiếu; nó không phải zero-allocation.

### 4.3. Warmup và tiered compilation

Lần gọi đầu có thể gồm JIT compilation, static initialization và cache lạnh. `WarmUp` gọi cả hai implementation trước khi đo.

.NET còn có tiered compilation/dynamic PGO; 30 lần không bảo đảm mọi tier đã ổn định trên mọi máy.

Không đưa setup, correctness comparison, `Console.WriteLine` hay forced GC vào timed region. Chúng là chi phí khác với operation cần đo.

### 4.4. Time measurement

`Stopwatch.GetTimestamp()` đọc timer đơn điệu độ phân giải cao của platform. `Stopwatch.GetElapsedTime` đổi delta tick sang `TimeSpan`; chia cho operation count tạo `ns/op` trung bình của sample.

Trong harness này, timed region gồm cả `ComputeChecksum`. Đây là consumer chung cần để quan sát toàn bộ output, nên số `ns/op` không phải thời gian riêng của builder. Vì hai bên tạo cùng string, checksum thêm cùng loại công việc; vẫn phải ghi rõ phạm vi đo khi báo kết quả.

Một operation quá ngắn gần timer resolution sẽ nhiễu. Lặp nhiều operation làm sample đủ dài, nhưng lặp cũng phải giống semantics cần đo. Không dùng `DateTime.Now` cho microbenchmark.

### 4.5. Allocation measurement

`GC.GetAllocatedBytesForCurrentThread()` là bộ đếm tích lũy managed bytes được cấp phát bởi thread gọi. Delta quanh loop cho estimate `B/op`:

```text
allocatedAfter - allocatedBefore
-------------------------------- = bytes/operation
          operation count
```

Nó không đo:

- allocation trên thread khác;
- native allocation;
- peak retained memory hoặc object lifetime;
- pause GC trực tiếp;
- chi phí I/O/network.

Allocated bytes khác live bytes: object có thể được cấp phát rồi sớm GC-eligible nhưng vẫn tính vào counter.

### 4.6. Nhiều sample, đảo thứ tự và median

OS scheduling, antivirus, thermal throttling, CPU frequency, GC và process nền tạo outlier. Sample đảo thứ tự baseline/candidate để giảm bias “luôn chạy trước”. Median của bảy sample ít bị một outlier lớn kéo lệch hơn mean.

Median không xóa bias hệ thống. Chạy trên máy ổn định, ghi runtime/OS/CPU/config, lặp ở CI benchmark riêng và xem distribution khi quyết định quan trọng.

### 4.7. Sơ đồ quy trình tối ưu

```text
đo end-to-end / profiler
          |
          v
xác nhận hotspot và metric cần cải thiện
          |
          v
viết baseline + correctness tests
          |
          v
thay đổi nhỏ có giả thuyết
          |
          v
benchmark Release nhiều sample
          |
          +-- không cải thiện / regression --> bỏ hoặc điều chỉnh
          |
          v
kiểm thử tải/end-to-end + theo dõi production
```

Microbenchmark là một bằng chứng cục bộ, không thay profile toàn request.

## 5. Kiến thức nền

### Metric phải gắn với mục tiêu

| Metric | Câu hỏi |
|---|---|
| latency | một operation/request mất bao lâu, đặc biệt percentile cao? |
| throughput | xử lý bao nhiêu operation trong một đơn vị thời gian? |
| allocation rate | tạo bao nhiêu managed bytes, gây áp lực GC thế nào? |
| CPU time | CPU thực dùng cho workload bao nhiêu? |
| memory/working set | process giữ/commit bao nhiêu memory theo thời gian? |
| GC pause/count | collection ảnh hưởng latency ra sao? |

Tối ưu một metric có thể làm metric khác xấu: cache giảm CPU nhưng tăng retained memory; batching tăng throughput nhưng tăng latency từng item.

### Debug và Release

Debug build, debugger attached và diagnostic tooling có thể đổi optimization/timing. Microbenchmark phải chạy Release ngoài debugger. Vẫn nên profile production-like build có symbol để tìm hotspot; “có symbol” không đồng nghĩa Debug.

### Baseline công bằng

- cùng input distribution và culture;
- cùng correctness/output ownership;
- setup ngoài vùng đo hoặc tính vào cả hai nếu production phải trả chi phí đó;
- không cho một bên dùng cache ấm còn bên kia cache lạnh;
- random/order có seed và được ghi lại khi cần tái tạo.

### Statistical humility

Một con số không phải chân lý phổ quát. Báo runtime, hardware, sample count, đơn vị, median/percentile và độ phân tán. Chỉ tuyên bố trong phạm vi workload đã đo.

### Khi dùng công cụ chuyên dụng

Harness nhỏ giúp hiểu cơ chế. Benchmark production nên dùng framework như BenchmarkDotNet để quản lý process isolation, warmup, iteration và diagnoser; profiler như `dotnet-trace`, `dotnet-counters` hoặc công cụ IDE giúp tìm hotspot thật. Chọn công cụ theo câu hỏi, không benchmark mọi method trước khi profile.

### Đào sâu (có thể quay lại sau)

Nhiều sample giúp nhìn biến động, benchmark framework chuyên dụng có quy trình warmup/iteration tốt hơn.

## 6. Lỗi thường gặp

### Đo Debug hoặc đang gắn debugger

Kết quả không đại diện optimized code. Build/run Release ngoài debugger và ghi rõ runtime/configuration.

### Chỉ chạy một lần

Một GC pause hoặc context switch có thể quyết định kết quả. Warm up, nhiều sample, xem distribution và tái chạy.

### Đo cả `Console.WriteLine`

Console I/O thường lấn át operation. Tính result/checksum trong vùng đo, chỉ in summary sau đó.

### Không kiểm tra output

JIT hoặc code candidate có thể bỏ công việc do result không dùng; tệ hơn, candidate sai nhưng trông nhanh. Consume result và có correctness test riêng.

### Gọi `GC.Collect()` rồi coi đó là production

Forced collection thay đổi workload. Sample chỉ dùng sau warmup để giảm rác setup, không ép giữa từng sample. Ứng dụng production hiếm khi nên tự gọi GC.

### Dùng allocation thread-local để kết luận toàn process

Async/parallel work có thể allocate trên thread khác. Dùng profiler/counter process-level cho workload đa thread.

### Tối ưu theo cảm tính

Code phức tạp hơn có chi phí bảo trì và bug. Nếu metric không cải thiện đáng kể ở hotspot, giữ phiên bản rõ hơn.

### Chỉ microbenchmark mà bỏ end-to-end

Database, serialization, lock, network hoặc queue có thể là bottleneck thật. Sau microbenchmark, chạy workload tích hợp và theo dõi production metric.

## 7. Bài tập

### Bài 1 — Thêm min/max sample

In median, minimum và maximum `ns/op` cho mỗi implementation.

**Gợi ý:** copy số đo ra array rồi sort ngoài timed region; không giấu outlier, giải thích nó.

### Bài 2 — So sánh `Split` và span parser

Dùng input của bài 14, so correctness, time và `B/op` của hai parser.

**Gợi ý:** không materialize string field trong phiên bản span nếu contract không cần; nếu cần output string, cả hai phải trả cùng ownership.

### Bài 3 — Khảo sát capacity

Chạy `StringBuilder` với capacity quá nhỏ, estimate vừa đủ và quá lớn.

**Gợi ý:** đo cả allocation lẫn retained memory trade-off; capacity lớn quá mức không miễn phí.

### Bài 4 — Nhiễu có chủ đích

Chạy một background task tiêu thụ CPU rồi so distribution trước/sau.

**Gợi ý:** không chỉ so median; ghi min/max và môi trường để thấy scheduler noise.

### Bài 5 — Tìm hotspot thật

Profile một console app xử lý nhiều file hoặc JSON, xác định top CPU/allocation trước khi sửa một method.

**Gợi ý:** ghi baseline end-to-end, một screenshot/trace evidence, giả thuyết, thay đổi và kết quả sau sửa.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi kiểm tra output giống nhau trước khi so tốc độ.
- [ ] Tôi chạy Release ngoài debugger và warm up cả hai phía.
- [ ] Tôi đo nhiều sample, đảo thứ tự và dùng thống kê có giải thích.
- [ ] Tôi hiểu `ns/op` và `B/op` của harness đang đo gì và bỏ sót gì.
- [ ] Tôi không đưa setup/console I/O ngoài ý muốn vào timed region.
- [ ] Tôi phân biệt microbenchmark, profiler, load test và production telemetry.
- [ ] Tôi chỉ giữ tối ưu khi evidence đủ mạnh và correctness không regression.

Điều hướng:

- Prerequisite: [Serialization với `System.Text.Json`](./17-serialization-system-text-json.md)
- Bài tiếp theo: [Dự án xử lý dữ liệu bất đồng bộ](./19-du-an-xu-ly-du-lieu-bat-dong-bo.md)
