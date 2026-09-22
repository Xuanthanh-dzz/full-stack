# Method, parameter và return

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, culture hoặc serialization; CI failure

## TL;DR

- Method đóng gói một thao tác; value, ref và out quy định cách dữ liệu đi qua lời gọi.
- Dùng TryReserveItem để kiểm tra trước rồi cập nhật tồn kho có kiểm soát.
- ref cho quyền sửa caller; cần giữ nguyên state khi từ chối yêu cầu.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- tách một quy trình thành các method có một trách nhiệm rõ;
- đọc và viết method signature, parameter, argument và return value;
- giải thích pass-by-value mặc định;
- dùng `ref` khi method cần đọc/ghi storage đã khởi tạo của caller;
- dùng `out` cho output bắt buộc phải được gán trong method;
- dùng `params`, optional argument và named argument đúng chỗ;
- theo dõi call stack và lifetime của local qua một chuỗi lời gọi;
- nhận ra khi API dùng quá nhiều `ref/out` và nên trả một object kết quả.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Bạn giao bản sao phiếu cho quầy thì quầy sửa bản sao; giao quyền sửa sổ kho thì thay đổi nằm lại sau khi quay về. out giống ô kết quả mà quầy phải điền trước khi trả lời.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| parameter | tên nhận input trong khai báo hàm | requestedQuantity |
| argument | giá trị hoặc biến truyền tại lời gọi | 3 và ref stock |
| ref | truy cập trực tiếp biến của caller | availableStock |
| out | biến kết quả phải được gán trước return | lineTotal/message |
| params | cho phép truyền nhiều đối số theo một nhóm | CalculateAverage |

### Ví dụ nhỏ — tính tay trước

stock = 2, yêu cầu 3 → false, stock vẫn 2, lineTotal = 0. Yêu cầu 2 món giá 5 → true, stock = 0, lineTotal = 10.

Một quầy thanh toán cần đặt hàng từ tồn kho, tính tiền từng dòng, cộng tổng, giảm giá, tính giá trị trung bình và tạo biên nhận. Nếu viết tất cả trong `Main`, validation tồn kho và công thức tiền sẽ bị lặp lại cho từng sản phẩm.

Ta cần chia quy trình sao cho:

- `TryReserveItem` trả thành công/thất bại, đồng thời cập nhật tồn kho và đưa line total/message ra ngoài;
- `ApplyDiscount` cập nhật tổng hiện có;
- `CalculateAverage` nhận số lượng line total linh hoạt;
- `FormatReceipt` có giá trị mặc định nhưng caller vẫn có thể gọi bằng tên argument.

Mục tiêu không phải tạo nhiều method nhất có thể. Mỗi method phải có hợp đồng dễ gọi và dễ kiểm tra.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project:

```bash
dotnet new console --name CheckoutMethods --framework net9.0 --use-program-main
cd CheckoutMethods
```

Thay `Program.cs` bằng:

