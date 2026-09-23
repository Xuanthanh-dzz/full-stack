# Stack, heap, value type và reference type

> **Last verified:** 2026-09-22 — published samples/contracts PASS; CI và maintainer review xem PROGRESS  
> **Baseline:** .NET SDK 9.0.121 · net9.0 · C# 13 · nullable enabled · warnings as errors  
> **Review cycle:** 180 days  
> **Re-verify triggers:** đổi sample/contract, SDK/runtime, culture hoặc serialization; CI failure

## TL;DR

- Value type được copy theo giá trị; reference type copy đường truy cập cùng object.
- Vẽ object graph để biết thao tác nào sửa bản sao và thao tác nào sửa dữ liệu chia sẻ.
- Quy tắc copy không đồng nghĩa value luôn nằm stack hoặc reference luôn nằm heap.

## 1. Mục tiêu

Sau bài này, bạn có thể:

- phân biệt **ngữ nghĩa type** với **vị trí storage**;
- giải thích vì sao “value type luôn ở stack, reference type luôn ở heap” là sai;
- theo dõi từng phép gán value type và reference type;
- chỉ ra mỗi lần `new` một class/array tạo object có identity riêng trên managed heap;
- phân biệt reference variable với object mà nó trỏ tới và nhận ra alias;
- mô tả value-type field/array element được lưu inline, reference field/element chứa reference;
- dự đoán tác động khi truyền value type hoặc reference type bằng parameter mặc định;
- giải thích boxing, unboxing và bản copy được tạo;
- dùng sơ đồ text để audit một object graph trước khi viết code phức tạp hơn.

## 2. Bài toán mở đầu

### Trực giác 60 giây

Chép tọa độ lên giấy mới cho bạn hai tọa độ độc lập. Chép địa chỉ tài khoản cho bạn hai cách tìm cùng một tài khoản. Nhìn tên biến không đủ biết dữ liệu có chung hay không.

### Từ vựng

| Thuật ngữ | Nghĩa đơn giản | Trong bài này |
|---|---|---|
| value type | kiểu có semantics copy dữ liệu của value | Coordinate |
| reference type | kiểu mà biến giữ reference tới object | Account |
| alias | đường truy cập khác tới cùng object | alias và primary |
| boxing | đặt bản sao value vào object để dùng như object | boxedCoordinate |

### Ví dụ nhỏ — tính tay trước

Coordinate A=(1,2); B=A; B.X=9 → A.X vẫn 1. Account A balance10; B=A; B.Balance=9 → A đọc được9.

Một lập trình viên viết chức năng giao hàng và tài khoản, rồi gặp bốn kết quả tưởng như mâu thuẫn:

1. Gán một `Coordinate` sang biến khác rồi sửa biến sau, biến đầu không đổi.
2. Gán một `Account` sang biến khác rồi sửa `Balance`, cả hai tên đều quan sát số dư mới.
3. Truyền `Account` vào method và sửa field thì caller thấy thay đổi; nhưng gán parameter sang `new Account(...)` thì caller vẫn trỏ object cũ.
4. Ép `Coordinate` sang `object`, sửa bản gốc rồi unbox, giá trị trong `object` không đổi.

Nếu chỉ học câu “stack nhanh, heap chậm” hoặc “struct ở stack, class ở heap”, ta không thể dự đoán đúng. Ta sẽ chạy một chương trình, đặt tên từng vùng nhớ logic và vẽ các reference đang trỏ tới đâu.

<a id="3-loi-giai-bang-code"></a>

## 3. Lời giải chạy được

Tạo project:

```bash
dotnet new console --name MemoryModel --framework net9.0 --use-program-main
cd MemoryModel
```

Thay `Program.cs` bằng:

```csharp
namespace MemoryModel;

internal static class Program
{
    private static void Main()
    {
        // Coordinate là value type. Phép gán copy toàn bộ value.
        Coordinate first = new(10, 20);
        Coordinate second = first;
        second.X = 99;

        Console.WriteLine($"Value assignment: first={first}, second={second}");

        // Account là reference type. Mỗi new Account tạo một object riêng.
        Account primary = new(100);       // object H1
        Account alias = primary;          // copy reference; vẫn trỏ H1
        alias.Balance -= 30;

        Account independent = new(100);   // object H2, khác H1
        Console.WriteLine(
            $"Reference assignment: primary={primary.Balance}, alias={alias.Balance}");
        Console.WriteLine(
            $"Two new objects are identical references: " +
            $"{ReferenceEquals(primary, independent)}");

        MoveValue(first);
        Console.WriteLine($"After value parameter: first={first}");

        Debit(primary, 10);
        Console.WriteLine($"After object mutation: primary={primary.Balance}");

        ReassignLocally(primary);          // tạo H3 nhưng không đổi primary
        Console.WriteLine($"After local reassignment: primary={primary.Balance}");

        // Basket là H4. DropOff nằm inline trong H4; Buyer là reference tới H1.
        Basket basket = new(primary, first);
        basket.DropOff.X = 30;
        Console.WriteLine(
            $"Inline field: first={first}, basket.DropOff={basket.DropOff}");

        // Array là object. Value-type elements nằm inline trong array object H5.
        Coordinate[] points = new Coordinate[2];
        points[0] = first;
        points[1] = second;
        points[0].X = 42;
        Console.WriteLine($"Value array: first={first}, points[0]={points[0]}");

        // Các element của reference-type array H6 là reference slot, ban đầu null.
        Account?[] accounts = new Account?[2];
        accounts[0] = primary;
        accounts[1] = independent;
        accounts[0]!.Balance -= 5;
        Console.WriteLine($"Reference array aliases H1: primary={primary.Balance}");

        // Boxing tạo object H7 chứa một COPY của first tại thời điểm boxing.
        object boxed = first;
        first.X = 777;

        // Unboxing rồi gán sang Coordinate lại tạo một value copy.
        Coordinate unboxed = (Coordinate)boxed;
        unboxed.X = 888;

        Console.WriteLine($"After boxing: first={first}");
        Console.WriteLine($"Value in box: {(Coordinate)boxed}");
        Console.WriteLine($"Unboxed copy: {unboxed}");
    }

    private static void MoveValue(Coordinate point)
    {
        // point là bản copy; sửa nó không sửa first ở caller.
        point.X = -1;
    }

    private static void Debit(Account account, int amount)
    {
        // Parameter là bản copy của reference tới H1; object H1 vẫn là cùng object.
        account.Balance -= amount;
    }

    private static void ReassignLocally(Account account)
    {
        // new tạo H3. Chỉ parameter local trỏ H3; primary của caller vẫn trỏ H1.
        account = new Account(999);
        account.Balance = 0;
    }
}

internal struct Coordinate
{
    public int X;
    public int Y;

    public Coordinate(int x, int y)
    {
        X = x;
        Y = y;
    }

    public override string ToString() => $"({X}, {Y})";
}

internal sealed class Account
{
    public int Balance;

    public Account(int balance)
    {
        Balance = balance;
    }
}

internal sealed class Basket
{
    // Value-type field chứa trực tiếp hai int của Coordinate trong Basket object.
    public Coordinate DropOff;

    // Reference-type field chứa reference, không chứa toàn bộ Account inline.
    public Account Buyer;

    public Basket(Account buyer, Coordinate dropOff)
    {
        Buyer = buyer;
        DropOff = dropOff;
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
Value assignment: first=(10, 20), second=(99, 20)
Reference assignment: primary=70, alias=70
Two new objects are identical references: False
After value parameter: first=(10, 20)
After object mutation: primary=60
After local reassignment: primary=60
Inline field: first=(10, 20), basket.DropOff=(30, 20)
Value array: first=(10, 20), points[0]=(42, 20)
Reference array aliases H1: primary=55
After boxing: first=(777, 20)
Value in box: (10, 20)
Unboxed copy: (888, 20)
```

Project đã được kiểm tra bằng .NET SDK `9.0.121`, target `net9.0`, không dùng package ngoài.

