# `async`, `await`, `Task` và state machine

## 1. Mục tiêu

Sau bài này, bạn có thể:

- đọc `Task` như một handle đại diện cho thao tác có thể hoàn thành trong tương lai;
- viết method trả `Task<T>` bằng `async`/`await` và gọi nó theo kiểu async all the way;
- khởi động các thao tác độc lập trước rồi phối hợp bằng `Task.WhenAll`;
- giải thích chính xác `await` không đồng nghĩa tạo thread mới;
- mô tả phần method chạy đồng bộ trước incomplete `await` đầu tiên;
- theo dõi state/local/reference qua compiler-generated async state machine;
- hiểu continuation có thể chạy trên thread khác và không dựa vào thread identity;
- tránh `.Result`, `.Wait()`, `async void` và fire-and-forget không được giám sát.

## 2. Bài toán mở đầu

Checkout cần lấy giá của hai SKU từ một nguồn bất đồng bộ rồi tính tổng. Hai yêu cầu lấy giá độc lập; nếu chờ giá bàn phím xong mới bắt đầu lấy giá chuột, latency bị cộng dồn.

Ta cũng cần trả control cho caller trong lúc chưa có giá, thay vì giữ một thread chỉ để ngồi chờ. Vì bài học phải chạy ổn định không phụ thuộc network hay tốc độ máy, nguồn giá demo dùng `TaskCompletionSource<T>`: code test chủ động quyết định khi nào từng `Task<T>` hoàn thành.

Mục tiêu không phải “làm mọi code chạy song song”. Mục tiêu là biểu diễn một thao tác chưa hoàn thành, tạm dừng method mà không block caller, rồi tiếp tục đúng state khi kết quả sẵn sàng.

## 3. Lời giải bằng code

Tạo project:

```bash
mkdir AsyncCheckoutDemo
cd AsyncCheckoutDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `AsyncCheckoutDemo.csproj` bằng:

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

Trong demo, `TaskCompletionSource<decimal>` là phía **producer** điều khiển một `Task<decimal>`: `Task` được đưa cho consumer, còn producer gọi `SetResult` để hoàn thành nó. Option `RunContinuationsAsynchronously` tránh chạy continuation ngay bên trong lệnh `SetResult`, giúp boundary producer/consumer rõ hơn.

Thay toàn bộ `Program.cs`:

```csharp
using System.Collections.Generic;

namespace AsyncCheckoutDemo;

public interface IPriceSource
{
    Task<decimal> GetPriceAsync(string sku);
}

public sealed class ControlledPriceSource : IPriceSource
{
    private readonly Dictionary<string, TaskCompletionSource<decimal>> _pending =
        new(StringComparer.OrdinalIgnoreCase);

    public Task<decimal> GetPriceAsync(string sku)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(sku);

        var completion = new TaskCompletionSource<decimal>(
            TaskCreationOptions.RunContinuationsAsynchronously);

        if (!_pending.TryAdd(sku, completion))
        {
            throw new InvalidOperationException($"A request for '{sku}' already exists.");
        }

        return completion.Task;
    }

    public void Complete(string sku, decimal price)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(price);

        if (!_pending.Remove(sku, out TaskCompletionSource<decimal>? completion))
        {
            throw new InvalidOperationException($"No pending request for '{sku}'.");
        }

        completion.SetResult(price);
    }
}

public sealed record CheckoutTotal(decimal Subtotal, decimal Tax, decimal Total);

public sealed class CheckoutService
{
    private readonly IPriceSource _priceSource;

    public CheckoutService(IPriceSource priceSource)
    {
        _priceSource = priceSource ??
            throw new ArgumentNullException(nameof(priceSource));
    }

    public async Task<CheckoutTotal> CalculateAsync(
        string firstSku,
        string secondSku)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(firstSku);
        ArgumentException.ThrowIfNullOrWhiteSpace(secondSku);

        // Gọi cả hai method trước khi await: hai operation được in-flight cùng lúc.
        Task<decimal> firstPriceTask = _priceSource.GetPriceAsync(firstSku);
        Task<decimal> secondPriceTask = _priceSource.GetPriceAsync(secondSku);

        decimal[] prices = await Task.WhenAll(firstPriceTask, secondPriceTask);

        decimal subtotal = prices[0] + prices[1];
        decimal tax = subtotal * 0.10m;
        return new CheckoutTotal(subtotal, tax, subtotal + tax);
    }
}

