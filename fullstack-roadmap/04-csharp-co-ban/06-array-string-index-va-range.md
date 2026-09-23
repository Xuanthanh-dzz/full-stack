# Mảng, chuỗi, `Index` và `Range`

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, culture hoặc serialization; CI failure

## TL;DR

- Array giữ phần tử theo chỉ số; string là chuỗi bất biến gồm đơn vị mã UTF-16.
- Dùng array cho tập có chiều dài cố định và range cho bản cắt rõ giới hạn.
- Cắt array tạo mảng mới nhưng không clone sâu các object phần tử.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- Chọn đúng giữa mảng một chiều (`T[]`), mảng chữ nhật (`T[,]`) và mảng răng cưa (`T[][]`).
- Khởi tạo, đọc, ghi và duyệt mảng mà không vượt giới hạn.
- Dùng cú pháp `^` (`Index`) và `..` (`Range`) để lấy phần tử hoặc một đoạn dữ liệu.
- Giải thích được vì sao `string` là reference type nhưng immutable.
- Phân biệt số UTF-16 code unit, Unicode scalar value và ký tự người dùng nhìn thấy.
- Vẽ được mô hình bộ nhớ khi nhiều biến cùng tham chiếu một mảng hoặc một chuỗi.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Một bảng ô cố định khác một danh sách các hàng có độ dài riêng. Cắt vài ô sang bảng mới tách bảng, nhưng nếu ô chứa địa chỉ thì hai bảng vẫn có thể dẫn tới cùng đồ vật.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| rectangular array | mảng nhiều chiều có kích thước hàng/cột chung | decimal[,] |
| jagged array | mảng mà mỗi phần tử là mảng riêng | decimal[][] |
| range | khoảng chỉ số đầu gồm, cuối không gồm | 1.. và ^2.. |
| UTF-16 code unit | đơn vị 16 bit của biểu diễn string | Length |
| Rune | một Unicode scalar value | emoji trong A😀B |

### Ví dụ nhỏ — tính tay trước

[10,20,30][1..] → mảng [20,30]. Sửa ô đầu bản cắt thành99 không sửa mảng số gốc. A😀B có4 đơn vị UTF-16,3 scalar; số ký tự người dùng nhìn còn phụ thuộc tổ hợp Unicode.

Một cửa hàng cần tổng hợp doanh thu:

- Kế hoạch doanh thu có đúng 3 ngày cho mỗi chi nhánh, nên dữ liệu tạo thành một bảng chữ nhật.
- Số giao dịch thực tế của mỗi chi nhánh không đều nhau, nên mỗi hàng phải có độ dài riêng.
- Báo cáo cần lấy hai giao dịch cuối mà không tự tính chỉ số.
- Tên chiến dịch có thể chứa emoji. Chương trình không được giả định `string.Length` luôn bằng số ký tự người dùng nhìn thấy.

Ta cần mô hình dữ liệu đúng trước khi tính toán. Ép mọi dữ liệu vào cùng một loại mảng sẽ làm code khó hiểu hoặc lãng phí ô nhớ.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo và chạy project độc lập bằng .NET 9:

```bash
mkdir csharp-array-demo
cd csharp-array-demo
dotnet new console --framework net9.0
# Thay toàn bộ Program.cs bằng code bên dưới.
dotnet build
dotnet run
```

`Program.cs`:

```csharp
using System;
using System.Linq;
using System.Text;

internal static class Program
{
    private static void Main()
    {
        string[] branches = ["Ha Noi", "Da Nang", "Can Tho"];

        // Rectangular array: mọi hàng có đúng 3 cột (Mon, Tue, Wed).
        decimal[,] plannedRevenue =
        {
            { 12_000_000m, 13_500_000m, 15_000_000m },
            {  9_000_000m, 10_000_000m, 11_500_000m },
            {  8_500_000m,  9_500_000m, 10_500_000m }
        };

        Console.WriteLine("=== Ke hoach theo chi nhanh ===");
        for (int row = 0; row < plannedRevenue.GetLength(0); row++)
        {
            decimal total = 0m;
            for (int column = 0; column < plannedRevenue.GetLength(1); column++)
            {
                total += plannedRevenue[row, column];
            }

            Console.WriteLine($"{branches[row],-8}: {total:N0} VND");
        }

        // Jagged array: mỗi chi nhánh có số giao dịch khác nhau.
        decimal[][] transactions =
        [
            [1_200_000m, 800_000m, 1_500_000m, 900_000m],
            [700_000m, 1_100_000m],
            [500_000m, 650_000m, 900_000m]
        ];

        Console.WriteLine("\n=== Giao dich gan nhat ===");
        for (int branchIndex = 0; branchIndex < transactions.Length; branchIndex++)
        {
            decimal[] branchTransactions = transactions[branchIndex];
            decimal newest = branchTransactions[^1];
            decimal[] lastTwo = branchTransactions[^2..];

            Console.WriteLine(
                $"{branches[branchIndex],-8}: moi nhat {newest:N0}; " +
                $"hai giao dich cuoi [{string.Join(", ", lastTwo)}]");
        }

        // Range trên mảng tạo một mảng mới (shallow copy các phần tử).
        string[] centralBranches = branches[1..];
        centralBranches[0] = "Da Nang - Central";
        Console.WriteLine($"\nMang goc     : {string.Join(" | ", branches)}");
        Console.WriteLine($"Mang cat moi : {string.Join(" | ", centralBranches)}");

        // Hai biến cùng giữ một reference tới đúng một mảng.
        decimal[] original = transactions[0];
        decimal[] alias = original;
        alias[0] = 9_999_000m;
        Console.WriteLine($"\noriginal[0] sau khi sua qua alias: {original[0]:N0}");
        Console.WriteLine($"Cung object mang: {ReferenceEquals(original, alias)}");

        // string là immutable: phép biến đổi trả về một string object khác.
        string campaign = "sale";
        string upperCampaign = campaign.ToUpperInvariant();
        Console.WriteLine($"\nChuoi goc: {campaign}; chuoi moi: {upperCampaign}");
        Console.WriteLine($"Cung object chuoi: {ReferenceEquals(campaign, upperCampaign)}");

        // .NET lưu string bằng UTF-16.
        string label = "A😀B";
        Console.WriteLine($"\nlabel       : {label}");
        Console.WriteLine($"Length      : {label.Length} UTF-16 code units");
        Console.WriteLine($"Rune count  : {label.EnumerateRunes().Count()} Unicode scalar values");

        Console.Write("Cac Rune    : ");
        foreach (Rune rune in label.EnumerateRunes())
        {
            Console.Write($"U+{rune.Value:X} ");
        }

        Console.WriteLine();
    }
}
```

Kết quả chính (định dạng số có thể khác đôi chút theo locale của máy):

```text
=== Ke hoach theo chi nhanh ===
Ha Noi  : 40,500,000 VND
Da Nang : 30,500,000 VND
Can Tho : 28,500,000 VND

original[0] sau khi sua qua alias: 9,999,000
Cung object mang: True

Chuoi goc: sale; chuoi moi: SALE
Cung object chuoi: False

label       : A😀B
Length      : 4 UTF-16 code units
Rune count  : 3 Unicode scalar values
Cac Rune    : U+41 U+1F600 U+42
```

### Walkthrough — execution / state / cost

1. Ba hàng kế hoạch cộng thành 40.5M,30.5M,28.5M.
2. Mỗi hàng giao dịch là object mảng riêng; ^1 lấy cuối, ^2.. tạo bản cắt hai phần tử.
3. Alias original cùng mảng giao dịch đầu; gán qua alias làm ô đầu thành9999000.
4. ToUpperInvariant trả text mới khi cần thay nội dung; Rune đi qua chuỗi. Cắt k phần tử tốn O(k) bộ nhớ/copy, duyệt bảng tốn tổng số ô.

### Mini-check

Nếu phần tử mảng là Account thay vì decimal, sửa Balance qua bản cắt có đổi object gốc không?

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1 Mảng một chiều

`T[]` là một object có độ dài cố định. Chỉ số hợp lệ bắt đầu từ `0` và kết thúc ở `Length - 1`:

```csharp
string[] branches = ["Ha Noi", "Da Nang", "Can Tho"];
string first = branches[0];
string last = branches[branches.Length - 1];
```

