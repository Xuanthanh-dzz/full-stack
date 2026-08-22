# Đệ quy và call stack

## 1. Mục tiêu

Sau bài này, bạn có thể:

- nhận ra bài toán có cấu trúc tự lặp lại và giải nó bằng **đệ quy**;
- viết đúng hai phần bắt buộc của mọi hàm đệ quy: **base case** và **recursive case**;
- theo dõi cách **call stack** lớn lên khi gọi vào và co lại khi trả về;
- giải thích vì sao Fibonacci đệ quy ngây thơ là `O(2^n)` và vì sao đó là vấn đề;
- biết khi nào đệ quy gây `StackOverflowException` và cách chuyển sang vòng lặp;
- chuyển đổi qua lại giữa lời giải đệ quy và lời giải lặp.

## 2. Bài toán mở đầu

Nhiều bài toán có dạng "giải bài lớn = làm một bước rồi giải bài nhỏ hơn cùng loại":

- Tính `n!` = `n × (n-1)!`.
- Tính tổng một mảng = phần tử đầu + tổng phần còn lại.
- Duyệt một cây thư mục = xử lý thư mục này + duyệt từng thư mục con.

Với những bài như vậy, viết bằng vòng lặp đôi khi phải tự quản lý một ngăn xếp thủ công. Đệ quy để chính **call stack** của chương trình làm việc đó cho bạn: mỗi lời gọi hàm tự động có vùng nhớ riêng cho tham số và biến cục bộ (bạn đã gặp khái niệm này ở [module 01, bài 10 — ngăn xếp lời gọi hàm](../01-nen-tang-lap-trinh/10-ngan-xep-loi-goi-ham.md)). Bài này biến call stack đó thành thứ nhìn thấy được, và chỉ ra cái bẫy khi dùng đệ quy sai cách.

## 3. Lời giải bằng code

Tạo project .NET 9:

```bash
dotnet new console --name RecursionDemo --framework net9.0 --use-program-main
cd RecursionDemo
```

Thay `RecursionDemo.csproj` bằng cấu hình chuẩn của module (như bài [01](./01-big-o-thoi-gian-va-bo-nho.md), có `Nullable` và `TreatWarningsAsErrors`), rồi thay `Program.cs` bằng:

```csharp
namespace RecursionDemo;

internal static class Program
{
    private static void Main()
    {
        Console.WriteLine("== Giai thừa 4! với dấu vết call stack ==");
        long result = Factorial(4, depth: 0);
        Console.WriteLine($"Kết quả: 4! = {result}");

        Console.WriteLine();
        Console.WriteLine("== Fibonacci đệ quy ngây thơ: số lời gọi bùng nổ ==");
        Console.WriteLine($"{"n",4} | {"fib(n)",8} | {"số lời gọi",12}");
        Console.WriteLine(new string('-', 32));
        foreach (int n in new[] { 5, 10, 20, 30 })
        {
            _callCount = 0;
            long value = Fibonacci(n);
            Console.WriteLine($"{n,4} | {value,8} | {_callCount,12}");
        }

        Console.WriteLine();
        Console.WriteLine("== Tổng mảng bằng đệ quy ==");
        int[] data = { 3, 1, 4, 1, 5, 9 };
        Console.WriteLine($"Mảng: [{string.Join(", ", data)}]");
        Console.WriteLine($"Tổng = {SumFrom(data, 0)}");
    }

    // Mỗi lời gọi là một stack frame mới; indent theo depth để "thấy" ngăn xếp.
    private static long Factorial(int n, int depth)
    {
        string pad = new string(' ', depth * 2);
        Console.WriteLine($"{pad}-> gọi Factorial({n})");
        long value;
        if (n <= 1)
        {
            value = 1; // base case: dừng đệ quy
        }
        else
        {
            value = n * Factorial(n - 1, depth + 1); // recursive case
        }
        Console.WriteLine($"{pad}<- Factorial({n}) trả {value}");
        return value;
    }

    private static long _callCount;

    private static long Fibonacci(int n)
    {
        _callCount++;
        if (n < 2)
        {
            return n; // base case: fib(0)=0, fib(1)=1
        }
        return Fibonacci(n - 1) + Fibonacci(n - 2);
    }

    // Đệ quy trên mảng: base case là "hết phần tử".
    private static int SumFrom(int[] data, int index)
    {
        if (index == data.Length)
        {
            return 0;
        }
        return data[index] + SumFrom(data, index + 1);
    }
}
```

