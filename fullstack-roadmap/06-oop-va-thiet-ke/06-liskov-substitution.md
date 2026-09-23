# Liskov substitution

> **Last verified:** 2026-09-22  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, invariant hoặc adapter; CI failure

## TL;DR

- LSP yêu cầu subtype giữ lời hứa mà caller dựa vào.
- Viết precondition, kết quả và state sau lỗi trước khi chọn quan hệ kế thừa.
- Cùng signature chưa chứng minh thay thế được; job có thể đã làm một phần trước lỗi.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phát biểu nguyên tắc thay thế Liskov bằng ngôn ngữ hợp đồng, không chỉ bằng “lớp con thay được lớp cha”;
- nhận ra bốn dạng vi phạm: thắt chặt precondition, nới lỏng postcondition, phá invariant, thêm exception mới;
- thấy được hậu quả cụ thể khi một implementation nói dối hợp đồng: caller đúng vẫn hỏng;
- sửa vi phạm bằng cách tách khả năng thành hợp đồng riêng thay vì thêm `if` ở caller;
- giải thích ví dụ hình chữ nhật – hình vuông theo đúng bản chất của nó;
- phân biệt vi phạm Liskov với việc chỉ đơn giản là kế thừa sai;
- viết hợp đồng đủ rõ để người implement biết mình được phép làm gì.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một ổ cắm ghi “cắm là cấp điện hoặc báo chưa có nguồn” không thể thay bằng ổ cùng hình nhưng luôn làm nổ cầu dao. Caller làm đúng theo nhãn mà vẫn hỏng chính là lỗi hợp đồng.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| precondition | điều caller phải đáp ứng trước gọi | amount>0 |
| postcondition | lời hứa sau gọi | false giữ nguyên balance |
| subtype | type thay tại nơi nhận contract cha | CheckingAccount qua IWithdrawable |
| history constraint | cam kết về state theo thời gian | không đổi dữ liệu được hứa bất biến |

### Ví dụ nhỏ — tính tay trước

Fee50:ACC1trừ50 rồi ACC3ném; không tự trả50 cho ACC1. Với contract mới, tài khoản limit20 có thể false với reason dù đủ balance.

Ngân hàng nhỏ của cửa hàng có một lớp tài khoản:

```csharp
public class BankAccount
{
    // Hợp đồng: trừ tiền và trả true nếu đủ số dư; trả false nếu không đủ.
    public virtual bool Withdraw(decimal amount) { /* ... */ }
}
```

Một job cuối tháng thu phí dịch vụ trên **mọi** tài khoản:

```csharp
foreach (BankAccount account in accounts)
{
    if (account.Withdraw(fee)) { charged++; }
}
```

Job này chạy tốt nhiều tháng. Rồi nghiệp vụ thêm loại tài khoản tiền gửi có kỳ hạn — không cho rút trước hạn. Người viết chọn cách nhanh nhất:

```csharp
public sealed class FixedDepositAccount : BankAccount
{
    public override bool Withdraw(decimal amount) =>
        throw new NotSupportedException("Cannot withdraw from a fixed deposit.");
}
```

Về cú pháp, đây vẫn là một `BankAccount`. Về hợp đồng thì không: hợp đồng nói “trả `true`/`false`”, implementation lại ném exception. Job cuối tháng đang chạy đúng bỗng dừng giữa chừng, một số tài khoản đã bị trừ phí còn số còn lại thì chưa, và người sửa lỗi sẽ bị dụ thêm một dòng `if (account is FixedDepositAccount) continue;` vào job — tức là mỗi loại tài khoản mới lại phải sửa job.

Nguyên tắc Liskov mô tả đúng ràng buộc bị vi phạm ở đây: **nếu `S` là subtype của `T`, thì mọi chỗ dùng `T` phải thay bằng `S` được mà chương trình vẫn đúng**.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project `.NET 9`:

```bash
mkdir LiskovDemo
cd LiskovDemo
dotnet new console --framework net9.0 --use-program-main
```

Thay `LiskovDemo.csproj` bằng:

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

Sample chạy hai lần: bản vi phạm để thấy hậu quả, rồi bản đã sửa.

Thay toàn bộ `Program.cs`:

```csharp
using System.Collections.Generic;

namespace LiskovDemo;

// ============ PHẦN 1: thiết kế vi phạm Liskov ============

public class BankAccount
{
    private decimal _balance;

    public BankAccount(string id, decimal openingBalance)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentOutOfRangeException.ThrowIfNegative(openingBalance);

        Id = id.Trim().ToUpperInvariant();
        _balance = openingBalance;
    }

    public string Id { get; }

    public decimal Balance => _balance;

    // HỢP ĐỒNG: trừ amount và trả true nếu đủ số dư; trả false nếu không đủ.
    // Không ném exception cho trường hợp thiếu tiền.
    public virtual bool Withdraw(decimal amount)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(amount);

        if (amount > _balance)
        {
            return false;
        }

        _balance -= amount;
        return true;
    }
}

// Vi phạm 1: thêm exception mà hợp đồng không cho phép.
public sealed class FixedDepositAccount : BankAccount
{
    public FixedDepositAccount(string id, decimal openingBalance)
        : base(id, openingBalance)
    {
    }

    public override bool Withdraw(decimal amount) =>
        throw new NotSupportedException($"Account {Id} does not allow withdrawal.");
}

// Vi phạm 2: thắt chặt precondition rồi trả false — caller hiểu nhầm là thiếu tiền.
public sealed class DailyLimitAccount : BankAccount
{
    private readonly decimal _dailyLimit;

    public DailyLimitAccount(string id, decimal openingBalance, decimal dailyLimit)
        : base(id, openingBalance)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(dailyLimit);
        _dailyLimit = dailyLimit;
    }

    public override bool Withdraw(decimal amount) =>
        amount > _dailyLimit ? false : base.Withdraw(amount);
}

public static class MonthlyFeeJob
{
    public static string Run(IReadOnlyList<BankAccount> accounts, decimal fee)
    {
        int charged = 0;
        int skipped = 0;

        foreach (BankAccount account in accounts)
        {
            if (account.Withdraw(fee))
            {
                charged++;
            }
            else
            {
                skipped++;
            }
        }

        return $"charged={charged}, skipped={skipped}";
    }
}

// ============ PHẦN 2: thiết kế đã sửa ============

public interface IAccount
{
    string Id { get; }

    decimal Balance { get; }

    void Deposit(decimal amount);
}

// Khả năng rút tiền là một hợp đồng RIÊNG, chỉ type nào giữ được mới implement.
public interface IWithdrawable : IAccount
{
    // Trả true nếu đã trừ tiền; false nếu không thể trừ vì bất kỳ lý do nghiệp vụ nào.
    // Lý do được đưa ra qua reason để caller không phải đoán.
    bool TryWithdraw(decimal amount, out string reason);
}

public abstract class AccountBase : IAccount
{
    private decimal _balance;

    protected AccountBase(string id, decimal openingBalance)
    {
        ArgumentException.ThrowIfNullOrWhiteSpace(id);
        ArgumentOutOfRangeException.ThrowIfNegative(openingBalance);

        Id = id.Trim().ToUpperInvariant();
        _balance = openingBalance;
    }

    public string Id { get; }

    public decimal Balance => _balance;

    public void Deposit(decimal amount)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(amount);
        _balance += amount;
    }

    // Lớp con không chạm thẳng vào _balance; invariant "không âm" được giữ ở đây.
    protected bool TryDebit(decimal amount)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(amount);
        if (amount > _balance)
        {
            return false;
        }

        _balance -= amount;
        return true;
    }
}

public sealed class CheckingAccount : AccountBase, IWithdrawable
{
    public CheckingAccount(string id, decimal openingBalance)
        : base(id, openingBalance)
    {
    }

    public bool TryWithdraw(decimal amount, out string reason)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(amount);

        if (!TryDebit(amount))
        {
            reason = "insufficient funds";
            return false;
        }

        reason = "ok";
        return true;
    }
}

public sealed class LimitedCheckingAccount : AccountBase, IWithdrawable
{
    private readonly decimal _perTransactionLimit;

    public LimitedCheckingAccount(string id, decimal openingBalance, decimal perTransactionLimit)
        : base(id, openingBalance)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(perTransactionLimit);
        _perTransactionLimit = perTransactionLimit;
    }

    public bool TryWithdraw(decimal amount, out string reason)
    {
        ArgumentOutOfRangeException.ThrowIfNegativeOrZero(amount);

        if (amount > _perTransactionLimit)
        {
            reason = $"over per-transaction limit {_perTransactionLimit:N0}";
            return false;
        }

        if (!TryDebit(amount))
        {
            reason = "insufficient funds";
            return false;
        }

        reason = "ok";
        return true;
    }
}

// Không implement IWithdrawable: compiler ngăn nó lọt vào job thu phí.
public sealed class TermDepositAccount : AccountBase
{
    public TermDepositAccount(string id, decimal openingBalance, DateOnly maturity)
        : base(id, openingBalance)
    {
        Maturity = maturity;
    }

    public DateOnly Maturity { get; }
}

public static class FeeCollector
{
    public static string Collect(IReadOnlyList<IWithdrawable> accounts, decimal fee)
    {
        var report = new List<string>();
        foreach (IWithdrawable account in accounts)
        {
            bool ok = account.TryWithdraw(fee, out string reason);
            report.Add($"{account.Id}:{(ok ? "charged" : reason)}");
        }

        return string.Join(" | ", report);
    }
}

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine("--- thiết kế vi phạm ---");

        var risky = new List<BankAccount>
        {
            new BankAccount("acc-1", 500_000m),
            new DailyLimitAccount("acc-2", 500_000m, dailyLimit: 20_000m),
            new FixedDepositAccount("acc-3", 5_000_000m),
            new BankAccount("acc-4", 500_000m)
        };

        try
        {
            Console.WriteLine(MonthlyFeeJob.Run(risky, fee: 50_000m));
        }
        catch (NotSupportedException ex)
        {
            Console.WriteLine($"Job crashed: {ex.Message}");
        }

        foreach (BankAccount account in risky)
        {
            Console.WriteLine($"  {account.Id}: {account.Balance:N0}");
        }

        Console.WriteLine("--- thiết kế đã sửa ---");

        var withdrawable = new List<IWithdrawable>
        {
            new CheckingAccount("acc-1", 500_000m),
            new LimitedCheckingAccount("acc-2", 500_000m, perTransactionLimit: 20_000m),
            new CheckingAccount("acc-4", 30_000m)
        };

        var term = new TermDepositAccount("acc-3", 5_000_000m, new DateOnly(2027, 1, 1));

        Console.WriteLine(FeeCollector.Collect(withdrawable, fee: 50_000m));
        Console.WriteLine($"  term deposit {term.Id} untouched: {term.Balance:N0}");

        foreach (IWithdrawable account in withdrawable)
        {
            Console.WriteLine($"  {account.Id}: {account.Balance:N0}");
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
--- thiết kế vi phạm ---
Job crashed: Account ACC-3 does not allow withdrawal.
  ACC-1: 450,000
  ACC-2: 500,000
  ACC-3: 5,000,000
  ACC-4: 500,000
--- thiết kế đã sửa ---
ACC-1:charged | ACC-2:over per-transaction limit 20,000 | ACC-4:insufficient funds
  term deposit ACC-3 untouched: 5,000,000
  ACC-1: 450,000
  ACC-2: 500,000
  ACC-4: 30,000
```

