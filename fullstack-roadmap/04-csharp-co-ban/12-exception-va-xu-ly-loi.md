# Exception và xử lý lỗi trong C#

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt dữ liệu không hợp lệ dự kiến trước với lỗi bất thường;
- dùng `try`, các `catch` cụ thể, exception filter và `finally` đúng phạm vi;
- chủ động báo lỗi bằng `throw` và giữ nguyên stack trace khi rethrow bằng `throw;`;
- tạo custom exception có dữ liệu chẩn đoán hữu ích và giữ `InnerException`;
- viết guard clause để chặn input sai ngay tại boundary của method;
- dùng `TryParse` hoặc kết quả trạng thái cho normal flow thay vì lạm dụng exception;
- tránh log dữ liệu nhạy cảm hoặc nuốt lỗi làm hệ thống tiếp tục trong trạng thái sai.

## 2. Bài toán mở đầu

Ứng dụng nhập đơn hàng từ console nhận `customerId` và số lượng ở dạng text. Bốn tình huống phải được phân biệt:

- text số lượng sai định dạng là lỗi nhập liệu thường gặp, người dùng có thể sửa;
- `customerId` rỗng vi phạm contract của method;
- số lượng hợp lệ nhưng kho không đủ là một lỗi nghiệp vụ cần dữ liệu cụ thể;
- ghi đơn hàng xuống file có thể thất bại vì I/O và cần giữ nguyên nguyên nhân gốc.

Nếu đặt một `catch (Exception)` rỗng quanh toàn bộ chương trình, ta mất nguyên nhân lỗi và có thể báo “thành công” dù dữ liệu chưa được lưu. Lời giải dưới đây xử lý lỗi ở tầng có đủ thông tin để quyết định.

## 3. Lời giải bằng code

Tạo project `.NET 9`:

```bash
mkdir ExceptionDemo
cd ExceptionDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay toàn bộ `Program.cs`:

```csharp
using System;
using System.Diagnostics;
using System.IO;

namespace ExceptionDemo;

public sealed class InventoryUnavailableException : Exception
{
    public string ProductId { get; }
    public int Requested { get; }
    public int Available { get; }

    public InventoryUnavailableException(
        string productId,
        int requested,
        int available)
        : base(
            $"Not enough inventory for product '{productId}'. " +
            $"Requested: {requested}; available: {available}.")
    {
        ProductId = productId;
        Requested = requested;
        Available = available;
    }
}

public sealed class OrderPersistenceException : Exception
{
    public OrderPersistenceException(string message, Exception innerException)
        : base(message, innerException)
    {
    }
}

public sealed class Inventory
{
    public int Available { get; private set; }

    public Inventory(int available)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(available);
        Available = available;
    }

    public void Reserve(string productId, int quantity)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(productId);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity);

        if (quantity > Available)
        {
            throw new InventoryUnavailableException(
                productId,
                quantity,
                Available);
        }

        Available -= quantity;
    }

    public void Release(string productId, int quantity)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(productId);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity);

        // Compensating action cho demo single-process.
        Available = checked(Available + quantity);
    }
}

public sealed class OrderRepository
{
    private readonly string _filePath;

    public OrderRepository(string filePath)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(filePath);
        _filePath = filePath;
    }

    public void Save(string orderId, string customerId, int quantity)
    {
        try
        {
            // Trong ứng dụng thật, không ghi secret hoặc dữ liệu nhạy cảm vào log/file thô.
            File.AppendAllText(
                _filePath,
                $"{orderId},{customerId},{quantity}{Environment.NewLine}");
        }
        catch (IOException exception)
        {
            throw new OrderPersistenceException(
                "Could not persist the order.",
                exception);
        }
        catch (UnauthorizedAccessException exception)
        {
            throw new OrderPersistenceException(
                "Could not persist the order.",
                exception);
        }
    }
}

public sealed class OrderService
{
    private const string ProductId = "BOOK-CSHARP";
    private readonly Inventory _inventory;
    private readonly OrderRepository _repository;

    public OrderService(Inventory inventory, OrderRepository repository)
    {
        _inventory = inventory ?? throw new ArgumentNullException(nameof(inventory));
        _repository = repository ?? throw new ArgumentNullException(nameof(repository));
    }

    public string PlaceOrder(string customerId, int quantity)
    {
        // Guard clauses làm rõ contract ngay đầu method.
        ArgumentException.ThrowIfNullOrWhiteSpace(customerId);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity);

