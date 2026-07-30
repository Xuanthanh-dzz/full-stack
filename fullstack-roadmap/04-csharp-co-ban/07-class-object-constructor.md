# Class, object và constructor

## 1. Mục tiêu

Sau bài này, bạn có thể:

- Khai báo một `class`, tạo object bằng `new` và gọi instance member.
- Phân biệt class (kiểu/thiết kế), object (instance trong bộ nhớ) và reference (giá trị dùng để truy cập object).
- Viết constructor có validation, constructor overload và constructor chaining bằng `this(...)`.
- Dùng `this` để chỉ object hiện tại và xử lý trường hợp parameter trùng tên field.
- Phân biệt instance field với `static` field/member.
- Giải thích rõ: mỗi lần `new` thành công tạo một object riêng; phép gán reference không tạo object mới.

## 2. Bài toán mở đầu

Một ứng dụng ngân hàng cần quản lý hai tài khoản. Mỗi tài khoản phải có:

- Chủ tài khoản, loại tiền và số dư riêng.
- Mã tài khoản tự tăng dùng chung quy tắc cấp số.
- Trạng thái hợp lệ ngay sau khi được tạo: chủ tài khoản không rỗng, số dư mở không âm.
- Các thao tác nạp, rút và chuyển tiền không làm số dư âm.

Nếu chỉ dùng các biến rời như `owner1`, `balance1`, `owner2`, `balance2`, rất dễ truyền nhầm số dư của người này với tên người kia. Ta cần gom dữ liệu và hành vi của một tài khoản thành một object có ranh giới rõ ràng.

## 3. Lời giải bằng code

Tạo project .NET 9:

```bash
mkdir csharp-class-demo
cd csharp-class-demo
dotnet new console --framework net9.0
# Thay toàn bộ Program.cs bằng code bên dưới.
dotnet build
dotnet run
```

`Program.cs`:

```csharp
using System;

internal static class Program
{
    private static void Main()
    {
        // Mỗi biểu thức new bên dưới tạo một BankAccount object riêng.
        BankAccount anAccount = new BankAccount("An", 2_000_000m);
        BankAccount binhAccount = new BankAccount("Binh", 1_000_000m, "VND");

        anAccount.Deposit(500_000m);
        anAccount.TransferTo(binhAccount, 700_000m);

        anAccount.PrintSummary();
        binhAccount.PrintSummary();

        Console.WriteLine($"So object da tao: {BankAccount.CreatedCount}");
        Console.WriteLine(
            $"Hai lan new co cung object? " +
            $"{ReferenceEquals(anAccount, binhAccount)}");

        // Phép gán này chỉ copy reference, không gọi constructor và không tạo object.
        BankAccount aliasOfAn = anAccount;
        aliasOfAn.Deposit(100_000m);

        Console.WriteLine(
            $"aliasOfAn va anAccount cung object? " +
            $"{ReferenceEquals(aliasOfAn, anAccount)}");
        Console.WriteLine($"So du An doc qua anAccount: {anAccount.Balance:N0} VND");
        Console.WriteLine($"So object van la: {BankAccount.CreatedCount}");
    }
}

internal sealed class BankAccount
{
    // Chỉ có một bản sao cho cả type BankAccount.
    private static int s_lastAccountNumber = 1_000;

    // Mỗi object có một bản sao riêng của các instance field này.
    private decimal _balance;

    public static int CreatedCount { get; private set; }

    public int Number { get; }
    public string Owner { get; }
    public string Currency { get; }
    public decimal Balance => _balance;

    // Overload tiện dụng chuyển việc khởi tạo sang constructor đầy đủ.
    public BankAccount(string owner, decimal openingBalance)
        : this(owner, openingBalance, "VND")
    {
    }

    public BankAccount(string owner, decimal openingBalance, string currency)
    {
        if (string.IsNullOrWhiteSpace(owner))
        {
            throw new ArgumentException("Owner must not be empty.", nameof(owner));
        }

        if (openingBalance < 0m)
        {
            throw new ArgumentOutOfRangeException(
                nameof(openingBalance),
                "Opening balance must not be negative.");
        }

        if (string.IsNullOrWhiteSpace(currency))
        {
            throw new ArgumentException("Currency must not be empty.", nameof(currency));
        }

        s_lastAccountNumber++;
        Number = s_lastAccountNumber;

        // this là reference tới object đang được khởi tạo.
        this.Owner = owner.Trim();
        this.Currency = currency.Trim().ToUpperInvariant();
        this._balance = openingBalance;

        CreatedCount++;
    }

    public void Deposit(decimal amount)
    {
        EnsurePositive(amount);
        this._balance += amount;
    }

    public void Withdraw(decimal amount)
    {
        EnsurePositive(amount);

        if (amount > _balance)
        {
            throw new InvalidOperationException("Insufficient balance.");
        }

        _balance -= amount;
    }

    public void TransferTo(BankAccount destination, decimal amount)
    {
        ArgumentNullException.ThrowIfNull(destination);

        if (ReferenceEquals(this, destination))
        {
            throw new InvalidOperationException("Cannot transfer to the same account.");
        }

        if (!string.Equals(Currency, destination.Currency, StringComparison.Ordinal))
        {
            throw new InvalidOperationException("Currencies must match.");
        }

        Withdraw(amount);
        destination.Deposit(amount);
    }

    public void PrintSummary()
    {
        Console.WriteLine(
            $"#{Number} | {Owner,-5} | {Balance,12:N0} {Currency}");
    }

    private static void EnsurePositive(decimal amount)
    {
        if (amount <= 0m)
        {
            throw new ArgumentOutOfRangeException(
                nameof(amount),
                "Amount must be positive.");
        }
    }
}
```

