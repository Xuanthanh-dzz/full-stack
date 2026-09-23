# Composition over inheritance

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, invariant hoặc adapter; CI failure

## TL;DR

- Composition ghép các object qua contract thay vì tạo class cho mọi tổ hợp.
- Dùng cho kênh gửi, retry và log có các chiều thay đổi độc lập.
- Thứ tự wrapper thay ý nghĩa log; retry không tự an toàn với side effect.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- nhận ra dấu hiệu bùng nổ tổ hợp của một cây kế thừa;
- phân biệt quan hệ “là một” với “có một” và chọn đúng công cụ cho từng quan hệ;
- xây một hành vi bằng cách ghép nhiều object nhỏ qua constructor injection;
- viết wrapper thêm khả năng (retry, log) dùng lại được cho mọi implementation;
- vẽ object graph của một chuỗi ghép và giải thích lời gọi đi qua những object nào;
- nêu đúng chi phí của composition: nhiều object hơn, nhiều lớp gián tiếp hơn;
- biết khi nào kế thừa vẫn là lựa chọn hợp lý.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Thêm lớp ghi nhật ký quanh máy gửi và thêm lớp thử lại là hai lựa chọn riêng. Ta lắp từng lớp, không sản xuất một loại máy mới cho mọi tổ hợp.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| composition | object dùng object khác để làm việc | OrderNotifier có channel |
| delegation | chuyển lời gọi sang collaborator | _inner.Send |
| wrapper | bọc cùng hợp đồng để thêm behavior | LoggingChannel |
| fan-out | gọi nhiều đích | CompositeChannel |

### Ví dụ nhỏ — tính tay trước

Email false,false,true: Log(Retry(email,3)) ghi1 dòng; Retry(Log(email),3) ghi3 dòng. Composite vẫn gọi SMS dù email đã true.

Hệ thống đặt hàng cần báo cho khách khi đơn được đặt. Ban đầu chỉ có email:

```csharp
public class EmailNotifier { public void Send(string to, string message) { /* ... */ } }
```

Rồi yêu cầu tăng dần, mỗi lần một chút:

1. Thêm kênh SMS → `SmsNotifier`.
2. Kênh nào cũng có lúc lỗi tạm thời, cần thử lại vài lần → `EmailNotifierWithRetry`, `SmsNotifierWithRetry`.
3. Vận hành muốn ghi log mọi lần gửi → `EmailNotifierWithRetryAndLog`, `SmsNotifierWithRetryAndLog`, và cả hai bản không retry nữa.

Với 2 kênh và 2 khả năng bổ sung, cây kế thừa đã cần tới 8 class; thêm kênh Zalo là 12; thêm khả năng “giới hạn tần suất” là 24. Tệ hơn: code retry bị chép lại trong mỗi nhánh, nên sửa một lỗi retry phải sửa nhiều chỗ.

Vấn đề không nằm ở việc viết thêm class. Vấn đề là **các khả năng này độc lập với nhau**, còn kế thừa lại buộc phải chọn một đường duy nhất trong cây. Composition xử lý đúng dạng bài này: mỗi khả năng là một object nhỏ, và ta ghép chúng lúc chạy.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project `.NET 9`:

```bash
mkdir CompositionDemo
cd CompositionDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `CompositionDemo.csproj` bằng:

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

Sample dùng kênh giả lập để kết quả không phụ thuộc mạng: `FlakyEmailChannel` hỏng đúng một số lần đầu rồi thành công, `SmsChannel` luôn thành công.

Thay toàn bộ `Program.cs`:

```csharp
using System.Collections.Generic;

namespace CompositionDemo;

public interface INotificationChannel
{
    string Name { get; }

    bool Send(string recipient, string message);
}

// Kênh nền: chỉ biết gửi, không biết retry, không biết log.
public sealed class FlakyEmailChannel : INotificationChannel
{
    private readonly int _failuresBeforeSuccess;
    private int _attempts;

    public FlakyEmailChannel(int failuresBeforeSuccess)
    {
        ArgumentOutOfRangeException.ThrowIfNegative(failuresBeforeSuccess);
        _failuresBeforeSuccess = failuresBeforeSuccess;
    }