Build và chạy:

```bash
dotnet build --configuration Release
dotnet run --configuration Release --no-build
```

Kết quả:

```text
== Giai thừa 4! với dấu vết call stack ==
-> gọi Factorial(4)
  -> gọi Factorial(3)
    -> gọi Factorial(2)
      -> gọi Factorial(1)
      <- Factorial(1) trả 1
    <- Factorial(2) trả 2
  <- Factorial(3) trả 6
<- Factorial(4) trả 24
Kết quả: 4! = 24

== Fibonacci đệ quy ngây thơ: số lời gọi bùng nổ ==
   n |   fib(n) |   số lời gọi
--------------------------------
   5 |        5 |           15
  10 |       55 |          177
  20 |     6765 |        21891
  30 |   832040 |      2692537

== Tổng mảng bằng đệ quy ==
Mảng: [3, 1, 4, 1, 5, 9]
Tổng = 23
```

## 4. Giải thích cơ chế

### 4.1 Base case và recursive case

Mọi hàm đệ quy đúng đều có hai nhánh:

- **Base case** — điều kiện dừng, trả kết quả trực tiếp mà không gọi lại chính nó. `Factorial` dừng ở `n <= 1`; `Fibonacci` dừng ở `n < 2`; `SumFrom` dừng khi `index == data.Length`.
- **Recursive case** — gọi lại chính nó với đầu vào **nhỏ hơn**, tiến dần về base case.

Nếu thiếu base case, hoặc recursive case không thu nhỏ đầu vào, đệ quy chạy mãi và làm tràn call stack. Quy tắc vàng: mỗi lời gọi đệ quy phải tiến gần hơn tới điều kiện dừng.

### 4.2 Call stack lớn lên rồi co lại

Dấu vết của `Factorial(4)` cho thấy chính xác call stack hoạt động thế nào. Mỗi mũi tên `->` là một frame được **push** lên stack; mỗi mũi tên `<-` là một frame **pop** ra sau khi trả giá trị:

```text
Thời gian ---->

push  Factorial(4)          [4]
push    Factorial(3)        [4][3]
push      Factorial(2)      [4][3][2]
push        Factorial(1)    [4][3][2][1]  <- chạm base case
pop         trả 1           [4][3][2]
pop       2*1 = 2           [4][3]
pop     3*2 = 6             [4]
pop   4*6 = 24              []            <- stack rỗng, xong
```

Phần "gọi vào" đi xuống tới base case; phần "trả về" đi ngược lên, nhân dồn kết quả. Mỗi frame giữ **bản sao riêng** của tham số `n`: frame của `Factorial(2)` có `n = 2` hoàn toàn độc lập với `n = 3` ở frame ngoài. Đó là lý do đệ quy không cần biến toàn cục để nhớ trạng thái từng mức.

### 4.3 Vì sao Fibonacci ngây thơ là `O(2^n)`

`Fibonacci(n)` gọi `Fibonacci(n-1)` **và** `Fibonacci(n-2)`. Cây lời gọi phân nhánh đôi ở gần như mỗi mức, và tệ hơn nữa là **tính lại** cùng một giá trị nhiều lần:

```text
                    fib(5)
              /                \
          fib(4)              fib(3)
         /      \            /      \
     fib(3)   fib(2)     fib(2)   fib(1)
     /   \     /  \       /  \
 fib(2) fib(1) ...       ...        (fib(2), fib(3) bị tính lặp lại)
```

Cột "số lời gọi" trong output nói lên tất cả: `fib(30)` cần hơn **2,6 triệu** lời gọi để ra một con số. Số lời gọi tăng gần gấp đôi mỗi khi `n` tăng 1 — đúng dáng `O(2^n)` mà bài [01](./01-big-o-thoi-gian-va-bo-nho.md) cảnh báo. Bài [17 — dynamic programming](./17-dynamic-programming.md) sẽ chỉ cách nhớ lại kết quả đã tính (memoization) để hạ xuống `O(n)`.