`branches.Length` là `3`; truy cập `branches[3]` ném `IndexOutOfRangeException`. “Độ dài cố định” nghĩa là không thêm ô vào chính object mảng đó. Bạn vẫn có thể thay giá trị trong từng ô nếu kiểu phần tử cho phép.

### 4.2 Mảng chữ nhật `T[,]`

`decimal[,] plannedRevenue` là **một object mảng hai chiều**. Runtime lưu metadata về số chiều và độ dài từng chiều:

```text
plannedRevenue (reference)
        |
        v
+---------------------------------------+
| decimal[3,3]                          |
| [0,0] [0,1] [0,2]                    |
| [1,0] [1,1] [1,2]                    |
| [2,0] [2,1] [2,2]                    |
+---------------------------------------+
```

- `GetLength(0)` trả số hàng.
- `GetLength(1)` trả số cột.
- `Rank` trả số chiều, ở đây là `2`.
- Truy cập một ô bằng hai chỉ số: `plannedRevenue[row, column]`.

Loại này phù hợp khi mọi hàng có cùng cấu trúc, ví dụ ma trận, bàn cờ hoặc bảng số liệu cố định.

### 4.3 Mảng răng cưa `T[][]`

`decimal[][]` thực chất là **một mảng chứa các reference tới những mảng con**:

```text
transactions
    |
    v
+----------+       +---------------------------+
| ref [0] -+------>| decimal[4]: 1.2, .8, 1.5, .9 |
| ref [1] -+----+  +---------------------------+
| ref [2] -+--+ |  +-------------------+
+----------+  | +->| decimal[2]: .7, 1.1 |
              |    +-------------------+
              +--->+------------------------+
                   | decimal[3]: .5, .65, .9 |
                   +------------------------+
```

Vì từng mảng con là object riêng, chúng có thể có độ dài khác nhau. `transactions.Length` là số hàng; `transactions[row].Length` là số phần tử của riêng hàng đó. Một ô của mảng ngoài cũng có thể là `null` nếu chưa gán mảng con; khi bật nullable reference types, nên khai báo đúng ý định nếu `null` được phép.

### 4.4 `Index` và toán tử `^`

`^n` đếm từ cuối:

- `^1` là phần tử cuối.
- `^2` là phần tử áp chót.
- `^0` biểu diễn vị trí ngay sau phần tử cuối, nên không hợp lệ khi dùng để đọc một phần tử.

Về cơ chế, với mảng độ dài `length`, vị trí `^n` tương ứng `length - n`. Vì thế `values[^1]` tương đương `values[values.Length - 1]`.

### 4.5 `Range` và toán tử `..`

Range có biên đầu **inclusive** và biên cuối **exclusive**:

```csharp
int[] values = [10, 20, 30, 40, 50];
int[] a = values[1..4];  // 20, 30, 40
int[] b = values[..2];   // 10, 20
int[] c = values[3..];   // 40, 50
int[] d = values[^2..];  // 40, 50
```

Khi range áp dụng lên array, .NET tạo **một array object mới** và copy các phần tử trong đoạn. Với value type, giá trị được copy. Với reference type, reference được copy; object mà reference trỏ tới không được clone. Đây là shallow copy.

Trong ví dụ, `branches[1..]` tạo mảng `centralBranches` mới. Đổi ô `centralBranches[0]` không đổi ô `branches[1]` vì hai ô thuộc hai object mảng khác nhau.

### 4.6 Bộ nhớ của array reference

Giả sử method đang chạy có:

```csharp
decimal[] original = transactions[0];
decimal[] alias = original;
alias[0] = 9_999_000m;
```

Mô hình đơn giản hóa:

```text
Stack frame Main                         Managed heap
+-----------------------+                +-------------------------+
| original: reference --+--------------->| decimal[] object        |
| alias:    reference --+--------------->| [9999000, 800000, ...] |
+-----------------------+                +-------------------------+
```

Phép gán `alias = original` copy **reference**, không copy array object. Do đó sửa `alias[0]` cũng quan sát được qua `original[0]`. Muốn mảng độc lập, phải tạo object mới, chẳng hạn `decimal[] copy = original[..];`.

### 4.7 `string` immutable nhưng vẫn là reference type

`string` là class (`System.String`), vì vậy biến `string` giữ reference hoặc `null`. Tuy nhiên, nội dung của một string object không thể bị sửa sau khi object được tạo:

```csharp
string campaign = "sale";
string upperCampaign = campaign.ToUpperInvariant();
```

`ToUpperInvariant()` không sửa object chứa `"sale"`; nó trả về reference tới một string mang nội dung kết quả. Những thao tác như `Replace`, `Trim`, nối chuỗi và đổi hoa/thường cũng theo nguyên tắc này. Nếu thao tác không làm nội dung thay đổi, một API được phép trả lại chính reference cũ; đừng dựa vào `ReferenceEquals` để suy luận nội dung chuỗi.

```text
Stack frame Main                         Managed heap / intern pool
+----------------------------+           +------------------+
| campaign      ref ----------+---------->| "sale"           |
| upperCampaign ref ----------+----+      +------------------+
+----------------------------+    |      +------------------+
                                  +----->| "SALE"           |
                                         +------------------+
```

### 4.8 UTF-16: `Length` đang đếm gì?

.NET biểu diễn `string` bằng chuỗi UTF-16 code unit; mỗi code unit là một giá trị 16 bit (`char`).

`"A😀B"` có:

```text
Ký hiệu nhìn thấy:      A       😀               B
Unicode scalar:       U+0041  U+1F600          U+0042
UTF-16 code unit:      0041    D83D DE00        0042
Chỉ số char:             0       1    2           3
```

Emoji `😀` cần một surrogate pair gồm hai `char`, nên `label.Length` là `4`, không phải `3`. `label[1]` chỉ lấy high surrogate, chưa phải một Unicode scalar hoàn chỉnh. Khi xử lý Unicode scalar value, duyệt `label.EnumerateRunes()` và dùng `System.Text.Rune`.

Ngay cả số `Rune` cũng chưa chắc bằng số grapheme cluster mà người dùng coi là một ký tự. Ví dụ một chữ có dấu có thể được cấu tạo từ base character và combining mark; emoji gia đình có thể gồm nhiều scalar nối bằng ZWJ. Khi cần tách “ký tự hiển thị”, dùng API xử lý text element như `System.Globalization.StringInfo` và kiểm thử với dữ liệu thật.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| T[,] | lưới chữ nhật | dùng chiều chung; một object mảng |
| T[][] | hàng riêng biệt | hợp độ dài khác; nhiều object và có thể có hàng null |
| string / Rune | code units / scalar values | chọn phép đếm theo contract Unicode, chưa phải grapheme |

### Misconception check

**Đúng hay sai?** new string[3] tạo ba chuỗi rỗng.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: ba ô reference ban đầu null.

</details>

**Đúng hay sai?** range trên array là view không cấp phát.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: tạo array mới; Span là bài nâng cao khác.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** index/range và alias.

- **Working Developer — dùng khi làm việc:** layout, null và Unicode.

- **Deep Dive — có thể quay lại sau:** grapheme/Span khi có driver.

### 5.1 Array là reference type, phần tử có kiểu riêng

Mọi array trong C# đều là reference type, kể cả `int[]` hay `decimal[,]`. Nhưng ô trong array tuân theo kiểu phần tử:

- `int[]`: mỗi ô chứa trực tiếp một giá trị `int`.
- `Customer[]`: mỗi ô chứa một reference tới `Customer` hoặc `null`.
- `int[][]`: mỗi ô của mảng ngoài chứa một reference tới một `int[]`.

`new int[3]` tạo một array object mới và mọi ô được gán default value (`0`). `new string[3]` tạo array object mới và mọi ô ban đầu là `null`; nullable analysis không theo dõi đầy đủ trạng thái từng ô nên không bảo đảm cảnh báo tại đây. Hãy gán các ô trước khi đọc hoặc dùng `string?[]` nếu `null` là trạng thái hợp lệ.

### 5.2 Khởi tạo collection expression

C# hiện đại cho phép collection expression:

```csharp
int[] numbers = [1, 2, 3];
string[][] groups = [["A", "B"], ["C"]];
```

Target type bên trái giúp compiler biết cần tạo kiểu gì. Cú pháp cũ `new[] { 1, 2, 3 }` vẫn hợp lệ. Với người mới, hãy ghi rõ kiểu biến nếu việc suy luận làm code khó đọc.

### 5.3 Duyệt bằng `for` hay `foreach`