```csharp
namespace CheckoutMethods;

internal static class Program
{
    private static void Main()
    {
        int stock = 10;
        decimal orderTotal = 0m;

        bool keyboardReserved = TryReserveItem(
            productName: "Keyboard",
            unitPrice: 250_000m,
            requestedQuantity: 3,
            availableStock: ref stock,
            lineTotal: out decimal keyboardTotal,
            message: out string keyboardMessage);

        Console.WriteLine(keyboardMessage);
        if (keyboardReserved)
        {
            orderTotal += keyboardTotal;
        }

        bool mouseReserved = TryReserveItem(
            "Mouse",
            125_000m,
            2,
            ref stock,
            out decimal mouseTotal,
            out string mouseMessage);

        Console.WriteLine(mouseMessage);
        if (mouseReserved)
        {
            orderTotal += mouseTotal;
        }

        ApplyDiscount(ref orderTotal, percentage: 10m);

        // Chỉ đưa các dòng đặt thành công vào average. Compiler gom những
        // argument được chọn thành một decimal[] cho params.
        decimal averageLineTotal = (keyboardReserved, mouseReserved) switch
        {
            (true, true) => CalculateAverage(keyboardTotal, mouseTotal),
            (true, false) => CalculateAverage(keyboardTotal),
            (false, true) => CalculateAverage(mouseTotal),
            _ => CalculateAverage()
        };

        // Named arguments cho phép thể hiện ý nghĩa và đổi thứ tự khi cần.
        // currency bị bỏ qua nên nhận default "VND".
        string receipt = FormatReceipt(
            total: orderTotal,
            customerName: "Lan",
            includeHeader: true);

        Console.WriteLine($"Stock remaining: {stock}");
        Console.WriteLine($"Average line total: {averageLineTotal:N0} VND");
        Console.WriteLine(receipt);
    }

    private static bool TryReserveItem(
        string productName,
        decimal unitPrice,
        int requestedQuantity,
        ref int availableStock,
        out decimal lineTotal,
        out string message)
    {
        // out parameters phải được gán trên mọi đường return.
        lineTotal = 0m;

        if (requestedQuantity <= 0)
        {
            message = $"{productName}: quantity must be positive.";
            return false;
        }

        if (unitPrice < 0m)
        {
            message = $"{productName}: price cannot be negative.";
            return false;
        }

        if (requestedQuantity > availableStock)
        {
            message = $"{productName}: not enough stock.";
            return false;
        }

        if (unitPrice > decimal.MaxValue / requestedQuantity)
        {
            message = $"{productName}: line total exceeds decimal range.";
            return false;
        }

        // Tính và format xong trước khi sửa tồn kho của caller.
        lineTotal = unitPrice * requestedQuantity;
        message = $"{productName}: reserved, line total {lineTotal:N0} VND.";
        availableStock -= requestedQuantity;
        return true;
    }

    private static void ApplyDiscount(ref decimal total, decimal percentage)
    {
        if (percentage < 0m || percentage > 100m)
        {
            // Bài exception sẽ giải thích cách thiết kế lỗi đầy đủ hơn.
            Console.WriteLine("Invalid discount; no discount was applied.");
            return;
        }

        total -= total * percentage / 100m;
    }

    private static decimal CalculateAverage(params decimal[] values)
    {
        if (values.Length == 0)
        {
            return 0m;
        }

        decimal sum = 0m;
        foreach (decimal value in values)
        {
            sum += value;
        }

        return sum / values.Length;
    }

    private static string FormatReceipt(
        string customerName,
        decimal total,
        string currency = "VND",
        bool includeHeader = false)
    {
        string header = includeHeader ? "=== RECEIPT ===\n" : string.Empty;
        return $"{header}Customer: {customerName}\nTotal: {total:N0} {currency}";
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Kết quả chính:

```text
Keyboard: reserved, line total 750,000 VND.
Mouse: reserved, line total 250,000 VND.
Stock remaining: 5
Average line total: 500,000 VND
=== RECEIPT ===
Customer: Lan
Total: 900,000 VND
```

Dấu phân cách số phụ thuộc locale. Project đã được kiểm tra bằng .NET SDK `9.0.121`, target `net9.0`, không dùng package ngoài.

### Walkthrough — execution / state / cost

1. Caller tạo stock = 10; cả hai lời gọi mượn chính biến này qua ref.
2. Hàm kiểm tra quantity/price/stock và cận decimal, tính rồi format trước khi trừ kho.
3. Hai dòng hợp lệ làm stock 10→7→5; tổng 1000000 giảm 10% thành 900000.
4. Method có local riêng nhưng ref/out ghi về caller. params tạo nhóm giá trị cho lời gọi; average duyệt số phần tử, không cost cố định với mọi số argument.

### Mini-check

Giá decimal.MaxValue, quantity = 2, stock = 10: guard nào giữ stock và output đúng trước phép nhân?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Method declaration và lời gọi ghép với nhau

Đây là toàn bộ **method declaration**:

```csharp
private static bool TryReserveItem(
    string productName,
    decimal unitPrice,
    int requestedQuantity,
    ref int availableStock,
    out decimal lineTotal,
    out string message)