    public string Name => "email";

    public bool Send(string recipient, string message)
    {
        _attempts++;
        return _attempts > _failuresBeforeSuccess;
    }
}

public sealed class SmsChannel : INotificationChannel
{
    public string Name => "sms";

    public bool Send(string recipient, string message) => true;
}

// Wrapper 1: thêm khả năng thử lại cho BẤT KỲ kênh nào.
public sealed class RetryingChannel : INotificationChannel
{
    private readonly INotificationChannel _inner;
    private readonly int _maxAttempts;

    public RetryingChannel(INotificationChannel inner, int maxAttempts)
    {
        ArgumentNullException.ThrowIfNull(inner);
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(maxAttempts);

        _inner = inner;
        _maxAttempts = maxAttempts;
    }

    public string Name => $"retry({_inner.Name})";

    public bool Send(string recipient, string message)
    {
        for (int attempt = 0; attempt < _maxAttempts; attempt++)
        {
            if (_inner.Send(recipient, message))
            {
                return true;
            }
        }

        return false;
    }
}

// Wrapper 2: thêm khả năng ghi log cho BẤT KỲ kênh nào.
public sealed class LoggingChannel : INotificationChannel
{
    private readonly INotificationChannel _inner;
    private readonly ICollection<string> _log;

    public LoggingChannel(INotificationChannel inner, ICollection<string> log)
    {
        ArgumentNullException.ThrowIfNull(inner);
        ArgumentNullException.ThrowIfNull(log);

        _inner = inner;
        _log = log;
    }

    public string Name => $"log({_inner.Name})";

    public bool Send(string recipient, string message)
    {
        bool sent = _inner.Send(recipient, message);
        _log.Add($"{_inner.Name} -> {recipient}: {(sent ? "sent" : "failed")}");
        return sent;
    }
}

// Ghép nhiều kênh thành một: gửi hết, thành công nếu có ít nhất một kênh nhận.
public sealed class CompositeChannel : INotificationChannel
{
    private readonly IReadOnlyList<INotificationChannel> _channels;

    public CompositeChannel(params INotificationChannel[] channels)
    {
        ArgumentNullException.ThrowIfNull(channels);

        if (channels.Length == 0)
        {
            throw new ArgumentException("At least one channel is required.", nameof(channels));
        }

        _channels = channels;
    }

    public string Name => "composite";

    public bool Send(string recipient, string message)
    {
        bool anySucceeded = false;
        foreach (INotificationChannel channel in _channels)
        {
            anySucceeded |= channel.Send(recipient, message);
        }

        return anySucceeded;
    }
}

// Code nghiệp vụ chỉ biết INotificationChannel; nó không biết có retry hay log.
public sealed class OrderNotifier
{
    private readonly INotificationChannel _channel;

    public OrderNotifier(INotificationChannel channel)
    {
        ArgumentNullException.ThrowIfNull(channel);
        _channel = channel;
    }

    public bool NotifyPlaced(string recipient, string orderId, decimal total)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(recipient);
        ArgumentException.ThrowIfNullOrWhiteSpace(orderId);

        string message = $"Order {orderId} placed, total {total:N0} VND.";
        return _channel.Send(recipient, message);
    }
}

