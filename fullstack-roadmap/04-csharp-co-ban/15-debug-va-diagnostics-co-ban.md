# Debug và diagnostics cơ bản trong C#

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, culture hoặc serialization; CI failure

## TL;DR

- Debug quan sát lần chạy; diagnostics để lại bằng chứng qua log và thời gian.
- Đặt breakpoint tại phép tính và theo call stack thay vì đoán từ output cuối.
- Debug.Assert không thay guard runtime; log che email một phần vẫn có dữ liệu cá nhân.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- đặt breakpoint có chủ đích và phân biệt Continue, Step Over, Step Into, Step Out;
- quan sát Locals, Watch và Call Stack mà không đoán state của chương trình;
- lần theo một giá trị sai từ caller tới method tạo ra nó;
- dùng conditional breakpoint/logpoint để giảm số lần dừng;
- hiểu vai trò cơ bản của symbol/PDB khi ánh xạ code đang chạy về source;
- dùng `Debug`, `Trace` và `Stopwatch` đúng phạm vi;
- ghi diagnostics có ID/context hữu ích nhưng không làm lộ password, token hoặc dữ liệu cá nhân;
- biết khi nào cần logging, metrics, tracing hoặc profiler chuyên dụng thay vì `Console.WriteLine`.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Kết quả hóa đơn sai giống tổng trên phiếu sai: cần dừng tại từng bước để xem input và phép tính. Khi chương trình đã chạy ở máy khác, log có mã lô giúp nối các bước liên quan.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| breakpoint | điểm debugger tạm dừng execution | CalculateSubtotal |
| call stack | chuỗi lời gọi dẫn tới điểm hiện tại | Main→Run→CalculateTotal |
| watch | biểu thức debugger đánh giá để quan sát | subtotal |
| correlation ID | mã gắn các sự kiện cùng công việc | batch_id |
| Stopwatch | đo khoảng thời gian trôi qua | invoice_duration |

### Ví dụ nhỏ — tính tay trước

2×750000+350000=1850000; giảm10%=185000; còn1665000. Nếu tính quantity sai ở dòng đầu, xem lineTotal trước khi xem discount.

Một batch tính hóa đơn trả tổng tiền thấp hơn dự kiến. Đoạn code có nhiều bước: cộng dòng hàng, áp dụng giảm giá, làm tròn và trả kết quả. Việc chèn `Console.WriteLine` vào mọi dòng vừa ồn, vừa dễ vô tình in email/token, lại không cho thấy chuỗi lời gọi.

Ta cần hai khả năng khác nhau:

1. Trong lúc phát triển, dừng đúng lần tính cần kiểm tra, xem biến và call stack.
2. Khi chương trình chạy không gắn debugger, ghi sự kiện/timing tối thiểu để biết batch nào chậm hoặc thất bại mà không lộ secret.

Ví dụ dưới đây đặt các vị trí breakpoint rõ ràng, đồng thời dùng `Debug`, `Trace` và `Stopwatch` theo vai trò riêng.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project `.NET 9`:

```bash
mkdir DebugDiagnosticsDemo
cd DebugDiagnosticsDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay toàn bộ `Program.cs`:

```csharp
using System;
using System.Collections.Generic;
using System.Diagnostics;

namespace DebugDiagnosticsDemo;

public sealed class InvoiceItem
{
    public string ProductId { get; }
    public int Quantity { get; }
    public decimal UnitPrice { get; }

    public InvoiceItem(string productId, int quantity, decimal unitPrice)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(productId);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(quantity);
        ArgumentOutOfRangeException.ThrowIfNegative(unitPrice);

        ProductId = productId;
        Quantity = quantity;
        UnitPrice = unitPrice;
    }
}

public static class SafeLogValue
{
    public static string MaskEmail(string email)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(email);

        int atIndex = email.IndexOf('@');
        return atIndex > 0
            ? $"{email[0]}***{email[atIndex..]}"
            : "***";
    }
}

public sealed class InvoiceService
{
    public decimal CalculateTotal(
        string batchId,
        IReadOnlyList<InvoiceItem> items,
        decimal discountRate)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(batchId);
        ArgumentNullException.ThrowIfNull(items);

        if (discountRate is < 0m or > 1m)
        {
            throw new ArgumentOutOfRangeException(nameof(discountRate));
        }

        // Debug output/assertion phục vụ development; không thay guard ở trên.
        Debug.WriteLine($"DEBUG item_count={items.Count}");
        Debug.Assert(discountRate is >= 0m and <= 1m);

