# Cancellation, timeout và exception bất đồng bộ

## 1. Mục tiêu

Sau bài này, bạn có thể:

- truyền `CancellationToken` xuyên suốt call chain và kiểm tra token tại điểm an toàn;
- phân biệt yêu cầu cancel với việc operation thực sự dừng;
- dùng `ThrowIfCancellationRequested` để task chuyển sang trạng thái Canceled đúng semantics;
- phân biệt caller cancellation, timeout policy và lỗi thật;
- hiểu `Task.WaitAsync(timeout)` chỉ giới hạn thời gian chờ, không tự dừng operation gốc;
- bắt exception tại `await` và giữ causal information;
- quan sát mọi exception của `Task.WhenAll` thay vì chỉ exception được ném từ `await`;
- quản lý lifetime của `CancellationTokenSource`, linked token và registration.

## 2. Bài toán mở đầu

Một tác vụ sinh báo cáo có năm trang. Người dùng bấm hủy sau trang thứ hai. Ở luồng khác, API gateway chỉ muốn chờ một dependency đến deadline; quá deadline, request phải trả về nhưng dependency có thể vẫn đang chạy. Cuối cùng, hai tác vụ nền cùng thất bại và ta cần chẩn đoán đủ cả hai nguyên nhân.

Ba tình huống này không cùng nghĩa:

- **cancellation** là tín hiệu hợp tác từ caller;
- **timeout** là policy giới hạn thời gian của bên chờ;
- **fault** là operation thất bại vì exception.

Nếu bắt tất cả bằng `catch (Exception)` rồi ghi “error”, hệ thống sẽ báo hủy hợp lệ như sự cố và có thể bỏ mất exception thứ hai.

## 3. Lời giải bằng code

Tạo project:

```bash
mkdir AsyncControlDemo
cd AsyncControlDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `AsyncControlDemo.csproj` bằng:

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

Thay toàn bộ `Program.cs`:

`CancellationTokenSource` là object phát tín hiệu hủy bằng `Cancel()`; `CancellationToken` là value được copy và truyền cho operation để quan sát tín hiệu đó. `ThrowIfCancellationRequested()` biến tín hiệu đã được yêu cầu thành `OperationCanceledException`. `Task.WaitAsync(TimeSpan)` tạo một lượt chờ có deadline nhưng không sửa task gốc. Các API này xuất hiện trực tiếp trong sample dưới đây.

Sample còn dùng `using var cancellationSource = ...`: đây là **using declaration**, bảo đảm gọi `Dispose()` khi method kết thúc vì source sở hữu timer/registration nội bộ có thể cần dọn. `Dispose` không đồng nghĩa `Cancel`; code vẫn phải gọi `Cancel()` để phát tín hiệu. Cơ chế `IDisposable`, `using` và ownership được học đầy đủ ở [bài 12](./12-idisposable-gc-va-quan-ly-tai-nguyen.md); đoạn này giới thiệu tối thiểu để không dùng cú pháp mới mà không giải thích.

```csharp
using System.Collections.Generic;

namespace AsyncControlDemo;

public sealed class ReportGenerator
{
    public async Task<IReadOnlyList<string>> GenerateAsync(
        int pageCount,
        Action<int> afterPage,
        CancellationToken cancellationToken)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(pageCount);
        ArgumentNullException.ThrowIfNull(afterPage);

        var pages = new List<string>(pageCount);

        for (int pageNumber = 1; pageNumber <= pageCount; pageNumber++)
        {
            // Chỉ dừng trước một unit of work, khi state vẫn nhất quán.
            cancellationToken.ThrowIfCancellationRequested();

            // Tạo async boundary deterministic, không dùng network/timer.
            await Task.Yield();

            pages.Add($"Page {pageNumber}");
            afterPage(pageNumber);
        }

        return pages.AsReadOnly();
    }
}

internal static class Program
{
    private static async Task Main()
    {
        await DemonstrateCancellationAsync();
        await DemonstrateTimeoutAsync();
        await DemonstrateMultipleFaultsAsync();
    }

    private static async Task DemonstrateCancellationAsync()
    {
        var generator = new ReportGenerator();
        using var cancellationSource = new CancellationTokenSource();

        try
        {
            await generator.GenerateAsync(
                pageCount: 5,
                afterPage: pageNumber =>
                {
                    Console.WriteLine($"Generated page {pageNumber}");
                    if (pageNumber == 2)
                    {
                        cancellationSource.Cancel();
                    }
                },
                cancellationSource.Token);
        }
        catch (OperationCanceledException exception)
            when (exception.CancellationToken == cancellationSource.Token)
        {
            Console.WriteLine("Canceled by caller after page 2.");
        }
    }

    private static async Task DemonstrateTimeoutAsync()
    {
        var producer = new TaskCompletionSource<string>(
            TaskCreationOptions.RunContinuationsAsynchronously);

        try
        {
            // Zero chỉ dùng để demo deterministic: Task gốc đang incomplete nên timeout ngay.
            await producer.Task.WaitAsync(TimeSpan.Zero);
        }
        catch (TimeoutException)
        {
            Console.WriteLine("Caller stopped waiting at its timeout.");
        }

        Console.WriteLine($"Underlying operation completed: {producer.Task.IsCompleted}");
    }