Project được kiểm tra bằng .NET SDK `9.0.121`, target `net9.0`, không dùng package ngoài.

### Walkthrough — execution / state / cost

1. Bản cũ chạy tuần tự qua base virtual; ACC2 nói false khác nghĩa và ACC3 ném.
2. Bản mới chỉ nhận IWithdrawable; TermDeposit không convert được vào vai ấy.
3. TryWithdraw validate rồi TryDebit bảo vệ số dương/đủ balance ở base.
4. Balances thuộc từng object; Collect tạo report O(n). Không transaction toàn danh sách và không exactly-once khi chạy job lại.

### Mini-check

Bộ test chung nên assert gì khi LimitedCheckingAccount từ chối một amount nhỏ hơn balance?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### Hậu quả nằm ở dữ liệu, không chỉ ở exception

Đọc kỹ output của bản vi phạm: `ACC-1` đã bị trừ `50.000`, `ACC-4` thì chưa, vì job chết ở `ACC-3` trước khi tới nó. Đây mới là thiệt hại thật — hệ thống rơi vào trạng thái nửa vời, và chạy lại job sẽ trừ `ACC-1` lần thứ hai.

`ACC-2` là vi phạm âm thầm hơn: `DailyLimitAccount` trả `false` vì vượt hạn mức, nhưng hợp đồng của `BankAccount.Withdraw` định nghĩa `false` là “không đủ số dư”. Job đếm nó vào cột `skipped` như một tài khoản hết tiền, trong khi tài khoản còn `500.000`. Không có exception nào, không có log nào, chỉ có một con số báo cáo sai.

