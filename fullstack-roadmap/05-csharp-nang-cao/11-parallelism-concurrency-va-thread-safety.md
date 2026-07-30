# Parallelism, concurrency và thread safety

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt concurrency (nhiều operation cùng tiến triển) với parallelism (thực thi đồng thời);
- giải thích async I/O không mặc định tạo thread và không đồng nghĩa parallel CPU work;
- nhận ra race condition từ một chuỗi read-modify-write không atomic;
- dùng một lịch thực thi được điều khiển để tái hiện lost update ổn định;
- bảo vệ critical section bằng `lock` và cập nhật scalar bằng `Interlocked`;
- hiểu visibility/ordering cơ bản mà synchronization primitive cung cấp;
- chọn immutable state, ownership, concurrent collection hoặc synchronization theo bài toán;
- tránh deadlock, khóa public object, `volatile` sai mục đích và giữ lock quá lâu.

## 2. Bài toán mở đầu

Hai worker cùng tăng bộ đếm số đơn đã xử lý. Code `_value++` trông như một statement, nhưng có thể bị tách thành đọc, cộng, ghi:

```text
Worker A đọc 0          Worker B đọc 0
Worker A tính 1         Worker B tính 1
Worker A ghi 1          Worker B ghi 1
```

Kết quả cuối là `1` dù có hai lần tăng. Một demo dựa vào chạy loop thật nhiều có lúc tái hiện, lúc không; đó không phải test ổn định. Ta sẽ ép hai operation cùng đọc trước khi cho phép ghi, rồi sửa bằng `lock` và `Interlocked`. Sau đó dùng `Parallel.For` để chạy CPU iterations mà kết quả vẫn deterministic.

## 3. Lời giải bằng code

Tạo project:

```bash
mkdir ThreadSafetyDemo
cd ThreadSafetyDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `ThreadSafetyDemo.csproj` bằng:

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

Ba primitive xuất hiện trong sample có vai trò khác nhau: `lock` tạo critical section mutual exclusion; `Interlocked.Increment` gộp phép tăng scalar thành một atomic operation; `Volatile.Read` đọc với visibility/ordering semantics nhưng không biến compound update thành atomic. `Parallel.For` phân phối các iteration CPU cho scheduler và có thể dùng nhiều thread-pool worker.

```csharp
namespace ThreadSafetyDemo;

// Chỉ dùng để chứng minh lost update; đây KHÔNG phải counter production.
public sealed class CoordinatedUnsafeCounter
{
    private readonly TaskCompletionSource _bothReadersReady = new(
        TaskCreationOptions.RunContinuationsAsynchronously);

    private readonly TaskCompletionSource _allowWrites = new(
        TaskCreationOptions.RunContinuationsAsynchronously);

    private int _value;
    private int _readerCount;

    public int Value => _value;
    public Task BothReadersReady => _bothReadersReady.Task;

    public async Task IncrementAsync()
    {
        // Cố ý đọc shared state ngoài synchronization bảo vệ _value.
        int snapshot = _value;

        // Interlocked ở đây chỉ làm barrier test đếm reader an toàn.
        if (Interlocked.Increment(ref _readerCount) == 2)
        {
            _bothReadersReady.SetResult();
        }

        await _allowWrites.Task;

        // Cả hai continuation đều ghi snapshot 0 + 1.
        _value = snapshot + 1;
    }

    public void ReleaseWrites() => _allowWrites.SetResult();
}

public sealed class LockedCounter
{
    private readonly object _gate = new();
    private int _value;

    public int Value
    {
        get
        {
            lock (_gate)
            {
                return _value;
            }
        }
    }

    public void Increment()
    {
        lock (_gate)
        {
            _value++;
        }
    }
}

public sealed class AtomicCounter
{
    private int _value;

    // Volatile.Read giúp reader quan sát write theo memory-ordering contract.
    public int Value => Volatile.Read(ref _value);

    public void Increment()
    {
        // Một atomic read-modify-write, không phải ba bước rời của _value++.
        Interlocked.Increment(ref _value);
    }
}