internal static class Program
{
    private static void Main()
    {
        var log = new List<string>();

        // Ghép lúc chạy: email hỏng 2 lần đầu, được bọc retry, rồi bọc log.
        INotificationChannel email = new LoggingChannel(
            new RetryingChannel(new FlakyEmailChannel(failuresBeforeSuccess: 2), maxAttempts: 3),
            log);

        INotificationChannel sms = new LoggingChannel(new SmsChannel(), log);

        var notifier = new OrderNotifier(new CompositeChannel(email, sms));
        bool notified = notifier.NotifyPlaced("an@example.com", "ORD-001", 1_850_000m);

        Console.WriteLine($"Notified: {notified}");

        // Cùng wrapper, kênh khác, không cần class mới nào.
        var smsOnly = new OrderNotifier(
            new LoggingChannel(new RetryingChannel(new SmsChannel(), maxAttempts: 2), log));
        Console.WriteLine($"SMS only: {smsOnly.NotifyPlaced("0900000000", "ORD-002", 350_000m)}");

        // Kênh hỏng hẳn: retry hết lượt vẫn thất bại.
        var broken = new OrderNotifier(
            new LoggingChannel(
                new RetryingChannel(new FlakyEmailChannel(failuresBeforeSuccess: 10), maxAttempts: 2),
                log));
        Console.WriteLine($"Broken email: {broken.NotifyPlaced("an@example.com", "ORD-003", 50_000m)}");

        Console.WriteLine("--- log ---");
        foreach (string entry in log)
        {
            Console.WriteLine($"  {entry}");
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
Notified: True
SMS only: True
Broken email: False
--- log ---
  retry(email) -> an@example.com: sent
  sms -> an@example.com: sent
  retry(sms) -> 0900000000: sent
  retry(email) -> an@example.com: failed
```

Project được kiểm tra bằng .NET SDK `9.0.121`, target `net9.0`, không dùng package ngoài.

### Walkthrough — execution / state / cost

1. Main ghép object graph một lần; tất cả wrapper dùng interface.
2. Retry gọi inner tối đa maxAttempts khi nhận false, dừng ngay khi true; exception đi lên.
3. Log ghi sau khi inner trả về nên inner ném thì không có dòng log của lần đó.
4. Composite dùng |= nên không short-circuit; giữ mảng caller và log dùng chung. Cost xấp xỉ số attempts nhân chi phí gửi, cộng wrapper/log allocation.

### Mini-check

Đổi |= thành anySucceeded = anySucceeded || channel.Send(...): kênh nào có thể không chạy?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Mỗi khả năng là một object, ghép lại lúc chạy

`RetryingChannel` không biết nó đang bọc email hay SMS; nó chỉ biết `INotificationChannel`. `LoggingChannel` cũng vậy. Nhờ đó, hai wrapper phục vụ mọi kênh hiện có và mọi kênh tương lai:

| Cách làm | Số class cần cho 3 kênh × 2 khả năng |
|---|---:|
| Kế thừa mỗi tổ hợp | 12 |
| Composition | 3 kênh + 2 wrapper = 5 |

Thêm kênh thứ tư: kế thừa cần thêm 4 class, composition cần thêm 1. Thêm khả năng thứ ba: kế thừa nhân đôi toàn bộ, composition thêm 1 wrapper.

### Lời gọi đi qua chuỗi object

Với nhánh email trong sample, `notifier.NotifyPlaced(...)` chạy qua:

```text
STACK (Main)                HEAP
notifier ─────────────────> OrderNotifier #1
                            └── _channel ──> CompositeChannel #1
                                              ├── [0] ──> LoggingChannel #1
                                              │            ├── _log ──> List<string> #1
                                              │            └── _inner ──> RetryingChannel #1
                                              │                            └── _inner ──> FlakyEmailChannel #1
                                              │                                            └── _attempts
                                              └── [1] ──> LoggingChannel #2
                                                           ├── _log ──> List<string> #1   (cùng list)
                                                           └── _inner ──> SmsChannel #1

Send("an@example.com", ...)
  CompositeChannel ──> LoggingChannel #1 ──> RetryingChannel #1 ──> FlakyEmailChannel #1  (lần 1: false)
                                          └────────────────────> FlakyEmailChannel #1  (lần 2: false)
                                          └────────────────────> FlakyEmailChannel #1  (lần 3: true)
                       LoggingChannel #1 ghi 1 dòng cho cả 3 lần thử
```

Hai `LoggingChannel` cùng trỏ tới **một** `List<string>` — mỗi `new` tạo object mới, nhưng reference thì chia sẻ được. Vì vậy log của cả hai kênh nằm chung một danh sách theo thứ tự gọi.

Chú ý dòng log của email chỉ có một, không phải ba: `LoggingChannel` bọc **ngoài** `RetryingChannel` nên nó chỉ thấy kết quả cuối cùng. Đảo thứ tự hai wrapper sẽ đổi ý nghĩa của log — thứ tự ghép là một quyết định thiết kế, không phải chi tiết ngẫu nhiên.

### “Là một” và “có một”

Câu hỏi để chọn công cụ:

- `CsvReceiptFormatter` **là một** `ReceiptFormatter` → kế thừa hợp lý (bài 2).
- `RetryingChannel` **có một** channel bên trong → composition.
- `OrderNotifier` **có một** channel → composition.

Thử áp kế thừa cho retry: `class RetryingEmailChannel : FlakyEmailChannel`. Nó buộc phải chọn đúng một lớp cha, nên không thể dùng lại cho SMS, và nó thừa hưởng cả những chi tiết nội bộ của email mà nó không cần.

### Delegation là cơ chế nền

Cả hai wrapper đều làm một việc: nhận lời gọi, làm thêm phần của mình, rồi **chuyển tiếp** cho object bên trong. Đó là delegation. Điểm khác biệt so với kế thừa:

| | Kế thừa | Composition + delegation |
|---|---|---|
| Quan hệ chốt lúc nào | biên dịch | chạy |
| Số “cha” | một | bao nhiêu cũng được |
| Truy cập nội bộ của thành phần kia | có (`protected`) | không, chỉ qua public API |
| Đổi hành vi lúc chạy | không | có, ghép lại là xong |

Việc wrapper chỉ dùng được public API của object bên trong là **ưu điểm**: nó không thể phá invariant của object đó.

### Đào sâu (có thể quay lại sau)

#### Tên gọi chính thức

Wrapper giữ nguyên interface và thêm hành vi có tên là **Decorator**; việc gộp nhiều object cùng interface thành một là **Composite**. Bạn không cần thuộc tên lúc này — [module 16](../PROGRESS.md#16-design-pattern) sẽ phân tích đầy đủ động lực, biến thể và chi phí. Điều quan trọng ở bài này là bạn tự suy ra được cấu trúc đó từ yêu cầu.

#### Chi phí của composition

- Nhiều object nhỏ hơn: mỗi wrapper là một lần `new` và một lần gọi gián tiếp.
- Stack trace dài hơn, và đọc code phải nhảy qua vài file mới thấy nơi làm việc thật.
- Nơi ghép (trong sample là `Main`) trở nên quan trọng: nó là **composition root**, và [bài 10](./10-dependency-injection-va-inversion-of-control.md) sẽ nói kỹ về nó.

Với hầu hết ứng dụng nghiệp vụ, chi phí này không đáng kể so với lợi ích. Ở hot path đã đo được, hãy cân nhắc gộp bớt tầng.

#### `params INotificationChannel[]` và mảng chia sẻ

`CompositeChannel` giữ trực tiếp mảng do caller truyền. Nếu caller còn giữ mảng đó và sửa phần tử sau này, `CompositeChannel` sẽ thấy thay đổi. Với code thư viện, hãy sao chép mảng vào một `List<T>` bên trong — đúng bài học “không để dữ liệu bên trong bị sửa từ ngoài” ở bài 1.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| inheritance theo tổ hợp | khóa nhánh type | bùng nổ khi nhiều chiều độc lập |
| composition | ghép các behavior | nhiều object/stack frame hơn |
| delegate | một callable nhỏ | đủ khi không cần Name và nhóm operation |

### Misconception check

**Đúng hay sai?** Composite chỉ gọi đến kênh thành công đầu tiên.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: sample fan-out tới mọi kênh nếu không có exception.

</details>

**Đúng hay sai?** Retry bắt mọi exception rồi thử tiếp.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: code chỉ retry kết quả false.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** vẽ chuỗi gọi.

- **Working Developer — dùng khi làm việc:** thứ tự wrapper và fault.

- **Deep Dive — có thể quay lại sau:** retry budget/idempotency khi có I/O thật.

### Bốn câu hỏi trước khi kế thừa

1. Lớp con có thật sự là một dạng của lớp cha, ở mọi ngữ cảnh caller dùng lớp cha không?
2. Lớp con có cần **tất cả** thành viên của lớp cha không?
3. Base có ổn định không, hay còn đổi liên tục?
4. Có bao nhiêu chiều biến đổi độc lập? Từ hai chiều trở lên là dấu hiệu bùng nổ tổ hợp.

Chỉ một câu trả lời “không” cũng đủ để cân nhắc composition.

### Các dạng composition thường gặp

| Dạng | Mô tả | Ví dụ trong bài |
|---|---|---|
| Wrapper cùng interface | thêm hành vi, giữ nguyên hợp đồng | `RetryingChannel`, `LoggingChannel` |
| Gộp nhiều thành một | fan-out tới nhiều implementation | `CompositeChannel` |
| Cộng tác viên | object giữ collaborator để nhờ việc | `OrderNotifier` giữ channel |
| Strategy truyền vào | chọn thuật toán bằng object/delegate | sẽ dùng ở [bài 5](./05-open-closed.md) |

### Composition bằng delegate

Không phải collaborator nào cũng cần interface. Nếu hợp đồng chỉ là một hàm, `Func<>`/`Action<>` (đã học ở [module 05, bài 2](../05-csharp-nang-cao/02-delegate-action-func-predicate.md)) là đủ:

```csharp
public sealed class OrderNotifier
{
    private readonly Func<string, string, bool> _send;

    public OrderNotifier(Func<string, string, bool> send) => _send = send;
}
```

Ưu điểm: gọn, dễ truyền lambda trong test. Nhược điểm: mất tên có nghĩa, và khi cần hai method liên quan thì phải truyền hai delegate. Nhiều hơn một hàm là lúc nên quay lại interface.

### Kế thừa vẫn đúng chỗ khi

- có phần khung ổn định và bắt buộc chung, như `ReceiptFormatterBase` ở bài 2;
- framework yêu cầu (ví dụ kế thừa một base class do thư viện định nghĩa);
- cần chia sẻ cả state lẫn hành vi mà việc tách ra sẽ tạo type vô nghĩa.

“Composition over inheritance” là **thứ tự ưu tiên khi cả hai đều dùng được**, không phải lệnh cấm kế thừa.

## 6. Lỗi thường gặp

### Kế thừa để dùng lại vài dòng code

Đây là nguyên nhân phổ biến nhất của cây kế thừa lệch lạc. Nếu chỉ cần một hàm tiện ích, hãy tách nó thành một type nhỏ hoặc một static method và dùng lại bằng composition.

### Wrapper phá hợp đồng của object bên trong

Nếu `RetryingChannel.Send` nuốt exception và trả `true`, caller sẽ tin là đã gửi được. Wrapper phải giữ đúng ý nghĩa của hợp đồng — đây chính là nội dung của [bài 6 về Liskov](./06-liskov-substitution.md).

### Ghép sai thứ tự rồi kết luận thiết kế sai

`Retry(Log(channel))` ghi một dòng cho mỗi lần thử; `Log(Retry(channel))` ghi một dòng cho cả lần gửi. Cả hai đều hợp lệ nhưng trả lời hai câu hỏi khác nhau. Hãy quyết định bạn cần loại log nào rồi ghép cho đúng.

### Chuỗi wrapper quá dài

Năm tầng wrapper thì việc debug trở nên khó chịu không kém cây kế thừa sâu. Giữ mỗi tầng có một lý do rõ, và đặt tên tầng theo lý do đó.

### Wrapper giữ state khiến không dùng lại được

`FlakyEmailChannel` trong sample giữ `_attempts` tích lũy qua nhiều lần gửi. Chỉ tạo instance mới khi muốn khởi động lại kịch bản lỗi giả lập. Nếu một wrapper có state như vậy được chia sẻ giữa nhiều luồng, kết quả sẽ sai. Khi một object được dùng chung, hãy giữ nó không có state thay đổi — bài [module 05, bài 11](../05-csharp-nang-cao/11-parallelism-concurrency-va-thread-safety.md) đã nói về ràng buộc này.

### Composition mà vẫn `new` bên trong

```csharp
public OrderNotifier() => _channel = new SmsChannel(); // vẫn dính chặt
```

Tự tạo một collaborator cố định bên trong làm giảm khả năng thay thế tại điểm đó: không thay được trong test, không đổi được lúc chạy. Hãy nhận collaborator qua constructor — [bài 8](./08-dependency-inversion.md) và [bài 10](./10-dependency-injection-va-inversion-of-control.md) sẽ đi sâu.

### Tạo interface cho mọi mảnh ghép

Không phải mọi thành phần đều cần abstraction. `StringBuilder` không cần `IStringBuilder`. Chỉ tách interface ở nơi thật sự cần thay implementation.

## 7. Khi nào KHÔNG dùng

Không retry thanh toán hoặc gửi không idempotent mà chưa xác định kết quả lần trước. Không thêm wrapper “dự phòng” khi một kênh cố định đã đủ.

## 8. Production notes & scale check

Kênh giả lập không gửi mạng, dùng tuần tự. Composite giữ array alias và chưa validate từng phần tử; caller phải cung cấp kênh không null và không thay mảng khi đang Send. Production cần ownership rõ, failure policy và retry budget/backoff theo driver.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Wrapper giới hạn số lần gửi

Viết `RateLimitedChannel` chỉ cho gửi tối đa `n` lần, các lần sau trả `false`. Ghép nó vào chuỗi hiện có mà không sửa class nào khác.

**Gợi ý:** giữ một bộ đếm private; thử đặt nó trong và ngoài `RetryingChannel` rồi so sánh kết quả.

### Bài 2 — Đảo thứ tự wrapper

Chạy lại sample với `RetryingChannel(new LoggingChannel(email, log), 3)` và giải thích khác biệt trong log.

**Gợi ý:** đếm số dòng log của lần gửi email đầu tiên trước khi chạy, rồi đối chiếu.

### Bài 3 — Từ cây kế thừa sang composition

Cho cây: `Report` → `PdfReport` → `PdfReportWithWatermark` → `PdfReportWithWatermarkAndCompression`. Hãy tách thành các thành phần ghép được và vẽ object graph cho bản “có watermark, không nén”.

**Gợi ý:** xác định đâu là hợp đồng chung, đâu là khả năng cộng thêm; watermark và nén có phụ thuộc nhau không?

### Bài 4 — Composite có chính sách khác

Sửa `CompositeChannel` thành hai phiên bản: một dừng ngay khi có kênh thành công, một yêu cầu mọi kênh đều thành công.

**Gợi ý:** đặt tên theo chính sách (`FirstSuccessChannel`, `AllRequiredChannel`); đừng thêm một `bool` để chọn giữa hai hành vi — bài 11 sẽ giải thích vì sao flag đó là mùi code.

### Bài 5 — Quyết định có lý do

Với ba tình huống: (a) `AdminUser` và `User`; (b) `CachedProductRepository` và `SqlProductRepository`; (c) `Button` và `RoundedButton` — chọn kế thừa hay composition và viết một câu lý do dựa trên bốn câu hỏi ở phần kiến thức nền.

**Gợi ý:** với (a), hỏi xem admin có phải chỉ là user có thêm quyền hay không, và quyền có đổi lúc chạy không.

## 10. Bài tập tích hợp liên module — Judgment

So callback Module02 và delegate Module05: wrapper giữ state nào sống qua lời gọi? Đặt log ở đâu nếu cần đếm attempt thay vì số thông báo?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Outer wrapper thấy bao nhiêu calls?
2. False và exception có cùng retry policy không?
3. Mảng channels có copy không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi nhận ra bùng nổ tổ hợp khi có từ hai chiều biến đổi độc lập.
- [ ] Tôi phân biệt “là một” và “có một” trước khi chọn công cụ.
- [ ] Tôi viết được wrapper dùng lại cho mọi implementation của một interface.
- [ ] Tôi vẽ được object graph và chỉ ra lời gọi đi qua những object nào.
- [ ] Tôi hiểu thứ tự ghép wrapper thay đổi ý nghĩa hành vi.
- [ ] Tôi nêu được chi phí của composition, không coi nó là lựa chọn miễn phí.
- [ ] Tôi build/run được sample trên `net9.0` và đối chiếu đúng output.

Điều hướng:

- Bài prerequisite: [Encapsulation, abstraction, inheritance và polymorphism](./02-encapsulation-abstraction-inheritance-polymorphism.md)
- Ôn lại nền tảng: [Abstract class, interface và composition](../04-csharp-co-ban/10-abstract-class-va-interface.md)
- Bài tiếp theo: [Single responsibility](./04-single-responsibility.md)
