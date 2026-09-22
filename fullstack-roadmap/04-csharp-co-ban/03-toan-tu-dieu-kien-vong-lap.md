# Toán tử, điều kiện và vòng lặp

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, culture hoặc serialization; CI failure

## TL;DR

- Điều kiện chọn nhánh, vòng lặp lặp công việc; continue và break cắt luồng khác nhau.
- Dùng để lọc đơn hủy và tổng hợp một batch có điều kiện dừng rõ.
- Kiểm tra ngân sách sau cộng cho phép tổng vượt ngưỡng; đó là policy của sample.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- đọc đúng thứ tự đánh giá của biểu thức và dùng ngoặc để thể hiện ý định;
- dùng toán tử số học, so sánh, logic, gán và tăng/giảm;
- hiểu short-circuit của `&&` và `||`;
- chọn `if/else`, `switch` statement, `switch` expression hoặc toán tử `?:`;
- chọn `for`, `while` hoặc `do-while` theo dạng bài toán;
- dùng `break` và `continue` mà không làm luồng xử lý khó hiểu;
- nhận ra integer division, phép so sánh sai và vòng lặp vô hạn.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Bạn duyệt từng phiếu: phiếu hủy thì bỏ qua; đủ điều kiện đóng lô thì ngừng xem phiếu sau. Bỏ một phiếu và đóng cả lô không cùng hành động.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| branch | nhánh được chọn theo điều kiện | if và switch |
| iteration | một lượt của vòng lặp | một orderId |
| continue | bỏ phần còn lại của lượt hiện tại | đơn 4 bị hủy |
| break | thoát vòng lặp gần nhất | đóng batch sau đơn 7 |

### Ví dụ nhỏ — tính tay trước

Giả sử tổng đang 4.7 triệu, đơn mới 0.6 triệu và ngưỡng 5 triệu. Cộng rồi kiểm tra → 5.3 triệu có đơn mới; kiểm tra trước nhận → vẫn 4.7 triệu. Hai policy khác nhau.

Kho hàng xử lý lần lượt tám đơn trong một đợt. Mỗi đơn có giá trị, vùng giao hàng và trạng thái VIP khác nhau. Quy tắc:

- đơn số 4 đã hủy nên phải bỏ qua;
- đơn từ `1_000_000` VND được giảm `10%`; đơn VIP từ `500_000` VND được giảm `5%`;
- miễn phí vận chuyển nếu số tiền sau giảm đạt `1_000_000` VND hoặc đơn VIP đạt `500_000` VND;
- phí còn lại phụ thuộc vùng;
- dừng đợt khi tổng cần thu vượt ngân sách xử lý `5_000_000` VND;
- máy in nhãn có thể thử tối đa ba lần; việc đóng gói luôn chạy ít nhất một batch.

Đây không phải bài toán “học `if`”. Ta cần biến một bộ quy tắc có thứ tự ưu tiên thành control flow đọc được và kiểm chứng được.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project:

```bash
dotnet new console --name OrderBatch --framework net9.0 --use-program-main
cd OrderBatch
```

Thay `Program.cs` bằng:

```csharp
namespace OrderBatch;

internal static class Program
{
    private static void Main()
    {
        const int lastOrderId = 8;
        const int canceledOrderId = 4;
        const decimal processingBudget = 5_000_000m;

        decimal amountToCollect = 0m;
        int processedCount = 0;

        for (int orderId = 1; orderId <= lastOrderId; orderId++)
        {
            if (orderId == canceledOrderId)
            {
                Console.WriteLine($"Order {orderId}: canceled, skipped.");
                continue; // Sang iteration kế tiếp, không chạy phần còn lại.
            }

            // Dữ liệu cố định để sample tái tạo được; sau này sẽ lấy từ database.
            decimal orderValue = orderId switch
            {
                1 => 400_000m,
                2 => 1_200_000m,
                3 => 800_000m,
                5 => 2_000_000m,
                6 => 600_000m,
                7 => 3_000_000m,
                _ => 500_000m
            };

            bool isVip = orderId % 2 == 0;
            int zoneCode = orderId % 3 + 1;

            decimal discountRate;
            if (orderValue >= 1_000_000m)
            {
                discountRate = 0.10m;
            }
            else if (isVip && orderValue >= 500_000m)
            {
                // Vế phải chỉ được kiểm tra nếu isVip là true.
                discountRate = 0.05m;
            }
            else
            {
                discountRate = 0m;
            }

            decimal discountedValue = orderValue * (1m - discountRate);
            bool getsFreeShipping =
                discountedValue >= 1_000_000m ||
                (isVip && discountedValue >= 500_000m);

            decimal shippingFee;
            string routeName;

            switch (zoneCode)
            {
                case 1:
                    shippingFee = 30_000m;
                    routeName = "Urban";
                    break;
                case 2:
                    shippingFee = 45_000m;
                    routeName = "Suburban";
                    break;
                case 3:
                    shippingFee = 70_000m;
                    routeName = "Remote";
                    break;
                default:
                    throw new InvalidOperationException("Unknown zone.");
            }

            // Toán tử ?: phù hợp khi chọn đúng một trong hai giá trị ngắn.
            shippingFee = getsFreeShipping ? 0m : shippingFee;
            decimal payable = discountedValue + shippingFee;

            amountToCollect += payable;
            processedCount++;

            Console.WriteLine(
                $"Order {orderId}: route={routeName}, vip={isVip}, " +
                $"discount={discountRate:P0}, payable={payable:N0}");

            if (amountToCollect > processingBudget)
            {
                Console.WriteLine("Processing budget reached; closing this batch.");
                break; // Thoát hẳn vòng for.
            }
        }

        Console.WriteLine($"Processed: {processedCount}");
        Console.WriteLine($"Amount to collect: {amountToCollect:N0} VND");

        int attemptsRemaining = 3;
        bool labelPrinted = false;

        while (!labelPrinted && attemptsRemaining > 0)
        {
            int attemptNumber = 4 - attemptsRemaining;
            Console.WriteLine($"Printing label, attempt {attemptNumber}...");

            // Giả lập: máy in thành công ở lần thứ hai.
            labelPrinted = attemptNumber == 2;
            attemptsRemaining--;
        }

        Console.WriteLine(labelPrinted ? "Label ready." : "Label failed.");

        int packagesRemaining = 5;
        do
        {
            int packagesInBatch = Math.Min(2, packagesRemaining);
            Console.WriteLine($"Packed {packagesInBatch} package(s).");
            packagesRemaining -= packagesInBatch;
        }
        while (packagesRemaining > 0);
    }
}
```

Build và chạy:

```bash
dotnet build
dotnet run --no-build
```

Các mốc quan trọng trong output:

```text
Order 4: canceled, skipped.
Processing budget reached; closing this batch.
Processed: 6
Amount to collect: 7,425,000 VND
Printing label, attempt 1...
Printing label, attempt 2...
Label ready.
Packed 2 package(s).
Packed 2 package(s).
Packed 1 package(s).
```

Dấu phân cách số có thể khác theo locale. Project đã được kiểm tra với .NET SDK `9.0.121`, target `net9.0`, không dùng package ngoài.

### Walkthrough — execution / state / cost

1. for xét đơn 1..8; đơn 4 đi continue nên không tăng count/tổng.
2. Discount được chọn trước, shipping dựa trên subtotal sau discount.
3. Sau đơn 7, count = 6 và tổng = 7425000; break ngăn xét đơn 8.
4. Retry in nhãn dừng lần 2; do/while đóng gói 2,2,1. State là counters/tổng; cost tuyến tính theo số đơn đã xét, bộ nhớ phụ cố định.

### Mini-check

Nếu chuyển processedCount++ lên trước nhánh hủy, report còn phản ánh số đơn thực xử lý không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Một iteration xử lý theo thứ tự nào?

Với mỗi `orderId`, luồng chạy là:

```text
orderId hiện tại
      |
      v
orderId == 4 ? --yes--> continue --> orderId++ --> kiểm tra điều kiện for
      |
      no
      v
lấy orderValue -> tính VIP/zone -> chọn discount
      |
      v
tính shipping/payable -> cộng tổng -> in kết quả
      |
      v
tổng > budget ? --yes--> break --> ra khỏi for
      |
      no
      v
orderId++ --> kiểm tra orderId <= 8
```