### Walkthrough — execution / state / cost

1. Hai Coordinate được copy; sửa second không sửa first.
2. primary/alias cùng Account: giảm qua alias rồi Debit cập nhật object từ 100→70→60.
3. Gán local parameter sang Account mới không chuyển reference của caller; mảng Account vẫn có thể giữ alias tới object cũ.
4. Box giữ bản sao (10,20), unbox tạo copy khác. Object graph quyết định reachability; vị trí vật lý local do runtime/JIT chọn. Copy struct theo kích thước, copy reference nhỏ nhưng không clone đích.

### Mini-check

Trong points[0] và accounts[0], thứ gì được copy khi gán từ biến ngoài? Vẽ từng mũi tên.

<a id="4-giai-thich-co-che"></a>

## 4. Cơ chế hoạt động

### 4.1. Hai câu hỏi phải tách riêng

Khi nhìn một biến, luôn hỏi riêng:

1. **Type có semantics gì?** Value type variable chứa value; reference type variable chứa managed reference hoặc `null`.
2. **Storage của value/reference đó đang ở đâu?** Local có thể ở stack frame/register; field nằm trong object chứa; element nằm trong array; boxed value nằm trong box object.

Không thể trả lời câu 2 chỉ bằng cách thấy keyword `struct`, `int` hoặc `class`.

### 4.2. Value assignment copy dữ liệu

Sau ba lệnh:

```csharp
Coordinate first = new(10, 20);
Coordinate second = first;
second.X = 99;
```

mô hình là:

```text
first  = { X: 10, Y: 20 }
second = { X: 99, Y: 20 }
```

`second = first` copy hai field `X`, `Y`. Không có mũi tên từ `second` về `first`. Sửa storage của `second` không đi ngược sửa `first`.

`new Coordinate(10, 20)` gọi constructor và tạo ra một **value**. Vì `Coordinate` là struct, keyword `new` ở đây không tự chứng minh có heap allocation và value không có object identity độc lập như class instance. Value cuối cùng được lưu theo context: ở đây là local `first` (JIT có thể dùng stack/register).

### 4.3. Reference assignment copy reference, không copy object

Ba lệnh:

```csharp
Account primary = new(100);      // H1
Account alias = primary;         // copy reference tới H1
Account independent = new(100);  // H2
```

tạo graph:

```text
primary -----┐
             +----> H1 Account { Balance: 100 }
alias -------┘

independent ------> H2 Account { Balance: 100 }
```

`alias = primary` copy **reference**, không chạy `new`, không tạo `Account` thứ hai và không deep-copy field. `alias.Balance -= 30` tìm H1 qua reference rồi sửa field trong H1, nên đọc qua `primary` cũng thấy `70`.

Hai lần `new Account(100)` tạo H1 và H2 là hai class object có identity riêng dù field bằng nhau. `ReferenceEquals(primary, independent)` là `false`. Mỗi lần expression `new` của reference type được đánh giá, một instance logic mới được tạo; runtime có thể tối ưu chi tiết vật lý nếu không thay đổi hành vi quan sát được, nhưng không được hợp nhất hai identity có thể quan sát thành một.

Managed heap có thể compact và di chuyển object. Vì vậy “H1” là nhãn identity logic trong bài, không phải địa chỉ số cố định mà code C# thông thường giữ.

### 4.4. Parameter mặc định luôn pass-by-value

`MoveValue(first)` copy value `{10,20}` vào parameter `point`. Method sửa bản copy; caller không đổi.

`Debit(primary, 10)` cũng pass-by-value, nhưng value được copy là reference tới H1:

```text
Main.primary ----> H1 Account
                      ^
Debit.account --------┘   (reference được copy)
```

`account.Balance -= amount` mutate H1 nên caller quan sát được. Đây **không phải** pass-by-reference; nó là pass-by-value của một reference.

Trong `ReassignLocally`:

```text
trước new:
Main.primary ----> H1 <---- ReassignLocally.account

sau account = new Account(999):
Main.primary ----> H1
ReassignLocally.account ----> H3
```