### Bốn quy tắc của hợp đồng subtype

| Quy tắc | Nghĩa là | Vi phạm trong sample |
|---|---|---|
| Precondition không được thắt chặt | lớp con không được đòi hỏi thêm điều kiện đầu vào | `DailyLimitAccount` yêu cầu `amount <= limit` |
| Postcondition không được nới lỏng | lớp con phải hứa ít nhất bằng lớp cha | `false` không còn nghĩa là “thiếu tiền” |
| Invariant phải được giữ | mọi điều luôn đúng ở lớp cha vẫn phải đúng | (bản sửa giữ invariant qua `TryDebit`) |
| Không thêm exception mới | lớp con không ném loại lỗi mà hợp đồng chưa nêu | `FixedDepositAccount` ném `NotSupportedException` |

Cách nhớ: lớp con được phép **nhận nhiều hơn và hứa nhiều hơn**, không được phép nhận ít hơn hoặc hứa ít hơn.

### Vì sao bản sửa không cần `if` ở caller

Bản sửa tách “có tài khoản” khỏi “rút được tiền”:

```text
IAccount              (Id, Balance, Deposit)
   ▲          ▲
   │          │
   │       IWithdrawable   (TryWithdraw)
   │              ▲     ▲
   │              │     │
TermDeposit  Checking  LimitedChecking
```

`FeeCollector.Collect` nhận `IReadOnlyList<IWithdrawable>`. `TermDepositAccount` **không compile được** vào danh sách đó. Lỗi được phát hiện lúc biên dịch, không phải lúc chạy job cuối tháng.

Ngoài ra, `TryWithdraw` có thêm `out string reason` nên hợp đồng đủ chỗ cho nhiều lý do từ chối khác nhau. `LimitedCheckingAccount` không phải nói dối: nó trả `false` kèm lý do đúng, và caller phân biệt được “vượt hạn mức” với “thiếu tiền”.

### Invariant được giữ ở đúng một nơi

`AccountBase` để `_balance` là `private` và chỉ mở ra `protected bool TryDebit`. Lớp con muốn trừ tiền phải đi qua đó, nên bất biến “số dư không âm” đúng cho mọi lớp con hiện tại và tương lai. Nếu để `protected decimal _balance`, mỗi lớp con lại có thể tự trừ và tự phá invariant — đúng lỗi đã nêu ở [bài 2](./02-encapsulation-abstraction-inheritance-polymorphism.md).