Kết quả chính:

```text
#1001 | An    |    1,800,000 VND
#1002 | Binh  |    1,700,000 VND
So object da tao: 2
Hai lan new co cung object? False
aliasOfAn va anAccount cung object? True
So du An doc qua anAccount: 1,900,000 VND
So object van la: 2
```

## 4. Giải thích cơ chế

### 4.1 Class, object và reference là ba khái niệm khác nhau

Trong khai báo:

```csharp
BankAccount anAccount = new BankAccount("An", 2_000_000m);
```

- `BankAccount` bên trái là **type** được compiler dùng để kiểm tra thao tác hợp lệ.
- `new BankAccount(...)` tạo và khởi tạo một **object** ở managed memory.
- `anAccount` là biến chứa một **reference** cho phép code tìm đến object đó.

Class mô tả các member mà mọi instance có: field, property, method và constructor. Class không phải object đang chạy. Object là một instance cụ thể của class.

### 4.2 Mỗi lần `new` tạo một vùng nhớ object riêng

Hai câu lệnh:

```csharp
BankAccount anAccount = new BankAccount("An", 2_000_000m);
BankAccount binhAccount = new BankAccount("Binh", 1_000_000m, "VND");
```

gọi `new` hai lần, nên có hai object riêng:

```text
Stack frame Main                       Managed heap
+----------------------+               +-----------------------------+
| anAccount: reference -+-------------->| BankAccount object A        |
|                      |               | Number=1001                 |
|                      |               | Owner -> "An"              |
|                      |               | _balance=1,800,000          |
|                      |               +-----------------------------+
| binhAccount: ref -----+-------------->| BankAccount object B        |
+----------------------+               | Number=1002                 |
                                       | Owner -> "Binh"            |
                                       | _balance=1,700,000          |
                                       +-----------------------------+
```

`anAccount.Deposit(...)` thay `_balance` của object A, không thay object B. Các instance field nằm trong từng object và mỗi object giữ trạng thái riêng.

Mô hình “local reference ở stack, object ở heap” giúp học ngữ nghĩa. JIT có thể tối ưu vị trí vật lý (ví dụ giữ local trong register). Điều không đổi là object A và B có identity riêng.