`continue` không “bỏ qua đơn mãi mãi”; nó bỏ phần còn lại của **iteration hiện tại**. Với `for`, biểu thức cập nhật `orderId++` vẫn chạy trước lần kiểm tra tiếp theo. `break` thoát vòng lặp gần nhất hoàn toàn.

### 4.2. Thứ tự ưu tiên của chính sách giảm giá

Chuỗi `if / else if / else` chọn đúng một nhánh đầu tiên có điều kiện `true`:

```text
orderValue >= 1,000,000 ? -> giảm 10%
không, nhưng VIP và >= 500,000 ? -> giảm 5%
không -> 0%
```

Đơn `1_200_000` VND và VIP vẫn chỉ nhận `10%`, vì nhánh đầu đã thắng. Đổi thứ tự hai nhánh có thể đổi nghiệp vụ. Điều kiện không chỉ là cú pháp; thứ tự của chúng là một phần policy.

### 4.3. Short-circuit bảo vệ vế phải

Với `A && B`, nếu `A` là `false`, toàn biểu thức chắc chắn `false`, nên `B` không chạy. Với `A || B`, nếu `A` là `true`, `B` không chạy.

```csharp
isVip && discountedValue >= 500_000m
```

Vế so sánh chỉ cần đánh giá khi `isVip` là `true`. Cơ chế này đặc biệt quan trọng khi vế phải dereference dữ liệu có thể `null` hoặc gọi method tốn chi phí. Không đặt side effect bắt buộc ở vế phải rồi kỳ vọng nó luôn chạy.

`&` và `|` cũng dùng được với `bool` nhưng đánh giá cả hai vế; chúng còn là bitwise operators với số nguyên. Trong điều kiện nghiệp vụ thông thường, dùng `&&` và `||`.

### 4.4. `switch` expression và `switch` statement

`orderId switch { ... }` là expression: mỗi arm tạo ra một giá trị và toàn expression được gán cho `orderValue`. Arm `_` là fallback. Compiler yêu cầu type kết quả tương thích.

`switch (zoneCode) { ... }` là statement: mỗi case chạy nhiều statement, gán hai biến rồi `break`. C# không tự fall through từ case có code sang case kế tiếp. `default` chủ động ném exception để state không hợp lệ không bị im lặng.

### 4.5. Chọn vòng lặp theo điều kiện

- `for`: có biến đếm, điểm bắt đầu, điều kiện và bước cập nhật rõ; phù hợp xử lý đơn 1 đến 8.
- `while`: chưa biết cần bao nhiêu lần, kiểm tra điều kiện **trước** mỗi lần; nếu máy in đã thành công từ đầu thì thân vòng không chạy.
- `do-while`: thân chạy trước rồi mới kiểm tra; đóng gói phải thực hiện ít nhất một batch nên phù hợp.

`attemptsRemaining--` là bắt buộc để `while` tiến tới kết thúc. Mỗi vòng lặp phải có một đại lượng hoặc sự kiện làm điều kiện có khả năng thành `false`.

### 4.6. Biểu thức được tính trước khi gán

```csharp
decimal discountedValue = orderValue * (1m - discountRate);
```

Ngoặc làm `1m - discountRate` chạy trước phép nhân. Không có ngoặc, `*` vốn ưu tiên hơn `-`, khiến biểu thức thành `orderValue * 1m - discountRate`, sai đơn vị và sai nghiệp vụ.

`amountToCollect += payable` tương đương về ý định với `amountToCollect = amountToCollect + payable`. `processedCount++` tăng một sau khi giá trị hiện tại được dùng; khi đứng thành statement riêng, khác biệt hậu tố/tiền tố không ảnh hưởng kết quả quan sát.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| continue | bỏ một lượt | dùng cho record không xử lý |
| break | thoát vòng hiện tại | dùng khi điều kiện đóng lô thỏa |
| return | thoát method | có thể bỏ cả phần in tổng phía sau |

### Misconception check

**Đúng hay sai?** break trong for cũng ngăn mọi code sau for chạy.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: chỉ thoát vòng lặp gần nhất.

