# `Span<T>`, `Memory<T>` và lập trình hiệu năng

## 1. Mục tiêu

Sau bài này, bạn có thể:

- parse một vùng dữ liệu bằng `ReadOnlySpan<T>` mà không tạo substring cho từng field;
- dùng slice như một view có `start/length`, không hiểu nhầm là bản copy;
- dùng `Span<T>` để sửa trực tiếp vùng nhớ phía sau;
- phân biệt array, `stackalloc`, `Span<T>`, `ReadOnlySpan<T>` và `Memory<T>`;
- giải thích vì sao `Span<T>` là `ref struct` và không được escape lifetime;
- chọn `Memory<T>` khi dữ liệu phải sống qua `await` hoặc được giữ trong object;
- nhận ra allocation vẫn còn ở boundary dù parsing dùng span;
- chỉ áp dụng tối ưu sau khi có phép đo và yêu cầu hiệu năng rõ ràng.

## 2. Bài toán mở đầu

Gateway nhận hàng triệu dòng cảm biến dạng:

```text
sensor-7,23.50,24.25,25.00,OK
```

Cách dễ viết là `Split(',')`, nhưng mỗi field text có thể trở thành một string mới. Trong hot path, số allocation này làm tăng áp lực GC. Ta cần:

- đọc năm field mà không tạo substring;
- parse ba mẫu số trực tiếp từ text span;
- dùng buffer nhỏ trên stack để hiệu chỉnh tại chỗ;
- chỉ tạo `string` cho sensor ID ở ranh giới cần giữ lâu;
- truyền dữ liệu qua một điểm `await` bằng `ReadOnlyMemory<char>`, không giữ `Span<char>` sai lifetime.

Đây là bài toán giảm allocation đã biết trước, không phải lời khuyên thay mọi `string` bằng span.

## 3. Lời giải bằng code

Tạo project:

```bash
dotnet new console --name SpanSensorParser --framework net9.0 --use-program-main
cd SpanSensorParser
```

Thay `SpanSensorParser.csproj` bằng:

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
using System.Globalization;

namespace SpanSensorParser;

internal static class Program
{
    private static async Task Main()
    {
        const string input = "sensor-7,23.50,24.25,25.00,OK";

        if (!TryParseReading(input.AsSpan(), out ReadingView reading))
        {
            Console.WriteLine("Invalid sensor line.");
            return;
        }

        // Ba double nằm trong buffer thuộc stack frame của Main.
        Span<double> samples = stackalloc double[3];
        samples[0] = reading.Sample1;
        samples[1] = reading.Sample2;
        samples[2] = reading.Sample3;

        ClampInPlace(samples, minimum: 0.0, maximum: 100.0);
        double average = Average(samples);

        // Đây là allocation có chủ đích tại persistence boundary.
        string sensorId = reading.SensorId.ToString();

        Console.WriteLine($"Sensor: {sensorId}");
        Console.WriteLine($"Status: {reading.Status.ToString()}");
        Console.WriteLine(FormattableString.Invariant($"Average: {average:F2}"));
        Console.WriteLine(FormattableString.Invariant(
            $"Adjusted samples: {samples[0]:F2}, {samples[1]:F2}, {samples[2]:F2}"));

        // Memory<T> là normal struct nên có thể đi qua await.
        await ReportLengthAfterYieldAsync(input.AsMemory());
    }

    private static bool TryParseReading(
        ReadOnlySpan<char> input,
        out ReadingView reading)
    {
        Span<int> separators = stackalloc int[4];
        if (!TryFindSeparators(input, separators))
        {
            reading = default;
            return false;
        }

        ReadOnlySpan<char> sensorId = input[..separators[0]];
        ReadOnlySpan<char> sample1Text =
            input[(separators[0] + 1)..separators[1]];
        ReadOnlySpan<char> sample2Text =
            input[(separators[1] + 1)..separators[2]];
        ReadOnlySpan<char> sample3Text =
            input[(separators[2] + 1)..separators[3]];
        ReadOnlySpan<char> status = input[(separators[3] + 1)..];

        if (sensorId.IsEmpty
            || !status.SequenceEqual("OK".AsSpan())
            || !TryParseDouble(sample1Text, out double sample1)
            || !TryParseDouble(sample2Text, out double sample2)
            || !TryParseDouble(sample3Text, out double sample3))
        {
            reading = default;
            return false;
        }

        reading = new ReadingView(
            input[..separators[0]],
            sample1,
            sample2,
            sample3,
            input[(separators[3] + 1)..]);
        return true;
    }

