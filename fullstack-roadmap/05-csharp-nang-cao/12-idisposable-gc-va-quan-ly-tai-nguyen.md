# `IDisposable`, GC và quản lý tài nguyên

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt managed memory với tài nguyên hữu hạn bên ngoài như file handle/socket;
- dùng `using` declaration/statement để gọi `Dispose` deterministic qua `try/finally`;
- viết một sealed owner implement `IDisposable` với `Dispose` idempotent;
- ném `ObjectDisposedException` khi object bị dùng sau khi đóng;
- dùng `IAsyncDisposable` và `await using` khi cleanup thật sự cần await;
- giải thích `Dispose` không giải phóng ngay managed object và GC không thay `Dispose`;
- mô tả reachability, eligibility for collection và finalizer ở mức cơ chế;
- ưu tiên `SafeHandle` thay vì tự quản lý raw unmanaged handle/finalizer.

## 2. Bài toán mở đầu

Ứng dụng ghi audit vào file. Nếu chỉ chờ GC, file handle có thể còn mở không xác định bao lâu; dữ liệu buffer chưa flush và deploy trên Windows có thể không thay/xóa được file. Ngược lại, gọi `Dispose` không làm object biến mất: reference vẫn còn và caller vẫn có thể gọi nhầm method sau khi tài nguyên đã đóng.

Ta cần một lifecycle rõ:

1. object mở và **sở hữu** writer;
2. code dùng object trong một scope;
3. rời scope luôn đóng writer, kể cả có exception;
4. gọi `Dispose` lần hai không phá state;
5. dùng sau dispose bị từ chối rõ ràng;
6. managed memory được GC thu hồi sau, theo reachability chứ không theo dấu ngoặc `using`.

## 3. Lời giải bằng code

Tạo project:

```bash
mkdir ResourceLifetimeDemo
cd ResourceLifetimeDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `ResourceLifetimeDemo.csproj` bằng:

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

`IDisposable` là contract đồng bộ có method `void Dispose()` và được tiêu thụ bằng `using`. `IAsyncDisposable` có method `ValueTask DisposeAsync()` và được tiêu thụ bằng `await using`; `ValueTask` là awaitable value type dùng để biểu diễn completion có thể đồng bộ hoặc bất đồng bộ. Sample giới thiệu cả hai, nhưng mỗi type chỉ chọn contract phù hợp với cleanup của nó.

```csharp
namespace ResourceLifetimeDemo;

// Sealed owner đơn giản: AuditFile sở hữu StreamWriter được truyền tạo bên trong.
// Type này được dùng theo một owner/thread; không tuyên bố thread-safe.
public sealed class AuditFile : IDisposable
{
    private StreamWriter? _writer;

    public AuditFile(string path)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(path);
        _writer = new StreamWriter(path, append: false);
    }

    public void WriteLine(string message)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(message);

        StreamWriter writer = _writer ??
            throw new ObjectDisposedException(nameof(AuditFile));

        writer.WriteLine(message);
    }

    public void Dispose()
    {
        // Null là state "đã dispose"; lần gọi sau trở thành no-op.
        StreamWriter? writer = _writer;
        if (writer is null)
        {
            return;
        }

        _writer = null;
        writer.Dispose(); // flush buffer và đóng FileStream/handle mà writer sở hữu.
    }
}

public sealed class AsyncSession : IAsyncDisposable
{
    private bool _disposed;

    public bool IsDisposed => _disposed;

    public async Task SendAsync(string message)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(message);
        ThrowIfDisposed();

        // Demo một async boundary; session thật có thể flush network bất đồng bộ.
        await Task.Yield();

        ThrowIfDisposed();
    }

    public async ValueTask DisposeAsync()
    {
        if (_disposed)
        {
            return;
        }

        // Demo cleanup cần await; không block bằng .Wait()/.Result.
        await Task.Yield();
        _disposed = true;
    }

    private void ThrowIfDisposed()
    {
        if (_disposed)
        {
            throw new ObjectDisposedException(nameof(AsyncSession));
        }
    }
}