        var stopwatch = Stopwatch.StartNew();

        try
        {
            decimal subtotal = CalculateSubtotal(items); // BREAKPOINT 1
            decimal total = ApplyDiscount(subtotal, discountRate); // BREAKPOINT 2

            Trace.TraceInformation(
                "event=invoice_calculated batch_id={0} item_count={1} total={2}",
                batchId,
                items.Count,
                total);

            return total;
        }
        catch (Exception exception)
        {
            // Chỉ ghi type và ID an toàn; message có thể chứa dữ liệu từ input.
            Trace.TraceError(
                "event=invoice_failed batch_id={0} error_type={1}",
                batchId,
                exception.GetType().Name);
            throw;
        }
        finally
        {
            stopwatch.Stop();
            Trace.TraceInformation(
                "event=invoice_duration batch_id={0} elapsed_ms={1:F3}",
                batchId,
                stopwatch.Elapsed.TotalMilliseconds);
        }
    }

    private static decimal CalculateSubtotal(IReadOnlyList<InvoiceItem> items)
    {
        decimal subtotal = 0m;

        for (int index = 0; index < items.Count; index++)
        {
            InvoiceItem item = items[index]; // BREAKPOINT 3: condition index == 1
            decimal lineTotal = item.Quantity * item.UnitPrice;
            subtotal += lineTotal;
        }

        return subtotal;
    }

    private static decimal ApplyDiscount(decimal subtotal, decimal discountRate)
    {
        decimal discount = subtotal * discountRate; // STEP INTO tới đây
        return decimal.Round(subtotal - discount, 2);
    }
}

public sealed class BatchRunner
{
    private readonly InvoiceService _invoiceService;

    public BatchRunner(InvoiceService invoiceService)
    {
        _invoiceService = invoiceService ??
            throw new ArgumentNullException(nameof(invoiceService));
    }

    public decimal Run(
        string batchId,
        string customerEmail,
        IReadOnlyList<InvoiceItem> items,
        decimal discountRate)
    {
        Trace.TraceInformation(
            "event=batch_started batch_id={0} customer={1}",
            batchId,
            SafeLogValue.MaskEmail(customerEmail));

        return _invoiceService.CalculateTotal(
            batchId,
            items,
            discountRate);
    }
}

internal static class Program
{
    private static void Main()
    {
        ConfigureDiagnostics();

        const string batchId = "BATCH-2026-001";
        InvoiceItem[] items =
        [
            new InvoiceItem("KEYBOARD", quantity: 2, unitPrice: 750_000m),
            new InvoiceItem("MOUSE", quantity: 1, unitPrice: 350_000m)
        ];

        var runner = new BatchRunner(new InvoiceService());
        decimal total = runner.Run(
            batchId,
            customerEmail: "learner@example.com",
            items,
            discountRate: 0.10m);

        Console.WriteLine($"Final total: {total:N0} VND");
    }