- Dùng `for` khi cần chỉ số, cần sửa ô, hoặc phối hợp nhiều array theo cùng index.
- Dùng `foreach` khi chỉ cần đọc lần lượt từng giá trị.
- Với rectangular array, `foreach` duyệt toàn bộ ô theo thứ tự nhưng không cung cấp cặp `row`, `column`; nested `for` thường rõ hơn.

`foreach (decimal amount in transactions[0])` copy giá trị `decimal` hiện tại vào biến lặp; biến lặp của dạng `foreach` này không cho phép gán lại (compiler từ chối). Muốn cập nhật ô, dùng chỉ số.

### 5.4 So sánh string

`==` trên `string` so sánh nội dung theo ordinal, case-sensitive, không dùng reference identity như nhiều class thông thường. Với quy tắc rõ ràng, dùng overload có `StringComparison`:

```csharp
bool sameCode = string.Equals(left, right, StringComparison.OrdinalIgnoreCase);
```

Mã định danh kỹ thuật thường dùng `Ordinal`/`OrdinalIgnoreCase`; văn bản cho người dùng có thể cần culture phù hợp. Đừng gọi `ToLower()` chỉ để so sánh vì tạo string mới và dễ dùng sai quy tắc culture.

### 5.5 Khi nào không nên dùng array?

Array phù hợp khi số phần tử cố định hoặc khi API cần vùng dữ liệu liên tiếp. Nếu cần thêm/xóa phần tử thường xuyên, `List<T>` thường phù hợp hơn; bài [Collection: `List`, `Dictionary`, `HashSet`, `Queue`, `Stack`](./13-collection-list-dictionary-hashset-queue-stack.md) sẽ trình bày sau.

### Đào sâu (có thể quay lại sau)

“Reference nằm trên stack” chỉ là mô hình thường gặp cho local variable đồng bộ. JIT có thể giữ biến trong register, và reference cũng có thể nằm trong field của một heap object. Điều quan trọng về ngữ nghĩa là hai biến đang giữ cùng định danh object.

Tính immutable giúp một string object được chia sẻ an toàn. Với rất nhiều phép nối trong vòng lặp, hãy dùng `StringBuilder` để tránh tạo dãy object trung gian không cần thiết.

## 6. Lỗi thường gặp

### 6.1 Dùng `<= Length`

Sai:

```csharp
for (int i = 0; i <= values.Length; i++)
{
    Console.WriteLine(values[i]);
}
```

Lượt cuối có `i == Length`, vượt chỉ số. Dùng `i < values.Length`.

### 6.2 Nhầm `GetLength` với `Length`

`matrix.Length` là tổng số ô. `matrix.GetLength(0)` và `matrix.GetLength(1)` mới là độ dài từng chiều. Dùng `matrix.Length` làm giới hạn cho biến hàng sẽ vượt biên.

### 6.3 Giả định mọi hàng jagged đều tồn tại và dài như nhau

Không viết `items[row][column]` trước khi chắc rằng hàng không `null` và `column < items[row].Length`. Khởi tạo đầy đủ hoặc kiểm tra điều kiện theo từng hàng.

### 6.4 Nghĩ range là một view không cấp phát

`array[start..end]` tạo array mới. Cắt liên tục trong hot path có thể tạo nhiều allocation. Sau khi học sâu hơn, dùng `Span<T>`/`ReadOnlySpan<T>` khi cần view không copy; không tối ưu sớm nếu chưa đo hiệu năng.

### 6.5 Dùng `^0` để lấy phần tử cuối

`^0` là vị trí sau cuối và chỉ hữu ích như một boundary của range. Phần tử cuối là `^1`.

### 6.6 Sửa kết quả string nhưng quên nhận reference mới

Sai:

```csharp
name.Trim();
```

Đúng:

```csharp
name = name.Trim();
```

### 6.7 Cắt string tại một `char` nằm giữa surrogate pair

`label[..2]` có thể kết thúc sau high surrogate và tạo dữ liệu Unicode không hợp lệ về mặt scalar. Nếu boundary đến từ nghiệp vụ “ký tự”, hãy duyệt `Rune` hoặc text element thay vì cắt tùy ý theo chỉ số `char`.