### 4.4 Đệ quy đổi được thành vòng lặp

Bất kỳ đệ quy nào cũng có thể viết lại bằng vòng lặp (đôi khi cần một stack thủ công). `Factorial` là ví dụ dễ nhất:

```csharp
static long FactorialLoop(int n)
{
    long value = 1;
    for (int i = 2; i <= n; i++)
    {
        value *= i;
    }
    return value;
}
```

Bản lặp không đẩy frame nào lên call stack ngoài chính nó, nên dùng bộ nhớ `O(1)` thay vì `O(n)`. Với bài toán tuyến tính đơn giản, vòng lặp thường gọn và an toàn hơn. Đệ quy tỏa sáng khi cấu trúc dữ liệu **tự phân nhánh** — cây và đồ thị ở các bài sau.

### Đào sâu (có thể quay lại sau)

- **Bộ nhớ của đệ quy.** Độ sâu đệ quy `d` chiếm `O(d)` bộ nhớ stack, vì `d` frame cùng tồn tại lúc chạm base case. `Factorial(4)` có độ sâu 4 nên 4 frame chồng lên nhau ở đỉnh.
- **Tail call.** Một số ngôn ngữ tối ưu "tail recursion" (lời gọi đệ quy là thao tác cuối) thành vòng lặp, dùng `O(1)` stack. C#/.NET **không bảo đảm** tối ưu này, nên đừng dựa vào nó để tránh tràn stack; hãy tự chuyển sang vòng lặp khi độ sâu lớn.
- **Đệ quy lẫn nhau (mutual recursion).** Hàm `A` gọi `B`, `B` gọi lại `A`. Vẫn cần một base case ở đâu đó trong vòng để dừng.

## 5. Kiến thức nền

### Ba câu hỏi để viết một hàm đệ quy

1. **Base case là gì?** Trường hợp nhỏ nhất trả lời được ngay, không cần gọi lại.
2. **Thu nhỏ thế nào?** Làm sao biến bài toán thành phiên bản nhỏ hơn cùng loại.
3. **Ghép kết quả ra sao?** Từ kết quả của bài nhỏ, tạo ra kết quả của bài lớn (với `Factorial` là phép nhân `n *`).

Trả lời được ba câu này là viết được hàm đệ quy.

### Đệ quy và ngăn xếp là hai mặt của một thứ

Call stack chính là một cấu trúc **stack** (ngăn xếp) — vào sau ra trước. Bài [05](./05-stack-queue-va-deque.md) sẽ dựng lại stack như một cấu trúc dữ liệu tường minh, và bạn sẽ thấy có thể thay đệ quy bằng một `Stack<T>` do mình quản lý. Hai cách tương đương về mặt tính toán.

### Khi nào chọn đệ quy

- **Nên dùng:** duyệt cây, đồ thị; chia để trị (merge sort, quicksort ở bài [13](./13-sorting.md)); backtracking (bài [16](./16-backtracking.md)); bài toán định nghĩa tự nhiên theo chính nó.
- **Nên cân nhắc vòng lặp:** lặp tuyến tính đơn giản; độ sâu có thể rất lớn (nguy cơ tràn stack); vòng nóng cần hiệu năng tối đa.

## 6. Lỗi thường gặp

### Quên base case hoặc không tiến về nó

`Factorial(n)` gọi `Factorial(n)` (không giảm) sẽ đệ quy vô hạn. Luôn kiểm tra: mỗi lời gọi con có đầu vào *thực sự nhỏ hơn* và có đường chạm base case không?

### `StackOverflowException` với độ sâu lớn

Đệ quy tuyến tính sâu hàng chục nghìn mức (ví dụ `SumFrom` trên mảng rất dài) có thể làm tràn stack. Khác với hầu hết exception, `StackOverflowException` **không bắt được** bằng `try/catch` và làm sập tiến trình. Với dữ liệu sâu, hãy dùng vòng lặp hoặc một `Stack<T>` tường minh.

### Tính lại cùng một bài toán con