    private static bool TryFindSeparators(
        ReadOnlySpan<char> input,
        Span<int> separators)
    {
        int searchStart = 0;
        for (int index = 0; index < separators.Length; index++)
        {
            int relativeIndex = input[searchStart..].IndexOf(',');
            if (relativeIndex < 0)
            {
                return false;
            }

            separators[index] = searchStart + relativeIndex;
            searchStart = separators[index] + 1;
        }

        // Đúng bốn separator: phần status không được chứa separator thứ năm.
        return input[searchStart..].IndexOf(',') < 0;
    }

    private static bool TryParseDouble(
        ReadOnlySpan<char> text,
        out double value)
    {
        return double.TryParse(
            text,
            NumberStyles.Float,
            CultureInfo.InvariantCulture,
            out value);
    }

    private static void ClampInPlace(
        Span<double> values,
        double minimum,
        double maximum)
    {
        for (int index = 0; index < values.Length; index++)
        {
            values[index] = Math.Clamp(values[index], minimum, maximum);
        }
    }

    private static double Average(ReadOnlySpan<double> values)
    {
        if (values.IsEmpty)
        {
            throw new ArgumentException("At least one sample is required.");
        }

        double total = 0.0;
        foreach (double value in values)
        {
            total += value;
        }

        return total / values.Length;
    }

    private static async Task ReportLengthAfterYieldAsync(
        ReadOnlyMemory<char> input)
    {
        await Task.Yield();
        Console.WriteLine($"Memory length after await: {input.Length}");
    }
}