### 4.3 Gán reference không tạo object

```csharp
BankAccount aliasOfAn = anAccount;
```

chỉ copy giá trị reference:

```text
Stack frame Main                       Managed heap
+----------------------+               +-----------------------------+
| anAccount: reference -+------------->| BankAccount object A        |
| aliasOfAn: reference -+------------->| _balance=1,900,000          |
+----------------------+               +-----------------------------+
```

Không có `new`, constructor không chạy, `CreatedCount` không tăng. Gọi `aliasOfAn.Deposit(...)` tác động lên chính object cũng được thấy qua `anAccount`.

### 4.4 `new` và constructor phối hợp ra sao?

Ở mức khái niệm, khi `new BankAccount(...)` thành công:

1. Runtime cấp vùng nhớ cho object và gán default value cho field (`0`, `false`, `null`, ...).
2. Field initializer và constructor chain của base type được thực thi theo quy tắc ngôn ngữ.
3. Constructor phù hợp của `BankAccount` chạy để thiết lập invariant.
4. Reference tới object đã khởi tạo được trả về cho biểu thức `new`.

Constructor có cùng tên class, không khai báo return type, và chỉ được gọi trong quá trình tạo object/constructor chaining. Nó phải đưa object về trạng thái hợp lệ hoặc ném exception. Nếu constructor ném exception, biểu thức `new` không cung cấp object đó cho caller.

### 4.5 Constructor overload và `this(...)`

Hai constructor cho phép caller chọn API ngắn hoặc đầy đủ:

```csharp
public BankAccount(string owner, decimal openingBalance)
    : this(owner, openingBalance, "VND")
{
}
```

`this(owner, openingBalance, "VND")` gọi một constructor khác của **cùng class** trước khi thân constructor ngắn chạy. Nhờ đó validation và gán field chỉ nằm ở một nơi. Constructor chaining phải xuất hiện sau dấu `:` và trước thân `{ ... }`; không gọi constructor như một method bình thường.

### 4.6 `this` là object nhận lời gọi hiện tại

Trong:

```csharp
anAccount.Deposit(500_000m);
```

bên trong `Deposit`, `this` trỏ tới cùng object mà `anAccount` đang trỏ tới. Vì vậy `this._balance += amount` cập nhật object A.

Trong constructor, `this.Owner` giúp phân biệt member của object với parameter `owner`. C# phân biệt hoa/thường nên ví dụ vẫn rõ, nhưng `this` đặc biệt hữu ích khi parameter và field cùng tên:

```csharp
private string _owner;

public void Rename(string owner)
{
    this._owner = owner;
}
```

`this` không tồn tại trong `static` member vì static member không chạy trên một instance cụ thể.

### 4.7 Instance member và static member

`_balance`, `Owner`, `Deposit()` là instance member. Muốn truy cập chúng cần một object:

```csharp
anAccount.Deposit(100m);
```

`s_lastAccountNumber` và `CreatedCount` là static member, thuộc về type `BankAccount` và chỉ có một trạng thái logic dùng chung:

```text
Type BankAccount (shared static state)
+----------------------------------+
| s_lastAccountNumber = 1002       |
| CreatedCount = 2                 |
+----------------------------------+

Object A                      Object B
+------------------+          +------------------+
| _balance=...     |          | _balance=...     |
+------------------+          +------------------+
```

Truy cập static member qua tên type: `BankAccount.CreatedCount`. Static mutable state dùng chung có thể gây race condition trong chương trình đa luồng. Bộ đếm đơn giản ở ví dụ chỉ phục vụ một console app đơn luồng; hệ thống thật nên dùng mã do database/`Guid` cấp hoặc đồng bộ hóa đúng cách.

## 5. Kiến thức nền

### 5.1 Field lưu trạng thái, method thực hiện hành vi

`_balance` là field lưu trạng thái bên trong object. `Deposit`, `Withdraw`, `TransferTo` là method làm thay đổi trạng thái theo quy tắc. Đưa hành vi vào class giúp không nơi nào tùy tiện làm số dư âm.