### 6.8 Dùng `ReferenceEquals` để so sánh nội dung string

String interning có thể khiến hai literal dùng chung object, còn string tạo lúc chạy có thể là object khác dù nội dung bằng nhau. So sánh nội dung bằng `string.Equals` với `StringComparison` phù hợp.

## 7. Khi nào KHÔNG dùng

Không dùng Length như số ký tự nhìn thấy trong mọi text. Không cắt mảng liên tục trong vòng nóng chỉ để tránh index; đo trước khi chuyển sang Span ở module sau.

## 8. Production notes & scale check

Ba chi nhánh đủ để học layout và index. Gate kiểm tra cả dòng jagged, bản cắt, alias và Unicode. Nullable analysis không tự đảm bảo mọi ô string[] đã khởi tạo. Giới hạn title theo UTF-16 phải được gọi đúng tên.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Tổng và trung bình mảng một chiều

Nhập 7 nhiệt độ vào `double[]`, in nhiệt độ cao nhất, thấp nhất và trung bình.

Gợi ý: khởi tạo `min` và `max` bằng phần tử đầu; xử lý riêng trường hợp mảng rỗng nếu bạn mở rộng chương trình.

### Bài 2 — Bảng điểm chữ nhật

Dùng `double[,]` lưu điểm của 4 học viên ở 3 môn. In điểm trung bình của từng học viên và từng môn.

Gợi ý: vòng lặp ngoài thay đổi theo đối tượng cần tổng hợp; dùng `GetLength(dimension)` thay vì ghi cứng `4` và `3` trong logic.

### Bài 3 — Lịch làm việc răng cưa

Dùng `string[][]` lưu các ca làm của từng nhân viên, trong đó mỗi người có số ca khác nhau. In ca cuối cùng của từng người bằng `^` và toàn bộ ca trừ ca đầu bằng range.

Gợi ý: trước khi dùng `^1`, kiểm tra mảng con có ít nhất một phần tử.

### Bài 4 — Kiểm chứng shallow copy

Tạo class nhỏ `Product`, một `Product[]`, rồi tạo bản cắt bằng `products[..2]`. Thay một field/property của object qua mảng cắt và quan sát mảng gốc; sau đó gán một object mới vào ô của mảng cắt và quan sát lại.

Gợi ý: range tạo mảng mới nhưng copy các reference đang nằm trong ô; phân biệt “sửa object được trỏ tới” với “đổi reference trong ô”.

### Bài 5 — Báo cáo Unicode

Với các chuỗi `"café"`, `"😀"`, `"👨‍👩‍👧‍👦"`, hãy in `Length`, số `Rune` và số text element.

Gợi ý: dùng `EnumerateRunes()` và `System.Globalization.StringInfo.ParseCombiningCharacters()`. Giải thích vì sao ba con số có thể khác nhau.

## 10. Bài tập tích hợp liên module — Judgment

So sánh chuỗi byte C Module 02 với string C#: ký tự tiếng Việt/emoji thay đổi cách tính capacity và độ dài ra sao? Chọn giới hạn byte lưu trữ hoặc ký tự UI theo requirement.

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. ^1 chỉ phần tử nào?
2. Mảng cắt có chia sẻ container không?
3. Length và Rune count khác nhau vì sao?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

Bạn hoàn thành bài khi có thể tự trả lời:

- [ ] Tôi chọn được `T[]`, `T[,]` hoặc `T[][]` dựa trên hình dạng dữ liệu.
- [ ] Tôi dùng đúng `Length`, `GetLength()` và giới hạn chỉ số.
- [ ] Tôi giải thích được `^1`, `1..4`, `..^1` và biên cuối exclusive.
- [ ] Tôi biết range trên array tạo object array mới và chỉ shallow-copy phần tử.
- [ ] Tôi vẽ được hai reference cùng trỏ tới một array object.
- [ ] Tôi giải thích được vì sao thao tác trên immutable `string` thường trả object mới.
- [ ] Tôi biết `string.Length` đếm UTF-16 code unit, không phải luôn là ký tự hiển thị.

Điều hướng:

- Bài tiên quyết: [Stack, heap, value type và reference type](./05-stack-heap-value-type-reference-type.md)
- Bài tiếp theo: [Class, object và constructor](./07-class-object-constructor.md)