Gán lại parameter chỉ thay reference copy trong frame method. Khi method return, parameter biến mất; H3 không còn reachable trong sample và trở thành **eligible for garbage collection**, không có nghĩa bị giải phóng ngay. Muốn method gán lại reference của caller phải dùng `ref Account`, nhưng thường return object mới làm data flow rõ hơn.

### 4.5. Boxing tạo box object và copy value

Conversion:

```csharp
object boxed = first;
```

yêu cầu `object` reference trỏ một object, trong khi `first` là value type. CLR tạo một box object H7 chứa copy của `Coordinate`:

```text
trước khi sửa first:

first = { X:10, Y:20 }
boxed = ref H7 ----> H7 boxed Coordinate { X:10, Y:20 }

sau first.X = 777:

first = { X:777, Y:20 }
boxed = ref H7 ----> H7 boxed Coordinate { X:10, Y:20 }
```

Hai storage độc lập. Unboxing:

```csharp
Coordinate unboxed = (Coordinate)boxed;
```

kiểm tra box chứa đúng type `Coordinate`, rồi copy value ra `unboxed`. Sửa `unboxed` không sửa H7. Unbox sai exact value type, ví dụ box `int` rồi cast trực tiếp sang `long`, ném `InvalidCastException` dù numeric conversion `int → long` bình thường tồn tại.

Boxing thường tạo allocation và tăng việc cho GC. Generic API như `List<T>` giúp giữ value type theo type cụ thể và tránh nhiều boxing so với collection nhận `object`; vẫn phải đo allocation thực tế thay vì tối ưu theo suy đoán.

### 4.6. Stack và managed heap quản lý lifetime khác nhau

Mô hình nền:

```text
Call stack
- tổ chức invocation/frame theo LIFO
- frame logic chứa parameter/local và return information
- return/unwind kết thúc lifetime của storage thuộc frame
- recursion quá sâu có thể gây StackOverflowException

Managed heap
- chứa class object, array, box và các managed object khác
- lifetime theo reachability từ GC roots, không theo block lexical đơn giản
- Garbage Collector tự tìm object unreachable và thu hồi sau
- object có thể được di chuyển khi compact; managed reference được cập nhật
```

GC quản lý **memory**, không bảo đảm giải phóng tức thời file handle, socket hay database connection. Tài nguyên cần cleanup xác định dùng `IDisposable`/`using`; phần `finally` và cleanup được giới thiệu ở [bài 12 — Exception và xử lý lỗi](./12-exception-va-xu-ly-loi.md). Heap cũng không đồng nghĩa unmanaged memory; đây là managed heap của CLR.

### So sánh để chọn đúng

| Lựa chọn | Semantics — ý nghĩa | Cost, use case và khi không dùng |
|---|---|---|
| struct copy | copy field value | field reference bên trong vẫn có thể chia sẻ đích |
| class assignment | copy reference | mutation object thấy qua các alias |
| boxing/unboxing | copy value vào/ra object | có allocation khi box; cần đúng kiểu lúc unbox |

### Misconception check

**Đúng hay sai?** Reassign parameter Account sẽ đổi biến caller sang object mới.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: parameter mặc định là bản sao reference.

</details>

**Đúng hay sai?** Struct có field string nghĩa toàn bộ ký tự string nằm inline trong struct.

<details markdown="1">
<summary>Tự trả lời rồi mở giải thích</summary>

Sai: field chứa reference, không phải toàn bộ object chuỗi.

</details>

<a id="5-kien-thuc-nen"></a>

## 5. Kiến thức nền và prerequisites

### Ba tầng học

- **Beginner core — cần để đi tiếp:** vẽ copy/alias.

- **Working Developer — dùng khi làm việc:** boxing, field và array semantics.

- **Deep Dive — có thể quay lại sau:** JIT/storage khi có bằng chứng đo.

### Phân loại type

Value types gồm:

- các numeric type như `int`, `double`, `decimal`;
- `bool`, `char`;
- `struct`, `record struct`, `enum`;
- nullable value type như `int?` (`Nullable<int>`);
- value tuple như `(int Id, string Name)` là struct, dù field bên trong có thể là reference.

Reference types gồm:

- `class`, `record class`;
- `string`;
- array;
- `delegate`;
- interface type và `object` dưới góc nhìn biến tham chiếu. Khi một struct được gán sang `object`/interface, boxing có thể xảy ra.

### Default value

- Numeric value fields/elements mặc định bằng `0`; `bool` là `false`; struct được zero-initialize theo field.
- Reference fields/elements mặc định là `null`.
- Local vẫn chịu definite assignment: compiler không cho đọc local chưa chắc đã gán, dù type có default.

`new Coordinate[2]` khởi tạo hai element về default `Coordinate`. `new Account?[2]` khởi tạo hai reference slot là `null`; nó **không** tạo hai `Account`.

### Shallow copy của struct có reference field

Value assignment copy từng field theo semantics của field. Nếu struct chứa một reference field, reference đó cũng được copy, nên hai struct copy có thể cùng trỏ object con:

```text
Struct A.Child ----┐
                   +----> cùng một class object
Struct B.Child ----┘
```

“Value type copy độc lập” chỉ có nghĩa storage field của struct được copy; nó không tự deep-copy object graph được tham chiếu bên trong. Vì vậy ưu tiên struct nhỏ, thường immutable, biểu diễn một value nhất quán.

### Đào sâu (có thể quay lại sau)

#### Sơ đồ đầy đủ: local, field và array

Snapshot sau khi tạo `basket`, hai array và trừ thêm 5 qua `accounts[0]` (bỏ qua string/runtime internal để tập trung):

```text
CALL STACK / REGISTERS (logical Main state)
┌──────────────────────────────────────────────────────────┐
│ first       = Coordinate { X:10, Y:20 }                 │
│ second      = Coordinate { X:99, Y:20 }                 │
│ primary     = ref H1 ───────────────────────────────┐    │
│ alias       = ref H1 ───────────────────────────────┤    │
│ independent = ref H2 ───────────────────────────┐   │    │
│ basket      = ref H4 ────────────────────────┐  │   │    │
│ points      = ref H5 ─────────────────────┐  │  │   │    │
│ accounts    = ref H6 ──────────────────┐  │  │  │   │    │
└────────────────────────────────────────|──|──|──|───|────┘
                                         |  |  |  |   |
MANAGED HEAP                             v  v  v  v   v
H6 Account?[2]  [ ref H1, ref H2 ] ------┘  |  |  |   |
H5 Coordinate[2]                           |  |  |   |
   [ {X:42,Y:20}, {X:99,Y:20} ] <----------┘  |  |   |
H4 Basket                                     |  |   |
   DropOff inline = { X:30, Y:20 } <----------┘  |   |
   Buyer = ref H1 --------------------------------|---┤
H2 Account { Balance:100 } <----------------------┘   |
H1 Account { Balance:55 } <---------------------------┘

H3 Account { Balance:0 }   [unreachable, GC-eligible]
```

Điểm cần đọc chính xác:

- `first` và `second` là value local. Hình đặt chúng trong logical frame cho dễ học; JIT có thể giữ một phần/toàn bộ trong register.
- `DropOff` là value-type field, nên dữ liệu `X/Y` nằm **inline bên trong H4**, không có một heap object Coordinate riêng bắt buộc.
- `Buyer` là reference-type field, nên trong H4 chỉ có reference slot trỏ H1.
- H5 là một array object trên heap; hai `Coordinate` element nằm inline trong vùng dữ liệu của H5. Gán `points[0] = first` copy value vào element.
- H6 là array object; mỗi element là một reference slot. Lúc `new Account?[2]`, hai slot mặc định là `null`; sau đó chúng trỏ H1 và H2. Account không nằm inline trong H6.
- Local reference, reference field và reference array element đều là nơi **chứa reference**; bản thân reference không phải object đích.