internal static class Program
{
    private static async Task Main()
    {
        string path = Path.Combine(
            Path.GetTempPath(),
            $"resource-lifetime-{Guid.NewGuid():N}.log");

        try
        {
            var audit = new AuditFile(path);

            // using gọi Dispose trong finally khi block kết thúc.
            using (audit)
            {
                audit.WriteLine("order-created");
                audit.WriteLine("order-paid");
            }

            // Dispose idempotent: gọi lần hai không ném.
            audit.Dispose();

            string content = string.Join(" | ", File.ReadAllLines(path));
            Console.WriteLine($"File content: {content}");

            bool rejectedAfterDispose;
            try
            {
                audit.WriteLine("should-fail");
                rejectedAfterDispose = false;
            }
            catch (ObjectDisposedException)
            {
                rejectedAfterDispose = true;
            }

            Console.WriteLine($"Disposed object rejects writes: {rejectedAfterDispose}");

            var session = new AsyncSession();
            await using (session)
            {
                await session.SendAsync("flush-me");
            }

            Console.WriteLine($"Async session disposed: {session.IsDisposed}");
        }
        finally
        {
            if (File.Exists(path))
            {
                File.Delete(path);
            }
        }
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
File content: order-created | order-paid
Disposed object rejects writes: True
Async session disposed: True
```

File tạm dùng tên ngẫu nhiên để không ghi đè dữ liệu có sẵn và được xóa trong `finally`. Output không chứa path nên vẫn deterministic.

## 4. Giải thích cơ chế

### Object graph trước và sau `Dispose`

Khi `AuditFile` đang mở:

```text
Main.audit reference
      │
      v
AuditFile object ──> StreamWriter object ──> FileStream/SafeFileHandle ──> OS file handle
   (managed)             (managed)                 (managed wrapper)          (external)
```

Mỗi `new` tạo object logic riêng: `AuditFile`, `StreamWriter` và các object nội bộ không phải một vùng nhớ duy nhất. `AuditFile` sở hữu writer vì chính constructor tạo nó và không chuyển ownership cho nơi khác.

Sau `Dispose`:

```text
Main.audit ──> AuditFile object { _writer = null }   vẫn reachable

StreamWriter/FileStream objects: không còn được AuditFile giữ
OS handle: đã được đóng deterministic bởi Dispose chain
```

`audit` vẫn trỏ object nên GC chưa thể thu object đó. `Dispose` thay **resource state**, không xóa reference và không giải phóng ngay managed memory. Method kiểm tra `_writer == null` để báo use-after-dispose.

### `using` được hạ về `try/finally`

Ý tưởng của:

```csharp
using (audit)
{
    Work();
}
```

là:

```csharp
try
{
    Work();
}
finally
{
    audit.Dispose();
}
```

Vì vậy `Dispose` chạy khi block kết thúc bình thường, `return` hoặc exception. Nó vẫn không được bảo đảm nếu process bị kill cưỡng bức/mất điện. Dữ liệu bền vững cần transaction/flush protocol phù hợp.

### `await using` và `ValueTask`

`await using` gọi `DisposeAsync` trong một async `finally` và await completion. Nó dành cho resource cần flush/close qua I/O async. `IAsyncDisposable.DisposeAsync` trả `ValueTask`; caller phải await trực tiếp theo contract, không block bằng `.Result`.

Sample dùng `Task.Yield` chỉ để minh họa control flow. Nếu cleanup chỉ làm việc đồng bộ nhỏ, implement `IDisposable`; đừng tạo fake async API không cần thiết.

## 5. Kiến thức nền

### GC quản lý memory theo reachability

GC bắt đầu từ roots như stack local đang sống, static field, handle runtime, rồi lần theo reference. Object không còn reachable trở thành **eligible for collection**; không có lời hứa nó được thu ngay lúc method return.

```text
GC roots -> reachable graph: giữ lại
GC roots -X-> unreachable graph: eligible; thu ở một GC tương lai
```

Generational GC tối ưu giả định phần lớn object sống ngắn. Runtime có thể compact/move managed object; code an toàn không giữ địa chỉ raw. `GC.Collect()` trong application code thông thường làm pause và phá heuristic, không phải cách thay `Dispose`.

### Managed resource và unmanaged/external resource

- Managed memory: object/array do GC theo dõi.
- External/scarce resource: file descriptor/handle, socket, database connection, native buffer, lock handle...
- Managed wrapper như `FileStream` là object GC-managed nhưng sở hữu external handle cần release sớm.

GC biết kích thước managed object, không hiểu business capacity của connection pool hay deadline giữ file. `IDisposable` cung cấp deterministic cleanup protocol.

### Ownership

Code tạo/nhận ownership resource chịu trách nhiệm dispose. Nếu dependency được inject và owner bên ngoài quản lý lifetime, service thường **không** tự dispose dependency đó. Ghi contract rõ để tránh double-dispose hoặc leak.

Nhiều BCL type như `CancellationTokenSource`, `SemaphoreSlim`, stream và timer implement `IDisposable`; chỉ dispose instance bạn sở hữu, tại lifecycle boundary thích hợp.

### Finalizer và `SafeHandle`

Finalizer chạy không deterministic trên finalizer thread sau khi object được phát hiện unreachable. Nó làm object sống lâu hơn và không có thứ tự an toàn để gọi managed dependency khác. Chỉ type trực tiếp sở hữu unmanaged resource mới cân nhắc finalizer; ưu tiên bọc raw handle bằng `SafeHandle`, rồi owner dispose `SafeHandle`.

Class chỉ sở hữu `StreamWriter` như sample không cần finalizer: writer/FileStream đã có cơ chế handle an toàn. `GC.SuppressFinalize(this)` chỉ có ý nghĩa trong dispose pattern của type có finalizer; không thêm máy móc vào mọi class.

### Dispose pattern khi có inheritance

Sealed class có thể dùng pattern đơn giản như sample. Base class có thể được kế thừa cần `protected virtual Dispose(bool disposing)` để derived type cleanup đúng, và cần thiết kế rất cẩn thận. Ưu tiên composition/sealed owner nếu không có requirement inheritance.

## 6. Lỗi thường gặp

### Chờ GC đóng file/connection

Finalization có thể trễ, làm cạn pool/handle trước khi thiếu memory kích hoạt GC. Dùng `using` tại scope ownership.

### Nghĩ `Dispose` làm object thành `null`

Reference vẫn tồn tại. Set field resource về null/state disposed và chặn public method bằng `ObjectDisposedException`; caller cũng nên kết thúc sử dụng sau scope.

### Dispose dependency không thuộc ownership

Một service dispose shared stream/client do DI container quản lý sẽ làm consumer khác hỏng. Xác định ai tạo, ai sở hữu, ai đóng.

### Viết finalizer cho mọi `IDisposable`

Finalizer không cần cho class chỉ sở hữu managed disposable. Nó tăng chi phí/lifetime và dễ cleanup sai. Dùng SafeHandle cho raw handle.

### Gọi async cleanup bằng `.Wait()`

Sync-over-async có thể deadlock/block thread và bỏ mất semantics exception. Dùng `await using`; nếu type cần cả sync và async dispose, định nghĩa contract/implementation riêng rõ ràng.

### Không idempotent hoặc dùng đồng thời không có contract

Dispose thường nên chịu được lần gọi lặp. Điều đó không tự làm type thread-safe khi `Write` và `Dispose` chạy đồng thời; sample tuyên bố single-owner. Nếu cần concurrency, thiết kế synchronization/lifetime protocol và test race riêng.

## 7. Bài tập

### Bài 1 — Dùng `using` declaration

Ghi hai dòng bằng `StreamWriter` với `using StreamWriter writer = ...;`, rồi xác định chính xác scope dispose.

Gợi ý: using declaration dispose ở cuối block hiện tại, theo thứ tự ngược khi có nhiều resource.

### Bài 2 — Wrapper idempotent

Tạo sealed `CsvWriter : IDisposable`, gọi `Dispose` hai lần và từ chối `WriteRow` sau dispose.

Gợi ý: field nullable biểu diễn state; owner dispose writer đúng một lần.

### Bài 3 — Exception vẫn cleanup

Ném exception giữa block dùng file, bắt ở ngoài và chứng minh file có thể mở lại sau đó.

Gợi ý: không catch trong resource chỉ để nuốt lỗi; `using` đã tạo finally.

### Bài 4 — Async cleanup

Tạo `FakeBatch : IAsyncDisposable` có `DisposeAsync` hoàn tất qua controlled Task thay vì delay.

Gợi ý: `await using` phải đợi cleanup trước khi in trạng thái cuối.

### Bài 5 — Audit ownership graph

Vẽ graph Controller -> Service -> injected repository -> connection. Chỉ ra component nào tạo/sở hữu/dispose mỗi node.

Gợi ý: dependency do container cấp thường được container đóng; object per-operation do method tạo thường được method dùng bằng using.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi phân biệt managed memory với external/scarce resource.
- [ ] Tôi giải thích được using hạ thành try/finally.
- [ ] Tôi viết Dispose idempotent và chặn use-after-dispose.
- [ ] Tôi biết Dispose không làm object biến mất và GC không thay Dispose.
- [ ] Tôi dùng await using chỉ khi cleanup thật sự async.
- [ ] Tôi xác định ownership trước khi dispose dependency.
- [ ] Tôi ưu tiên SafeHandle, không thêm finalizer máy móc.
- [ ] Tôi đã build/run demo và xác nhận file tạm được dọn.

Bài prerequisite: [Parallelism, concurrency và thread safety](./11-parallelism-concurrency-va-thread-safety.md).

Bài tiếp theo: [Reflection, attribute và `dynamic`](./13-reflection-attribute-va-dynamic.md).