```

- tên method là `TryReserveItem`;
- return type là `bool`;
- sáu parameter có type, thứ tự và modifier;
- `private` giới hạn truy cập trong type `Program`;
- `static` cho phép gọi không cần object `Program`.

Không gọi toàn bộ declaration trên là “signature”. Khi phân biệt các overload, C# dựa vào tên method, số type parameter và parameter list (type cùng dạng truyền value/`ref`/`out`/`in` theo quy tắc ngôn ngữ). Return type, access modifier và `static` không cho phép tạo một overload khác. Vì vậy hai method chỉ khác `bool`/`int` ở return type sẽ không compile.

Parameter là biến trong khai báo method. Argument là biểu thức/biến caller truyền ở lời gọi. `requestedQuantity` là parameter; literal `3` là argument.

Mỗi lời gọi phải khớp type và modifier. Caller phải viết `ref stock`, `out decimal keyboardTotal`; chỉ khai báo `ref/out` ở phía method là chưa đủ.

### 4.2. Pass-by-value mặc định tạo bản sao giá trị parameter

Ba parameter đầu không có modifier:

```csharp
string productName, decimal unitPrice, int requestedQuantity
```

Caller truyền **by value**: parameter nhận một bản sao giá trị argument. Với `decimal` và `int`, sửa parameter local sẽ không sửa biến caller. Với reference type như `string`, giá trị được sao chép là reference; cả hai reference ban đầu cùng trỏ object, không phải object được deep-copy. Bài 05 sẽ vẽ chính xác trường hợp này.

### 4.3. `ref` tạo alias đến storage của caller

Trước lời gọi, `stock` đã có giá trị `10`. Khi truyền `ref stock`, parameter `availableStock` không nhận bản sao `10`; nó alias đúng storage của `stock`. Vì vậy:

```csharp
availableStock -= requestedQuantity;
```

thay đổi `stock` trong `Main`. `ref` cho phép method đọc và ghi; argument phải là biến đã definite-assigned và type phải khớp chính xác.

`ref` không phải raw pointer tùy ý như C. Nó là managed reference chịu quy tắc type/lifetime của C#; bạn không tự làm arithmetic trên địa chỉ.

### 4.4. `out` cũng alias storage nhưng có hợp đồng gán đầu ra

`keyboardTotal` và `keyboardMessage` được khai báo ngay tại call site. Caller không cần khởi tạo trước. Bên trong `TryReserveItem`, compiler buộc `lineTotal` và `message` được gán trên mọi đường `return`.

Code gán `lineTotal = 0m` ở đầu, rồi mỗi nhánh gán `message` trước khi return. Nếu bỏ một phép gán, build thất bại thay vì để caller đọc dữ liệu chưa xác định.

Quy ước tên `Try...` trong .NET thường là: return `bool`, kết quả qua `out`, lỗi input dự kiến không dùng exception. Ví dụ chuẩn là `int.TryParse`.

### 4.5. Call stack khi gọi `TryReserveItem`

Mô hình khái niệm tại lời gọi đầu tiên:

```text
CALL STACK (top)

TryReserveItem frame
├── productName       = copy của reference tới "Keyboard"
├── unitPrice         = copy 250000m
├── requestedQuantity = copy 3
├── availableStock -------- alias ----------┐
├── lineTotal ------------- out alias ----┐  |
└── message --------------- out alias --┐ |  |
                                        | |  |