internal static class Program
{
    private static async Task Main()
    {
        var unsafeCounter = new CoordinatedUnsafeCounter();

        Task first = unsafeCounter.IncrementAsync();
        Task second = unsafeCounter.IncrementAsync();

        await unsafeCounter.BothReadersReady;
        unsafeCounter.ReleaseWrites();
        await Task.WhenAll(first, second);

        Console.WriteLine($"Unsafe expected 2, actual: {unsafeCounter.Value}");

        const int iterations = 20_000;

        var lockedCounter = new LockedCounter();
        Parallel.For(0, iterations, _ => lockedCounter.Increment());
        Console.WriteLine($"Locked counter: {lockedCounter.Value}");

        var atomicCounter = new AtomicCounter();
        Parallel.For(0, iterations, _ => atomicCounter.Increment());
        Console.WriteLine($"Interlocked counter: {atomicCounter.Value}");
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Output deterministic:

```text
Unsafe expected 2, actual: 1
Locked counter: 20000
Interlocked counter: 20000
```

`Parallel.For` được phép dùng nhiều worker nhưng runtime có thể chọn mức parallelism theo máy. Correctness/output không phụ thuộc số thread thực tế.

## 4. Giải thích cơ chế

### Concurrency khác parallelism

```text
Concurrency, một core có thể interleave:
time ──> A1 A2 | B1 B2 | A3 | B3

Parallelism, nhiều core có thể chạy cùng thời điểm:
core 1:  A1 A2 A3
core 2:  B1 B2 B3
time ─────────────>
```

Concurrency là thiết kế nhiều operation có lifetime chồng lấn và cùng tiến triển. Parallelism là một cách execution dùng nhiều processing unit cùng lúc. Một chương trình concurrent có thể chạy trên một core; một loop CPU có thể được parallelize trên nhiều core.

.NET thread pool tái sử dụng worker cho `Task.Run`, timer callback và nhiều continuation.

`Task.WhenAll` của async I/O phối hợp concurrent operations nhưng không tự tạo thread. `Parallel.For` chia CPU iterations cho scheduler và có thể chạy parallel. `Task.Run` queue delegate CPU/blocking work lên thread pool; nó cũng không bảo đảm một dedicated thread hoặc tốc độ tăng.

### Lost update là read-modify-write race

`_value++` tương đương ý tưởng:

```text
temp = read(_value)
temp = temp + 1
write(_value, temp)
```

Demo buộc cả hai call đọc `0`, sau đó mới release cả hai continuation:

```text
Increment #1 state machine: snapshot=0 ──await allowWrites──> write 1
Increment #2 state machine: snapshot=0 ──await allowWrites──> write 1
                                              │
Main ------------------------------------------┘ SetResult
```

Mỗi write `int` riêng lẻ là atomic trên .NET, nhưng toàn chuỗi đọc-cộng-ghi không atomic. Không có exception; kết quả chỉ sai. Đây là lý do race thường khó chẩn đoán.

### `lock` tạo mutual exclusion

`lock (_gate)` chỉ cho một thread vào critical section tại một thời điểm. Thread khác phải chờ. Khi rời lock, kể cả do exception, monitor được release; compiler hạ `lock` về ý tưởng `Monitor.Enter` + `try/finally` + `Monitor.Exit`.

Synchronization còn tạo quan hệ visibility/ordering cần thiết: write trước khi release lock được thread acquire cùng lock sau đó quan sát theo memory model. Vì getter cũng lock cùng `_gate`, cả đọc và ghi tham gia một protocol.

Mỗi lần `new LockedCounter()` tạo object counter và object `_gate` riêng. Khóa một counter không chặn counter khác.

### `Interlocked` cho thao tác scalar

`Interlocked.Increment(ref _value)` thực hiện tăng như một atomic read-modify-write. Nó gọn hơn lock cho một counter đơn. `Volatile.Read` ở getter bảo đảm read có semantics visibility phù hợp; nó không làm phép `++` thường trở thành atomic.

Khi invariant trải trên nhiều field, một Interlocked riêng cho từng field có thể không đủ. Dùng lock hoặc thiết kế immutable snapshot/CAS loop có chủ đích.

## 5. Kiến thức nền

### Thread safety là property của toàn bộ protocol

Một method dùng lock chưa đủ nếu method khác đọc cùng field không lock, hoặc caller phải thực hiện hai method atomically. Ví dụ `if (queue.Count > 0) queue.Dequeue()` vẫn race nếu thread khác dequeue giữa hai lời gọi.

Các chiến lược chính:

- tránh sharing bằng local state/ownership rõ ràng;
- chia sẻ immutable snapshot;
- dùng `lock` cho critical section nhiều bước;
- dùng `Interlocked` cho update scalar hỗ trợ;
- dùng `ConcurrentDictionary`, `ConcurrentQueue`... cho operation collection đã thiết kế thread-safe;
- truyền message/channel để một owner duy nhất mutate state.

Concurrent collection không tự làm một chuỗi nhiều operation thành atomic; dùng API compound như `GetOrAdd`/`AddOrUpdate` và hiểu delegate có thể được gọi nhiều lần.

### Async mutual exclusion

Không thể đặt `await` trực tiếp trong body `lock`, và cũng không nên giữ monitor trong lúc chờ I/O. Khi thật sự cần mutex async, dùng `SemaphoreSlim` với ownership/finally:

```csharp
await semaphore.WaitAsync(cancellationToken);
try
{
    await UpdateAsync(cancellationToken);
}
finally
{
    semaphore.Release();
}
```

Semaphore phải có owner/lifetime rõ ràng. Đừng biến mọi service thành một global lock; có thể làm throughput về một request tại một thời điểm.

### Giới hạn parallelism

Nhiều hơn không luôn nhanh hơn. CPU cores, memory bandwidth, downstream connection limit và allocation đều hữu hạn. Với `ParallelOptions.MaxDegreeOfParallelism` hoặc bounded worker/queue, chọn giới hạn từ measurement và capacity, không từ số lượng input.

Async I/O cũng cần bounded concurrency; tạo một triệu Task cùng lúc có thể gây memory pressure hoặc overload dependency dù không có một triệu thread.

### Đào sâu (có thể quay lại sau)

#### Thread pool

Blocking lâu trên pool có thể gây starvation; tạo thread thủ công chỉ hợp requirement rất cụ thể. Server code ưu tiên API async thật cho I/O.

## 6. Lỗi thường gặp

### Dùng `volatile` để sửa `_value++`

`volatile` ảnh hưởng read/write visibility và ordering nhất định; nó không gộp read-modify-write thành một operation atomic. Dùng `Interlocked.Increment` hoặc lock.

### Khóa `this`, string hoặc `typeof(T)`

Object đó có thể bị code khác khóa ngoài ý muốn, tạo contention/deadlock khó truy. Dùng private readonly gate object không công khai.

### Giữ lock khi gọi I/O hoặc code ngoài

Critical section dài làm contention tăng; callback bên ngoài có thể re-enter hoặc khóa theo thứ tự khác. Chỉ giữ lock quanh shared invariant tối thiểu.

### Khóa nhiều object không cùng thứ tự

Thread A giữ gate 1 đợi gate 2, thread B giữ gate 2 đợi gate 1 tạo deadlock. Quy định global lock order hoặc thiết kế giảm nhiều lock.

### Cho rằng collection thread-safe làm element thread-safe

`ConcurrentDictionary<string, Order>` bảo vệ cấu trúc dictionary, không bảo vệ mutation đồng thời bên trong cùng `Order`. Element cần immutable hoặc protocol riêng.

### Benchmark bằng một lần chạy Debug

Scheduling và contention thay đổi theo máy/lần chạy. Dùng test deterministic cho correctness như sample; benchmark Release nhiều iteration bằng công cụ phù hợp cho performance.

## 7. Bài tập

### Bài 1 — Lost update có kiểm soát

Mở rộng counter unsafe cho ba reader cùng đọc trước khi ghi; dự đoán output.

Gợi ý: barrier test có target `3`; không dùng delay để “hy vọng” race xảy ra.

### Bài 2 — Bank account invariant

Cho hai worker rút tiền từ cùng account; bảo đảm balance không âm và check+update atomic.

Gợi ý: lock cùng private gate quanh cả kiểm tra lẫn phép trừ.

### Bài 3 — Interlocked statistics

Đếm số success/failure độc lập bằng `Interlocked`; giải thích vì sao tổng hợp invariant giữa hai counter có thể cần snapshot/lock.

Gợi ý: đọc từng counter bằng `Volatile.Read`, rồi thảo luận snapshot có thể thuộc hai thời điểm khác nhau.

### Bài 4 — Async gate

Bảo vệ một section async bằng `SemaphoreSlim`, hỗ trợ cancellation và luôn release khi exception.

Gợi ý: `WaitAsync` nằm trước `try`; chỉ `Release` sau khi acquire thành công.

### Bài 5 — Chọn mô hình

Với cache read-heavy, queue công việc và batch CPU, đề xuất immutable snapshot, concurrent collection, channel hay parallel loop.

Gợi ý: ghi thao tác atomic cần có, ownership và giới hạn concurrency trước khi chọn API.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt concurrency với parallelism và async với parallel CPU work.
- [ ] Tôi tách được `_value++` thành read-modify-write và giải thích lost update.
- [ ] Tôi dùng private gate và khóa mọi đường truy cập cùng invariant.
- [ ] Tôi dùng Interlocked cho scalar phù hợp, không thay bằng volatile.
- [ ] Tôi không await trong lock hoặc giữ lock quanh I/O/callback ngoài.
- [ ] Tôi xét thread safety của element và compound operation, không chỉ collection.
- [ ] Tôi đã build/run race demo deterministic bằng .NET 9.

Bài prerequisite: [Cancellation, timeout và exception bất đồng bộ](./10-cancellation-timeout-va-exception-bat-dong-bo.md).

Bài tiếp theo: [`IDisposable`, GC và quản lý tài nguyên](./12-idisposable-gc-va-quan-ly-tai-nguyen.md).