internal static class Program
{
    private static async Task Main()
    {
        var source = new ControlledPriceSource();
        var service = new CheckoutService(source);

        // Method chạy tới incomplete await rồi trả Task cho Main.
        Task<CheckoutTotal> calculation = service.CalculateAsync(
            "KEYBOARD",
            "MOUSE");

        Console.WriteLine($"Returned before prices: {!calculation.IsCompleted}");

        // Producer hoàn thành hai operation theo thứ tự do test kiểm soát.
        source.Complete("MOUSE", 350_000m);
        source.Complete("KEYBOARD", 750_000m);

        CheckoutTotal result = await calculation;

        Console.WriteLine($"Subtotal: {result.Subtotal:N0} VND");
        Console.WriteLine($"Tax: {result.Tax:N0} VND");
        Console.WriteLine($"Total: {result.Total:N0} VND");
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
Returned before prices: True
Subtotal: 1,100,000 VND
Tax: 110,000 VND
Total: 1,210,000 VND
```

Phân cách hàng nghìn có thể khác theo locale. Không có delay/network nên thứ tự và giá trị không phụ thuộc timing máy.

## 4. Giải thích cơ chế

### `Task` không phải thread

`Task<decimal>` là object biểu diễn trạng thái và kết quả tương lai: chưa hoàn thành, hoàn thành thành công, faulted hoặc canceled. Trong sample, gọi `GetPriceAsync` chỉ tạo `TaskCompletionSource`/`Task` và lưu chúng vào dictionary; không có `Thread`, `Task.Run` hay worker mới.

```text
Main thread gọi CalculateAsync
        │
        ├─ tạo price Task P1 (incomplete)
        ├─ tạo price Task P2 (incomplete)
        ├─ Task.WhenAll tạo Task A (đợi P1 + P2)
        └─ await thấy A incomplete -> CalculateAsync trả Task C cho Main

Không có thread bị dành riêng để "ngồi trong await".
```

Nguồn I/O thật đăng ký operation với OS/runtime rồi trả `Task`. Khi I/O hoàn tất, completion được báo và continuation trở nên runnable. Async giúp thread rảnh xử lý việc khác trong thời gian chờ; nó không tự làm CPU work nhanh hơn.

### Phần trước `await` chạy đồng bộ

Gọi một `async` method bắt đầu thực thi ngay trên thread hiện tại. `CalculateAsync` validate input, gọi hai source và đến `await Task.WhenAll(...)`. Vì task tổng chưa xong, method tạm dừng và trả `Task<CheckoutTotal>`.

Nếu awaitable đã hoàn thành, `await` có thể tiếp tục đồng bộ mà không suspend. Vì vậy không được dựa vào `await` như một ranh giới chắc chắn đổi thread hoặc trì hoãn execution.

### State machine giữ state qua lần tạm dừng

Compiler biến method `async` thành state machine có ý tưởng:

```text
Async state machine của CalculateAsync
┌─────────────────────────────────────────────┐
│ state: đang chờ Task.WhenAll                │
│ this/service reference ──> CheckoutService  │
│ firstSku reference ──────> string object    │
│ secondSku reference ─────> string object    │
│ awaiter của Task A                          │
│ builder cho Task<CheckoutTotal> C            │
└─────────────────────────────────────────────┘
```

Khi suspend, dữ liệu cần dùng sau `await` phải sống lâu hơn stack frame ban đầu. Compiler/runtime lưu state và đăng ký continuation với awaiter. Khi P1 và P2 hoàn thành, Task A hoàn thành; continuation khôi phục state, tính `subtotal`, `tax`, rồi complete Task C.

Chi tiết implementation có thể được JIT tối ưu; state machine thường bắt đầu dưới dạng struct do compiler sinh và chỉ cần representation sống lâu khi thực sự suspend. Điều cần dựa vào là semantics: local cần thiết được giữ, method tiếp tục đúng điểm, không phải stack frame cũ bị block.

### Continuation và scheduling

`await` hỏi awaiter xem operation đã hoàn thành chưa. Nếu chưa, nó đăng ký continuation. Nơi continuation chạy phụ thuộc awaiter và context/scheduler hiện tại.

Console application thường không có custom `SynchronizationContext`, nên continuation async thường được queue về thread pool và có thể chạy trên thread khác. UI framework có thể capture context để quay lại UI thread. Code đúng không dựa vào managed thread ID trước/sau `await` giống nhau.

`RunContinuationsAsynchronously` trong producer ngăn `SetResult` trực tiếp chạy toàn bộ consumer continuation trên call stack của producer. Nó vẫn không hứa một thread riêng cho mỗi continuation.

`ControlledPriceSource` chỉ là test double single-owner để điều khiển completion deterministic. `Dictionary` bên trong không thread-safe; đừng dùng class demo này như production source có nhiều producer thread. Bài concurrency sẽ dạy synchronization và concurrent collection.

## 5. Kiến thức nền

### Chữ ký async chuẩn

- `Task` cho operation không trả value.
- `Task<T>` cho operation trả `T`.
- `ValueTask<T>` chỉ nên dùng khi API/performance profile chứng minh có lợi; nó có quy tắc consumption phức tạp hơn.
- `async void` chỉ dành cho event handler bắt buộc có chữ ký `void`; caller không thể await hoặc quan sát completion/exception như `Task`.

Tên method bất đồng bộ theo convention kết thúc bằng `Async`.

### `Task.WhenAll`: concurrent composition

Hai lời gọi được tạo trước `await`, nên cả hai operation cùng ở trạng thái in-flight. `Task.WhenAll` tạo task chỉ complete khi mọi task input complete. Nó không tự tạo các operation và không tự biến chúng thành parallel thread work.

Sai về latency:

```csharp
decimal first = await source.GetPriceAsync("A");
decimal second = await source.GetPriceAsync("B");
```

Đúng khi hai operation độc lập:

```csharp
Task<decimal> firstTask = source.GetPriceAsync("A");
Task<decimal> secondTask = source.GetPriceAsync("B");
decimal[] prices = await Task.WhenAll(firstTask, secondTask);
```

Nếu operation thứ hai phụ thuộc kết quả thứ nhất, await tuần tự là đúng.

### Exception trong `Task`

Exception phát sinh trong `async Task` method làm returned task chuyển sang Faulted. `await` task đó sẽ ném lại exception để code dùng `try/catch` tự nhiên. Chi tiết cancellation, timeout và nhiều exception được xử lý ở bài tiếp theo.

### Async I/O và CPU-bound work

- I/O-bound: dùng API async thật của file/database/network để không block thread trong lúc chờ.
- CPU-bound: `async` không làm phép tính nhanh hơn; UI/server có thể dùng `Task.Run` có cân nhắc để chuyển CPU work sang thread pool, còn parallelism được học riêng.
- Đừng bọc một API I/O đồng bộ trong `Task.Run` rồi gọi đó là scalable async I/O.

## 6. Lỗi thường gặp

### Chặn bằng `.Result` hoặc `.Wait()`

Hai API này giữ thread chờ task. Trong context một-thread, continuation cần quay lại chính context đó có thể deadlock; trên server, blocking làm giảm throughput. Dùng `await` xuyên suốt call chain.

### Gọi lần lượt khi operation độc lập

Await operation đầu trước khi tạo operation thứ hai làm latency cộng dồn. Tạo cả hai task trước, sau đó `WhenAll`, nhưng chỉ khi hệ thống downstream chịu được mức concurrency đó.

### Dùng `async void`

Caller không await được, exception không nằm trong Task và lifecycle khó test. Ngoài event handler, trả `Task`.

### Fire-and-forget không ownership

```csharp
_ = SendReceiptAsync();
```

Operation có thể fault sau khi request kết thúc, mất exception hoặc dùng dependency đã dispose. Hãy await, hoặc giao cho background queue/service có lifecycle, retry và logging rõ ràng.

### Mang test double single-owner vào production

`TaskCompletionSource` là primitive thấp; completion lặp, race và exception cần protocol rõ. Test source trong bài cố ý được Main điều khiển từ một owner. Production adapter nên dùng API async thật của dependency và chỉ dùng TCS khi đang bridge một callback/event contract đã được thiết kế kỹ.

### Nghĩ `await` tạo thread mới

Sample chứng minh task có thể hoàn tất hoàn toàn nhờ producer gọi `SetResult`, không tạo worker. Muốn chạy CPU work trên thread pool là một quyết định riêng, không phải semantics của `await`.

## 7. Bài tập

### Bài 1 — Một kết quả bất đồng bộ

Tạo `TaskCompletionSource<string>`, trả Task cho một method consumer, sau đó complete từ `Main` và await kết quả.

Gợi ý: bật `RunContinuationsAsynchronously`; in `IsCompleted` trước và sau `SetResult`.

### Bài 2 — Tuần tự và concurrent

Viết service lấy ba giá độc lập; phiên bản đầu await tuần tự, phiên bản sau tạo cả ba task trước `WhenAll`.

Gợi ý: dùng controlled source, không cần đo milliseconds; kiểm tra số request pending trước khi complete.

### Bài 3 — State qua `await`

Tạo local `orderId` trước `await`, dùng lại sau `await`, rồi vẽ reference nào phải được state machine giữ.

Gợi ý: đặt breakpoint trước và sau await, so sánh thread ID nhưng không viết assertion chúng phải khác.

### Bài 4 — Loại bỏ sync-over-async

Tìm `.Result`/`.Wait()` trong một call chain mẫu và refactor mọi method lên tới `Main` thành `async Task`.

Gợi ý: đổi từ lá lên caller; đừng thay bằng `Task.Run(...).Result`.

### Bài 5 — Ownership cho background work

Thiết kế interface queue nhận một công việc gửi email thay vì bỏ Task bằng `_ =`.

Gợi ý: xác định ai await/monitor, cách báo exception và lúc application shutdown.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi hiểu Task là trạng thái operation, không phải một thread.
- [ ] Tôi mô tả được phần async method chạy trước incomplete await.
- [ ] Tôi vẽ được state machine giữ local/reference qua suspension.
- [ ] Tôi dùng `Task.WhenAll` cho operation độc lập mà không gọi nó là parallelism mặc định.
- [ ] Tôi không dựa vào continuation chạy cùng thread.
- [ ] Tôi tránh `.Result`, `.Wait()`, `async void` và fire-and-forget vô chủ.
- [ ] Tôi đã build/run demo deterministic bằng .NET 9.

Bài prerequisite: [Pattern matching](./08-pattern-matching.md).

Bài tiếp theo: [Cancellation, timeout và exception bất đồng bộ](./10-cancellation-timeout-va-exception-bat-dong-bo.md).