Đây là lý do value type không đồng nghĩa stack: `DropOff` và phần tử H5 đều nằm trong heap object chứa chúng. Reference cũng không đồng nghĩa “biến nằm trên heap”: local `primary` là root logic ở frame/register nhưng giá trị của nó trỏ tới heap object H1.

#### Identity, equality và sameness

- `ReferenceEquals(a, b)` hỏi hai reference có trỏ đúng cùng instance không.
- `==` có thể là reference equality mặc định cho class hoặc được type overload để so value.
- `.Equals` có thể được override.

Hai `new Account(100)` khác identity nhưng có field bằng nhau. Đừng dùng reference identity thay business equality, và đừng đoán semantics của `==` mà không biết type.

#### `string` là trường hợp dễ gây nhầm

`string` là immutable reference type. Phép “sửa” chuỗi thực tế tạo/nhận reference tới chuỗi khác; object chuỗi cũ không bị mutate. Compiler/runtime còn có string interning cho literal, nên hai literal giống nhau có thể cùng instance. Không dùng `ReferenceEquals` để so nội dung string; dùng equality phù hợp và `StringComparison` khi cần.

#### GC roots và reachability

GC bắt đầu từ roots như reference đang sống trong stack/register, static fields và runtime handles, rồi đi theo reference field/array element. Object reachable được giữ; object không reachable mới eligible. Gán một local thành `null` không đảm bảo GC chạy ngay và đôi khi JIT đã xác định local không còn sống trước statement đó.

## 6. Lỗi thường gặp

### Học thuộc “struct ở stack, class ở heap”

Class instance/array được mô hình hóa trên managed heap, nhưng struct có thể inline trong object/array trên heap hoặc bị boxing. Local reference có thể ở frame/register. Luôn hỏi context chứa storage.

### Nghĩ reference variable chính là object

`primary` là một slot chứa reference; H1 mới là object. Nhiều slot có thể cùng trỏ H1, một slot có thể được gán sang H2, và slot nullable có thể chứa `null`.

### Nghĩ mỗi phép gán reference tạo object mới

`alias = primary` không có `new`, chỉ copy reference. Muốn instance khác cần `new Account(...)` hoặc một cơ chế clone có semantics được định nghĩa.

### Nghĩ mọi `new` đều cấp phát heap như nhau

`new Account()` và `new Account[2]` tạo heap object có identity. `new Coordinate()` tạo một value được lưu theo context và không bắt buộc cấp phát object riêng. Boxing có thể cấp phát dù source không có keyword `new`.

### Gán lại parameter rồi kỳ vọng caller đổi reference

Parameter mặc định nhận copy của reference. Mutate object qua nó thì thấy chung; gán parameter sang `new` chỉ đổi copy. Return reference mới hoặc dùng `ref` khi hợp đồng thực sự yêu cầu.

### Mong struct assignment deep-copy toàn graph

Struct copy field-by-field. Reference field bên trong vẫn alias object con. Thiết kế struct nhỏ/immutable và vẽ nested reference nếu có.

### Boxing trong loop mà không nhận ra

Thêm value type vào API nhận `object`, format/call interface theo một số đường code, hoặc dùng collection không generic có thể box liên tục. Dùng generic và đo allocation bằng profiler/benchmark trước khi kết luận.

### Unbox sang type “gần giống”

Box chứa exact runtime value type. `object x = 42; long y = (long)x;` lỗi runtime. Phải unbox `int` trước rồi numeric-convert sang `long`.

### Tưởng GC thay thế deterministic cleanup

GC không hứa thời điểm chạy. Không chờ finalizer để đóng file/connection; dùng `using`/`Dispose` theo ownership.

### Phụ thuộc địa chỉ vật lý của managed object

Compacting GC có thể di chuyển object. Reference vẫn hợp lệ vì runtime quản lý; chỉ code interop/unsafe đặc biệt mới pin/lấy pointer và phải kiểm soát lifetime rất cẩn thận.

## 7. Khi nào KHÔNG dùng

Không chọn struct chỉ vì nghĩ stack luôn nhanh. Không dùng sơ đồ vật lý như lời hứa JIT; hãy chốt semantics alias/copy trước khi đo allocation.