    private static void ConfigureDiagnostics()
    {
        // Demo console only. Ứng dụng production sẽ dùng ILogger/OpenTelemetry.
        Trace.Listeners.Clear();
        Trace.Listeners.Add(new ConsoleTraceListener(useErrorStream: false));
        Trace.AutoFlush = true;
    }
}
```

Build và chạy không gắn debugger:

```bash
dotnet build
dotnet run --no-build
```

Output có các event `batch_started`, `invoice_calculated`, `invoice_duration` và:

```text
Final total: 1,665,000 VND
```

Thời gian đo thay đổi theo máy. Email xuất hiện dưới dạng `l***@example.com`; code không nhận hoặc ghi token/password.

### Phiên debug có chủ đích

Mở folder/project trong Visual Studio, Rider hoặc VS Code có C# tooling, chọn cấu hình Debug rồi:

1. Đặt breakpoint tại comment `BREAKPOINT 1` và chạy debugger.
2. Xem `items`, `discountRate`, `batchId` trong Locals.
3. Thêm `items[1].Quantity * items[1].UnitPrice` vào Watch.
4. Step Into lời gọi `ApplyDiscount`; xem `subtotal`, `discountRate`, `discount`.
5. Mở Call Stack; chuỗi chính là `Main -> BatchRunner.Run -> InvoiceService.CalculateTotal -> ApplyDiscount`.
6. Đặt breakpoint tại `BREAKPOINT 3`, thêm condition `index == 1`, chạy lại và xác nhận chỉ dừng ở dòng hàng thứ hai.

Tên nút/phím tắt khác nhau giữa IDE; semantics của các thao tác vẫn giống nhau.

### Walkthrough — execution / state / cost

1. Main cấu hình Trace listener ra console rồi tạo hai InvoiceItem.
2. BatchRunner log batch_started với email đã che, service validate input.
3. for cộng lineTotal, ApplyDiscount làm tròn; log invoice_calculated.
4. finally ghi duration cả đường thành công hoặc exception. Object/input sống trong process; log I/O có cost và có thể lộ dữ liệu; timing một lần không đại diện performance.

### Mini-check

Nếu discountRate=1.1 trong Release, guard nào còn hoạt động khi Debug.Assert bị bỏ?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Breakpoint dừng trước statement

Debugger dùng thông tin symbol (thường là file `.pdb`) để ánh xạ source line tới code đã compile/JIT. Khi thread chạm breakpoint, thread bị tạm dừng **trước** khi statement tương ứng hoàn thành. Vì vậy tại `BREAKPOINT 1`, `subtotal` có thể chưa nhận kết quả cho tới khi Step Over xong lời gọi.

Các lệnh điều khiển:

| Lệnh | Hành vi |
|---|---|
| Continue | chạy tới breakpoint/exception tiếp theo hoặc kết thúc |
| Step Over | chạy statement hiện tại, không dừng trong method được gọi |
| Step Into | đi vào method được gọi nếu có source/symbol phù hợp |
| Step Out | chạy phần còn lại của method hiện tại và dừng ở caller |

### Locals, Watch và Call Stack

- **Locals/Variables** hiển thị parameter và local đang có trong stack frame được chọn.
- **Watch** đánh giá expression do bạn nhập trong context frame hiện tại.
- **Call Stack** cho biết chuỗi method dẫn tới vị trí dừng; chọn frame trên để xem state của caller.

### Stack frame, reference và object khi dừng

Khi dừng trong `CalculateSubtotal`, mô hình khái niệm là:

```text
Thread call stack
┌──────────────────────────────────────────────┐
│ CalculateSubtotal frame                     │
│ index, subtotal, lineTotal, item reference ──┼──┐
├──────────────────────────────────────────────┤  │
│ CalculateTotal frame                         │  │
│ batchId ref, items ref, discountRate         │  │
├──────────────────────────────────────────────┤  │
│ BatchRunner.Run frame                        │  │
├──────────────────────────────────────────────┤  │
│ Program.Main frame                           │  │
└──────────────────────────────────────────────┘  │
                                                  │