### Đào sâu (có thể quay lại sau)

#### Hình chữ nhật và hình vuông

Ví dụ kinh điển: `Square : Rectangle`. Về toán học, hình vuông **là một** hình chữ nhật. Về hợp đồng lập trình thì không, nếu `Rectangle` có setter riêng cho `Width` và `Height`, vì caller được quyền tin:

```text
r.Width = 5; r.Height = 4;  =>  r.Area == 20
```

Với `Square`, đặt `Height` phải đổi luôn `Width`, nên `Area` thành `16`. Postcondition mà `Rectangle` hứa đã bị phá.

Điểm mấu chốt: vi phạm không nằm ở quan hệ toán học mà nằm ở **hợp đồng có thể thay đổi độc lập hai chiều**. Bất biến loại bỏ lỗi setter đổi hai chiều cùng lúc, nhưng vẫn phải kiểm tra hợp đồng các method. Ví dụ `WithWidth` phải được phép trả một `Rectangle` không vuông; nếu subtype hứa luôn trả `Square` và ép hai chiều bằng nhau thì lỗi vẫn còn. Bất biến làm Liskov dễ giữ hơn rất nhiều.

#### History constraint

Một dạng vi phạm khó thấy: lớp cha hứa “object này không đổi sau khi tạo”, lớp con lại thêm method đổi state. Caller đang cache object đó vì tin nó bất biến sẽ nhận dữ liệu sai. Ràng buộc này gọi là history constraint và không thể phát hiện bằng cách chỉ nhìn chữ ký method.

#### Liskov áp dụng cả với interface

Nguyên tắc không giới hạn ở kế thừa class. Một `INotificationChannel` trả `true` khi chưa thực sự gửi được (ví dụ chỉ mới đưa vào hàng đợi) là vi phạm y hệt, dù không có `class ... : ...` nào. Hợp đồng ở đâu thì Liskov ở đó.

#### Kiểm tra bằng test dùng chung