Ví dụ dùng property chỉ đọc `Balance => _balance` để caller quan sát nhưng không gán trực tiếp. Property và encapsulation được trình bày sâu ở bài tiếp theo.

### 5.2 Object identity khác equality

`ReferenceEquals(a, b)` kiểm tra hai reference có trỏ đúng cùng object hay không. Hai object khác nhau vẫn có thể biểu diễn dữ liệu bằng nhau. Khi cần equality theo giá trị, type phải định nghĩa quy tắc phù hợp (`Equals`, `GetHashCode`, record, ...); đừng đồng nhất “cùng dữ liệu” với “cùng object”.

### 5.3 Null reference

Một reference type variable có thể mang `null` nếu type cho phép, nghĩa là không trỏ tới object nào. Gọi member qua `null` gây `NullReferenceException`:

```csharp
BankAccount? account = null;
// account.Deposit(100m); // Không an toàn.
```

Với nullable reference types bật mặc định trong project .NET mới, dấu `?` thể hiện `null` là trạng thái dự kiến và compiler hỗ trợ kiểm tra. Bài nâng cao sẽ đi sâu vào nullable annotations.

### 5.4 Default constructor không phải lúc nào cũng tồn tại

Nếu class không khai báo constructor instance nào, compiler cung cấp parameterless constructor mặc định. Khi bạn đã tự khai báo bất kỳ constructor instance nào, compiler không tự thêm `BankAccount()` nữa. Nếu nghiệp vụ không cho phép object thiếu owner, việc không có parameterless constructor là đúng.

### 5.5 Object lifetime và Garbage Collector

C# không yêu cầu `free` object managed bằng tay. Khi không còn reference khả dụng tới object, object trở thành ứng viên để Garbage Collector thu hồi vào một thời điểm sau đó. “Ra khỏi scope” không đồng nghĩa được thu hồi ngay, và còn reference ở nơi khác thì object vẫn sống.

GC quản lý bộ nhớ managed, không tự giải phóng kịp thời mọi tài nguyên ngoài managed memory như file handle hoặc socket. Chủ đề đó được xử lý bằng `IDisposable` ở phần nâng cao.

### 5.6 Class nên giữ invariant

Invariant là điều luôn phải đúng đối với một object hợp lệ. Với `BankAccount`:

- `Owner` không rỗng.
- `Currency` không rỗng.
- `_balance >= 0`.

Constructor thiết lập invariant; mọi public method phải bảo toàn nó. Validation chỉ ở UI là không đủ vì object có thể được gọi từ API, test hoặc background job.

## 6. Lỗi thường gặp

### 6.1 Nghĩ phép gán class tạo bản sao sâu

```csharp
BankAccount second = first;
```

không clone account. Cả hai biến cùng trỏ một object. Nếu cần copy độc lập, hãy định nghĩa operation có chủ đích và quyết định rõ field/reference con nào cần copy sâu.

### 6.2 Tạo nhiều object rồi kỳ vọng chúng chia sẻ instance field

Mỗi `new BankAccount(...)` có `_balance` riêng. Chỉ `static` state mới chia sẻ ở cấp type. Đừng đổi field thành static chỉ để “thấy cùng dữ liệu”; hãy xác định dữ liệu thực sự thuộc object nào hoặc service/store nào.

### 6.3 Để object tồn tại ở trạng thái không hợp lệ

Constructor rỗng cộng nhiều setter công khai có thể tạo khoảng thời gian object chưa có owner hoặc balance sai. Yêu cầu dữ liệu bắt buộc trong constructor và validate ngay tại biên của class.

### 6.4 Lặp code ở mọi constructor

Copy validation và gán field vào nhiều overload dễ khiến một overload bị thiếu rule. Dùng `this(...)` để hội tụ vào một constructor chính.

### 6.5 Dùng static mutable state cho dữ liệu theo request/user