        try
        {
            _inventory.Reserve(ProductId, quantity);
        }
        catch (InventoryUnavailableException exception)
        {
            Console.Error.WriteLine(
                $"Reservation failed for product {exception.ProductId}.");

            throw; // Giữ stack trace gốc; không viết "throw exception;".
        }

        string orderId = Guid.NewGuid().ToString("N");

        try
        {
            _repository.Save(orderId, customerId, quantity);
            return orderId;
        }
        catch (OrderPersistenceException)
        {
            // Save thất bại: hoàn tác reservation trong memory trước khi đẩy
            // exception lên boundary. Không nuốt exception gốc.
            _inventory.Release(ProductId, quantity);
            throw;
        }
    }
}

internal static class Program
{
    private static void Main()
    {
        var inventory = new Inventory(10);
        var repository = new OrderRepository("orders.log");
        var service = new OrderService(inventory, repository);

        (string CustomerId, string QuantityText)[] inputs =
        [
            ("CUS-001", "2"),
            ("CUS-002", "not-a-number"),
            ("", "1"),
            ("CUS-003", "99")
        ];

        foreach ((string customerId, string quantityText) in inputs)
        {
            // Sai định dạng là normal flow: không cần ném rồi bắt exception.
            if (!int.TryParse(quantityText, out int quantity))
            {
                Console.WriteLine($"Invalid quantity: '{quantityText}'.");
                continue;
            }

            ProcessOne(service, customerId, quantity);
        }

        Console.WriteLine($"Remaining inventory: {inventory.Available}");
    }