Fibonacci ngây thơ là ví dụ điển hình: cùng `fib(k)` bị tính đi tính lại. Nếu thấy cây đệ quy trùng lặp bài toán con, đó là dấu hiệu cần memoization hoặc quy hoạch động (bài [17](./17-dynamic-programming.md)).

### Truyền trạng thái bằng biến toàn cục sai cách

Dùng một biến `static` để tích lũy kết quả giữa các lời gọi (ngoài mục đích đếm như `_callCount` ở đây) khiến hàm không thể chạy song song và khó kiểm thử. Hãy truyền trạng thái qua **tham số** và **giá trị trả về**; mỗi frame giữ phần của nó.

### Nhầm "đệ quy" với "luôn thanh lịch"

Đệ quy gọn về mặt diễn đạt nhưng không miễn phí: mỗi frame tốn bộ nhớ và thời gian đẩy/lấy. Với bài tuyến tính, vòng lặp thường vừa nhanh vừa an toàn hơn.

## 7. Bài tập

### Bài 1 — Đếm ngược đệ quy

Viết `CountDown(int n)` in các số từ `n` về `1` rồi in `"Xong"`. Chỉ ra base case và recursive case.

**Gợi ý:** in `n` trước rồi gọi `CountDown(n - 1)`; base case là `n == 0`.

### Bài 2 — Lũy thừa `O(log n)`

Viết `Power(baseValue, exp)` tính `baseValue^exp`. Bản ngây thơ là `O(exp)`; hãy làm bản `O(log exp)` bằng cách bình phương: `x^exp = (x^(exp/2))^2` (nhân thêm `x` khi `exp` lẻ).

**Gợi ý:** đây là "chia để trị"; đếm số lời gọi để xác nhận nó là họ logarit như cột `O(log n)` ở bài 01.

### Bài 3 — Đảo ngược chuỗi bằng đệ quy

Viết hàm nhận `string` và trả về chuỗi đảo ngược, không dùng vòng lặp.

**Gợi ý:** ký tự cuối + đảo ngược phần đầu; base case là chuỗi rỗng hoặc một ký tự.

### Bài 4 — Đệ quy sang vòng lặp

Chuyển `SumFrom` trong bài thành một vòng `for` không đệ quy. So sánh độ phức tạp bộ nhớ của hai bản.

**Gợi ý:** bản lặp dùng `O(1)` stack; bản đệ quy dùng `O(n)` vì `n` frame cùng tồn tại.

### Bài 5 — Tìm độ sâu tối đa

Chạy `SumFrom` (hoặc một hàm đệ quy tuyến tính bất kỳ) với mảng ngày càng dài cho tới khi tràn stack. Ghi lại độ sâu xấp xỉ gây tràn, rồi giải thích vì sao bản lặp không gặp giới hạn đó.

**Gợi ý:** tăng kích thước theo cấp số nhân (10^4, 10^5, ...) để khoanh vùng; nhớ rằng không bắt được `StackOverflowException`.

## 8. Checklist tự đánh giá và điều hướng

- [ ] Tôi viết được hàm đệ quy với base case và recursive case rõ ràng.
- [ ] Tôi vẽ được call stack push/pop cho một lời gọi đệ quy cụ thể.
- [ ] Tôi giải thích được vì sao mỗi frame có bản sao tham số riêng.
- [ ] Tôi nhận ra Fibonacci ngây thơ là `O(2^n)` do phân nhánh và tính lặp.
- [ ] Tôi biết đệ quy sâu có thể gây `StackOverflowException` không bắt được.
- [ ] Tôi chuyển được một đệ quy tuyến tính thành vòng lặp và ngược lại.

Điều hướng:

- Bài prerequisite: [Big-O về thời gian và bộ nhớ](./01-big-o-thoi-gian-va-bo-nho.md)
- Ôn lại nền tảng: [Ngăn xếp lời gọi hàm](../01-nen-tang-lap-trinh/10-ngan-xep-loi-goi-ham.md), [Hàm: tham số, giá trị trả về](../01-nen-tang-lap-trinh/09-ham-tham-so-gia-tri-tra-ve.md)
- Bài tiếp theo: [Mảng và dynamic array](./03-mang-va-dynamic-array.md)