Static tồn tại dùng chung trong process. Lưu “current user”, request hiện tại hoặc số dư đang thao tác vào static field làm các request ảnh hưởng nhau. Static phù hợp với hành vi không trạng thái, constant, cache được thiết kế cẩn thận hoặc state có đồng bộ rõ ràng.

### 6.6 Trả reference nội bộ có thể bị sửa từ ngoài

Nếu class có field là array và trả thẳng array đó, caller có thể sửa các ô mà không qua rule của class. Hãy cân nhắc trả read-only view hoặc bản copy tùy yêu cầu hiệu năng và ownership.

### 6.7 Quên kiểm tra parameter reference

`TransferTo` cần một destination thật. `ArgumentNullException.ThrowIfNull(destination)` làm lỗi xuất hiện ngay tại biên method với thông tin rõ, thay vì `NullReferenceException` mơ hồ ở dòng sau.

## 7. Bài tập

### Bài 1 — `Rectangle`

Tạo class `Rectangle` nhận `width`, `height` dương trong constructor; có method `GetArea()` và `GetPerimeter()`. Tạo hai object và chứng minh thay đổi/trạng thái của object này độc lập object kia.

Gợi ý: dùng private field hoặc get-only property; ném `ArgumentOutOfRangeException` khi đầu vào không dương.

### Bài 2 — Constructor chaining

Tạo class `Employee` với constructor đầy đủ `(name, department, startingSalary)` và overload `(name)` dùng department `"Unassigned"`, salary `0`. Không lặp validation.

Gợi ý: overload ngắn gọi `: this(...)`.

### Bài 3 — Bộ đếm object

Thêm static property đếm số `Employee` đã tạo thành công. Thử tạo một object với dữ liệu sai và giải thích bộ đếm nên tăng ở vị trí nào trong constructor.

Gợi ý: chỉ tăng sau khi toàn bộ validation đã qua; lưu ý bộ đếm đơn giản chưa thread-safe.

### Bài 4 — Reference alias

Tạo class `Counter` với `Increment()`. Cho hai biến cùng tham chiếu một object, gọi qua từng biến và vẽ sơ đồ bộ nhớ. Sau đó gán biến thứ hai bằng một lần `new` khác và vẽ lại.

Gợi ý: dùng `ReferenceEquals` để kiểm chứng identity, không dùng nó thay cho equality dữ liệu.

### Bài 5 — Chuyển tiền an toàn hơn

Mở rộng `BankAccount` để ghi nhận tổng số lần giao dịch và từ chối chuyển khác currency. Viết các tình huống kiểm tra: số tiền `0`, âm, vượt số dư, cùng account và chuyển hợp lệ.

Gợi ý: kiểm tra hết điều kiện trước khi thay đổi số dư; suy nghĩ chuyện gì xảy ra nếu bước nạp destination thất bại sau khi đã rút source.

## 8. Checklist tự đánh giá và điều hướng

Bạn hoàn thành bài khi có thể tự trả lời:

- [ ] Tôi phân biệt được class, object và reference.
- [ ] Tôi giải thích được từng bước chính của biểu thức `new`.
- [ ] Tôi biết mỗi lần `new` thành công tạo một object có instance state riêng.
- [ ] Tôi vẽ được hai biến cùng giữ reference tới một object.
- [ ] Tôi viết được constructor validation và overload dùng `this(...)`.
- [ ] Tôi biết `this` trỏ tới object nhận lời gọi hiện tại.
- [ ] Tôi phân biệt instance member và static member, kể cả rủi ro static mutable state.
- [ ] Tôi hiểu object không được GC thu hồi chỉ vì một biến ra khỏi scope nếu vẫn còn reference khác.

Điều hướng:

- Bài tiên quyết: [Mảng, chuỗi, `Index` và `Range`](./06-array-string-index-va-range.md)
- Bài tiếp theo: [Property, encapsulation và access modifier](./08-property-encapsulation-va-access-modifier.md)
