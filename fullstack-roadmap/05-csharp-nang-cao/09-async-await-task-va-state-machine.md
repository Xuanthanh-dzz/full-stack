# `async`, `await`, `Task` và state machine

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, async lifecycle hoặc serializer; CI failure

## TL;DR

- Task biểu diễn completion; await phối hợp mà không giữ thread ngồi chờ.
- Khởi động các I/O độc lập trước rồi await WhenAll khi phù hợp capacity.
- Async không tự tạo thread và không làm CPU work nhanh hơn.

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

### Trực giác 60 giây

Bạn nhận hai phiếu hẹn giá rồi làm việc khác; phiếu không phải một nhân viên đứng đợi riêng. Khi cả hai phiếu có kết quả, bạn tiếp tục tính tổng từ state đã giữ.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| Task | handle trạng thái/kết quả operation | firstPriceTask |
| await | tiếp tục khi awaitable hoàn tất | WhenAll |
| continuation | phần chạy tiếp sau chờ | tính subtotal |
| state machine | cơ chế giữ điểm chạy và local cần thiết | CalculateAsync |
| producer | phía hoàn thành kết quả | TaskCompletionSource |

### Ví dụ nhỏ — tính tay trước

B hoàn thành2 trước A3; calculation vẫn pending tới A xong. WhenAll trả theo thứ tự input[A,B], subtotal5,tax0.5,total5.5.

Checkout cần lấy giá của hai SKU từ một nguồn bất đồng bộ rồi tính tổng. Hai yêu cầu lấy giá độc lập; nếu chờ giá bàn phím xong mới bắt đầu lấy giá chuột, latency bị cộng dồn.

Ta cũng cần trả control cho caller trong lúc chưa có giá, thay vì giữ một thread chỉ để ngồi chờ. Vì bài học phải chạy ổn định không phụ thuộc network hay tốc độ máy, nguồn giá demo dùng `TaskCompletionSource<T>`: code test chủ động quyết định khi nào từng `Task<T>` hoàn thành.

Mục tiêu không phải “làm mọi code chạy song song”. Mục tiêu là biểu diễn một thao tác chưa hoàn thành, tạm dừng method mà không block caller, rồi tiếp tục đúng state khi kết quả sẵn sàng.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

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

Trong demo, `TaskCompletionSource<decimal>` là phía **producer** điều khiển một `Task<decimal>`: `Task` được đưa cho consumer, còn producer gọi `SetResult` để hoàn thành nó.

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

### Walkthrough — execution / state / cost

1. CalculateAsync chạy ngay validation và tạo hai request trước await chưa hoàn tất.
2. State cần thiết được giữ; Main nhận task pending.
3. CompleteB rồiA; continuation tính tổng và complete task ngoài.
4. TCS/dictionary giữ pending tasks, không có thread riêng cho mỗi giá. Latency chờ độc lập có thể chồng; task/state và I/O vẫn có cost.

### Mini-check

Complete chỉ B có đủ để tính không? Nếu source thứ hai ném đồng bộ, ai còn sở hữu request A đang pending?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

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

Code đúng không dựa vào managed thread ID trước/sau `await` giống nhau.

### State machine giữ state qua lần tạm dừng

Khi suspend, dữ liệu cần dùng sau `await` phải sống lâu hơn stack frame ban đầu. Compiler/runtime lưu state và đăng ký continuation với awaiter. Khi P1 và P2 hoàn thành, Task A hoàn thành; continuation khôi phục state, tính `subtotal`, `tax`, rồi complete Task C.

### Đào sâu (có thể quay lại sau)

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

Option `RunContinuationsAsynchronously` tránh chạy continuation ngay bên trong lệnh `SetResult`, giúp boundary producer/consumer rõ hơn.

Chi tiết implementation có thể được JIT tối ưu; state machine thường bắt đầu dưới dạng struct do compiler sinh và chỉ cần representation sống lâu khi thực sự suspend. Điều cần dựa vào là semantics: local cần thiết được giữ, method tiếp tục đúng điểm, không phải stack frame cũ bị block.

#### Continuation và scheduling

`await` hỏi awaiter xem operation đã hoàn thành chưa. Nếu chưa, nó đăng ký continuation. Nơi continuation chạy phụ thuộc awaiter và context/scheduler hiện tại.

Console application thường không có custom `SynchronizationContext`, nên continuation async thường được queue về thread pool và có thể chạy trên thread khác. UI framework có thể capture context để quay lại UI thread.

`RunContinuationsAsynchronously` trong producer ngăn `SetResult` trực tiếp chạy toàn bộ consumer continuation trên call stack của producer. Nó vẫn không hứa một thread riêng cho mỗi continuation.

`ControlledPriceSource` chỉ là test double single-owner để điều khiển completion deterministic. `Dictionary` bên trong không thread-safe; đừng dùng class demo này như production source có nhiều producer thread. Bài concurrency sẽ dạy synchronization và concurrent collection.

- `ValueTask<T>` chỉ nên dùng khi API/performance profile chứng minh có lợi; nó có quy tắc consumption phức tạp hơn.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| await tuần tự | operation sau chờ trước | đúng khi có dependency |
| WhenAll | phối hợp tasks đã tạo | đúng khi độc lập, cần capacity |
| Task.Run | queue work lên pool | không cần cho I/O async đã có |

### Misconception check

**Đúng hay sai?** Mỗi await chắc chắn đổi thread.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: awaitable đã xong có thể tiếp tục đồng bộ.

</details>

**Đúng hay sai?** WhenAll tự bắt đầu hai method chưa gọi.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: nó nhận tasks của operation đã tạo.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** Task/await trace.

- **Working Developer — dùng khi làm việc:** ownership và async all the way.

- **Deep Dive — có thể quay lại sau:** context/scheduler khi có driver.

### Chữ ký async chuẩn

- `Task` cho operation không trả value.
- `Task<T>` cho operation trả `T`.
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

## 7. Khi nào KHÔNG dùng

Không dùng .Result/.Wait trong async chain. Không đưa ControlledPriceSource single-owner vào production nhiều producer; sample chưa có failure/cancel cleanup protocol cho mọi request.

## 8. Production notes & scale check

Test pending trước completion, chỉ một giá chưa đủ, kết quả và fault validation khi await. Không assert threadID hoặc milliseconds. TCS dùng RunContinuationsAsynchronously để không inline consumer trong SetResult; vẫn không hứa dedicated thread.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

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

## 10. Bài tập tích hợp liên module — Judgment

So với callback Module02 và delegate Module05, Task bổ sung contract completion/error nào? Với hai giá phụ thuộc nhau, giải thích vì sao sequential await lại đúng.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Task có phải thread không?
2. Phần nào chạy trước await?
3. Local cần sau suspend sống nhờ đâu?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi hiểu Task là trạng thái operation, không phải một thread.
- [ ] Tôi mô tả được phần async method chạy trước incomplete await.
- [ ] Tôi vẽ được state machine giữ local/reference qua suspension.
- [ ] Tôi dùng `Task.WhenAll` cho operation độc lập mà không gọi nó là parallelism mặc định.
- [ ] Tôi không dựa vào continuation chạy cùng thread.
- [ ] Tôi tránh `.Result`, `.Wait()`, `async void` và fire-and-forget vô chủ.
- [ ] Tôi đã build/run demo deterministic bằng .NET 9.

Bài prerequisite: [Pattern matching](./08-pattern-matching.md).

Bài tiếp theo: [Cancellation, timeout và exception bất đồng bộ](./10-cancellation-timeout-va-exception-bat-dong-bo.md).