Managed heap                                      │
items array ──> [ref item #1, ref item #2]        │
                   │             └────────────────┘
                   └────────> InvoiceItem objects
```

Mỗi `new InvoiceItem(...)` tạo một object riêng trên heap. Array là object khác và giữ reference tới chúng. Biến local `item` chỉ sao chép một reference từ array; debugger sửa `item.Quantity` (nếu setter tồn tại) sẽ sửa object dùng chung, không phải một bản clone.

### Ba công cụ diagnostics trong ví dụ

`Debug.WriteLine` và `Debug.Assert` phục vụ lúc phát triển. Các lời gọi `Debug` được điều khiển bởi symbol `DEBUG`; không dùng assertion làm validation bắt buộc vì Release có thể không thực thi lời gọi đó.

`Trace.TraceInformation/Error` phát sự kiện cho listener. SDK thường định nghĩa symbol `TRACE`, kể cả Release, nhưng listener và cấu hình quyết định sự kiện đi đâu. Ví dụ gắn `ConsoleTraceListener` để tự chạy độc lập; backend production sẽ dùng `ILogger` và hệ thống thu thập log/traces chuẩn ở module sau.

`Stopwatch` đo elapsed time bằng nguồn thời gian đơn điệu phù hợp đo duration. `DateTime.Now` có thể nhảy khi đồng hồ hệ thống đồng bộ và không phải lựa chọn tốt để benchmark thời lượng.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| Breakpoint/Watch | quan sát phiên đang chạy | cần debugger, có thể làm thay timing |
| Trace log | bằng chứng sau sự kiện | cần correlation và policy dữ liệu |
| Debug.Assert | kiểm tra giả định lúc debug | có thể bị bỏ ở Release; không thay validation |

### Misconception check

**Đúng hay sai?** Release vẫn chạy mọi Debug.Assert như Debug.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: lời gọi conditional có thể bị compiler bỏ.

</details>

**Đúng hay sai?** Một elapsed_ms thấp đủ chứng minh thuật toán tối ưu.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: startup/JIT/cache/I/O và workload ảnh hưởng phép đo.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** breakpoint và call stack.

- **Working Developer — dùng khi làm việc:** log an toàn, guard và repro.

- **Deep Dive — có thể quay lại sau:** measurement khi có vấn đề thực.

### Debugger là công cụ kiểm tra giả thuyết

Trước khi đặt breakpoint, hãy viết giả thuyết cụ thể: “dòng thứ hai bị nhân sai quantity” hoặc “discount được áp dụng hai lần”. Đặt điểm dừng tại nơi value được tạo và nơi value được tiêu thụ; so sánh invariant tại từng ranh giới.

Một quy trình ngắn:

```text
Tái hiện ổn định -> khoanh input -> đặt breakpoint -> kiểm tra state/call stack
-> tìm statement đầu tiên sai -> sửa nguyên nhân -> chạy lại + thêm test
```

Đừng chỉ sửa value bằng debugger để phiên chạy “đúng”; thay đổi đó mất khi process kết thúc và không sửa source.

### Breakpoint hữu ích

- line breakpoint: dừng ở dòng source;
- conditional breakpoint: dừng khi expression đúng;
- hit count: dừng ở lần đi qua thứ `n`;
- exception breakpoint: dừng lúc exception được throw, trước khi code bắt nó;
- function/method breakpoint: dừng khi method cụ thể được gọi;
- logpoint/tracepoint: ghi thông tin không suspend thread.

### Diagnostics production-friendly

Một event hữu ích thường có:

- tên event ổn định như `invoice_calculated`;
- correlation/batch/request ID không nhạy cảm;
- số lượng, trạng thái, duration và error type cần thiết;
- timestamp/severity do logging infrastructure cung cấp.

Không log password, access/refresh token, API key, connection string, cookie/session ID, số thẻ hoặc payload cá nhân nguyên bản. Mask email trong ví dụ chỉ để minh họa; production cần data-classification và policy retention/access cụ thể. Khi không cần dữ liệu cá nhân để chẩn đoán, tốt nhất không thu thập.

`Trace` cơ bản không thay thế observability stack. Về sau:

- logs giải thích sự kiện rời rạc có context;
- metrics tổng hợp số lượng/latency/error rate;
- distributed traces nối request qua nhiều service;
- profiler đo CPU/allocation/call stack theo mẫu.

### Đào sâu (có thể quay lại sau)

Conditional breakpoint `index == 1` vẫn có overhead vì debugger phải kiểm tra điều kiện khi đi qua điểm đó, nhưng tránh dừng ở mọi iteration. Logpoint có thể ghi message mà không dừng; dùng nó có kiểm soát và không đưa secret vào expression.

Watch/property evaluation có thể gọi getter hoặc `ToString()`. Nếu các method đó có side effect hoặc tốn I/O, chỉ riêng việc quan sát có thể làm đổi behavior/timing. Production code nên giữ getter đơn giản, và người debug không nên gọi method thay đổi state chỉ để “xem thử”.

JIT có thể tối ưu local, inline method hoặc giữ value trong register, đặc biệt ở Release; một số biến có thể hiển thị là optimized away. Debug build thường dễ step và inspect hơn nhưng timing/performance không đại diện Release.

Không phải IDE/runtime nào cũng hỗ trợ mọi loại giống nhau. Breakpoint trong ứng dụng đa luồng có thể làm thay đổi timing và che/khơi ra race condition.

#### Đo hiệu năng đúng phạm vi

`Stopwatch` tốt để quan sát duration thô, không đủ cho microbenchmark tin cậy. Lần chạy đầu còn JIT, cache và GC làm nhiễu. Muốn kết luận tối ưu, đo Release, warm-up, nhiều iteration, dữ liệu đại diện và dùng công cụ benchmark/profiler phù hợp.

## 6. Lỗi thường gặp

### Dùng `Console.WriteLine` như logging production

Chuỗi tự do thiếu severity, event name, correlation và routing. Dùng abstraction logging của host khi sang ASP.NET Core; cấu trúc field để hệ thống truy vấn được.

### Log toàn bộ object/request

`ToString()` hoặc serialize nguyên request có thể làm lộ secret/PII và tạo log khổng lồ. Chỉ allow-list field cần thiết, redact/mask theo policy.

### Đặt breakpoint quá muộn

Nếu chỉ dừng tại chỗ output sai, nguyên nhân đã xảy ra trước đó. Theo data flow ngược tới statement đầu tiên biến value đúng thành sai.

### Nhầm Step Over với “bỏ qua” method

Step Over vẫn chạy toàn bộ method; nó chỉ không dừng ở từng dòng bên trong. Method vẫn có side effect và vẫn có thể ném exception.

### Tin rằng Debug và Release giống nhau về timing

Optimization, JIT, assertion và instrumentation khác nhau. Debug để hiểu correctness; đo performance trên cấu hình gần production.

### Đặt logic bắt buộc trong `Debug.Assert`

Assertion không thay guard/exception/test. Điều kiện an toàn nghiệp vụ phải chạy trong mọi build configuration.

### Đánh giá expression có side effect trong Watch

Gọi `queue.Dequeue()` hoặc method ghi database từ Watch làm đổi chương trình. Chỉ dùng expression quan sát thuần khiết nếu có thể.

### Bắt `Exception` rồi chỉ trace message

Message có thể thiếu context hoặc chứa input nhạy cảm. Ở boundary phù hợp, ghi event/correlation/type và giữ exception cho logger có policy; không nuốt lỗi.

## 7. Khi nào KHÔNG dùng

Không log toàn bộ object khách hàng để sửa một lỗi tổng tiền. Không dùng Watch gọi method có side effect khi đang tìm lỗi state; việc quan sát có thể làm đổi lần chạy.

## 8. Production notes & scale check

Gate tự động chạy Debug/Release, kiểm tra tổng, guard và log không chứa email đầy đủ. Breakpoint, Step Into và Watch trong IDE vẫn là bài thực hành cần người học/reviewer làm; verifier không chứng nhận thao tác UI đã xảy ra.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Theo dõi phép tính sai

Cố tình đổi `subtotal - discount` thành `subtotal + discount`, đặt breakpoint và tìm statement đầu tiên làm total sai.

Gợi ý: Watch `subtotal`, `discount`, `subtotal - discount`; dùng Step Into.

### Bài 2 — Conditional breakpoint

Tạo 100 dòng hàng, đặt condition dừng khi `item.UnitPrice > 1_000_000m`.

Gợi ý: thêm hit count và so sánh số lần debugger suspend.

### Bài 3 — Đọc call stack

Thêm `PricingPolicy.Apply` giữa `CalculateTotal` và `ApplyDiscount`, rồi ghi lại call stack tại dòng tính discount.

Gợi ý: chọn từng frame và quan sát locals thay đổi theo scope.

### Bài 4 — Safe diagnostics

Viết `PaymentAttempt` có `OrderId`, email, card token và amount; log một event thất bại an toàn.

Gợi ý: allow-list `OrderId`, amount, error type; không log token, chỉ mask email nếu thật sự cần.

### Bài 5 — Đo và không kết luận vội

Dùng `Stopwatch` so sánh hai cách nối chuỗi ở Debug và Release, có warm-up và nhiều vòng lặp.

Gợi ý: không in console trong vùng đo; ghi nhận GC/allocation và giải thích vì sao đây vẫn chưa phải benchmark chuẩn.

## 10. Bài tập tích hợp liên module — Judgment

Đối chiếu trace tay Module01 và debugger C/C++ Module03: chọn ba giá trị cần quan sát khi tổng lệch10%. Thu thập bằng chứng trước khi sửa công thức.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Step Over khác Step Into thế nào?
2. Guard nào tồn tại trong Release?
3. Mã batch giúp ghép log ra sao?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi đặt breakpoint dựa trên giả thuyết thay vì dừng ngẫu nhiên.
- [ ] Tôi phân biệt Continue, Step Over, Step Into và Step Out.
- [ ] Tôi đọc được Locals, Watch và Call Stack ở frame phù hợp.
- [ ] Tôi biết Watch có thể gây side effect.
- [ ] Tôi giải thích được object/reference nào đang được xem khi debugger dừng.
- [ ] Tôi phân biệt vai trò của `Debug`, `Trace` và `Stopwatch`.
- [ ] Tôi không dùng `Debug.Assert` thay validation bắt buộc.
- [ ] Tôi thiết kế event có ID/context mà không log secret/PII không cần thiết.
- [ ] Tôi đã build/run ví dụ và thực hiện ít nhất một phiên debug.

Bài prerequisite: [Project, solution, namespace và assembly](./14-project-solution-namespace-va-assembly.md).

Bài tiếp theo: [Dự án console C# quản lý công việc](./16-du-an-console-csharp-quan-ly-cong-viec.md).