internal readonly ref struct ReadingView
{
    public ReadingView(
        ReadOnlySpan<char> sensorId,
        double sample1,
        double sample2,
        double sample3,
        ReadOnlySpan<char> status)
    {
        SensorId = sensorId;
        Sample1 = sample1;
        Sample2 = sample2;
        Sample3 = sample3;
        Status = status;
    }

    public ReadOnlySpan<char> SensorId { get; }

    public double Sample1 { get; }

    public double Sample2 { get; }

    public double Sample3 { get; }

    public ReadOnlySpan<char> Status { get; }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Output:

```text
Sensor: sensor-7
Status: OK
Average: 24.25
Adjusted samples: 23.50, 24.25, 25.00
Memory length after await: 29
```

## 4. Giải thích cơ chế

### 4.1. Slice là view, không phải substring

`input.AsSpan()` tạo một `ReadOnlySpan<char>` nhìn vào dữ liệu ký tự của string. `remaining[..separatorIndex]` tạo span header mới với vùng bắt đầu và độ dài khác; nó không copy các ký tự thành string mới.

Mô hình logic trong lúc parse:

```text
MANAGED HEAP
H1 string "sensor-7,23.50,24.25,25.00,OK"
index:    0......7 8 9...13 14 15..19 20 21..25 26 27.28
field:    sensor-7 , 23.50  ,  24.25  ,  25.00  ,   OK
             ^                ^
             |                |
SensorId span|                sample2Text span

STACK / REGISTERS của TryParseReading
input       = managed byref vào H1 + length 29
sensorId    = managed byref vào H1[0]  + length 8
sample2Text = managed byref vào H1[15] + length 5
```

Đây là sơ đồ semantics, không phải địa chỉ số cố định. GC có thể di chuyển string; runtime theo dõi managed byref để reference vẫn hợp lệ. Không lưu raw pointer lấy từ span sau khi lifetime kết thúc.

### 4.2. Lưu offset rồi tạo view trực tiếp từ input

`TryFindSeparators` ghi bốn vị trí dấu phẩy vào `Span<int>` do caller cấp. Sau đó `TryParseReading` tạo mọi field bằng range trực tiếp trên `input`. Không ký tự nào bị sửa hoặc copy.

Việc tạo `ReadingView` từ các slice trực tiếp của `input` còn cho compiler thấy lifetime của hai field span không dài hơn input từ caller. Một helper tùy ý trả span qua `out` có thể bị từ chối nếu compiler không chứng minh được span đó không trỏ vào local stack của helper. Không dùng cast hay `unsafe` để lách kiểm tra escape; hãy thiết kế data flow để lifetime rõ ràng.

### 4.3. `stackalloc` và mutation qua `Span<T>`

```csharp
Span<double> samples = stackalloc double[3];
```

xin một vùng liên tiếp đủ ba `double` trong stack frame hiện tại và tạo span nhìn vào vùng đó. `ClampInPlace(samples, ...)` nhận một span header by value; header được copy nhưng cả hai header vẫn nhìn cùng buffer, nên gán `values[index]` đổi buffer mà `Main` đọc.

```text
Main frame
samples header ----┐
                   v
stackalloc buffer [23.50][24.25][25.00]
                   ^
values header -----┘   (header copy, cùng backing storage)
```

Không `stackalloc` kích thước lớn hoặc kích thước không giới hạn từ input trong loop. Stack nhỏ hơn heap và recursion/stack allocation quá mức có thể gây `StackOverflowException`.

### 4.4. Vì sao `Span<T>` là `ref struct`?

Span có thể trỏ vào stack memory hoặc interior của managed object. Nếu span thoát ra object heap và sống lâu hơn buffer stack, reference sẽ bị treo. Compiler áp dụng escape analysis/lifetime rule bằng cách biến span thành `ref struct`:

- không box thành `object` hoặc interface;
- không làm field của class hay non-`ref struct`;
- không capture trong lambda/local function tạo closure;
- không được sống qua `await` hoặc `yield`.

### 4.5. `Memory<T>` khác `Span<T>` ở đâu?

`ReadOnlyMemory<char>` là normal struct, có thể nằm trong async state machine hoặc field. Với `input.AsMemory()`, nó giữ reference tới string cùng offset/length, nhờ vậy backing string còn reachable qua `await`.

```text
async state-machine object (managed heap)
└── input: ReadOnlyMemory<char>
       └── reference ----> H1 string

await tạm dừng / tiếp tục: state machine và H1 vẫn reachable
```

Sau `await`, code đồng bộ có thể lấy `input.Span`, dùng xong trước suspension point tiếp theo. `Memory<T>` không có nghĩa dữ liệu luôn được copy lên heap; nó là descriptor storable cho backing memory có lifetime phù hợp.

### 4.6. Allocation nào đã tránh, allocation nào vẫn còn?

Parsing không gọi `Split` hay `Substring`; `double.TryParse(ReadOnlySpan<char>, ...)` đọc trực tiếp slice. Tuy nhiên chương trình vẫn có allocation:

- string input là object có sẵn;
- `sensorId.ToString()` cố ý tạo string cần giữ;
- async state machine có thể allocate tùy đường thực thi;
- format/console output có allocation và I/O.

Không được quảng cáo “zero allocation” cho toàn chương trình chỉ vì có span. Đo đúng đoạn cần tối ưu bằng công cụ của bài 18.

### Đào sâu (có thể quay lại sau)

C# mới cho phép một số ref-struct local trong async/iterator nếu compiler chứng minh chúng không vượt qua suspension point. Quy tắc an toàn vẫn là: kết thúc mọi thao tác span trước `await`; dùng `Memory<T>` nếu dữ liệu cần vượt qua điểm tạm dừng.

## 5. Kiến thức nền

### Bảng chọn type

| Type | Ghi được? | Có thể giữ trong class/qua `await`? | Backing storage thường gặp |
|---|---:|---:|---|
| `T[]` | có | có | array object trên managed heap |
| `Span<T>` | có | không nếu span sống qua suspension/escape | array, stackalloc, unmanaged memory |
| `ReadOnlySpan<T>` | không qua API span | không nếu span sống qua suspension/escape | string, array, memory khác |
| `Memory<T>` | có | có | thường array hoặc memory manager |
| `ReadOnlyMemory<T>` | không qua API memory | có | string, array hoặc memory manager |

Readonly view ngăn ghi qua view đó, không chứng minh backing storage bất biến. `ReadOnlySpan<T>` nhìn vào array vẫn có thể quan sát thay đổi do code khác ghi array.

### Range check và slice

`span[index]` kiểm tra biên. `span[start..end]` cũng kiểm tra range rồi tạo view. JIT có thể loại một số bounds check khi chứng minh loop an toàn; không dùng `unsafe` chỉ để phỏng đoán nhanh hơn.

### API nhận span

Ưu tiên overload `ReadOnlySpan<T>` cho input chỉ đọc và `Span<T>` cho output/mutation đồng bộ. Nếu caller thường có string/array, overload span giúp caller truyền slice không copy. API public vẫn có thể cần overload string/array để usability tốt.

### `Memory<T>` và ownership

Memory chỉ mô tả vùng; nó không tự định nghĩa ai trả buffer về pool. Khi dùng `ArrayPool<T>`, `IMemoryOwner<T>` hoặc unmanaged memory, phải có ownership/lifetime contract rõ và `Dispose` đúng nơi. Không trả buffer về pool khi consumer còn giữ memory view.

## 6. Lỗi thường gặp

### Trả span trỏ vào `stackalloc` local

Compiler từ chối vì buffer chết khi method return. Hãy để caller cấp buffer hoặc trả object sở hữu dữ liệu.

### Giữ span qua `await`

Async method có thể tiếp tục trên một frame khác sau suspension. Dùng `Memory<T>` qua `await`, rồi lấy `.Span` trong đoạn đồng bộ ngắn.

### Nghĩ slice là bản copy độc lập

Hai writable span có thể alias cùng array. Ghi qua span này có thể thấy qua span kia; vẽ offset/length và backing storage trước mutation phức tạp.

### Gọi `.ToString()` trên mọi field

Điều này tạo lại allocation mà parsing span muốn tránh. Chỉ materialize string khi API downstream cần sở hữu text lâu hơn.

### `stackalloc` theo kích thước input chưa giới hạn

Input lớn có thể làm cạn stack. Đặt ngưỡng nhỏ; trên ngưỡng đó dùng array/pool với ownership rõ.

### Tối ưu mà không đo

Span làm API và lifetime phức tạp hơn. Nếu đoạn code không phải hotspot hoặc allocation không đáng kể, phiên bản `Split` có thể dễ bảo trì hơn. Đo baseline trước và sau.

## 7. Bài tập

### Bài 1 — Parse ba số nguyên

Parse `"10|20|30"` bằng `ReadOnlySpan<char>`, không dùng `Split` hoặc `Substring`.

**Gợi ý:** tổng quát hóa `TryTakeField` để nhận separator; kiểm tra thừa/thiếu field.

### Bài 2 — Sửa một slice của array

Tạo `int[]`, lấy `Span<int>` của ba phần tử giữa rồi tăng chúng. Vẽ array trước/sau.

**Gợi ý:** chứng minh slice không copy bằng cách in array gốc.

### Bài 3 — Buffer do caller sở hữu

Viết `bool TryNormalize(ReadOnlySpan<double> input, Span<double> destination)` và từ chối khi destination quá ngắn.

**Gợi ý:** không trả span tạo từ `stackalloc` bên trong method; trả số phần tử đã ghi nếu cần.

### Bài 4 — Qua một điểm `await`

Viết method nhận `ReadOnlyMemory<byte>`, `await Task.Delay(10)`, sau đó tính checksum trong một helper đồng bộ nhận `ReadOnlySpan<byte>`.

**Gợi ý:** không khai báo span trước `await`; gọi helper bằng `memory.Span` sau khi tiếp tục.

### Bài 5 — Đo allocation

So sánh parser dùng `Split` với parser span trên cùng dữ liệu và kiểm tra kết quả bằng nhau.

**Gợi ý:** warm up, chạy Release, đo nhiều lần; dùng kỹ thuật ở bài 18 và không tính `Console.WriteLine` trong vùng đo.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi vẽ được span header và backing storage riêng biệt.
- [ ] Tôi biết slice tạo view, không tự copy dữ liệu.
- [ ] Tôi dùng `Span<T>` cho mutation đồng bộ và `ReadOnlySpan<T>` cho input.
- [ ] Tôi không để span của stack memory escape hoặc sống qua `await`.
- [ ] Tôi chọn `Memory<T>` khi descriptor phải được lưu hoặc đi qua async suspension.
- [ ] Tôi phân biệt giảm allocation cục bộ với tuyên bố zero-allocation toàn chương trình.
- [ ] Tôi chỉ dùng span sau khi đo và xác nhận hotspot.

Điều hướng:

- Prerequisite: [Reflection, attribute và `dynamic`](./13-reflection-attribute-va-dynamic.md)
- Bài tiếp theo: [Covariance và contravariance](./15-covariance-va-contravariance.md)