    private static async Task DemonstrateMultipleFaultsAsync()
    {
        Task first = FailAsync("JOB-A");
        Task second = FailAsync("JOB-B");
        Task combined = Task.WhenAll(first, second);

        try
        {
            await combined;
        }
        catch (InvalidOperationException exception)
        {
            Console.WriteLine($"Caught from await: {exception.GetType().Name}");
            Console.WriteLine(
                $"Faults recorded by WhenAll: {combined.Exception?.InnerExceptions.Count}");
        }
    }

    private static async Task FailAsync(string jobId)
    {
        await Task.Yield();
        throw new InvalidOperationException($"{jobId} failed.");
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Output:

```text
Generated page 1
Generated page 2
Canceled by caller after page 2.
Caller stopped waiting at its timeout.
Underlying operation completed: False
Caught from await: InvalidOperationException
Faults recorded by WhenAll: 2
```

Demo timeout dùng `TimeSpan.Zero` trên task chắc chắn chưa complete, nên không phụ thuộc tốc độ máy. Trong code thật, timeout là khoảng dương lấy từ requirement/configuration.

## 4. Giải thích cơ chế

### Cancellation là cooperative protocol

`CancellationTokenSource` là object mutable giữ trạng thái cancel. Property `Token` trả một value type nhỏ; các bản copy token cùng quan sát trạng thái của source liên quan.

```text
cancellationSource object
┌──────────────────────────────────────┐
│ IsCancellationRequested: false/true  │
│ registrations ...                   │
└──────────────────────────────────────┘
       ^                 ^
       │                 │
token copy ở Main        token copy trong async state machine
```

`Cancel()` chỉ đổi trạng thái và chạy callback đã đăng ký. Nó không abort thread, không tự rollback và không buộc code dừng tại một instruction tùy ý. `GenerateAsync` hợp tác bằng cách kiểm tra token trước mỗi trang. `ThrowIfCancellationRequested()` ném `OperationCanceledException` gắn đúng token; async method hoàn thành ở trạng thái Canceled.

Điểm kiểm tra phải bảo toàn invariant. Không nên kiểm tra giữa hai bước mà bước sau bắt buộc để hoàn tất một transaction cục bộ. Sau “point of no cancellation”, hãy hoàn tất commit hoặc có compensation rõ ràng.

### Timeout của bên chờ không dừng task gốc

`producer.Task.WaitAsync(TimeSpan.Zero)` tạo một task chờ kết quả hoặc timeout. Vì task gốc chưa complete, task chờ ném `TimeoutException`; dòng sau vẫn in `producer.Task.IsCompleted == false`.

```text
underlying Task U: Pending ───────────────────────────────>
                         \
waiting Task W:           └─ timeout -> Faulted(TimeoutException)

U không tự chuyển sang Canceled.
```

Nếu operation hỗ trợ token và requirement là dừng cả operation, caller có thể tạo `CancellationTokenSource`, gọi `CancelAfter(timeout)` rồi truyền token xuống. Operation vẫn phải quan sát token. `WaitAsync(timeout)` phù hợp khi chỉ ownership thời gian chờ; `CancelAfter` phù hợp khi caller cũng sở hữu quyền yêu cầu operation dừng.

### Exception của async method nằm trong Task

`FailAsync` ném sau `await`, nên task chuyển sang Faulted. `await combined` quan sát task và ném một exception để `try/catch` hoạt động tự nhiên. Returned task giữ exception/stack trace; dùng `throw;` khi rethrow như bài exception cơ bản.

Khi nhiều task fault, `Task.WhenAll` hoàn thành Faulted và property `combined.Exception` là `AggregateException` chứa các lỗi. `await` không cung cấp lần lượt mọi inner exception qua nhiều catch; nếu cần chẩn đoán đủ batch, sau khi catch hãy inspect task tổng như sample. Không dựa vào message hoặc “exception nào được chọn để ném” làm business contract.

## 5. Kiến thức nền

### Truyền token xuyên call chain

Method async có operation hủy được thường nhận token cuối cùng và đặt default chỉ ở public boundary khi optional thực sự hợp lý:

```csharp
public Task SaveAsync(Order order, CancellationToken cancellationToken)
{
    return _repository.SaveAsync(order, cancellationToken);
}
```

Đừng nhận token rồi quên truyền xuống API I/O. Đừng tạo `new CancellationTokenSource()` trong mỗi tầng và làm mất quyền cancel của caller.

### Linked token

Một operation có thể dừng khi request bị hủy **hoặc** application shutdown:

```csharp
using CancellationTokenSource linked =
    CancellationTokenSource.CreateLinkedTokenSource(requestToken, shutdownToken);

await ProcessAsync(linked.Token);
```

Dispose linked source để tháo registration khỏi source cha. `Dispose()` không có nghĩa là `Cancel()`; nếu cần signal cancel, gọi `Cancel` theo lifecycle rồi dispose.

### Timeout policy

```csharp
using var timeoutSource = new CancellationTokenSource();
timeoutSource.CancelAfter(TimeSpan.FromSeconds(2));
await dependency.CallAsync(timeoutSource.Token);
```

Trong ứng dụng thật thường link request token và timeout token. Quyết định mapping rõ: caller cancel có thể trả trạng thái khác dependency timeout. Không retry tự động một operation không idempotent.

### `OperationCanceledException` và `TaskCanceledException`

`TaskCanceledException` kế thừa `OperationCanceledException`. Consumer thường catch base type và dùng token/filter để phân biệt cancellation mình dự kiến. Không nên phụ thuộc API cụ thể luôn ném subtype nào.

Exception validation trong thân `async Task` method cũng được lưu vào returned task, kể cả code nằm trước `await`; caller quan sát khi await. Một method thường (không `async`) trả Task có thể ném đồng bộ trước khi trả task. Contract cần được test ở call site bằng `await`.

Khi public API yêu cầu argument exception xuất hiện đồng bộ, tách wrapper không `async` khỏi core async:

```csharp
public Task SaveAsync(Order order, CancellationToken token)
{
    ArgumentNullException.ThrowIfNull(order);
    return SaveCoreAsync(order, token);
}

private async Task SaveCoreAsync(Order order, CancellationToken token)
{
    await _repository.SaveAsync(order, token);
}
```

Đây là lựa chọn contract, không phải lý do dùng `.Wait()` hoặc bỏ `await` trong core.

## 6. Lỗi thường gặp

### Chỉ gọi `Cancel()` rồi nghĩ work đã dừng

Operation không đọc token vẫn tiếp tục. Token phải đi tới API thấp nhất và được kiểm tra ở boundary an toàn.

### Nuốt cancellation như lỗi

`catch (Exception)` rồi log Error làm metric sai. Catch `OperationCanceledException` dự kiến riêng; rethrow cancellation không thuộc token/policy của bạn.

### Biến timeout thành cancellation nhưng mất nguyên nhân

Caller cancellation và deadline nội bộ có ý nghĩa vận hành khác nhau. Giữ token/source hoặc result code đủ để mapping đúng, không chỉ catch mọi `OperationCanceledException` rồi trả một message.

### Timeout xong bỏ quên operation gốc

`WaitAsync` hết hạn không dừng task gốc. Nếu task giữ socket/resource hoặc có side effect, phải có ownership: truyền token, theo dõi completion, hoặc giao operation cho background component có lifecycle.

### Chỉ log exception từ `await WhenAll`

Batch nhiều task có thể có nhiều fault. Inspect `combined.Exception.InnerExceptions` sau khi task hoàn thành faulted nếu mọi nguyên nhân đều cần chẩn đoán; tránh log trùng cùng exception ở mọi tầng.

## 7. Bài tập

### Bài 1 — Hủy import theo dòng

Import 100 dòng, cancel sau dòng 10 và bảo đảm không xử lý dòng 11.

Gợi ý: kiểm tra token trước mỗi unit; callback deterministic thay vì dựa vào delay.

### Bài 2 — Propagate token

Tạo chuỗi Controller giả -> Service -> Repository; truyền cùng token xuống method cuối.

Gợi ý: đặt breakpoint và so sánh `CancellationToken` equality; không tạo source mới ở service.

### Bài 3 — Timeout không dừng underlying task

Lặp lại sample với một `TaskCompletionSource`, timeout trước rồi complete underlying task sau đó.

Gợi ý: await task gốc ở cuối để chứng minh nó vẫn có thể hoàn thành.

### Bài 4 — Linked cancellation

Tạo request source và shutdown source, link chúng, rồi cancel từng source trong hai lượt chạy.

Gợi ý: dispose linked source; ghi rõ source nào đã yêu cầu dừng.

### Bài 5 — Nhiều fault

Cho ba task fault với ba custom exception; await `WhenAll` và in type của mọi `InnerExceptions` theo thứ tự ổn định.

Gợi ý: collect rồi sort tên type/job ID khi output phải deterministic.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi biết cancellation là cooperative, không phải thread abort.
- [ ] Tôi truyền token tới API thấp nhất và kiểm tra ở điểm giữ invariant.
- [ ] Tôi phân biệt timeout chờ với hủy operation gốc.
- [ ] Tôi catch cancellation dự kiến theo token/policy.
- [ ] Tôi quan sát được mọi fault của `Task.WhenAll` khi cần.
- [ ] Tôi dispose source/linked registration đúng ownership.
- [ ] Tôi đã build/run demo không phụ thuộc network/timing.

Bài prerequisite: [`async`, `await`, `Task` và state machine](./09-async-await-task-va-state-machine.md).

Bài tiếp theo: [Parallelism, concurrency và thread safety](./11-parallelism-concurrency-va-thread-safety.md).