</details>

**Đúng hay sai?** Ngưỡng 5 triệu bảo đảm tổng cuối không vượt 5 triệu.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: sample kiểm tra sau khi đã nhận đơn.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** trace từng nhánh.

- **Working Developer — dùng khi làm việc:** policy dừng và test cận.

- **Deep Dive — có thể quay lại sau:** tách rule khi số nhánh thực sự tăng.

### Các nhóm toán tử chính

| Nhóm | Toán tử | Ghi chú |
|---|---|---|
| Số học | `+ - * / %` | `%` lấy remainder, không chỉ dùng cho số chẵn/lẻ |
| So sánh | `== != < <= > >=` | kết quả là `bool` |
| Logic short-circuit | `&& || !` | `!` đảo `bool`; `&&`/`||` có thể bỏ vế phải |
| Gán | `= += -= *= /= ??=` | gán thay đổi state của biến/field |
| Tăng giảm | `++ --` | phải bảo đảm loop vẫn tiến tới dừng |
| Điều kiện | `condition ? whenTrue : whenFalse` | expression chọn một giá trị |
| Null | `??`, `?.` | dùng fallback hoặc truy cập có điều kiện; học sâu cùng nullable |
| Bitwise | `& | ^ ~ << >>` | thao tác bit của số nguyên; không thay `&&/||` tùy tiện |

### Integer division

Type toán hạng quyết định phép chia:

```csharp
int a = 5 / 2;          // 2
double b = 5 / 2;       // vẫn là 2, sau đó convert thành 2.0
double c = 5.0 / 2;     // 2.5
decimal d = 5m / 2m;    // 2.5m
```

Type bên trái không quay ngược thay đổi phép tính bên phải.

### Equality không phải assignment

`=` gán; `==` so sánh. Điều kiện C# phải có type `bool`, nên `if (count = 3)` không compile như ở một số ngôn ngữ cho phép số làm truthy/falsy.

Với floating point, `==` có thể không phù hợp vì sai số. Cần tolerance theo domain. Với `decimal`, vẫn phải thống nhất scale/rounding nghiệp vụ.

### Precedence và associativity

Compiler có bảng ưu tiên, nhưng người đọc không nên phải thuộc toàn bộ. Dùng ngoặc ở ranh giới nghiệp vụ:

```csharp
bool allowed = isVip && (orderValue >= minimum || hasCoupon);
```

Không lạm dụng ngoặc quanh từng literal; mục tiêu là làm nhóm logic rõ.

### Biến loop và scope

`int orderId` khai báo trong phần đầu của `for` chỉ tồn tại trong vòng lặp. Các biến khai báo trong thân loop được tạo về mặt ngữ nghĩa cho mỗi lần vào block; lifetime vật lý có thể được JIT tối ưu. Không giữ tham chiếu đến state mutable ngoài ý muốn khi sau này dùng lambda.

## 6. Lỗi thường gặp

### Điều kiện biên sai một đơn vị

`orderId < lastOrderId` bỏ đơn cuối; `<=` bao gồm nó. Viết rõ tập cần xử lý và thử các biên đầu/cuối.

### Vòng `while` không cập nhật state

Quên `attemptsRemaining--` có thể tạo vòng vô hạn. Trước khi chạy, chỉ ra điều gì thay đổi và vì sao điều kiện cuối cùng thành `false`.

### Dùng nhiều `if` độc lập khi chỉ một nhánh được phép thắng

Hai `if` có thể cùng chạy và ghi đè `discountRate`. Dùng `if/else if/else` khi policy có thứ tự ưu tiên loại trừ nhau.

### Nhầm `&&` với `&`, `||` với `|`

`&`/`|` đánh giá cả hai vế với `bool`. Nếu vế phải truy cập object có thể `null`, chương trình có thể lỗi dù vế trái đã đủ quyết định kết quả.

### Dùng `continue` trước cập nhật trong `while`

Trong `while`, `continue` nhảy thẳng lên kiểm tra; nếu bước cập nhật nằm cuối thân, nó bị bỏ và loop có thể kẹt. Đặt cập nhật đúng vị trí hoặc chọn `for`.