Main frame                              | |  |
├── stock = 10 <------------------------|-|--┘
├── keyboardTotal <---------------------|-┘
├── keyboardMessage <-------------------┘
└── orderTotal = 0m
```

Sau khi method chạy, `stock = 7`, `keyboardTotal = 750000m` và `keyboardMessage` có text. Frame `TryReserveItem` được pop; local riêng của nó hết lifetime, còn storage của `Main` vẫn tồn tại.

### 4.6. `return` kết thúc invocation hiện tại

`return false;` vừa chọn giá trị trả về vừa dừng method ngay. Code phía dưới trong method không chạy. `return;` trong method `void` chỉ kết thúc sớm, như nhánh discount sai.

Return value được caller nhận vào `keyboardReserved`. Một method chỉ có một return value tường minh, nhưng có thể có nhiều statement `return` ở các nhánh; mọi nhánh reachable của method non-`void` phải trả type tương thích.

### 4.7. `params`, optional và named arguments

`params decimal[] values` cho phép hai kiểu gọi:

```csharp
CalculateAverage(10m, 20m, 30m);
CalculateAverage(new decimal[] { 10m, 20m, 30m });
```

Ở lời gọi thứ nhất, compiler tạo array chứa argument. `params` phải là parameter cuối và chỉ có một `params` trong signature.

`currency = "VND"` và `includeHeader = false` là optional parameters với compile-time default. Caller bỏ `currency`, nên compiler chèn giá trị mặc định vào call site.

Named arguments (`total:`, `customerName:`) ánh xạ theo tên thay vì vị trí, giúp lời gọi có nhiều `bool`/số dễ đọc.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| value | copy giá trị parameter | số nhỏ dễ hiểu; reference copy vẫn cùng object |
| ref | alias tới biến caller | dùng khi thay biến là contract rõ |
| out | output bắt buộc gán | hợp Try API; không thay validation |

### Misconception check

**Đúng hay sai?** Mọi giá trị truyền value đều clone object sâu.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: với class, bản sao reference vẫn trỏ cùng object.

</details>

**Đúng hay sai?** Hàm trả false phải giữ out chưa gán.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: out phải gán trên mọi đường return; sample đặt lineTotal = 0.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace value/ref/out.

- **Working Developer — dùng khi làm việc:** failure state và trách nhiệm hàm.

- **Deep Dive — có thể quay lại sau:** allocation của params và thiết kế API.

### Một method tốt có hợp đồng rõ

Hợp đồng gồm:

- input hợp lệ là gì;
- output/return biểu diễn gì;
- state nào có thể thay đổi;
- lỗi được báo thế nào;
- có side effect như I/O, ghi database hay log không.

`CalculateAverage` chỉ tính và return nên dễ test. `TryReserveItem` có side effect lên `availableStock`, thể hiện bằng `ref`, nhưng nhiều output làm signature nặng; đây là tín hiệu cân nhắc một result type khi mô hình lớn hơn.

### `ref`, `out` và `in`

| Modifier | Caller phải khởi tạo? | Callee được đọc ban đầu? | Callee phải gán? | Mục đích |
|---|---:|---:|---:|---|
| không có | có giá trị hợp lệ | có, từ bản sao | không | input mặc định |
| `ref` | có | có | không | đọc/ghi cùng storage |
| `out` | không | không trước khi gán | có | output bắt buộc |
| `in` | có | có | không | readonly reference, hữu ích có chọn lọc với struct lớn |

### Method overloading

C# cho phép nhiều method cùng tên nếu parameter list khác đủ để compiler chọn:

```csharp
static decimal CalculateTax(decimal amount) => amount * 0.10m;
static decimal CalculateTax(decimal amount, decimal rate) => amount * rate;
```

Không thể overload chỉ bằng return type. Overload quá giống nhau, kết hợp optional arguments, có thể gây ambiguous call.

### Local scope và lifetime

Local trong method không thể truy cập trực tiếp từ method khác. Mỗi invocation có bộ local logic riêng, nên recursive call cũng có state riêng. Lifetime của managed object mà local reference trỏ tới lại do reachability/GC quyết định, không nhất thiết kết thúc khi frame pop.

### Khi nào không nên dùng nhiều `out`

Một cặp `bool + out value` phù hợp `TryParse` đơn giản. Nếu operation trả status, error code, nhiều data field và metadata, hãy định nghĩa result object/record rõ tên. Nó dễ mở rộng và tránh argument list dài. Class/record sẽ được học sau.

### Đào sâu (có thể quay lại sau)

JIT có thể inline method và không tạo physical frame đúng như hình. Hình mô tả semantics quan sát được: mỗi invocation có local/parameter logic riêng và return quay lại call site.

#### params, optional và named arguments

Đừng dùng nó ở hot path mà bỏ qua chi phí array allocation; đo trước khi tối ưu.

Với public library, đổi default ở library mới không tự đổi call site cũ nếu caller chưa recompile.

Đổi tên public parameter có thể làm vỡ source của caller dùng named arguments.

`in` có thể tránh copy một struct lớn nhưng không mặc nhiên nhanh hơn; JIT và defensive copy ảnh hưởng kết quả. Đo benchmark trước khi dùng vì hiệu năng.

## 6. Lỗi thường gặp

### Quên modifier ở call site

`TryReserveItem(..., stock, ...)` không khớp `ref int`. Viết `ref stock`. Modifier là một phần hợp đồng, caller phải nhìn thấy mutation.

### Truyền literal hoặc expression cho `ref/out`

Không thể truyền `ref (stock + 1)` hay `ref 10`; chúng không phải storage variable phù hợp để alias. Gán expression vào biến trước nếu thực sự cần.

### Không gán `out` trên mọi đường return

Compiler báo lỗi. Khởi tạo output hợp lý ở đầu hoặc gán rõ trong từng nhánh; đừng gán giá trị giả khiến caller hiểu nhầm mà không document.

### Tin parameter thường có thể đổi biến caller

`void Reset(int value) { value = 0; }` chỉ đổi bản sao. Cần return giá trị mới hoặc `ref`; thường return làm data flow rõ hơn.

### Nhầm “reference type” với “pass by reference”

Truyền một class instance bằng parameter thường vẫn là pass-by-value của **reference**. Method có thể mutate object được trỏ tới, nhưng gán parameter sang object khác không đổi biến caller. Bài 05 minh họa bằng địa chỉ logic.

### `params` nhận `null` hoặc zero arguments mà không có policy

Zero arguments tạo array rỗng và sample trả `0m`; đó là lựa chọn domain, không phải trung bình toán học chuẩn. Với public API, hãy document hoặc reject. Caller cũng có thể truyền `null` tường minh nếu nullable warning bị bỏ qua; API production cần guard.

### Optional parameter che giấu ý nghĩa

Lời gọi nhiều `bool` như `FormatReceipt("Lan", total, "VND", true)` khó đọc. Dùng named arguments hoặc options object khi tùy chọn tăng nhiều.

### Method làm quá nhiều việc

Method vừa validate, tính tiền, ghi file, gửi email và mutate global state sẽ khó test. Tách theo trách nhiệm và data flow, không tách máy móc mỗi ba dòng.

## 7. Khi nào KHÔNG dùng

Không dùng ref cho mọi số để tránh copy. Không gom nhiều output không liên quan vào một method chỉ vì out cho phép. Hai sản phẩm dùng chung stock ở đây chỉ minh họa parameter, chưa phải kho theo SKU.

## 8. Production notes & scale check

Test từ chối quantity 0, thiếu hàng và overflow trước commit. Average và discount chỉ phục vụ miền nhỏ của hóa đơn demo; tính tổng một dãy decimal bất kỳ vẫn có thể overflow. Lỗi allocation/process bị kết thúc không nằm trong cam kết nghiệp vụ này.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Method tính VAT thuần

Viết `CalculateVat(decimal subtotal, decimal rate)` trả số VAT, không đọc `Console` và không sửa biến ngoài.

**Gợi ý:** validate rate ở caller trước; thử nhiều lời gọi với cùng input phải cùng output.

### Bài 2 — `TryWithdraw`

Viết method nhận số tiền yêu cầu, `ref decimal balance`, `out string message`; chỉ trừ khi số tiền dương và không vượt số dư.

**Gợi ý:** gán `message` trên mọi đường; kiểm tra balance không đổi khi thất bại.

### Bài 3 — Tổng linh hoạt với `params`

Viết `Sum(params decimal[] values)` và gọi với zero, one, many arguments và một array có sẵn.

**Gợi ý:** xác định policy của zero arguments; không sửa array đầu vào.

### Bài 4 — Optional/named arguments

Viết `CreateUserLabel(string name, string role = "User", bool uppercase = false)` rồi gọi bằng positional và named arguments.

**Gợi ý:** thử bỏ `role` nhưng vẫn truyền `uppercase` bằng tên.

### Bài 5 — Vẽ call stack

Viết `Main → CalculateInvoice → CalculateTax`, đặt local ở mỗi method và vẽ frame ngay khi đang ở `CalculateTax`.

**Gợi ý:** ghi rõ parameter nào là copy, local nào thuộc frame nào, frame nào pop trước; sau đó bật debugger kiểm tra call stack.

## 10. Bài tập tích hợp liên module — Judgment

So sánh output pointer trong C Module 02 với ref/out: compiler kiểm tra thêm điều gì? Thiết kế reserve theo SKU cần thay contract dữ liệu nào trước khi thêm database?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Parameter khác argument ở đâu?
2. Caller thấy state nào khi Try trả false?
3. Named argument có đổi signature của method không?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi đọc được access modifier, `static`, return type, tên và parameter list.
- [ ] Tôi phân biệt parameter với argument và pass-by-value với `ref/out`.
- [ ] Tôi giải thích được tại sao `stock` đổi qua `ref`.
- [ ] Tôi bảo đảm `out` được gán trên mọi đường return.
- [ ] Tôi dùng `params`, optional và named argument có chủ đích.
- [ ] Tôi vẽ đúng call stack và không đồng nhất frame với lifetime của object trên heap.

Điều hướng:

- Prerequisite: [Toán tử, điều kiện và vòng lặp](./03-toan-tu-dieu-kien-vong-lap.md)
- Bài tiếp theo: [Stack, heap, value type và reference type](./05-stack-heap-value-type-reference-type.md)