## 8. Production notes & scale check

Demo nhỏ chứng minh quan hệ identity bằng ReferenceEquals và giá trị, không đo địa chỉ stack. Object không còn reachable mới đủ điều kiện GC; không có thời điểm thu hồi tức thì được hứa. Struct lớn copy nhiều có cost đáng kể.

<a id="7-bai-tap"></a>

## 9. Bài tập kỹ thuật

### Bài 1 — Dự đoán trước khi chạy

Tạo `struct Size { int Width; int Height; }`, gán `b = a`, sửa `b.Width`, rồi vẽ hai storage và dự đoán output.

**Gợi ý:** không vẽ mũi tên giữa hai value variable; ghi từng field sau phép copy.

### Bài 2 — Ba reference, hai object

Tạo `Account a = new(10)`, `b = a`, `c = new(10)`; sửa qua `b`, rồi in balance và `ReferenceEquals` cho từng cặp.

**Gợi ý:** đặt nhãn H1/H2 ngay tại từng `new`; phép gán không tạo H mới.

### Bài 3 — Parameter mutation và reassignment

Viết một method mutate field của class, một method gán parameter sang object mới, và một method dùng `ref` để gán caller sang object mới. Dự đoán graph sau mỗi call.

**Gợi ý:** với lời gọi thường, copy reference; với `ref`, parameter alias chính slot reference của caller.

### Bài 4 — Field và array inline

Tạo class có một struct field và một class field; tạo cả `StructType[]` và `ClassType?[]`. Vẽ object graph ngay sau `new`, trước khi gán element.

**Gợi ý:** struct field/element chứa field data inline; class field/element chỉ là reference slot mặc định `null`.

### Bài 5 — Boxing và exact unboxing

Box một `int`, thử unbox đúng về `int`, sau đó khảo sát vì sao cast thẳng sang `long` thất bại và viết chuỗi conversion đúng.

**Gợi ý:** tách “unbox exact type” khỏi “numeric conversion”; dùng `try/catch` chỉ để quan sát lỗi trong lab.

## 10. Bài tập tích hợp liên module — Judgment

Đối chiếu copy pointer C và deep copy C++ Module 02–03. C# GC loại bỏ trách nhiệm nào và có loại bỏ lỗi chia sẻ state ngoài ý muốn không?

**Tiêu chí:** nêu contract, nơi state sống, chi phí và driver; không chấm theo số công cụ/pattern. Phần liên module là câu hỏi chuẩn bị, không yêu cầu API chưa học.

## 11. Retrieval practice

Không nhìn bài; trả lời bằng ví dụ khác sample.

1. Vì sao primary còn 60 sau Reassign?
2. Box có giữ alias tới first không?
3. Field struct trong object chứa dữ liệu ở đâu theo mô hình logic?

<a id="8-checklist-tu-anh-gia-va-ieu-huong"></a>

## 12. Checklist tự đánh giá & điều hướng

- [ ] Tôi không còn đồng nhất value type với stack hay reference type với vị trí của biến.
- [ ] Tôi vẽ được slot reference và heap object thành hai thực thể khác nhau.
- [ ] Tôi đánh nhãn một object riêng cho mỗi `new` class/array và không tạo object giả cho assignment.
- [ ] Tôi chỉ ra value-type field/element nằm inline và reference field/element chứa gì.
- [ ] Tôi dự đoán đúng mutation và reassignment khi parameter nhận reference by value.
- [ ] Tôi giải thích boxing là heap object chứa copy và unboxing tạo value copy.
- [ ] Tôi phân biệt “unreachable/GC-eligible” với “đã được giải phóng ngay”.

Điều hướng:

- Prerequisite: [Method, parameter và return](./04-method-parameter-va-return.md)
- Bài tiếp theo: [Array, string, Index và Range](./06-array-string-index-va-range.md)

**Checkpoint cụm:** [Failure Lab](./failure-labs/01-ref-va-overflow.md) · [Review](./reviews/review-01.md).