    private static void ProcessOne(
        OrderService service,
        string customerId,
        int quantity)
    {
        var stopwatch = Stopwatch.StartNew();

        try
        {
            string orderId = service.PlaceOrder(customerId, quantity);
            Console.WriteLine($"Created order: {orderId}");
        }
        catch (InventoryUnavailableException exception)
            when (exception.Available > 0)
        {
            // Filter chỉ xử lý trường hợp còn hàng nhưng ít hơn yêu cầu.
            Console.WriteLine(
                $"Reduce quantity to at most {exception.Available} and retry.");
        }
        catch (InventoryUnavailableException)
        {
            Console.WriteLine("Product is out of stock.");
        }
        catch (ArgumentException exception)
        {
            Console.WriteLine($"Invalid order input: {exception.ParamName}.");
        }
        catch (OrderPersistenceException exception)
        {
            Console.Error.WriteLine(
                $"Order was not saved. Cause: {exception.InnerException?.GetType().Name}");
        }
        finally
        {
            stopwatch.Stop();
            Console.WriteLine($"Attempt took {stopwatch.ElapsedMilliseconds} ms.");
        }
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Chương trình tạo `orders.log` cho đơn hợp lệ. `orderId` và thời gian thay đổi theo mỗi lần chạy; các nhánh còn lại báo sai định dạng, input rỗng và thiếu tồn kho mà không làm process bị crash.

## 4. Giải thích cơ chế

### Luồng điều khiển của `try/catch/finally`

Với một lần gọi `ProcessOne`, runtime thực hiện:

```text
try
 │
 ├─ không có exception ───────────────> tiếp tục cuối try
 │
 └─ có exception
      │
      ├─ tìm catch phù hợp từ cụ thể đến tổng quát
      ├─ exception filter phải trả true
      └─ không có catch phù hợp -> unwind lên caller
                  │
                  v
             finally chạy
                  │
                  v
        trả về caller hoặc tiếp tục throw
```

Khi exception xuất hiện, các statement còn lại trong `try` bị bỏ qua. Runtime tìm handler phù hợp và tháo các stack frame (`stack unwinding`) cho tới nơi bắt được lỗi. `finally` dùng cho cleanup cần chạy dù thành công hay thất bại. Với tài nguyên implement `IDisposable`, cú pháp `using` thường rõ và an toàn hơn một `try/finally` gọi `Dispose` thủ công.

Không coi `finally` là cam kết trong mọi tình huống vật lý: process bị kill cưỡng bức, mất điện hoặc lỗi runtime nghiêm trọng có thể khiến code cleanup không kịp chạy. Dữ liệu quan trọng vẫn cần thiết kế bền vững ở tầng lưu trữ.

### `throw`, rethrow và stack trace

Trong `Inventory.Reserve`, `throw new InventoryUnavailableException(...)` tạo một exception object trên managed heap. Object này mang type, message, dữ liệu nghiệp vụ và stack trace khi được throw.

Trong `OrderService`:

```csharp
catch (InventoryUnavailableException exception)
{
    Console.Error.WriteLine(...);
    throw;
}
```

`throw;` ném lại exception hiện tại và giữ vị trí phát sinh gốc. `throw exception;` đặt lại điểm ném nhìn thấy trong stack trace, làm chẩn đoán khó hơn.

Khi cần đổi abstraction, repository tạo exception mới nhưng truyền nguyên nhân cũ qua `InnerException`:

```text
OrderPersistenceException
└── InnerException: IOException hoặc UnauthorizedAccessException
```

Caller chỉ phụ thuộc ngôn ngữ của tầng repository, trong khi log chẩn đoán vẫn truy được nguyên nhân I/O.

### Guard clause

Guard clause xác nhận precondition trước khi method thay đổi state:

```csharp
ArgumentException.ThrowIfNullOrWhiteSpace(customerId);
ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity);
```

Lỗi xuất hiện gần nguồn nhất, `ParamName` rõ ràng và phần thân method không bị lồng nhiều `if`. Guard không thay thế validation nghiệp vụ tổng hợp ở UI/API; nó bảo vệ contract của code.

### Exception filter

`catch (...) when (...)` kiểm tra điều kiện trước khi handler được chọn. Nếu filter trả `false`, quá trình tìm handler tiếp tục mà chưa bước vào block `catch`. Filter nên nhanh, không thay đổi state và không tự ném lỗi.

### Compensation không phải transaction

`PlaceOrder` thay đổi hai nơi: tồn kho trong memory và file đơn hàng. Nếu `Reserve` thành công nhưng `Save` ném `OrderPersistenceException`, code gọi `Release` để trả tồn kho về giá trị trước đó rồi rethrow. Đây là **compensating action**, giúp service không tiếp tục với state “đã trừ hàng nhưng báo lưu thất bại”.

Nó vẫn không tạo atomic transaction thật giữa memory và filesystem: process có thể dừng giữa các bước, file append có thể ghi được một phần trước khi báo lỗi, và compensation cũng có failure mode. Hệ thống production cần persistence/transaction boundary phù hợp, idempotency và recovery; các module database/architecture sẽ xử lý sâu hơn. Điểm của bài này là khi một method đã mutate state rồi thao tác sau thất bại, phải có quyết định rollback/compensate rõ ràng thay vì chỉ catch và tiếp tục.

## 5. Kiến thức nền

### Chọn cơ chế báo kết quả

| Tình huống | Cơ chế phù hợp |
|---|---|
| User nhập số sai và có thể thử lại | `TryParse`, validation result |
| Tìm key có thể không tồn tại | `TryGetValue`, `bool` + `out` |
| Caller vi phạm contract của method | `ArgumentException` phù hợp |
| Không đủ tồn kho, caller phải xử lý riêng | custom exception hoặc domain result tùy contract |
| File/database/network thất bại bất thường | exception, có context và nguyên nhân gốc |

Exception có chi phí tạo object, thu stack trace và unwind stack. Quan trọng hơn, exception làm luồng normal flow khó đọc. Không dùng `try/catch` thay cho `if`, `TryParse` hoặc `TryGetValue` ở đường đi dự kiến thường xuyên.

### Bắt exception ở đâu

Chỉ `catch` khi tầng hiện tại có thể làm ít nhất một việc có ý nghĩa:

- khôi phục hoặc thử phương án thay thế an toàn;
- chuyển lỗi sang abstraction phù hợp và giữ `InnerException`;
- thêm context rồi rethrow;
- biến lỗi thành response/exit code ở boundary của ứng dụng.

Để exception tự đi lên nếu method không biết xử lý. Một global handler ở process/API boundary có thể log và trả lỗi chuẩn, nhưng không thể tự động khôi phục mọi lỗi.

### Thứ tự `catch`

Đặt type cụ thể trước type cơ sở. `ArgumentOutOfRangeException` kế thừa `ArgumentException`; nếu bắt `ArgumentException` trước, nhánh cụ thể phía sau không thể tới được và compiler sẽ báo lỗi.

Tránh `catch (Exception)` trong logic thông thường. Nếu dùng ở boundary để tránh process chết không kiểm soát, phải log đủ correlation/context, trả trạng thái thất bại và không giả vờ thao tác đã thành công.

### Custom exception

Tên nên kết thúc bằng `Exception`. Chỉ tạo type mới khi caller cần phân biệt hoặc cần dữ liệu chuyên biệt. Message dành cho chẩn đoán, không phải contract để code parse. Đưa dữ liệu ổn định vào property như `Requested` và `Available`.

Không đặt password, access token, connection string hoặc dữ liệu cá nhân không cần thiết trong message/property vì exception có thể được log qua nhiều tầng.

## 6. Lỗi thường gặp

### Nuốt lỗi

```csharp
try { Save(); }
catch { }
```

Đoạn code làm caller tưởng `Save` thành công. Hãy xử lý cụ thể hoặc để exception đi lên.

### `throw exception;` khi chỉ muốn rethrow

Cách này làm mất vị trí lỗi gốc trong stack trace. Trong chính block `catch`, dùng `throw;`.

### Bọc exception nhưng bỏ nguyên nhân

`throw new OrderPersistenceException("Failed", exception)` giữ causal chain. Nếu bỏ `exception`, log chỉ còn message tổng quát.

### Bắt type quá rộng và tiếp tục chạy

Sau lỗi không dự kiến, state có thể đã thay đổi một phần. Không tiếp tục xử lý như thành công nếu chưa chứng minh được invariant còn đúng.

### Dùng exception cho validation hàng loạt

Ném exception cho từng dòng CSV sai định dạng gây code ồn và chậm. Thu thập `ValidationError` cho lỗi dự kiến; dành exception cho tình huống bất thường hoặc contract bị vi phạm.

### Log trùng ở mọi tầng

Nếu repository, service và boundary đều log cùng một exception, hệ thống tạo ba sự kiện cho một lỗi. Thường tầng giữa thêm context rồi rethrow; boundary chịu trách nhiệm log một lần theo policy.

### `finally` ném exception mới

Exception từ `finally` có thể che exception gốc. Cleanup nên nhỏ, an toàn; nếu có thể thất bại, thiết kế cách ghi nhận mà không phá causal information.

## 7. Bài tập

### Bài 1 — Parse ngày giao

Nhận ngày ở dạng text và trả thông báo validation nếu sai hoặc nằm trong quá khứ.

Gợi ý: dùng `DateOnly.TryParse`; không dùng exception cho input sai thường xuyên.

### Bài 2 — Guard cho chuyển tiền

Viết `Transfer(string sourceId, string destinationId, decimal amount)` với guard cho ID rỗng, hai tài khoản trùng nhau và số tiền không dương.

Gợi ý: chọn `ArgumentException`/`ArgumentOutOfRangeException` và điền đúng `paramName`.

### Bài 3 — Custom exception

Tạo `CreditLimitExceededException` có `Limit`, `CurrentDebt`, `RequestedAmount`; bắt riêng ở application boundary.

Gợi ý: code không parse `Message`; đọc các property có type rõ ràng.

### Bài 4 — Giữ nguyên nguyên nhân

Viết repository đọc một file JSON. Bọc `IOException` và `UnauthorizedAccessException` thành `CustomerDataException`, giữ `InnerException`.

Gợi ý: không bắt `Exception`; thử đường dẫn không có quyền và xem toàn bộ stack trace.

### Bài 5 — Cleanup an toàn

Tạo một class implement `IDisposable`, dùng cả `try/finally` và `using` để chứng minh `Dispose` chạy khi block ném lỗi.

Gợi ý: đặt breakpoint trong `Dispose`; so sánh code sau khi compiler hạ cú pháp `using` về ý tưởng `try/finally`.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi biết khi nào dùng `TryParse` thay vì exception.
- [ ] Tôi mô tả được đường đi qua `try`, `catch`, filter và `finally`.
- [ ] Tôi dùng `throw;` để giữ stack trace khi rethrow.
- [ ] Tôi giữ exception gốc trong `InnerException` khi đổi abstraction.
- [ ] Tôi viết được guard clause với đúng type và parameter name.
- [ ] Tôi không nuốt lỗi, log trùng hoặc để secret trong exception.
- [ ] Tôi đã build/run ví dụ và xem `orders.log` được tạo.

Bài prerequisite: [Struct, enum và tuple](./11-struct-enum-va-tuple.md).

Bài tiếp theo: [Collection: List, Dictionary, HashSet, Queue và Stack](./13-collection-list-dictionary-hashset-queue-stack.md).