Cách thực dụng để phát hiện vi phạm: viết một bộ test cho **hợp đồng**, rồi chạy bộ test đó với mọi implementation. Nếu một implementation cần test riêng để “bỏ qua trường hợp này”, đó chính là dấu hiệu vi phạm. Kỹ thuật viết bộ test dùng chung sẽ có ở [module 14](../PROGRESS.md#14-testing-chat-luong).

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| kế thừa hình thức | compiler thấy quan hệ type | chưa bảo đảm behavior |
| tách capability | chỉ type đáp ứng mới implement | phát hiện sai vai lúc compile |
| nới contract | false có nhiều lý do hợp lệ | caller phải xử lý reason thay vì giả định thiếu tiền |

### Misconception check

**Đúng hay sai?** IWithdrawable buộc mọi amount trong balance đều thành công.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: contract cho phép lý do nghiệp vụ khác.

</details>

**Đúng hay sai?** Rectangle bất biến tự làm mọi Square hợp LSP.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: vẫn phải kiểm lời hứa WithWidth/WithHeight và kiểu kết quả.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** caller và lời hứa.

- **Working Developer — dùng khi làm việc:** contract tests dùng chung.

- **Deep Dive — có thể quay lại sau:** history và failure semantics.

### Hợp đồng của một method gồm những gì

- **Precondition:** caller phải bảo đảm gì trước khi gọi.
- **Postcondition:** method bảo đảm gì sau khi chạy xong.
- **Invariant:** điều gì luôn đúng trước và sau mọi thao tác công khai.
- **Lỗi:** những loại lỗi nào có thể xảy ra và được báo ra sao.

Ba phần đầu quen thuộc; phần thứ tư hay bị bỏ quên và lại là nguồn vi phạm phổ biến nhất. [Bài 13](./13-design-by-contract-va-invariant.md) sẽ viết hợp đồng một cách hệ thống.

### Dấu hiệu vi phạm Liskov trong code

- Caller có `if (x is ConcreteType)` hoặc `switch` theo type để “xử lý riêng”.
- Một implementation ném `NotSupportedException` hoặc `NotImplementedException`.
- Tài liệu của lớp con có câu “không dùng method này”.
- Một override để thân method rỗng, âm thầm không làm gì.
- Test của lớp con phải bỏ qua vài trường hợp mà lớp cha vượt qua.

### Ba cách sửa

| Cách | Khi nào phù hợp |
|---|---|
| Tách khả năng thành interface riêng | khi chỉ một phần type giữ được hợp đồng (dùng trong sample) |
| Nới hợp đồng của lớp cha | khi từ chối là kết quả hợp lệ của mọi implementation |
| Bỏ quan hệ subtype, dùng composition | khi hai type thật ra không cùng họ |

Cách thứ hai đáng cân nhắc: nếu hợp đồng gốc là `TryWithdraw` trả `bool` kèm lý do ngay từ đầu, `FixedDepositAccount` đã có thể trả `false, "fixed deposit"` mà không nói dối. Hợp đồng rộng vừa đủ giúp tránh vi phạm về sau.

### Liskov và các nguyên tắc lân cận

- Không có Liskov thì open/closed sụp đổ: caller buộc phải biết type cụ thể.
- Interface segregation ([bài 7](./07-interface-segregation.md)) là công cụ chính để sửa vi phạm — tách hợp đồng lớn thành các vai nhỏ.
- Kế thừa sai kiểu “dùng lại code” ([bài 3](./03-composition-over-inheritance.md)) thường kéo theo vi phạm Liskov, vì lớp con vốn không thuộc cùng họ.

## 6. Lỗi thường gặp

### Ném `NotSupportedException` cho method không dùng tới

Đây là cách nhanh nhất để thỏa mãn compiler và cũng là cách nhanh nhất để phá caller. Nếu một type không giữ nổi một phần hợp đồng, phần đó không thuộc hợp đồng của nó.

### Trả giá trị “có vẻ hợp lệ” cho trường hợp không xử lý được

Trả `false`, `null` hoặc `0` để tránh exception có thể còn tệ hơn, vì lỗi trở nên vô hình. Hãy chọn giá trị trả về có khả năng diễn đạt lý do, như `out string reason` trong sample.

### Override rồi bỏ trống thân method

```csharp
public override void Refresh() { }
```

Caller gọi `Refresh` và tin dữ liệu đã mới. Nếu “không làm gì” là hành vi đúng, hãy ghi rõ điều đó trong hợp đồng của lớp cha.

### Thêm điều kiện đầu vào ở lớp con

Lớp cha nhận mọi số dương, lớp con chỉ nhận số nhỏ hơn hạn mức. Caller viết theo hợp đồng của lớp cha sẽ thất bại không báo trước. Nếu điều kiện đó là nghiệp vụ thật, nó phải nằm trong hợp đồng gốc.

### Dùng `is`/`as` ở caller để vá

Mỗi lần thêm một `if (account is FixedDepositAccount)` là một lần abstraction mất giá trị. Sau vài lần, caller phải biết toàn bộ danh sách type con — đúng thứ mà polymorphism sinh ra để tránh.

### Coi mọi quan hệ “là một” trong đời thật là subtype hợp lệ

Chim là động vật, chim cánh cụt là chim, nhưng nếu hợp đồng của “chim” có `Fly()` thì chim cánh cụt phá hợp đồng. Quan hệ trong code là quan hệ giữa **các hợp đồng**, không phải giữa các khái niệm ngoài đời.

### Quên rằng property cũng có hợp đồng

Một lớp con làm `Balance` trả giá trị đã làm tròn hoặc trả `0` khi tài khoản bị khóa cũng là vi phạm. Caller cộng dồn số dư sẽ ra tổng sai.

## 7. Khi nào KHÔNG dùng

Không thêm if cụ thể vào mọi caller để vá contract sai. Không dùng ví dụ toán học thay việc đọc API mutation thật.

## 8. Production notes & scale check

Sample không ngân hàng thật. Test chung cả hai implementation: số âm bị chặn, success giảm đúng tiền, false không đổi state; thêm subclass thử gọi protected TryDebit âm để kiểm guard tập trung. Compiler chặn TermDeposit vào list rút tiền.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Tìm vi phạm

Trong bản vi phạm ở sample, chỉ ra chính xác dòng nào phá quy tắc nào trong bốn quy tắc hợp đồng, và hậu quả tương ứng trong output.

**Gợi ý:** so sánh số dư `ACC-1` và `ACC-4` sau khi job chết; hậu quả nào không có exception nào báo?

### Bài 2 — Nới hợp đồng thay vì tách interface

Sửa `BankAccount.Withdraw` thành `TryWithdraw(decimal amount, out string reason)` cho phép mọi lý do từ chối, rồi cho `FixedDepositAccount` trả `false` với lý do đúng. So sánh hai hướng sửa.

**Gợi ý:** hướng nào phát hiện lỗi lúc biên dịch, hướng nào lúc chạy? Hướng nào dễ thêm loại tài khoản mới hơn?

### Bài 3 — Hình chữ nhật bất biến

Viết `Rectangle` bất biến với method `WithWidth`/`WithHeight` trả object mới, rồi thử cho `Square` kế thừa. Nêu điều kiện để không vi phạm: phép biến đổi có được trả `Rectangle` không vuông hay buộc giữ `Square`?

**Gợi ý:** viết assertion `r.WithWidth(5).WithHeight(4).Area == 20` và chạy với cả hai type.

### Bài 4 — Bộ test cho hợp đồng

Viết một method `CheckContract(IWithdrawable account)` kiểm tra: rút quá số dư trả `false`, rút thành công giảm đúng số dư; rút bị từ chối giữ nguyên state, rút số âm ném `ArgumentOutOfRangeException`. Chạy nó với cả hai implementation.

**Gợi ý:** dùng `if (...) throw new InvalidOperationException("contract violated: ...")`; công cụ test thật sẽ học ở module 14.

### Bài 5 — Vi phạm trong wrapper

Quay lại `RetryingChannel` ở [bài 3](./03-composition-over-inheritance.md). Hãy viết một phiên bản vi phạm Liskov, mô tả caller nào bị hỏng, rồi sửa lại.

**Gợi ý:** thử để wrapper nuốt exception và trả `true`; ai là người tin vào giá trị trả về đó?

## 10. Bài tập tích hợp liên module — Judgment

Liên hệ variance Module05: conversion hợp kiểu có chứng minh semantics và exception policy không? So wrapper retry với contract gửi thành công khi chưa gửi.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. False nghĩa gì trong hai thiết kế?
2. Job lỗi có rollback không?
3. Protected method phải validate gì?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phát biểu Liskov theo hợp đồng: precondition, postcondition, invariant và lỗi.
- [ ] Tôi chỉ ra được hậu quả dữ liệu của một vi phạm, không chỉ hậu quả exception.
- [ ] Tôi nhận ra vi phạm âm thầm khi giá trị trả về đổi ý nghĩa.
- [ ] Tôi sửa vi phạm bằng cách tách khả năng thành hợp đồng riêng.
- [ ] Tôi giải thích được ví dụ hình chữ nhật – hình vuông theo hợp đồng.
- [ ] Tôi coi `is`/`as` ở caller là dấu hiệu abstraction đang hỏng.
- [ ] Tôi build/run được sample trên `net9.0` và đối chiếu đúng output.

Điều hướng:

- Bài prerequisite: [Open/closed](./05-open-closed.md)
- Ôn lại nền tảng: [Exception và xử lý lỗi](../04-csharp-co-ban/12-exception-va-xu-ly-loi.md)
- Bài tiếp theo: [Interface segregation](./07-interface-segregation.md)