### Quên `default` hoặc fallback `_`

Khi domain có thể mở rộng, state mới có thể bị xử lý im lặng. Chọn fallback có chủ đích: giá trị mặc định hợp lệ hoặc fail fast bằng exception.

### Viết condition có side effect khó đoán

Ví dụ gọi method thay đổi state ở vế phải của `||`; method có thể không chạy do short-circuit. Tách side effect thành statement riêng.

### Dùng `double` equality để quyết định tiền/đo lường

Không dùng `value == 0.3` cho kết quả từ nhiều phép tính binary floating point. Dùng tolerance phù hợp hoặc `decimal` nếu domain là thập phân như tiền.

## 7. Khi nào KHÔNG dùng

Không dùng nested conditional dài khi một switch nhỏ đã mô tả đủ các route. Không chuyển vòng lặp đơn giản thành framework xử lý workflow khi chưa có driver.

## 8. Production notes & scale check

Một batch tám đơn: cần quyết định ngân sách là ngưỡng đóng sau nhận hay trần cứng. Sample dùng ngưỡng đóng sau nhận. Gate đối chiếu toàn bộ thứ tự output, count và tổng; retry mô phỏng không phải cơ chế gửi nhãn mạng đáng tin cậy.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Phân loại điểm

Nhận điểm `0–100`, dùng `if/else if` để phân loại A/B/C/D/F và từ chối ngoài range.

**Gợi ý:** viết các ngưỡng từ cao xuống thấp; kiểm thử `100`, `90`, `89`, `0`, `-1`, `101`.

### Bài 2 — Bảng cửu chương

Nhận một số `1–9`, dùng `for` in bảng nhân từ 1 đến 10.

**Gợi ý:** parse/validate trước loop; biến đếm nên có scope trong `for`.

### Bài 3 — Máy rút tiền đơn giản

Cho số tiền nguyên dương chia hết cho `10_000`, dùng `while` tính số tờ `500_000`, `200_000`, `100_000`, `50_000`, `20_000`, `10_000`.

**Gợi ý:** `/` lấy số tờ, `%` lấy phần còn lại; có thể dùng `switch` theo mệnh giá hiện tại.

### Bài 4 — FizzBuzz có cấu hình

In từ 1 đến N: bội 3 in `Fizz`, bội 5 in `Buzz`, bội cả hai in `FizzBuzz`.

**Gợi ý:** kiểm tra trường hợp cả hai trước hoặc ghép hai phần text; test N bằng 15.

### Bài 5 — Retry có backoff giả lập

Mô phỏng tối đa năm lần gọi dịch vụ, thành công ở lần thứ tư; in delay dự kiến `1, 2, 4, 8...` giây nhưng không thật sự chờ.

**Gợi ý:** dùng `while`, tăng attempt và nhân đôi delay; dừng ngay khi thành công bằng condition hoặc `break`.

## 10. Bài tập tích hợp liên module — Judgment

Đối chiếu vòng lặp Module 01: thay policy bằng trần cứng và nêu có bỏ đơn lớn để xét đơn nhỏ sau hay đóng luôn. Viết ví dụ phân biệt hai quyết định.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Đơn 4 ảnh hưởng count thế nào?
2. Vì sao đơn 8 không được xét?
3. do/while khác while khi số kiện ban đầu là 0?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi phân biệt assignment, comparison và logical operators.
- [ ] Tôi dự đoán được khi nào vế phải của `&&`/`||` không chạy.
- [ ] Tôi chọn được `if`, `switch` statement, `switch` expression hoặc `?:`.
- [ ] Tôi chọn đúng `for`, `while`, `do-while` theo điều kiện bài toán.
- [ ] Tôi giải thích chính xác tác dụng của `break` và `continue`.
- [ ] Tôi kiểm tra được điều kiện biên, integer division và khả năng kết thúc loop.

Điều hướng:

- Prerequisite: [Cú pháp, biến và kiểu dữ liệu](./02-cu-phap-bien-va-kieu-du-lieu.md)
- Bài tiếp theo: [Method, parameter và return](./04-method-parameter-va-return.md)
